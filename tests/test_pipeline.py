from app.collector import pipeline


class _FakeCollector:
    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.config = type("Config", (), {"per_keyword_limit": 0})()

    def collect(self, keyword: str):
        return [
            {
                "product_id": f"{self.platform}-{keyword}-1",
                "title": f"{keyword} sample",
                "brand": "demo",
                "price_current": 199.0,
                "price_original": None,
                "image_url": "https://example.com/image.jpg",
                "product_url": "https://example.com/product",
                "shop_name": "demo-shop",
                "shop_type": "flagship",
                "sales_or_reviews": 1,
                "heating_type": "unknown",
                "core_features": [],
                "rating": None,
                "keyword": keyword,
            }
        ]


def test_collect_products_filters_platforms(monkeypatch):
    monkeypatch.setattr(pipeline, "JDCollector", lambda: _FakeCollector("jd"))
    monkeypatch.setattr(pipeline, "TmallCollector", lambda: _FakeCollector("tmall"))

    records, jobs = pipeline.collect_products(
        keywords=["???"],
        per_platform_limit=5,
        platforms=["jd"],
    )

    assert len(records) == 1
    assert records[0].platform == "jd"
    assert len(jobs) == 1
    assert jobs[0].platform == "jd"
