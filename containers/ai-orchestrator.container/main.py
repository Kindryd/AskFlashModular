from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
import os

from core.config import settings
from core.database import get_db
from api.routes import router as api_router
from services.quality_analyzer import InformationQualityAnalyzer
from services.intent_ai import ConversationIntentAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
quality_analyzer = InformationQualityAnalyzer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🧠 Flash AI Orchestrator starting up...")
    
    # Initialize services
    logger.info("✅ Information Quality Analyzer initialized")
    logger.info("✅ Intent AI system ready")
    
    yield
    
    logger.info("🛑 Flash AI Orchestrator shutting down...")

app = FastAPI(
    title="Flash AI Orchestrator",
    description="🧠 AI Provider Management & Information Quality Enhancement",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint returning AI Orchestrator status"""
    return {
        "status": "operational",
        "service": "Flash AI Orchestrator",
        "version": "2.0.0",
        "description": "🧠 AI Provider Management & Information Quality Enhancement",
        "capabilities": [
            "Information Quality Analysis",
            "Intent AI (GPT-3.5)",
            "Provider Routing",
            "Quality-Aware Prompts",
            "Cross-Reference Validation"
        ]
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    try:
        # Basic health checks
        openai_configured = bool(settings.OPENAI_API_KEY)
        
        return {
            "status": "healthy",
            "service": "ai-orchestrator",
            "openai_configured": str(openai_configured),
            "quality_analyzer": "ready",
            "intent_ai": "ready"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get AI orchestrator capabilities"""
    return {
        "information_quality": {
            "conflict_detection": True,
            "authority_scoring": True,
            "freshness_scoring": True,
            "cross_reference_validation": True
        },
        "intent_analysis": {
            "conversation_analysis": True,
            "context_summarization": True,
            "ai_guidance": True,
            "model": "gpt-3.5-turbo"
        },
        "provider_routing": {
            "openai_gpt4": True,
            "openai_gpt35": True,
            "fallback_strategies": True
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP error in AI orchestrator: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "service": "Flash AI Orchestrator"
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error in AI orchestrator: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal AI orchestrator error",
            "service": "Flash AI Orchestrator"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8003, 
        reload=True,
        log_level="info"
    ) 