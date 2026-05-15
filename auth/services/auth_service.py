from datetime import datetime, timedelta, timezone
from typing import Any, cast
from uuid import UUID, uuid4

import jwt
from loguru import logger
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy.ext.asyncio import AsyncSession

from auth.core.config import AuthSettings, get_settings
from auth.exceptions.auth_errors import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidRefreshToken,
    InvalidTokenClaims,
    RefreshTokenExpired,
    RefreshTokenNotFound,
    RefreshTokenRevoked,
)
from auth.repositories.token_repository import RefreshTokenRepository
from auth.repositories.user_repository import UserRepository
from auth.schemas.token import RefreshTokenEntity, TokenPairResponse
from auth.schemas.user import UserEntity
from shared.services import BaseService

password_hash = PasswordHash((BcryptHasher(),))


class AuthService(BaseService[UserEntity, UserRepository]):
    """Service for auth workflows and refresh token rotation."""

    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository | None = None,
        settings: AuthSettings | None = None,
    ):
        super().__init__(session=session, repo=user_repo)
        self.token_repo = token_repo or RefreshTokenRepository(session)
        self.settings = settings or get_settings()

    async def register_user(self, email: str, password: str) -> UserEntity:
        existing = await self.repo.get_by_email(email)
        if existing:
            raise EmailAlreadyRegistered()

        hashed_password = password_hash.hash(password)
        user = UserEntity.create(email=email, hashed_password=hashed_password)
        created = await self.repo.save(user)
        await self.session.commit()
        logger.info("User registration complete")
        return created

    async def authenticate_user(self, email: str, password: str) -> UserEntity:
        user = await self.repo.get_by_email(email)
        if not user:
            raise InvalidCredentials()
        if not user.verify_password(password, password_hash):
            raise InvalidCredentials()
        logger.info("User authentication successful")
        return user

    async def issue_tokens(self, user_id: UUID) -> TokenPairResponse:
        access_token, expires_in = self._create_access_token(user_id)
        refresh_token, refresh_jti, refresh_exp = self._create_refresh_token(user_id)

        refresh_entity = RefreshTokenEntity.create(
            user_id=user_id, jti=refresh_jti, expires_at=refresh_exp
        )
        await self.token_repo.save(refresh_entity)
        await self.session.commit()
        logger.info("Token pair issued")

        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    async def rotate_refresh_token(self, refresh_token: str) -> TokenPairResponse:
        payload = self._decode_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise InvalidRefreshToken()

        jti = self._require_uuid_claim(payload, "jti")
        user_id = self._require_uuid_claim(payload, "sub")

        token_entity = await self.token_repo.get_by_jti(jti)
        if not token_entity:
            raise RefreshTokenNotFound()
        if token_entity.is_revoked():
            raise RefreshTokenRevoked()

        now = datetime.now(timezone.utc)
        if token_entity.is_expired(now):
            token_entity.mark_revoked(now=now)
            await self.token_repo.save(token_entity)
            await self.session.commit()
            raise RefreshTokenExpired()

        access_token, expires_in = self._create_access_token(user_id)
        new_refresh_token, new_jti, new_exp = self._create_refresh_token(user_id)

        new_entity = RefreshTokenEntity.create(
            user_id=user_id, jti=new_jti, expires_at=new_exp
        )
        await self.token_repo.save(new_entity)
        token_entity.mark_revoked(replaced_by=new_jti, now=now)
        await self.token_repo.save(token_entity)
        await self.session.commit()
        logger.info("Refresh token rotated")

        return TokenPairResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

    async def logout(self, refresh_token: str) -> None:
        payload = self._decode_token(refresh_token)
        if payload.get("token_type") != "refresh":
            raise InvalidRefreshToken()

        jti = self._require_uuid_claim(payload, "jti")

        # Let the repo handle the traversal logic
        await self.token_repo.revoke_lineage(jti)
        await self.session.commit()
        logger.info("Logout complete and lineage revoked")

    async def get_user_profile(self, user_id: UUID) -> UserEntity | None:
        return await self.get_by_id(user_id)

    def _decode_token(self, token: str) -> dict[str, object]:
        audience = self.settings.JWT_AUDIENCE
        issuer = self.settings.JWT_ISSUER
        leeway = float(self.settings.JWT_LEEWAY_SECONDS)
        options = None if audience else cast(Any, {"verify_aud": False})

        return jwt.decode(
            token,
            key=self.settings.JWT_SECRET_KEY,
            algorithms=[self.settings.JWT_ALGORITHM],
            leeway=leeway,
            issuer=issuer,
            audience=audience,
            options=options,
        )

    def _create_access_token(self, user_id: UUID) -> tuple[str, int]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(
            minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = self._base_claims(user_id, now, expires_at)
        payload["token_type"] = "access"
        token = jwt.encode(
            payload, self.settings.JWT_SECRET_KEY, algorithm=self.settings.JWT_ALGORITHM
        )
        expires_in = int((expires_at - now).total_seconds())
        return token, expires_in

    def _create_refresh_token(self, user_id: UUID) -> tuple[str, UUID, datetime]:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=self.settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        jti = uuid4()
        payload = self._base_claims(user_id, now, expires_at, jti=jti)
        payload["token_type"] = "refresh"
        token = jwt.encode(
            payload, self.settings.JWT_SECRET_KEY, algorithm=self.settings.JWT_ALGORITHM
        )
        return token, jti, expires_at

    def _base_claims(
        self,
        user_id: UUID,
        now: datetime,
        expires_at: datetime,
        jti: UUID | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": str(jti or uuid4()),
        }
        if self.settings.JWT_ISSUER:
            payload["iss"] = self.settings.JWT_ISSUER
        if self.settings.JWT_AUDIENCE:
            payload["aud"] = self.settings.JWT_AUDIENCE
        return payload

    @staticmethod
    def _require_uuid_claim(payload: dict[str, object], claim: str) -> UUID:
        value = payload.get(claim)
        if not isinstance(value, str):
            raise InvalidTokenClaims()
        return UUID(value)
