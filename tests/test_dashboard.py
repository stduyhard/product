import json

from app.analysis.metrics import summarize
from app.models import ProductRecord
from app.report.dashboard import build_dashboard_snapshot


def _build(price: float, brand: str, features: list[str], shop_type: str) -> ProductRecord:
    return ProductRecord(
        record_id=f"id-{price}-{brand}",
        platform="jd",
        keyword="???",
        product_id=f"p-{price}",
        title=f"{brand} ???",
        brand=brand,
        price_current=price,
        price_original=None,
        image_url="",
        product_url="",
        shop_name="shop",
        shop_type=shop_type,
        sales_or_reviews=10,
        capacity_l=12,
        heating_type="constant-temp",
        core_features=features,
    )


def test_build_dashboard_snapshot_writes_json(tmp_path):
    records = [
        _build(199, "??", ["??", "??"], "flagship"),
        _build(299, "??", ["??"], "flagship"),
        _build(499, "???", ["??"], "other"),
    ]
    metrics = summarize(records)
    out = tmp_path / 'dashboard.json'
    path = build_dashboard_snapshot(metrics, str(out))
    payload = json.loads(out.read_text(encoding='utf-8'))

    assert path.endswith('dashboard.json')
    assert payload['summary']['total'] == 3
    assert payload['charts']['brand_top'][0]['brand'] == '??'
    assert payload['charts']['price_band'][0]['band'] == '0-199'
