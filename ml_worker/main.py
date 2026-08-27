import asyncio

from loguru import logger

from shared.core import ModelSettingsProtocol
from ml_worker.core.config import get_gemini_settings
from ml_worker.infra.vector_store import get_vector_store
from ml_worker.services.rag_graph import RagGraphService
from ml_worker.services.task_processor import TaskProcessor
from ml_worker.worker.runner import LangGraphRunner, Runner
from shared.core.logging import setup_logging
from shared.messaging import (
    Processor,
    QueueConsumer,
    QueuePublisher,
    RedisQueue,
    get_result_queue,
    get_task_queue,
)
from shared.schemas import ResultMessage, TaskMessage


def _init_processor(
    *,
    runner: Runner,
    result_queue: RedisQueue,
) -> Processor[TaskMessage, ResultMessage]:
    """
    Initialize the task processor with a runner and result publisher.
    """
    publisher = QueuePublisher(result_queue)
    task_processor = TaskProcessor(runner=runner, publisher=publisher)

    return task_processor


def _init_runner(settings: ModelSettingsProtocol) -> Runner:
    """
    Initializes the VectorStore, LangGraph StateGraph workflow, and LangGraphRunner.
    """
    vector_store = get_vector_store(settings)
    rag_graph = RagGraphService(settings=settings, vector_store=vector_store)
    return LangGraphRunner(rag_graph=rag_graph, model_name=settings.MODEL)


async def main():
    setup_logging()

    logger.info("Starting ML Worker service with LangGraph & ChromaDB RAG")

    settings = get_gemini_settings()

    # Initialize LangGraph & ChromaDB runner
    runner = _init_runner(settings)

    # Initialize Redis client and queues
    task_queue = get_task_queue()
    result_queue = get_result_queue()

    # Initialize publisher and processor
    task_processor = _init_processor(runner=runner, result_queue=result_queue)

    # Initialize and start queue consumer
    queue_consumer = QueueConsumer[TaskMessage, ResultMessage](
        processor=task_processor,
        queue=task_queue,
        message_factory=TaskMessage.model_validate_json,
    )

    logger.info("Starting queue consumer loop")

    await queue_consumer.run()


if __name__ == "__main__":
    with logger.contextualize(service="ml_worker"):
        asyncio.run(main())
