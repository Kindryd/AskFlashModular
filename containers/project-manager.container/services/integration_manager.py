import httpx
import json
from typing import Dict, Any, Optional, List
from jira import JIRA
from core.config import settings
from core.database import get_db, Integration, IntegrationLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class IntegrationManager:
    """Manages integrations with external services like JIRA"""
    
    def __init__(self):
        self.jira_url = settings.JIRA_URL
        self.jira_token = settings.JIRA_TOKEN
        self.jira_username = settings.JIRA_USERNAME
        self.timeout = settings.INTEGRATION_TIMEOUT
        self.max_retries = settings.MAX_INTEGRATION_RETRIES
        
    def is_jira_configured(self) -> bool:
        """Check if JIRA integration is properly configured"""
        return bool(self.jira_url and self.jira_token)
    
    async def get_jira_client(self) -> Optional[JIRA]:
        """Get JIRA client if configured"""
        if not self.is_jira_configured():
            return None
            
        try:
            # Create JIRA client with token authentication
            jira = JIRA(
                server=self.jira_url,
                token_auth=self.jira_token,
                timeout=self.timeout
            )
            return jira
        except Exception as e:
            logger.error(f"Failed to create JIRA client: {e}")
            return None
    
    async def create_jira_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium"
    ) -> Dict[str, Any]:
        """Create a JIRA issue"""
        if not self.is_jira_configured():
            return {
                "success": False,
                "error": "JIRA not configured"
            }
        
        try:
            jira = await self.get_jira_client()
            if not jira:
                return {
                    "success": False,
                    "error": "Failed to connect to JIRA"
                }
            
            # Create issue
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
            
            issue = jira.create_issue(fields=issue_dict)
            
            # Log the action
            await self._log_integration_action(
                integration_name="jira",
                action="create_issue",
                status="success",
                request_data=issue_dict,
                response_data={"issue_key": issue.key, "issue_id": issue.id}
            )
            
            return {
                "success": True,
                "issue_key": issue.key,
                "issue_id": issue.id,
                "issue_url": f"{self.jira_url}/browse/{issue.key}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create JIRA issue: {e}")
            
            # Log the error
            await self._log_integration_action(
                integration_name="jira",
                action="create_issue",
                status="error",
                request_data={"summary": summary, "project": project_key},
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_jira_issues(
        self,
        jql: str,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """Search JIRA issues using JQL"""
        if not self.is_jira_configured():
            return {
                "success": False,
                "error": "JIRA not configured"
            }
        
        try:
            jira = await self.get_jira_client()
            if not jira:
                return {
                    "success": False,
                    "error": "Failed to connect to JIRA"
                }
            
            # Search issues
            issues = jira.search_issues(jql, maxResults=max_results)
            
            issue_data = []
            for issue in issues:
                issue_data.append({
                    "key": issue.key,
                    "id": issue.id,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                    "created": issue.fields.created,
                    "updated": issue.fields.updated,
                    "url": f"{self.jira_url}/browse/{issue.key}"
                })
            
            # Log the action
            await self._log_integration_action(
                integration_name="jira",
                action="search_issues",
                status="success",
                request_data={"jql": jql, "max_results": max_results},
                response_data={"count": len(issue_data)}
            )
            
            return {
                "success": True,
                "issues": issue_data,
                "total": len(issue_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to search JIRA issues: {e}")
            
            # Log the error
            await self._log_integration_action(
                integration_name="jira",
                action="search_issues",
                status="error",
                request_data={"jql": jql},
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_jira_projects(self) -> Dict[str, Any]:
        """Get list of JIRA projects"""
        if not self.is_jira_configured():
            return {
                "success": False,
                "error": "JIRA not configured"
            }
        
        try:
            jira = await self.get_jira_client()
            if not jira:
                return {
                    "success": False,
                    "error": "Failed to connect to JIRA"
                }
            
            # Get projects
            projects = jira.projects()
            
            project_data = []
            for project in projects:
                project_data.append({
                    "key": project.key,
                    "name": project.name,
                    "description": getattr(project, 'description', ''),
                    "lead": getattr(project, 'lead', {}).get('displayName', '') if hasattr(project, 'lead') else ''
                })
            
            return {
                "success": True,
                "projects": project_data,
                "total": len(project_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get JIRA projects: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_jira_connection(self) -> Dict[str, Any]:
        """Test JIRA connection"""
        if not self.is_jira_configured():
            return {
                "status": "not_configured",
                "message": "JIRA credentials not provided"
            }
        
        try:
            jira = await self.get_jira_client()
            if not jira:
                return {
                    "status": "failed",
                    "message": "Failed to create JIRA client"
                }
            
            # Test by getting user info
            current_user = jira.current_user()
            
            return {
                "status": "success",
                "message": "JIRA connection successful",
                "user": current_user,
                "server": self.jira_url
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"JIRA connection failed: {str(e)}"
            }
    
    async def _log_integration_action(
        self,
        integration_name: str,
        action: str,
        status: str,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        response_time_ms: Optional[int] = None
    ):
        """Log integration action to database"""
        try:
            # For now, just log to console - database integration can be added later
            logger.info(f"Integration action: {integration_name}.{action} - {status}")
            if error_message:
                logger.error(f"Integration error: {error_message}")
                
        except Exception as e:
            logger.error(f"Failed to log integration action: {e}")
    
 