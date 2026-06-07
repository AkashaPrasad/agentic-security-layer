"""
Async database engine and session factory.

Provides:
  - ``async_engine``  — the single AsyncEngine for the application.
  - ``AsyncSessionLocal`` — a session factory bound to the engine.
  - ``get_async_session()`` — FastAPI dependency that yields a session
    per request and commits / rolls back automatically.
"""

from collections.abc import AsyncGenerator
import ssl as _ssl

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def _engine_kwargs() -> dict:
    """Add asyncpg SSL settings only for cloud-style Postgres hosts."""
    if not settings.postgres_requires_ssl:
        return {}

    ctx = _ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = _ssl.CERT_NONE
    return {
        "connect_args": {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "ssl": ctx,
        }
    }

async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.app_debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_timeout=30,
    **_engine_kwargs(),
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Standalone factory for background threads (separate event loop)
# ---------------------------------------------------------------------------
def create_standalone_session_factory() -> tuple:
    """Create a brand-new engine + session factory.

    Use this when running in a thread with its own ``asyncio`` event loop
    (e.g. the experiment runner).  The global ``async_engine`` is bound to
    the *main* loop and will raise "Future attached to a different loop"
    if used from another one.

    Returns ``(engine, SessionFactory)``.
    """
    engine = create_async_engine(
        settings.async_database_url,
        echo=settings.app_debug,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30,
        **_engine_kwargs(),
    )
    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, factory


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session; commit on success, rollback on error."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
