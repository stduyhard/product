from app.bot.deepseek import DeepSeekConsultingResponder


class _FakeAnalyzer:
    def __init__(self, answer: str) -> None:
        self.answer_text = answer
        self.queries: list[str] = []

    def answer_product_question(self, query: str) -> str:
        self.queries.append(query)
        return self.answer_text


def test_consulting_responder_delegates_to_analyzer_question_answering():
    analyzer = _FakeAnalyzer("建议优先看恒温和排水设计。")
    responder = DeepSeekConsultingResponder(analyzer)  # type: ignore[arg-type]

    answer = responder.answer("泡脚桶怎么选？")

    assert answer == "建议优先看恒温和排水设计。"
    assert analyzer.queries == ["泡脚桶怎么选？"]
