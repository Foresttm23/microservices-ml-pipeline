from typing import Any, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from orchestrator.core.enums import QueryState
from orchestrator.db.base import Base, CreatedAtMixin, UpdatedAtMixin


class ResponseModel(Base, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "responses"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    query_id: Mapped[UUID] = mapped_column(
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column()
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # ORM relationship to parent query
    query: Mapped["QueryModel"] = relationship("QueryModel", back_populates="responses")


class QueryModel(Base, CreatedAtMixin, UpdatedAtMixin):
    __tablename__ = "queries"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[str] = mapped_column(index=True)
    correlation_id: Mapped[UUID] = mapped_column(index=True, unique=True)
    interaction_id: Mapped[UUID] = mapped_column()
    message: Mapped[str] = mapped_column()
    state: Mapped[QueryState] = mapped_column(
        Enum(QueryState, native_enum=False),
        default=QueryState.PENDING,
        server_default=QueryState.PENDING.value,
    )
    # convenient ORM relationships
    responses: Mapped[List["ResponseModel"]] = relationship(
        "ResponseModel",
        back_populates="query",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # passive_deletes - Only used when we already have a foreign key setup for the ondelete behavior,
    # so we can rely on the database to handle the cascade delete,
    # without needing SQLAlchemy to load the related objects into memory first.
    logs: Mapped[List["LogModel"]] = relationship(
        "LogModel",
        back_populates="query",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @classmethod
    def create(cls, user_id: str, correlation_id: UUID, message: str) -> "QueryModel":
        """Factory method to ensure every new query starts correctly."""
        return cls(
            user_id=user_id,
            correlation_id=correlation_id,
            interaction_id=uuid4(),
            message=message,
            state=QueryState.PENDING,
        )

    def transition_to(self, next_state: QueryState) -> None:
        if self.state != QueryState.PENDING:
            raise ValueError("Cannot modify a non pending query")

        self.state = next_state


class LogModel(Base, CreatedAtMixin):
    __tablename__ = "logs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    query_id: Mapped[UUID] = mapped_column(
        ForeignKey("queries.id", ondelete="CASCADE"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column()
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    query: Mapped["QueryModel"] = relationship("QueryModel", back_populates="logs")
