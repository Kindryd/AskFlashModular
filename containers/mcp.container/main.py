from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from contextlib import asynccontextmanager
import logging
import json
import asyncio
from typing import Dict, Any, Optional
import os

from core.config import settings
from core.database import get_db
from api.routes import router as api_router
from services.quality_analyzer import InformationQualityAnalyzer
from services.intent_ai import ConversationIntentAI
from services.task_coordinator import TaskCoordinator
from services.message_broker import MessageBroker
from services.state_manager import StateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global service instances
quality_analyzer = InformationQualityAnalyzer()
task_coordinator: Optional[TaskCoordinator] = None
message_broker: Optional[MessageBroker] = None
state_manager: Optional[StateManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global task_coordinator, message_broker, state_manager
    
    logger.info("🐄 Flash AI MCP (Master Control Program) starting up...")
    
    # Initialize core MCP services
    try:
        # Initialize message broker
        message_broker = MessageBroker()
        await message_broker.connect()
        logger.info("✅ Message Broker initialized")
        
        # Initialize state manager
        state_manager = StateManager()
        await state_manager.initialize()
        logger.info("✅ State Manager initialized")
        
        # Initialize task coordinator
        task_coordinator = TaskCoordinator()
        await task_coordinator.initialize()
        logger.info("✅ Task Coordinator initialized")
        
        # Initialize existing services
        logger.info("✅ Information Quality Analyzer ready")
        logger.info("✅ Intent AI system ready")
        
        logger.info("🚀 MCP fully operational - ready for multi-agent AI coordination")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize MCP: {e}")
        raise
    
    yield
    
    # Cleanup on shutdown
    logger.info("🛑 Flash AI MCP shutting down...")
    try:
        if task_coordinator:
            await task_coordinator.cleanup()
        if message_broker:
            await message_broker.close()
        if state_manager:
            await state_manager.cleanup()
        logger.info("🧹 MCP cleanup completed")
    except Exception as e:
        logger.error(f"❌ Error during MCP cleanup: {e}")

app = FastAPI(
    title="Flash AI MCP",
    description="🐄 Master Control Program for Multi-Agent AI Coordination",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint returning MCP status"""
    return {
        "status": "operational",
        "service": "Flash AI MCP",
        "version": "3.0.0",
        "description": "🐄 Master Control Program for Multi-Agent AI Coordination",
        "capabilities": [
            "DAG Task Orchestration",
            "Multi-Agent Coordination",
            "Real-time Progress Tracking",
            "Information Quality Analysis", 
            "Intent AI (GPT-3.5)",
            "Provider Routing",
            "State Management",
            "Performance Analytics"
        ]
    }

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "service": "mcp",
            "version": "3.0.0"
        }
        
        # Check core services
        if message_broker:
            broker_health = await message_broker.health_check()
            health_status["message_broker"] = broker_health["overall"]
            health_status["rabbitmq"] = "connected" if broker_health["rabbitmq"]["connected"] else "disconnected"
            health_status["redis"] = "connected" if broker_health["redis"]["connected"] else "disconnected"
        else:
            health_status["message_broker"] = "not_initialized"
        
        # Check other services
        health_status["openai_configured"] = str(bool(settings.OPENAI_API_KEY))
        health_status["quality_analyzer"] = "ready"
        health_status["intent_ai"] = "ready"
        health_status["task_coordinator"] = "ready" if task_coordinator else "not_initialized"
        health_status["state_manager"] = "ready" if state_manager else "not_initialized"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """Get MCP capabilities"""
    return {
        "task_coordination": {
            "dag_execution": True,
            "multi_agent_orchestration": True,
            "real_time_progress": True,
            "state_persistence": True,
            "performance_tracking": True
        },
        "messaging": {
            "rabbitmq_queues": True,
            "redis_pubsub": True,
            "task_routing": True,
            "event_streaming": True
        },
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
            "model": "gpt-3.5-turbo"
        },
        "agent_management": {
            "health_monitoring": True,
            "performance_analytics": True,
            "load_balancing": True,
            "failure_recovery": True
        }
    }

@app.post("/api/v1/tasks/create")
async def create_task(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Create and execute new MCP task
    
    Expected request format:
    {
        "user_id": "string",
        "query": "string", 
        "template": "string" (optional, defaults to "standard_query"),
        "conversation_id": "string" (optional)
    }
    """
    try:
        if not task_coordinator:
            raise HTTPException(status_code=503, detail="Task Coordinator not available")
        
        # Validate request
        user_id = request.get("user_id")
        query = request.get("query")
        
        if not user_id or not query:
            raise HTTPException(status_code=400, detail="user_id and query are required")
        
        template = request.get("template", "standard_query")
        conversation_id = request.get("conversation_id")
        
        # Create and execute task
        task_id = await task_coordinator.create_and_execute_task(
            user_id=user_id,
            query=query,
            template=template,
            conversation_id=conversation_id
        )
        
        logger.info(f"🚀 Created MCP task {task_id} for user {user_id}")
        
        return {
            "task_id": task_id,
            "status": "created",
            "message": "Task created and execution started",
            "template": template,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks/{task_id}/status")
async def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get current task status"""
    try:
        if not task_coordinator:
            raise HTTPException(status_code=503, detail="Task Coordinator not available")
        
        task_data = await task_coordinator.get_task_status(task_id)
        
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task_id,
            "status": task_data["status"],
            "current_stage": task_data.get("current_stage"),
            "completed_stages": task_data.get("completed_stages", []),
            "progress_percentage": task_data.get("progress_percentage", 0),
            "started_at": task_data["started_at"],
            "updated_at": task_data["updated_at"],
            "template": task_data.get("template"),
            "plan": task_data.get("plan", []),
            "error": task_data.get("error")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tasks/{task_id}/progress")
async def get_task_progress(task_id: str) -> Dict[str, Any]:
    """Get detailed task progress including thinking steps"""
    try:
        from shared.redis_manager import AsyncRedisTaskManager
        
        redis_manager = AsyncRedisTaskManager()
        
        # Get basic task data
        task_data = await redis_manager.get_task(task_id)
        if not task_data:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get progress stream
        progress_events = redis_manager.get_progress_stream(task_id)
        
        return {
            "task_id": task_id,
            "status": task_data["status"],
            "progress_percentage": task_data.get("progress_percentage", 0),
            "current_stage": task_data.get("current_stage"),
            "thinking_steps": progress_events,
            "total_stages": len(task_data.get("plan", [])),
            "completed_stages": len(task_data.get("completed_stages", [])),
            "last_updated": task_data["updated_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting task progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tasks/{task_id}/abort")
async def abort_task(task_id: str) -> Dict[str, Any]:
    """Abort a running task"""
    try:
        if not task_coordinator:
            raise HTTPException(status_code=503, detail="Task Coordinator not available")
        
        success = await task_coordinator.abort_task(task_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found or could not be aborted")
        
        return {
            "task_id": task_id,
            "status": "aborted",
            "message": "Task aborted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error aborting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/tasks")
async def get_task_analytics(hours: int = 24) -> Dict[str, Any]:
    """Get task analytics for specified time period"""
    try:
        if not state_manager:
            raise HTTPException(status_code=503, detail="State Manager not available")
        
        analytics = await state_manager.get_task_analytics(hours=hours)
        return analytics
        
    except Exception as e:
        logger.error(f"❌ Error getting task analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/agents")
async def get_agent_analytics(hours: int = 24) -> Dict[str, Any]:
    """Get agent performance analytics"""
    try:
        if not state_manager:
            raise HTTPException(status_code=503, detail="State Manager not available")
        
        analytics = await state_manager.get_agent_performance_summary(hours=hours)
        return analytics
        
    except Exception as e:
        logger.error(f"❌ Error getting agent analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/system/status")
async def get_system_status() -> Dict[str, Any]:
    """Get comprehensive system status including all agent containers"""
    try:
        import httpx
        import asyncio
        from datetime import datetime
        
        # MCP Core Status
        status = {
            "mcp": {
                "version": "3.0.0",
                "status": "operational",
                "timestamp": datetime.utcnow().isoformat()
            },
            "core_services": {
                "task_coordinator": task_coordinator is not None,
                "message_broker": message_broker is not None,
                "state_manager": state_manager is not None,
                "quality_analyzer": True,
                "intent_ai": True
            },
            "infrastructure": {},
            "agents": {},
            "active_tasks": len(task_coordinator.active_tasks) if task_coordinator else 0,
            "overall_health": "unknown"
        }
        
        # Get infrastructure status
        if message_broker:
            broker_health = await message_broker.health_check()
            status["infrastructure"] = {
                "rabbitmq": {
                    "connected": broker_health["rabbitmq"]["connected"],
                    "channel_open": broker_health["rabbitmq"]["channel_open"]
                },
                "redis": {
                    "connected": broker_health["redis"]["connected"]
                }
            }
        
        # Check agent health via HTTP
        agent_services = {
            "intent-agent": "http://intent-agent:8010/health",
            "executor-agent": "http://executor-agent:8011/health", 
            "websearch-agent": "http://websearch-agent:8012/health",
            "moderator-agent": "http://moderator-agent:8013/health",
            "conversation": "http://conversation:8001/health",
            "embedding": "http://embedding:8002/health"
        }
        
        async def check_agent_health(agent_name: str, health_url: str):
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(health_url)
                    return {
                        "agent": agent_name,
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000),
                        "url": health_url
                    }
            except Exception as e:
                return {
                    "agent": agent_name,
                    "status": "unavailable",
                    "error": str(e),
                    "url": health_url
                }
        
        # Check all agents concurrently
        agent_tasks = [
            check_agent_health(agent_name, health_url) 
            for agent_name, health_url in agent_services.items()
        ]
        
        agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Process agent results
        healthy_agents = 0
        total_agents = len(agent_services)
        
        for result in agent_results:
            if isinstance(result, dict):
                agent_name = result["agent"]
                status["agents"][agent_name] = result
                if result["status"] == "healthy":
                    healthy_agents += 1
            else:
                # Handle exceptions
                logger.error(f"Error checking agent health: {result}")
        
        # Calculate overall health
        infrastructure_healthy = (
            status["infrastructure"].get("rabbitmq", {}).get("connected", False) and
            status["infrastructure"].get("redis", {}).get("connected", False)
        )
        
        core_services_healthy = all(status["core_services"].values())
        agent_health_ratio = healthy_agents / total_agents if total_agents > 0 else 0
        
        if infrastructure_healthy and core_services_healthy and agent_health_ratio >= 0.8:
            status["overall_health"] = "healthy"
        elif infrastructure_healthy and core_services_healthy and agent_health_ratio >= 0.6:
            status["overall_health"] = "degraded"
        else:
            status["overall_health"] = "unhealthy"
        
        status["health_summary"] = {
            "agents_healthy": f"{healthy_agents}/{total_agents}",
            "core_services_healthy": core_services_healthy,
            "infrastructure_healthy": infrastructure_healthy
        }
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/queues/status")
async def get_queue_status() -> Dict[str, Any]:
    """Get RabbitMQ queue status"""
    try:
        if not message_broker:
            raise HTTPException(status_code=503, detail="Message Broker not available")
        
        queues = [
            "intent.task",
            "embedding.task", 
            "executor.task",
            "moderator.task",
            "websearch.task",
            "mcp.responses"
        ]
        
        queue_statuses = []
        for queue_name in queues:
            status = await message_broker.get_queue_status(queue_name)
            queue_statuses.append(status)
        
        return {
            "queues": queue_statuses,
            "total_queues": len(queues),
            "timestamp": "datetime.utcnow().isoformat()"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP error in MCP: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "service": "Flash AI MCP"
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error in MCP: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal MCP error",
            "service": "Flash AI MCP"
        },
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8003, 
        reload=True,
        log_level="info"
    ) 