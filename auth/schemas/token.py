from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from shared.schemas import BaseSchema


class RefreshTokenEntity(BaseSchema):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    jti: UUID
    expires_at: datetime
    created_at: datetime | None = None
    revoked_at: datetime | None = None
    replaced_by: UUID | None = None

    @classmethod
    def create(cls, user_id: UUID, jti: UUID, expires_at: datetime) -> "RefreshTokenEntity":
        return cls(user_id=user_id, jti=jti, expires_at=expires_at)


class TokenPairResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class LogoutRequest(BaseSchema):
    refresh_token: str

