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
