from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any
import os

from core.config import settings
from core.database import get_db
from api.routes import router as api_router
from services.enhanced_search import EnhancedDocumentationService
from services.vector_manager import VectorStoreManager
from services.alias_discovery import SmartAliasDiscovery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
vector_manager = VectorStoreManager()
alias_discovery = SmartAliasDiscovery()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🔍 Flash AI Embedding Service starting up...")
    
    # Initialize services
    logger.info("✅ Vector Store Manager initialized")
    logger.info("✅ Enhanced Documentation Service ready")
    logger.info("✅ Smart Alias Discovery loaded")
    
    # Initialize Qdrant connection
    await vector_manager.initialize_collections()
    logger.info("✅ Qdrant collections verified")
    
    yield
    
    logger.info("🛑 Flash AI Embedding Service shutting down...")

app = FastAPI(
    title="Flash AI Embedding Service",
    description="🔍 Document Processing, Vector Generation & Semantic Search",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint returning Embedding Service status"""
    return {
        "status": "operational",
        "service": "Flash AI Embedding Service",
        "version": "2.0.0",
        "description": "🔍 Document Processing, Vector Generation & Semantic Search",
        "capabilities": [
            "Enhanced Documentation Processing",
            "Smart Alias Discovery",
            "Semantic Vector Search",
            "Multi-source Document Indexing",
            "Automatic Relationship Mapping",
            "Content-based Chunking"
        ]
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    try:
        # Check Qdrant connection
        qdrant_status = await vector_manager.health_check()
        
        # Check alias discovery cache
        alias_status = alias_discovery.is_cache_healthy()
        
        return {
            "status": "healthy",
            "service": "embedding",
            "qdrant_connection": str(qdrant_status),
            "alias_discovery": "ready" if alias_status else "initializing",
            "enhanced_search": "ready",
            "openai_configured": str(bool(settings.OPENAI_API_KEY))
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get embedding service capabilities"""
    return {
        "document_processing": {
            "enhanced_chunking": True,
            "html_cleaning": True,
            "structure_preservation": True,
            "semantic_metadata": True
        },
        "vector_operations": {
            "embedding_generation": True,
            "semantic_search": True,
            "hybrid_search": True,
            "similarity_scoring": True
        },
        "alias_discovery": {
            "automatic_detection": True,
            "relationship_mapping": True,
            "co_occurrence_analysis": True,
            "confidence_scoring": True
        },
        "supported_sources": [
            "azure_devops_wiki",
            "confluence", 
            "notion",
            "github_repos",
            "sharepoint"
        ]
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP error in embedding service: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "service": "Flash AI Embedding Service"
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error in embedding service: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal embedding service error",
            "service": "Flash AI Embedding Service"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8002, 
        reload=True,
        log_level="info"
    ) 