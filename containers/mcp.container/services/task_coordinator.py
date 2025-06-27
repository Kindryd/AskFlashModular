"""
Task Coordinator for AskFlash MCP Architecture

This service implements the core DAG execution engine for the Master Control Program (MCP).
It coordinates multi-agent AI workflows through Redis and RabbitMQ.
"""

import asyncio
import json
import logging
import uuid
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from shared.redis_manager import AsyncRedisTaskManager
from services.message_broker import MessageBroker
from services.state_manager import StateManager
from core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class DAGTemplate:
    """Represents a task DAG template"""
    name: str
    description: str
    stages: List[str]
    conditions: Dict[str, Any]
    estimated_duration_ms: int = 15000

class TaskCoordinator:
    """
    Core DAG execution engine for MCP
    
    Responsibilities:
    - Create and manage task DAGs
    - Coordinate stage execution across agents
    - Handle failures and retries
    - Emit real-time progress events
    """
    
    def __init__(self):
        self.redis_manager = AsyncRedisTaskManager()
        self.message_broker = MessageBroker()
        self.state_manager = StateManager()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # DAG stage routing map
        self.stage_routes = {
            "intent_analysis": "intent.task",
            "embedding_lookup": "embedding.task", 
            "executor_reasoning": "executor.task",
            "moderation": "moderator.task",
            "web_search": "websearch.task",
            "response_packaging": self._handle_response_packaging
        }
        
        # Default DAG templates
        self.default_templates = {
            "standard_query": DAGTemplate(
                name="standard_query",
                description="Standard question answering flow for most queries",
                stages=["intent_analysis", "embedding_lookup", "executor_reasoning", "moderation", "response_packaging"],
                conditions={"complexity": "medium", "requires_web_search": False},
                estimated_duration_ms=15000
            ),
            "simple_lookup": DAGTemplate(
                name="simple_lookup", 
                description="Simple document lookup without complex reasoning",
                stages=["embedding_lookup", "response_packaging"],
                conditions={"complexity": "low", "direct_answer": True},
                estimated_duration_ms=5000
            ),
            "complex_research": DAGTemplate(
                name="complex_research",
                description="Complex multi-step research with web augmentation", 
                stages=["intent_analysis", "embedding_lookup", "web_search", "executor_reasoning", "moderation", "response_packaging"],
                conditions={"complexity": "high", "requires_web_search": True},
                estimated_duration_ms=30000
            ),
            "web_enhanced": DAGTemplate(
                name="web_enhanced",
                description="Web search enhanced response for current information",
                stages=["intent_analysis", "web_search", "embedding_lookup", "executor_reasoning", "moderation", "response_packaging"],
                conditions={"complexity": "medium", "requires_web_search": True},
                estimated_duration_ms=20000
            ),
            "quick_answer": DAGTemplate(
                name="quick_answer",
                description="Ultra-fast response for simple factual queries",
                stages=["embedding_lookup", "executor_reasoning", "response_packaging"],
                conditions={"complexity": "very_low", "direct_answer": True},
                estimated_duration_ms=3000
            )
        }
        
    async def initialize(self):
        """Initialize task coordinator with Redis and message broker"""
        try:
            # Initialize Redis task manager
            self.redis_manager = AsyncRedisTaskManager(
                redis_url=settings.REDIS_URL,
                password="askflash123"
            )
            await self.redis_manager.initialize()
            
            # Initialize message broker
            self.message_broker = MessageBroker(
                rabbitmq_url=settings.RABBITMQ_URL,
                redis_client=self.redis_manager.redis
            )
            await self.message_broker.connect()
            
            # Set up ReAct event forwarding for real-time frontend updates
            await self._setup_react_forwarding()
            
            logger.info("🎯 Task Coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Task Coordinator: {e}")
            raise
    
    async def _setup_react_forwarding(self):
        """Set up Redis pub/sub to forward ReAct events to frontend"""
        try:
            # Subscribe to all agent ReAct channels
            pubsub = self.redis_manager.redis.pubsub()
            await pubsub.psubscribe("ai:react:*")
            
            # Start background task to forward ReAct events
            asyncio.create_task(self._forward_react_events(pubsub))
            
            logger.info("🔄 ReAct event forwarding initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to set up ReAct forwarding: {e}")
    
    async def _forward_react_events(self, pubsub):
        """Forward ReAct events from agents to frontend streaming"""
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    try:
                        # Parse ReAct event
                        react_data = json.loads(message['data'])
                        task_id = react_data.get("task_id")
                        
                        if task_id:
                            # Forward to frontend streaming channel
                            frontend_event = {
                                "type": "react",
                                "step": react_data.get("step", "thought"),
                                "content": react_data.get("message", ""),
                                "agent": react_data.get("agent", "unknown"),
                                "timestamp": react_data.get("timestamp")
                            }
                            
                            # Publish to frontend channel
                            await self.redis_manager.redis.publish(
                                f"frontend:stream:{task_id}",
                                json.dumps(frontend_event)
                            )
                            
                            # Also store in task progress stream for history
                            stream_key = f"task:{task_id}:react_steps"
                            await self.redis_manager.redis.xadd(
                                stream_key,
                                {
                                    "step": react_data.get("step", "thought"),
                                    "message": react_data.get("message", ""),
                                    "agent": react_data.get("agent", "unknown"),
                                    "timestamp": react_data.get("timestamp", "")
                                }
                            )
                            
                    except Exception as e:
                        logger.warning(f"Failed to forward ReAct event: {e}")
                        
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
        except Exception as e:
            logger.error(f"❌ ReAct event forwarding error: {e}")
            # Restart forwarding after error
            await asyncio.sleep(5)
            await self._setup_react_forwarding()
    
    async def create_and_execute_task(
        self, 
        user_id: str, 
        query: str, 
        template: str = "standard_query",
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Create new task and begin execution
        
        Args:
            user_id: User identifier
            query: User query to process
            template: DAG template to use
            conversation_id: Optional conversation context
            
        Returns:
            Task ID for tracking
        """
        try:
            # Get DAG template
            dag_template = await self._get_dag_template(template)
            if not dag_template:
                raise ValueError(f"Unknown DAG template: {template}")
            
            # **ADAPTIVE INTEGRATION**: Get persona-driven optimization recommendations
            adaptive_recommendations = await self._get_adaptive_recommendations(
                user_id=user_id,
                query=query,
                conversation_history=[]  # TODO: Get from conversation service
            )
            
            # Create task in Redis
            task_id = await self.redis_manager.create_task(
                user_id=user_id,
                query=query,
                plan=dag_template.stages,
                template=template
            )
            
            # Store adaptive recommendations in task context
            await self.redis_manager.redis.setex(
                f"task:{task_id}:adaptive_recommendations",
                600,  # 10 minute TTL
                json.dumps(adaptive_recommendations)
            )
            
            # Store additional context
            context_data = {
                "conversation_id": conversation_id,
                "template_info": asdict(dag_template),
                "created_by": "mcp_coordinator"
            }
            
            await self.redis_manager.redis.setex(
                f"task:{task_id}:context",
                600,  # 10 minute TTL
                json.dumps(context_data)
            )
            
            # Start execution in background
            execution_task = asyncio.create_task(self._execute_dag(task_id))
            self.active_tasks[task_id] = execution_task
            
            # Emit initial progress
            await self.redis_manager.emit_progress_event(
                task_id=task_id,
                stage="created",
                message=f"Task created with {len(dag_template.stages)} stages",
                metadata={
                    "template": template,
                    "estimated_duration_ms": dag_template.estimated_duration_ms,
                    "stage_count": len(dag_template.stages)
                }
            )
            
            logger.info(f"🚀 Created and started task {task_id} for user {user_id} using template '{template}'")
            return task_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create task: {e}")
            raise
    
    async def _execute_dag(self, task_id: str):
        """
        Execute task DAG stages sequentially
        
        Args:
            task_id: Task identifier
        """
        try:
            task_data = await self.redis_manager.get_task(task_id)
            if not task_data:
                logger.error(f"Task {task_id} not found")
                return
            
            logger.info(f"🔄 Starting DAG execution for task {task_id}")
            
            while task_data["current_stage"] and task_data["status"] == "in_progress":
                stage = task_data["current_stage"]
                
                logger.info(f"▶️  Executing stage '{stage}' for task {task_id}")
                
                # Emit stage start event
                await self.redis_manager.emit_progress_event(
                    task_id=task_id,
                    stage=stage,
                    message=f"Starting {stage}",
                    metadata={"action": "stage_start"}
                )
                
                # Execute current stage
                success = await self._execute_stage(task_id, stage, task_data)
                
                if not success:
                    await self._handle_stage_failure(task_id, stage)
                    break
                
                # Move to next stage
                await self._advance_to_next_stage(task_id)
                task_data = await self.redis_manager.get_task(task_id)
            
            # Complete task if successful
            if task_data and task_data["status"] == "in_progress":
                await self._complete_task(task_id)
                
        except Exception as e:
            logger.error(f"❌ Error executing DAG for task {task_id}: {e}")
            await self._handle_task_error(task_id, str(e))
        finally:
            # Cleanup
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _execute_stage(self, task_id: str, stage: str, task_data: Dict) -> bool:
        """
        Execute a single DAG stage
        
        Args:
            task_id: Task identifier
            stage: Stage name to execute
            task_data: Current task data
            
        Returns:
            True if stage executed successfully
        """
        try:
            if stage == "response_packaging":
                return await self._handle_response_packaging(task_id, task_data)
            
            # Get queue for stage
            queue_name = self.stage_routes.get(stage)
            if not queue_name:
                logger.error(f"Unknown stage {stage} for task {task_id}")
                return False
            
            # **ADAPTIVE INTEGRATION**: Retrieve adaptive recommendations
            adaptive_recommendations = {}
            try:
                recommendations_data = await self.redis_manager.redis.get(f"task:{task_id}:adaptive_recommendations")
                if recommendations_data:
                    adaptive_recommendations = json.loads(recommendations_data)
                    logger.info(f"🧠 Using adaptive recommendations for {stage}: confidence {adaptive_recommendations.get('confidence', 0):.2f}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load adaptive recommendations: {e}")
            
            # Prepare task payload with adaptive optimization
            payload = {
                "task_id": task_id,
                "query": task_data["query"],
                "user_id": task_data["user_id"],
                "stage": stage,
                "context": task_data.get("context", ""),
                "vector_hits": task_data.get("vector_hits", []),
                "template": task_data.get("template", "standard_query"),
                "conversation_id": task_data.get("conversation_id"),
                "timestamp": datetime.utcnow().isoformat(),
                
                # **ADAPTIVE INTEGRATION**: Pass optimization hints to agents
                "adaptive_recommendations": adaptive_recommendations,
                "user_persona": adaptive_recommendations.get("personalization", {}),
                "response_style": adaptive_recommendations.get("response_style", {}),
                "context_optimization": adaptive_recommendations.get("context_optimization", {}),
                "conversation_flow": adaptive_recommendations.get("conversation_flow", {})
            }
            
            # Publish to RabbitMQ
            await self.message_broker.publish_task(queue_name, payload)
            
            logger.info(f"📤 Published task {task_id} stage '{stage}' to queue '{queue_name}'")
            
            # Wait for completion (with timeout)
            success = await self._wait_for_stage_completion(task_id, stage, timeout=300)
            
            if success:
                # Integrate stage results into task data
                await self._integrate_stage_results(task_id, stage)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error executing stage {stage} for task {task_id}: {e}")
            return False
    
    async def _wait_for_stage_completion(self, task_id: str, stage: str, timeout: int = 300) -> bool:
        """
        Wait for stage completion event
        
        Args:
            task_id: Task identifier
            stage: Stage name
            timeout: Timeout in seconds
            
        Returns:
            True if stage completed successfully
        """
        # Map stage names to actual completion channels used by agents
        completion_channels = {
            "intent_analysis": "ai:intent:complete",
            "embedding_lookup": "ai:embedding:complete", 
            "executor_reasoning": "ai:execution:complete",
            "moderation": "ai:moderation:complete",
            "web_search": "ai:websearch:complete"
        }
        
        completion_event = completion_channels.get(stage)
        if not completion_event:
            logger.error(f"Unknown completion channel for stage: {stage}")
            return False
        
        try:
            # Wait for Redis pub/sub event
            result = await asyncio.wait_for(
                self.message_broker.wait_for_event(completion_event, task_id),
                timeout=timeout
            )
            
            success = result.get("success", True)  # Default to success if not specified
            if success:
                logger.info(f"✅ Stage '{stage}' completed for task {task_id}")
            else:
                logger.warning(f"⚠️  Stage '{stage}' failed for task {task_id}")
            
            return success
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Stage '{stage}' timed out for task {task_id}")
            return False
    
    async def _integrate_stage_results(self, task_id: str, stage: str):
        """Integrate stage results into main task data"""
        try:
            # Map stages to their result keys
            result_keys = {
                "intent_analysis": f"intent_result:{task_id}",
                "embedding_lookup": f"embedding_result:{task_id}",
                "executor_reasoning": f"executor_result:{task_id}",
                "moderation": f"moderation_result:{task_id}",
                "web_search": f"websearch_result:{task_id}"
            }
            
            result_key = result_keys.get(stage)
            if not result_key:
                logger.warning(f"No result integration defined for stage: {stage}")
                return
            
            # Get stage result
            result_data = await self.redis_manager.redis.get(result_key)
            if not result_data:
                logger.warning(f"No result found for stage {stage} task {task_id}")
                return
            
            result = json.loads(result_data)
            
            # Get current task data
            task_data = await self.redis_manager.get_task(task_id)
            if not task_data:
                logger.error(f"Task {task_id} not found during result integration")
                return
            
            # Integrate based on stage type
            if stage == "intent_analysis":
                task_data["intent_analysis"] = result.get("intent_classification", {})
                task_data["processing_strategy"] = result.get("processing_strategy", {})
                
            elif stage == "embedding_lookup":
                task_data["vector_hits"] = result.get("documents", [])
                task_data["context"] = result.get("context", "")
                
            elif stage == "executor_reasoning":
                task_data["ai_response"] = result.get("response", {})
                task_data["reasoning_metadata"] = result.get("reasoning_metadata", {})
                
            elif stage == "moderation":
                task_data["moderation_result"] = result.get("moderation_result", {})
                task_data["safety_score"] = result.get("safety_score", 1.0)
                
            elif stage == "web_search":
                # Merge web search results with existing vector hits
                web_docs = result.get("documents", [])
                existing_docs = task_data.get("vector_hits", [])
                task_data["vector_hits"] = existing_docs + web_docs
                task_data["web_search_metadata"] = result.get("search_metadata", {})
            
            # Update task data in Redis
            await self.redis_manager.redis.setex(
                f"task:{task_id}",
                600,
                json.dumps(task_data)
            )
            
            logger.info(f"🔗 Integrated {stage} results for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to integrate {stage} results for task {task_id}: {e}")

    async def _advance_to_next_stage(self, task_id: str):
        """Move task to next stage in DAG"""
        task_data = await self.redis_manager.get_task(task_id)
        if not task_data:
            return
        
        current_stage = task_data["current_stage"]
        current_index = task_data["plan"].index(current_stage)
        
        if current_index + 1 < len(task_data["plan"]):
            next_stage = task_data["plan"][current_index + 1]
            
            # Update task with progress
            progress_percentage = int(((current_index + 1) / len(task_data["plan"])) * 100)
            
            # Move to next stage
            task_data["completed_stages"].append(current_stage)
            task_data["current_stage"] = next_stage
            task_data["updated_at"] = datetime.utcnow().isoformat()
            task_data["progress_percentage"] = progress_percentage
            
            # Update in Redis
            await self.redis_manager.redis.setex(
                f"task:{task_id}",
                600,
                json.dumps(task_data)
            )
            
            # Emit progress event
            await self.redis_manager.emit_progress_event(
                task_id=task_id,
                stage="transition",
                message=f"Completed '{current_stage}', moving to '{next_stage}'",
                metadata={
                    "completed_stage": current_stage,
                    "next_stage": next_stage,
                    "progress_percentage": progress_percentage
                }
            )
            
            logger.info(f"🔄 Task {task_id} advanced from '{current_stage}' to '{next_stage}' ({progress_percentage}%)")
        else:
            # No more stages - prepare for completion
            task_data["current_stage"] = None
            await self.redis_manager.redis.setex(
                f"task:{task_id}",
                600,
                json.dumps(task_data)
            )
    
    async def _handle_response_packaging(self, task_id: str, task_data: Dict) -> bool:
        """
        Final stage: package response for frontend
        
        Args:
            task_id: Task identifier
            task_data: Current task data
            
        Returns:
            True if packaging successful
        """
        try:
            # Get AI response from executor stage results
            ai_response = task_data.get("ai_response", {})
            content = ai_response.get("content", task_data.get("context", ""))
            
            # Get vector hits from embedding or web search
            vector_hits = task_data.get("vector_hits", [])
            
            # Get ReAct steps from Redis stream
            react_steps = await self._get_thinking_steps(task_id)
            
            # Calculate confidence from moderation and AI results
            moderation_result = task_data.get("moderation_result", {})
            ai_confidence = ai_response.get("confidence_score", 0.8)
            safety_score = task_data.get("safety_score", 1.0)
            final_confidence = min(ai_confidence, safety_score)
            
            # Package final response
            response = {
                "content": content,
                "sources": vector_hits,
                "confidence": final_confidence,
                "react_steps": react_steps,
                "task_id": task_id,
                "template": task_data.get("template", "standard_query"),
                "completed_stages": task_data.get("completed_stages", []),
                "reasoning_metadata": task_data.get("reasoning_metadata", {}),
                "moderation_result": moderation_result,
                "metadata": {
                    "total_stages": len(task_data.get("plan", [])),
                    "duration_ms": self._calculate_duration(task_data),
                    "agent_count": len(set([step.get("agent", "") for step in react_steps])),
                    "react_steps_count": len(react_steps),
                    "documents_processed": len(vector_hits),
                    "safety_score": safety_score
                }
            }
            
            # Update task with final response
            task_data["response"] = response
            task_data["status"] = "complete" 
            task_data["progress_percentage"] = 100
            task_data["updated_at"] = datetime.utcnow().isoformat()
            
            await self.redis_manager.redis.setex(
                f"task:{task_id}",
                600,
                json.dumps(task_data)
            )
            
            # Emit completion events
            await self.redis_manager.emit_progress_event(
                task_id=task_id,
                stage="complete",
                message="Task completed successfully",
                metadata={
                    "final_response": True,
                    "response_length": len(content),
                    "source_count": len(vector_hits),
                    "react_steps_count": len(react_steps),
                    "final_confidence": final_confidence
                }
            )
            
            await self.message_broker.publish_event("ai:response:ready", {
                "task_id": task_id,
                "response": response,
                "user_id": task_data["user_id"]
            })
            
            logger.info(f"📦 Response packaged successfully for task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error packaging response for task {task_id}: {e}")
            return False
    
    async def _get_thinking_steps(self, task_id: str) -> List[Dict]:
        """Retrieve ReAct steps from Redis stream"""
        try:
            stream_key = f"task:{task_id}:react_steps"
            events = await self.redis_manager.redis.xrange(stream_key)
            
            react_steps = []
            for event_id, fields in events:
                react_steps.append({
                    "id": event_id,
                    "step": fields.get("step", "thought"),
                    "message": fields.get("message", ""),
                    "agent": fields.get("agent", "unknown"),
                    "timestamp": fields.get("timestamp", "")
                })
            
            # Sort by timestamp for proper order
            react_steps.sort(key=lambda x: x.get("timestamp", ""))
            
            return react_steps
            
        except Exception as e:
            logger.error(f"❌ Error retrieving ReAct steps for task {task_id}: {e}")
            return []
    
    def _calculate_duration(self, task_data: Dict) -> int:
        """Calculate task duration in milliseconds"""
        try:
            started_at = datetime.fromisoformat(task_data["started_at"])
            updated_at = datetime.fromisoformat(task_data["updated_at"])
            duration = (updated_at - started_at).total_seconds() * 1000
            return int(duration)
        except:
            return 0
    
    async def _handle_stage_failure(self, task_id: str, stage: str):
        """Handle stage failure with retry logic"""
        try:
            # TODO: Implement retry logic
            # For now, mark task as failed
            task_data = await self.redis_manager.get_task(task_id)
            if task_data:
                task_data["status"] = "failed"
                task_data["error"] = f"Stage '{stage}' failed"
                task_data["updated_at"] = datetime.utcnow().isoformat()
                
                await self.redis_manager.redis.setex(
                    f"task:{task_id}",
                    600,
                    json.dumps(task_data)
                )
                
                await self.redis_manager.emit_progress_event(
                    task_id=task_id,
                    stage="error",
                    message=f"Stage '{stage}' failed",
                    metadata={"failed_stage": stage}
                )
                
            logger.error(f"❌ Stage '{stage}' failed for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling stage failure: {e}")
    
    async def _handle_task_error(self, task_id: str, error: str):
        """Handle general task error"""
        try:
            await self.redis_manager.fail_task(task_id, error)
            logger.error(f"❌ Task {task_id} failed: {error}")
        except Exception as e:
            logger.error(f"❌ Error handling task error: {e}")
    
    async def _complete_task(self, task_id: str):
        """Mark task as complete"""
        try:
            task_data = await self.redis_manager.get_task(task_id)
            if task_data and task_data.get("response"):
                await self.redis_manager.complete_task(task_id, task_data["response"])
                logger.info(f"✅ Task {task_id} completed successfully")
        except Exception as e:
            logger.error(f"❌ Error completing task {task_id}: {e}")
    
    async def _get_dag_template(self, template_name: str) -> Optional[DAGTemplate]:
        """Get DAG template by name"""
        # First check default templates
        if template_name in self.default_templates:
            return self.default_templates[template_name]
        
        # TODO: Check database for custom templates
        return None
    
    async def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current task status"""
        return await self.redis_manager.get_task(task_id)
    
    async def abort_task(self, task_id: str) -> bool:
        """Abort a running task"""
        try:
            if task_id in self.active_tasks:
                self.active_tasks[task_id].cancel()
                del self.active_tasks[task_id]
            
            task_data = await self.redis_manager.get_task(task_id)
            if task_data:
                task_data["status"] = "aborted"
                task_data["updated_at"] = datetime.utcnow().isoformat()
                
                await self.redis_manager.redis.setex(
                    f"task:{task_id}",
                    600,
                    json.dumps(task_data)
                )
                
                await self.redis_manager.emit_progress_event(
                    task_id=task_id,
                    stage="aborted",
                    message="Task aborted by user",
                    metadata={"action": "abort"}
                )
                
                logger.info(f"🛑 Task {task_id} aborted")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error aborting task {task_id}: {e}")
            
        return False
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cancel all active tasks
            for task_id, task in self.active_tasks.items():
                task.cancel()
                logger.info(f"🧹 Cancelled task {task_id}")
            
            self.active_tasks.clear()
            
            # Close connections
            await self.message_broker.close()
            
            logger.info("🧹 Task Coordinator cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
    
    async def _get_adaptive_recommendations(self, user_id: str, query: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """Get adaptive learning recommendations for task optimization"""
        try:
            # Call adaptive engine for optimization recommendations
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                payload = {
                    "user_id": user_id,
                    "query": query,
                    "context": "",  # Will be populated from embeddings
                    "conversation_history": conversation_history or []
                }
                
                async with session.post(
                    "http://adaptive-engine:8015/api/v1/optimization/recommendations", 
                    json=payload
                ) as response:
                    if response.status == 200:
                        recommendations = await response.json()
                        logger.info(f"🧠 Got adaptive recommendations for user {user_id}: confidence {recommendations.get('confidence', 0):.2f}")
                        return recommendations
                    else:
                        logger.warning(f"⚠️ Adaptive engine returned {response.status}, using defaults")
                        return self._get_default_recommendations()
                        
        except Exception as e:
            logger.warning(f"⚠️ Failed to get adaptive recommendations: {e}, using defaults")
            return self._get_default_recommendations()
    
    def _get_default_recommendations(self) -> Dict[str, Any]:
        """Default recommendations when adaptive engine is unavailable"""
        return {
            "response_style": {
                "detail_level": "moderate",
                "technical_depth": "medium",
                "include_examples": True,
                "structured_format": True,
                "confidence": 0.5
            },
            "context_optimization": {
                "context_relevance_score": 0.5,
                "needs_more_context": False,
                "context_optimization": "medium",
                "confidence": 0.5
            },
            "conversation_flow": {
                "flow_stage": "initial",
                "recommended_approach": "direct_answer",
                "confidence": 0.5
            },
            "personalization": {
                "personalization_level": "minimal",
                "confidence": 0.3
            },
            "confidence": 0.4
        } 