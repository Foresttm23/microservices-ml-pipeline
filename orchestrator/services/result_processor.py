from __future__ import annotations

from uuid import UUID

from loguru import logger

from orchestrator.exceptions import ResultPublishFailed
from orchestrator.repositories.log_repository import LogRepository
from orchestrator.repositories.query_repository import QueryRepository
from orchestrator.repositories.response_repository import ResponseRepository
from orchestrator.services.query_service import QueryService
from shared.core import QueryState
from shared.db import db_session_manager
from shared.messaging import Processor, RedisPubSub, result_channel
from shared.schemas import ResultMessage


class ResultProcessor(Processor[ResultMessage, None]):
    def __init__(self, pubsub: RedisPubSub) -> None:
        self._pubsub = pubsub

    async def process(self, result: ResultMessage) -> None:
        # 1. Extraction and Basic Validation
        query_uuid = self._extract_query_id(result)
        if not query_uuid:
            logger.warning("Skipping result without query_id metadata")
            return

        async with db_session_manager.session() as session:
            # Initialize repositories
            query_repo = QueryRepository(session)
            response_repo = ResponseRepository(session)
            log_repo = LogRepository(session)

            # Initialize service with all repositories
            service = QueryService(session, query_repo, response_repo, log_repo)

            # 2. Fetch
            query = await query_repo.get_by_id(query_uuid)
            if not query:
                logger.warning("Query not found for result: query_id={}", query_uuid)
                return
            if query.state != QueryState.PENDING:
                logger.info(
                    "Ignoring result for non-pending query: query_id={} state={}",
                    query_uuid,
                    query.state,
                )
                return

            # 3. Delegate ALL business logic to the service
            await service.handle_result(query, result)

            await session.commit()
            user_id = result.user_id or query.user_id

        # 4. Infrastructure/Outbound messaging
        channel = result_channel(user_id)
        logger.info("Publishing result to channel {}", channel)
        try:
            await self._pubsub.publish(channel, result.model_dump_json())
        except Exception as exc:
            raise ResultPublishFailed("Failed to publish result") from exc
        logger.info("Result published: query_id={} channel={}", query_uuid, channel)

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
