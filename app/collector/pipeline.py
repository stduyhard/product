from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

from app.collector.normalizer import normalize_record
from app.collector.sources import JDCollector, TmallCollector
from app.models import JobResult, ProductRecord


class _Collector(Protocol):
    platform: str
    config: Any

    def collect(self, keyword: str) -> list[dict[str, object]]: ...


def collect_products(
    keywords: list[str],
    per_platform_limit: int = 100,
    platforms: list[str] | None = None,
) -> tuple[list[ProductRecord], list[JobResult]]:
    selected_platforms = {item.strip().lower() for item in (platforms or ["jd", "tmall"])}
    collectors: list[_Collector] = []
    if "jd" in selected_platforms:
        collectors.append(JDCollector())
    if "tmall" in selected_platforms:
        collectors.append(TmallCollector())
    records: list[ProductRecord] = []
    jobs: list[JobResult] = []

    for collector in collectors:
        collector.config.per_keyword_limit = per_platform_limit
        for keyword in keywords:
            raw_items = collector.collect(keyword)
            success_count = 0
            for raw in raw_items:
                rec = normalize_record(collector.platform, keyword, raw)
                records.append(rec)
                success_count += 1

            jobs.append(
                JobResult(
                    job_id=f"{collector.platform}-{keyword}",
                    run_time=datetime.now(UTC),
                    platform=collector.platform,
                    keyword=keyword,
                    target_count=per_platform_limit,
                    success_count=success_count,
                    fail_count=max(0, per_platform_limit - success_count),
                    status="success",
                )
            )

    deduped = _dedupe_records(records)
    return deduped, jobs


def _dedupe_records(records: list[ProductRecord]) -> list[ProductRecord]:
    seen: dict[str, ProductRecord] = {}
    for rec in records:
        seen[rec.record_id] = rec
    return list(seen.values())
