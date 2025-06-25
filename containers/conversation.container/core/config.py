from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Configuration settings for conversation service"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/askflashdb"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    
    # Service URLs
    AI_ORCHESTRATOR_URL: str = "http://ai-orchestrator:8003"
    EMBEDDING_SERVICE_URL: str = "http://embedding:8002"
    
    # Conversation settings
    MAX_CONVERSATION_LENGTH: int = 1000
    CONVERSATION_TIMEOUT_HOURS: int = 24
    AUTO_CLEANUP_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 