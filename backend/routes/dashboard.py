from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
import logging

from ..models import SystemMetrics, AgentActivity, SystemDashboard
from ..database import (
    get_agents_collection, get_leads_collection, get_activities_collection,
    get_system_metrics_collection, get_documents_collection
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=SystemDashboard)
async def get_dashboard():
    """Get complete dashboard overview"""
    try:
        # Get current system metrics
        metrics = await get_current_metrics()
        
        # Get recent activities
        activities = await get_recent_activities()
        
        # Get agent summary
        agent_summary = await get_agent_summary()
        
        # Get revenue summary
        revenue_summary = await get_revenue_summary()
        
        return SystemDashboard(
            metrics=metrics,
            recent_activities=activities,
            agent_summary=agent_summary,
            revenue_summary=revenue_summary
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get current system metrics"""
    try:
        return await get_current_metrics()
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system metrics")

@router.get("/activities")
async def get_dashboard_activities(limit: int = 10):
    """Get recent system activities for dashboard"""
    try:
        activities = await get_recent_activities(limit)
        return {"activities": activities}
    except Exception as e:
        logger.error(f"Error getting dashboard activities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activities")

async def get_current_metrics() -> SystemMetrics:
    """Calculate current system metrics"""
    try:
        agents_collection = await get_agents_collection()
        leads_collection = await get_leads_collection()
        documents_collection = await get_documents_collection()
        
        # Count active agents
        active_agents = await agents_collection.count_documents({"status": "active"})
        
        # Calculate total tasks completed (sum from all agents)
        pipeline = [
            {"$group": {"_id": None, "total_tasks": {"$sum": "$tasks_completed"}}}
        ]
        tasks_result = await agents_collection.aggregate(pipeline).to_list(1)
        total_tasks = tasks_result[0]["total_tasks"] if tasks_result else 0
        
        # Calculate total revenue from leads
        revenue_pipeline = [
            {"$match": {"status": "converted"}},
            {"$group": {"_id": None, "total_revenue": {"$sum": "$value"}}}
        ]
        revenue_result = await leads_collection.aggregate(revenue_pipeline).to_list(1)
        total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
        
        # Calculate system efficiency (average of all agent efficiencies)
        efficiency_pipeline = [
            {"$group": {"_id": None, "avg_efficiency": {"$avg": "$efficiency"}}}
        ]
        efficiency_result = await agents_collection.aggregate(efficiency_pipeline).to_list(1)
        system_efficiency = efficiency_result[0]["avg_efficiency"] if efficiency_result else 0
        
        # Mock some advanced metrics (in real implementation, these would be calculated)
        neural_processing_power = min(87 + (active_agents * 2), 100)
        knowledge_utilization = min(94 + (total_tasks / 100), 100)
        autonomous_decision_rate = min(98 - (active_agents * 0.5), 100)
        learning_acceleration = min(76 + (total_tasks / 200), 100)
        
        return SystemMetrics(
            active_agents=active_agents,
            total_tasks_completed=total_tasks,
            total_revenue_generated=total_revenue,
            system_efficiency=round(system_efficiency, 1),
            neural_processing_power=round(neural_processing_power, 1),
            knowledge_base_utilization=round(knowledge_utilization, 1),
            autonomous_decision_rate=round(autonomous_decision_rate, 1),
            learning_acceleration=round(learning_acceleration, 1)
        )
        
    except Exception as e:
        logger.error(f"Error calculating system metrics: {e}")
        raise

async def get_recent_activities(limit: int = 10) -> List[AgentActivity]:
    """Get recent agent activities"""
    try:
        collection = await get_activities_collection()
        
        cursor = collection.find({}).sort("timestamp", -1).limit(limit)
        activities_data = await cursor.to_list(limit)
        
        return [AgentActivity(**activity) for activity in activities_data]
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        return []

async def get_agent_summary() -> dict:
    """Get agent performance summary"""
    try:
        collection = await get_agents_collection()
        
        # Count agents by status
        active_count = await collection.count_documents({"status": "active"})
        training_count = await collection.count_documents({"status": "training"})
        idle_count = await collection.count_documents({"status": "idle"})
        
        # Get top performing agents
        cursor = collection.find({}).sort("efficiency", -1).limit(3)
        top_agents = await cursor.to_list(3)
        
        # Count quantum-level agents
        quantum_count = await collection.count_documents({"autonomy_level": "Quantum"})
        
        return {
            "active_agents": active_count,
            "training_agents": training_count,
            "idle_agents": idle_count,
            "quantum_agents": quantum_count,
            "top_performers": [
                {
                    "name": agent.get("name", "Unknown"),
                    "efficiency": agent.get("efficiency", 0),
                    "type": agent.get("type", "Unknown")
                } for agent in top_agents
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting agent summary: {e}")
        return {}

async def get_revenue_summary() -> dict:
    """Get revenue and business performance summary"""
    try:
        leads_collection = await get_leads_collection()
        
        # Get current month revenue
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        current_month_pipeline = [
            {
                "$match": {
                    "status": "converted",
                    "updated_at": {"$gte": current_month_start}
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]
        
        current_month_result = await leads_collection.aggregate(current_month_pipeline).to_list(1)
        current_month_revenue = current_month_result[0]["total"] if current_month_result else 0
        
        # Get total pipeline value
        pipeline_result = await leads_collection.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]).to_list(1)
        total_pipeline = pipeline_result[0]["total"] if pipeline_result else 0
        
        # Calculate conversion metrics
        total_leads = await leads_collection.count_documents({})
        converted_leads = await leads_collection.count_documents({"status": "converted"})
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            "current_month_revenue": current_month_revenue,
            "total_pipeline_value": total_pipeline,
            "conversion_rate": round(conversion_rate, 2),
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "ai_contribution_percentage": 67  # Mock percentage of AI-driven revenue
        }
        
    except Exception as e:
        logger.error(f"Error getting revenue summary: {e}")
        return {}

@router.post("/metrics/update")
async def update_system_metrics():
    """Manually trigger system metrics update"""
    try:
        metrics = await get_current_metrics()
        
        # Store metrics in database for historical tracking
        collection = await get_system_metrics_collection()
        await collection.insert_one(metrics.dict())
        
        return {"message": "System metrics updated successfully", "metrics": metrics}
        
    except Exception as e:
        logger.error(f"Error updating system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to update system metrics")