from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
from html import unescape
import re
from typing import Any
from urllib.parse import urlparse

import requests

from catalog_matching import refresh_catalog_matches
from database import get_session
from models import CatalogProduct, CatalogProductImage, CatalogProductVariant


USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/135.0.0.0 Safari/537.36'
)


def import_shopify_feeds(urls: list[str]) -> dict[str, Any]:
    session = get_session()
    summary = {'processed_urls': 0, 'imported_products': 0, 'errors': []}

    try:
        for url in urls:
            retailer = _retailer_name_from_url(url)
            try:
                products = _fetch_products(url)
                imported_count = 0
                for raw_product in products:
                    normalized = _normalize_product(raw_product, retailer, url)
                    _upsert_product(session, normalized)
                    imported_count += 1

                session.commit()
                summary['processed_urls'] += 1
                summary['imported_products'] += imported_count
            except Exception as exc:
                session.rollback()
                summary['errors'].append({'url': url, 'error': str(exc)})

        if summary['processed_urls'] > 0:
            summary['match_refresh'] = refresh_catalog_matches(session)
            session.commit()
    finally:
        session.close()

    return summary


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


def _normalize_product(raw_product: dict[str, Any], retailer: str, feed_url: str) -> dict[str, Any]:
    variants = raw_product.get('variants') or []
    images = raw_product.get('images') or []
    description_html = raw_product.get('body_html') or ''
    description_text = _strip_html(description_html)
    tags = _normalize_tags(raw_product.get('tags'))
    title = (raw_product.get('title') or '').strip()
    product_type = raw_product.get('product_type') or ''

    price_values = [_safe_float(variant.get('price')) for variant in variants if _safe_float(variant.get('price')) is not None]
    compare_at_values = [
        _safe_float(variant.get('compare_at_price'))
        for variant in variants
        if _safe_float(variant.get('compare_at_price')) is not None
    ]

    color_raw = _extract_color(title, description_text, tags)
    category, subcategory = _categorize_product(title, product_type, tags)
    gender = _extract_gender(title, tags)
    hero_image_url = images[0].get('src') if images else None
    material = _extract_material(description_text, tags)

    source_product_id = str(raw_product.get('id'))
    product_id = f'{retailer}:{source_product_id}'
    handle = raw_product.get('handle') or source_product_id

    return {
        'product': {
            'id': product_id,
            'retailer': retailer,
            'source_product_id': source_product_id,
            'handle': handle,
            'product_url': _build_product_url(feed_url, handle),
            'title': title,
            'normalized_title': _normalize_title(title),
            'brand': (raw_product.get('vendor') or retailer.title()).strip(),
            'product_type': product_type,
            'category': category,
            'subcategory': subcategory,
            'gender': gender,
            'color_primary': color_raw.split('/')[0].strip() if color_raw else None,
            'color_raw': color_raw,
            'material': material,
            'description_html': description_html,
            'description_text': description_text,
            'tags': tags,
            'price_min': min(price_values) if price_values else None,
            'price_max': max(price_values) if price_values else None,
            'compare_at_price_min': min(compare_at_values) if compare_at_values else None,
            'compare_at_price_max': max(compare_at_values) if compare_at_values else None,
            'currency': 'USD',
            'hero_image_url': hero_image_url,
            'image_count': len(images),
            'is_active': True,
            'published_at': _parse_datetime(raw_product.get('published_at')),
            'source_created_at': _parse_datetime(raw_product.get('created_at')),
            'source_updated_at': _parse_datetime(raw_product.get('updated_at')),
            'text_embedding': _build_text_embedding(title, description_text, tags, material, color_raw),
            'image_embedding': _build_image_embedding(hero_image_url, images),
            'hero_image_phash': _build_phash(hero_image_url),
            'raw_payload': raw_product,
            'ingested_at': datetime.utcnow(),
        },
        'variants': [
            {
                'source_variant_id': str(variant.get('id')),
                'sku': variant.get('sku'),
                'title': variant.get('title'),
                'size_value': variant.get('option1') or variant.get('title'),
                'color_value': variant.get('option2'),
                'price': _safe_float(variant.get('price')),
                'compare_at_price': _safe_float(variant.get('compare_at_price')),
                'available': bool(variant.get('available')),
                'position': variant.get('position') or 0,
                'raw_payload': variant,
            }
            for variant in variants
        ],
        'images': [
            {
                'source_image_id': str(image.get('id')),
                'image_url': image.get('src'),
                'position': image.get('position') or 0,
                'width': image.get('width'),
                'height': image.get('height'),
                'phash': _build_phash(image.get('src')),
                'image_embedding': _build_image_embedding(image.get('src'), [image]),
                'is_primary': index == 0,
                'raw_payload': image,
            }
            for index, image in enumerate(images)
            if image.get('src')
        ],
    }


def _upsert_product(session, normalized: dict[str, Any]) -> None:
    product_data = normalized['product']
    product = session.get(CatalogProduct, product_data['id'])
    if product is None:
        product = CatalogProduct(**product_data)
        session.add(product)
    else:
        for key, value in product_data.items():
            setattr(product, key, value)
        product.variants.clear()
        product.images.clear()

    for variant_data in normalized['variants']:
        product.variants.append(CatalogProductVariant(**variant_data))

    for image_data in normalized['images']:
        product.images.append(CatalogProductImage(**image_data))


def _retailer_name_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith('www.'):
        host = host[4:]
    return host.split('.')[0]


def _build_product_url(feed_url: str, handle: str) -> str:
    parsed = urlparse(feed_url)
    return f'{parsed.scheme}://{parsed.netloc}/products/{handle}'


def _normalize_title(value: str) -> str:
    normalized = re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()
    return re.sub(r'\s+', ' ', normalized)


