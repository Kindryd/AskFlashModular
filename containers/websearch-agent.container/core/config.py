from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class WebSearchSettings(BaseSettings):
    """Web Search Agent configuration settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "Web Search Agent"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8012
    
    # Search Configuration
    MAX_RESULTS: int = 20
    SEARCH_TIMEOUT: int = 30
    MAX_CONCURRENT_SEARCHES: int = 5
    
    # DuckDuckGo Configuration
    DUCKDUCKGO_REGION: str = "us-en"
    DUCKDUCKGO_SAFESEARCH: str = "moderate"  # off, moderate, strict
    DUCKDUCKGO_TIME: Optional[str] = None  # d, w, m, y for day, week, month, year
    
    # Content Processing
    MAX_CONTENT_LENGTH: int = 2000  # Max characters per result content
    ENABLE_CONTENT_EXTRACTION: bool = True
    EXTRACT_SNIPPETS: bool = True
    
    # Result Filtering
    MIN_RELEVANCE_SCORE: float = 0.3
    ENABLE_DEDUPLICATION: bool = True
    SIMILARITY_THRESHOLD: float = 0.8
    
    # RabbitMQ Configuration
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "askflash"
    RABBITMQ_PASSWORD: str = "askflash123"
    RABBITMQ_VHOST: str = "/"
    
    # Queue Configuration
    QUEUE_NAME: str = "websearch.task"
    RESPONSE_QUEUE: str = "mcp.responses"
    QUEUE_DURABLE: bool = True
    
    # Redis Configuration (for caching and progress)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "askflash123"
    REDIS_DB: int = 0
    
    # Caching Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # Cache search results for 1 hour
    CACHE_MAX_SIZE: int = 1000  # Max cached searches
    
    # Performance Configuration
    REQUEST_DELAY: float = 0.5  # Delay between requests to avoid rate limiting
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: float = 1.0
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix="WEBSEARCH_",
        env_file=".env"
    )

# Global settings instance
settings = WebSearchSettings()

def get_settings() -> WebSearchSettings:
    """Get the global web search settings instance"""
    return settings 