import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import socketio
from fastapi import HTTPException

from database import (
    get_leads_collection, 
    get_agents_collection, 
    get_activities_collection,
    get_documents_collection
)

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

# Track connected clients and their subscriptions
connected_clients: Dict[str, Dict[str, Any]] = {}
subscription_channels: Dict[str, List[str]] = {
    'dashboard_metrics': [],
    'lead_updates': [],
    'agent_status': [],
    'activity_feed': [], 
    'workflow_updates': [],
    'document_updates': [],
    'notifications': []
}

class RealTimeManager:
    """Manages real-time updates and WebSocket communications"""
    
    def __init__(self):
        self.active_connections = set()
        
    async def broadcast_to_channel(self, channel: str, event: str, data: Dict[str, Any]):
        """Broadcast data to all clients subscribed to a channel"""
        try:
            if channel in subscription_channels:
                client_ids = subscription_channels[channel]
                
                for client_id in client_ids:
                    try:
                        await sio.emit(event, data, room=client_id)
                        logger.debug(f"Broadcasted {event} to {client_id} on channel {channel}")
                    except Exception as e:
                        logger.error(f"Failed to broadcast to {client_id}: {e}")
                        # Remove disconnected client
                        if client_id in connected_clients:
                            del connected_clients[client_id]
                        if client_id in client_ids:
                            client_ids.remove(client_id)
                            
        except Exception as e:
            logger.error(f"Error broadcasting to channel {channel}: {e}")
    
    async def send_notification(self, user_id: Optional[str], notification: Dict[str, Any]):
        """Send notification to specific user or all users"""
        try:
            notification_data = {
                'id': f"notif_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                'timestamp': datetime.now().isoformat(),
                'read': False,
                **notification
            }
            
            if user_id:
                # Send to specific user
                await sio.emit('notification', notification_data, room=user_id)
            else:
                # Broadcast to all subscribed clients
                await self.broadcast_to_channel('notifications', 'notification', notification_data)
                
            logger.info(f"Notification sent: {notification.get('title', 'Untitled')}")
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def update_dashboard_metrics(self):
        """Fetch and broadcast updated dashboard metrics"""
        try:
            # Get collections
            leads_collection = await get_leads_collection()
            agents_collection = await get_agents_collection()
            activities_collection = await get_activities_collection()
            documents_collection = await get_documents_collection()
            
            # Calculate live metrics
            total_leads = await leads_collection.count_documents({})
            hot_leads = await leads_collection.count_documents({"status": "hot"})
            converted_leads = await leads_collection.count_documents({"status": "converted"})
            
            # Pipeline value calculation
            pipeline = leads_collection.aggregate([
                {"$match": {"status": {"$in": ["warm", "hot"]}}},
                {"$group": {"_id": None, "total": {"$sum": "$value"}}}
            ])
            pipeline_result = await pipeline.to_list(1)
            pipeline_value = pipeline_result[0]["total"] if pipeline_result else 0
            
            # Agent metrics
            total_agents = await agents_collection.count_documents({})
            active_agents = await agents_collection.count_documents({"status": "active"})
            
            # Recent activities
            recent_activities = await activities_collection.find({}).sort("timestamp", -1).limit(10).to_list(10)
            
            # Document metrics
            total_documents = await documents_collection.count_documents({})
            
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'leads': {
                    'total': total_leads,
                    'hot': hot_leads,
                    'converted': converted_leads,
                    'pipeline_value': pipeline_value
                },
                'agents': {
                    'total': total_agents,
                    'active': active_agents,
                    'utilization': round((active_agents / max(total_agents, 1)) * 100, 1)
                },
                'documents': {
                    'total': total_documents
                },
                'activities': {
                    'recent': [
                        {
                            'id': str(activity.get('_id', '')),
                            'agent_name': activity.get('agent_name', 'System'),
                            'activity_type': activity.get('activity_type', 'unknown'),
                            'description': activity.get('description', ''),
                            'timestamp': activity.get('timestamp', datetime.now()).isoformat() if isinstance(activity.get('timestamp'), datetime) else activity.get('timestamp', datetime.now().isoformat())
                        }
                        for activity in recent_activities
                    ]
                }
            }
            
            await self.broadcast_to_channel('dashboard_metrics', 'dashboard_update', metrics_data)
            logger.debug("Dashboard metrics updated and broadcast")
            
        except Exception as e:
            logger.error(f"Error updating dashboard metrics: {e}")
    
    async def broadcast_lead_update(self, lead_data: Dict[str, Any], action: str):
        """Broadcast lead updates to subscribed clients"""
        try:
            update_data = {
                'action': action,  # 'created', 'updated', 'deleted'
                'lead': lead_data,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.broadcast_to_channel('lead_updates', 'lead_update', update_data)
            
            # Send notification for important lead changes
            if action in ['created', 'updated'] and lead_data.get('status') == 'hot':
                await self.send_notification(None, {
                    'type': 'success',
                    'title': f'Hot Lead {action.title()}',
                    'message': f"Lead {lead_data.get('name', 'Unknown')} is now HOT with ${lead_data.get('value', 0):,} potential value",
                    'category': 'lead'
                })
                
        except Exception as e:
            logger.error(f"Error broadcasting lead update: {e}")
    
    async def broadcast_agent_status(self, agent_data: Dict[str, Any], status: str):
        """Broadcast agent status changes"""
        try:
            status_data = {
                'agent_id': agent_data.get('id'),
                'name': agent_data.get('name'),
                'status': status,
                'autonomy_level': agent_data.get('autonomy_level'),
                'tasks_completed': agent_data.get('metrics', {}).get('tasks_completed', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            await self.broadcast_to_channel('agent_status', 'agent_status_update', status_data)
            
        except Exception as e:
            logger.error(f"Error broadcasting agent status: {e}")
    
    async def broadcast_activity(self, activity_data: Dict[str, Any]):
        """Broadcast new activity to activity feed"""
        try:
            formatted_activity = {
                'id': activity_data.get('id', str(datetime.now().timestamp())),
                'agent_name': activity_data.get('agent_name', 'System'),
                'activity_type': activity_data.get('activity_type', 'unknown'),
                'description': activity_data.get('description', ''),
                'timestamp': activity_data.get('timestamp', datetime.now().isoformat()),
                'metadata': activity_data.get('metadata', {})
            }
            
            await self.broadcast_to_channel('activity_feed', 'new_activity', formatted_activity)
            
        except Exception as e:
            logger.error(f"Error broadcasting activity: {e}")

# Global real-time manager instance
realtime_manager = RealTimeManager()

# Socket.IO Event Handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    try:
        logger.info(f"Client connected: {sid}")
        
        # Initialize client data
        connected_clients[sid] = {
            'connected_at': datetime.now().isoformat(),
            'subscriptions': [],
            'user_id': None  # Can be set during authentication
        }
        
        # Send initial connection confirmation
        await sio.emit('connected', {
            'client_id': sid,
            'server_time': datetime.now().isoformat(),
            'message': 'Connected to Nexus Core Real-Time Server'
        }, room=sid)
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling connection for {sid}: {e}")
        return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    try:
        logger.info(f"Client disconnected: {sid}")
        
        # Remove client from all subscriptions
        if sid in connected_clients:
            subscriptions = connected_clients[sid].get('subscriptions', [])
            for channel in subscriptions:
                if channel in subscription_channels and sid in subscription_channels[channel]:
                    subscription_channels[channel].remove(sid)
            
            del connected_clients[sid]
        
    except Exception as e:
        logger.error(f"Error handling disconnection for {sid}: {e}")

@sio.event
async def subscribe(sid, data):
    """Handle channel subscription"""
    try:
        channel = data.get('channel')
        if not channel:
            await sio.emit('error', {'message': 'Channel name required'}, room=sid)
            return
        
        if channel not in subscription_channels:
            await sio.emit('error', {'message': f'Invalid channel: {channel}'}, room=sid)
            return
        
        # Add client to channel
        if sid not in subscription_channels[channel]:
            subscription_channels[channel].append(sid)
        
        # Update client subscriptions
        if sid in connected_clients:
            if channel not in connected_clients[sid]['subscriptions']:
                connected_clients[sid]['subscriptions'].append(channel)
        
        logger.info(f"Client {sid} subscribed to {channel}")
        
        # Send confirmation
        await sio.emit('subscribed', {
            'channel': channel,
            'message': f'Subscribed to {channel}'
        }, room=sid)
        
        # Send initial data for dashboard_metrics
        if channel == 'dashboard_metrics':
            await realtime_manager.update_dashboard_metrics()
        
    except Exception as e:
        logger.error(f"Error handling subscription for {sid}: {e}")
        await sio.emit('error', {'message': 'Subscription failed'}, room=sid)

@sio.event
async def unsubscribe(sid, data):
    """Handle channel unsubscription"""
    try:
        channel = data.get('channel')
        if not channel:
            return
        
        # Remove client from channel
        if channel in subscription_channels and sid in subscription_channels[channel]:
            subscription_channels[channel].remove(sid)
        
        # Update client subscriptions
        if sid in connected_clients and channel in connected_clients[sid]['subscriptions']:
            connected_clients[sid]['subscriptions'].remove(channel)
        
        logger.info(f"Client {sid} unsubscribed from {channel}")
        
        await sio.emit('unsubscribed', {
            'channel': channel,
            'message': f'Unsubscribed from {channel}'
        }, room=sid)
        
    except Exception as e:
        logger.error(f"Error handling unsubscription for {sid}: {e}")

@sio.event
async def ping(sid, data):
    """Handle ping for connection testing"""
    await sio.emit('pong', {
        'timestamp': datetime.now().isoformat(),
        'message': 'Server is alive'
    }, room=sid)

# Background task for periodic updates
async def periodic_updates():
    """Background task for periodic metric updates"""
    while True:
        try:
            await asyncio.sleep(30)  # Update every 30 seconds
            
            # Update dashboard metrics for subscribed clients
            if subscription_channels['dashboard_metrics']:
                await realtime_manager.update_dashboard_metrics()
                
        except Exception as e:
            logger.error(f"Error in periodic updates: {e}")
            await asyncio.sleep(60)  # Wait longer if there's an error

# Function to start background tasks
def start_background_tasks():
    """Start background tasks for real-time updates"""
    try:
        asyncio.create_task(periodic_updates())
        logger.info("Background tasks started for real-time updates")
    except Exception as e:
        logger.error(f"Error starting background tasks: {e}")

# Export the Socket.IO app for integration with FastAPI
socketio_app = socketio.ASGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

# Helper functions for other modules to trigger real-time updates
async def trigger_lead_update(lead_data: Dict[str, Any], action: str = 'updated'):
    """Trigger real-time lead update broadcast"""
    await realtime_manager.broadcast_lead_update(lead_data, action)

async def trigger_agent_status_update(agent_data: Dict[str, Any], status: str):
    """Trigger real-time agent status update"""
    await realtime_manager.broadcast_agent_status(agent_data, status)

async def trigger_activity_broadcast(activity_data: Dict[str, Any]):
    """Trigger real-time activity broadcast"""
    await realtime_manager.broadcast_activity(activity_data)

async def send_notification(title: str, message: str, type: str = 'info', user_id: Optional[str] = None):
    """Send real-time notification"""
    await realtime_manager.send_notification(user_id, {
        'type': type,
        'title': title,
        'message': message,
        'category': 'system'
    })

# Get connection statistics
def get_connection_stats():
    """Get current WebSocket connection statistics"""
    return {
        'total_connections': len(connected_clients),
        'channels': {
            channel: len(clients) for channel, clients in subscription_channels.items()
        },
        'connected_clients': list(connected_clients.keys())
    }