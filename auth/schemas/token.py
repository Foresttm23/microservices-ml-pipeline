from datetime import datetime, timezone
from uuid import UUID


from shared.schemas import BaseDomainEntity, BaseSchema


class RefreshTokenEntity(BaseDomainEntity):
    user_id: UUID
    jti: UUID
    expires_at: datetime
    revoked_at: datetime | None = None
    replaced_by: UUID | None = None

    @classmethod
    def create(
        cls, user_id: UUID, jti: UUID, expires_at: datetime
    ) -> "RefreshTokenEntity":
        return cls(user_id=user_id, jti=jti, expires_at=expires_at)

    def is_expired(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return self.expires_at <= current

    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def mark_revoked(
        self, replaced_by: UUID | None = None, now: datetime | None = None
    ) -> None:
        self.revoked_at = now or datetime.now(timezone.utc)
        self.replaced_by = replaced_by


class TokenPairResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseSchema):
    refresh_token: str


class LogoutRequest(BaseSchema):
    refresh_token: str
