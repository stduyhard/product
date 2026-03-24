from app.collector.normalizer import extract_capacity_l, normalize_record


def test_extract_capacity_l():
    assert extract_capacity_l("家用泡脚桶 15L 恒温") == 15.0


def test_normalize_record_generates_expected_fields():
    raw = {
        "product_id": "abc-1",
        "title": "美的泡脚桶 恒温 12L 按摩",
        "brand": "Midea",
        "price_current": 269,
        "image_url": "https://example.com/i.jpg",
        "product_url": "https://example.com/p",
        "shop_name": "midea-flagship",
        "shop_type": "flagship",
        "sales_or_reviews": 1200,
    }
    record = normalize_record("jd", "泡脚桶", raw)
    assert record.record_id == "jd:abc-1"
    assert record.brand == "midea"
    assert record.capacity_l == 12.0
    assert "按摩" in record.core_features
    assert record.data_quality_flag == "normal"