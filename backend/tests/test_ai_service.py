import pytest

from app.ai_service import (
    ANTHROPIC_MODEL,
    AnthropicError,
    AIResponse,
    ask_model,
    apply_board_changes,
    build_board_ai_prompt,
    check_connectivity,
    generate_board_response,
    parse_structured_board_response,
)
from app.board import BoardData


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


def test_parse_structured_board_response_accepts_json_payload() -> None:
    result = parse_structured_board_response(
        '{"assistant": "Done", "changes": [{"type": "move_card", "cardId": "card-2", "columnId": "col-progress", "position": 0}]}'
    )

    assert result == AIResponse(
        assistant="Done",
        changes=[
            {
                "type": "move_card",
                "cardId": "card-2",
                "columnId": "col-progress",
                "position": 0,
            }
        ],
    )


def test_ai_response_requires_valid_json_and_schema() -> None:
    with pytest.raises(AnthropicError, match="valid JSON"):
        parse_structured_board_response("not json")

    with pytest.raises(AnthropicError, match="missing an assistant message"):
        parse_structured_board_response('{"changes": []}')

    with pytest.raises(AnthropicError, match="changes do not match"):
        parse_structured_board_response('{"assistant": "Done", "changes": [{"type": "bad"}]}')


def test_apply_board_changes_supports_create_edit_and_move() -> None:
    board = BoardData(
        id="board-1",
        columns=[
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
            {"id": "col-discovery", "title": "Discovery", "cardIds": []},
            {"id": "col-progress", "title": "In Progress", "cardIds": []},
            {"id": "col-review", "title": "Review", "cardIds": []},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        cards={
            "card-1": {"id": "card-1", "title": "Alpha", "details": "One"},
        },
    )

    result = apply_board_changes(
        board,
        [
            {"type": "create_card", "columnId": "col-discovery", "card": {"id": "card-2", "title": "Beta", "details": "Two"}},
            {"type": "edit_card", "cardId": "card-1", "title": "Alpha updated"},
            {"type": "move_card", "cardId": "card-1", "columnId": "col-progress", "position": 0},
        ],
    )

    assert result.cards["card-2"]["title"] == "Beta"
    assert result.cards["card-1"]["title"] == "Alpha updated"
    assert result.columns[2]["cardIds"] == ["card-1"]


def test_generate_board_response_returns_structured_ai_result(monkeypatch: pytest.MonkeyPatch) -> None:
    board = BoardData(
        id="board-1",
        columns=[
            {"id": "col-backlog", "title": "Backlog", "cardIds": []},
            {"id": "col-discovery", "title": "Discovery", "cardIds": []},
            {"id": "col-progress", "title": "In Progress", "cardIds": []},
            {"id": "col-review", "title": "Review", "cardIds": []},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        cards={},
    )

    def fake_ask_model(prompt: str) -> str:
        assert "User request: add a task" in prompt
        return '{"assistant": "Added a task.", "changes": [{"type": "create_card", "columnId": "col-backlog", "card": {"id": "card-99", "title": "Task", "details": "Details"}}]}'

    monkeypatch.setattr("app.ai_service.ask_model", fake_ask_model)

    response = generate_board_response(board, "add a task")

    assert response["assistant"] == "Added a task."
    assert response["board"].cards["card-99"]["title"] == "Task"
    assert response["changes"][0]["type"] == "create_card"


def test_build_board_ai_prompt_includes_history_and_board_state() -> None:
    board = BoardData(
        id="board-1",
        columns=[
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
            {"id": "col-discovery", "title": "Discovery", "cardIds": []},
            {"id": "col-progress", "title": "In Progress", "cardIds": []},
            {"id": "col-review", "title": "Review", "cardIds": []},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        cards={"card-1": {"id": "card-1", "title": "Task", "details": "Details"}},
    )

    prompt = build_board_ai_prompt(board, "move it", [{"role": "user", "content": "hello"}])

    assert "Current board:" in prompt
    assert "User request: move it" in prompt
    assert "user: hello" in prompt
    assert '"card-1"' in prompt
