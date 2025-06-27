from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import logging

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["websearch"])

# Global reference to services (will be set from main.py)
web_searcher = None
rabbitmq_consumer = None

def set_services(searcher, consumer):
    """Set service references from main application"""
    global web_searcher, rabbitmq_consumer
    web_searcher = searcher
    rabbitmq_consumer = consumer

@router.post("/search")
async def search_web(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Perform web search (direct API call, not via queue)"""
    try:
        if not web_searcher:
            raise HTTPException(status_code=503, detail="Web searcher not available")
        
        query = request.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        max_results = request.get("max_results", settings.MAX_RESULTS)
        search_type = request.get("search_type", "web")
        
        logger.info(f"🔍 Direct search request: {query[:50]}...")
        
        if search_type == "instant":
            result = await web_searcher.search_instant_answers(query)
        else:
            result = await web_searcher.search_web(query, max_results)
        
        return {
            "status": "success",
            "result": result,
            "direct_call": True
        }
        
    except Exception as e:
        logger.error(f"❌ Search API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/instant")
async def search_instant_answers(query: str) -> Dict[str, Any]:
    """Get instant answers for a query"""
    try:
        if not web_searcher:
            raise HTTPException(status_code=503, detail="Web searcher not available")
        
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        logger.info(f"🎯 Instant answer request: {query[:50]}...")
        
        result = await web_searcher.search_instant_answers(query)
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"❌ Instant answer API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_search_stats() -> Dict[str, Any]:
    """Get web search service statistics"""
    try:
        if not web_searcher:
            raise HTTPException(status_code=503, detail="Web searcher not available")
        
        stats = await web_searcher.get_stats()
        
        # Add queue status if available
        if rabbitmq_consumer:
            queue_status = await rabbitmq_consumer.get_queue_status()
            stats["queue_status"] = queue_status
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Stats API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """Get RabbitMQ queue status"""
    try:
        if not rabbitmq_consumer:
            raise HTTPException(status_code=503, detail="RabbitMQ consumer not available")
        
        status = await rabbitmq_consumer.get_queue_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Queue status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_search(request: Dict[str, Any]) -> Dict[str, Any]:
    """Test endpoint for web search functionality"""
    try:
        query = request.get("query", "test search")
        
        return {
            "status": "test_mode",
            "query": query,
            "message": "Web search agent is operational",
            "capabilities": [
                "web_search",
                "instant_answers", 
                "result_ranking",
                "content_extraction"
            ],
            "config": {
                "max_results": settings.MAX_RESULTS,
                "region": settings.DUCKDUCKGO_REGION,
                "safesearch": settings.DUCKDUCKGO_SAFESEARCH
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Test API error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 