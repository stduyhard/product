from __future__ import annotations

from pathlib import Path
from typing import Any


def build_executive_brief(metrics: dict[str, Any], output_path: str, ai_summary: str = "") -> str:
    lines = [
        "# 泡脚桶项目简明结论",
        "",
        "## 核心建议",
        f"- 当前样本量：{metrics.get('total', 0)}",
        f"- 平均价格：{metrics.get('avg_price', 0)} 元",
        "- 建议优先聚焦 200-399 元主力款，并用 399 元以上高配款做锚点。",
        "- 卖点沟通优先围绕恒温、排水、按摩、安全清洁展开。",
    ]

    if ai_summary.strip():
        lines.extend(["", "## AI摘要", ai_summary.strip()])

    content = "\n".join(lines)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)
