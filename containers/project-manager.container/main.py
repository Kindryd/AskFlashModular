from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from core.config import settings
from core.database import init_db
from api.routes import router

# Create FastAPI app
app = FastAPI(
    title="Flash AI Project Manager Service",
    description="🐄 Integration management, Teams bot, and project coordination",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from services.integration_manager import IntegrationManager
    from services.teams_bot import TeamsBot
    
    # Check service readiness
    integration_manager = IntegrationManager()
    teams_bot = TeamsBot()
    
    return {
        "status": "healthy",
        "service": "project-manager",
        "version": "2.0.0",
        "integrations": {
            "jira": "configured" if settings.JIRA_URL else "not_configured",
            "teams": "configured" if settings.TEAMS_WEBHOOK_URL else "not_configured"
        },
        "message": "Project manager ready for integration coordination"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    await init_db()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    ) 