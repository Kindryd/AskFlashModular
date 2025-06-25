from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
import redis.asyncio as redis
from core.config import settings

# Database setup
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Redis setup
redis_client = redis.from_url(settings.REDIS_URL)

class Base(DeclarativeBase):
    pass

class Integration(Base):
    __tablename__ = "integrations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "jira", "teams"
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "webhook", "api"
    config: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)  # Configuration data
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used: Mapped[datetime] = mapped_column(DateTime, nullable=True)

class IntegrationLog(Base):
    __tablename__ = "integration_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    integration_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "webhook_sent", "jira_created"
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, error, pending
    request_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    response_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)

class TeamsBotSession(Base):
    __tablename__ = "teams_bot_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(36), nullable=True)  # Link to conversation service
    teams_conversation_id: Mapped[str] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_redis():
    """Get Redis client"""
    return redis_client 