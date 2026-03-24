from datetime import UTC, datetime

from app.models import JobResult, ProductRecord
from app.settings import settings
from app.sync.feishu import FeishuBitableClient, _job_to_fields, _product_to_fields


def test_feishu_cn_fields_mapping():
    old = settings.feishu_use_cn_fields
    settings.feishu_use_cn_fields = True
    try:
        product = ProductRecord(
            record_id="jd:1",
            platform="jd",
            keyword="泡脚桶",
            product_id="1",
            title="test title",
            brand="midea",
            price_current=199.0,
            price_original=299.0,
            image_url="https://example.com/i.jpg",
            product_url="https://example.com/p",
            shop_name="shop",
            shop_type="flagship",
            sales_or_reviews=123,
            capacity_l=12.0,
            heating_type="恒温",
            core_features=["按摩", "排水"],
            capture_time=datetime.now(UTC),
        )
        fields = _product_to_fields(product)
        assert "记录ID" in fields
        assert fields["关键词"] == "泡脚桶"

        job = JobResult(
            job_id="jd-泡脚桶",
            run_time=datetime.now(UTC),
            platform="jd",
            keyword="泡脚桶",
            target_count=30,
            success_count=28,
            fail_count=2,
            status="success",
        )
        job_fields = _job_to_fields(job)
        assert "任务ID" in job_fields
        assert job_fields["状态"] == "success"
    finally:
        settings.feishu_use_cn_fields = old


def test_user_access_token_is_preferred():
    old = settings.feishu_user_access_token
    settings.feishu_user_access_token = "user-token"
    try:
        client = FeishuBitableClient()
        assert client._access_token() == "user-token"
    finally:
        settings.feishu_user_access_token = old
