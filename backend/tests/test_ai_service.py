import pytest

from app.ai_service import ANTHROPIC_MODEL, AnthropicError, ask_model, check_connectivity


def test_ask_model_uses_anthropic_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self) -> dict[str, object]:
            return {"content": [{"text": "4"}]}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: int):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("app.ai_service.httpx.post", fake_post)

    assert ask_model("What is 2+2?") == "4"
    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"]["x-api-key"] == "test-key"
    assert captured["json"]["model"] == ANTHROPIC_MODEL
    assert captured["timeout"] == 30


def test_missing_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(AnthropicError, match="ANTHROPIC_API_KEY is not configured"):
        ask_model("What is 2+2?")


def test_provider_errors_are_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        status_code = 401
        text = "invalid key"

        def json(self) -> dict[str, object]:
            return {}

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: int):
        return FakeResponse()

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr("app.ai_service.httpx.post", fake_post)

    with pytest.raises(AnthropicError, match="Anthropic request failed with status 401"):
        ask_model("What is 2+2?")


def test_connectivity_check_accepts_expected_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def fake_post(url: str, headers: dict[str, str], json: dict[str, object], timeout: int):
        class FakeResponse:
            status_code = 200
            text = ""

            def json(self) -> dict[str, object]:
                return {"content": [{"text": "4"}]}

        return FakeResponse()

    monkeypatch.setattr("app.ai_service.httpx.post", fake_post)

    assert check_connectivity() == {"model": ANTHROPIC_MODEL, "answer": "4"}
