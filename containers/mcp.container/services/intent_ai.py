from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)

class ConversationIntentAI:
    """
    Lightweight AI service for conversation analysis, intent detection, and context summarization.
    This is the 'meta-cognitive' layer that guides the main AI service.
    Uses GPT-3.5-turbo for fast and cost-effective analysis.
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_INTENT_MODEL
        self.timeout = settings.INTENT_ANALYSIS_TIMEOUT
    
    async def analyze_conversation_intent(
        self, 
        current_query: str, 
        conversation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Analyze current query in context of conversation to determine intent and guidance."""
        
        try:
            if not settings.INTENT_AI_ENABLED:
                return self._get_disabled_response()
            
            if not self.client:
                logger.warning("OpenAI client not configured, falling back to defaults")
                return self._get_fallback_response(current_query)
            
            if conversation_history is None:
                conversation_history = []
            
            # Simple intent analysis for now
            analysis = {
                "intent_type": "question",
                "conversation_type": "informational",
                "needs_documentation_search": True,
                "confidence": 0.8,
                "key_topics": [current_query],
                "model_used": self.model
            }
            
            context_summary = {
                "summary": "New conversation" if not conversation_history else "Ongoing conversation",
                "key_facts": [],
                "relevant_to_current_query": True
            }
            
            ai_guidance = {
                "approach": "standard",
                "focus_areas": ["accuracy"],
                "response_style": "professional"
            }
            
            return {
                "intent_analysis": analysis,
                "context_summary": context_summary,
                "ai_guidance": ai_guidance,
                "conversation_length": len(conversation_history) // 2,
                "requires_fresh_search": True,
                "conversation_type": "informational",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "intent_ai"
            }
            
        except Exception as e:
            logger.error(f"Error in conversation intent analysis: {str(e)}", exc_info=True)
            return self._get_error_response(str(e))
    
    def _get_disabled_response(self) -> Dict[str, Any]:
        """Return response when intent AI is disabled"""
        return {
            "intent_analysis": {"confidence": 0.7, "needs_documentation_search": True, "enabled": False},
            "context_summary": {"summary": "Intent AI disabled", "key_facts": []},
            "ai_guidance": {"approach": "standard", "focus_areas": []},
            "conversation_length": 0,
            "requires_fresh_search": True,
            "conversation_type": "informational",
            "service": "intent_ai"
        }
    
    def _get_fallback_response(self, current_query: str) -> Dict[str, Any]:
        """Return fallback response when OpenAI is not available"""
        return {
            "intent_analysis": {"confidence": 0.6, "needs_documentation_search": True, "fallback": True},
            "context_summary": {"summary": "No OpenAI available", "key_facts": []},
            "ai_guidance": {"approach": "standard", "focus_areas": []},
            "conversation_length": 0,
            "requires_fresh_search": True,
            "conversation_type": "informational",
            "service": "intent_ai"
        }
    
    def _get_error_response(self, error: str) -> Dict[str, Any]:
        """Return error response"""
        return {
            "intent_analysis": {"confidence": 0.5, "needs_documentation_search": True, "error": error},
            "context_summary": {"summary": "Analysis failed", "key_facts": []},
            "ai_guidance": {"approach": "standard", "focus_areas": []},
            "conversation_length": 0,
            "requires_fresh_search": True,
            "conversation_type": "informational",
            "service": "intent_ai"
        }
    
    async def generate_search_strategy(
        self,
        query: str,
        intent_analysis: Dict[str, Any],
        context_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate search strategy based on intent and context"""
        
        strategy = {
            "search_type": "standard",
            "priority_sources": ["azure_devops"],
            "search_terms": [query],
            "max_results": 5,
            "quality_threshold": 0.6
        }
        
        # Adjust strategy based on intent
        conversation_type = intent_analysis.get("conversation_type", "informational")
        
        if conversation_type == "team_inquiry":
            strategy["search_type"] = "team_focused"
            strategy["priority_sources"] = ["azure_devops", "confluence"]
            strategy["max_results"] = 8
        elif conversation_type == "technical":
            strategy["search_type"] = "technical_detailed"
            strategy["priority_sources"] = ["azure_devops", "github"]
            strategy["quality_threshold"] = 0.7
        
        return strategy
