from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel

from database import (
    get_leads_collection,
    get_agents_collection, 
    get_activities_collection,
    get_documents_collection
)
from websocket import get_connection_stats, send_notification

router = APIRouter(prefix="/realtime", tags=["realtime"])
logger = logging.getLogger(__name__)

# Pydantic models for real-time data
class LiveMetrics(BaseModel):
    timestamp: str
    leads: Dict[str, Any]
    agents: Dict[str, Any]
    documents: Dict[str, Any]
    activities: Dict[str, Any]
    system: Dict[str, Any]

class NotificationRequest(BaseModel):
    title: str
    message: str
    type: str = "info"  # info, success, warning, error
    user_id: Optional[str] = None
    category: str = "system"

class SystemAlert(BaseModel):
    id: str
    type: str
    title: str
    message: str
    severity: str  # low, medium, high, critical
    timestamp: str
    resolved: bool = False

@router.get("/metrics/live", response_model=LiveMetrics)
async def get_live_metrics():
    """Get current live metrics for real-time dashboard"""
    try:
        # Get collections
        leads_collection = await get_leads_collection()
        agents_collection = await get_agents_collection()
        activities_collection = await get_activities_collection()
        documents_collection = await get_documents_collection()
        
        # Calculate comprehensive metrics
        
        # Lead metrics
        total_leads = await leads_collection.count_documents({})
        lead_statuses = await leads_collection.aggregate([
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_value": {"$sum": "$value"}
            }}
        ]).to_list(10)
        
        lead_metrics = {
            'total': total_leads,
            'by_status': {status['_id']: {'count': status['count'], 'value': status['total_value']} for status in lead_statuses},
            'hot_leads': await leads_collection.count_documents({"status": "hot"}),
            'converted': await leads_collection.count_documents({"status": "converted"}),
            'pipeline_value': sum(status['total_value'] for status in lead_statuses if status['_id'] in ['warm', 'hot'])
        }
        
        # Recent lead activity (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_leads = await leads_collection.count_documents({
            "created_at": {"$gte": yesterday}
        })
        lead_metrics['recent_leads_24h'] = recent_leads
        
        # Agent metrics
        total_agents = await agents_collection.count_documents({})
        active_agents = await agents_collection.count_documents({"status": "active"})
        
        # Agent performance metrics
        agent_performance = await agents_collection.aggregate([
            {"$match": {"status": "active"}},
            {"$group": {
                "_id": None,
                "avg_autonomy": {"$avg": {"$switch": {
                    "branches": [
                        {"case": {"$eq": ["$autonomy_level", "Low"]}, "then": 1},
                        {"case": {"$eq": ["$autonomy_level", "Medium"]}, "then": 2},
                        {"case": {"$eq": ["$autonomy_level", "High"]}, "then": 3},
                        {"case": {"$eq": ["$autonomy_level", "Quantum"]}, "then": 4}
                    ],
                    "default": 2
                }}},
                "total_tasks": {"$sum": "$metrics.tasks_completed"}
            }}
        ]).to_list(1)
        
        agent_metrics = {
            'total': total_agents,
            'active': active_agents,
            'utilization': round((active_agents / max(total_agents, 1)) * 100, 1),
            'avg_autonomy_score': round(agent_performance[0]['avg_autonomy'], 1) if agent_performance else 2.0,
            'total_tasks_completed': agent_performance[0]['total_tasks'] if agent_performance else 0
        }
        
        # Document metrics
        total_documents = await documents_collection.count_documents({})
        recent_documents = await documents_collection.count_documents({
            "created_at": {"$gte": yesterday}
        })
        
        document_metrics = {
            'total': total_documents,
            'recent_24h': recent_documents,
            'generation_rate': round(recent_documents / 24, 2)  # Per hour
        }
        
        # Activity metrics
        total_activities = await activities_collection.count_documents({})
        recent_activities = await activities_collection.count_documents({
            "timestamp": {"$gte": yesterday}
        })
        
        # Activity breakdown by type
        activity_types = await activities_collection.aggregate([
            {"$match": {"timestamp": {"$gte": yesterday}}},
            {"$group": {
                "_id": "$activity_type",
                "count": {"$sum": 1}
            }}
        ]).to_list(10)
        
        activity_metrics = {
            'total': total_activities,
            'recent_24h': recent_activities,
            'by_type': {activity['_id']: activity['count'] for activity in activity_types},
            'activity_rate': round(recent_activities / 24, 2)  # Per hour
        }
        
        # System metrics
        connection_stats = get_connection_stats()
        system_metrics = {
            'websocket_connections': connection_stats['total_connections'],
            'active_channels': len([c for c, clients in connection_stats['channels'].items() if clients > 0]),
            'uptime_hours': 24,  # Placeholder - would track actual uptime
            'system_health': 'excellent'  # Would include actual health checks
        }
        
        return LiveMetrics(
            timestamp=datetime.now().isoformat(),
            leads=lead_metrics,
            agents=agent_metrics,
            documents=document_metrics,
            activities=activity_metrics,
            system=system_metrics
        )
        
    except Exception as e:
        logger.error(f"Error getting live metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve live metrics")

