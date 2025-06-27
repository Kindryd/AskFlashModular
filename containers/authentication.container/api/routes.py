from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/api/v1", tags=["authentication"])

# Global reference to services (will be set from main.py)
auth_manager = None
user_manager = None
session_manager = None

def set_services(auth_mgr, user_mgr, session_mgr):
    """Set service references from main application"""
    global auth_manager, user_manager, session_manager
    auth_manager = auth_mgr
    user_manager = user_mgr
    session_manager = session_mgr

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str]
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    is_active: bool

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, req: Request):
    """User login endpoint"""
    try:
        if not auth_manager or not user_manager:
            raise HTTPException(status_code=503, detail="Authentication services unavailable")
        
        # Get client IP for audit logging
        client_ip = req.client.host if req.client else "unknown"
        
        # Check if account is locked
        if await auth_manager.is_account_locked(request.username):
            await auth_manager.track_login_attempt(request.username, False, client_ip)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed attempts"
            )
        
        # Validate credentials
        user = await user_manager.authenticate_user(request.username, request.password)
        if not user:
            await auth_manager.track_login_attempt(request.username, False, client_ip)
            
            # Check failed attempt count
            failed_attempts = await auth_manager.get_failed_attempts(request.username)
            remaining_attempts = settings.MAX_LOGIN_ATTEMPTS - failed_attempts
            
            detail = "Invalid username or password"
            if remaining_attempts <= 2:
                detail += f". {remaining_attempts} attempts remaining before account lockout."
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=detail
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Create tokens
        token_data = {
            "sub": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "permissions": user["permissions"]
        }
        
        access_token = auth_manager.create_access_token(token_data)
        refresh_token = auth_manager.create_refresh_token({"sub": user["user_id"]})
        
        # Create session
        if session_manager:
            await session_manager.create_session(
                user["user_id"], 
                access_token, 
                client_ip
            )
        
        # Track successful login
        await auth_manager.track_login_attempt(request.username, True, client_ip)
        
        logger.info(f"✅ User logged in: {request.username}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """User registration endpoint"""
    try:
        if not auth_manager or not user_manager:
            raise HTTPException(status_code=503, detail="Authentication services unavailable")
        
        # Validate password strength
        is_strong, issues = auth_manager.validate_password_strength(request.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet requirements", "issues": issues}
            )
        
        # Check if user already exists
        existing_user = await user_manager.get_user_by_username(request.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )
        
        existing_email = await user_manager.get_user_by_email(request.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Create user
        user = await user_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        logger.info(f"✅ User registered: {request.username}")
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        if not auth_manager or not user_manager:
            raise HTTPException(status_code=503, detail="Authentication services unavailable")
        
        # Validate refresh token
        payload = await auth_manager.validate_token(refresh_token)
        if not payload or payload.get("token_type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user data
        user = await user_manager.get_user_by_id(payload["user_id"])
        if not user or not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        token_data = {
            "sub": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "roles": user["roles"],
            "permissions": user["permissions"]
        }
        
        access_token = auth_manager.create_access_token(token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """User logout endpoint"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided"
            )
        
        if not auth_manager or not session_manager:
            raise HTTPException(status_code=503, detail="Authentication services unavailable")
        
        # Validate token
        user_data = await auth_manager.validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Revoke token
        await auth_manager.revoke_token(credentials.credentials)
        
        # End session
        await session_manager.end_session(user_data["user_id"], credentials.credentials)
        
        logger.info(f"✅ User logged out: {user_data['username']}")
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/profile", response_model=UserResponse)
async def get_profile(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user profile"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided"
            )
        
        if not auth_manager or not user_manager:
            raise HTTPException(status_code=503, detail="Authentication services unavailable")
        
        # Validate token
        user_data = await auth_manager.validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get full user profile
        user = await user_manager.get_user_by_id(user_data["user_id"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Profile retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Profile retrieval failed")

@router.post("/api-key")
async def generate_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Generate API key for user"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided"
            )
        
        if not auth_manager or not user_manager:
            raise HTTPException(status_code=503, detail="Authentication services unavailable")
        
        # Validate token
        user_data = await auth_manager.validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Generate API key
        api_key = auth_manager.generate_api_key(user_data["user_id"])
        
        # Store API key (in real implementation, would store in database)
        await user_manager.store_api_key(user_data["user_id"], api_key)
        
        return {
            "api_key": api_key,
            "message": "API key generated successfully",
            "note": "Store this key securely - it won't be shown again"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ API key generation error: {e}")
        raise HTTPException(status_code=500, detail="API key generation failed")

@router.get("/sessions")
async def get_active_sessions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get user's active sessions"""
    try:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No token provided"
            )
        
        if not auth_manager or not session_manager:
            raise HTTPException(status_code=503, detail="Authentication services unavailable")
        
        # Validate token
        user_data = await auth_manager.validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get active sessions
        sessions = await session_manager.get_user_sessions(user_data["user_id"])
        
        return {
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Sessions retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Sessions retrieval failed")

@router.get("/stats")
async def get_auth_stats():
    """Get authentication service statistics"""
    try:
        if not auth_manager:
            raise HTTPException(status_code=503, detail="Authentication manager unavailable")
        
        stats = await auth_manager.get_auth_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Stats API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_token_route(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate token (for other services)"""
    try:
        if not credentials:
            return {"valid": False, "reason": "No token provided"}
        
        if not auth_manager:
            raise HTTPException(status_code=503, detail="Authentication manager unavailable")
        
        # Validate token
        user_data = await auth_manager.validate_token(credentials.credentials)
        
        if user_data:
            return {
                "valid": True,
                "user": user_data,
                "permissions": user_data.get("permissions", []),
                "roles": user_data.get("roles", [])
            }
        else:
            return {"valid": False, "reason": "Invalid or expired token"}
        
    except Exception as e:
        logger.error(f"❌ Token validation error: {e}")
        return {"valid": False, "reason": f"Validation error: {str(e)}"}

@router.post("/test")
async def test_authentication():
    """Test endpoint for authentication functionality"""
    return {
        "status": "test_mode",
        "message": "Authentication service is operational",
        "features": [
            "JWT authentication",
            "user_management",
            "session_management",
            "api_key_generation",
            "password_security"
        ],
        "config": {
            "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
            "password_min_length": settings.PASSWORD_MIN_LENGTH
        }
    } 