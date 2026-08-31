import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from httpx import HTTPError, Request, Response

from ml_worker.core.config import GeminiSettings
from ml_worker.core.exceptions.definitions import (
    ModelInitializationFailed,
    ProviderRequestFailed,
    ProviderResponseInvalid,
)
from ml_worker.infra.gemini_adapter import GeminiTextGenerator, MockTextGenerator


def test_gemini_text_generator_init_missing_api_key():
    settings = GeminiSettings(API_KEY=None, ML_WORKER_DRY_RUN=False)
    with pytest.raises(ModelInitializationFailed):
        GeminiTextGenerator(settings)


@pytest.mark.asyncio
async def test_mock_text_generator_generate():
    generator = MockTextGenerator()
    interaction_id = uuid4()
    result = await generator.generate(prompt="What is AI?", interaction_id=interaction_id)

    assert result.is_dry_run is True
    assert f"Mocked response for {interaction_id}" in result.text


@pytest.mark.asyncio
@patch("ml_worker.infra.gemini_adapter.get_redis_client")
async def test_gemini_text_generator_generate_success(mock_get_redis):
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_get_redis.return_value = mock_redis

    settings = GeminiSettings(API_KEY="test-key", MODEL="gemini-2.0-flash")
    generator = GeminiTextGenerator(settings)

    interaction_id = uuid4()
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Gemini response text"}]
                }
            }
        ],
        "usageMetadata": {"totalTokenCount": 25},
    }

    with patch.object(generator, "_execute_request", return_value=mock_response) as mock_exec:
        result = await generator.generate(prompt="Hello Gemini", interaction_id=interaction_id)

        assert result.text == "Gemini response text"
        assert result.model == "gemini-2.0-flash"
        assert result.is_dry_run is False
        assert result.tokens_used == 25
        mock_exec.assert_called_once()
        mock_redis.set.assert_called_once()


@pytest.mark.asyncio
@patch("ml_worker.infra.gemini_adapter.get_redis_client")
async def test_gemini_text_generator_generate_invalid_response(mock_get_redis):
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_get_redis.return_value = mock_redis

    settings = GeminiSettings(API_KEY="test-key")
    generator = GeminiTextGenerator(settings)

    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"candidates": []}

    with patch.object(generator, "_execute_request", return_value=mock_response):
        with pytest.raises(ProviderResponseInvalid):
            await generator.generate(prompt="Hello", interaction_id=uuid4())


@pytest.mark.asyncio
@patch("ml_worker.infra.gemini_adapter.get_redis_client")
async def test_gemini_text_generator_with_existing_history(mock_get_redis):
    existing_history = [{"role": "user", "parts": [{"text": "Previous prompt"}]}]
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(existing_history)
    mock_get_redis.return_value = mock_redis

    settings = GeminiSettings(API_KEY="test-key")
    generator = GeminiTextGenerator(settings)

    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Next response"}]}}]
    }

    with patch.object(generator, "_execute_request", return_value=mock_response) as mock_exec:
        result = await generator.generate(prompt="Follow up", interaction_id=uuid4())
        assert result.text == "Next response"
        # Verify the history contains previous prompt, follow up, and model response
        payload = mock_exec.call_args[0][1]
        assert len(payload["contents"]) == 3
        assert payload["contents"][0]["role"] == "user"
        assert payload["contents"][1]["role"] == "user"
        assert payload["contents"][2]["role"] == "model"
