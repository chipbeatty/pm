import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class AnthropicError(RuntimeError):
    pass


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


def check_connectivity() -> dict[str, str]:
    answer = ask_model("What is 2+2? Reply with only the number.")
    cleaned = answer.strip()
    if cleaned not in {"4", "4."}:
        raise AnthropicError(f"Unexpected connectivity response: {answer!r}")
    return {"model": ANTHROPIC_MODEL, "answer": "4"}
