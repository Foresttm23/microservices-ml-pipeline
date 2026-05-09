from __future__ import annotations

from uuid import UUID

from loguru import logger

from orchestrator.core.enums import QueryState
from orchestrator.db.session import db_session_manager
from orchestrator.repositories.query_repository import QueryRepository
from orchestrator.services.query_service import QueryService
from shared.messaging import Processor, RedisPubSub, result_channel
from shared.schemas.result import ResultMessage


class ResultProcessor(Processor[ResultMessage, None]):
    def __init__(self, pubsub: RedisPubSub) -> None:
        self._pubsub = pubsub

    async def process(self, result: ResultMessage) -> None:
        # 1. Extraction and Basic Validation
        query_uuid = self._extract_query_id(result)
        if not query_uuid:
            return

        async with db_session_manager.session() as session:
            repo = QueryRepository(session)
            service = QueryService(session, repo)  # Or inject this

            # 2. Fetch
            query = await repo.get_model_by_id(query_uuid)
            if not query or query.state != QueryState.PENDING:
                return

            # 3. Delegate ALL business logic to the service
            await service.handle_result(query, result)

            await session.commit()
            user_id = result.user_id or query.user_id

        # 4. Infrastructure/Outbound messaging
        await self._pubsub.publish(result_channel(user_id), result.model_dump_json())

    @staticmethod
    def _extract_query_id(result: ResultMessage) -> UUID | None:
        query_id = result.metadata.get("query_id")
        if not query_id:
            logger.error("Result message missing query_id metadata")
            return None

        try:
            query_uuid = UUID(str(query_id))
        except ValueError:
            logger.error("Invalid query_id in result metadata: {}", query_id)
            return None

        return query_uuid
