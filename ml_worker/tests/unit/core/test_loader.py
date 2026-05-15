import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from ml_worker.core.loader import GeminiModelLoader
from ml_worker.schemas.text_generator import GenerationResult

@pytest.fixture
def mock_settings():
    return MagicMock()

@pytest.fixture
def mock_generator():
    return AsyncMock()

@pytest.fixture
def loader(mock_settings, mock_generator):
    return GeminiModelLoader(settings=mock_settings, generator=mock_generator)

@pytest.mark.asyncio
async def test_gemini_model_loader_generate_text_delegation(loader, mock_generator):
    """Test that GeminiModelLoader delegates to the generator."""
    prompt = "Test prompt"
    interaction_id = uuid4()
    expected_result = GenerationResult(
        text="Response",
        model="gemini",
        is_dry_run=False,
        tokens_used=10
    )
    mock_generator.generate.return_value = expected_result
    
    result = await loader.generate_text(prompt, interaction_id)
    
    assert result == expected_result
    mock_generator.generate.assert_called_once_with(prompt, interaction_id)
