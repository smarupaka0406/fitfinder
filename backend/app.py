from __future__ import annotations
from catalog_import import DEFAULT_FEEDS, import_shopify_feeds
from onnx_clip import get_image_embedding, cosine_similarity



def _ensure_catalog_data(session) -> None:
    if session.query(CatalogProduct).count() == 0:
        logger.info('Catalog empty. Importing default feeds before search.')
        summary = import_shopify_feeds(session, DEFAULT_FEEDS)
        logger.info('Catalog import summary: %s', summary)

from flask import Flask, request, jsonify
from io import BytesIO
import logging
import math
import importlib
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import os
import time
import threading
import tempfile
from urllib.parse import urlparse

import imagehash
from PIL import Image
import requests

from catalog_import import DEFAULT_FEEDS
from database import get_session, init_db
from models import CatalogProduct


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
load_dotenv()
init_db()

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

IMAGE_HASH_CACHE: dict[str, imagehash.ImageHash | None] = {}



def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200


@app.route('/api/catalog/import', methods=['POST'])



@app.route('/api/search', methods=['POST'])
def search():
    logger.info('/api/search called. Method: %s, Content-Type: %s', request.method, request.content_type)

    has_file = 'image' in request.files
    has_link = 'link' in request.form or (request.is_json and 'link' in (request.get_json(silent=True) or {}))

    if not (has_file or has_link):
        return jsonify({'success': False, 'error': 'Please provide either an image file or a link'}), 400

    session = get_session()
    try:
        if has_file:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            if not allowed_file(file.filename):
                return jsonify({'success': False, 'error': 'Invalid file type. Allowed: jpg, jpeg, png, gif, webp'}), 400

            filename = secure_filename(file.filename)
            timestamp = int(time.time() * 1000)
            filename = f'{timestamp}_{filename}'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            logger.info('File saved to: %s', filepath)

            category_hint = _extract_query_category_hint(filename)
            results = _search_catalog_by_image(session, filepath, category_hint=category_hint)
            return jsonify(
                {
                    'success': True,
                    'results': results,
                    'originalItem': {
                        'id': 'original',
                        'name': 'Your uploaded item',
                        'brand': 'User Upload',
                        'price': 0,
                        'image': f'data:image/*;base64,{filename}',
                        'link': '#',
                        'similarity': 100,
                    },
                }
            ), 200

        link_data = request.get_json(silent=True) or {}
        link = link_data.get('link') or request.form.get('link')
        if not link:
            return jsonify({'success': False, 'error': 'No link provided'}), 400
        if not link.startswith(('http://', 'https://')):
            return jsonify({'success': False, 'error': 'Invalid link. Must start with http:// or https://'}), 400

        results = _search_catalog_by_link(session, link)
        return jsonify(
            {
                'success': True,
                'results': results,
                'originalItem': {
                    'id': 'original',
                    'name': 'Item from link',
                    'brand': 'External Source',
                    'price': 0,
                    'image': 'https://picsum.photos/300/400?random=original',
                    'link': link,
                    'similarity': 100,
                },
            }
        ), 200
    except Exception as exc:
        logger.error('Error in /api/search: %s', exc, exc_info=True)
        return jsonify({'success': False, 'error': f'Search failed: {str(exc)}'}), 500
    finally:
        session.close()


    pass


def _search_catalog_by_image(session, filepath: str, limit: int = 6, category_hint: str | None = None) -> list[dict]:
    _ensure_catalog_data(session)

    # Try ONNX CLIP semantic matching first
    try:
        uploaded_embedding = get_image_embedding(filepath)
    except Exception as exc:
        logger.warning('ONNX CLIP embedding failed for uploaded image: %s', exc)
        uploaded_embedding = None

    if uploaded_embedding is not None:
        products = (
            session.query(CatalogProduct)
            .filter(CatalogProduct.is_active.is_(True))
            .all()
        )

        scored: list[tuple[float, CatalogProduct]] = []
        for product in products:
            if not product.hero_image_url:
                continue
            try:
                # Download and embed catalog image
                response = requests.get(product.hero_image_url, timeout=20)
                response.raise_for_status()
                with Image.open(BytesIO(response.content)) as img, tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    tmp_path = tmp.name
                    img.convert('RGB').save(tmp_path, format='JPEG')
                try:
                    catalog_embedding = get_image_embedding(tmp_path)
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                similarity = cosine_similarity(uploaded_embedding, catalog_embedding)
                # Convert similarity (-1 to 1) to 0-100 scale
                score = max(0, min(99, round(((similarity + 1.0) / 2.0) * 100)))
                score = _apply_category_adjustment(score, product.category, category_hint)
                scored.append((score, product))
            except requests.RequestException as exc:
                logger.info('Skipping catalog image URL (unavailable): %s (%s)', product.hero_image_url, exc)
                continue
            except Exception as exc:
                logger.warning('ONNX CLIP embedding failed for catalog image: %s', exc)
                continue

        if scored:
            scored.sort(key=lambda pair: pair[0], reverse=True)
            return [_serialize_product(product, similarity) for similarity, product in scored[:limit]]

    # Fallback to pHash if ONNX CLIP fails
    uploaded_hash = _hash_local_image(filepath)
    if uploaded_hash is None:
        logger.warning('Could not hash uploaded image, using fallback catalog ranking.')
        return _fallback_catalog(session, limit)

    products = (
        session.query(CatalogProduct)
        .filter(CatalogProduct.is_active.is_(True))
        .all()
    )

    scored: list[tuple[int, CatalogProduct]] = []
    for product in products:
        if not product.hero_image_url:
            continue

        catalog_hash = _hash_remote_image(product.hero_image_url)
        if catalog_hash is None:
            continue

        similarity = _phash_similarity(uploaded_hash, catalog_hash)
        similarity = _apply_category_adjustment(similarity, product.category, category_hint)
        scored.append((similarity, product))

    if not scored:
        logger.warning('No catalog images could be hashed. Returning fallback catalog list.')
        return _fallback_catalog(session, limit, category_hint=category_hint)

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [_serialize_product(product, similarity) for similarity, product in scored[:limit]]





