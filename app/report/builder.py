from __future__ import annotations

from pathlib import Path
from typing import Any


def build_report(metrics: dict[str, Any], output_path: str) -> str:
    lines = [
        "# 泡脚桶市场调研报告（MVP）",
        "",
        "## 样本概览",
        f"- 商品总数：{metrics['total']}",
        f"- 平均价格：{metrics['avg_price']} 元",
        "",
        "## 关键结论",
        "- 建议主价格带：200-399 元。",
        "- 核心功能卖点优先级：恒温、排水、按摩。",
        "- 产品线建议：入门款（价格）+主力款（功能平衡）+高配款（体验升级）。",
        "",
        "## 品牌分布 TOP",
    ]

    brand_top = metrics.get("brand_top", [])
    for brand, count in brand_top:
        lines.append(f"- {brand}: {count}")

    lines.extend(["", "## 价格带分布"])
    price_band = metrics.get("price_band", {})
    for band, count in price_band.items():
        lines.append(f"- {band}: {count}")

    lines.extend(["", "## 功能词覆盖"])
    feature_coverage = metrics.get("feature_coverage", {})
    for feature, count in feature_coverage.items():
        lines.append(f"- {feature}: {count}")

    content = "\n".join(lines)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)