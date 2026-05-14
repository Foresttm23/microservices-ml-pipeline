from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, field_validator
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


class UserRegisterRequest(BaseSchema):
    """Payload for new user registration.

    Validation rules:
    - ``email`` must be a syntactically valid email address.
    - ``password`` must be at least 8 characters, contain at least one uppercase
      letter, one lowercase letter, and one digit.
    """

    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        errors: list[str] = []
        if len(value) < 8:
            errors.append("at least 8 characters")
        if not any(c.isupper() for c in value):
            errors.append("at least one uppercase letter")
        if not any(c.islower() for c in value):
            errors.append("at least one lowercase letter")
        if not any(c.isdigit() for c in value):
            errors.append("at least one digit")
        if errors:
            raise ValueError(f"Password must contain {', '.join(errors)}.")
        return value


class UserLoginRequest(BaseSchema):
    """Payload for user login.

    Validates that the email is well-formed before forwarding to the auth service.
    Password is not strength-checked on login to avoid leaking policy details.
    """

    email: EmailStr
    password: str


class UserResponse(BaseSchema):
    id: UUID
    email: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
