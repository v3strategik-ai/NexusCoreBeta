from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from ..models import (
    Agent, AgentCreate, AgentUpdate, AgentListResponse,
    AgentActivity, AutonomyLevel, AgentStatus
)
from ..database import get_agents_collection, get_activities_collection

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=AgentListResponse)
async def get_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AgentStatus] = None,
    type: Optional[str] = None
):
    """Get list of all digital employees/agents"""
    try:
        collection = await get_agents_collection()
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if type:
            filter_dict["type"] = type
        
        # Get total count
        total = await collection.count_documents(filter_dict)
        
        # Get agents with pagination
        cursor = collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
        agents_data = await cursor.to_list(limit)
        
        agents = [Agent(**agent) for agent in agents_data]
        
        return AgentListResponse(agents=agents, total=total)
        
    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agents")

@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get a specific digital employee/agent by ID"""
    try:
        collection = await get_agents_collection()
        agent_data = await collection.find_one({"id": agent_id})
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return Agent(**agent_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent")

@router.post("/", response_model=Agent)
async def create_agent(agent_data: AgentCreate):
    """Create a new digital employee/agent"""
    try:
        collection = await get_agents_collection()
        
        # Create agent object
        agent = Agent(
            **agent_data.dict(),
            status=AgentStatus.TRAINING,
            efficiency=0.0,
            tasks_completed=0,
            learning_progress=0.0,
            knowledge_base=[],
            metrics={}
        )
        
        # Insert into database
        await collection.insert_one(agent.dict())
        
        # Log activity
        await log_agent_activity(
            agent.id,
            agent.name,
            "agent_created",
            f"New digital employee '{agent.name}' created with {agent.autonomy_level} autonomy level",
            agent.autonomy_level
        )
        
        logger.info(f"Created new agent: {agent.name} ({agent.id})")
        return agent
        
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")

@router.put("/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, agent_update: AgentUpdate):
    """Update a digital employee/agent"""
    try:
        collection = await get_agents_collection()
        
        # Get existing agent
        existing_agent = await collection.find_one({"id": agent_id})
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Prepare update data
        update_data = {k: v for k, v in agent_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        # Update agent
        await collection.update_one(
            {"id": agent_id},
            {"$set": update_data}
        )
        
        # Get updated agent
        updated_agent_data = await collection.find_one({"id": agent_id})
        updated_agent = Agent(**updated_agent_data)
        
        # Log activity
        await log_agent_activity(
            agent_id,
            updated_agent.name,
            "agent_updated",
            f"Digital employee configuration updated",
            updated_agent.autonomy_level
        )
        
        logger.info(f"Updated agent: {agent_id}")
        return updated_agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent")

@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete a digital employee/agent"""
    try:
        collection = await get_agents_collection()
        
        # Check if agent exists
        agent_data = await collection.find_one({"id": agent_id})
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Delete agent
        await collection.delete_one({"id": agent_id})
        
        # Log activity
        await log_agent_activity(
            agent_id,
            agent_data.get("name", "Unknown"),
            "agent_deleted",
            f"Digital employee '{agent_data.get('name')}' was deleted",
            agent_data.get("autonomy_level", "Unknown")
        )
        
        logger.info(f"Deleted agent: {agent_id}")
        return {"message": "Agent deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")

@router.post("/{agent_id}/activate")
async def activate_agent(agent_id: str):
    """Activate a digital employee/agent"""
    try:
        collection = await get_agents_collection()
        
        # Check if agent exists
        agent_data = await collection.find_one({"id": agent_id})
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update status to active
        await collection.update_one(
            {"id": agent_id},
            {
                "$set": {
                    "status": AgentStatus.ACTIVE,
                    "last_active": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log activity
        await log_agent_activity(
            agent_id,
            agent_data.get("name", "Unknown"),
            "agent_activated",
            f"Digital employee activated and ready for autonomous operation",
            agent_data.get("autonomy_level", "Unknown")
        )
        
        return {"message": "Agent activated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate agent")

@router.post("/{agent_id}/deactivate")
async def deactivate_agent(agent_id: str):
    """Deactivate a digital employee/agent"""
    try:
        collection = await get_agents_collection()
        
        # Check if agent exists
        agent_data = await collection.find_one({"id": agent_id})
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update status to idle
        await collection.update_one(
            {"id": agent_id},
            {
                "$set": {
                    "status": AgentStatus.IDLE,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log activity
        await log_agent_activity(
            agent_id,
            agent_data.get("name", "Unknown"),
            "agent_deactivated",
            f"Digital employee deactivated and set to idle mode",
            agent_data.get("autonomy_level", "Unknown")
        )
        
        return {"message": "Agent deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to deactivate agent")

@router.get("/{agent_id}/activities")
async def get_agent_activities(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get recent activities for a specific agent"""
    try:
        collection = await get_activities_collection()
        
        cursor = collection.find({"agent_id": agent_id}).sort("timestamp", -1).limit(limit)
        activities_data = await cursor.to_list(limit)
        
        activities = [AgentActivity(**activity) for activity in activities_data]
        
        return {"activities": activities}
        
    except Exception as e:
        logger.error(f"Error getting activities for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent activities")

async def log_agent_activity(
    agent_id: str,
    agent_name: str,
    activity_type: str,
    description: str,
    autonomy_level: str,
    metadata: dict = None
):
    """Helper function to log agent activities"""
    try:
        collection = await get_activities_collection()
        
        activity = AgentActivity(
            agent_id=agent_id,
            agent_name=agent_name,
            activity_type=activity_type,
            description=description,
            autonomy_level=autonomy_level,
            metadata=metadata or {}
        )
        
        await collection.insert_one(activity.dict())
        
    except Exception as e:
        logger.error(f"Error logging agent activity: {e}")