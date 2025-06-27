from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class ModeratorSettings(BaseSettings):
    """Moderator Agent configuration settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "Moderator Agent"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8013
    
    # Moderation Configuration
    ENABLE_TOXICITY_CHECK: bool = True
    ENABLE_PROFANITY_FILTER: bool = True
    ENABLE_HATE_SPEECH_CHECK: bool = True
    ENABLE_SPAM_DETECTION: bool = True
    ENABLE_QUALITY_ASSESSMENT: bool = True
    
    # Thresholds
    TOXICITY_THRESHOLD: float = 0.7
    HATE_SPEECH_THRESHOLD: float = 0.6
    SPAM_THRESHOLD: float = 0.8
    QUALITY_THRESHOLD: float = 0.5
    CONFIDENCE_THRESHOLD: float = 0.7
    
    # Content Limits
    MAX_CONTENT_LENGTH: int = 10000  # Max characters to process
    MIN_CONTENT_LENGTH: int = 3      # Min characters to process
    
    # Filtering Configuration
    BLOCKED_WORDS: List[str] = [
        # Add specific words to block
        "spam", "scam", "phishing"
    ]
    
    ALLOWED_DOMAINS: List[str] = [
        # Add trusted domains
        "example.com", "trusted-site.org"
    ]
    
    # Policy Configuration
    ENFORCE_ENTERPRISE_POLICY: bool = True
    ALLOW_EXTERNAL_LINKS: bool = True
    REQUIRE_SOURCE_ATTRIBUTION: bool = True
    
    # OpenAI Configuration for AI-based moderation
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    ENABLE_AI_MODERATION: bool = False  # Disable by default for cost control
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "askflash"
    RABBITMQ_PASSWORD: str = "askflash123"
    RABBITMQ_VHOST: str = "/"
    
    # Queue Configuration
    QUEUE_NAME: str = "moderator.task"
    RESPONSE_QUEUE: str = "mcp.responses"
    QUEUE_DURABLE: bool = True
    
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "askflash123"
    REDIS_DB: int = 0
    
    # Caching Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 1800  # Cache moderation results for 30 minutes
    CACHE_MAX_SIZE: int = 5000  # Max cached moderation results
    
    # Performance Configuration
    MAX_CONCURRENT_CHECKS: int = 10
    CHECK_TIMEOUT: int = 30
    RETRY_ATTEMPTS: int = 2
    RETRY_DELAY: float = 1.0
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_MODERATION_ACTIONS: bool = True
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix="MODERATOR_",
        env_file=".env"
    )

# Global settings instance
settings = ModeratorSettings()

def get_settings() -> ModeratorSettings:
    """Get the global moderator settings instance"""
    return settings 