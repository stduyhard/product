from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.analysis.ai_summary import DeepSeekAnalyzer
from app.analysis.metrics import summarize
from app.bot.kb import build_knowledge_base
from app.collector.pipeline import collect_products
from app.report.brief import build_executive_brief
from app.report.builder import build_report
from app.report.dashboard import build_dashboard_snapshot
from app.settings import settings
from app.sync.feishu import FeishuBitableClient

DEFAULT_KEYWORDS = [
    "\u6ce1\u811a\u6876",
    "\u8db3\u6d74\u76c6",
    "\u6052\u6e29\u8db3\u6d74\u6876",
    "\u6298\u53e0\u6ce1\u811a\u6876",
]


def _repair_text(value: str) -> str:
    if not value:
        return value
    try:
        repaired = value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value
    return repaired if repaired else value


def _load_keywords(config_path: str = "config/keywords.json") -> list[str]:
    override = [
        _repair_text(item.strip())
        for item in settings.keywords_override.split(",")
        if item.strip()
    ]
    if override:
        return override

    path = Path(config_path)
    if not path.exists():
        return DEFAULT_KEYWORDS

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    raw = payload.get("keywords", []) if isinstance(payload, dict) else []
    keywords = [str(item).strip() for item in raw if str(item).strip()]
    return keywords or DEFAULT_KEYWORDS


def _load_platforms() -> list[str]:
    platforms = [
        item.strip().lower() for item in settings.collector_platforms.split(",") if item.strip()
    ]
    return platforms or ["jd", "tmall"]


def run() -> None:
    keywords = _load_keywords()
    platforms = _load_platforms()
    records, jobs = collect_products(
        keywords=keywords,
        per_platform_limit=settings.collector_per_platform_limit,
        platforms=platforms,
    )

    feishu = FeishuBitableClient()
    feishu.sync_products(records)
    feishu.sync_jobs(jobs)

    metrics = summarize(records)
    ai_summary = ""
    if settings.ai_enabled:
        try:
            analyzer = DeepSeekAnalyzer(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
                model=settings.openai_model,
            )
            ai_summary = analyzer.generate_market_summary(records, metrics)
        except Exception as exc:
            print(f"ai_summary_warning={exc}")

    report_path = build_report(metrics, "output/market_report.md", ai_summary=ai_summary)
    brief_path = build_executive_brief(metrics, "output/executive_brief.md", ai_summary=ai_summary)
    dashboard_path = build_dashboard_snapshot(metrics, "output/dashboard_summary.json")
    kb_path = build_knowledge_base(records, "data/knowledge_base.json")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("MVP run complete")
    print(f"platforms={','.join(platforms)}")
    print(f"keywords={','.join(keywords)}")
    print(f"records={len(records)}")
    print(f"jobs={len(jobs)}")
    print(f"report={report_path}")
    print(f"brief={brief_path}")
    print(f"dashboard={dashboard_path}")
    print(f"knowledge_base={kb_path}")
    print(f"timestamp={datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    run()
