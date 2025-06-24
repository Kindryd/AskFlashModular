from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
import httpx
import logging
from typing import Dict, Any
import json

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Service routing map based on legacy endpoint organization
SERVICE_ROUTES = {
    # Conversation Container routes
    "/chat": "conversation",
    "/conversations": "conversation",
    
    # AI Orchestrator Container routes  
    "/semantic": "ai-orchestrator",  # Quality enhancement endpoints
    
    # Embedding Container routes
    "/docs": "embedding",  # Documentation search
    "/embeddings": "embedding",  # Vector operations
    "/wiki-index": "embedding",  # Wiki indexing
    
    # Project Manager Container routes
    "/teams": "project-manager",  # Teams bot
    "/integrations": "project-manager",  # Integration management
    
    # Gateway-handled routes (no proxying)
    "/auth": "gateway",  # Authentication (gateway handles)
    "/users": "gateway",  # User management (gateway handles)  
    "/rulesets": "gateway",  # Ruleset management (gateway handles)
    "/monitoring": "gateway",  # Monitoring (gateway aggregates)
    "/search": "gateway",  # Search coordination (gateway coordinates)
    
    # Analytics Container routes
    "/analytics": "analytics",  # Analytics endpoints
    
    # Adaptive Engine Container routes  
    "/adaptive": "adaptive-engine",  # Learning endpoints
    
    # Local LLM Container routes
    "/llm": "local-llm",  # Local LLM endpoints
}

# Service URL mapping
SERVICE_URLS = {
    "conversation": settings.CONVERSATION_SERVICE_URL,
    "ai-orchestrator": settings.AI_ORCHESTRATOR_SERVICE_URL,
    "embedding": settings.EMBEDDING_SERVICE_URL,
    "project-manager": settings.PROJECT_MANAGER_SERVICE_URL,
    "analytics": settings.ANALYTICS_SERVICE_URL,
    "adaptive-engine": settings.ADAPTIVE_ENGINE_SERVICE_URL,
    "local-llm": settings.LOCAL_LLM_SERVICE_URL,
}

async def proxy_request(
    request: Request,
    target_service: str,
    path: str,
    **kwargs
) -> Response:
    """Proxy request to target microservice"""
    
    if target_service not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Service {target_service} not found")
    
    target_url = f"{SERVICE_URLS[target_service]}{path}"
    
    # Prepare request data
    headers = dict(request.headers)
    # Remove host header to avoid conflicts
    headers.pop('host', None)
    
    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    try:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            # Make the proxied request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=request.query_params,
                content=body,
                **kwargs
            )
            
            # Handle streaming responses
            if response.headers.get("content-type", "").startswith("text/event-stream"):
                return StreamingResponse(
                    response.aiter_text(),
                    media_type="text/event-stream",
                    headers=dict(response.headers)
                )
            
            # Handle regular responses
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
    except httpx.TimeoutException:
        logger.error(f"Timeout proxying to {target_service}: {target_url}")
        raise HTTPException(status_code=504, detail=f"Service {target_service} timeout")
    except httpx.ConnectError:
        logger.error(f"Connection error proxying to {target_service}: {target_url}")
        raise HTTPException(status_code=502, detail=f"Service {target_service} unavailable")
    except Exception as e:
        logger.error(f"Error proxying to {target_service}: {e}")
        raise HTTPException(status_code=500, detail="Internal gateway error")

@router.api_route(
    "/chat/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_chat(request: Request, path: str):
    """Proxy chat requests to conversation container"""
    return await proxy_request(request, "conversation", f"/api/v1/chat/{path}")

@router.api_route(
    "/conversations/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_conversations(request: Request, path: str):
    """Proxy conversation requests to conversation container"""
    return await proxy_request(request, "conversation", f"/api/v1/conversations/{path}")

@router.api_route(
    "/docs/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_docs(request: Request, path: str):
    """Proxy documentation requests to embedding container"""
    return await proxy_request(request, "embedding", f"/api/v1/docs/{path}")

@router.api_route(
    "/embeddings/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_embeddings(request: Request, path: str):
    """Proxy embedding requests to embedding container"""
    return await proxy_request(request, "embedding", f"/api/v1/embeddings/{path}")

@router.api_route(
    "/wiki-index/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_wiki_index(request: Request, path: str):
    """Proxy wiki index requests to embedding container"""
    return await proxy_request(request, "embedding", f"/api/v1/wiki-index/{path}")

@router.api_route(
    "/teams/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_teams(request: Request, path: str):
    """Proxy Teams bot requests to project manager container"""
    return await proxy_request(request, "project-manager", f"/api/v1/teams/{path}")

@router.api_route(
    "/integrations/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_integrations(request: Request, path: str):
    """Proxy integration requests to project manager container"""
    return await proxy_request(request, "project-manager", f"/api/v1/integrations/{path}")

@router.api_route(
    "/semantic/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_semantic(request: Request, path: str):
    """Proxy semantic enhancement requests to AI orchestrator container"""
    return await proxy_request(request, "ai-orchestrator", f"/api/v1/semantic/{path}")

# Gateway-handled endpoints (implemented directly in gateway)

@router.get("/search/status")
async def search_status():
    """Search coordination status - gateway aggregates from multiple services"""
    return {
        "status": "operational",
        "services": {
            "embedding": "vector search",
            "ai-orchestrator": "quality enhancement",
            "conversation": "search integration"
        },
        "description": "🔍 Flash AI Search - Coordinated across microservices"
    }

@router.get("/monitoring/gateway")
async def gateway_monitoring():
    """Gateway-specific monitoring endpoint"""
    return {
        "service": "Flash AI Gateway",
        "version": settings.GATEWAY_VERSION,
        "status": "operational",
        "routes_configured": len(SERVICE_ROUTES),
        "services_available": len(SERVICE_URLS)
    }

@router.get("/auth/status")
async def auth_status():
    """Authentication status - placeholder for gateway auth"""
    return {
        "status": "operational",
        "description": "Authentication handled by gateway",
        "note": "Implement JWT/OAuth here for production"
    }

@router.get("/users/status") 
async def users_status():
    """User management status - placeholder for gateway user management"""
    return {
        "status": "operational",
        "description": "User management handled by gateway",
        "note": "Implement user CRUD operations here"
    }

@router.get("/rulesets/status")
async def rulesets_status():
    """Ruleset management status - placeholder for gateway ruleset management"""
    return {
        "status": "operational", 
        "description": "Ruleset management handled by gateway",
        "note": "Implement ruleset CRUD operations here"
    } 