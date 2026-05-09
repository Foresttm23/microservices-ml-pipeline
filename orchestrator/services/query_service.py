from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.core.enums import QueryState
from orchestrator.db.models import LogModel, QueryModel, ResponseModel
from orchestrator.repositories.query_repository import QueryRepository
from shared.messaging import (
    QueuePublisher,
    get_task_queue,
)
from shared.schemas import TaskMessage
from shared.schemas.result import ResultMessage
from shared.services import BaseService

# todo add full representation of the QueryModel as pydantic schema and import here.


class QueryService(BaseService[QuerySchema, QueryRepository]):
    """Service for managing queries and tasks."""

    def __init__(self, session: AsyncSession, query_repo: QueryRepository):
        self.session = session
        self.query_repo = query_repo

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
        # Create query record (not committed yet)
        query = QueryModel.create(
            correlation_id=correlation_id,
            user_id=user_id,
            message=message,
        )
        await self.query_repo.add(query)

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

        await self.session.commit()
        logger.info(
            "Created query {} and enqueued task for pipeline {}", query.id, pipeline_id
        )

        return query.id

    async def handle_result(self, query: QueryModel, result: ResultMessage):
        if result.status in (QueryState.COMPLETED, QueryState.MOCKED):
            query.transition_to(QueryState.COMPLETED)
            if result.output_text:
                await self.repo.add_response(
                    ResponseModel(query_id=query.id, content=result.output_text)
                )
        else:
            query.transition_to(QueryState.FAILED)
            if result.error:
                await self.repo.add_log(
                    LogModel(query_id=query.id, message=result.error)
                )

    async def get_by_id(self, entity_id: Any) -> QuerySchema | None:
        raise NotImplementedError("QueryService.get_by_id not implemented.")

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[QuerySchema]:
        raise NotImplementedError("QueryService.get_all not implemented.")

    async def create(self, entity: QuerySchema) -> QuerySchema:
        raise NotImplementedError("QueryService.create not implemented.")

    async def update(self, entity_id: Any, entity: QuerySchema) -> QuerySchema | None:
        raise NotImplementedError("QueryService.update not implemented.")

    async def delete(self, entity_id: Any) -> bool:
        raise NotImplementedError("QueryService.delete not implemented.")
