"""
PostgreSQL Database Connection using SQLAlchemy Async
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from ..config import settings

# Create async engine. Behavior depends on deployment target:
#   * sqlite (tests): no pool sizing.
#   * Supabase transaction pooler (port 6543): pgBouncer already pools, so we
#     skip pool_size/max_overflow, and disable asyncpg prepared-statement cache
#     (pgBouncer in transaction mode does not support prepared statements).
#   * Anything else (direct Postgres, session pooler on 5432): normal pooling.
_url = settings.DATABASE_URL
_is_sqlite = _url.startswith("sqlite")
_is_tx_pooler = ":6543" in _url  # Supabase transaction pooler convention
# Local dev (Docker bridge or loopback) — no TLS, normal prepared-statement cache.
_is_local = any(h in _url for h in ("@localhost", "@127.0.0.1", "@postgres:", "@postgres/"))

_engine_kwargs: dict = {"echo": settings.DEBUG, "pool_pre_ping": True}
if not _is_sqlite and not _is_tx_pooler:
    _engine_kwargs["pool_size"] = 10
    _engine_kwargs["max_overflow"] = 20

if _url.startswith("postgresql+asyncpg") and not _is_sqlite and not _is_local:
    # Managed Postgres (Supabase, Neon, RDS, etc.) — require TLS.
    _connect_args: dict = {"ssl": "require"}
    if _is_tx_pooler:
        # pgBouncer transaction mode: no server-side prepared statements.
        _connect_args["statement_cache_size"] = 0
        _connect_args["prepared_statement_cache_size"] = 0
    _engine_kwargs["connect_args"] = _connect_args

engine = create_async_engine(_url, **_engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def init_db():
    """Initialize database - create tables."""
    async with engine.begin() as conn:
        # Import models to register them
        from ..models import user, profile, skill, roadmap, progress, resume
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connection."""
    await engine.dispose()


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
