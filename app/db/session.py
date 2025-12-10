from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings

engine = create_async_engine(
    str(settings.db.async_url),
    pool_pre_ping=True,
    max_overflow=settings.db.max_overflow,
    echo=settings.db.echo,
    pool_size=20,  # Increase pool size
    pool_recycle=3600,  # Recycle connections hourly
    connect_args={"server_settings": {"application_name": settings.fastapi.title + "_async"}},
)

session_factory = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
