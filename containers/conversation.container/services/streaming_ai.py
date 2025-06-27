from typing import AsyncGenerator, Dict, List, Any, Optional
import asyncio
import json
import logging
from datetime import datetime
import httpx
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from .conversation_manager import ConversationManager
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class StreamingAIService:
    """
    Enhanced AI service with MCP ReAct integration.
    Forwards ReAct reasoning steps from MCP agents to frontend.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.conversation_manager = ConversationManager(db)
        self.mcp_url = settings.AI_ORCHESTRATOR_URL  # Now points to MCP
        self.redis_client = None

    async def initialize_redis(self):
        """Initialize Redis connection for ReAct event subscription"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✅ Redis connection established for ReAct streaming")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None

    async def process_query_with_reasoning(
        self,
        query: str,
        user_id: str,
        mode: str = "company",
        conversation_id: Optional[str] = None,
        ruleset_id: int = 1
    ) -> AsyncGenerator[str, None]:
        """
        Process query with MCP ReAct reasoning integration.
        Yields ReAct steps from MCP agents in real-time.
        """
        start_time = datetime.now()
        
        try:
            # Initialize Redis if needed
            if not self.redis_client:
                await self.initialize_redis()
            
            # Step 1: Initialize conversation
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

            # Step 2: Start MCP task and get task ID
            task_id = await self._start_mcp_task(query, user_id, mode, conversation_id)
            
            if not task_id:
                yield self._format_error("Failed to start AI reasoning task")
                return

            # Step 3: Poll for ReAct events and final response
            last_event_id = "0-0"  # Start from beginning of stream
            task_complete = False
            
            while not task_complete:
                # Check for new ReAct events
                try:
                    if self.redis_client:
                        stream_key = f"task:{task_id}:react_steps"
                        events = await self.redis_client.xread({stream_key: last_event_id}, block=500)
                        
                        for stream, messages in events:
                            for message_id, fields in messages:
                                # Yield ReAct event to frontend
                                react_event = {
                                    "type": "react",
                                    "step": fields.get("step", "thought"),
                                    "content": fields.get("message", ""),
                                    "agent": fields.get("agent", "Flash AI"),
                                    "timestamp": fields.get("timestamp", datetime.now().isoformat())
                                }
                                yield self._format_react_event(react_event)
                                last_event_id = message_id
                                
                except Exception as e:
                    logger.warning(f"Error polling ReAct events: {e}")
                
                # Check if task is complete
                try:
                    task_status = await self._check_task_status(task_id)
                    if task_status:
                        if task_status.get("status") == "complete":
                            final_response = task_status.get("response")
                            task_complete = True
                            
                            if final_response:
                                # Calculate response time
                                response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                                
                                # Save assistant response
                                await self.conversation_manager.save_message(
                                    conversation_id=conversation_id,
                                    role="assistant",
                                    content=final_response.get("content", ""),
                                    mode=mode,
                                    sources=final_response.get("sources", []),
                                    confidence=final_response.get("confidence", 0.8),
                                    response_time_ms=response_time_ms
                                )

                                # Yield final response
                                yield self._format_final_response({
                                    "response": final_response.get("content", ""),
                                    "mode": mode,
                                    "sources": final_response.get("sources", []),
                                    "confidence": final_response.get("confidence", 0.8),
                                    "conversation_id": conversation_id,
                                    "timestamp": datetime.now().isoformat()
                                })
                            else:
                                yield self._format_error("Failed to get response from AI reasoning system")
                                
                        elif task_status.get("status") == "failed":
                            yield self._format_error(f"AI reasoning failed: {task_status.get('error', 'Unknown error')}")
                            task_complete = True
                            
                except Exception as e:
                    logger.error(f"Error checking task status: {e}")
                
                # Small delay to prevent busy polling
                if not task_complete:
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Streaming AI error: {str(e)}")
            yield self._format_error(f"Error processing request: {str(e)}")

    async def _start_mcp_task(self, query: str, user_id: str, mode: str, conversation_id: str) -> Optional[str]:
        """Start MCP task and return task ID"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mcp_url}/api/v1/tasks/create",
                    json={
                        "query": query,
                        "user_id": user_id,
                        "mode": mode,
                        "conversation_id": conversation_id,
                        "template": "standard_query"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("task_id")
                else:
                    logger.error(f"MCP task creation failed: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error starting MCP task: {e}")
        
        return None

    async def _check_task_status(self, task_id: str) -> Optional[Dict]:
        """Check MCP task status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.mcp_url}/api/v1/tasks/{task_id}/status",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return response.json()
                    
        except Exception as e:
            logger.error(f"Error checking task status: {e}")
        
        return None

    def _format_react_event(self, event_data: Dict) -> str:
        """Format ReAct event for frontend"""
        return json.dumps({
            "type": event_data.get("type", "react"),
            "step": event_data.get("step", "thought"),
            "content": event_data.get("content", ""),
            "agent": event_data.get("agent", "Flash AI"),
            "timestamp": event_data.get("timestamp", datetime.now().isoformat())
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