from uuid import UUID
from typing import Any, Protocol

from httpx import AsyncClient, HTTPError, Response

from ml_worker.core.config import GeminiSettings
from ml_worker.utils.gemini import extract_text_from_gemini_response
from ml_worker.schemas.text_generator import GenerationResult


class TextGenerator(Protocol):
    """The Contract: Any generator must follow this rule."""

    async def generate(self, prompt: str, interaction_id: UUID) -> GenerationResult: ...


class GeminiTextGenerator(TextGenerator):
    def __init__(self, settings: GeminiSettings):
        self._settings = settings

        if not self._settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required unless ML_WORKER_DRY_RUN=true")

    async def generate(self, prompt: str, interaction_id: UUID) -> GenerationResult:
        model = self._settings.GEMINI_MODEL

        endpoint = self._get_gemini_endpoint(self._settings.GEMINI_API_BASE, model)
        payload = self._get_gemini_payload(prompt)
        headers = self._get_gemini_headers(interaction_id)

        gemini_response = await self._execute_request(endpoint, payload, headers)

        text = extract_text_from_gemini_response(gemini_response.json())
        if not text:
            raise RuntimeError("Gemini response did not include text output")
        return GenerationResult(text=text, model=model, is_dry_run=False)

    async def _execute_request(
        self, endpoint: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> Response:
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

            return response

    @staticmethod
    def _get_gemini_endpoint(api_base: str, model: str) -> str:
        return f"{api_base}/models/{model}:generateContent"

    @staticmethod
    def _get_gemini_payload(prompt: str) -> dict[str, Any]:
        return {
            "contents": [{"parts": [{"text": prompt}]}],
        }

    @staticmethod
    def _get_gemini_headers(interaction_id) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Interaction-Id": interaction_id,
        }


class MockTextGenerator(TextGenerator):
    """Used when ML_WORKER_DRY_RUN=true"""

    async def generate(self, prompt: str, interaction_id: UUID) -> GenerationResult:
        text = f"[dry-run] Mocked response for {interaction_id}: {prompt}"
        return GenerationResult(text=text, model="", is_dry_run=True)
