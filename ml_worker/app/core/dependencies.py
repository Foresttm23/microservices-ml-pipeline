from typing import Annotated

from fastapi import Depends

from processors.task_processor import TaskConsumer
from ..inference.runner import InferenceRunner
from ..models.loader import GeminiModelLoader
from ..publishers.queue_publisher import ResultPublisher
from .config import GeminiSettings, get_gemini_settings


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
    return ResultPublisher()


ResultPublisherDep = Annotated[ResultPublisher, Depends(get_result_publisher)]


def get_task_consumer(
    runner: InferenceRunnerDep,
    publisher: ResultPublisherDep,
) -> TaskConsumer:
    return TaskConsumer(runner=runner, publisher=publisher)


TaskConsumerDep = Annotated[TaskConsumer, Depends(get_task_consumer)]
