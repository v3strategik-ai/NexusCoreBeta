from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime

from models import (
    Workflow, WorkflowCreate, WorkflowStatus, WorkflowStep
)
from database import get_workflows_collection

router = APIRouter(prefix="/workflows", tags=["workflows"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Workflow])
async def get_workflows(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[WorkflowStatus] = None,
    agent_id: Optional[str] = None
):
    """Get automation workflows"""
    try:
        collection = await get_workflows_collection()
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if agent_id:
            filter_dict["agent_id"] = agent_id
        
        cursor = collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
        workflows_data = await cursor.to_list(limit)
        
        # Fix None updated_at values
        for workflow in workflows_data:
            if workflow.get('updated_at') is None:
                workflow['updated_at'] = workflow.get('created_at', datetime.utcnow())
        
        return [Workflow(**workflow) for workflow in workflows_data]
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflows")

@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: str):
    """Get a specific workflow"""
    try:
        collection = await get_workflows_collection()
        workflow_data = await collection.find_one({"id": workflow_id})
        
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return Workflow(**workflow_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow")

@router.post("/", response_model=Workflow)
async def create_workflow(workflow_data: WorkflowCreate):
    """Create a new automation workflow"""
    try:
        # Create workflow object
        workflow = Workflow(
            **workflow_data.dict(),
            status=WorkflowStatus.ACTIVE,
            last_run=None,
            run_count=0,
            success_rate=0.0
        )
        
        # Insert into database
        collection = await get_workflows_collection()
        await collection.insert_one(workflow.dict())
        
        logger.info(f"Created new workflow: {workflow.name} ({workflow.id})")
        return workflow
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")

@router.put("/{workflow_id}", response_model=Workflow)
async def update_workflow(workflow_id: str, workflow_update: dict):
    """Update a workflow"""
    try:
        collection = await get_workflows_collection()
        
        # Check if workflow exists
        existing_workflow = await collection.find_one({"id": workflow_id})
        if not existing_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update workflow
        workflow_update["updated_at"] = datetime.utcnow()
        await collection.update_one(
            {"id": workflow_id},
            {"$set": workflow_update}
        )
        
        # Get updated workflow
        updated_workflow_data = await collection.find_one({"id": workflow_id})
        return Workflow(**updated_workflow_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workflow")

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        collection = await get_workflows_collection()
        
        # Check if workflow exists
        workflow_data = await collection.find_one({"id": workflow_id})
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Delete workflow
        await collection.delete_one({"id": workflow_id})
        
        return {"message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workflow")

@router.post("/{workflow_id}/start")
async def start_workflow(workflow_id: str):
    """Start/resume a workflow"""
    try:
        collection = await get_workflows_collection()
        
        # Check if workflow exists
        workflow_data = await collection.find_one({"id": workflow_id})
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update status to active
        await collection.update_one(
            {"id": workflow_id},
            {
                "$set": {
                    "status": WorkflowStatus.ACTIVE,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # In a real implementation, you would trigger the workflow execution here
        await execute_workflow(workflow_id, workflow_data)
        
        return {"message": "Workflow started successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start workflow")

@router.post("/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """Pause a workflow"""
    try:
        collection = await get_workflows_collection()
        
        # Check if workflow exists
        workflow_data = await collection.find_one({"id": workflow_id})
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update status to paused
        await collection.update_one(
            {"id": workflow_id},
            {
                "$set": {
                    "status": WorkflowStatus.PAUSED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Workflow paused successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to pause workflow")

@router.post("/{workflow_id}/stop")
async def stop_workflow(workflow_id: str):
    """Stop a workflow"""
    try:
        collection = await get_workflows_collection()
        
        # Check if workflow exists
        workflow_data = await collection.find_one({"id": workflow_id})
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update status to stopped
        await collection.update_one(
            {"id": workflow_id},
            {
                "$set": {
                    "status": WorkflowStatus.STOPPED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Workflow stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop workflow")

@router.get("/{workflow_id}/history")
async def get_workflow_history(workflow_id: str, limit: int = Query(50, ge=1, le=200)):
    """Get workflow execution history"""
    try:
        # In a real implementation, you would have a separate collection for workflow runs
        # For now, return mock data
        return {
            "workflow_id": workflow_id,
            "total_runs": 23,
            "successful_runs": 22,
            "failed_runs": 1,
            "average_duration": "2.3 minutes",
            "last_execution": datetime.utcnow().isoformat(),
            "recent_runs": [
                {
                    "run_id": "run_001",
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "status": "success",
                    "duration": "2.1 minutes"
                },
                {
                    "run_id": "run_002",
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "status": "success",
                    "duration": "2.5 minutes"
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow history {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow history")

@router.get("/stats/summary")
async def get_workflow_stats():
    """Get workflow automation statistics"""
    try:
        collection = await get_workflows_collection()
        
        # Total workflows
        total_workflows = await collection.count_documents({})
        
        # Workflows by status
        active_count = await collection.count_documents({"status": WorkflowStatus.ACTIVE})
        paused_count = await collection.count_documents({"status": WorkflowStatus.PAUSED})
        stopped_count = await collection.count_documents({"status": WorkflowStatus.STOPPED})
        
        # Calculate total runs and average success rate
        pipeline = [
            {"$group": {
                "_id": None,
                "total_runs": {"$sum": "$run_count"},
                "avg_success_rate": {"$avg": "$success_rate"}
            }}
        ]
        
        stats_result = await collection.aggregate(pipeline).to_list(1)
        total_runs = stats_result[0]["total_runs"] if stats_result else 0
        avg_success_rate = stats_result[0]["avg_success_rate"] if stats_result else 0
        
        return {
            "total_workflows": total_workflows,
            "active_workflows": active_count,
            "paused_workflows": paused_count,
            "stopped_workflows": stopped_count,
            "total_executions": total_runs,
            "average_success_rate": round(avg_success_rate, 2),
            "automation_time_saved": "147 hours",  # Mock value
            "cost_savings": "$12,450"  # Mock value
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow statistics")

async def execute_workflow(workflow_id: str, workflow_data: dict):
    """Execute a workflow (mock implementation)"""
    try:
        collection = await get_workflows_collection()
        
        # Update last run time and increment run count
        await collection.update_one(
            {"id": workflow_id},
            {
                "$set": {
                    "last_run": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                "$inc": {"run_count": 1}
            }
        )
        
        # In a real implementation, you would:
        # 1. Process each workflow step
        # 2. Execute the configured actions
        # 3. Handle errors and retries
        # 4. Log execution results
        # 5. Update success rate
        
        logger.info(f"Executed workflow: {workflow_id}")
        
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        # Update workflow status to error
        await collection.update_one(
            {"id": workflow_id},
            {"$set": {"status": WorkflowStatus.ERROR}}
        )