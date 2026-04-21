from flask import Flask, request, jsonify
import logging
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import time
import random

from catalog_import import import_shopify_feeds
from catalog_matching import refresh_catalog_matches
from database import init_db
from database import get_session
from models import CatalogProduct, CatalogProductMatch


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
load_dotenv()
init_db()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/catalog/import', methods=['POST'])
def import_catalog():
    payload = request.get_json(silent=True) or {}
    urls = payload.get('urls') or [
        'https://www.allbirds.com/products.json',
        'https://www.gymshark.com/products.json',
        'https://kith.com/products.json',
    ]

    try:
        summary = import_shopify_feeds(urls)
        return jsonify({'success': True, 'summary': summary}), 200
    except Exception as exc:
        logger.error('Catalog import failed: %s', exc, exc_info=True)
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/catalog/matches/refresh', methods=['POST'])
def refresh_catalog_match_index():
    session = get_session()
    try:
        summary = refresh_catalog_matches(session)
        session.commit()
        return jsonify({'success': True, 'summary': summary}), 200
    except Exception as exc:
        session.rollback()
        logger.error('Catalog match refresh failed: %s', exc, exc_info=True)
        return jsonify({'success': False, 'error': str(exc)}), 500
    finally:
        session.close()


@app.route('/api/catalog/products', methods=['GET'])
def list_catalog_products():
    session = get_session()
    try:
        query = session.query(CatalogProduct).filter(CatalogProduct.is_active.is_(True))

        retailer = request.args.get('retailer')
        category = request.args.get('category')
        gender = request.args.get('gender')
        search = request.args.get('search')
        limit = min(max(int(request.args.get('limit', 24)), 1), 100)

        if retailer:
            query = query.filter(CatalogProduct.retailer == retailer)
        if category:
            query = query.filter(CatalogProduct.category == category)
        if gender:
            query = query.filter(CatalogProduct.gender == gender)
        if search:
            like_value = f"%{search.lower()}%"
            query = query.filter(CatalogProduct.normalized_title.like(like_value))

        products = query.order_by(CatalogProduct.updated_at.desc()).limit(limit).all()
        return jsonify({'success': True, 'products': [_serialize_product_summary(product) for product in products]}), 200
    finally:
        session.close()


@app.route('/api/catalog/products/<path:product_id>', methods=['GET'])
def get_catalog_product(product_id):
    session = get_session()
    try:
        product = session.get(CatalogProduct, product_id)
        if product is None:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        return jsonify({'success': True, 'product': _serialize_product_detail(product)}), 200
    finally:
        session.close()


@app.route('/api/catalog/products/<path:product_id>/matches', methods=['GET'])
def get_catalog_product_matches(product_id):
    session = get_session()
    try:
        matches = (
            session.query(CatalogProductMatch)
            .filter(CatalogProductMatch.left_product_id == product_id)
            .order_by(CatalogProductMatch.final_score.desc())
            .limit(50)
            .all()
        )
        return jsonify(
            {
                'success': True,
                'matches': [_serialize_match(match) for match in matches],
            }
        ), 200
    finally:
        session.close()

