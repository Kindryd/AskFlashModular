"""
State Manager for AskFlash MCP Architecture

This service manages task state persistence between Redis and PostgreSQL.
It handles task lifecycle, agent performance tracking, and system analytics.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncpg
from dataclasses import dataclass

from core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class TaskState:
    """Represents current task state"""
    task_id: str
    user_id: str
    status: str
    current_stage: Optional[str]
    completed_stages: List[str]
    progress_percentage: int
    started_at: datetime
    updated_at: datetime
    context: str = ""
    error: Optional[str] = None

@dataclass
class AgentPerformanceData:
    """Agent performance metrics"""
    agent_name: str
    task_id: str
    stage: str
    duration_ms: int
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

class StateManager:
    """
    Manages task state persistence and analytics
    
    Responsibilities:
    - Sync task state between Redis and PostgreSQL
    - Track agent performance metrics
    - Provide analytics and insights
    - Manage task lifecycle events
    """
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.sync_interval = 30  # seconds
        self.cleanup_interval = 3600  # 1 hour
        self.sync_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """Initialize state manager"""
        try:
            # Create database connection pool
            await self._create_db_pool()
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("✅ State Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize State Manager: {e}")
            raise
    
    async def _create_db_pool(self):
        """Create PostgreSQL connection pool"""
        try:
            database_url = settings.POSTGRES_URL
            
            self.db_pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Test connection
            async with self.db_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            logger.info("✅ Connected to PostgreSQL for state management")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise
    
    async def _start_background_tasks(self):
        """Start background sync and cleanup tasks"""
        # State synchronization task
        self.sync_task = asyncio.create_task(self._sync_loop())
        
        # Cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("🔄 Started background state management tasks")
    
    async def persist_task_start(self, task_data: Dict[str, Any]) -> bool:
        """
        Persist task start to database
        
        Args:
            task_data: Task information from Redis
            
        Returns:
            True if persisted successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO task_histories (
                        id, user_id, query, plan, template, status,
                        current_stage, completed_stages, context,
                        progress_percentage, started_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                    ) ON CONFLICT (id) DO UPDATE SET
                        updated_at = $12,
                        status = $6,
                        current_stage = $7,
                        progress_percentage = $10
                """, 
                    task_data["task_id"],
                    task_data["user_id"],
                    task_data["query"],
                    json.dumps(task_data["plan"]),
                    task_data["template"],
                    task_data["status"],
                    task_data.get("current_stage"),
                    json.dumps(task_data.get("completed_stages", [])),
                    task_data.get("context", ""),
                    task_data.get("progress_percentage", 0),
                    datetime.fromisoformat(task_data["started_at"]),
                    datetime.fromisoformat(task_data["updated_at"])
                )
            
            logger.debug(f"💾 Persisted task start: {task_data['task_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error persisting task start: {e}")
            return False
    
    async def update_task_state(self, task_data: Dict[str, Any]) -> bool:
        """
        Update task state in database
        
        Args:
            task_data: Updated task data from Redis
            
        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE task_histories SET
                        status = $1,
                        current_stage = $2,
                        completed_stages = $3,
                        context = $4,
                        response = $5,
                        error = $6,
                        progress_percentage = $7,
                        updated_at = $8
                    WHERE id = $9
                """,
                    task_data["status"],
                    task_data.get("current_stage"),
                    json.dumps(task_data.get("completed_stages", [])),
                    task_data.get("context", ""),
                    json.dumps(task_data.get("response")) if task_data.get("response") else None,
                    task_data.get("error"),
                    task_data.get("progress_percentage", 0),
                    datetime.fromisoformat(task_data["updated_at"]),
                    task_data["task_id"]
                )
            
            logger.debug(f"💾 Updated task state: {task_data['task_id']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating task state: {e}")
            return False
    
    async def log_stage_event(
        self, 
        task_id: str, 
        stage: str, 
        action: str, 
        message: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Log task stage event
        
        Args:
            task_id: Task identifier
            stage: Stage name
            action: Action type (start, complete, fail, retry)
            message: Event message
            metadata: Additional metadata
            
        Returns:
            True if logged successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO task_stage_logs (
                        task_id, stage, action, message, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    task_id,
                    stage,
                    action,
                    message,
                    json.dumps(metadata or {}),
                    datetime.utcnow()
                )
            
            logger.debug(f"📝 Logged stage event: {task_id} {stage} {action}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error logging stage event: {e}")
            return False
    
    async def record_agent_performance(
        self, 
        performance_data: AgentPerformanceData
    ) -> bool:
        """
        Record agent performance metrics
        
        Args:
            performance_data: Agent performance information
            
        Returns:
            True if recorded successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_performance (
                        agent_name, task_id, stage, duration_ms, success,
                        error_message, metadata, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                    performance_data.agent_name,
                    performance_data.task_id,
                    performance_data.stage,
                    performance_data.duration_ms,
                    performance_data.success,
                    performance_data.error_message,
                    json.dumps(performance_data.metadata or {}),
                    datetime.utcnow()
                )
            
            logger.debug(f"📊 Recorded agent performance: {performance_data.agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recording agent performance: {e}")
            return False
    
    async def update_agent_health(
        self, 
        agent_name: str, 
        status: str,
        metrics: Optional[Dict] = None
    ) -> bool:
        """
        Update agent health status
        
        Args:
            agent_name: Agent identifier
            status: Health status (healthy, unhealthy, starting, stopping)
            metrics: Additional health metrics
            
        Returns:
            True if updated successfully
        """
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO agent_health (
                        agent_name, status, last_heartbeat, cpu_usage,
                        memory_usage, queue_size, processed_tasks,
                        failed_tasks, metadata, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (agent_name) DO UPDATE SET
                        status = $2,
                        last_heartbeat = $3,
                        cpu_usage = $4,
                        memory_usage = $5,
                        queue_size = $6,
                        processed_tasks = agent_health.processed_tasks + COALESCE($7, 0),
                        failed_tasks = agent_health.failed_tasks + COALESCE($8, 0),
                        metadata = $9,
                        updated_at = $11
                """,
                    agent_name,
                    status,
                    datetime.utcnow(),
                    metrics.get("cpu_usage") if metrics else None,
                    metrics.get("memory_usage") if metrics else None,
                    metrics.get("queue_size", 0) if metrics else 0,
                    metrics.get("processed_tasks", 0) if metrics else 0,
                    metrics.get("failed_tasks", 0) if metrics else 0,
                    json.dumps(metrics or {}),
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            
            logger.debug(f"💗 Updated agent health: {agent_name} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating agent health: {e}")
            return False
    
    async def get_task_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get task analytics for specified time period
        
        Args:
            hours: Time period in hours
            
        Returns:
            Analytics data
        """
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.db_pool.acquire() as conn:
                # Get task summary
                task_stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN status = 'complete' THEN 1 END) as completed_tasks,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
                        COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as active_tasks,
                        AVG(EXTRACT(EPOCH FROM (updated_at - started_at)) * 1000)::INTEGER as avg_duration_ms
                    FROM task_histories 
                    WHERE started_at >= $1
                """, since_time)
                
                # Get template usage
                template_stats = await conn.fetch("""
                    SELECT 
                        template,
                        COUNT(*) as count,
                        AVG(EXTRACT(EPOCH FROM (updated_at - started_at)) * 1000)::INTEGER as avg_duration_ms
                    FROM task_histories 
                    WHERE started_at >= $1
                    GROUP BY template
                    ORDER BY count DESC
                """, since_time)
                
                # Get hourly breakdown
                hourly_stats = await conn.fetch("""
                    SELECT 
                        DATE_TRUNC('hour', started_at) as hour,
                        COUNT(*) as tasks,
                        COUNT(CASE WHEN status = 'complete' THEN 1 END) as completed
                    FROM task_histories 
                    WHERE started_at >= $1
                    GROUP BY hour
                    ORDER BY hour
                """, since_time)
            
            analytics = {
                "period": f"last_{hours}_hours",
                "task_summary": dict(task_stats),
                "template_usage": [dict(row) for row in template_stats],
                "hourly_breakdown": [
                    {
                        "hour": row["hour"].isoformat(),
                        "tasks": row["tasks"],
                        "completed": row["completed"],
                        "success_rate": round((row["completed"] / row["tasks"]) * 100, 1) if row["tasks"] > 0 else 0
                    }
                    for row in hourly_stats
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Error getting task analytics: {e}")
            return {"error": str(e)}
    
    async def get_agent_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get agent performance summary
        
        Args:
            hours: Time period in hours
            
        Returns:
            Agent performance data
        """
        try:
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            async with self.db_pool.acquire() as conn:
                # Get agent performance
                agent_stats = await conn.fetch("""
                    SELECT 
                        agent_name,
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN success = true THEN 1 END) as successful_tasks,
                        AVG(duration_ms)::INTEGER as avg_duration_ms,
                        MIN(duration_ms) as min_duration_ms,
                        MAX(duration_ms) as max_duration_ms
                    FROM agent_performance 
                    WHERE created_at >= $1
                    GROUP BY agent_name
                    ORDER BY total_tasks DESC
                """, since_time)
                
                # Get current agent health
                health_stats = await conn.fetch("""
                    SELECT 
                        agent_name, status, last_heartbeat,
                        cpu_usage, memory_usage, queue_size,
                        processed_tasks, failed_tasks
                    FROM agent_health
                    ORDER BY agent_name
                """)
            
            summary = {
                "period": f"last_{hours}_hours",
                "agent_performance": [
                    {
                        **dict(row),
                        "success_rate": round((row["successful_tasks"] / row["total_tasks"]) * 100, 1) if row["total_tasks"] > 0 else 0
                    }
                    for row in agent_stats
                ],
                "agent_health": [
                    {
                        **dict(row),
                        "last_heartbeat": row["last_heartbeat"].isoformat() if row["last_heartbeat"] else None,
                        "is_healthy": row["status"] == "healthy" and 
                                    row["last_heartbeat"] and 
                                    (datetime.utcnow() - row["last_heartbeat"]).total_seconds() < 300
                    }
                    for row in health_stats
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error getting agent performance summary: {e}")
            return {"error": str(e)}
    
    async def _sync_loop(self):
        """Background task to sync Redis state to PostgreSQL"""
        while True:
            try:
                await asyncio.sleep(self.sync_interval)
                # TODO: Implement Redis to PostgreSQL sync
                logger.debug("🔄 Running state sync (placeholder)")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in sync loop: {e}")
    
    async def _cleanup_loop(self):
        """Background task to cleanup old data"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Cleanup old task stage logs (older than 7 days)
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                
                async with self.db_pool.acquire() as conn:
                    deleted_logs = await conn.execute("""
                        DELETE FROM task_stage_logs 
                        WHERE created_at < $1
                    """, cutoff_time)
                    
                    deleted_performance = await conn.execute("""
                        DELETE FROM agent_performance 
                        WHERE created_at < $1
                    """, cutoff_time)
                
                if deleted_logs or deleted_performance:
                    logger.info(f"🧹 Cleaned up old data: {deleted_logs} logs, {deleted_performance} performance records")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")
    
    async def get_task_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get task history for user
        
        Args:
            user_id: User identifier
            limit: Maximum number of tasks to return
            
        Returns:
            List of task histories
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        id, query, template, status, progress_percentage,
                        started_at, updated_at, 
                        EXTRACT(EPOCH FROM (updated_at - started_at)) * 1000 as duration_ms
                    FROM task_histories 
                    WHERE user_id = $1
                    ORDER BY started_at DESC
                    LIMIT $2
                """, user_id, limit)
            
            return [
                {
                    "task_id": row["id"],
                    "query": row["query"],
                    "template": row["template"],
                    "status": row["status"],
                    "progress_percentage": row["progress_percentage"],
                    "started_at": row["started_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat(),
                    "duration_ms": int(row["duration_ms"]) if row["duration_ms"] else 0
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting task history: {e}")
            return []
    
    async def cleanup(self):
        """Cleanup state manager resources"""
        try:
            # Cancel background tasks
            if self.sync_task:
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
            
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Close database pool
            if self.db_pool:
                await self.db_pool.close()
            
            logger.info("🧹 State Manager cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Error during State Manager cleanup: {e}") 