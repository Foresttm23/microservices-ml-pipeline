import contextlib
from typing import Any, AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from orchestrator.core.config import OrchestratorSettings
from shared.core import SessionNotInitializedException


class DBSessionManager:
    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def start(self, database_url: str, **pool_kwargs: Any) -> None:
        if self.engine is None:
            self.engine = create_async_engine(database_url, **pool_kwargs)
            self.sessionmaker = async_sessionmaker(
                autocommit=False, bind=self.engine, expire_on_commit=False
            )

    async def stop(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None
            self.sessionmaker = None

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        if self.sessionmaker is None:
            raise SessionNotInitializedException("POSTGRES_DB")

        session = self.sessionmaker()
        try:
            yield session
        except Exception:
            logger.error("DB session failed, rolling back", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()  # Always close to return to pool


db_session_manager = DBSessionManager()


def init_db(settings: OrchestratorSettings, **pool_kwargs: Any) -> None:
    db_session_manager.start(settings.DATABASE_URL, **pool_kwargs)


async def close_db() -> None:
    await db_session_manager.stop()