@app.route('/api/search', methods=['POST'])
def search():
    logger.info(f"/api/search called. Method: {request.method}, Content-Type: {request.content_type}")
    try:
        # Check if it's an image upload or link submission
        has_file = 'image' in request.files
        has_link = 'link' in request.form or (request.is_json and 'link' in request.get_json(silent=True) or {})

        logger.info(f"has_file: {has_file}, has_link: {has_link}")

        if has_file:
            file = request.files['image']
            logger.info(f"Received file: {file.filename}")
            if file.filename == '':
                logger.warning("No file selected for upload.")
                return jsonify({
                    'success': False,
                    'error': 'No file selected'
                }), 400
            if not allowed_file(file.filename):
                logger.warning(f"Invalid file type: {file.filename}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid file type. Allowed: jpg, jpeg, png, gif, webp'
                }), 400
            filename = secure_filename(file.filename)
            timestamp = int(time.time() * 1000)
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info(f"File saved to: {filepath}")
            seed = timestamp % 1000000
            results = _generate_mock_results(seed)
            logger.info(f"Returning mock results for image upload.")
            return jsonify({
                'success': True,
                'results': results,
                'originalItem': {
                    'id': 'original',
                    'name': 'Your uploaded item',
                    'brand': 'User Upload',
                    'price': 0,
                    'image': f'data:image/*;base64,{filename}',
                    'link': '#',
                    'similarity': 100
                }
            }), 200
        elif has_link:
            link_data = request.get_json(silent=True) or {}
            link = link_data.get('link') or request.form.get('link')
            logger.info(f"Received link: {link}")
            if not link:
                logger.warning("No link provided in request.")
                return jsonify({
                    'success': False,
                    'error': 'No link provided'
                }), 400
            if not link.startswith(('http://', 'https://')):
                logger.warning(f"Invalid link format: {link}")
                return jsonify({
                    'success': False,
                    'error': 'Invalid link. Must start with http:// or https://'
                }), 400
            seed = int(time.time() * 1000) % 1000000
            results = _generate_mock_results(seed)
            logger.info(f"Returning mock results for link submission.")
            return jsonify({
                'success': True,
                'results': results,
                'originalItem': {
                    'id': 'original',
                    'name': 'Item from link',
                    'brand': 'External Source',
                    'price': 0,
                    'image': 'https://picsum.photos/300/400?random=original',
                    'link': link,
                    'similarity': 100
                }
            }), 200
        else:
            logger.warning("Neither image nor link provided in request.")
            return jsonify({
                'success': False,
                'error': 'Please provide either an image file or a link'
            }), 400
    except Exception as e:
        logger.error(f"Error in /api/search: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500

def _generate_mock_results(seed):
    """Generate mock fashion results"""
    product_names = [
        'Casual Cotton T-Shirt',
        'Basic Crew Neck Tee',
        'Premium Quality T-Shirt',
        'Comfortable Everyday Shirt',
        'Classic Cotton Top',
        'Minimalist Design Shirt',
        'Essential Basics Tee',
        'Everyday Cotton Shirt'
    ]
    
    brand_names = [
        'Urban Style',
        'Essential Co',
        'Fashion Plus',
        'Casual Wear',
        'Basics Plus',
        'Modern Basics',
        'Simple Store',
        'Minimalist Brand'
    ]
    
    random.seed(seed)
    mock_results = []
    
    for i in range(6):
        price = random.randint(15, 60)
        similarity = random.randint(75, 98)
        product_idx = random.randint(0, len(product_names) - 1)
        brand_idx = random.randint(0, len(brand_names) - 1)
        
        mock_results.append({
            'id': str(i + 1),
            'name': product_names[product_idx],
            'brand': brand_names[brand_idx],
            'price': price,
            'originalPrice': price + random.randint(10, 30),
            'similarity': similarity,
            'image': f'https://picsum.photos/300/400?random={seed + i}',
            'link': f'https://example.com/item_{i + 1}',
            'category': 'Clothing'
        })
    
    return mock_results


def _serialize_product_summary(product):
    return {
        'id': product.id,
        'retailer': product.retailer,
        'title': product.title,
        'brand': product.brand,
        'category': product.category,
        'subcategory': product.subcategory,
        'gender': product.gender,
        'colorPrimary': product.color_primary,
        'priceMin': product.price_min,
        'priceMax': product.price_max,
        'heroImageUrl': product.hero_image_url,
        'productUrl': product.product_url,
        'updatedAt': product.updated_at.isoformat() if product.updated_at else None,
    }


def _serialize_product_detail(product):
    return {
        **_serialize_product_summary(product),
        'handle': product.handle,
        'productType': product.product_type,
        'descriptionText': product.description_text,
        'descriptionHtml': product.description_html,
        'material': product.material,
        'colorRaw': product.color_raw,
        'tags': product.tags or [],
        'compareAtPriceMin': product.compare_at_price_min,
        'compareAtPriceMax': product.compare_at_price_max,
        'currency': product.currency,
        'imageCount': product.image_count,
        'variants': [
            {
                'id': variant.id,
                'sourceVariantId': variant.source_variant_id,
                'sku': variant.sku,
                'title': variant.title,
                'sizeValue': variant.size_value,
                'colorValue': variant.color_value,
                'price': variant.price,
                'compareAtPrice': variant.compare_at_price,
                'available': variant.available,
                'position': variant.position,
            }
            for variant in product.variants
        ],
        'images': [
            {
                'id': image.id,
                'sourceImageId': image.source_image_id,
                'imageUrl': image.image_url,
                'position': image.position,
                'width': image.width,
                'height': image.height,
                'isPrimary': image.is_primary,
            }
            for image in product.images
        ],
    }


def _serialize_match(match):
    return {
        'id': match.id,
        'matchStatus': match.match_status,
        'imageScore': match.image_score,
        'textScore': match.text_score,
        'priceScore': match.price_score,
        'attributeScore': match.attribute_score,
        'finalScore': match.final_score,
        'product': _serialize_product_summary(match.right_product),
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

