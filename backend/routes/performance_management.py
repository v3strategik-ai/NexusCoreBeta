from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time
import logging
from collections import defaultdict, deque
import asyncio
from pydantic import BaseModel, Field

from performance_optimizer import performance_optimizer, monitor_performance, run_performance_optimization

router = APIRouter(prefix="/performance", tags=["performance"])
logger = logging.getLogger(__name__)

# Rate limiting storage (use Redis in production)
rate_limit_storage = defaultdict(lambda: deque())
request_counts = defaultdict(int)

# Pydantic Models
class RateLimitConfig(BaseModel):
    requests_per_minute: int = Field(default=100, description="Maximum requests per minute")
    requests_per_hour: int = Field(default=1000, description="Maximum requests per hour")
    burst_limit: int = Field(default=20, description="Burst request limit")
    
class PerformanceConfig(BaseModel):
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    max_cache_size: int = Field(default=10000, description="Maximum cache entries")
    slow_query_threshold: int = Field(default=100, description="Slow query threshold in ms")
    max_response_time: float = Field(default=2.0, description="Maximum response time in seconds")

class OptimizationRequest(BaseModel):
    include_database: bool = Field(default=True, description="Include database optimization")
    include_memory: bool = Field(default=True, description="Include memory optimization") 
    include_cache: bool = Field(default=True, description="Include cache optimization")

class RateLimitMiddleware:
    """Rate limiting middleware for API endpoints"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
    
    async def check_rate_limit(self, request: Request) -> bool:
        """Check if request is within rate limits"""
        try:
            # Get client identifier (IP + user ID if available)
            client_ip = request.client.host
            client_id = f"{client_ip}"
            
            # Add user ID to client_id if available (from auth)
            # user_id = getattr(request.state, 'user_id', None)
            # if user_id:
            #     client_id = f"{client_ip}:{user_id}"
            
            current_time = datetime.utcnow()
            
            # Clean old entries (older than 1 hour)
            cutoff_time = current_time - timedelta(hours=1)
            client_requests = rate_limit_storage[client_id]
            
            while client_requests and client_requests[0] < cutoff_time:
                client_requests.popleft()
            
            # Check per-minute limit
            minute_cutoff = current_time - timedelta(minutes=1)
            recent_requests = [req_time for req_time in client_requests if req_time > minute_cutoff]
            
            if len(recent_requests) >= self.config.requests_per_minute:
                return False
            
            # Check per-hour limit
            if len(client_requests) >= self.config.requests_per_hour:
                return False
            
            # Check burst limit (last 10 seconds)
            burst_cutoff = current_time - timedelta(seconds=10)
            burst_requests = [req_time for req_time in client_requests if req_time > burst_cutoff]
            
            if len(burst_requests) >= self.config.burst_limit:
                return False
            
            # Add current request
            client_requests.append(current_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow request if rate limiting fails
    
    def get_rate_limit_headers(self, client_id: str) -> Dict[str, str]:
        """Get rate limit headers for response"""
        try:
            current_time = datetime.utcnow()
            client_requests = rate_limit_storage[client_id]
            
            # Count recent requests
            minute_cutoff = current_time - timedelta(minutes=1)
            recent_count = len([req for req in client_requests if req > minute_cutoff])
            
            remaining = max(0, self.config.requests_per_minute - recent_count)
            reset_time = int((current_time + timedelta(minutes=1)).timestamp())
            
            return {
                "X-RateLimit-Limit": str(self.config.requests_per_minute),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time)
            }
        except Exception as e:
            logger.error(f"Error generating rate limit headers: {e}")
            return {}

# Global rate limiter
rate_limiter = RateLimitMiddleware()

async def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting"""
    if not await rate_limiter.check_rate_limit(request):
        # Get client ID for headers
        client_ip = request.client.host
        headers = rate_limiter.get_rate_limit_headers(client_ip)
        
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers=headers
        )

# API Endpoints

