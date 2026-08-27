import pytest
from unittest.mock import AsyncMock
from ml_worker.services.task_processor import TaskProcessor
from shared.schemas import TaskMessage, ResultMessage
from shared.core import QueryState
from uuid import uuid4

@pytest.fixture
def mock_runner():
    return AsyncMock()

@pytest.fixture
def mock_publisher():
    return AsyncMock()

@pytest.fixture
def task_processor(mock_runner, mock_publisher):
    return TaskProcessor(runner=mock_runner, publisher=mock_publisher)

@pytest.fixture
def task_message():
    return TaskMessage(
        correlation_id=uuid4(),
        user_id="user-123",
        prompt="Explain quantum physics",
        model="gemini-pro"
    )

@pytest.mark.asyncio
async def test_task_processor_process_success(task_processor, mock_runner, mock_publisher, task_message):
    """Test that TaskProcessor runs the task and publishes the result."""
    expected_result = ResultMessage(
        correlation_id=task_message.correlation_id,
        interaction_id=uuid4(),
        status=QueryState.COMPLETED,
        model="gemini-pro",
        output_text="Quantum physics is...",
        user_id="user-123"
    )
    mock_runner.run.return_value = expected_result
    
    result = await task_processor.process(task_message)
    
    # Assertions
    assert result == expected_result
    mock_runner.run.assert_called_once_with(task_message)
    mock_publisher.publish.assert_called_once()
    
    # Verify published content (json)
    published_arg = mock_publisher.publish.call_args[0][0]
    assert expected_result.model_dump_json() == published_arg

@pytest.mark.asyncio
async def test_task_processor_process_handles_runner_exception(task_processor, mock_runner, mock_publisher, task_message):
    """
    Test that TaskProcessor handles runner exceptions via the @task_wrapper.
    Note: The @task_wrapper is tested in test_task_wrapper.py, but here we verify 
    the interaction between TaskProcessor and the wrapper in a failing scenario.
    """
    mock_runner.run.side_effect = ValueError("Runner crashed")
    
    result = await task_processor.process(task_message)
    
    assert result.status == QueryState.FAILED
    assert result.error == "ml_processing_failed"
    mock_publisher.publish.assert_not_called() # Wrapper returns result, doesn't publish for us (processor publishes in its body)
