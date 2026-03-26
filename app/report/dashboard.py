from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_dashboard_snapshot(metrics: dict[str, Any], output_path: str) -> str:
    payload = {
        "summary": {
            "total": metrics.get("total", 0),
            "avg_price": metrics.get("avg_price", 0),
        },
        "charts": {
            "brand_top": [
                {"brand": brand, "count": count}
                for brand, count in metrics.get("brand_top", [])
            ],
            "price_band": [
                {"band": band, "count": count}
                for band, count in metrics.get("price_band", {}).items()
            ],
            "feature_coverage": [
                {"feature": feature, "count": count}
                for feature, count in metrics.get("feature_coverage", {}).items()
            ],
            "shop_type_share": [
                {"shop_type": shop_type, "count": count}
                for shop_type, count in metrics.get("shop_type_share", {}).items()
            ],
        },
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
