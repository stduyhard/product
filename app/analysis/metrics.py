from __future__ import annotations

from collections import Counter

from app.models import ProductRecord


def summarize(records: list[ProductRecord]) -> dict[str, object]:
    if not records:
        return {
            "total": 0,
            "avg_price": 0,
            "brand_top": [],
            "price_band": {},
            "feature_coverage": {},
            "shop_type_share": {},
        }

    total = len(records)
    avg_price = round(sum(item.price_current for item in records) / total, 2)

    brand_counts = Counter(item.brand for item in records)
    brand_top = brand_counts.most_common(10)

    bands = Counter(_price_band(item.price_current) for item in records)
    feature_counts: Counter[str] = Counter()
    for item in records:
        feature_counts.update(item.core_features)

    shop_types = Counter(item.shop_type for item in records)
    return {
        "total": total,
        "avg_price": avg_price,
        "brand_top": brand_top,
        "price_band": dict(bands),
        "feature_coverage": dict(feature_counts),
        "shop_type_share": dict(shop_types),
    }


def _price_band(price: float) -> str:
    if price < 200:
        return "0-199"
    if price < 400:
        return "200-399"
    return "400+"