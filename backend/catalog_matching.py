from __future__ import annotations

import math
from typing import Any

from sqlalchemy import or_

from models import CatalogProduct, CatalogProductMatch


MATCH_THRESHOLD = 0.55
MAX_CANDIDATES_PER_PRODUCT = 20


def refresh_catalog_matches(session) -> dict[str, int]:
    products = session.query(CatalogProduct).filter(CatalogProduct.is_active.is_(True)).all()
    session.query(CatalogProductMatch).delete()

    created = 0
    for product in products:
        candidates = _candidate_products(session, product)
        ranked = []
        for candidate in candidates:
            if candidate.id == product.id:
                continue

            score_bundle = score_products(product, candidate)
            if score_bundle['final_score'] >= MATCH_THRESHOLD:
                ranked.append((candidate, score_bundle))

        ranked.sort(key=lambda item: item[1]['final_score'], reverse=True)
        for candidate, score_bundle in ranked[:MAX_CANDIDATES_PER_PRODUCT]:
            session.add(
                CatalogProductMatch(
                    left_product_id=product.id,
                    right_product_id=candidate.id,
                    image_score=score_bundle['image_score'],
                    text_score=score_bundle['text_score'],
                    price_score=score_bundle['price_score'],
                    attribute_score=score_bundle['attribute_score'],
                    final_score=score_bundle['final_score'],
                )
            )
            created += 1

    session.flush()
    return {'products': len(products), 'matches': created}


def score_products(left: CatalogProduct, right: CatalogProduct) -> dict[str, float]:
    image_score = cosine_similarity(left.image_embedding, right.image_embedding)
    text_score = cosine_similarity(left.text_embedding, right.text_embedding)
    price_score = relative_price_similarity(left.price_min, right.price_min)
    attribute_score = attribute_similarity(left, right)

    final_score = (
        0.45 * image_score
        + 0.3 * text_score
        + 0.15 * attribute_score
        + 0.1 * price_score
    )

    return {
        'image_score': round(image_score, 4),
        'text_score': round(text_score, 4),
        'price_score': round(price_score, 4),
        'attribute_score': round(attribute_score, 4),
        'final_score': round(final_score, 4),
    }


def cosine_similarity(left: Any, right: Any) -> float:
    if not isinstance(left, list) or not isinstance(right, list) or not left or not right:
        return 0.0

    size = min(len(left), len(right))
    dot_product = sum(float(left[index]) * float(right[index]) for index in range(size))
    left_norm = math.sqrt(sum(float(left[index]) ** 2 for index in range(size)))
    right_norm = math.sqrt(sum(float(right[index]) ** 2 for index in range(size)))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return max(0.0, min(1.0, dot_product / (left_norm * right_norm)))


def relative_price_similarity(left_price: float | None, right_price: float | None) -> float:
    if left_price is None or right_price is None:
        return 0.0
    denominator = max(left_price, right_price, 1.0)
    return max(0.0, 1.0 - abs(left_price - right_price) / denominator)


def attribute_similarity(left: CatalogProduct, right: CatalogProduct) -> float:
    score = 0.0
    checks = 0
    for left_value, right_value in [
        (left.category, right.category),
        (left.subcategory, right.subcategory),
        (left.gender, right.gender),
        (left.color_primary, right.color_primary),
        (left.brand, right.brand),
    ]:
        if left_value or right_value:
            checks += 1
            if (left_value or '').lower() == (right_value or '').lower():
                score += 1.0
    if checks == 0:
        return 0.0
    return score / checks


def _candidate_products(session, product: CatalogProduct) -> list[CatalogProduct]:
    category_filter = [CatalogProduct.category == product.category]
    if product.subcategory:
        category_filter.append(CatalogProduct.subcategory == product.subcategory)

    query = (
        session.query(CatalogProduct)
        .filter(CatalogProduct.is_active.is_(True))
        .filter(CatalogProduct.id != product.id)
        .filter(CatalogProduct.retailer != product.retailer)
        .filter(or_(*category_filter))
    )

    if product.gender:
        query = query.filter(or_(CatalogProduct.gender == product.gender, CatalogProduct.gender.is_(None)))

    return query.limit(200).all()