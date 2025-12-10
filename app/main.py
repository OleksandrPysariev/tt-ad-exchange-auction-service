import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import settings
from app.config.logging_config import configure_logging
from app.startup import setup

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info("Starting up application...")
    setup()
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.fastapi.title,
    version=settings.fastapi.version,
    docs_url=settings.fastapi.docs_url,
    redoc_url=settings.fastapi.redoc_url,
    root_path=settings.fastapi.root_path,
    lifespan=lifespan,
)
