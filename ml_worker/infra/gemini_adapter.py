import json
from typing import Any, Protocol
from uuid import UUID

from httpx import AsyncClient, HTTPError, Response
from loguru import logger
from redis.asyncio import Redis

from ml_worker.core.config import GeminiSettings
from ml_worker.core.exceptions.definitions import (
    ModelInitializationFailed,
    ProviderRequestFailed,
    ProviderResponseInvalid,
)
from ml_worker.schemas.text_generator import GenerationResult
from ml_worker.utils.gemini import (
    extract_text_from_gemini_response,
    extract_tokens_from_gemini_response,
)
from shared.messaging import get_redis_client


class TextGenerator(Protocol):
    """The Contract: Any generator must follow this rule."""

    async def generate(self, prompt: str, interaction_id: UUID) -> GenerationResult: ...


class GeminiTextGenerator(TextGenerator):
    def __init__(self, settings: GeminiSettings):
        self._settings = settings

        if not self._settings.API_KEY:
            raise ModelInitializationFailed(
                "API_KEY is required unless ML_WORKER_DRY_RUN=true"
            )

    async def generate(self, prompt: str, interaction_id: UUID) -> GenerationResult:
        model = self._settings.MODEL

        endpoint = self._get_gemini_endpoint(self._settings.API_BASE, model)


        redis_client = get_redis_client()
        redis_key = f"interaction:{interaction_id}:history"
        contents = await self._get_contents_context(redis_client, redis_key)

        contents.append({"role": "user", "parts": [{"text": prompt}]})
        payload = {
            "system_instruction": self._get_system_instruction(),
            "contents": contents,
        }

        headers = self._get_gemini_headers(interaction_id)

        logger.debug("Calling Gemini model {}", model)
        gemini_response = await self._execute_request(endpoint, payload, headers)

        response_payload = gemini_response.json()
        text = extract_text_from_gemini_response(response_payload)
        if not text:
            raise ProviderResponseInvalid("Gemini response did not include text output")

        contents.append({"role": "model", "parts": [{"text": text}]})
        await self._set_contents_context(redis_client, redis_key, contents)

        tokens_used = extract_tokens_from_gemini_response(response_payload)
        return GenerationResult(
            text=text,
            model=model,
            is_dry_run=False,
            tokens_used=tokens_used,
        )

    @staticmethod
    def _get_system_instruction() -> dict[str, Any]:
        return {
            "parts": [
                {
                    "text": "You are a helpful conversational AI assistant. Engage the user directly and concisely. Do not output your internal reasoning or analysis of the prompt, just respond appropriately to the user."
                }
            ]
        }

    @staticmethod
    async def _get_contents_context(
        redis_client: Redis, redis_key: str
    ) -> list[dict[str, Any]]:
        history_json = await redis_client.get(redis_key)
        if history_json:
            contents = json.loads(history_json)
        else:
            contents = []

        return contents

    @staticmethod
    async def _set_contents_context(
        redis_client: Redis,
        redis_key: str,
        contents: list[dict[str, Any]],
        ex: int = 86400,
    ) -> None:
        await redis_client.set(redis_key, json.dumps(contents), ex=ex)

    async def _execute_request(
        self, endpoint: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> Response:
        async with AsyncClient(timeout=self._settings.TIMEOUT_SECONDS) as client:
            response = await client.post(
                endpoint,
                params={"key": self._settings.API_KEY},
                json=payload,
                headers=headers,
            )
            try:
                response.raise_for_status()
            except HTTPError as exc:
                logger.warning(
                    "Gemini request failed with status {}", response.status_code
                )
                raise ProviderRequestFailed(
                    f"Gemini request failed: {response.text}"
                ) from exc

            logger.debug("Gemini response status {}", response.status_code)
            return response

    @staticmethod
    def _get_gemini_endpoint(api_base: str, model: str) -> str:
        return f"{api_base}/models/{model}:generateContent"

    @staticmethod
    def _get_gemini_headers(interaction_id: UUID) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Interaction-Id": str(interaction_id),
        }


class MockTextGenerator(TextGenerator):
    """Used when ML_WORKER_DRY_RUN=true"""

    async def generate(self, prompt: str, interaction_id: UUID) -> GenerationResult:
        text = f"[dry-run] Mocked response for {interaction_id}: {prompt}"
        return GenerationResult(text=text, model="", is_dry_run=True, tokens_used=None)
