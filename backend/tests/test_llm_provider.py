from app.domains.llm_search import provider as provider_module
from app.domains.llm_search.provider import JsonLlmProvider, sanitize_context


class _Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "answer": "채널 연결 상태와 최근 오류를 확인하세요.",
            "sources": [{"title": "Channels ERROR", "reference": "channels/ERROR.md"}],
            "confidence": "medium",
        }


def test_llm_provider_uses_json_contract_and_context_allowlist(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return _Response()

    monkeypatch.setattr(provider_module.settings, "llm_api_url", "http://llm.internal/analyze")
    monkeypatch.setattr(provider_module.requests, "post", fake_post)

    result = JsonLlmProvider().analyze(
        "ALT-1",
        "원인을 알려줘",
        {
            "sid": "POP",
            "title": "Receiver 오류",
            "detail": "연결 실패",
            "payload": "must-not-be-forwarded",
        },
    )

    assert captured["json"]["response_format"]["type"] == "json"
    assert captured["json"]["context"]["sid"] == "POP"
    assert "payload" not in captured["json"]["context"]
    assert result["answer"].startswith("채널")
    assert result["response_format"] == "json"


def test_context_sanitizer_drops_unapproved_fields() -> None:
    assert sanitize_context({"sid": "PMP", "token": "secret"}) == {"sid": "PMP"}
