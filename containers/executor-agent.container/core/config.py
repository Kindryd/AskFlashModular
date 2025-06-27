"""
Configuration settings for Executor Agent
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional, List

class ExecutorAgentSettings(BaseSettings):
    """Configuration settings for Executor Agent"""
    
    # Service settings
    service_name: str = "Flash AI Executor Agent"
    service_version: str = "1.0.0"
    debug: bool = False
    
    # OpenAI settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model_primary: str = "gpt-4"
    openai_model_fallback: str = "gpt-3.5-turbo-16k"
    openai_model_simple: str = "gpt-3.5-turbo"
    openai_timeout: int = 60
    openai_max_tokens: int = 2000
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_password: str = os.getenv("REDIS_PASSWORD", "askflash123")
    redis_db: int = 0
    redis_max_connections: int = 10
    
    # RabbitMQ settings
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://askflash:askflash123@localhost:5672/")
    rabbitmq_queue: str = "executor.task"
    rabbitmq_prefetch_count: int = 5  # Lower for more intensive tasks
    rabbitmq_reconnect_delay: int = 5
    
    # Task processing settings
    max_concurrent_tasks: int = 5
    task_timeout: int = 120  # 2 minutes for complex reasoning
    retry_attempts: int = 2
    retry_delay: int = 3
    
    # AI reasoning settings
    max_context_tokens: int = 6000
    max_documents_per_query: int = 10
    min_confidence_threshold: float = 0.7
    enable_reasoning_trace: bool = True
    reasoning_temperature: float = 0.3
    
    # Document processing settings
    max_document_length: int = 2000  # Characters per document
    document_overlap_ratio: float = 0.1
    relevance_threshold: float = 0.6
    
    # Response generation settings
    response_formats: List[str] = [
        "structured", "conversational", "technical", "summary", "detailed"
    ]
    default_response_format: str = "conversational"
    include_sources: bool = True
    max_response_length: int = 1500
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = ExecutorAgentSettings() 