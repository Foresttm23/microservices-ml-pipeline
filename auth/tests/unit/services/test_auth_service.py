import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from auth.services.auth_service import AuthService
from auth.exceptions.auth_errors import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    RefreshTokenExpired,
)
from auth.schemas.user import UserEntity
from auth.schemas.token import RefreshTokenEntity

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def mock_token_repo():
    return AsyncMock()

@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.JWT_SECRET_KEY = "secret"
    settings.JWT_ALGORITHM = "HS256"
    settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15
    settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
    settings.JWT_ISSUER = "test-issuer"
    settings.JWT_AUDIENCE = "test-audience"
    settings.JWT_LEEWAY_SECONDS = 0
    return settings

@pytest.fixture
def service(mock_session, mock_user_repo, mock_token_repo, mock_settings):
    # BaseService uses self.repo, which is mock_user_repo here
    return AuthService(
        session=mock_session,
        user_repo=mock_user_repo,
        token_repo=mock_token_repo,
        settings=mock_settings
    )

@pytest.mark.asyncio
async def test_register_user_delta(service, mock_user_repo, mock_session):
    """Test register_user orchestration (Delta)."""
    email = "test@example.com"
    password = "password123"
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.save.side_effect = lambda x: x
    
    with patch("auth.services.auth_service.password_hash") as mock_pwd:
        mock_pwd.hash.return_value = "hashed_pwd"
        user = await service.register_user(email, password)
    
    assert user.email == email
    assert user.hashed_password == "hashed_pwd"
    mock_user_repo.get_by_email.assert_called_once_with(email)
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_register_user_already_registered(service, mock_user_repo):
    mock_user_repo.get_by_email.return_value = MagicMock(spec=UserEntity)
    
    with pytest.raises(EmailAlreadyRegistered):
        await service.register_user("exists@example.com", "pass")

@pytest.mark.asyncio
async def test_authenticate_user_success(service, mock_user_repo):
    user = MagicMock(spec=UserEntity)
    user.verify_password.return_value = True
    mock_user_repo.get_by_email.return_value = user
    
    result = await service.authenticate_user("test@example.com", "pass")
    
    assert result == user
    user.verify_password.assert_called_once()

@pytest.mark.asyncio
async def test_authenticate_user_failed(service, mock_user_repo):
    user = MagicMock(spec=UserEntity)
    user.verify_password.return_value = False
    mock_user_repo.get_by_email.return_value = user
    
    with pytest.raises(InvalidCredentials):
        await service.authenticate_user("test@example.com", "wrong")

@pytest.mark.asyncio
async def test_issue_tokens_orchestration(service, mock_token_repo, mock_session):
    user_id = uuid4()
    
    with patch("auth.services.auth_service.jwt.encode") as mock_encode:
        mock_encode.return_value = "token_str"
        response = await service.issue_tokens(user_id)
    
    assert response.access_token == "token_str"
    assert response.refresh_token == "token_str"
    mock_token_repo.save.assert_called_once()
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_rotate_refresh_token_success(service, mock_token_repo, mock_session):
    user_id = uuid4()
    jti = uuid4()
    token_entity = MagicMock(spec=RefreshTokenEntity)
    token_entity.is_revoked.return_value = False
    token_entity.is_expired.return_value = False
    mock_token_repo.get_by_jti.return_value = token_entity
    
    payload = {"token_type": "refresh", "jti": str(jti), "sub": str(user_id)}
    
    with patch.object(service, "_decode_token", return_value=payload), \
         patch("auth.services.auth_service.jwt.encode", return_value="new_token"):
        response = await service.rotate_refresh_token("old_token")
    
    assert response.refresh_token == "new_token"
    token_entity.mark_revoked.assert_called_once()
    assert mock_token_repo.save.call_count == 2 # One for new, one for revoked old
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_rotate_refresh_token_expired(service, mock_token_repo, mock_session):
    user_id = uuid4()
    jti = uuid4()
    token_entity = MagicMock(spec=RefreshTokenEntity)
    token_entity.is_revoked.return_value = False
    token_entity.is_expired.return_value = True
    mock_token_repo.get_by_jti.return_value = token_entity
    
    payload = {"token_type": "refresh", "jti": str(jti), "sub": str(user_id)}
    
    with patch.object(service, "_decode_token", return_value=payload), \
         pytest.raises(RefreshTokenExpired):
        await service.rotate_refresh_token("old_token")
    
    token_entity.mark_revoked.assert_called_once()
    mock_token_repo.save.assert_called_once_with(token_entity)
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_logout_orchestration(service, mock_token_repo, mock_session):
    jti = uuid4()
    payload = {"token_type": "refresh", "jti": str(jti)}
    
    with patch.object(service, "_decode_token", return_value=payload):
        await service.logout("token")
    
    mock_token_repo.revoke_lineage.assert_called_once_with(jti)
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_profile_delta(service, mock_user_repo):
    """Test get_user_profile (Delta logic calling base get_by_id)."""
    user_id = uuid4()
    expected = MagicMock(spec=UserEntity)
    # We mock the base method's dependency (repo.get_by_id) to verify delegation
    mock_user_repo.get_by_id.return_value = expected
    
    result = await service.get_user_profile(user_id)
    
    assert result == expected
    mock_user_repo.get_by_id.assert_called_once_with(user_id)
