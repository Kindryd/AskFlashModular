from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from core.config import settings
from core.database import init_db
from api.routes import router

# Create FastAPI app
app = FastAPI(
    title="Flash AI Conversation Service",
    description="🐄 Persistent conversation management and chat history",
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
app.include_router(router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "conversation",
        "version": "2.0.0",
        "message": "Conversation service ready for chat history management"
    }

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_db()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    ) 