import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.config.logging_config import configure_logging
from app.routers import bid, root, stat
from app.startup import setup

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    await setup()
    logger.info("Application startup complete")

    yield

    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.fastapi.title,
    version=settings.fastapi.version,
    docs_url=settings.fastapi.docs_url,
    redoc_url=settings.fastapi.redoc_url,
    root_path=settings.fastapi.root_path,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,  # noqa
    allow_origins=settings.general.allow_origins,
    allow_credentials=settings.general.allow_credentials,
    allow_methods=settings.general.allow_methods,
    allow_headers=settings.general.allow_headers,
)

app.include_router(bid.router)
app.include_router(stat.router)
app.include_router(root.router)
