from typing import Any


def extract_text_from_gemini_response(data: dict[str, Any]) -> str | None:
    """Extract text content from a Gemini API response payload."""
    candidates = data.get("candidates")
    if not candidates:
        return None

    first = candidates[0]
    content = first.get("content") or {}
    parts = content.get("parts") or []
    for part in parts:
        text = part.get("text")
        if text:
            return str(text)
    return None


def extract_tokens_from_gemini_response(data: dict[str, Any]) -> int | None:
    """Extract token usage counts from a Gemini API response payload."""
    usage = data.get("usageMetadata") or {}
    total_tokens = usage.get("totalTokenCount")
    if total_tokens is None:
        prompt_tokens = usage.get("promptTokenCount")
        candidate_tokens = usage.get("candidatesTokenCount")
        if prompt_tokens is None and candidate_tokens is None:
            return None
        total_tokens = (prompt_tokens or 0) + (candidate_tokens or 0)

    try:
        return int(total_tokens)
    except (TypeError, ValueError):
        return None
