"""Service layer for query and task management."""

from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.repositories.query_repository import QueryRepository
from shared.messaging import get_task_queue
from shared.schemas import TaskMessage


class QueryService:
    """Service for managing queries and tasks."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_repo = QueryRepository(session)

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
        query = await self.query_repo.create(
            correlation_id=correlation_id,
            user_id=user_id,
            message=message,
        )

        task_payload = TaskMessage(
            prompt=message,
            correlation_id=correlation_id,
            interaction_id=query.interaction_id,
            user_id="orchestrator",
            metadata={
                "query_id": str(query.id),
                "correlation_id": str(correlation_id),
                "pipeline_id": pipeline_id,
            },
        )

        # Enqueue to Redis task queue
        task_queue = get_task_queue()
        await task_queue.enqueue(task_payload.model_dump_json())

        await self.session.commit()
        logger.info(
            f"Created query {query.id} and enqueued task for pipeline {pipeline_id}"
        )

        return query.id
