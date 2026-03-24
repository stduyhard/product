from __future__ import annotations

import json
from pathlib import Path

from app.models import ProductRecord


def build_knowledge_base(records: list[ProductRecord], kb_path: str) -> str:
    rows = []
    for record in records:
        rows.append(
            {
                "question": f"{record.brand}泡脚桶有什么特点？",
                "answer": (
                    f"{record.title}，当前价格约{record.price_current}元，"
                    f"核心功能：{','.join(record.core_features) or '基础功能'}，"
                    f"店铺类型：{record.shop_type}。"
                ),
                "keywords": [record.brand, *record.core_features, record.keyword],
            }
        )
    out = Path(kb_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)


def load_knowledge_base(kb_path: str) -> list[dict[str, object]]:
    path = Path(kb_path)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

