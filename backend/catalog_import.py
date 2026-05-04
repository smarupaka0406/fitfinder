from typing import Any
from datetime import datetime
import re
from urllib.parse import urlparse

import requests

from models import CatalogProduct

def import_shopify_feeds(session, urls: list[str] | None = None) -> dict[str, Any]:
    feeds = urls or DEFAULT_FEEDS
    summary: dict[str, Any] = {
        'processed_urls': 0,
        'imported_products': 0,
        'errors': [],
    }

    from typing import Any

    for url in feeds:
        retailer = _retailer_name_from_url(url)
        try:
            products = _fetch_products(url)
            imported_count = 0
            for raw in products:
                normalized = _normalize_product(raw, retailer, url)
                _upsert_product(session, normalized)
                imported_count += 1
            session.commit()
            summary['processed_urls'] += 1
            summary['imported_products'] += imported_count
        except Exception as exc:  # keep partial success across feeds
            session.rollback()
            summary['errors'].append({'url': url, 'error': str(exc)})

    return summary




DEFAULT_FEEDS = [
    'https://www.allbirds.com/products.json',
    'https://www.gymshark.com/products.json',
    'https://kith.com/products.json',
]

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/135.0.0.0 Safari/537.36'
)

def _fetch_products(url: str) -> list[dict[str, Any]]:
    response = requests.get(
        url,
        headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    products = payload.get('products')
    if not isinstance(products, list):
        raise ValueError(f'Unexpected payload shape from {url}')
    return products


def _normalize_product(raw: dict[str, Any], retailer: str, feed_url: str) -> dict[str, Any]:
    variants = raw.get('variants') or []
    tags = _normalize_tags(raw.get('tags'))

    source_product_id = str(raw.get('id'))
    handle = raw.get('handle') or source_product_id
    title = (raw.get('title') or '').strip() or handle

    prices = [_safe_float(variant.get('price')) for variant in variants]
    prices = [value for value in prices if value is not None]
    compare_prices = [_safe_float(variant.get('compare_at_price')) for variant in variants]
    compare_prices = [value for value in compare_prices if value is not None]

    image_urls = [image.get('src') for image in (raw.get('images') or []) if image.get('src')]
    category = _categorize_product(title, raw.get('product_type') or '', tags)

    return {
        'id': f'{retailer}:{source_product_id}',
        'retailer': retailer,
        'source_product_id': source_product_id,
        'handle': handle,
        'title': title,
        'normalized_title': _normalize_title(title),
        'brand': (raw.get('vendor') or retailer.title()).strip(),
        'category': category,
        'price_min': min(prices) if prices else None,
        'price_max': max(prices) if prices else None,
        'compare_at_price_min': min(compare_prices) if compare_prices else None,
        'compare_at_price_max': max(compare_prices) if compare_prices else None,
        'hero_image_url': image_urls[0] if image_urls else None,
        'product_url': _build_product_url(feed_url, handle),
        'tags': tags,
        'is_active': True,
        'raw_payload': raw,
        'image_count': len(image_urls),
        'updated_at': datetime.utcnow(),
    }


def _upsert_product(session, product_data: dict[str, Any]) -> None:
    existing = session.get(CatalogProduct, product_data['id'])
    if existing is None:
        session.add(CatalogProduct(**product_data))
        return

    for key, value in product_data.items():
        setattr(existing, key, value)


def _retailer_name_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith('www.'):
        host = host[4:]
    return host.split('.')[0]


def _build_product_url(feed_url: str, handle: str) -> str:
    parsed = urlparse(feed_url)
    return f'{parsed.scheme}://{parsed.netloc}/products/{handle}'


def _normalize_tags(tags: Any) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]
    if isinstance(tags, str):
        return [segment.strip() for segment in tags.split(',') if segment.strip()]
    return []


def _normalize_title(value: str) -> str:
    normalized = re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()
    return re.sub(r'\s+', ' ', normalized)


def _categorize_product(title: str, product_type: str, tags: list[str]) -> str:
    haystack = ' '.join([title, product_type, *tags]).lower()
    if any(term in haystack for term in ['tee', 'shirt', 'top', 'tank', 'blouse', 'crop']):
        return 'top'
    if any(term in haystack for term in ['legging', 'pant', 'jean', 'short', 'skirt', 'dress']):
        return 'bottom'
    if any(term in haystack for term in ['shoe', 'sneaker', 'runner', 'sandal', 'slipper']):
        return 'footwear'
    if any(term in haystack for term in ['hoodie', 'sweatshirt', 'jacket', 'coat']):
        return 'outerwear'
    return 'apparel'


def _safe_float(value: Any) -> float | None:
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
