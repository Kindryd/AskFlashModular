"""
API Routes for Intent Agent

This module provides REST endpoints for the Intent Agent container.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

class AnalyzeRequest(BaseModel):
    """Request model for manual intent analysis"""
    query: str
    user_id: str = "test_user"

@router.get("/stats")
async def get_stats():
    """Get agent processing statistics"""
    try:
        from main import consumer
        
        if consumer:
            stats = await consumer.get_stats()
            return {
                "agent": "intent_analyzer",
                "stats": stats,
                "status": "operational" if stats["is_consuming"] else "stopped"
            }
        else:
            return {
                "agent": "intent_analyzer", 
                "stats": {},
                "status": "not_initialized"
            }
            
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@router.post("/analyze")
async def manual_analyze(request: AnalyzeRequest):
    """Manually trigger intent analysis (for testing)"""
    try:
        from main import intent_analyzer
        
        if not intent_analyzer:
            raise HTTPException(status_code=503, detail="Intent analyzer not initialized")
        
        # Generate test task ID
        import uuid
        task_id = f"test_{uuid.uuid4()}"
        
        # Perform analysis
        result = await intent_analyzer.analyze_intent(
            task_id=task_id,
            query=request.query,
            user_id=request.user_id
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "analysis": result
        }
        
    except Exception as e:
        logger.error(f"Manual analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/queue/status")
async def get_queue_status():
    """Get RabbitMQ queue status"""
    try:
        from main import consumer
        
        if not consumer:
            return {"status": "consumer_not_initialized"}
        
        stats = await consumer.get_stats()
        
        return {
            "queue_name": "intent.task",
            "connection_status": stats["connection_status"],
            "is_consuming": stats["is_consuming"],
            "processed_count": stats["processed_count"],
            "error_count": stats["error_count"],
            "active_tasks": stats["active_tasks"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve queue status") 