from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any, Optional
import asyncio

from core.config import settings
from services.auth_manager import AuthManager
from services.user_manager import UserManager  
from services.session_manager import SessionManager
from api.routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
auth_manager: Optional[AuthManager] = None
user_manager: Optional[UserManager] = None
session_manager: Optional[SessionManager] = None

# Security
security = HTTPBearer(auto_error=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global auth_manager, user_manager, session_manager
    
    logger.info("🔐 Authentication Service starting up...")
    
    try:
        # Initialize managers
        auth_manager = AuthManager()
        user_manager = UserManager()
        session_manager = SessionManager()
        
        # Initialize database connections
        await auth_manager.initialize()
        await user_manager.initialize()
        await session_manager.initialize()
        
        logger.info("✅ Authentication services initialized")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    finally:
        logger.info("🛑 Authentication Service shutting down...")
        if session_manager:
            await session_manager.close()

app = FastAPI(
    title="Authentication Service",
    description="🔐 Enterprise Authentication and Authorization Service for Flash AI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Set service references for API routes
@app.on_event("startup")
async def set_api_services():
    """Set service references for API routes"""
    from api.routes import set_services
    set_services(auth_manager, user_manager, session_manager)

# Dependency for token validation
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and return current user"""
    if not credentials:
        return None  # Allow anonymous access for some endpoints
    
    try:
        if not auth_manager:
            raise HTTPException(status_code=503, detail="Auth service unavailable")
        
        # Validate token
        user_data = await auth_manager.validate_token(credentials.credentials)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "Authentication Service",
        "version": "1.0.0", 
        "status": "operational",
        "description": "🔐 Enterprise authentication and authorization for Flash AI",
        "features": [
            "JWT authentication",
            "Role-based access control",
            "Session management",
            "User management",
            "API key management"
        ]
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    try:
        # Check if services are initialized
        services_healthy = (
            auth_manager is not None and
            user_manager is not None and
            session_manager is not None
        )
        
        if services_healthy:
            return {
                "status": "healthy",
                "service": "Authentication Service",
                "version": "1.0.0"
            }
        else:
            raise HTTPException(status_code=503, detail="Services not initialized")
            
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get authentication service capabilities"""
    return {
        "service_type": "authentication",
        "version": "1.0.0",
        "authentication_methods": [
            "username_password",
            "api_key",
            "jwt_token"
        ],
        "authorization_features": [
            "role_based_access_control",
            "permission_management",
            "resource_access_control"
        ],
        "enterprise_features": [
            "session_management",
            "audit_logging",
            "password_policies",
            "account_lockout"
        ],
        "integrations": [
            "oauth2",
            "saml",
            "active_directory"
        ],
        "performance": {
            "token_validation": "<50ms",
            "login_time": "<500ms",
            "concurrent_sessions": "10000+"
        }
    }

@app.get("/validate-token")
async def validate_token_endpoint(current_user: dict = Depends(get_current_user)):
    """Validate token endpoint for other services"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {
        "valid": True,
        "user": current_user,
        "permissions": current_user.get("permissions", []),
        "roles": current_user.get("roles", [])
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP error in Authentication Service: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "service": "Authentication Service"
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error in Authentication Service: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal authentication service error",
            "service": "Authentication Service"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8014, 
        reload=True,
        log_level="info"
    ) 