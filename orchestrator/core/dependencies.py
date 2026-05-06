"""Dependency injection for orchestrator service."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.db.session import db_session_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for dependency injection.

    Yields:
        AsyncSession: Active database session
    """
    async with db_session_manager.session() as session:
        yield session
