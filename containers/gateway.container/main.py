from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import httpx
import logging
from typing import Dict, Any
import os

from core.config import settings
from api.routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service discovery mapping
SERVICE_URLS = {
    "conversation": os.getenv("CONVERSATION_SERVICE_URL", "http://conversation:8001"),
    "embedding": os.getenv("EMBEDDING_SERVICE_URL", "http://embedding:8002"),
    "mcp": os.getenv("MCP_SERVICE_URL", "http://mcp:8003"),
    "project-manager": os.getenv("PROJECT_MANAGER_SERVICE_URL", "http://project-manager:8004"),
    "adaptive-engine": os.getenv("ADAPTIVE_ENGINE_SERVICE_URL", "http://adaptive-engine:8015"),
    "local-llm": os.getenv("LOCAL_LLM_SERVICE_URL", "http://local-llm:8006"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://analytics:8007"),
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Flash AI Gateway starting up...")
    
    # Health check all services on startup
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICE_URLS.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} service healthy at {service_url}")
                else:
                    logger.warning(f"⚠️  {service_name} service unhealthy: {response.status_code}")
            except Exception as e:
                logger.warning(f"❌ {service_name} service unavailable: {e}")
    
    yield
    
    logger.info("🛑 Flash AI Gateway shutting down...")

app = FastAPI(
    title="Flash AI Gateway",
    description="🐄 Flash AI Assistant - API Gateway for microservices architecture",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for Flash AI branding
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint returning Flash AI Gateway status"""
    return {
        "status": "operational",
        "service": "Flash AI Gateway",
        "version": "2.0.0",
        "description": "🐄 Flash AI Assistant - Making enterprise knowledge easier",
        "architecture": "microservices",
        "services": list(SERVICE_URLS.keys())
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check routed through MCP"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get comprehensive system status from MCP
            mcp_url = SERVICE_URLS.get("mcp", "http://mcp:8003")
            response = await client.get(f"{mcp_url}/api/v1/system/status")
            
            if response.status_code == 200:
                mcp_status = response.json()
                
                # Format for gateway response
                health_status = {
                    "gateway": "healthy",
                    "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
                    "architecture": "microservices_mcp",
                    "mcp_health": mcp_status.get("overall_health", "unknown"),
                    "system_summary": mcp_status.get("health_summary", {}),
                    "active_tasks": mcp_status.get("active_tasks", 0),
                    "agents": mcp_status.get("agents", {}),
                    "infrastructure": mcp_status.get("infrastructure", {}),
                    "overall": mcp_status.get("overall_health", "unknown")
                }
                
                return health_status
            else:
                # MCP is down, provide basic gateway status
                return {
                    "gateway": "healthy",
                    "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
                    "mcp_health": "unavailable",
                    "overall": "degraded",
                    "error": f"MCP health check failed: {response.status_code}"
                }
                
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "gateway": "healthy",
            "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
            "mcp_health": "unavailable", 
            "overall": "degraded",
            "error": f"Cannot reach MCP: {str(e)}"
        }

@app.get("/services")
async def service_discovery() -> Dict[str, Any]:
    """Service discovery endpoint"""
    return {
        "services": SERVICE_URLS,
        "architecture": "microservices",
        "communication": "http + redis events"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler with Flash AI branding"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "service": "Flash AI Gateway",
            "path": str(request.url.path)
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error in gateway: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "service": "Flash AI Gateway",
            "path": str(request.url.path)
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    ) 