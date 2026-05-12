from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from shared.schemas import BaseSchema


class UserEntity(BaseSchema):
    id: UUID = Field(default_factory=uuid4)
    email: str
    hashed_password: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, email: str, hashed_password: str) -> "UserEntity":
        return cls(email=email, hashed_password=hashed_password)


class UserRegisterRequest(BaseSchema):
    email: str
    password: str


class UserLoginRequest(BaseSchema):
    email: str
    password: str


class UserResponse(BaseSchema):
    id: UUID
    email: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