@router.get("/health")
@monitor_performance("performance_health")
async def get_performance_health():
    """Get system performance health status"""
    try:
        report = await performance_optimizer.get_performance_report()
        
        # Determine health status
        performance_summary = report.get("performance_summary", {})
        avg_response_time = performance_summary.get("average_response_time", 0)
        slow_requests_percent = performance_summary.get("slow_requests_percentage", 0)
        
        if avg_response_time < 1.0 and slow_requests_percent < 5:
            health_status = "healthy"
        elif avg_response_time < 2.0 and slow_requests_percent < 10:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return {
            "status": health_status,
            "performance_report": report,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance health")

@router.get("/metrics")
@monitor_performance("performance_metrics")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        report = await performance_optimizer.get_performance_report()
        
        # Add system metrics
        import psutil
        
        system_metrics = {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
            "process_count": len(psutil.pids())
        }
        
        # Add rate limiting metrics
        active_clients = len(rate_limit_storage)
        total_requests_tracked = sum(len(requests) for requests in rate_limit_storage.values())
        
        rate_limit_metrics = {
            "active_clients": active_clients,
            "total_requests_tracked": total_requests_tracked,
            "rate_limit_config": {
                "requests_per_minute": rate_limiter.config.requests_per_minute,
                "requests_per_hour": rate_limiter.config.requests_per_hour,
                "burst_limit": rate_limiter.config.burst_limit
            }
        }
        
        return {
            "performance_metrics": report,
            "system_metrics": system_metrics,
            "rate_limit_metrics": rate_limit_metrics,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@router.post("/optimize")
@monitor_performance("performance_optimize")
async def run_optimization(optimization_request: OptimizationRequest):
    """Run comprehensive performance optimization"""
    try:
        logger.info("Starting performance optimization via API...")
        
        optimization_result = await run_performance_optimization()
        
        return {
            "message": "Performance optimization completed",
            "optimization_result": optimization_result,
            "request_config": optimization_request.dict(),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error running optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Performance optimization failed: {str(e)}")

@router.get("/cache/stats")
@monitor_performance("cache_stats")
async def get_cache_statistics():
    """Get cache performance statistics"""
    try:
        cache_stats = {
            "cache_size": len(performance_optimizer.query_cache),
            "cache_capacity": performance_optimizer.optimization_rules['max_cache_size'],
            "cache_utilization_percent": round(
                (len(performance_optimizer.query_cache) / performance_optimizer.optimization_rules['max_cache_size']) * 100, 2
            ),
            "ttl_entries": len(performance_optimizer.cache_ttl),
            "default_ttl_seconds": performance_optimizer.optimization_rules['cache_ttl_default']
        }
        
        # Calculate cache hit rate from recent metrics
        recent_metrics = performance_optimizer.metrics_history[-100:] if performance_optimizer.metrics_history else []
        total_cache_requests = sum(m.cache_hits + m.cache_misses for m in recent_metrics)
        
        if total_cache_requests > 0:
            total_hits = sum(m.cache_hits for m in recent_metrics)
            cache_stats["cache_hit_rate_percent"] = round((total_hits / total_cache_requests) * 100, 2)
        else:
            cache_stats["cache_hit_rate_percent"] = 0
        
        return {
            "cache_statistics": cache_stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")

@router.post("/cache/clear")
@monitor_performance("cache_clear")
async def clear_cache():
    """Clear performance cache"""
    try:
        cache_size_before = len(performance_optimizer.query_cache)
        
        performance_optimizer.query_cache.clear()
        performance_optimizer.cache_ttl.clear()
        
        return {
            "message": "Cache cleared successfully",
            "entries_cleared": cache_size_before,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.get("/rate-limits")
@monitor_performance("rate_limits_status")
async def get_rate_limit_status():
    """Get rate limiting status and statistics"""
    try:
        current_time = datetime.utcnow()
        
        # Calculate active clients and request statistics
        active_clients = 0
        total_requests_last_hour = 0
        total_requests_last_minute = 0
        
        hour_cutoff = current_time - timedelta(hours=1)
        minute_cutoff = current_time - timedelta(minutes=1)
        
        for client_id, requests in rate_limit_storage.items():
            if requests:  # Client has recent requests
                active_clients += 1
                
                hour_requests = [req for req in requests if req > hour_cutoff]
                minute_requests = [req for req in requests if req > minute_cutoff]
                
                total_requests_last_hour += len(hour_requests)
                total_requests_last_minute += len(minute_requests)
        
        rate_limit_stats = {
            "active_clients": active_clients,
            "total_requests_last_hour": total_requests_last_hour,
            "total_requests_last_minute": total_requests_last_minute,
            "rate_limit_config": {
                "requests_per_minute": rate_limiter.config.requests_per_minute,
                "requests_per_hour": rate_limiter.config.requests_per_hour,
                "burst_limit": rate_limiter.config.burst_limit
            },
            "storage_size": len(rate_limit_storage)
        }
        
        return {
            "rate_limit_status": rate_limit_stats,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rate limit status")

@router.put("/config")
@monitor_performance("update_config")
async def update_performance_config(
    rate_limit_config: Optional[RateLimitConfig] = None,
    performance_config: Optional[PerformanceConfig] = None
):
    """Update performance configuration"""
    try:
        updated_configs = {}
        
        if rate_limit_config:
            # Update rate limiter configuration
            global rate_limiter
            rate_limiter.config = rate_limit_config
            updated_configs["rate_limiting"] = rate_limit_config.dict()
        
        if performance_config:
            # Update performance optimizer configuration
            performance_optimizer.optimization_rules.update({
                'cache_ttl_default': performance_config.cache_ttl,
                'max_cache_size': performance_config.max_cache_size,
                'slow_query_threshold': performance_config.slow_query_threshold,
                'max_response_time': performance_config.max_response_time
            })
            updated_configs["performance"] = performance_config.dict()
        
        return {
            "message": "Performance configuration updated successfully",
            "updated_configs": updated_configs,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error updating performance config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update performance configuration")

@router.get("/slow-queries")
@monitor_performance("slow_queries")
async def get_slow_queries():
    """Get detected slow queries and optimization suggestions"""
    try:
        slow_queries_data = []
        
        for query_result in performance_optimizer.slow_queries[-20:]:  # Last 20 slow queries
            slow_queries_data.append({
                "collection": query_result.collection,
                "query": str(query_result.query),
                "execution_time_ms": query_result.execution_time_ms,
                "documents_examined": query_result.documents_examined,
                "documents_returned": query_result.documents_returned,
                "index_used": query_result.index_used,
                "optimization_suggestions": query_result.optimization_suggestions
            })
        
        return {
            "slow_queries": slow_queries_data,
            "total_slow_queries_detected": len(performance_optimizer.slow_queries),
            "analysis_threshold_ms": performance_optimizer.optimization_rules['slow_query_threshold'],
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting slow queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get slow queries")

# Background cleanup task
async def cleanup_rate_limit_storage():
    """Background task to clean up old rate limit data"""
    while True:
        try:
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(hours=2)  # Keep 2 hours of data
            
            # Clean up old entries
            cleaned_clients = 0
            for client_id in list(rate_limit_storage.keys()):
                client_requests = rate_limit_storage[client_id]
                
                # Remove old requests
                while client_requests and client_requests[0] < cutoff_time:
                    client_requests.popleft()
                
                # Remove client if no recent requests
                if not client_requests:
                    del rate_limit_storage[client_id]
                    cleaned_clients += 1
            
            if cleaned_clients > 0:
                logger.info(f"Cleaned up {cleaned_clients} inactive clients from rate limit storage")
            
            # Wait 10 minutes before next cleanup
            await asyncio.sleep(600)
            
        except Exception as e:
            logger.error(f"Error in rate limit cleanup: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

# Start background cleanup task when module is imported
# asyncio.create_task(cleanup_rate_limit_storage())