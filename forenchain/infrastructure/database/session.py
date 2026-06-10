from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from forenchain.config import get_settings

_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        # Convert sync postgresql:// to async postgresql+asyncpg://
        db_url = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        _engine = create_async_engine(
            db_url,
            echo=settings.environment == "development",
            pool_pre_ping=True,       # detects dead connections before use
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_get_engine(),
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a session and closes it after the request."""
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