@router.get("/activities/stream")
async def get_activity_stream(limit: int = Query(20, ge=1, le=100)):
    """Get recent activity stream for real-time feed"""
    try:
        collection = await get_activities_collection()
        
        activities = await collection.find({}).sort("timestamp", -1).limit(limit).to_list(limit)
        
        formatted_activities = []
        for activity in activities:
            formatted_activities.append({
                'id': str(activity.get('_id', '')),
                'agent_name': activity.get('agent_name', 'System'),
                'activity_type': activity.get('activity_type', 'unknown'),
                'description': activity.get('description', ''),
                'timestamp': activity.get('timestamp', datetime.now()).isoformat() if isinstance(activity.get('timestamp'), datetime) else activity.get('timestamp', datetime.now().isoformat()),
                'metadata': activity.get('metadata', {})
            })
        
        return {
            'activities': formatted_activities,
            'total_count': len(formatted_activities),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting activity stream: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve activity stream")

@router.get("/agents/status")
async def get_agents_status():
    """Get current status of all agents for real-time monitoring"""
    try:
        collection = await get_agents_collection()
        
        agents = await collection.find({}).to_list(100)
        
        agent_statuses = []
        for agent in agents:
            agent_statuses.append({
                'id': agent.get('id'),
                'name': agent.get('name'),
                'type': agent.get('type'),
                'status': agent.get('status', 'inactive'),
                'autonomy_level': agent.get('autonomy_level', 'Medium'),
                'tasks_completed': agent.get('metrics', {}).get('tasks_completed', 0),
                'last_active': agent.get('updated_at', agent.get('created_at', datetime.now())).isoformat() if isinstance(agent.get('updated_at'), datetime) else agent.get('updated_at', datetime.now().isoformat()),
                'configuration_complexity': agent.get('metrics', {}).get('configuration_complexity', 0),
                'readiness_score': agent.get('metrics', {}).get('readiness_score', 0)
            })
        
        return {
            'agents': agent_statuses,
            'summary': {
                'total': len(agent_statuses),
                'active': len([a for a in agent_statuses if a['status'] == 'active']),
                'inactive': len([a for a in agent_statuses if a['status'] == 'inactive']),
                'average_readiness': round(sum(a['readiness_score'] for a in agent_statuses) / max(len(agent_statuses), 1), 1)
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agents status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agents status")

@router.get("/leads/pipeline")
async def get_pipeline_status():
    """Get real-time sales pipeline status"""
    try:
        collection = await get_leads_collection()
        
        # Pipeline analysis
        pipeline_data = await collection.aggregate([
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_value": {"$sum": "$value"},
                "avg_value": {"$avg": "$value"}
            }},
            {"$sort": {"total_value": -1}}
        ]).to_list(10)
        
        # Recent lead activity
        recent_leads = await collection.find({}).sort("created_at", -1).limit(10).to_list(10)
        
        # Conversion rate calculation
        total_leads = await collection.count_documents({})
        converted_leads = await collection.count_documents({"status": "converted"})
        conversion_rate = round((converted_leads / max(total_leads, 1)) * 100, 2)
        
        return {
            'pipeline': [
                {
                    'status': item['_id'],
                    'count': item['count'],
                    'total_value': item['total_value'],
                    'avg_value': round(item['avg_value'], 2)
                }
                for item in pipeline_data
            ],
            'recent_leads': [
                {
                    'id': lead.get('id'),
                    'name': lead.get('name'),
                    'company': lead.get('company'),
                    'status': lead.get('status'),
                    'value': lead.get('value'),
                    'created_at': lead.get('created_at', datetime.now()).isoformat() if isinstance(lead.get('created_at'), datetime) else lead.get('created_at', datetime.now().isoformat())
                }
                for lead in recent_leads
            ],
            'summary': {
                'total_leads': total_leads,
                'converted_leads': converted_leads,
                'conversion_rate': conversion_rate,
                'total_pipeline_value': sum(item['total_value'] for item in pipeline_data)
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pipeline status")

@router.post("/notifications/send")
async def send_realtime_notification(notification: NotificationRequest):
    """Send real-time notification to connected clients"""
    try:
        await send_notification(
            title=notification.title,
            message=notification.message,  
            type=notification.type,
            user_id=notification.user_id
        )
        
        return {
            'status': 'success',
            'message': 'Notification sent successfully',
            'notification': notification.dict()
        }
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@router.get("/websocket/stats")
async def get_websocket_stats():
    """Get current WebSocket connection statistics"""
    try:
        stats = get_connection_stats()
        
        return {
            'connections': stats,
            'status': 'healthy' if stats['total_connections'] > 0 else 'no_connections',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve WebSocket statistics")

@router.get("/system/alerts")
async def get_system_alerts():
    """Get current system alerts and warnings"""
    try:
        # This would typically check various system health indicators
        # For now, returning placeholder alerts
        
        alerts = []
        
        # Check WebSocket connections
        stats = get_connection_stats()
        if stats['total_connections'] == 0:
            alerts.append(SystemAlert(
                id="ws_no_connections",
                type="warning",
                title="No WebSocket Connections",
                message="No clients are currently connected to real-time updates",
                severity="medium",
                timestamp=datetime.now().isoformat()
            ))
        
        # Check recent activity
        activities_collection = await get_activities_collection()
        recent_activity_count = await activities_collection.count_documents({
            "timestamp": {"$gte": datetime.now() - timedelta(hours=1)}
        })
        
        if recent_activity_count == 0:
            alerts.append(SystemAlert(
                id="low_activity",
                type="info", 
                title="Low System Activity",
                message="No activities recorded in the last hour",
                severity="low",
                timestamp=datetime.now().isoformat()
            ))
        
        return {
            'alerts': [alert.dict() for alert in alerts],
            'total_alerts': len(alerts),
            'critical_count': len([a for a in alerts if a.severity == 'critical']),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting system alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system alerts")

@router.get("/performance/metrics")
async def get_performance_metrics():
    """Get system performance metrics"""
    try:
        # This would typically include actual performance monitoring
        # For now, returning simulated metrics
        
        metrics = {
            'response_times': {
                'avg_api_response': 45,  # milliseconds
                'avg_db_query': 23,     # milliseconds
                'avg_websocket_latency': 12  # milliseconds
            },
            'throughput': {
                'api_requests_per_minute': 150,
                'websocket_messages_per_minute': 320,
                'database_operations_per_minute': 89
            },
            'resource_usage': {
                'cpu_usage': 35.2,      # percentage
                'memory_usage': 62.8,   # percentage
                'database_connections': 8  # active connections
            },
            'error_rates': {
                'api_error_rate': 0.12,      # percentage
                'websocket_error_rate': 0.05,  # percentage
                'database_error_rate': 0.01   # percentage
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")