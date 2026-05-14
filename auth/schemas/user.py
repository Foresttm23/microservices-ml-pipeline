from datetime import datetime
from uuid import UUID

from pwdlib import PasswordHash

from shared.schemas import BaseDomainEntity, BaseSchema, CreatedAtMixin, UpdatedAtMixin


class UserEntity(BaseDomainEntity, CreatedAtMixin, UpdatedAtMixin):
    email: str
    hashed_password: str

    @classmethod
    def create(cls, email: str, hashed_password: str) -> "UserEntity":
        return cls(email=email, hashed_password=hashed_password)

    def verify_password(self, password: str, verifier: PasswordHash) -> bool:
        return verifier.verify(password, self.hashed_password)


class UserResponse(BaseSchema):
    id: UUID
    email: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
