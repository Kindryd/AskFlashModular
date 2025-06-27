from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any, Optional, List
import asyncio
import os

from core.config import settings
from services.web_searcher import WebSearcher
from services.rabbitmq_consumer import RabbitMQConsumer
from api.routes import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
web_searcher: Optional[WebSearcher] = None
rabbitmq_consumer: Optional[RabbitMQConsumer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global web_searcher, rabbitmq_consumer
    
    logger.info("🔍 Web Search Agent starting up...")
    
    try:
        # Initialize Web Searcher
        web_searcher = WebSearcher()
        logger.info("✅ Web Searcher initialized")
        
        # Initialize RabbitMQ consumer
        rabbitmq_consumer = RabbitMQConsumer(web_searcher)
        
        # Start consuming messages in background
        consumer_task = asyncio.create_task(rabbitmq_consumer.start_consuming())
        logger.info("✅ RabbitMQ consumer started")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    finally:
        logger.info("🛑 Web Search Agent shutting down...")
        if rabbitmq_consumer:
            await rabbitmq_consumer.close()

app = FastAPI(
    title="Web Search Agent",
    description="🔍 DuckDuckGo Web Search Agent for Flash AI MCP Architecture",
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
    set_services(web_searcher, rabbitmq_consumer)

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "service": "Web Search Agent",
        "version": "1.0.0",
        "status": "operational",
        "description": "🔍 DuckDuckGo web search capabilities for Flash AI",
        "capabilities": [
            "web_search",
            "result_ranking",
            "content_extraction",
            "relevance_scoring"
        ]
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    try:
        # Check if services are initialized
        services_healthy = (
            web_searcher is not None and
            rabbitmq_consumer is not None
        )
        
        if services_healthy:
            return {
                "status": "healthy",
                "service": "Web Search Agent",
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
        "agent_type": "websearch",
        "version": "1.0.0",
        "capabilities": {
            "search_engines": ["duckduckgo"],
            "result_formats": ["json", "structured"],
            "max_results": 20,
            "features": [
                "web_search",
                "instant_answers",
                "result_ranking",
                "content_extraction",
                "relevance_scoring",
                "deduplication"
            ]
        },
        "performance": {
            "avg_search_time": "2-5 seconds",
            "max_concurrent_searches": 5,
            "timeout": "30 seconds"
        },
        "queue_info": {
            "listens_to": "websearch.task",
            "publishes_to": "mcp.responses"
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP error in Web Search Agent: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "service": "Web Search Agent"
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error in Web Search Agent: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Web Search Agent error",
            "service": "Web Search Agent"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8012, 
        reload=True,
        log_level="info"
    ) 