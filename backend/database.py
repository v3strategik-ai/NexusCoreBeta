from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

# Global database instance
db_instance = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'nexus_core')
        
        db_instance.client = AsyncIOMotorClient(mongo_url)
        db_instance.database = db_instance.client[db_name]
        
        # Test the connection
        await db_instance.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB at {mongo_url}")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if db_instance.client:
        db_instance.client.close()
        logger.info("Disconnected from MongoDB")

async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if not db_instance.database:
        await connect_to_mongo()
    return db_instance.database

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        db = db_instance.database
        
        # Agents collection indexes
        await db.agents.create_index("name")
        await db.agents.create_index("type")
        await db.agents.create_index("status")
        await db.agents.create_index([("created_at", -1)])
        
        # Leads collection indexes
        await db.leads.create_index("email", unique=True)
        await db.leads.create_index("status")
        await db.leads.create_index("assigned_agent_id")
        await db.leads.create_index([("created_at", -1)])
        await db.leads.create_index([("score", -1)])
        
        # Knowledge base indexes
        await db.knowledge_base.create_index("category")
        await db.knowledge_base.create_index("tags")
        await db.knowledge_base.create_index([("created_at", -1)])
        
        # Documents indexes
        await db.documents.create_index("type")
        await db.documents.create_index("client_name")
        await db.documents.create_index([("created_at", -1)])
        
        # Workflows indexes
        await db.workflows.create_index("status")
        await db.workflows.create_index("agent_id")
        
        # Activities indexes
        await db.activities.create_index("agent_id")
        await db.activities.create_index([("timestamp", -1)])
        
        # Users indexes
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True)
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

# Collection helpers
async def get_agents_collection():
    db = await get_database()
    return db.agents

async def get_leads_collection():
    db = await get_database()
    return db.leads

async def get_knowledge_collection():
    db = await get_database()
    return db.knowledge_base

async def get_documents_collection():
    db = await get_database()
    return db.documents

async def get_workflows_collection():
    db = await get_database()
    return db.workflows

async def get_activities_collection():
    db = await get_database()
    return db.activities

async def get_users_collection():
    db = await get_database()
    return db.users

async def get_system_metrics_collection():
    db = await get_database()
    return db.system_metrics