from sqlalchemy.orm import DeclarativeBase


class OrchestratorBase(DeclarativeBase):
    __mapper_args__ = {"eager_defaults": True}
