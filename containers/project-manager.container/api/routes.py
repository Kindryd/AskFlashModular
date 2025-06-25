from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
from services.teams_bot import TeamsBot
from services.integration_manager import IntegrationManager
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

# Pydantic models for request/response
class TeamsMessageRequest(BaseModel):
    title: str
    message: str
    color: Optional[str] = "7ed321"
    facts: Optional[Dict[str, str]] = None

class JiraIssueRequest(BaseModel):
    project_key: str
    summary: str
    description: str
    issue_type: Optional[str] = "Task"
    priority: Optional[str] = "Medium"

class JiraSearchRequest(BaseModel):
    jql: str
    max_results: Optional[int] = 50

class FlashNotificationRequest(BaseModel):
    event_type: str
    details: Dict[str, Any]

# Teams Bot Endpoints
@router.post("/teams/send-message")
async def send_teams_message(request: TeamsMessageRequest):
    """Send a message to Teams channel"""
    teams_bot = TeamsBot()
    
    success = await teams_bot.send_message(
        title=request.title,
        message=request.message,
        color=request.color,
        facts=request.facts
    )
    
    if success:
        return {"status": "success", "message": "Teams message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Teams message")

@router.post("/teams/send-notification")
async def send_flash_notification(request: FlashNotificationRequest):
    """Send Flash AI specific notification to Teams"""
    teams_bot = TeamsBot()
    
    success = await teams_bot.send_flash_notification(
        event_type=request.event_type,
        details=request.details
    )
    
    if success:
        return {"status": "success", "message": "Flash notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Flash notification")

@router.get("/teams/test")
async def test_teams_connection():
    """Test Teams webhook connection"""
    teams_bot = TeamsBot()
    result = await teams_bot.test_connection()
    return result

@router.get("/teams/status")
async def get_teams_status():
    """Get Teams integration status"""
    teams_bot = TeamsBot()
    return {
        "configured": teams_bot.is_configured(),
        "webhook_url": bool(teams_bot.webhook_url),
        "bot_name": teams_bot.bot_name
    }

# JIRA Integration Endpoints
@router.post("/jira/create-issue")
async def create_jira_issue(request: JiraIssueRequest):
    """Create a JIRA issue"""
    integration_manager = IntegrationManager()
    
    result = await integration_manager.create_jira_issue(
        project_key=request.project_key,
        summary=request.summary,
        description=request.description,
        issue_type=request.issue_type,
        priority=request.priority
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@router.post("/jira/search-issues")
async def search_jira_issues(request: JiraSearchRequest):
    """Search JIRA issues using JQL"""
    integration_manager = IntegrationManager()
    
    result = await integration_manager.search_jira_issues(
        jql=request.jql,
        max_results=request.max_results
    )
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@router.get("/jira/projects")
async def get_jira_projects():
    """Get list of JIRA projects"""
    integration_manager = IntegrationManager()
    
    result = await integration_manager.get_jira_projects()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@router.get("/jira/test")
async def test_jira_connection():
    """Test JIRA connection"""
    integration_manager = IntegrationManager()
    result = await integration_manager.test_jira_connection()
    return result

@router.get("/jira/status")
async def get_jira_status():
    """Get JIRA integration status"""
    integration_manager = IntegrationManager()
    return {
        "configured": integration_manager.is_jira_configured(),
        "server_url": integration_manager.jira_url,
        "has_token": bool(integration_manager.jira_token)
    }

# Integration Management Endpoints
@router.get("/integrations/stats")
async def get_integration_stats():
    """Get integration usage statistics"""
    integration_manager = IntegrationManager()
    return {
        "integrations": [],
        "total_integrations": 0,
        "total_logs": 0,
        "jira_configured": integration_manager.is_jira_configured(),
        "teams_configured": False,
        "message": "Integration statistics - database logging temporarily disabled"
    }

@router.get("/capabilities")
async def get_capabilities():
    """Get project manager service capabilities"""
    teams_bot = TeamsBot()
    integration_manager = IntegrationManager()
    
    return {
        "service": "project-manager",
        "version": "2.0.0",
        "capabilities": [
            "teams_integration",
            "jira_integration", 
            "notification_system",
            "integration_logging",
            "webhook_management"
        ],
        "integrations": {
            "teams": {
                "configured": teams_bot.is_configured(),
                "features": [
                    "send_messages",
                    "flash_notifications", 
                    "connection_testing",
                    "adaptive_cards"
                ]
            },
            "jira": {
                "configured": integration_manager.is_jira_configured(),
                "features": [
                    "create_issues",
                    "search_issues",
                    "get_projects",
                    "connection_testing"
                ]
            }
        },
        "endpoints": {
            "teams": [
                "/teams/send-message",
                "/teams/send-notification", 
                "/teams/test",
                "/teams/status"
            ],
            "jira": [
                "/jira/create-issue",
                "/jira/search-issues",
                "/jira/projects",
                "/jira/test",
                "/jira/status"
            ],
            "general": [
                "/integrations/stats",
                "/capabilities"
            ]
        }
    }

# Health and utility endpoints
@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "service": "project-manager"}

@router.post("/notify-ai-response")
async def notify_ai_response(
    question: str = Body(...),
    answer: str = Body(...),
    user_id: str = Body(...),
    confidence: float = Body(0.0),
    sources: Optional[list] = Body(None)
):
    """Notify Teams about AI response (called by other services)"""
    teams_bot = TeamsBot()
    
    success = await teams_bot.send_ai_response(
        question=question,
        answer=answer,
        user_id=user_id,
        confidence=confidence,
        sources=sources
    )
    
    if success:
        return {"status": "success", "message": "AI response notification sent"}
    else:
        return {"status": "warning", "message": "Teams notification not configured or failed"}

@router.post("/system-health-notification")
async def send_system_health_notification(
    status: str = Body(...),
    services_count: int = Body(...),
    uptime: str = Body(...),
    active_users: int = Body(0),
    total_conversations: int = Body(0)
):
    """Send system health notification to Teams"""
    teams_bot = TeamsBot()
    
    success = await teams_bot.send_flash_notification(
        event_type="system_health",
        details={
            "status": status,
            "services_count": services_count,
            "uptime": uptime,
            "active_users": active_users,
            "total_conversations": total_conversations
        }
    )
    
    if success:
        return {"status": "success", "message": "System health notification sent"}
    else:
        return {"status": "warning", "message": "Teams notification not configured or failed"} 