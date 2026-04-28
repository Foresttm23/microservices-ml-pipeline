from .consumers.task_consumer import TaskConsumer
from .core.config import get_settings
from shared.core.logging import setup_logging
from .inference.runner import InferenceRunner
from .models.loader import GeminiModelLoader
from .publishers.result_publisher import ResultPublisher

# TODO initialize the queue


setup_logging()

settings = get_settings()
loader = GeminiModelLoader(settings=settings)

runner = InferenceRunner(loader=loader)
publisher = ResultPublisher()
task_consumer = TaskConsumer(runner=runner, publisher=publisher)
