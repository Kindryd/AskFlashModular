from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional, List
import logging

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["moderator"])

# Global reference to services (will be set from main.py)
content_moderator = None
rabbitmq_consumer = None

def set_services(moderator, consumer):
    """Set service references from main application"""
    global content_moderator, rabbitmq_consumer
    content_moderator = moderator
    rabbitmq_consumer = consumer

@router.post("/moderate")
async def moderate_content(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Perform content moderation (direct API call, not via queue)"""
    try:
        if not content_moderator:
            raise HTTPException(status_code=503, detail="Content moderator not available")
        
        content = request.get("content", "").strip()
        if not content:
            raise HTTPException(status_code=400, detail="Content parameter is required")
        
        content_type = request.get("content_type", "text")
        context = request.get("context", {})
        
        logger.info(f"🛡️ Direct moderation request for {content_type} content ({len(content)} chars)")
        
        result = await content_moderator.moderate_content(content, content_type, context)
        
        return {
            "status": "success",
            "result": result,
            "direct_call": True
        }
        
    except Exception as e:
        logger.error(f"❌ Moderation API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-ai-response")
async def validate_ai_response(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Validate AI-generated response"""
    try:
        if not content_moderator:
            raise HTTPException(status_code=503, detail="Content moderator not available")
        
        response = request.get("response", "").strip()
        if not response:
            raise HTTPException(status_code=400, detail="Response parameter is required")
        
        query = request.get("query", "")
        sources = request.get("sources", [])
        
        logger.info(f"🛡️ AI response validation request ({len(response)} chars)")
        
        result = await content_moderator.validate_ai_response(response, query, sources)
        
        return {
            "status": "success",
            "result": result,
            "validation_type": "ai_response"
        }
        
    except Exception as e:
        logger.error(f"❌ AI response validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-moderate")
async def batch_moderate_content(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Moderate multiple content items in batch"""
    try:
        if not content_moderator:
            raise HTTPException(status_code=503, detail="Content moderator not available")
        
        content_items = request.get("content_items", [])
        if not content_items:
            raise HTTPException(status_code=400, detail="content_items parameter is required")
        
        if len(content_items) > 50:  # Reasonable batch limit
            raise HTTPException(status_code=400, detail="Batch size too large (max 50 items)")
        
        logger.info(f"🛡️ Batch moderation request for {len(content_items)} items")
        
        results = []
        for i, item in enumerate(content_items):
            content = item.get("content", "")
            content_type = item.get("content_type", "text")
            context = item.get("context", {})
            
            try:
                result = await content_moderator.moderate_content(content, content_type, context)
                result["batch_index"] = i
                results.append(result)
            except Exception as e:
                error_result = {
                    "batch_index": i,
                    "approved": False,
                    "error": str(e),
                    "reason": f"Moderation failed: {str(e)}",
                    "confidence": 0.0
                }
                results.append(error_result)
        
        # Summary statistics
        approved_count = sum(1 for r in results if r.get("approved", False))
        
        return {
            "status": "success",
            "results": results,
            "summary": {
                "total_items": len(content_items),
                "approved_count": approved_count,
                "blocked_count": len(content_items) - approved_count,
                "approval_rate": approved_count / len(content_items) if content_items else 0
            },
            "batch_processing": True
        }
        
    except Exception as e:
        logger.error(f"❌ Batch moderation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/check-text")
async def quick_text_check(
    text: str,
    check_type: str = "basic"
) -> Dict[str, Any]:
    """Quick text safety check"""
    try:
        if not content_moderator:
            raise HTTPException(status_code=503, detail="Content moderator not available")
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text parameter is required")
        
        logger.info(f"🛡️ Quick text check: {check_type}")
        
        if check_type == "basic":
            # Just profanity and basic safety
            result = await content_moderator.moderate_content(text, "text", {"quick_check": True})
        else:
            # Full moderation
            result = await content_moderator.moderate_content(text, "text")
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "approved": result.get("approved", False),
            "confidence": result.get("confidence", 0.0),
            "flags": result.get("flags", []),
            "quick_check": check_type == "basic"
        }
        
    except Exception as e:
        logger.error(f"❌ Quick check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_moderation_stats() -> Dict[str, Any]:
    """Get moderation service statistics"""
    try:
        if not content_moderator:
            raise HTTPException(status_code=503, detail="Content moderator not available")
        
        stats = await content_moderator.get_stats()
        
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

@router.get("/config")
async def get_moderation_config() -> Dict[str, Any]:
    """Get current moderation configuration"""
    try:
        return {
            "service": "Moderator Agent",
            "version": settings.SERVICE_VERSION,
            "thresholds": {
                "toxicity": settings.TOXICITY_THRESHOLD,
                "spam": settings.SPAM_THRESHOLD,
                "quality": settings.QUALITY_THRESHOLD,
                "confidence": settings.CONFIDENCE_THRESHOLD
            },
            "enabled_checks": {
                "toxicity": settings.ENABLE_TOXICITY_CHECK,
                "profanity": settings.ENABLE_PROFANITY_FILTER,
                "hate_speech": settings.ENABLE_HATE_SPEECH_CHECK,
                "spam": settings.ENABLE_SPAM_DETECTION,
                "quality": settings.ENABLE_QUALITY_ASSESSMENT
            },
            "policies": {
                "enforce_enterprise_policy": settings.ENFORCE_ENTERPRISE_POLICY,
                "allow_external_links": settings.ALLOW_EXTERNAL_LINKS,
                "require_source_attribution": settings.REQUIRE_SOURCE_ATTRIBUTION
            },
            "limits": {
                "max_content_length": settings.MAX_CONTENT_LENGTH,
                "min_content_length": settings.MIN_CONTENT_LENGTH,
                "max_concurrent_checks": settings.MAX_CONCURRENT_CHECKS
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Config API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_moderation(request: Dict[str, Any]) -> Dict[str, Any]:
    """Test endpoint for moderation functionality"""
    try:
        test_content = request.get("content", "This is a test message for content moderation.")
        
        return {
            "status": "test_mode",
            "content": test_content,
            "message": "Moderator agent is operational",
            "capabilities": [
                "toxicity_detection",
                "profanity_filtering",
                "spam_detection",
                "quality_assessment",
                "policy_compliance"
            ],
            "config": {
                "toxicity_threshold": settings.TOXICITY_THRESHOLD,
                "spam_threshold": settings.SPAM_THRESHOLD,
                "quality_threshold": settings.QUALITY_THRESHOLD
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Test API error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 