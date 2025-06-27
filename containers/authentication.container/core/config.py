from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import secrets

class AuthenticationSettings(BaseSettings):
    """Authentication service configuration settings"""
    
    # Service Configuration
    SERVICE_NAME: str = "Authentication Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8014
    
    # JWT Configuration
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate secure key
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HASH_ROUNDS: int = 12
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    SESSION_TIMEOUT_MINUTES: int = 480  # 8 hours
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://askflash:askflash123@postgres:5432/askflash"
    
    # Redis Configuration (for sessions and caching)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "askflash123"
    REDIS_DB: int = 1  # Use different DB than other services
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # API Key Configuration
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "flash_"
    
    # Role Configuration
    DEFAULT_USER_ROLE: str = "user"
    ADMIN_ROLE: str = "admin"
    SYSTEM_ROLES: List[str] = ["user", "admin", "moderator", "developer"]
    
    # Permission Categories
    PERMISSION_CATEGORIES: List[str] = [
        "chat", "search", "admin", "moderation", "analytics"
    ]
    
    # Enterprise Features
    ENABLE_AUDIT_LOGGING: bool = True
    ENABLE_SSO: bool = False  # Enable for enterprise
    SSO_PROVIDER: Optional[str] = None  # "saml", "oauth", "active_directory"
    
    # Rate Limiting
    LOGIN_RATE_LIMIT: int = 10  # attempts per minute
    API_RATE_LIMIT: int = 1000  # requests per minute
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_AUTH_EVENTS: bool = True
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix="AUTH_",
        env_file=".env"
    )

# Global settings instance
settings = AuthenticationSettings()

def get_settings() -> AuthenticationSettings:
    """Get the global authentication settings instance"""
    return settings 