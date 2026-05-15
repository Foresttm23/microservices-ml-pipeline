import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from orchestrator.services.result_processor import ResultProcessor
from shared.schemas import ResultMessage
from shared.core import QueryState
from orchestrator.exceptions.orchestrator_errors import ResultPublishFailed

@pytest.fixture
def mock_pubsub():
    return AsyncMock()

@pytest.fixture
def processor(mock_pubsub):
    return ResultProcessor(pubsub=mock_pubsub)

@pytest.fixture
def valid_result():
    return ResultMessage(
        correlation_id=uuid4(),
        interaction_id=uuid4(),
        status=QueryState.COMPLETED,
        model="test-model",
        output_text="Test response",
        user_id="user-1",
        metadata={"query_id": str(uuid4())}
    )

@pytest.mark.asyncio
async def test_extract_query_id_valid(processor, valid_result):
    """Test extracting query_id from valid result metadata."""
    query_id = processor._extract_query_id(valid_result)
    assert query_id == UUID(valid_result.metadata["query_id"])

@pytest.mark.asyncio
async def test_extract_query_id_missing(processor):
    """Test extracting query_id when missing from metadata."""
    result = ResultMessage(
        correlation_id=uuid4(),
        interaction_id=uuid4(),
        status=QueryState.COMPLETED,
        model="test-model",
        user_id="u1",
        metadata={}
    )
    query_id = processor._extract_query_id(result)
    assert query_id is None

@pytest.mark.asyncio
async def test_extract_query_id_invalid(processor):
    """Test extracting query_id with invalid UUID string."""
    result = ResultMessage(
        correlation_id=uuid4(),
        interaction_id=uuid4(),
        status=QueryState.COMPLETED,
        model="test-model",
        user_id="u1",
        metadata={"query_id": "not-a-uuid"}
    )
    query_id = processor._extract_query_id(result)
    assert query_id is None

@pytest.mark.asyncio
async def test_process_missing_query_id_early_return(processor, mock_pubsub):
    """Test process returns early when query_id is missing from metadata."""
    result = ResultMessage(
        correlation_id=uuid4(),
        interaction_id=uuid4(),
        status=QueryState.COMPLETED,
        model="test-model",
        user_id="u1",
        metadata={}
    )
    await processor.process(result)
    mock_pubsub.publish.assert_not_called()

@pytest.mark.asyncio
async def test_process_success(processor, mock_pubsub, valid_result):
    """Test successful result processing flow."""
    query_uuid = UUID(valid_result.metadata["query_id"])
    
    # Mocking DB session context manager
    mock_session = AsyncMock()
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = mock_session
    
    with patch("orchestrator.services.result_processor.db_session_manager.session", return_value=mock_session_cm):
        with patch("orchestrator.services.result_processor.QueryRepository") as MockQueryRepo, \
             patch("orchestrator.services.result_processor.QueryService") as MockQueryService:
            
            mock_repo = MockQueryRepo.return_value
            mock_repo.get_by_id = AsyncMock()
            
            mock_query = MagicMock()
            mock_query.state = QueryState.PENDING
            mock_query.user_id = "user-1"
            mock_repo.get_by_id.return_value = mock_query
            
            mock_service = MockQueryService.return_value
            mock_service.handle_result = AsyncMock()
            
            await processor.process(valid_result)
            
            # Verify retrieval and delegation
            mock_repo.get_by_id.assert_called_once_with(query_uuid)
            mock_service.handle_result.assert_called_once_with(mock_query, valid_result)
            mock_session.commit.assert_called_once()
            
            # Verify pub/sub publish
            mock_pubsub.publish.assert_called_once()

@pytest.mark.asyncio
async def test_process_query_not_found(processor, mock_pubsub, valid_result):
    """Test process skips when query is not found in DB."""
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = AsyncMock()
    
    with patch("orchestrator.services.result_processor.db_session_manager.session", return_value=mock_session_cm):
        with patch("orchestrator.services.result_processor.QueryRepository") as MockQueryRepo:
            mock_repo = MockQueryRepo.return_value
            mock_repo.get_by_id = AsyncMock(return_value=None)
            
            await processor.process(valid_result)
            
            mock_pubsub.publish.assert_not_called()

@pytest.mark.asyncio
async def test_process_publish_failure(processor, mock_pubsub, valid_result):
    """Test that failure to publish to Redis raises ResultPublishFailed."""
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = AsyncMock()
    mock_pubsub.publish.side_effect = Exception("Redis error")
    
    with patch("orchestrator.services.result_processor.db_session_manager.session", return_value=mock_session_cm):
        with patch("orchestrator.services.result_processor.QueryRepository") as MockQueryRepo, \
             patch("orchestrator.services.result_processor.QueryService") as MockQueryService:
            mock_repo = MockQueryRepo.return_value
            mock_repo.get_by_id = AsyncMock()
            
            mock_query = MagicMock()
            mock_query.state = QueryState.PENDING
            mock_repo.get_by_id.return_value = mock_query
            
            mock_service = MockQueryService.return_value
            mock_service.handle_result = AsyncMock()
            
            with pytest.raises(ResultPublishFailed):
                await processor.process(valid_result)

@pytest.mark.asyncio
async def test_process_query_not_pending(processor, mock_pubsub, valid_result):
    """Test process skips when query state is not PENDING."""
    mock_session_cm = MagicMock()
    mock_session_cm.__aenter__.return_value = AsyncMock()
    
    with patch("orchestrator.services.result_processor.db_session_manager.session", return_value=mock_session_cm):
        with patch("orchestrator.services.result_processor.QueryRepository") as MockQueryRepo:
            mock_repo = MockQueryRepo.return_value
            mock_repo.get_by_id = AsyncMock()
            
            mock_query = MagicMock()
            mock_query.state = QueryState.COMPLETED # Not PENDING
            mock_repo.get_by_id.return_value = mock_query
            
            await processor.process(valid_result)
            
            mock_pubsub.publish.assert_not_called()
