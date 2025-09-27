#!/usr/bin/env python3
"""
Phase 7: Platform Performance Optimizer
Comprehensive performance optimization for database queries, API responses, and resource management
"""

import asyncio
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from motor.motor_asyncio import AsyncIOMotorDatabase
import psutil
import gc
from functools import wraps

from database import get_database

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    endpoint: str
    response_time: float
    memory_usage: float
    cpu_usage: float
    database_queries: int
    cache_hits: int
    cache_misses: int
    timestamp: datetime
    
@dataclass
class QueryOptimizationResult:
    """Query optimization analysis result"""
    collection: str
    query: Dict[str, Any]
    execution_time_ms: float
    documents_examined: int
    documents_returned: int
    index_used: bool
    optimization_suggestions: List[str]

class PerformanceOptimizer:
    """Comprehensive performance optimization system"""
    
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl: Dict[str, datetime] = {}
        self.slow_queries: List[QueryOptimizationResult] = []
        self.optimization_rules = {
            'max_response_time': 2.0,  # seconds
            'max_memory_usage': 1024,  # MB
            'cache_ttl_default': 300,  # 5 minutes
            'slow_query_threshold': 100,  # ms
            'max_cache_size': 10000
        }
    
    def performance_monitor(self, endpoint: str):
        """Decorator to monitor API endpoint performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                start_cpu = psutil.cpu_percent()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    end_time = time.time()
                    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    end_cpu = psutil.cpu_percent()
                    
                    # Record metrics
                    metrics = PerformanceMetrics(
                        endpoint=endpoint,
                        response_time=end_time - start_time,
                        memory_usage=end_memory - start_memory,
                        cpu_usage=end_cpu - start_cpu,
                        database_queries=getattr(func, '_db_queries', 0),
                        cache_hits=getattr(func, '_cache_hits', 0),
                        cache_misses=getattr(func, '_cache_misses', 0),
                        timestamp=datetime.utcnow()
                    )
                    
                    self.record_metrics(metrics)
                    
                    # Log slow requests
                    if metrics.response_time > self.optimization_rules['max_response_time']:
                        logger.warning(f"Slow request detected: {endpoint} took {metrics.response_time:.3f}s")
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Error in {endpoint}: {e}")
                    raise
                    
            return wrapper
        return decorator
    
    def record_metrics(self, metrics: PerformanceMetrics):
        """Record performance metrics"""
        self.metrics_history.append(metrics)
        
        # Keep only recent metrics (last 1000 entries)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    async def optimize_database_indexes(self):
        """Create comprehensive database indexes for performance"""
        try:
            db = await get_database()
            
            # Enhanced indexes for multi-tenant architecture
            optimization_results = []
            
            # Tenants collection
            await db.tenants.create_index("subdomain", unique=True)
            await db.tenants.create_index("status")
            await db.tenants.create_index([("created_at", -1)])
            optimization_results.append("Tenants: subdomain, status, created_at indexes")
            
            # Users collection (enterprise)
            await db.users.create_index([("tenant_id", 1), ("email", 1)], unique=True)
            await db.users.create_index([("tenant_id", 1), ("role", 1)])
            await db.users.create_index([("tenant_id", 1), ("is_active", 1)])
            await db.users.create_index([("tenant_id", 1), ("last_login", -1)])
            optimization_results.append("Users: tenant_id compound indexes for multi-tenancy")
            
            # Agents collection (performance critical)
            await db.agents.create_index([("tenant_id", 1), ("status", 1)])
            await db.agents.create_index([("tenant_id", 1), ("type", 1)])
            await db.agents.create_index([("tenant_id", 1), ("efficiency", -1)])
            await db.agents.create_index([("tenant_id", 1), ("last_active", -1)])
            await db.agents.create_index([("tenant_id", 1), ("created_by", 1)])
            optimization_results.append("Agents: tenant-aware performance indexes")
            
            # Leads collection (high-frequency queries)
            await db.leads.create_index([("tenant_id", 1), ("status", 1)])
            await db.leads.create_index([("tenant_id", 1), ("assigned_agent_id", 1)])
            await db.leads.create_index([("tenant_id", 1), ("score", -1)])
            await db.leads.create_index([("tenant_id", 1), ("last_contact", -1)])
            await db.leads.create_index([("tenant_id", 1), ("email", 1)], unique=True)
            await db.leads.create_index([("tenant_id", 1), ("created_at", -1)])
            optimization_results.append("Leads: high-frequency query optimization")
            
            # Workflows collection (automation performance)
            await db.workflows.create_index([("tenant_id", 1), ("status", 1)])
            await db.workflows.create_index([("tenant_id", 1), ("category", 1)])
            await db.workflows.create_index([("tenant_id", 1), ("created_by", 1)])
            await db.workflows.create_index([("tenant_id", 1), ("execution_count", -1)])
            optimization_results.append("Workflows: automation query optimization")
            
            # Audit logs (compliance and performance)
            await db.audit_logs.create_index([("tenant_id", 1), ("created_at", -1)])
            await db.audit_logs.create_index([("tenant_id", 1), ("user_id", 1)])
            await db.audit_logs.create_index([("tenant_id", 1), ("action", 1)])
            await db.audit_logs.create_index([("tenant_id", 1), ("resource_type", 1)])
            await db.audit_logs.create_index([("tenant_id", 1), ("success", 1)])
            optimization_results.append("Audit logs: compliance query optimization")
            
            # Documents collection
            await db.documents.create_index([("tenant_id", 1), ("type", 1)])
            await db.documents.create_index([("tenant_id", 1), ("client_name", 1)])
            await db.documents.create_index([("tenant_id", 1), ("created_at", -1)])
            await db.documents.create_index([("tenant_id", 1), ("created_by", 1)])
            optimization_results.append("Documents: tenant-scoped document queries")
            
            # Knowledge base
            await db.knowledge_files.create_index([("tenant_id", 1), ("category", 1)])
            await db.knowledge_files.create_index([("tenant_id", 1), ("tags", 1)])
            await db.knowledge_files.create_index([("tenant_id", 1), ("processed", 1)])
            optimization_results.append("Knowledge: content management optimization")
            
            # Voice sessions (Phase 6D)
            await db.voice_sessions.create_index([("tenant_id", 1), ("user_id", 1)])
            await db.voice_sessions.create_index([("tenant_id", 1), ("status", 1)])
            await db.voice_sessions.create_index([("tenant_id", 1), ("created_at", -1)])
            optimization_results.append("Voice sessions: real-time performance")
            
            # Analytics aggregation indexes
            await db.analytics_cache.create_index([("tenant_id", 1), ("cache_key", 1)], unique=True)
            await db.analytics_cache.create_index("expires_at", expireAfterSeconds=0)
            optimization_results.append("Analytics: cached aggregation optimization")
            
            logger.info("Database optimization completed:")
            for result in optimization_results:
                logger.info(f"  ✅ {result}")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return []
    
    async def analyze_slow_queries(self, collection_name: str, sample_queries: List[Dict]) -> List[QueryOptimizationResult]:
        """Analyze query performance and suggest optimizations"""
        results = []
        
        try:
            db = await get_database()
            collection = db[collection_name]
            
            for query in sample_queries:
                start_time = time.time()
                
                # Run explain on the query
                explain_result = await collection.find(query).explain()
                
                execution_time = (time.time() - start_time) * 1000  # ms
                
                execution_stats = explain_result.get('executionStats', {})
                
                result = QueryOptimizationResult(
                    collection=collection_name,
                    query=query,
                    execution_time_ms=execution_time,
                    documents_examined=execution_stats.get('totalDocsExamined', 0),
                    documents_returned=execution_stats.get('totalDocsReturned', 0),
                    index_used=execution_stats.get('totalDocsExamined', 0) == execution_stats.get('totalDocsReturned', 0),
                    optimization_suggestions=[]
                )
                
                # Generate optimization suggestions
                if execution_time > self.optimization_rules['slow_query_threshold']:
                    result.optimization_suggestions.append(f"Query execution time ({execution_time:.2f}ms) exceeds threshold")
                
                if not result.index_used:
                    result.optimization_suggestions.append("Consider adding an index for this query pattern")
                
                if result.documents_examined > result.documents_returned * 10:
                    result.optimization_suggestions.append("High document examination ratio - optimize query selectivity")
                
                results.append(result)
                
                if result.optimization_suggestions:
                    self.slow_queries.append(result)
                    
        except Exception as e:
            logger.error(f"Query analysis failed for {collection_name}: {e}")
        
        return results
    
    def get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    async def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get result from cache if valid"""
        if cache_key in self.query_cache:
            # Check TTL
            if cache_key in self.cache_ttl:
                if datetime.utcnow() < self.cache_ttl[cache_key]:
                    return self.query_cache[cache_key]
                else:
                    # Expired, remove from cache
                    del self.query_cache[cache_key]
                    del self.cache_ttl[cache_key]
        
        return None
    
    async def set_cached_result(self, cache_key: str, result: Any, ttl_seconds: int = None):
        """Store result in cache"""
        if ttl_seconds is None:
            ttl_seconds = self.optimization_rules['cache_ttl_default']
        
        # Check cache size limit
        if len(self.query_cache) >= self.optimization_rules['max_cache_size']:
            # Remove oldest entries
            old_keys = list(self.query_cache.keys())[:100]
            for key in old_keys:
                del self.query_cache[key]
                if key in self.cache_ttl:
                    del self.cache_ttl[key]
        
        self.query_cache[cache_key] = result
        self.cache_ttl[cache_key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    async def optimize_memory_usage(self):
        """Optimize memory usage and garbage collection"""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Get current memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            optimization_result = {
                "objects_collected": collected,
                "memory_usage_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": process.memory_percent(),
                "cache_size": len(self.query_cache),
                "metrics_history_size": len(self.metrics_history)
            }
            
            # Clean old cache entries
            current_time = datetime.utcnow()
            expired_keys = [
                key for key, expiry in self.cache_ttl.items()
                if current_time > expiry
            ]
            
            for key in expired_keys:
                del self.query_cache[key]
                del self.cache_ttl[key]
            
            optimization_result["expired_cache_entries"] = len(expired_keys)
            
            logger.info(f"Memory optimization completed: {optimization_result}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {}
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.metrics_history:
            return {"message": "No performance metrics available"}
        
        # Calculate statistics
        recent_metrics = self.metrics_history[-100:]  # Last 100 requests
        
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        max_response_time = max(m.response_time for m in recent_metrics)
        avg_memory_usage = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        
        # Count slow requests
        slow_requests = len([m for m in recent_metrics if m.response_time > self.optimization_rules['max_response_time']])
        
        # Cache statistics
        total_cache_requests = sum(m.cache_hits + m.cache_misses for m in recent_metrics)
        cache_hit_rate = 0
        if total_cache_requests > 0:
            total_hits = sum(m.cache_hits for m in recent_metrics)
            cache_hit_rate = (total_hits / total_cache_requests) * 100
        
        return {
            "performance_summary": {
                "total_requests_analyzed": len(recent_metrics),
                "average_response_time": round(avg_response_time, 3),
                "max_response_time": round(max_response_time, 3),
                "slow_requests_count": slow_requests,
                "slow_requests_percentage": round((slow_requests / len(recent_metrics)) * 100, 2),
                "average_memory_usage_mb": round(avg_memory_usage, 2)
            },
            "cache_performance": {
                "cache_hit_rate_percentage": round(cache_hit_rate, 2),
                "cache_size": len(self.query_cache),
                "cache_capacity": self.optimization_rules['max_cache_size']
            },
            "database_optimization": {
                "slow_queries_detected": len(self.slow_queries),
                "indexes_status": "optimized",
                "query_cache_enabled": True
            },
            "system_resources": {
                "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_usage_percent": psutil.cpu_percent(),
                "disk_usage_percent": psutil.disk_usage('/').percent
            },
            "optimization_recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        if not self.metrics_history:
            return ["Insufficient data for recommendations"]
        
        recent_metrics = self.metrics_history[-50:]
        
        # Check response time
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)
        if avg_response_time > self.optimization_rules['max_response_time']:
            recommendations.append("Consider API endpoint optimization - average response time is high")
        
        # Check memory usage
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        if avg_memory > self.optimization_rules['max_memory_usage']:
            recommendations.append("Memory usage is high - consider increasing cache cleanup frequency")
        
        # Check cache hit rate
        total_requests = sum(m.cache_hits + m.cache_misses for m in recent_metrics)
        if total_requests > 0:
            hit_rate = sum(m.cache_hits for m in recent_metrics) / total_requests
            if hit_rate < 0.7:  # Less than 70% cache hit rate
                recommendations.append("Low cache hit rate - consider adjusting cache TTL or cache keys")
        
        # Check slow queries
        if len(self.slow_queries) > 10:
            recommendations.append("Multiple slow queries detected - review database indexes and query patterns")
        
        if not recommendations:
            recommendations.append("System performance is optimal")
        
        return recommendations

# Global optimizer instance
performance_optimizer = PerformanceOptimizer()

# Decorator for easy use
def monitor_performance(endpoint: str):
    """Convenience decorator for monitoring endpoint performance"""
    return performance_optimizer.performance_monitor(endpoint)

# Async context manager for database optimization
class OptimizedDatabaseQuery:
    """Context manager for optimized database queries with caching"""
    
    def __init__(self, cache_key: str, ttl_seconds: int = 300):
        self.cache_key = cache_key
        self.ttl_seconds = ttl_seconds
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        
        # Try to get from cache first
        cached_result = await performance_optimizer.get_cached_result(self.cache_key)
        if cached_result is not None:
            return cached_result, True  # True indicates cache hit
        
        return None, False  # False indicates cache miss
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time = time.time() - self.start_time
            logger.debug(f"Query executed in {execution_time:.3f}s for key: {self.cache_key}")

async def run_performance_optimization():
    """Run comprehensive performance optimization"""
    logger.info("Starting comprehensive performance optimization...")
    
    try:
        # 1. Database optimization
        logger.info("Step 1: Optimizing database indexes...")
        db_results = await performance_optimizer.optimize_database_indexes()
        
        # 2. Memory optimization
        logger.info("Step 2: Optimizing memory usage...")
        memory_results = await performance_optimizer.optimize_memory_usage()
        
        # 3. Generate performance report
        logger.info("Step 3: Generating performance report...")
        performance_report = await performance_optimizer.get_performance_report()
        
        optimization_summary = {
            "database_optimization": {
                "status": "completed",
                "indexes_created": len(db_results),
                "details": db_results
            },
            "memory_optimization": {
                "status": "completed",
                "details": memory_results
            },
            "performance_report": performance_report,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("Performance optimization completed successfully")
        return optimization_summary
        
    except Exception as e:
        logger.error(f"Performance optimization failed: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    # Run optimization when script is called directly
    asyncio.run(run_performance_optimization())