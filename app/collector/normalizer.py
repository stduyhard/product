from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from app.models import ProductRecord

_BRAND_ALIASES = {
    "midea": "midea",
    "美的": "midea",
    "haier": "haier",
    "海尔": "haier",
    "aux": "aux",
    "奥克斯": "aux",
    "xiaomi": "xiaomi",
    "小米": "xiaomi",
}

_FEATURE_ALIASES = {
    "massage": "按摩",
    "按摩": "按摩",
    "foldable": "折叠",
    "折叠": "折叠",
    "sterilize": "杀菌",
    "杀菌": "杀菌",
    "drain": "排水",
    "排水": "排水",
    "timer": "定时",
    "定时": "定时",
    "constant-temp": "恒温",
    "恒温": "恒温",
    "fast-heat": "速热",
    "速热": "速热",
}


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_brand(raw_brand: str, title: str) -> str:
    text = (raw_brand or title or "").lower()
    for alias, normalized in _BRAND_ALIASES.items():
        if alias in text:
            return normalized
    return raw_brand.strip() if raw_brand else "unknown-brand"


def extract_capacity_l(title: str) -> float | None:
    matched = re.search(r"(\d+(?:\.\d+)?)\s*L", title, flags=re.IGNORECASE)
    if not matched:
        return None
    return float(matched.group(1))


def extract_features(title: str) -> list[str]:
    title_lower = title.lower()
    features: list[str] = []
    for alias, canonical in _FEATURE_ALIASES.items():
        if alias in title_lower and canonical not in features:
            features.append(canonical)
    return features


def normalize_record(platform: str, keyword: str, raw: dict[str, Any]) -> ProductRecord:
    product_id = str(raw.get("product_id", ""))
    title = str(raw.get("title", "")).strip()
    brand = normalize_brand(str(raw.get("brand", "")).strip(), title)
    price_current = _to_float(raw.get("price_current"), 0.0)

    price_original_raw = raw.get("price_original")
    price_original = _to_float(price_original_raw) if price_original_raw else None
    image_url = str(raw.get("image_url", ""))
    product_url = str(raw.get("product_url", ""))
    shop_name = str(raw.get("shop_name", ""))
    shop_type = str(raw.get("shop_type", "other"))
    sales_or_reviews = _to_int(raw.get("sales_or_reviews"), 0)

    rating_raw = raw.get("rating")
    rating = _to_float(rating_raw) if rating_raw is not None else None
    heating_type = str(raw.get("heating_type", "unknown"))

    capacity_raw = raw.get("capacity_l")
    capacity_l = _to_float(capacity_raw) if capacity_raw is not None else extract_capacity_l(title)

    core_features_raw = raw.get("core_features")
    if isinstance(core_features_raw, list):
        core_features = [str(item) for item in core_features_raw]
    else:
        core_features = extract_features(title)

    hash_source = title.encode("utf-8")
    fallback_id = hashlib.sha256(hash_source).hexdigest()[:12]
    record_key = f"{platform}:{product_id or fallback_id}"

    quality = "normal"
    if not title or price_current <= 0:
        quality = "missing_fields"

    return ProductRecord(
        record_id=record_key,
        platform=platform,
        keyword=keyword,
        product_id=product_id or record_key,
        title=title,
        brand=brand,
        price_current=price_current,
        price_original=price_original,
        image_url=image_url,
        product_url=product_url,
        shop_name=shop_name,
        shop_type=shop_type,
        sales_or_reviews=sales_or_reviews,
        capacity_l=capacity_l,
        heating_type=heating_type,
        core_features=core_features,
        rating=rating,
        capture_time=datetime.now(UTC),
        data_quality_flag=quality,
        raw=dict(raw),
    )