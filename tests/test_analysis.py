from app.analysis.metrics import summarize
from app.models import ProductRecord


def _build(price: float, brand: str, features: list[str], shop_type: str) -> ProductRecord:
    return ProductRecord(
        record_id=f"id-{price}-{brand}",
        platform="jd",
        keyword="foot-bath-bucket",
        product_id=f"p-{price}",
        title=f"{brand} foot bath",
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