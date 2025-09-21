from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List
import uuid
from datetime import datetime

# Import database functions
from database import connect_to_mongo, close_mongo_connection, get_database

# Import all route modules
from routes import agents, crm, dashboard, knowledge, documents, workflows, ai_chat, email, realtime, workflows_advanced

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app
app = FastAPI(
    title="Nexus Core API",
    description="Autonomous Digital Employees Powerhouse - Complete AI Business Automation Platform",
    version="1.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Legacy models for backward compatibility
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

# Legacy routes for backward compatibility
@api_router.get("/")
async def root():
    return {
        "message": "Welcome to Nexus Core API",
        "version": "1.0.0",
        "description": "Autonomous Digital Employees Powerhouse",
        "features": [
            "Digital Employee Management",
            "CRM Intelligence",
            "Knowledge Hub",
            "Document Generation",
            "Automation Workflows",
            "Neural Configuration"
        ]
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    """Legacy status check endpoint for backward compatibility"""
    db = await get_database()
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    """Legacy status check endpoint for backward compatibility"""
    db = await get_database()
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db = await get_database()
        # Test database connection
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

# Include all route modules
api_router.include_router(agents.router)
api_router.include_router(crm.router)
api_router.include_router(dashboard.router)
api_router.include_router(knowledge.router)
api_router.include_router(documents.router)
api_router.include_router(workflows.router)
api_router.include_router(ai_chat.router)
api_router.include_router(email.router)
api_router.include_router(realtime.router)
api_router.include_router(workflows_advanced.router)

# Include the main API router
app.include_router(api_router)

# Static file serving for uploaded files
upload_dir = Path("/app/uploads")
upload_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        await connect_to_mongo()
        logger.info("Nexus Core API started successfully")
        logger.info("Available endpoints:")
        logger.info("  - Digital Employees: /api/agents")
        logger.info("  - CRM Intelligence: /api/crm")
        logger.info("  - Dashboard: /api/dashboard")
        logger.info("  - Knowledge Hub: /api/knowledge")
        logger.info("  - Documents: /api/documents")
        logger.info("  - Workflows: /api/workflows")
    except Exception as e:
        logger.error(f"Failed to start Nexus Core API: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        await close_mongo_connection()
        logger.info("Nexus Core API shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Root endpoint
@app.get("/")
async def root_endpoint():
    """Root endpoint with API information"""
    return {
        "name": "Nexus Core API",
        "version": "1.0.0",
        "description": "Autonomous Digital Employees Powerhouse - Complete AI Business Automation Platform",
        "api_docs": "/docs",
        "health": "/api/health",
        "features": {
            "digital_employees": "/api/agents",
            "crm_intelligence": "/api/crm",
            "dashboard": "/api/dashboard",
            "knowledge_hub": "/api/knowledge",
            "document_generation": "/api/documents",
            "automation_workflows": "/api/workflows"
        },
        "status": "operational",
        "quantum_level": True
    }
