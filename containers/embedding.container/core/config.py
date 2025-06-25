from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Configuration settings for Flash AI Embedding Service"""
    
    # Database Configuration
    POSTGRES_URL: str = os.getenv(
        "POSTGRES_URL", 
        "postgresql://postgres:postgres@postgres/askflashdb"
    )
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    # Qdrant Vector Database
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "flash_docs")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    VECTOR_DIMENSIONS: int = int(os.getenv("VECTOR_DIMENSIONS", "1536"))
    
    # Document Processing
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))
    
    # Smart Alias Discovery
    ALIAS_CONFIDENCE_THRESHOLD: float = float(os.getenv("ALIAS_CONFIDENCE_THRESHOLD", "0.7"))
    ALIAS_CACHE_TTL: int = int(os.getenv("ALIAS_CACHE_TTL", "86400"))  # 24 hours
    
    # Flash Branding
    FLASH_BRAND_COLOR: str = "#7ed321"
    FLASH_BRAND_EMOJI: str = "🔍"
    
    # Service URLs
    AI_ORCHESTRATOR_URL: str = os.getenv("AI_ORCHESTRATOR_URL", "http://ai-orchestrator:8000")
    ANALYTICS_URL: str = os.getenv("ANALYTICS_URL", "http://analytics:8000")
    
    # Processing Limits
    MAX_CONCURRENT_EMBEDDINGS: int = int(os.getenv("MAX_CONCURRENT_EMBEDDINGS", "10"))
    PROCESSING_TIMEOUT: int = int(os.getenv("PROCESSING_TIMEOUT", "300"))  # 5 minutes
    
    # Quality Settings
    ENABLE_QUALITY_ANALYSIS: bool = os.getenv("ENABLE_QUALITY_ANALYSIS", "true").lower() == "true"
    ENABLE_ALIAS_DISCOVERY: bool = os.getenv("ENABLE_ALIAS_DISCOVERY", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings() 