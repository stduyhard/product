from app.analysis.metrics import summarize
from app.models import ProductRecord
from app.report.brief import build_executive_brief


def _build(price: float, brand: str) -> ProductRecord:
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
        shop_type="flagship",
        sales_or_reviews=10,
        capacity_l=12,
        heating_type="constant-temp",
        core_features=["按摩", "恒温"],
    )


def test_build_executive_brief_outputs_one_page_summary(tmp_path):
    metrics = summarize([_build(299, '美的'), _build(499, '飞利浦')])
    out = tmp_path / 'brief.md'
    path = build_executive_brief(metrics, str(out), ai_summary='建议主推 200-399 元主力款。')
    content = out.read_text(encoding='utf-8')

    assert path.endswith('brief.md')
    assert '泡脚桶项目简明结论' in content
    assert '核心建议' in content
    assert '200-399' in content
