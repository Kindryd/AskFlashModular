"""
API Routes for Executor Agent

This module provides REST endpoints for the Executor Agent container.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

class ExecuteRequest(BaseModel):
    """Request model for manual AI execution"""
    query: str
    context: str = ""
    documents: list = []
    strategy: dict = {}

@router.get("/stats")
async def get_stats():
    """Get agent processing statistics"""
    try:
        from main import consumer
        
        if consumer:
            stats = await consumer.get_stats()
            return {
                "agent": "ai_executor",
                "stats": stats,
                "status": "operational" if stats["is_consuming"] else "stopped"
            }
        else:
            return {
                "agent": "ai_executor", 
                "stats": {},
                "status": "not_initialized"
            }
            
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.post("/execute")
async def manual_execute(request: ExecuteRequest):
    """Manually trigger AI execution (for testing)"""
    try:
        from main import ai_executor
        
        if not ai_executor:
            raise HTTPException(status_code=503, detail="AI executor not initialized")
        
        # Generate test task ID
        import uuid
        task_id = f"test_{uuid.uuid4()}"
        
        # Prepare reasoning request
        reasoning_request = {
            "query": request.query,
            "context": request.context,
            "documents": request.documents,
            "strategy": request.strategy or {"approach": "standard_query", "complexity_level": "medium"},
            "intent_analysis": {"primary_intent": "informational"}
        }
        
        # Perform execution
        result = await ai_executor.execute_reasoning(
            task_id=task_id,
            reasoning_request=reasoning_request
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "execution_result": result
        }
        
    except Exception as e:
        logger.error(f"Manual execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.get("/queue/status")
async def get_queue_status():
    """Get RabbitMQ queue status"""
    try:
        from main import consumer
        
        if not consumer:
            return {"status": "consumer_not_initialized"}
        
        stats = await consumer.get_stats()
        
        return {
            "queue_name": "executor.task",
            "connection_status": stats["connection_status"],
            "is_consuming": stats["is_consuming"],
            "processed_count": stats["processed_count"],
            "error_count": stats["error_count"],
            "active_tasks": stats["active_tasks"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve queue status")

@router.get("/models")
async def get_available_models():
    """Get information about available AI models"""
    from core.config import settings
    
    return {
        "primary_model": settings.openai_model_primary,
        "fallback_model": settings.openai_model_fallback,
        "simple_model": settings.openai_model_simple,
        "token_limits": {
            "gpt-4": 8192,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        },
        "current_settings": {
            "max_tokens": settings.openai_max_tokens,
            "temperature": settings.reasoning_temperature,
            "timeout": settings.openai_timeout
        }
    } 