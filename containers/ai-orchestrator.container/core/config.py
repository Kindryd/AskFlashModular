from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class AIOrchestratorSettings(BaseSettings):
    """AI Orchestrator specific configuration settings"""
    
    # Service Info
    SERVICE_NAME: str = "Flash AI Orchestrator"
    SERVICE_VERSION: str = "2.0.0"
    SERVICE_PORT: int = 8003
    
    # Database Settings
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "askflash"
    DATABASE_URI: Union[str, None] = None
    
    @field_validator("DATABASE_URI", mode="after")
    @classmethod
    def assemble_db_connection(cls, v, values):
        if not v:
            return f"postgresql+asyncpg://{values.data.get('POSTGRES_USER')}:{values.data.get('POSTGRES_PASSWORD')}@{values.data.get('POSTGRES_SERVER')}/{values.data.get('POSTGRES_DB')}"
        return v
    
    # OpenAI Settings
    OPENAI_API_KEY: str = ""
    OPENAI_DEFAULT_MODEL: str = "gpt-4"
    OPENAI_INTENT_MODEL: str = "gpt-3.5-turbo"  # Faster model for intent analysis
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_TIMEOUT: int = 30
    
    # Information Quality Enhancement Settings
    QUALITY_ANALYSIS_ENABLED: bool = True
    CONFLICT_DETECTION_ENABLED: bool = True
    AUTHORITY_SCORING_ENABLED: bool = True
    FRESHNESS_SCORING_ENABLED: bool = True
    CROSS_REFERENCE_ENABLED: bool = True
    
    # Source Authority Scores
    SOURCE_AUTHORITY_AZURE_DEVOPS: float = 0.9
    SOURCE_AUTHORITY_CONFLUENCE: float = 0.8
    SOURCE_AUTHORITY_SHAREPOINT: float = 0.7
    SOURCE_AUTHORITY_GITHUB: float = 0.6
    SOURCE_AUTHORITY_DOCS: float = 0.6
    SOURCE_AUTHORITY_UNKNOWN: float = 0.5
    
    # Intent AI Settings
    INTENT_AI_ENABLED: bool = True
    INTENT_ANALYSIS_TIMEOUT: int = 10
    CONTEXT_SUMMARY_ENABLED: bool = True
    AI_GUIDANCE_ENABLED: bool = True
    
    # Provider Routing Settings
    PROVIDER_ROUTING_ENABLED: bool = True
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: float = 1.0
    FALLBACK_TO_GPT35: bool = True
    
    # Quality-Aware Prompt Settings
    QUALITY_PROMPT_ENHANCEMENT: bool = True
    CONFLICT_WARNING_THRESHOLD: float = 0.6
    LOW_QUALITY_WARNING_THRESHOLD: float = 0.5
    
    # Redis Settings (for event communication)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Union[str, None] = None
    
    @field_validator("REDIS_URL", mode="after")
    @classmethod
    def assemble_redis_url(cls, v, values):
        if not v:
            return f"redis://{values.data.get('REDIS_HOST')}:{values.data.get('REDIS_PORT')}/{values.data.get('REDIS_DB')}"
        return v
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Flash AI Branding
    FLASH_EMOJI: str = "🧠"
    FLASH_PRIMARY_COLOR: str = "#7ed321"
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix="AI_ORCHESTRATOR_",
        env_file=".env"
    )

# Global settings instance
settings = AIOrchestratorSettings()

def get_settings() -> AIOrchestratorSettings:
    """Get the global AI orchestrator settings instance"""
    return settings 