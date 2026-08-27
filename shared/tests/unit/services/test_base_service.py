import pytest
from unittest.mock import AsyncMock
from pydantic import BaseModel
from shared.services.base import BaseService
from shared.repositories.base import BaseRepository

# Mock definitions for testing the abstract base class
class MockEntity(BaseModel):
    id: str | None = None
    name: str

class MockService(BaseService[MockEntity, BaseRepository]):
    """Concrete implementation of BaseService for testing base logic."""
    pass

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_repo():
    return AsyncMock(spec=BaseRepository)

@pytest.fixture
def service(mock_session, mock_repo):
    return MockService(mock_session, mock_repo)

@pytest.mark.asyncio
async def test_base_service_initialization(mock_session, mock_repo):
    """
    Test that BaseService correctly initializes with session and repository.
    This ensures the 'Main Implementation' of the base class works.
    """
    service = MockService(mock_session, mock_repo)
    assert service.session == mock_session
    assert service.repo == mock_repo

@pytest.mark.asyncio
async def test_base_service_get_by_id_delegation(service, mock_repo):
    """
    Test that get_by_id delegates correctly to the repository.
    This is core shared logic that all subclasses will inherit.
    """
    entity_id = "test-id"
    expected_entity = MockEntity(id=entity_id, name="Test Name")
    mock_repo.get_by_id.return_value = expected_entity

    result = await service.get_by_id(entity_id)

    assert result == expected_entity
    mock_repo.get_by_id.assert_called_once_with(entity_id)

@pytest.mark.asyncio
async def test_base_service_get_by_id_not_found(service, mock_repo):
    """Test get_by_id when the repository returns None."""
    mock_repo.get_by_id.return_value = None
    
    result = await service.get_by_id("missing")
    
    assert result is None
    mock_repo.get_by_id.assert_called_once_with("missing")
