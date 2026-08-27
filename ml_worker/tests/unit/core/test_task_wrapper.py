import pytest
from unittest.mock import MagicMock
from uuid import uuid4, UUID
from ml_worker.core.exceptions.task_wrapper import task_wrapper
from shared.core import QueryState
from shared.schemas import ResultMessage

class MockService:
    @task_wrapper
    async def successful_task(self, message):
        return "success"

    @task_wrapper
    async def failing_task(self, message):
        raise ValueError("test error")

@pytest.fixture
def service():
    return MockService()

@pytest.fixture
def mock_message():
    message = MagicMock()
    message.correlation_id = uuid4()
    message.user_id = "user-123"
    message.interaction_id = uuid4()
    return message

@pytest.mark.asyncio
async def test_task_wrapper_success(service, mock_message):
    """Test that task_wrapper passes through successful results and sets context."""
    result = await service.successful_task(mock_message)
    assert result == "success"

@pytest.mark.asyncio
async def test_task_wrapper_failure_returns_result_message(service, mock_message):
    """Test that task_wrapper catches exceptions and returns a ResultMessage with FAILED status."""
    result = await service.failing_task(mock_message)
    
    assert isinstance(result, ResultMessage)
    assert result.status == QueryState.FAILED
    assert result.user_id == mock_message.user_id
    assert result.correlation_id == mock_message.correlation_id
    assert result.interaction_id == mock_message.interaction_id
    # "test error" is not in ML_ERROR_MAP probably, so it defaults to "ml_processing_failed"
    assert result.error == "ml_processing_failed"

@pytest.mark.asyncio
async def test_task_wrapper_handles_missing_ids(service):
    """Test that task_wrapper generates IDs if missing from message."""
    message = MagicMock(spec=[]) # No attributes
    
    result = await service.failing_task(message)
    
    assert isinstance(result.correlation_id, UUID)
    assert result.user_id == "anonymous"
    assert isinstance(result.interaction_id, UUID)
