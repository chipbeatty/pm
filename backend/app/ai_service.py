import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.board import BoardCard, BoardData

ANTHROPIC_MODEL = "claude-haiku-5-5"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class AnthropicError(RuntimeError):
    pass


class AIBoardChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    cardId: str | None = None
    columnId: str | None = None
    position: int | None = None
    title: str | None = None
    details: str | None = None
    card: dict[str, str] | None = None

    @property
    def change_type(self) -> str:
        return self.type

    @model_validator(mode="after")
    def validate_change_shape(self) -> "AIBoardChange":
        if self.type == "create_card":
            if not self.columnId or not self.card:
                raise ValueError("create_card requires a columnId and a card object.")
            if not self.card.get("id") or not self.card.get("title"):
                raise ValueError("create_card requires a card id and title.")
        elif self.type == "edit_card":
            if not self.cardId:
                raise ValueError("edit_card requires a cardId.")
            if self.title is None and self.details is None:
                raise ValueError("edit_card requires at least one field to edit.")
        elif self.type == "move_card":
            if not self.cardId or not self.columnId:
                raise ValueError("move_card requires a cardId and columnId.")
        else:
            raise ValueError("AI change type must be one of: create_card, edit_card, move_card.")
        return self


class AIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assistant: str = Field(min_length=1)
    changes: list[AIBoardChange] = Field(default_factory=list)


def get_api_key() -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise AnthropicError("ANTHROPIC_API_KEY is not configured.")
    return api_key


