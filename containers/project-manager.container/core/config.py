from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Configuration settings for project manager service"""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/askflashdb"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # JIRA Integration
    JIRA_URL: Optional[str] = None
    JIRA_TOKEN: Optional[str] = None
    JIRA_USERNAME: Optional[str] = None
    
    # Teams Integration
    TEAMS_WEBHOOK_URL: Optional[str] = None
    TEAMS_BOT_NAME: str = "Flash AI Assistant"
    
    # Service URLs
    AI_ORCHESTRATOR_URL: str = "http://ai-orchestrator:8003"
    EMBEDDING_SERVICE_URL: str = "http://embedding:8002"
    CONVERSATION_SERVICE_URL: str = "http://conversation:8001"
    
    # Integration settings
    MAX_INTEGRATION_RETRIES: int = 3
    INTEGRATION_TIMEOUT: int = 30
    WEBHOOK_TIMEOUT: int = 10
    
    # Security
    SECRET_KEY: str = "project-manager-secret-key"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings() 