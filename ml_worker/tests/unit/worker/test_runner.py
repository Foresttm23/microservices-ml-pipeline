import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from ml_worker.worker.runner import InferenceRunner
from ml_worker.schemas.text_generator import GenerationResult
from shared.core import QueryState
from shared.schemas import TaskMessage, ResultMessage

@pytest.fixture
def mock_loader():
    loader = AsyncMock()
    return loader

@pytest.fixture
def runner(mock_loader):
    return InferenceRunner(loader=mock_loader)

@pytest.fixture
def task_message():
    return TaskMessage(
        correlation_id=uuid4(),
        user_id="user-123",
        prompt="Test prompt",
        model="test-model"
    )

@pytest.mark.asyncio
async def test_inference_runner_success(runner, mock_loader, task_message):
    """Test successful inference run."""
    gen_result = GenerationResult(
        text="Response text",
        model="test-model",
        tokens_used=15,
        is_dry_run=False
    )
    mock_loader.generate_text.return_value = gen_result
    
    result = await runner.run(task_message)
    
    assert isinstance(result, ResultMessage)
    assert result.status == QueryState.COMPLETED
    assert result.output_text == "Response text"
    assert result.tokens_used == 15
    assert result.correlation_id == task_message.correlation_id
    mock_loader.generate_text.assert_called_once()

@pytest.mark.asyncio
async def test_inference_runner_dry_run(runner, mock_loader, task_message):
    """Test inference run in dry run mode."""
    gen_result = GenerationResult(
        text="Mocked text",
        model="mock-model",
        tokens_used=0,
        is_dry_run=True
    )
    mock_loader.generate_text.return_value = gen_result
    
    result = await runner.run(task_message)
    
    assert result.status == QueryState.MOCKED
    assert result.model == "mock-model"

@pytest.mark.asyncio
async def test_inference_runner_failure(runner, mock_loader, task_message):
    """Test inference run with exception."""
    mock_loader.generate_text.side_effect = Exception("API Error")
    
    result = await runner.run(task_message)
    
    assert result.status == QueryState.FAILED
    assert result.error == "ml_processing_failed"
    assert result.correlation_id == task_message.correlation_id
