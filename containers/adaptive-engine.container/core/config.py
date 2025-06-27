"""
Configuration settings for Adaptive Learning Engine
"""

import os
from pydantic import BaseSettings
from typing import Optional

class AdaptiveLearningSettings(BaseSettings):
    """Configuration for Adaptive Learning Engine"""
    
    # Service Configuration
    SERVICE_NAME: str = "adaptive-learning-engine"
    SERVICE_VERSION: str = "3.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Database Configuration
    POSTGRES_URL: str = os.getenv(
        "POSTGRES_URL", 
        "postgresql://askflash:askflash123@localhost:5432/askflashdb"
    )
    
    # Redis Configuration  
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "askflash123")
    
    # Qdrant Configuration
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_URL: str = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
    
    # Learning Configuration
    ANALYSIS_BATCH_SIZE: int = int(os.getenv("ANALYSIS_BATCH_SIZE", "100"))
    LEARNING_THRESHOLD: float = float(os.getenv("LEARNING_THRESHOLD", "0.8"))
    PATTERN_DETECTION_WINDOW_DAYS: int = int(os.getenv("PATTERN_DETECTION_WINDOW_DAYS", "7"))
    INSIGHT_RETENTION_DAYS: int = int(os.getenv("INSIGHT_RETENTION_DAYS", "90"))
    
    # Persona Building Configuration
    MIN_INTERACTIONS_FOR_PERSONA: int = int(os.getenv("MIN_INTERACTIONS_FOR_PERSONA", "5"))
    PERSONA_CONFIDENCE_THRESHOLD: float = float(os.getenv("PERSONA_CONFIDENCE_THRESHOLD", "0.7"))
    
    # Knowledge Evolution Configuration
    KNOWLEDGE_UPDATE_BATCH_SIZE: int = int(os.getenv("KNOWLEDGE_UPDATE_BATCH_SIZE", "50"))
    KNOWLEDGE_CONFIDENCE_THRESHOLD: float = float(os.getenv("KNOWLEDGE_CONFIDENCE_THRESHOLD", "0.85"))
    FAQ_PATTERN_MIN_OCCURRENCES: int = int(os.getenv("FAQ_PATTERN_MIN_OCCURRENCES", "3"))
    
    # Pattern Analysis Configuration
    PATTERN_CONFIDENCE_THRESHOLD: float = float(os.getenv("PATTERN_CONFIDENCE_THRESHOLD", "0.75"))
    CROSS_USER_PATTERN_MIN_USERS: int = int(os.getenv("CROSS_USER_PATTERN_MIN_USERS", "3"))
    TEMPORAL_PATTERN_WINDOW_HOURS: int = int(os.getenv("TEMPORAL_PATTERN_WINDOW_HOURS", "168"))  # 1 week
    
    # Optimization Configuration
    OPTIMIZATION_LEARNING_RATE: float = float(os.getenv("OPTIMIZATION_LEARNING_RATE", "0.1"))
    ADAPTATION_CONFIDENCE_THRESHOLD: float = float(os.getenv("ADAPTATION_CONFIDENCE_THRESHOLD", "0.8"))
    CONTEXT_RELEVANCE_THRESHOLD: float = float(os.getenv("CONTEXT_RELEVANCE_THRESHOLD", "0.7"))
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    
    # Background Task Configuration
    PERSONA_LEARNING_INTERVAL: int = int(os.getenv("PERSONA_LEARNING_INTERVAL", "30"))
    KNOWLEDGE_EVOLUTION_INTERVAL: int = int(os.getenv("KNOWLEDGE_EVOLUTION_INTERVAL", "60"))
    PATTERN_ANALYSIS_INTERVAL: int = int(os.getenv("PATTERN_ANALYSIS_INTERVAL", "45"))
    OPTIMIZATION_INTERVAL_MINUTES: int = int(os.getenv("OPTIMIZATION_INTERVAL_MINUTES", "90"))
    
    # Redis Channel Configuration
    REDIS_CHANNELS = {
        # Channels we subscribe to
        "conversation_ended": "conversation:ended",
        "response_rated": "ai:response_rated", 
        "feedback_given": "user:feedback_given",
        "task_completed": "ai:task:completed",
        
        # Channels we publish to
        "insight_generated": "adaptive:insight_generated",
        "pattern_detected": "adaptive:pattern_detected",
        "persona_updated": "adaptive:persona_updated",
        "knowledge_evolved": "adaptive:knowledge_evolved",
        "optimization_available": "adaptive:optimization_available"
    }
    
    # Feature Flags
    ENABLE_PERSONA_BUILDING: bool = os.getenv("ENABLE_PERSONA_BUILDING", "true").lower() == "true"
    ENABLE_KNOWLEDGE_EVOLUTION: bool = os.getenv("ENABLE_KNOWLEDGE_EVOLUTION", "true").lower() == "true" 
    ENABLE_PATTERN_ANALYSIS: bool = os.getenv("ENABLE_PATTERN_ANALYSIS", "true").lower() == "true"
    ENABLE_CROSS_USER_LEARNING: bool = os.getenv("ENABLE_CROSS_USER_LEARNING", "true").lower() == "true"
    ENABLE_TEMPORAL_ANALYSIS: bool = os.getenv("ENABLE_TEMPORAL_ANALYSIS", "true").lower() == "true"
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance Configuration
    MAX_CONCURRENT_LEARNING_TASKS: int = int(os.getenv("MAX_CONCURRENT_LEARNING_TASKS", "5"))
    LEARNING_TASK_TIMEOUT_SECONDS: int = int(os.getenv("LEARNING_TASK_TIMEOUT_SECONDS", "300"))
    
    # Data Retention Configuration
    USER_INTERACTION_RETENTION_DAYS: int = int(os.getenv("USER_INTERACTION_RETENTION_DAYS", "365"))
    PATTERN_DATA_RETENTION_DAYS: int = int(os.getenv("PATTERN_DATA_RETENTION_DAYS", "180"))
    LEARNING_LOG_RETENTION_DAYS: int = int(os.getenv("LEARNING_LOG_RETENTION_DAYS", "30"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = AdaptiveLearningSettings()

def get_settings() -> AdaptiveLearningSettings:
    """Get configuration settings instance"""
    return settings 