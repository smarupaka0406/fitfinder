from flask import Flask, request, jsonify
import logging
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import time
import random


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

