from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any, Optional
import asyncio
import os

from core.config import settings
from services.content_moderator import ContentModerator
from services.rabbitmq_consumer import RabbitMQConsumer
from api.routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
content_moderator: Optional[ContentModerator] = None
rabbitmq_consumer: Optional[RabbitMQConsumer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global content_moderator, rabbitmq_consumer
    
    logger.info("🛡️ Moderator Agent starting up...")
    
    try:
        # Initialize Content Moderator
        content_moderator = ContentModerator()
        await content_moderator.initialize()
        logger.info("✅ Content Moderator initialized")
        
        # Initialize RabbitMQ consumer
        rabbitmq_consumer = RabbitMQConsumer(content_moderator)
        
        # Start consuming messages in background
        consumer_task = asyncio.create_task(rabbitmq_consumer.start_consuming())
        logger.info("✅ RabbitMQ consumer started")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    finally:
        logger.info("🛑 Moderator Agent shutting down...")
        if rabbitmq_consumer:
            await rabbitmq_consumer.close()

app = FastAPI(
    title="Moderator Agent",
    description="🛡️ Content Moderation and Safety Agent for Flash AI MCP Architecture",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API router
app.include_router(api_router)

# Set service references for API routes
@app.on_event("startup")
async def set_api_services():
    """Set service references for API routes"""
    from api.routes import set_services
    set_services(content_moderator, rabbitmq_consumer)

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "Moderator Agent",
        "version": "1.0.0",
        "status": "operational",
        "description": "🛡️ Content moderation and safety validation for Flash AI",
        "capabilities": [
            "content_safety_check",
            "toxicity_detection",
            "quality_assessment",
            "policy_compliance",
            "content_filtering"
        ]
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    try:
        # Check if services are initialized
        services_healthy = (
            content_moderator is not None and
            rabbitmq_consumer is not None
        )
        
        if services_healthy:
            return {
                "status": "healthy",
                "service": "Moderator Agent",
                "version": "1.0.0"
            }
        else:
            raise HTTPException(status_code=503, detail="Services not initialized")
            
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get agent capabilities"""
    return {
        "agent_type": "moderator",
        "version": "1.0.0",
        "capabilities": {
            "content_checks": [
                "toxicity_detection",
                "hate_speech_detection", 
                "profanity_filtering",
                "spam_detection",
                "quality_assessment"
            ],
            "safety_features": [
                "policy_compliance",
                "content_filtering",
                "risk_assessment",
                "confidence_scoring"
            ],
            "moderation_types": [
                "text_content",
                "ai_responses",
                "user_input",
                "search_results"
            ]
        },
        "performance": {
            "avg_check_time": "200-500ms",
            "max_concurrent_checks": 10,
            "confidence_threshold": 0.7
        },
        "queue_info": {
            "listens_to": "moderator.task",
            "publishes_to": "mcp.responses"
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP error in Moderator Agent: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "service": "Moderator Agent"
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error in Moderator Agent: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Moderator Agent error",
            "service": "Moderator Agent"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8013, 
        reload=True,
        log_level="info"
    ) 