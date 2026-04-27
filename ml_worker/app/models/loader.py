from typing import Any

from httpx import AsyncClient, HTTPError

from ..core.config import Settings


class GeminiModelLoader:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def generate_text(
        self,
        *,
        prompt: str,
        interaction_id: str,
        model: str | None = None,
    ) -> tuple[str, str, bool]:
        resolved_model = model or self._settings.GEMINI_MODEL

        if self._settings.ML_WORKER_DRY_RUN:
            return (
                f"[dry-run] Gemini response for interaction {interaction_id}: {prompt}",
                resolved_model,
                True,
            )

        if not self._settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required unless ML_WORKER_DRY_RUN=true")

        endpoint = (
            f"{self._settings.GEMINI_API_BASE}/models/{resolved_model}:generateContent"
        )
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
        }
        headers = {
            "Content-Type": "application/json",
            "X-Interaction-Id": interaction_id,
        }

        async with AsyncClient(timeout=self._settings.GEMINI_TIMEOUT_SECONDS) as client:
            response = await client.post(
                endpoint,
                params={"key": self._settings.GEMINI_API_KEY},
                json=payload,
                headers=headers,
            )
            try:
                response.raise_for_status()
            except HTTPError as exc:
                raise RuntimeError(f"Gemini request failed: {response.text}") from exc

            data = response.json()

        text = _extract_text(data)
        if not text:
            raise RuntimeError("Gemini response did not include text output")

        return text, resolved_model, False


def _extract_text(data: dict[str, Any]) -> str | None:
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
