from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=0
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models (if needed for this container)
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    Each request gets its own session.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_async_db_session() -> AsyncSession:
    """
    Get a new database session (for use in services).
    Caller is responsible for closing the session.
    """
    return async_session_factory()

async def init_database():
    """Initialize database (create tables if needed)"""
    async with engine.begin() as conn:
        # AI Orchestrator doesn't create its own tables,
        # it uses shared tables managed by other services
        logger.info("🗄️ Connected to shared PostgreSQL database")

async def close_database():
    """Close database connections"""
    await engine.dispose()
    logger.info("🗄️ Database connections closed") 