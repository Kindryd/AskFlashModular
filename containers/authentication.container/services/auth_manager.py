import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config import settings

logger = logging.getLogger(__name__)

class AuthManager:
    """Core authentication manager with JWT and password handling"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_client: Optional[redis.Redis] = None
        self.db_engine = None
        self.db_session_factory = None
        
    async def initialize(self):
        """Initialize database and Redis connections"""
        try:
            # Initialize Redis for session management
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            await self.redis_client.ping()
            
            # Initialize database engine
            self.db_engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_pre_ping=True
            )
            
            self.db_session_factory = sessionmaker(
                self.db_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("✅ Authentication manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize auth manager: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> tuple[bool, List[str]]:
        """Validate password meets security requirements"""
        issues = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            issues.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user data"""
        try:
            # Decode JWT
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Check token type
            token_type = payload.get("type")
            if token_type != "access":
                return None
            
            # Get user info
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Check if token is blacklisted (if implementing token blacklist)
            if self.redis_client:
                is_blacklisted = await self.redis_client.get(f"blacklist:{token}")
                if is_blacklisted:
                    return None
            
            # Return user data from token
            return {
                "user_id": user_id,
                "username": payload.get("username"),
                "email": payload.get("email"),
                "roles": payload.get("roles", []),
                "permissions": payload.get("permissions", []),
                "token_type": token_type
            }
            
        except JWTError as e:
            logger.warning(f"JWT validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    async def revoke_token(self, token: str):
        """Add token to blacklist"""
        try:
            if self.redis_client:
                # Decode to get expiration
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                exp = payload.get("exp")
                
                if exp:
                    # Calculate TTL until token would naturally expire
                    expire_time = datetime.fromtimestamp(exp)
                    ttl = int((expire_time - datetime.utcnow()).total_seconds())
                    
                    if ttl > 0:
                        await self.redis_client.setex(f"blacklist:{token}", ttl, "revoked")
                        
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
    
    def generate_api_key(self, user_id: str) -> str:
        """Generate API key for a user"""
        random_part = secrets.token_urlsafe(settings.API_KEY_LENGTH)
        api_key = f"{settings.API_KEY_PREFIX}{user_id}_{random_part}"
        return api_key
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user data"""
        try:
            if not api_key.startswith(settings.API_KEY_PREFIX):
                return None
            
            # API key validation would typically involve database lookup
            # For now, return basic structure
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            if self.redis_client:
                # Check if API key exists and is valid
                key_data = await self.redis_client.get(f"api_key:{api_key_hash}")
                if key_data:
                    import json
                    return json.loads(key_data)
            
            return None
            
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None
    
    async def track_login_attempt(self, identifier: str, success: bool, ip_address: str = None):
        """Track login attempts for security monitoring"""
        try:
            if self.redis_client:
                timestamp = datetime.utcnow().isoformat()
                
                # Track failed attempts for account lockout
                if not success:
                    key = f"failed_attempts:{identifier}"
                    current_attempts = await self.redis_client.get(key)
                    attempts = int(current_attempts) + 1 if current_attempts else 1
                    
                    # Set expiration for lockout period
                    await self.redis_client.setex(
                        key, 
                        settings.LOCKOUT_DURATION_MINUTES * 60, 
                        str(attempts)
                    )
                    
                    # Check if account should be locked
                    if attempts >= settings.MAX_LOGIN_ATTEMPTS:
                        await self.redis_client.setex(
                            f"locked:{identifier}",
                            settings.LOCKOUT_DURATION_MINUTES * 60,
                            timestamp
                        )
                        logger.warning(f"Account locked due to excessive failed attempts: {identifier}")
                else:
                    # Clear failed attempts on successful login
                    await self.redis_client.delete(f"failed_attempts:{identifier}")
                    await self.redis_client.delete(f"locked:{identifier}")
                
                # Log audit trail if enabled
                if settings.LOG_AUTH_EVENTS:
                    audit_data = {
                        "identifier": identifier,
                        "success": success,
                        "timestamp": timestamp,
                        "ip_address": ip_address
                    }
                    
                    # Store in audit log (could be database or separate log service)
                    await self.redis_client.lpush(
                        f"audit_log:{identifier}",
                        str(audit_data)
                    )
                    # Keep last 100 audit entries
                    await self.redis_client.ltrim(f"audit_log:{identifier}", 0, 99)
                    
        except Exception as e:
            logger.error(f"Error tracking login attempt: {e}")
    
    async def is_account_locked(self, identifier: str) -> bool:
        """Check if account is currently locked"""
        try:
            if self.redis_client:
                is_locked = await self.redis_client.get(f"locked:{identifier}")
                return is_locked is not None
            return False
        except Exception as e:
            logger.error(f"Error checking account lock status: {e}")
            return False
    
    async def get_failed_attempts(self, identifier: str) -> int:
        """Get current failed login attempt count"""
        try:
            if self.redis_client:
                attempts = await self.redis_client.get(f"failed_attempts:{identifier}")
                return int(attempts) if attempts else 0
            return 0
        except Exception as e:
            logger.error(f"Error getting failed attempts: {e}")
            return 0
    
    async def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication service statistics"""
        stats = {
            "service": "Authentication Manager",
            "version": settings.SERVICE_VERSION,
            "security_config": {
                "password_min_length": settings.PASSWORD_MIN_LENGTH,
                "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
                "lockout_duration_minutes": settings.LOCKOUT_DURATION_MINUTES,
                "session_timeout_minutes": settings.SESSION_TIMEOUT_MINUTES
            },
            "jwt_config": {
                "algorithm": settings.ALGORITHM,
                "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
                "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_DAYS
            },
            "features": {
                "audit_logging": settings.ENABLE_AUDIT_LOGGING,
                "sso_enabled": settings.ENABLE_SSO,
                "api_keys": True,
                "token_blacklist": True
            }
        }
        
        try:
            if self.redis_client:
                # Get some basic stats
                stats["redis_connected"] = True
                stats["cache_keys"] = await self.redis_client.dbsize()
            else:
                stats["redis_connected"] = False
        except Exception:
            stats["redis_connected"] = False
        
        return stats 