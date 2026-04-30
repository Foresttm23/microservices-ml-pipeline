from typing import Annotated

from fastapi import Depends

from shared.messaging import get_result_queue

from ml_worker.core.config import GeminiSettings, get_gemini_settings
from ml_worker.loader import GeminiModelLoader
from ml_worker.messaging.queue_publisher import ResultPublisher
from ml_worker.runner import InferenceRunner
from ml_worker.task_processor import TaskProcessor


def get_worker_settings() -> GeminiSettings:
    return get_gemini_settings()


WorkerSettingsDep = Annotated[GeminiSettings, Depends(get_worker_settings)]


def get_model_loader(
    settings: WorkerSettingsDep,
) -> GeminiModelLoader:
    return GeminiModelLoader(settings=settings)


ModelLoaderDep = Annotated[GeminiModelLoader, Depends(get_model_loader)]


def get_inference_runner(
    loader: ModelLoaderDep,
) -> InferenceRunner:
    return InferenceRunner(loader=loader)


InferenceRunnerDep = Annotated[InferenceRunner, Depends(get_inference_runner)]


def get_result_publisher() -> ResultPublisher:
    result_queue = get_result_queue()
    return ResultPublisher(queue=result_queue)


ResultPublisherDep = Annotated[ResultPublisher, Depends(get_result_publisher)]


def get_task_consumer(
    runner: InferenceRunnerDep,
    publisher: ResultPublisherDep,
) -> TaskProcessor:
    return TaskProcessor(runner=runner, publisher=publisher)


TaskProcessorDep = Annotated[TaskProcessor, Depends(get_task_consumer)]
