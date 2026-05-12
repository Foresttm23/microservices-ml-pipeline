from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from auth.api.v1.auth import router as auth_router
from auth.core.config import get_settings
from shared.core.exceptions import global_exception_handler
from shared.core.logging import setup_logging
from shared.db import close_db, init_db
from shared.middlewares import (
    JWTAuthMiddleware,
    LoggingContextMiddleware,
    ResponseLogMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # Startup
    logger.info("Startup")
    auth_settings = get_settings()
    init_db(auth_settings.DATABASE_URL, pool_size=10, max_overflow=5)

    yield

    # Shutdown
    logger.info("Shutdown")
    await close_db()


app = FastAPI(lifespan=lifespan)
global_exception_handler(app)

app.add_middleware(JWTAuthMiddleware, settings=get_settings())
app.add_middleware(LoggingContextMiddleware)
app.add_middleware(ResponseLogMiddleware)


app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


def main() -> None:
    settings = get_settings()
    uvicorn.run("auth.main:app", host="0.0.0.0", port=settings.PORT, reload=True)


if __name__ == "__main__":
    main()
