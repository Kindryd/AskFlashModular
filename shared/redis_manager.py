"""
Redis Task Manager for AskFlash MCP Architecture

This module provides Redis-based task management capabilities for the Master Control Program (MCP).
It handles task state storage, progress tracking, and event streaming.
"""

import redis
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class RedisTaskManager:
    """Manages task state and progress in Redis for MCP coordination"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", password: str = "askflash123"):
        self.redis_url = redis_url
        self.password = password
        self.redis = redis.from_url(redis_url, decode_responses=True, password=password)
        self.task_ttl = 600  # 10 minutes default TTL
        
    def create_task(self, user_id: str, query: str, plan: List[str], template: str = "standard_query") -> str:
        """Create a new task DAG in Redis"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "query": query,
            "plan": plan,
            "template": template,
            "current_stage": plan[0] if plan else None,
            "completed_stages": [],
            "status": "in_progress",
            "context": "",
            "vector_hits": [],
            "response": None,
            "error": None,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "progress_percentage": 0
        }
        
        # Store main task data
        task_key = f"task:{task_id}"
        self.redis.setex(task_key, self.task_ttl, json.dumps(task_data))
        
        # Initialize progress stream
        self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": "initialized", 
                "message": f"Task created with template '{template}'", 
                "timestamp": datetime.utcnow().isoformat(),
                "progress": "0"
            }
        )
        
        # Track user tasks
        user_tasks_key = f"user:{user_id}:tasks"
        self.redis.lpush(user_tasks_key, task_id)
        self.redis.expire(user_tasks_key, self.task_ttl * 2)  # Keep user task list longer
        
        logger.info(f"Created task {task_id} for user {user_id} with plan: {plan}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve task data"""
        task_key = f"task:{task_id}"
        task_data_str = self.redis.get(task_key)
        
        if task_data_str:
            try:
                return json.loads(task_data_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode task data for {task_id}: {e}")
                return None
        return None
    
    def update_task_stage(self, task_id: str, new_stage: str, context: str = None, progress_message: str = None):
        """Update task to next stage"""
        task_key = f"task:{task_id}"
        task_data = self.get_task(task_id)
        
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
        
        # Move current stage to completed
        if task_data["current_stage"]:
            task_data["completed_stages"].append(task_data["current_stage"])
        
        # Calculate progress percentage
        total_stages = len(task_data["plan"])
        completed_stages = len(task_data["completed_stages"])
        progress_percentage = int((completed_stages / total_stages) * 100) if total_stages > 0 else 0
        
        task_data["current_stage"] = new_stage
        task_data["updated_at"] = datetime.utcnow().isoformat()
        task_data["progress_percentage"] = progress_percentage
        
        if context:
            task_data["context"] = context
        
        # Update in Redis
        self.redis.setex(task_key, self.task_ttl, json.dumps(task_data))
        
        # Add progress event
        self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": new_stage, 
                "message": progress_message or f"Advanced to {new_stage}",
                "timestamp": datetime.utcnow().isoformat(),
                "progress": str(progress_percentage)
            }
        )
        
        logger.info(f"Task {task_id} advanced to stage {new_stage} ({progress_percentage}% complete)")
    
    def complete_task(self, task_id: str, response: Dict[str, Any]):
        """Mark task as complete with final response"""
        task_data = self.get_task(task_id)
        
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
        
        # Move current stage to completed if exists
        if task_data["current_stage"]:
            task_data["completed_stages"].append(task_data["current_stage"])
        
        task_data["current_stage"] = None
        task_data["status"] = "complete"
        task_data["response"] = response
        task_data["updated_at"] = datetime.utcnow().isoformat()
        task_data["progress_percentage"] = 100
        
        # Store updated task
        task_key = f"task:{task_id}"
        self.redis.setex(task_key, self.task_ttl, json.dumps(task_data))
        
        # Final progress event
        self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": "complete", 
                "message": "Task completed successfully",
                "timestamp": datetime.utcnow().isoformat(),
                "progress": "100"
            }
        )
        
        logger.info(f"Task {task_id} completed successfully")
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed"""
        task_data = self.get_task(task_id)
        
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
        
        task_data["status"] = "failed"
        task_data["error"] = error
        task_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Store updated task
        task_key = f"task:{task_id}"
        self.redis.setex(task_key, self.task_ttl, json.dumps(task_data))
        
        # Error progress event
        self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": "error", 
                "message": f"Task failed: {error}",
                "timestamp": datetime.utcnow().isoformat(),
                "progress": str(task_data.get("progress_percentage", 0))
            }
        )
        
        logger.error(f"Task {task_id} failed: {error}")
    
    def emit_progress_event(self, task_id: str, stage: str, message: str, metadata: Dict = None):
        """Emit progress event for frontend consumption"""
        event_data = {
            "task_id": task_id,
            "stage": stage,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            event_data.update(metadata)
        
        # Publish to Redis pub/sub for real-time updates
        channel = f"ai:progress:{task_id}"
        self.redis.publish(channel, json.dumps(event_data))
        
        # Also add to progress stream for persistence
        self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": stage,
                "message": message,
                "timestamp": event_data["timestamp"],
                "metadata": json.dumps(metadata) if metadata else "{}"
            }
        )
        
        logger.debug(f"Emitted progress event for task {task_id}: {message}")
    
    def get_progress_stream(self, task_id: str, start: str = "-", end: str = "+") -> List[Dict]:
        """Retrieve progress events from stream"""
        try:
            stream_key = f"task:{task_id}:progress"
            events = self.redis.xrange(stream_key, start, end)
            
            progress_events = []
            for event_id, fields in events:
                event = {
                    "id": event_id,
                    "stage": fields.get("stage", ""),
                    "message": fields.get("message", ""),
                    "timestamp": fields.get("timestamp", ""),
                    "progress": fields.get("progress", "0")
                }
                
                if "metadata" in fields:
                    try:
                        event["metadata"] = json.loads(fields["metadata"])
                    except json.JSONDecodeError:
                        event["metadata"] = {}
                
                progress_events.append(event)
            
            return progress_events
            
        except Exception as e:
            logger.error(f"Error retrieving progress stream for task {task_id}: {e}")
            return []
    
    def update_task_context(self, task_id: str, context_updates: Dict[str, Any]):
        """Update specific fields in task context"""
        task_data = self.get_task(task_id)
        
        if not task_data:
            raise ValueError(f"Task {task_id} not found")
        
        # Update context fields
        if "context" in context_updates:
            task_data["context"] = context_updates["context"]
        if "vector_hits" in context_updates:
            task_data["vector_hits"] = context_updates["vector_hits"]
        if "agent_data" in context_updates:
            if "agent_data" not in task_data:
                task_data["agent_data"] = {}
            task_data["agent_data"].update(context_updates["agent_data"])
        
        task_data["updated_at"] = datetime.utcnow().isoformat()
        
        # Store updated task
        task_key = f"task:{task_id}"
        self.redis.setex(task_key, self.task_ttl, json.dumps(task_data))
        
        logger.debug(f"Updated context for task {task_id}")
    
    def get_user_tasks(self, user_id: str, limit: int = 10) -> List[str]:
        """Get recent task IDs for a user"""
        user_tasks_key = f"user:{user_id}:tasks"
        return self.redis.lrange(user_tasks_key, 0, limit - 1)
    
    def cleanup_expired_tasks(self):
        """Clean up expired task data"""
        try:
            # Find expired task keys
            pattern = "task:*"
            expired_count = 0
            
            for key in self.redis.scan_iter(match=pattern):
                # Check if key still exists (not expired)
                if not self.redis.exists(key):
                    continue
                
                # Check task data for expiration
                if ":progress" in key or ":context" in key:
                    continue  # Skip non-main task keys
                    
                task_data_str = self.redis.get(key)
                if task_data_str:
                    try:
                        task_data = json.loads(task_data_str)
                        started_at = datetime.fromisoformat(task_data["started_at"])
                        
                        # Remove tasks older than 1 hour
                        if datetime.utcnow() - started_at > timedelta(hours=1):
                            task_id = key.split(":")[1]
                            
                            # Delete task and related keys
                            self.redis.delete(key)
                            self.redis.delete(f"task:{task_id}:progress")
                            self.redis.delete(f"task:{task_id}:context")
                            
                            expired_count += 1
                            
                    except (json.JSONDecodeError, ValueError, KeyError):
                        # Invalid task data, delete it
                        self.redis.delete(key)
                        expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired tasks")
                
        except Exception as e:
            logger.error(f"Error during task cleanup: {e}")

# Async version for use in async contexts
class AsyncRedisTaskManager:
    """Async version of RedisTaskManager"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", password: str = "askflash123"):
        import redis.asyncio as aioredis
        self.redis_url = redis_url
        self.password = password
        self.redis = aioredis.from_url(redis_url, decode_responses=True, password=password)
        self.task_ttl = 600
    
    async def initialize(self):
        """Initialize async Redis connection"""
        try:
            # Test connection
            await self.redis.ping()
            logger.info("✅ AsyncRedisTaskManager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AsyncRedisTaskManager: {e}")
            raise
    
    async def create_task(self, user_id: str, query: str, plan: List[str], template: str = "standard_query") -> str:
        """Async version of create_task"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "query": query,
            "plan": plan,
            "template": template,
            "current_stage": plan[0] if plan else None,
            "completed_stages": [],
            "status": "in_progress",
            "context": "",
            "vector_hits": [],
            "response": None,
            "error": None,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "progress_percentage": 0
        }
        
        # Store main task data
        await self.redis.setex(f"task:{task_id}", self.task_ttl, json.dumps(task_data))
        
        # Initialize progress stream
        await self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": "initialized",
                "message": f"Task created with template '{template}'",
                "timestamp": datetime.utcnow().isoformat(),
                "progress": "0"
            }
        )
        
        return task_id
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Async version of get_task"""
        task_data_str = await self.redis.get(f"task:{task_id}")
        if task_data_str:
            try:
                return json.loads(task_data_str)
            except json.JSONDecodeError:
                return None
        return None
    
    async def emit_progress_event(self, task_id: str, stage: str, message: str, metadata: Dict = None):
        """Async version of emit_progress_event"""
        event_data = {
            "task_id": task_id,
            "stage": stage,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if metadata:
            event_data.update(metadata)
        
        # Publish to Redis pub/sub
        await self.redis.publish(f"ai:progress:{task_id}", json.dumps(event_data))
        
        # Add to progress stream
        await self.redis.xadd(
            f"task:{task_id}:progress",
            {
                "stage": stage,
                "message": message,
                "timestamp": event_data["timestamp"],
                "metadata": json.dumps(metadata) if metadata else "{}"
            }
        )
</rewritten_file> 