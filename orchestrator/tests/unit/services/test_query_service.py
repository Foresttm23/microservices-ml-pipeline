import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from orchestrator.services.query_service import QueryService
from orchestrator.exceptions.orchestrator_errors import TaskEnqueueFailed
from orchestrator.schemas.query import QueryEntity
from shared.core import QueryState
from shared.schemas import ResultMessage

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_query_repo():
    return AsyncMock()

@pytest.fixture
def mock_response_repo():
    return AsyncMock()

@pytest.fixture
def mock_log_repo():
    return AsyncMock()

@pytest.fixture
def query_service(mock_session, mock_query_repo, mock_response_repo, mock_log_repo):
    with patch("orchestrator.services.query_service.get_settings") as mock_settings:
        mock_settings.return_value.DEFAULT_PAGINATION_LIMIT = 10
        mock_settings.return_value.MAX_PAGINATION_LIMIT = 50
        return QueryService(
            session=mock_session,
            repo=mock_query_repo,
            response_repo=mock_response_repo,
            log_repo=mock_log_repo
        )

@pytest.mark.asyncio
async def test_create_and_enqueue_task_success(query_service, mock_session, mock_query_repo):
    """Test successful task creation and enqueuing."""
    correlation_id = uuid4()
    user_id = "user-123"
    message = "Hello, world!"
    pipeline_id = "test-pipeline"
    
    with patch("orchestrator.services.query_service.QueuePublisher") as MockPublisher:
        mock_publisher_inst = MockPublisher.return_value
        mock_publisher_inst.publish = AsyncMock()
        
        query_id = await query_service.create_and_enqueue_task(
            correlation_id=correlation_id,
            user_id=user_id,
            message=message,
            pipeline_id=pipeline_id
        )
        
        # Verify DB interactions
        mock_query_repo.save.assert_called_once()
        mock_session.commit.assert_called_once()
        
        # Verify Redis interaction
        MockPublisher.assert_called_once()
        mock_publisher_inst.publish.assert_called_once()
        
        assert isinstance(query_id, type(uuid4()))

@pytest.mark.asyncio
async def test_create_and_enqueue_task_fails_on_publish(query_service, mock_session, mock_query_repo):
    """Test that failure to publish to Redis raises TaskEnqueueFailed."""
    correlation_id = uuid4()
    
    with patch("orchestrator.services.query_service.QueuePublisher") as MockPublisher:
        mock_publisher_inst = MockPublisher.return_value
        mock_publisher_inst.publish = AsyncMock(side_effect=Exception("Redis down"))
        
        with pytest.raises(TaskEnqueueFailed):
            await query_service.create_and_enqueue_task(
                correlation_id=correlation_id,
                user_id="user-123",
                message="test",
                pipeline_id="test-pipe"
            )

@pytest.mark.asyncio
async def test_handle_result_completed(query_service, mock_query_repo, mock_response_repo):
    """Test handling a COMPLETED result."""
    query = QueryEntity.create(user_id="u1", correlation_id=uuid4(), message="m1")
    result = ResultMessage(
        correlation_id=query.correlation_id,
        interaction_id=query.interaction_id,
        status=QueryState.COMPLETED,
        model="test-model",
        output_text="Success",
        tokens_used=10,
        user_id="u1",
        metadata={"query_id": str(query.id)}
    )
    
    await query_service.handle_result(query, result)
    
    assert query.state == QueryState.COMPLETED
    mock_response_repo.save.assert_called_once()
    mock_query_repo.save.assert_called_once_with(query)

@pytest.mark.asyncio
async def test_handle_result_failed(query_service, mock_query_repo, mock_log_repo):
    """Test handling a FAILED result."""
    query = QueryEntity.create(user_id="u1", correlation_id=uuid4(), message="m1")
    result = ResultMessage(
        correlation_id=query.correlation_id,
        interaction_id=query.interaction_id,
        status=QueryState.FAILED,
        model="test-model",
        error="Something went wrong",
        user_id="u1",
        metadata={"query_id": str(query.id)}
    )
    
    await query_service.handle_result(query, result)
    
    assert query.state == QueryState.FAILED
    mock_log_repo.save.assert_called_once()
    mock_query_repo.save.assert_called_once_with(query)

@pytest.mark.asyncio
async def test_get_user_chats_delegation(query_service, mock_query_repo):
    """Test get_user_chats delegates to the repository."""
    user_id = "user-123"
    mock_query_repo.get_chats_paginated.return_value = ([], 0)
    
    await query_service.get_user_chats(user_id)
    
    mock_query_repo.get_chats_paginated.assert_called_once_with(user_id, 0, 10)

@pytest.mark.asyncio
async def test_get_chat_messages_delegation(query_service, mock_query_repo):
    """Test get_chat_messages delegates to the repository."""
    user_id = "user-123"
    interaction_id = uuid4()
    mock_query_repo.get_chat_messages_paginated.return_value = ([], 0)
    
    await query_service.get_chat_messages(user_id, interaction_id)
    
    mock_query_repo.get_chat_messages_paginated.assert_called_once_with(user_id, interaction_id, 0, 10)
