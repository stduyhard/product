from app.analysis.metrics import summarize
from app.models import ProductRecord
from app.report.builder import build_report


def _build(price: float, brand: str, features: list[str], shop_type: str) -> ProductRecord:
    return ProductRecord(
        record_id=f"id-{price}-{brand}",
        platform="jd",
        keyword="泡脚桶",
        product_id=f"p-{price}",
        title=f"{brand} 泡脚桶",
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


def test_summarize_basic_metrics():
    records = [
        _build(199, "brand-a", ["massage"], "flagship"),
        _build(299, "brand-a", ["constant-temp"], "flagship"),
        _build(499, "brand-b", ["drain"], "specialty"),
    ]
    data = summarize(records)
    assert data["total"] == 3
    assert data["avg_price"] == 332.33
    assert data["price_band"]["0-199"] == 1
    assert data["price_band"]["200-399"] == 1
    assert data["price_band"]["400+"] == 1
    assert data["brand_top"][0][0] == "brand-a"


def test_build_report_outputs_readable_chinese(tmp_path):
    records = [
        _build(199, "美的", ["按摩", "恒温"], "flagship"),
        _build(299, "美的", ["排水"], "flagship"),
        _build(499, "飞利浦", ["杀菌"], "flagship"),
    ]
    metrics = summarize(records)
    report_path = build_report(metrics, str(tmp_path / "report.md"))
    content = (tmp_path / "report.md").read_text(encoding="utf-8")

    assert report_path.endswith("report.md")
    assert "泡脚桶市场调研报告" in content
    assert "关键结论" in content
    assert "品牌分布 TOP" in content
    assert "美的" in content
