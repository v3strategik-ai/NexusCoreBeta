from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from models import (
    Agent, AgentCreate, AgentUpdate, AgentListResponse,
    AgentActivity, AutonomyLevel, AgentStatus
)
from database import get_agents_collection, get_activities_collection

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
    """Update a digital employee/agent with advanced configuration processing"""
    try:
        collection = await get_agents_collection()
        
        # Get existing agent
        existing_agent = await collection.find_one({"id": agent_id})
        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Prepare update data
        update_data = {k: v for k, v in agent_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        # Advanced configuration processing
        if "configuration" in update_data:
            processed_config = await process_agent_configuration(
                agent_id, 
                update_data["configuration"], 
                existing_agent.get("configuration", {})
            )
            update_data["configuration"] = processed_config
            
            # Update agent metrics based on new configuration
            metrics_update = calculate_configuration_metrics(processed_config)
            update_data["metrics"] = {
                **existing_agent.get("metrics", {}),
                **metrics_update,
                "last_config_update": datetime.utcnow().isoformat()
            }
        
        # Update agent
        await collection.update_one(
            {"id": agent_id},
            {"$set": update_data}
        )
        
        # Get updated agent
        updated_agent_data = await collection.find_one({"id": agent_id})
        updated_agent = Agent(**updated_agent_data)
        
        # Log configuration activity
        config_summary = summarize_configuration_changes(
            existing_agent.get("configuration", {}),
            update_data.get("configuration", {})
        )
        
        await log_agent_activity(
            agent_id,
            updated_agent.name,
            "configuration_updated",
            f"Agent configuration updated: {config_summary}",
            updated_agent.autonomy_level,
            {"configuration_changes": config_summary}
        )
        
        logger.info(f"Updated agent configuration: {agent_id} - {config_summary}")
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

async def process_agent_configuration(agent_id: str, new_config: dict, existing_config: dict) -> dict:
    """Process and validate agent configuration updates"""
    try:
        # Merge configurations with validation
        processed_config = {**existing_config, **new_config}
        
        # Validate configuration structure
        if "capabilities" in processed_config:
            # Ensure capabilities is a list
            if not isinstance(processed_config["capabilities"], list):
                processed_config["capabilities"] = []
        
        if "parameters" in processed_config:
            # Ensure parameters is a dict
            if not isinstance(processed_config["parameters"], dict):
                processed_config["parameters"] = {}
        
        # Add processing timestamp
        processed_config["last_processed"] = datetime.utcnow().isoformat()
        
        logger.info(f"Processed configuration for agent {agent_id}")
        return processed_config
        
    except Exception as e:
        logger.error(f"Error processing configuration for agent {agent_id}: {e}")
        return existing_config

def calculate_configuration_metrics(config: dict) -> dict:
    """Calculate metrics based on agent configuration"""
    try:
        metrics = {}
        
        # Calculate complexity score based on configuration
        complexity_score = 0
        if "capabilities" in config:
            complexity_score += len(config["capabilities"]) * 10
        if "parameters" in config:
            complexity_score += len(config["parameters"]) * 5
        
        metrics["configuration_complexity"] = complexity_score
        metrics["capabilities_count"] = len(config.get("capabilities", []))
        metrics["parameters_count"] = len(config.get("parameters", {}))
        
        # Calculate readiness score
        readiness_score = min(100, complexity_score * 2)
        metrics["readiness_score"] = readiness_score
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating configuration metrics: {e}")
        return {}

def summarize_configuration_changes(old_config: dict, new_config: dict) -> str:
    """Generate a summary of configuration changes"""
    try:
        changes = []
        
        # Check for new capabilities
        old_capabilities = set(old_config.get("capabilities", []))
        new_capabilities = set(new_config.get("capabilities", []))
        
        added_capabilities = new_capabilities - old_capabilities
        removed_capabilities = old_capabilities - new_capabilities
        
        if added_capabilities:
            changes.append(f"Added capabilities: {', '.join(added_capabilities)}")
        if removed_capabilities:
            changes.append(f"Removed capabilities: {', '.join(removed_capabilities)}")
        
        # Check for parameter changes
        old_params = old_config.get("parameters", {})
        new_params = new_config.get("parameters", {})
        
        param_changes = []
        for key, value in new_params.items():
            if key not in old_params:
                param_changes.append(f"Added {key}")
            elif old_params[key] != value:
                param_changes.append(f"Updated {key}")
        
        for key in old_params:
            if key not in new_params:
                param_changes.append(f"Removed {key}")
        
        if param_changes:
            changes.append(f"Parameter changes: {', '.join(param_changes)}")
        
        return "; ".join(changes) if changes else "Minor configuration updates"
        
    except Exception as e:
        logger.error(f"Error summarizing configuration changes: {e}")
        return "Configuration updated"