def _search_catalog_by_link(session, link: str, limit: int = 6) -> list[dict]:
    _ensure_catalog_data(session)

    host = urlparse(link).netloc.lower().replace('www.', '')
    retailer_hint = host.split('.')[0] if host else None
    products_query = session.query(CatalogProduct).filter(CatalogProduct.is_active.is_(True))

    if retailer_hint:
        prioritized = products_query.filter(CatalogProduct.retailer == retailer_hint).limit(limit).all()
        if prioritized:
            return [_serialize_product(product, 90 - index * 3) for index, product in enumerate(prioritized)]

    return _fallback_catalog(session, limit)


def _fallback_catalog(session, limit: int = 6, category_hint: str | None = None) -> list[dict]:
    query = session.query(CatalogProduct).filter(CatalogProduct.is_active.is_(True))
    if category_hint:
        filtered = query.filter(CatalogProduct.category == category_hint).order_by(CatalogProduct.updated_at.desc()).limit(limit).all()
        if filtered:
            products = filtered
        else:
            products = query.order_by(CatalogProduct.updated_at.desc()).limit(limit).all()
    else:
        products = query.order_by(CatalogProduct.updated_at.desc()).limit(limit).all()

    if not products:
        return []

    return [_serialize_product(product, max(50, 85 - index * 4)) for index, product in enumerate(products)]


def _hash_local_image(filepath: str) -> imagehash.ImageHash | None:
    try:
        with Image.open(filepath) as image:
            return imagehash.phash(image)
    except Exception as exc:
        logger.warning('Failed to hash local image %s: %s', filepath, exc)
        return None


def _hash_remote_image(url: str) -> imagehash.ImageHash | None:
    if url in IMAGE_HASH_CACHE:
        return IMAGE_HASH_CACHE[url]

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        with Image.open(BytesIO(response.content)) as image:
            hashed = imagehash.phash(image)
            IMAGE_HASH_CACHE[url] = hashed
            return hashed
    except Exception:
        IMAGE_HASH_CACHE[url] = None
        return None















    right_norm = math.sqrt(sum(right[index] * right[index] for index in range(size)))
    if left_norm == 0 or right_norm == 0:
        return None
    return dot_product / (left_norm * right_norm)


def _extract_query_category_hint(filename: str | None) -> str | None:
    if not filename:
        return None

    lowered = filename.lower()
    keyword_map = {
        'bottom': ['skirt', 'dress', 'pant', 'trouser', 'jean', 'legging', 'short'],
        'top': ['top', 'tee', 'shirt', 'blouse', 'tank', 'crop'],
        'footwear': ['shoe', 'sneaker', 'sandal', 'slipper', 'boot', 'heel'],
        'outerwear': ['jacket', 'coat', 'hoodie', 'sweatshirt'],
    }

    for category, keywords in keyword_map.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return None


def _apply_category_adjustment(score: int, product_category: str | None, category_hint: str | None) -> int:
    if not category_hint:
        return score

    normalized_product_category = (product_category or '').lower().strip()
    adjusted = score
    if normalized_product_category == category_hint:
        adjusted += 12
    elif category_hint == 'bottom' and normalized_product_category == 'footwear':
        adjusted -= 20
    elif category_hint == 'footwear' and normalized_product_category in {'top', 'bottom', 'outerwear'}:
        adjusted -= 20
    else:
        adjusted -= 8

    return max(0, min(99, adjusted))


def _phash_similarity(left: imagehash.ImageHash, right: imagehash.ImageHash) -> int:
    # pHash size is 8x8 (64 bits) by default, so normalize hamming distance to percentage.
    distance = left - right
    similarity = round(100 * (1 - (distance / 64.0)))
    return max(0, min(99, similarity))


def _serialize_product(product: CatalogProduct, similarity: int) -> dict:
    primary_price = product.price_min if product.price_min is not None else product.price_max
    fallback_price = product.compare_at_price_min if product.compare_at_price_min is not None else product.compare_at_price_max

    return {
        'id': product.id,
        'name': product.title,
        'brand': product.brand,
        'price': round(primary_price if primary_price is not None else 0.0, 2),
        'originalPrice': round(fallback_price, 2) if fallback_price is not None else None,
        'similarity': similarity,
        'image': product.hero_image_url or 'https://picsum.photos/300/400?random=fallback',
        'link': product.product_url,
        'category': product.category,
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
