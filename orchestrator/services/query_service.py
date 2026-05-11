from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.core.enums import QueryState
from orchestrator.repositories.log_repository import LogRepository
from orchestrator.repositories.query_repository import QueryRepository
from orchestrator.repositories.response_repository import ResponseRepository
from orchestrator.schemas.log import LogEntity
from orchestrator.schemas.query import QueryEntity
from orchestrator.schemas.response import ResponseEntity
from shared.messaging import (
    QueuePublisher,
    get_task_queue,
)
from shared.schemas import TaskMessage
from shared.schemas.result import ResultMessage
from shared.services import BaseService


class QueryService(BaseService[QueryEntity, QueryRepository]):
    """Service for managing queries and tasks."""

    def __init__(
        self,
        session: AsyncSession,
        query_repo: QueryRepository,
        response_repo: ResponseRepository | None = None,
        log_repo: LogRepository | None = None,
    ):
        self.session = session
        self.query_repo = query_repo
        self.response_repo = response_repo or ResponseRepository(session)
        self.log_repo = log_repo or LogRepository(session)

    async def create_and_enqueue_task(
        self,
        correlation_id: UUID,
        user_id: str,
        message: str,
        pipeline_id: str,
    ) -> UUID:
        """
        Create a PENDING query and enqueue it for processing.

        Args:
            correlation_id: Unique tracking ID
            user_id: User ID
            message: Query message content
            pipeline_id: Target pipeline

        Returns:
            UUID of the created query

        Flow:
            1. Create PENDING query in database
            2. Enqueue task to Redis task_queue
            3. Commit database transaction
            4. Return query ID
        """
        logger.debug(
            "Creating query: pipeline_id={}",
            pipeline_id,
        )
        # Create query record (not committed yet)
        query = QueryEntity.create(
            correlation_id=correlation_id,
            user_id=user_id,
            message=message,
        )
        await self.query_repo.save(query)
        await self.session.commit()

        task_payload = TaskMessage(
            prompt=message,
            correlation_id=correlation_id,
            interaction_id=query.interaction_id,
            user_id=user_id,
            metadata={
                "query_id": str(query.id),
                "correlation_id": str(correlation_id),
                "pipeline_id": pipeline_id,
            },
        )

        # Enqueue to Redis task queue via the generic publisher
        task_publisher = QueuePublisher(get_task_queue())
        await task_publisher.publish(task_payload.model_dump_json())

        logger.info(
            "Created query {} and enqueued task for pipeline {}", query.id, pipeline_id
        )

        return query.id

    async def handle_result(self, query: QueryEntity, result: ResultMessage):
        """
        Handle a result message by updating query state and persisting responses/logs.

        Args:
            query: The QueryEntity to update
            result: The ResultMessage from ml_worker

        Business Logic:
            1. Transition query state based on result status
            2. Save responses or logs as appropriate
            3. Persist all changes to database
        """
        logger.debug("Handling result: query_id={} status={}", query.id, result.status)
        if result.status in (QueryState.COMPLETED, QueryState.MOCKED):
            query.transition_to(QueryState.COMPLETED)
            if result.output_text:
                # Create and persist response entity
                response = ResponseEntity.create(
                    query_id=query.id,
                    content=result.output_text,
                    tokens_used=result.tokens_used,
                )
                await self.response_repo.save(response)
        else:
            query.transition_to(QueryState.FAILED)
            if result.error:
                # Create and persist error log entity
                log = LogEntity.create(
                    query_id=query.id,
                    message=result.error,
                    metadata={"error_type": "processing_error"},
                )
                log.mark_as_error()
                await self.log_repo.save(log)

        # Persist the updated query entity state back to the database
        await self.query_repo.save(query)

    async def get_by_id(self, entity_id: Any) -> QueryEntity | None:
        raise NotImplementedError("QueryService.get_by_id not implemented.")

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[QueryEntity]:
        raise NotImplementedError("QueryService.get_all not implemented.")

    async def create(self, entity: QueryEntity) -> QueryEntity:
        raise NotImplementedError("QueryService.create not implemented.")

    async def update(self, entity_id: Any, entity: QueryEntity) -> QueryEntity | None:
        raise NotImplementedError("QueryService.update not implemented.")

    async def delete(self, entity_id: Any) -> bool:
        raise NotImplementedError("QueryService.delete not implemented.")