def _normalize_tags(tags: Any) -> list[str]:
    if tags is None:
        return []
    if isinstance(tags, list):
        return [str(tag).strip() for tag in tags if str(tag).strip()]
    if isinstance(tags, str):
        return [segment.strip() for segment in tags.split(',') if segment.strip()]
    return []


def _strip_html(value: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', value)
    text = unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def _extract_gender(title: str, tags: list[str]) -> str | None:
    haystack = ' '.join([title, *tags]).lower()
    if 'womens' in haystack or "women's" in haystack or 'wmns' in haystack:
        return 'womens'
    if 'mens' in haystack or "men's" in haystack:
        return 'mens'
    if 'kids' in haystack or 'toddl' in haystack or 'baby' in haystack or 'infant' in haystack:
        return 'kids'
    if 'unisex' in haystack:
        return 'unisex'
    return None


def _extract_color(title: str, description_text: str, tags: list[str]) -> str | None:
    title_match = re.search(r' - ([^-]+(?: / [^-]+)*)$', title)
    if title_match:
        return title_match.group(1).strip()

    description_match = re.search(r'Color:\s*([^\.]+)', description_text, re.IGNORECASE)
    if description_match:
        return description_match.group(1).strip()

    hues = []
    for tag in tags:
        tag_lower = tag.lower()
        if 'hue =' in tag_lower:
            hues.append(tag.split('=>')[-1].strip())
    if hues:
        return ' / '.join(hues)
    return None


def _extract_material(description_text: str, tags: list[str]) -> str | None:
    description_match = re.search(r'Material:\s*([^\.]+)', description_text, re.IGNORECASE)
    if description_match:
        return description_match.group(1).strip()

    for tag in tags:
        tag_lower = tag.lower()
        if 'material =' in tag_lower:
            return tag.split('=>')[-1].strip()
    return None


def _categorize_product(title: str, product_type: str, tags: list[str]) -> tuple[str, str | None]:
    haystack = ' '.join([title, product_type, *tags]).lower()

    if any(term in haystack for term in ['tank', 'tee', 'top', 'blouse', 'shirt', 'crop']):
        gender = _extract_gender(title, tags)
        prefix = gender if gender in {'womens', 'mens', 'kids'} else 'apparel'
        if 'tank' in haystack:
            return f'{prefix}_top', 'tank'
        if 'blouse' in haystack:
            return f'{prefix}_top', 'blouse'
        if 'tee' in haystack or 't-shirt' in haystack or 'shirt' in haystack:
            return f'{prefix}_top', 'tee'
        if 'crop' in haystack:
            return f'{prefix}_top', 'crop_top'
        return f'{prefix}_top', 'top'

    if any(term in haystack for term in ['legging', 'brief', 'bra', 'bralette']):
        if 'legging' in haystack:
            return 'bottom', 'legging'
        return 'underwear', 'sports_bra'

    if any(term in haystack for term in ['sneaker', 'runner', 'shoe', 'sandals', 'sandal', 'slipper', 'flat']):
        if 'sandal' in haystack:
            return 'footwear', 'sandal'
        if 'slipper' in haystack:
            return 'footwear', 'slipper'
        if 'flat' in haystack:
            return 'footwear', 'flat'
        return 'footwear', 'sneaker'

    if 'hoodie' in haystack:
        return 'apparel', 'hoodie'
    if 'sweatpant' in haystack:
        return 'bottom', 'sweatpant'
    if 'short' in haystack:
        return 'bottom', 'short'

    fallback = _normalize_title(product_type).replace(' ', '_') or 'unknown'
    return fallback, None


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None


def _safe_float(value: Any) -> float | None:
    if value in (None, ''):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_text_embedding(
    title: str,
    description_text: str,
    tags: list[str],
    material: str | None,
    color_raw: str | None,
    dimensions: int = 32,
) -> list[float]:
    tokens = _tokenize(' '.join([title, description_text, material or '', color_raw or '', *tags]))
    return _hashed_embedding(tokens, dimensions)


def _build_image_embedding(hero_image_url: str | None, images: list[dict[str, Any]], dimensions: int = 32) -> list[float]:
    url_tokens = []
    if hero_image_url:
        url_tokens.extend(_tokenize(hero_image_url))
    for image in images[:4]:
        src = image.get('src') if isinstance(image, dict) else None
        if src:
            url_tokens.extend(_tokenize(src))
    return _hashed_embedding(url_tokens, dimensions)


def _build_phash(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.md5(value.encode('utf-8')).hexdigest()[:16]


def _hashed_embedding(tokens: list[str], dimensions: int) -> list[float]:
    if not tokens:
        return [0.0] * dimensions

    vector = [0.0] * dimensions
    for token in tokens:
        digest = hashlib.sha256(token.encode('utf-8')).digest()
        bucket = digest[0] % dimensions
        sign = 1.0 if digest[1] % 2 == 0 else -1.0
        weight = 1.0 + (digest[2] / 255.0)
        vector[bucket] += sign * weight

    norm = sum(component * component for component in vector) ** 0.5
    if norm == 0:
        return vector
    return [round(component / norm, 6) for component in vector]


def _tokenize(value: str) -> list[str]:
    return re.findall(r'[a-z0-9]+', value.lower())


def main() -> None:
    parser = argparse.ArgumentParser(description='Import Shopify-style product feeds into the catalog tables.')
    parser.add_argument(
        'urls',
        nargs='*',
        default=[
            'https://www.allbirds.com/products.json',
            'https://www.gymshark.com/products.json',
            'https://kith.com/products.json',
        ],
        help='One or more Shopify-style products.json URLs.',
    )
    args = parser.parse_args()
    print(import_shopify_feeds(args.urls))


if __name__ == '__main__':
    main()