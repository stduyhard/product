from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.analysis.metrics import summarize
from app.bot.kb import build_knowledge_base
from app.collector.pipeline import collect_products
from app.report.builder import build_report
from app.sync.feishu import FeishuBitableClient

DEFAULT_KEYWORDS = [
    "\u6ce1\u811a\u6876",
    "\u8db3\u6d74\u76c6",
    "\u6052\u6e29\u8db3\u6d74\u6876",
    "\u6298\u53e0\u6ce1\u811a\u6876",
]


def _load_keywords(config_path: str = "config/keywords.json") -> list[str]:
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_KEYWORDS

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    raw = payload.get("keywords", []) if isinstance(payload, dict) else []
    keywords = [str(item).strip() for item in raw if str(item).strip()]
    return keywords or DEFAULT_KEYWORDS


def run() -> None:
    keywords = _load_keywords()
    records, jobs = collect_products(keywords=keywords, per_platform_limit=30)

    feishu = FeishuBitableClient()
    feishu.sync_products(records)
    feishu.sync_jobs(jobs)

    metrics = summarize(records)
    report_path = build_report(metrics, "output/market_report.md")
    kb_path = build_knowledge_base(records, "data/knowledge_base.json")

    print("MVP run complete")
    print(f"keywords={','.join(keywords)}")
    print(f"records={len(records)}")
    print(f"jobs={len(jobs)}")
    print(f"report={report_path}")
    print(f"knowledge_base={kb_path}")
    print(f"timestamp={datetime.now(UTC).isoformat()}")


if __name__ == "__main__":
    run()