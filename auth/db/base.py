
from sqlalchemy.orm import DeclarativeBase


class AuthBase(DeclarativeBase):
    __mapper_args__ = {"eager_defaults": True}