def ask_model(prompt: str) -> str:
    api_key = get_api_key()
    response = httpx.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 256,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=30,
    )

    if response.status_code >= 400:
        raise AnthropicError(
            f"Anthropic request failed with status {response.status_code}: {response.text}"
        )

    payload = response.json()
    try:
        content = payload["content"]
        if not isinstance(content, list):
            raise TypeError("content is not a list")
        message_content = content[0]["text"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise AnthropicError("Anthropic returned an unexpected response payload.") from exc

    if isinstance(message_content, str):
        return message_content.strip()

    raise AnthropicError("Anthropic returned a non-text response payload.")


def parse_structured_board_response(raw_response: str) -> AIResponse:
    candidate = raw_response.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        if candidate.lower().startswith("json"):
            candidate = candidate[4:].lstrip()
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise AnthropicError("AI response was not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise AnthropicError("AI response must be a JSON object.")

    assistant = (
        payload.get("assistant")
        or payload.get("response")
        or payload.get("text")
        or payload.get("message")
        or payload.get("answer")
        or ""
    )
    if not isinstance(assistant, str) or not assistant.strip():
        raise AnthropicError("AI response is missing an assistant message.")

    changes = (
        payload.get("changes")
        or payload.get("board_changes")
        or payload.get("boardChanges")
        or payload.get("operations")
        or []
    )
    if changes is None:
        changes = []
    if not isinstance(changes, list):
        raise AnthropicError("AI response changes must be a list.")

    try:
        validated_changes = [AIBoardChange.model_validate(change) for change in changes]
        return AIResponse(assistant=assistant, changes=validated_changes)
    except ValidationError as exc:
        raise AnthropicError(
            "AI response changes do not match the expected board-operation schema."
        ) from exc


def build_board_ai_prompt(board: BoardData, user_message: str, history: list[dict[str, str]] | None = None) -> str:
    history_text = ""
    if history:
        history_text = "\n".join(
            f"{entry.get('role','user')}: {entry.get('content','')}" for entry in history
        )
    board_json = json.dumps(board.model_dump(mode="json"), indent=2)
    return f"""
You are the project board assistant. Use the user's request and the current board state.
Return JSON only in this exact shape:
{{
  "assistant": "a brief human-readable response",
  "changes": [
    {{"type": "create_card", "columnId": "col-backlog", "card": {{"id": "card-99", "title": "New task", "details": "Details"}}}},
    {{"type": "edit_card", "cardId": "card-1", "title": "Updated title", "details": "Updated details"}},
    {{"type": "move_card", "cardId": "card-2", "columnId": "col-progress", "position": 0}}
  ]
}}
Rules:
- Only use the allowed change types: create_card, edit_card, move_card.
- For create_card, provide a new card id and card object.
- For edit_card, include only fields you want to change.
- For move_card, include the cardId, the destination columnId, and a valid integer position.
- If no board change is needed, use "changes": [].
- Do not return markdown fences.
Current board:
{board_json}
Conversation history:
{history_text or 'No prior messages.'}
User request: {user_message}
"""


def apply_board_changes(board: BoardData, changes: list[AIBoardChange] | list[dict[str, Any]]) -> BoardData:
    if not changes:
        return board

    normalized_changes = [
        AIBoardChange.model_validate(change) if isinstance(change, dict) else change
        for change in changes
    ]

    updated = board.model_copy(deep=True)
    columns_by_id = {column.id: column for column in updated.columns}

    for change in normalized_changes:
        change_type = change.type
        if change_type == "create_card":
            if not change.card or not change.columnId:
                raise AnthropicError("create_card requires a card and a columnId.")
            card_data = change.card
            card_id = card_data.get("id")
            title = card_data.get("title")
            details = card_data.get("details", "")
            if not card_id or not isinstance(card_id, str) or not title or not isinstance(title, str):
                raise AnthropicError("create_card requires a valid card id and title.")
            if card_id in updated.cards:
                raise AnthropicError(f"Card {card_id} already exists.")
            column = columns_by_id.get(change.columnId)
            if column is None:
                raise AnthropicError(f"Unknown column id: {change.columnId}.")
            updated.cards[card_id] = BoardCard.model_validate({
                "id": card_id,
                "title": title,
                "details": details,
            })
            column.cardIds.append(card_id)
        elif change_type == "edit_card":
            if not change.cardId:
                raise AnthropicError("edit_card requires a cardId.")
            card = updated.cards.get(change.cardId)
            if card is None:
                raise AnthropicError(f"Unknown card id: {change.cardId}.")
            if change.title is not None:
                card["title"] = change.title
            if change.details is not None:
                card["details"] = change.details
        elif change_type == "move_card":
            if not change.cardId or not change.columnId:
                raise AnthropicError("move_card requires a cardId and columnId.")
            source_column = next(
                (column for column in updated.columns if change.cardId in column.cardIds),
                None,
            )
            if source_column is None:
                raise AnthropicError(f"Card {change.cardId} is not on the board.")
            destination_column = columns_by_id.get(change.columnId)
            if destination_column is None:
                raise AnthropicError(f"Unknown column id: {change.columnId}.")
            source_column.cardIds = [card_id for card_id in source_column.cardIds if card_id != change.cardId]
            destination_index = change.position if change.position is not None else len(destination_column.cardIds)
            destination_column.cardIds.insert(
                max(0, min(destination_index, len(destination_column.cardIds))),
                change.cardId,
            )
        else:
            raise AnthropicError(f"Unsupported AI board change type: {change_type}.")

    validated = BoardData.model_validate(updated.model_dump(mode="json"))
    return validated


def generate_board_response(board: BoardData, user_message: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    prompt = build_board_ai_prompt(board, user_message, history)
    raw_response = ask_model(prompt)
    structured = parse_structured_board_response(raw_response)
    updated_board = apply_board_changes(board, structured.changes)
    return {
        "assistant": structured.assistant,
        "message": structured.assistant,
        "changes": [change.model_dump(mode="json") for change in structured.changes],
        "board": updated_board,
    }


def check_connectivity() -> dict[str, str]:
    answer = ask_model("What is 2+2? Reply with only the number.")
    cleaned = answer.strip()
    if cleaned not in {"4", "4."}:
        raise AnthropicError(f"Unexpected connectivity response: {answer!r}")
    return {"model": ANTHROPIC_MODEL, "answer": "4"}
