import sys
from loguru import logger


def setup_logging():
    # Remove default handler
    logger.remove()

    # 1. Console Handler (Human-readable for Dev)
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 2. File Handler (JSON for Production/Analysis)
    # Using JSON allows tools like ELK or Loki to parse your logs easily
    logger.add(
        "logs/service.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        serialize=True,  # This turns it into JSON
        rotation="10 MB",
        compression="zip",
    )


# Run this once in your main.py / entrypoint
