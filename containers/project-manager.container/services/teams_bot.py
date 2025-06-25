import pymsteams
import httpx
import json
from typing import Dict, Any, Optional
from core.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

class TeamsBot:
    """Microsoft Teams bot integration for Flash AI"""
    
    def __init__(self):
        self.webhook_url = settings.TEAMS_WEBHOOK_URL
        self.bot_name = settings.TEAMS_BOT_NAME
        self.timeout = settings.WEBHOOK_TIMEOUT
        
    def is_configured(self) -> bool:
        """Check if Teams integration is properly configured"""
        return bool(self.webhook_url)
    
    async def send_message(
        self,
        title: str,
        message: str,
        color: str = "7ed321",  # Flash AI green
        facts: Optional[Dict[str, str]] = None
    ) -> bool:
        """Send a message to Teams channel"""
        if not self.is_configured():
            logger.warning("Teams webhook not configured")
            return False
            
        try:
            # Create Teams message card
            card = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": title,
                "themeColor": color,
                "sections": [
                    {
                        "activityTitle": f"🐄 {title}",
                        "activitySubtitle": f"From {self.bot_name}",
                        "text": message,
                        "markdown": True
                    }
                ]
            }
            
            # Add facts if provided
            if facts:
                card["sections"][0]["facts"] = [
                    {"name": key, "value": value} 
                    for key, value in facts.items()
                ]
            
            # Send async HTTP request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Teams message sent successfully: {title}")
                    return True
                else:
                    logger.error(f"Teams webhook failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Teams message: {e}")
            return False
    
    async def send_flash_notification(
        self,
        event_type: str,
        details: Dict[str, Any]
    ) -> bool:
        """Send Flash AI specific notification"""
        
        # Event-specific formatting
        if event_type == "question_answered":
            title = "🤖 Question Answered"
            message = f"**Question:** {details.get('question', 'N/A')}\n\n**Answer:** {details.get('answer', 'N/A')}"
            facts = {
                "User": details.get('user_id', 'Unknown'),
                "Confidence": f"{details.get('confidence', 0):.2%}",
                "Response Time": f"{details.get('response_time', 0):.2f}s"
            }
            
        elif event_type == "document_indexed":
            title = "📚 Document Indexed"
            message = f"Successfully indexed: **{details.get('document_name', 'Unknown Document')}**"
            facts = {
                "Source": details.get('source_type', 'Unknown'),
                "Chunks": str(details.get('chunk_count', 0)),
                "Vector Dimensions": str(details.get('vector_dimensions', 0))
            }
            
        elif event_type == "integration_error":
            title = "⚠️ Integration Error"
            message = f"**Error:** {details.get('error_message', 'Unknown error')}\n\n**Service:** {details.get('service', 'Unknown')}"
            facts = {
                "Timestamp": details.get('timestamp', 'N/A'),
                "Error Code": details.get('error_code', 'N/A')
            }
            color = "ff6b6b"  # Red for errors
            
        elif event_type == "system_health":
            title = "💚 System Health Update"
            message = f"**Status:** {details.get('status', 'Unknown')}\n\n**Services:** {details.get('services_count', 0)} active"
            facts = {
                "Uptime": details.get('uptime', 'N/A'),
                "Active Users": str(details.get('active_users', 0)),
                "Total Conversations": str(details.get('total_conversations', 0))
            }
            color = "7ed321"  # Green for health
            
        else:
            title = f"🔔 {event_type.replace('_', ' ').title()}"
            message = json.dumps(details, indent=2)
            facts = None
            
        return await self.send_message(
            title=title,
            message=message,
            color=color if 'color' in locals() else "7ed321",
            facts=facts
        )
    
    async def send_ai_response(
        self,
        question: str,
        answer: str,
        user_id: str,
        confidence: float = 0.0,
        sources: Optional[list] = None
    ) -> bool:
        """Send AI response to Teams channel"""
        facts = {
            "User": user_id,
            "Confidence": f"{confidence:.2%}",
            "Sources": str(len(sources)) if sources else "0"
        }
        
        if sources:
            sources_text = "\n".join([f"• {source}" for source in sources[:3]])
            if len(sources) > 3:
                sources_text += f"\n• ... and {len(sources) - 3} more"
            message = f"**Q:** {question}\n\n**A:** {answer}\n\n**Sources:**\n{sources_text}"
        else:
            message = f"**Q:** {question}\n\n**A:** {answer}"
            
        return await self.send_message(
            title="Flash AI Response",
            message=message,
            facts=facts
        )
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Teams webhook connection"""
        if not self.is_configured():
            return {
                "status": "not_configured",
                "message": "Teams webhook URL not provided"
            }
        
        try:
            success = await self.send_message(
                title="🧪 Connection Test",
                message="Flash AI Teams bot is working correctly!",
                facts={"Test Time": "Now", "Status": "✅ Success"}
            )
            
            return {
                "status": "success" if success else "failed",
                "message": "Teams connection test completed",
                "webhook_configured": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Teams connection test failed: {str(e)}",
                "webhook_configured": True
            } 