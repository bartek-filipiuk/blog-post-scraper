"""Database configuration and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator

from src.config import settings, get_logger

logger = get_logger(__name__)

# Create declarative base for models
Base = declarative_base()

# Convert sqlite:/// to sqlite+aiosqlite:/// for async support
async_database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# Create async engine
# Note: StaticPool is used for SQLite to avoid connection pool issues
engine = create_async_engine(
    async_database_url,
    echo=settings.log_level == "DEBUG",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session.

    Yields:
        AsyncSession: Database session

    Example:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            # Use db here
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in models if they don't exist.
    Safe to call multiple times (idempotent).
    """
    try:
        # Import all models here to ensure they're registered with Base
        from src.models import blog_post, scraping_job  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database initialized successfully", database_url=settings.database_url)
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def drop_db() -> None:
    """Drop all database tables.

    WARNING: This will delete all data!
    Use only for testing or cleanup.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("Database tables dropped", database_url=settings.database_url)
    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise


# TODO: Future enhancement - Add Alembic for database migrations
# For MVP, we use create_all() which is sufficient for SQLite
# To add migrations:
# 1. pip install alembic
# 2. alembic init alembic
# 3. Configure alembic.ini with database URL
# 4. Create initial migration: alembic revision --autogenerate -m "Initial"
# 5. Apply migration: alembic upgrade head
