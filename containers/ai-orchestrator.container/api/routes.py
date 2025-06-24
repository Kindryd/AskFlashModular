from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import logging

from core.database import get_db
from services.quality_analyzer import InformationQualityAnalyzer, DocumentationSource
from services.intent_ai import ConversationIntentAI

logger = logging.getLogger(__name__)

router = APIRouter()

# Global service instances
quality_analyzer = InformationQualityAnalyzer()

@router.get("/quality/status")
async def quality_status():
    """Get information quality analysis status"""
    return {
        "status": "operational",
        "service": "information_quality_analyzer",
        "capabilities": [
            "conflict_detection",
            "authority_scoring", 
            "freshness_scoring",
            "cross_reference_validation"
        ]
    }

@router.post("/quality/analyze")
async def analyze_quality(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze information quality for provided sources
    
    Expected request format:
    {
        "sources": [
            {
                "title": "Document Title",
                "content": "Document content...",
                "url": "https://source.url",
                "source_type": "azure_devops",
                "last_updated": "2025-01-01T00:00:00Z"
            }
        ],
        "query": "User query",
        "session_id": "optional-session-id"
    }
    """
    try:
        sources_data = request.get("sources", [])
        query = request.get("query", "")
        session_id = request.get("session_id")
        
        if not sources_data:
            raise HTTPException(status_code=400, detail="No sources provided")
        
        # Convert to DocumentationSource objects
        sources = []
        for source_data in sources_data:
            from datetime import datetime
            
            last_updated = None
            if source_data.get("last_updated"):
                try:
                    last_updated = datetime.fromisoformat(source_data["last_updated"].replace('Z', '+00:00'))
                except:
                    pass
            
            source = DocumentationSource(
                title=source_data.get("title", ""),
                content=source_data.get("content", ""),
                url=source_data.get("url", ""),
                source_type=source_data.get("source_type", "unknown"),
                last_updated=last_updated
            )
            sources.append(source)
        
        # Perform quality analysis
        result = await quality_analyzer.analyze_information_quality(
            sources=sources,
            query=query,
            session_id=session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Quality analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quality analysis failed: {str(e)}")

@router.get("/intent/status")
async def intent_status():
    """Get intent AI status"""
    return {
        "status": "operational",
        "service": "conversation_intent_ai",
        "model": "gpt-3.5-turbo",
        "capabilities": [
            "conversation_analysis",
            "context_summarization",
            "ai_guidance",
            "search_strategy"
        ]
    }

@router.post("/intent/analyze")
async def analyze_intent(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze conversation intent and provide AI guidance
    
    Expected request format:
    {
        "query": "Current user query",
        "conversation_id": "optional-conversation-id",
        "conversation_history": [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
    }
    """
    try:
        query = request.get("query", "")
        conversation_id = request.get("conversation_id")
        conversation_history = request.get("conversation_history", [])
        
        if not query:
            raise HTTPException(status_code=400, detail="No query provided")
        
        # Create intent AI service instance
        intent_ai = ConversationIntentAI(db)
        
        # Perform intent analysis
        result = await intent_ai.analyze_conversation_intent(
            current_query=query,
            conversation_id=conversation_id,
            conversation_history=conversation_history
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Intent analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Intent analysis failed: {str(e)}")

@router.post("/intent/search-strategy")
async def generate_search_strategy(
    request: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Generate search strategy based on intent analysis
    
    Expected request format:
    {
        "query": "User query",
        "intent_analysis": {...},
        "context_summary": {...}
    }
    """
    try:
        query = request.get("query", "")
        intent_analysis = request.get("intent_analysis", {})
        context_summary = request.get("context_summary", {})
        
        if not query:
            raise HTTPException(status_code=400, detail="No query provided")
        
        # Create intent AI service instance
        intent_ai = ConversationIntentAI(db)
        
        # Generate search strategy
        strategy = await intent_ai.generate_search_strategy(
            query=query,
            intent_analysis=intent_analysis,
            context_summary=context_summary
        )
        
        return strategy
        
    except Exception as e:
        logger.error(f"Search strategy generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search strategy generation failed: {str(e)}")

@router.get("/semantic/status")
async def semantic_status():
    """Legacy semantic enhancement status (ALTO deprecated)"""
    return {
        "status": "deprecated",
        "service": "semantic_enhancement",
        "note": "ALTO protocol was reverted for stability",
        "redirect": "Use /quality/analyze for information quality enhancement"
    }

@router.post("/provider/route")
async def route_ai_provider(
    request: Dict[str, Any]
):
    """
    Route AI requests to appropriate provider based on requirements
    
    Expected request format:
    {
        "query": "User query",
        "requirements": {
            "model_preference": "gpt-4|gpt-3.5-turbo",
            "max_tokens": 1000,
            "temperature": 0.7,
            "quality_threshold": 0.8
        },
        "context": {...}
    }
    """
    try:
        query = request.get("query", "")
        requirements = request.get("requirements", {})
        context = request.get("context", {})
        
        if not query:
            raise HTTPException(status_code=400, detail="No query provided")
        
        # Simple provider routing logic
        model_preference = requirements.get("model_preference", "gpt-4")
        
        # Route based on requirements
        if requirements.get("fast_response", False):
            selected_provider = {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "reasoning": "Fast response requested"
            }
        elif requirements.get("quality_threshold", 0.7) > 0.8:
            selected_provider = {
                "provider": "openai",
                "model": "gpt-4",
                "reasoning": "High quality threshold requested"
            }
        else:
            selected_provider = {
                "provider": "openai",
                "model": model_preference,
                "reasoning": "Default routing based on preference"
            }
        
        return {
            "selected_provider": selected_provider,
            "routing_decision": {
                "timestamp": str(__import__('datetime').datetime.utcnow()),
                "factors_considered": list(requirements.keys()),
                "fallback_available": True
            }
        }
        
    except Exception as e:
        logger.error(f"Provider routing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Provider routing failed: {str(e)}")

@router.get("/capabilities")
async def get_all_capabilities():
    """Get all AI orchestrator capabilities"""
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
            "search_strategy": True,
            "model": "gpt-3.5-turbo"
        },
        "provider_routing": {
            "openai_gpt4": True,
            "openai_gpt35": True,
            "fallback_strategies": True,
            "quality_based_routing": True
        },
        "legacy_support": {
            "alto_protocol": False,
            "semantic_enhancement": "deprecated"
        }
    } 