from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class ProductRecord:
    record_id: str
    platform: str
    keyword: str
    product_id: str
    title: str
    brand: str
    price_current: float
    price_original: float | None
    image_url: str
    product_url: str
    shop_name: str
    shop_type: str
    sales_or_reviews: int
    capacity_l: float | None
    heating_type: str
    core_features: list[str] = field(default_factory=list)
    rating: float | None = None
    capture_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    data_quality_flag: str = "normal"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobResult:
    job_id: str
    run_time: datetime
    platform: str
    keyword: str
    target_count: int
    success_count: int
    fail_count: int
    status: str
    error_summary: str = ""