from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class GatewaySettings(BaseSettings):
    """Gateway-specific configuration settings"""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Flash AI Gateway"
    GATEWAY_VERSION: str = "2.0.0"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]  # Frontend URL
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str], None]) -> List[str]:
        # Handle None or empty values
        if v is None or v == "":
            return ["http://localhost:3000"]
        
        # Handle string input
        if isinstance(v, str):
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
            else:
                # Handle JSON-like string
                try:
                    import json
                    return json.loads(v)
                except:
                    return ["http://localhost:3000"]
        
        # Handle list input
        elif isinstance(v, list):
            return v
        
        # Fallback to default
        return ["http://localhost:3000"]
    
    # Service URLs (can be overridden by environment variables)
    CONVERSATION_SERVICE_URL: str = "http://conversation:8001"
    EMBEDDING_SERVICE_URL: str = "http://embedding:8002"
    MCP_SERVICE_URL: str = "http://mcp:8003"
    PROJECT_MANAGER_SERVICE_URL: str = "http://project-manager:8004"
    AUTHENTICATION_SERVICE_URL: str = "http://authentication:8014"
    ADAPTIVE_ENGINE_SERVICE_URL: str = "http://adaptive-engine:8015"
    LOCAL_LLM_SERVICE_URL: str = "http://local-llm:8006"
    ANALYTICS_SERVICE_URL: str = "http://analytics:8007"
    
    # Gateway Configuration
    REQUEST_TIMEOUT: int = 30  # Timeout for service requests
    RETRY_ATTEMPTS: int = 3  # Number of retry attempts
    RETRY_DELAY: float = 1.0  # Delay between retries
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: int = 5  # Health check timeout
    HEALTH_CHECK_INTERVAL: int = 30  # Health check interval in seconds
    
    # Rate Limiting (if needed)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_REQUESTS: int = 100  # Requests per minute
    RATE_LIMIT_WINDOW: int = 60  # Window in seconds
    
    # Flash AI Branding
    FLASH_EMOJI: str = "🐄"
    FLASH_PRIMARY_COLOR: str = "#7ed321"  # Flash Green
    FLASH_MOTTO: str = "Making enterprise knowledge easier"
    
    # Security Settings
    SECRET_KEY: str = "flash-ai-gateway-secret-key"  # Change in production
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix="GATEWAY_",
        env_file=".env"
    )

# Global settings instance
settings = GatewaySettings()

def get_settings() -> GatewaySettings:
    """Get the global gateway settings instance"""
    return settings 