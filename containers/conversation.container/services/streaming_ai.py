from typing import AsyncGenerator, Dict, List, Any, Optional
import asyncio
import json
import logging
from datetime import datetime
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from .conversation_manager import ConversationManager
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class StreamingAIService:
    """
    Enhanced AI service with step-by-step reasoning capabilities.
    Extracted from legacy streaming_ai.py with Flash AI enhancements.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_manager = ConversationManager(db)
        self.ai_orchestrator_url = settings.AI_ORCHESTRATOR_URL
        self.embedding_service_url = settings.EMBEDDING_SERVICE_URL

    async def process_query_with_reasoning(
        self,
        query: str,
        user_id: str,
        mode: str = "company",
        conversation_id: Optional[str] = None,
        ruleset_id: int = 1
    ) -> AsyncGenerator[str, None]:
        """
        Process query with transparent step-by-step reasoning.
        Yields intermediate thoughts and progress updates.
        Compatible with legacy Chat.js streaming parser.
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Initialize conversation
            yield self._format_step("🔍 Initializing conversation...")
            
            conversation = await self.conversation_manager.get_or_create_active_conversation(
                user_id, mode, conversation_id
            )
            conversation_id = conversation.conversation_id
            
            # Save user message immediately
            await self.conversation_manager.save_message(
                conversation_id=conversation_id,
                role="user",
                content=query,
                mode=mode
            )

            # Step 2: Context gathering
            yield self._format_step("📚 Gathering conversation context...")
            history = await self.conversation_manager.get_conversation_messages(
                conversation_id, limit=5
            )
            
            if history:
                yield self._format_step(f"✅ Found {len(history)} previous messages")

            # Step 3: Information Quality Enhancement
            yield self._format_step("🎯 Analyzing information quality...")
            
            quality_analysis = await self._get_quality_analysis(query, mode)
            if quality_analysis:
                yield self._format_step("✅ Quality analysis complete")

            # Step 4: Knowledge retrieval (Company mode)
            sources = []
            confidence = 0.8
            
            if mode == "company":
                yield self._format_step("🔎 Searching Flash documentation...")
                
                try:
                    # Enhanced semantic search with alias discovery
                    search_results = await self._enhanced_documentation_search(query)
                    if search_results:
                        sources = search_results.get("sources", [])
                        confidence = search_results.get("confidence", 0.8)
                        yield self._format_step(f"📋 Found {len(sources)} relevant documents")
                        
                        # Show top sources
                        for i, source in enumerate(sources[:3], 1):
                            title = source.get("title", "Document")
                            yield self._format_step(f"  {i}. {title}")
                    else:
                        yield self._format_step("ℹ️ No specific documentation found, using general knowledge")
                except Exception as e:
                    logger.error(f"Documentation search error: {str(e)}")
                    yield self._format_step("⚠️ Documentation search unavailable, using general knowledge")

            # Step 5: Intent analysis
            yield self._format_step("🧠 Analyzing conversation intent...")
            
            intent_analysis = await self._get_intent_analysis(query, mode, history)
            if intent_analysis:
                yield self._format_step("✅ Intent analysis complete")

            # Step 6: Response generation
            yield self._format_step("💭 Generating comprehensive response...")
            
            # Build context for AI generation
            context = {
                "query": query,
                "mode": mode,
                "conversation_history": [
                    {"role": msg.role, "content": msg.content}
                    for msg in history[-3:]  # Last 3 messages for context
                ],
                "sources": sources,
                "quality_analysis": quality_analysis,
                "intent_analysis": intent_analysis
            }

            # Generate response via AI Orchestrator
            response = await self._generate_ai_response(context)
            
            # Step 7: Final quality assessment
            yield self._format_step("🎯 Assessing response quality...")
            final_confidence = await self._assess_response_quality(query, response, sources)
            
            # Step 8: Save and return
            yield self._format_step("✨ Response ready!")
            
            # Calculate response time
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Save assistant response
            await self.conversation_manager.save_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response,
                mode=mode,
                sources=sources,
                confidence=final_confidence,
                response_time_ms=response_time_ms
            )

            # Yield final response
            yield self._format_final_response({
                "response": response,
                "mode": mode,
                "sources": sources,
                "confidence": final_confidence,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Streaming AI error: {str(e)}")
            yield self._format_error(f"Error processing request: {str(e)}")

    async def _get_quality_analysis(self, query: str, mode: str) -> Optional[Dict]:
        """Get information quality analysis from AI Orchestrator"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_orchestrator_url}/quality/analyze",
                    json={"query": query, "mode": mode},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Quality analysis error: {str(e)}")
        return None

    async def _get_intent_analysis(self, query: str, mode: str, history: List) -> Optional[Dict]:
        """Get intent analysis from AI Orchestrator"""
        try:
            context = [{"role": msg.role, "content": msg.content} for msg in history[-3:]]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_orchestrator_url}/intent/analyze",
                    json={"query": query, "mode": mode, "context": context},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Intent analysis error: {str(e)}")
        return None

    async def _enhanced_documentation_search(self, query: str) -> Optional[Dict]:
        """Enhanced documentation search with semantic alias discovery"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.embedding_service_url}/search",
                    json={"query": query, "enhanced": True, "limit": 5},
                    timeout=15.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Enhanced search error: {str(e)}")
        return None

    async def _generate_ai_response(self, context: Dict) -> str:
        """Generate AI response via AI Orchestrator"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_orchestrator_url}/generate",
                    json=context,
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "I'm sorry, I couldn't generate a response.")
                
        except Exception as e:
            logger.error(f"AI generation error: {str(e)}")
        
        # Fallback response
        if context["mode"] == "company":
            return "I'm sorry, I'm having trouble accessing the Flash documentation right now. Please try again later."
        else:
            return "I'm sorry, I'm experiencing technical difficulties. Please try again later."

    async def _assess_response_quality(self, query: str, response: str, sources: List) -> float:
        """Assess response quality and adjust confidence"""
        try:
            # Basic quality assessment
            base_confidence = 0.7
            
            # Boost confidence if we have sources
            if sources:
                base_confidence = min(0.95, base_confidence + (len(sources) * 0.05))
            
            # Boost confidence for longer, detailed responses
            if len(response) > 200:
                base_confidence = min(0.95, base_confidence + 0.05)
            
            # Reduce confidence for very short responses
            if len(response) < 50:
                base_confidence = max(0.3, base_confidence - 0.2)
            
            # Reduce confidence for "I don't know" type responses
            if any(phrase in response.lower() for phrase in ["i don't know", "i'm not sure", "unable to", "can't help"]):
                base_confidence = max(0.3, base_confidence - 0.3)
            
            return round(base_confidence, 2)
            
        except Exception as e:
            logger.error(f"Quality assessment error: {str(e)}")
            return 0.6

    def _format_step(self, message: str) -> str:
        """Format intermediate reasoning step for frontend"""
        return json.dumps({
            "type": "thinking",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }) + "\n"

    def _format_final_response(self, data: Dict) -> str:
        """Format final response data for frontend"""
        return json.dumps({
            "type": "response",
            "data": data
        }) + "\n"

    def _format_error(self, message: str) -> str:
        """Format error message for frontend"""
        return json.dumps({
            "type": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }) + "\n"

    async def process_regular_chat(
        self,
        query: str,
        user_id: str,
        mode: str = "company",
        conversation_id: Optional[str] = None,
        ruleset_id: int = 1
    ) -> Dict[str, Any]:
        """
        Process regular (non-streaming) chat request.
        Legacy compatibility for non-streaming endpoints.
        """
        try:
            conversation = await self.conversation_manager.get_or_create_active_conversation(
                user_id, mode, conversation_id
            )
            
            # Save user message
            await self.conversation_manager.save_message(
                conversation_id=conversation.conversation_id,
                role="user",
                content=query,
                mode=mode
            )

            # Get context and generate response
            context = {
                "query": query,
                "mode": mode,
                "conversation_history": []
            }

            if mode == "company":
                search_results = await self._enhanced_documentation_search(query)
                if search_results:
                    context["sources"] = search_results.get("sources", [])

            response = await self._generate_ai_response(context)
            confidence = await self._assess_response_quality(query, response, context.get("sources", []))

            # Save assistant response
            await self.conversation_manager.save_message(
                conversation_id=conversation.conversation_id,
                role="assistant",
                content=response,
                mode=mode,
                sources=context.get("sources", []),
                confidence=confidence
            )

            return {
                "response": response,
                "conversation_id": conversation.conversation_id,
                "mode": mode,
                "sources": context.get("sources", []),
                "confidence": confidence,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Regular chat error: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error processing your request.",
                "conversation_id": conversation_id,
                "mode": mode,
                "sources": [],
                "confidence": 0.1,
                "error": str(e)
            } 