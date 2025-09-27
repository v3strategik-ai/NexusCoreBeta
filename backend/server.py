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
from routes import agents, crm, dashboard, knowledge, documents, workflows, ai_chat, email, realtime, workflows_advanced, analytics, ab_testing, lead_scoring, ai_content, sentiment, workflow_engine, workflow_execution, nl_workflows, tenants, users_management, audit, advanced_voice, data_export, performance
from websocket import socketio_app, start_background_tasks

# Import Phase 7 performance optimization components
from middleware import RateLimitMiddleware
from rate_limiter import setup_rate_limiter, cleanup_rate_limiter
from redis_cache import setup_redis_cache, cleanup_redis_cache
from performance_optimizer import performance_optimizer

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
api_router.include_router(analytics.router)
api_router.include_router(ab_testing.router)
api_router.include_router(lead_scoring.router)
api_router.include_router(ai_content.router)
api_router.include_router(sentiment.router)
api_router.include_router(workflow_engine.router)
api_router.include_router(workflow_execution.router)
api_router.include_router(nl_workflows.router)

# Phase 6C: Enterprise Architecture Routes
api_router.include_router(tenants.router)
api_router.include_router(users_management.router)
api_router.include_router(audit.router)

# Phase 6D: Advanced Intelligence & Voice Routes
api_router.include_router(advanced_voice.router)
api_router.include_router(data_export.router)

# Phase 7: Platform Optimization & Performance Routes
api_router.include_router(performance.router)

# Include the main API router
app.include_router(api_router)

# Mount WebSocket app for real-time connections
app.mount("/socket.io", socketio_app)

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

# Phase 7: Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware, exclude_paths=[
    "/docs", "/redoc", "/openapi.json", "/api/health", "/api/performance/health"
])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting Nexus Core API...")
    
    # Connect to MongoDB
    await connect_to_mongo()
    
    # Phase 7: Initialize performance optimization systems
    logger.info("Initializing performance optimization systems...")
    
    # Setup Redis cache
    cache_success = await setup_redis_cache()
    logger.info(f"Redis cache: {'enabled' if cache_success else 'fallback mode'}")
    
    # Setup rate limiter
    await setup_rate_limiter()
    logger.info("Rate limiter: enabled")
    
    # Run initial database optimization
    try:
        optimization_results = await performance_optimizer.optimize_database_indexes()
        logger.info(f"Database optimization: {len(optimization_results)} collections optimized")
    except Exception as e:
        logger.warning(f"Database optimization skipped: {e}")
    
    # Start background tasks for real-time updates
    start_background_tasks()
    
    logger.info("Nexus Core API started successfully")
    logger.info("Available endpoints:")
    logger.info("  - Digital Employees: /api/agents")
    logger.info("  - CRM Intelligence: /api/crm")
    logger.info("  - Dashboard: /api/dashboard")
    logger.info("  - Knowledge Hub: /api/knowledge")
    logger.info("  - Documents: /api/documents")
    logger.info("  - Workflows: /api/workflows")
    logger.info("  - Email Automation: /api/email")
    logger.info("  - Real-Time: /api/realtime")
    logger.info("  - Advanced Workflows: /api/workflows/advanced")
    logger.info("  - Performance Optimization: /api/performance")
    logger.info("  - WebSocket: /socket.io")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        # Phase 7: Cleanup performance optimization systems
        logger.info("Shutting down performance optimization systems...")
        await cleanup_rate_limiter()
        await cleanup_redis_cache()
        logger.info("Performance systems shut down successfully")
        
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
