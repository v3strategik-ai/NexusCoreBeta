from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field
from bson import ObjectId

from database import get_database
from models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])
logger = logging.getLogger(__name__)

# Pydantic Models for API
class AuditLogResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    user_email: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime

class AuditFilters(BaseModel):
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class AuditStats(BaseModel):
    total_actions: int
    successful_actions: int
    failed_actions: int
    unique_users: int
    most_common_actions: List[Dict[str, Any]]
    actions_by_hour: List[Dict[str, Any]]

# API Endpoints
@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """Get audit logs with filters"""
    try:
        db = await get_database()
        
        # Build query filters
        query = {}
        
        if tenant_id:
            query["tenant_id"] = tenant_id
        if user_id:
            query["user_id"] = user_id
        if action:
            query["action"] = {"$regex": action, "$options": "i"}
        if resource_type:
            query["resource_type"] = resource_type
        if success is not None:
            query["success"] = success
        
        # Date range filter
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date)
            query["created_at"] = date_filter
        
        # Execute query
        cursor = db.audit_logs.find(query).sort("created_at", -1).skip(skip).limit(limit)
        logs = []
        
        async for log_doc in cursor:
            log_doc["id"] = str(log_doc["_id"])
            log_doc.pop("_id", None)
            logs.append(AuditLogResponse(**log_doc))
        
        return logs
        
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")

@router.get("/stats", response_model=AuditStats)
async def get_audit_statistics(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant"),
    days: int = Query(30, description="Number of days to analyze")
):
    """Get audit statistics"""
    try:
        db = await get_database()
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Base query
        base_query = {
            "created_at": {"$gte": start_date, "$lte": end_date}
        }
        if tenant_id:
            base_query["tenant_id"] = tenant_id
        
        # Aggregation pipeline
        pipeline = [
            {"$match": base_query},
            {
                "$facet": {
                    "total_stats": [
                        {
                            "$group": {
                                "_id": None,
                                "total_actions": {"$sum": 1},
                                "successful_actions": {
                                    "$sum": {"$cond": [{"$eq": ["$success", True]}, 1, 0]}
                                },
                                "failed_actions": {
                                    "$sum": {"$cond": [{"$eq": ["$success", False]}, 1, 0]}
                                },
                                "unique_users": {"$addToSet": "$user_id"}
                            }
                        },
                        {
                            "$project": {
                                "total_actions": 1,
                                "successful_actions": 1,
                                "failed_actions": 1,
                                "unique_users": {"$size": "$unique_users"}
                            }
                        }
                    ],
                    "action_stats": [
                        {
                            "$group": {
                                "_id": "$action",
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"count": -1}},
                        {"$limit": 10}
                    ],
                    "hourly_stats": [
                        {
                            "$group": {
                                "_id": {"$hour": "$created_at"},
                                "count": {"$sum": 1}
                            }
                        },
                        {"$sort": {"_id": 1}}
                    ]
                }
            }
        ]
        
        # Execute aggregation
        result = await db.audit_logs.aggregate(pipeline).to_list(1)
        
        if not result:
            return AuditStats(
                total_actions=0,
                successful_actions=0,
                failed_actions=0,
                unique_users=0,
                most_common_actions=[],
                actions_by_hour=[]
            )
        
        data = result[0]
        total_stats = data["total_stats"][0] if data["total_stats"] else {}
        
        return AuditStats(
            total_actions=total_stats.get("total_actions", 0),
            successful_actions=total_stats.get("successful_actions", 0),
            failed_actions=total_stats.get("failed_actions", 0),
            unique_users=total_stats.get("unique_users", 0),
            most_common_actions=[
                {"action": item["_id"], "count": item["count"]}
                for item in data["action_stats"]
            ],
            actions_by_hour=[
                {"hour": item["_id"], "count": item["count"]}
                for item in data["hourly_stats"]
            ]
        )
        
    except Exception as e:
        logger.error(f"Error getting audit statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit statistics")

@router.get("/actions", response_model=List[str])
async def get_available_actions(tenant_id: Optional[str] = Query(None)):
    """Get list of all available actions for filtering"""
    try:
        db = await get_database()
        
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        # Get distinct actions
        actions = await db.audit_logs.distinct("action", query)
        return sorted(actions)
        
    except Exception as e:
        logger.error(f"Error getting available actions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get actions")

@router.get("/resource-types", response_model=List[str])
async def get_resource_types(tenant_id: Optional[str] = Query(None)):
    """Get list of all resource types for filtering"""
    try:
        db = await get_database()
        
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        # Get distinct resource types
        resource_types = await db.audit_logs.distinct("resource_type", query)
        return sorted(resource_types)
        
    except Exception as e:
        logger.error(f"Error getting resource types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get resource types")

@router.delete("/cleanup")
async def cleanup_old_audit_logs(
    days_to_keep: int = Query(90, description="Number of days of logs to keep"),
    tenant_id: Optional[str] = Query(None, description="Specific tenant to clean up")
):
    """Clean up old audit logs (Admin only)"""
    try:
        db = await get_database()
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Build delete query
        delete_query = {"created_at": {"$lt": cutoff_date}}
        if tenant_id:
            delete_query["tenant_id"] = tenant_id
        
        # Delete old logs
        result = await db.audit_logs.delete_many(delete_query)
        
        return {
            "message": f"Cleaned up {result.deleted_count} old audit log entries",
            "deleted_count": result.deleted_count,
            "cutoff_date": cutoff_date
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup audit logs")

@router.get("/export")
async def export_audit_logs(
    tenant_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    format: str = Query("json", description="Export format: json or csv")
):
    """Export audit logs for compliance/backup purposes"""
    try:
        db = await get_database()
        
        # Build query
        query = {}
        if tenant_id:
            query["tenant_id"] = tenant_id
        
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = datetime.fromisoformat(start_date)
            if end_date:
                date_filter["$lte"] = datetime.fromisoformat(end_date)
            query["created_at"] = date_filter
        
        # Get logs
        cursor = db.audit_logs.find(query).sort("created_at", -1)
        logs = []
        
        async for log_doc in cursor:
            log_doc["id"] = str(log_doc["_id"])
            log_doc.pop("_id", None)
            # Convert datetime to string for JSON serialization
            log_doc["created_at"] = log_doc["created_at"].isoformat()
            if log_doc.get("updated_at"):
                log_doc["updated_at"] = log_doc["updated_at"].isoformat()
            logs.append(log_doc)
        
        return {
            "logs": logs,
            "count": len(logs),
            "exported_at": datetime.utcnow().isoformat(),
            "filters": query
        }
        
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to export audit logs")