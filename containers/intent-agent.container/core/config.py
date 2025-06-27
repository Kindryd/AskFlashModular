"""
Configuration settings for Intent Agent
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class IntentAgentSettings(BaseSettings):
    """Configuration settings for Intent Agent"""
    
    # Service settings
    service_name: str = "Flash AI Intent Agent"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-3.5-turbo"
    openai_fallback_model: str = "gpt-3.5-turbo-16k"
    openai_timeout: int = 30
    openai_max_tokens: int = 1000
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_password: str = os.getenv("REDIS_PASSWORD", "askflash123")
    redis_db: int = 0
    redis_max_connections: int = 10
    
    # RabbitMQ settings
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://askflash:askflash123@localhost:5672/")
    rabbitmq_queue: str = "intent.task"
    rabbitmq_prefetch_count: int = 10
    rabbitmq_reconnect_delay: int = 5
    
    # Task processing settings
    max_concurrent_tasks: int = 10
    task_timeout: int = 60
    retry_attempts: int = 3
    retry_delay: int = 2
    
    # Intent analysis settings
    min_query_length: int = 3
    max_query_length: int = 2000
    complexity_threshold_words: int = 10
    web_search_keywords: list = [
        "current", "today", "latest", "recent", "news", "weather", 
        "stock", "price", "what's happening", "real-time", "live"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = IntentAgentSettings() 