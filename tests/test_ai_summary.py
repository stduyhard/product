from app.analysis.ai_summary import DeepSeekAnalyzer, _chat_completions_url
from app.analysis.metrics import summarize
from app.models import ProductRecord
from app.report.builder import build_report


class _FakeAIMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls: list[object] = []

    def invoke(self, messages):
        self.calls.append(messages)
        return _FakeAIMessage(self.content)


def _build(price: float, brand: str) -> ProductRecord:
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
        shop_type="flagship",
        sales_or_reviews=10,
        capacity_l=12,
        heating_type="constant-temp",
        core_features=["??", "??"],
    )


def test_chat_completions_url_accepts_base_or_full_path():
    assert _chat_completions_url("https://api.deepseek.com") == "https://api.deepseek.com/chat/completions"
    assert _chat_completions_url("https://api.deepseek.com/v1") == "https://api.deepseek.com/v1/chat/completions"
    assert _chat_completions_url("https://api.deepseek.com/chat/completions") == "https://api.deepseek.com/chat/completions"


def test_deepseek_analyzer_uses_llm_invoke():
    llm = _FakeLLM("???? 200-399 ????????????????")
    analyzer = DeepSeekAnalyzer(
        api_key='test-key',
        base_url='https://api.deepseek.com/chat/completions',
        model='deepseek-chat',
        llm=llm,
    )
    records = [_build(299, '??'), _build(399, '???')]
    metrics = summarize(records)

    content = analyzer.generate_market_summary(records, metrics)

    assert '200-399' in content
    assert len(llm.calls) == 1


def test_deepseek_analyzer_answers_consulting_query_via_llm():
    llm = _FakeLLM("?????????????????")
    analyzer = DeepSeekAnalyzer(
        api_key='test-key',
        base_url='https://api.deepseek.com/chat/completions',
        model='deepseek-chat',
        llm=llm,
    )

    answer = analyzer.answer_product_question('???????')

    assert '??' in answer
    assert len(llm.calls) == 1


def test_build_report_appends_ai_section(tmp_path):
    metrics = summarize([_build(299, '??')])
    path = tmp_path / 'report.md'
    build_report(metrics, str(path), ai_summary='???????????????')
    content = path.read_text(encoding='utf-8')

    assert 'AI分析结论' in content
    assert '???????????????' in content
