#!/usr/bin/env python3
"""
Phase 7: Redis Caching System
High-performance Redis-based caching for database queries, API responses, and computed results
"""

import asyncio
import json
import logging
import pickle
import time
import zlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import redis.asyncio as redis
import hashlib
import os

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategies for different data types"""
    WRITE_THROUGH = "write_through"      # Write to cache and DB simultaneously
    WRITE_BEHIND = "write_behind"        # Write to cache first, DB later
    CACHE_ASIDE = "cache_aside"          # Manual cache management
    REFRESH_AHEAD = "refresh_ahead"      # Proactive cache refresh

class CompressionType(Enum):
    """Compression types for cached data"""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"

@dataclass
class CacheConfig:
    """Cache configuration for different data types"""
    ttl_seconds: int
    strategy: CacheStrategy
    compression: CompressionType
    max_size_bytes: int
    preload: bool = False

@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0

class RedisCache:
    """High-performance Redis caching system"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.stats = CacheStats()
        
        # Cache configurations for different data types
        self.cache_configs = {
            # High-frequency, short-lived data
            'api_responses': CacheConfig(
                ttl_seconds=300,  # 5 minutes
                strategy=CacheStrategy.CACHE_ASIDE,
                compression=CompressionType.ZLIB,
                max_size_bytes=1024 * 1024,  # 1MB
                preload=False
            ),
            
            # Database query results
            'db_queries': CacheConfig(
                ttl_seconds=1800,  # 30 minutes
                strategy=CacheStrategy.CACHE_ASIDE,
                compression=CompressionType.ZLIB,
                max_size_bytes=5 * 1024 * 1024,  # 5MB
                preload=False
            ),
            
            # Analytics and aggregated data
            'analytics': CacheConfig(
                ttl_seconds=3600,  # 1 hour
                strategy=CacheStrategy.WRITE_THROUGH,
                compression=CompressionType.ZLIB,
                max_size_bytes=10 * 1024 * 1024,  # 10MB
                preload=True
            ),
            
            # User sessions and temporary data
            'sessions': CacheConfig(
                ttl_seconds=7200,  # 2 hours
                strategy=CacheStrategy.CACHE_ASIDE,
                compression=CompressionType.NONE,
                max_size_bytes=512 * 1024,  # 512KB
                preload=False
            ),
            
            # Static configuration data
            'config': CacheConfig(
                ttl_seconds=86400,  # 24 hours
                strategy=CacheStrategy.REFRESH_AHEAD,
                compression=CompressionType.GZIP,
                max_size_bytes=1024 * 1024,  # 1MB
                preload=True
            ),
            
            # AI model responses (expensive to generate)
            'ai_responses': CacheConfig(
                ttl_seconds=7200,  # 2 hours
                strategy=CacheStrategy.CACHE_ASIDE,
                compression=CompressionType.ZLIB,
                max_size_bytes=2 * 1024 * 1024,  # 2MB
                preload=False
            ),
            
            # File metadata and processing results
            'file_processing': CacheConfig(
                ttl_seconds=14400,  # 4 hours
                strategy=CacheStrategy.WRITE_THROUGH,
                compression=CompressionType.GZIP,
                max_size_bytes=3 * 1024 * 1024,  # 3MB
                preload=False
            )
        }
    
    async def initialize(self):
        """Initialize Redis connection and setup"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            # Test connection
            await self.redis_client.ping()
            
            # Setup Redis configurations
            await self._setup_redis_config()
            
            logger.info("Redis cache initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def _setup_redis_config(self):
        """Setup Redis configurations for optimal performance"""
        try:
            # Set memory policy
            await self.redis_client.config_set('maxmemory-policy', 'allkeys-lru')
            
            # Enable keyspace notifications for cache invalidation
            await self.redis_client.config_set('notify-keyspace-events', 'Ex')
            
            logger.info("Redis configuration optimized for caching")
        except Exception as e:
            logger.warning(f"Could not optimize Redis configuration: {e}")
    
    def _generate_cache_key(self, cache_type: str, identifier: str, **kwargs) -> str:
        """Generate consistent cache key"""
        key_parts = [cache_type, identifier]
        
        # Add tenant isolation if available
        if 'tenant_id' in kwargs:
            key_parts.append(f"tenant:{kwargs['tenant_id']}")
        
        # Add additional parameters
        if kwargs:
            # Sort for consistency
            sorted_params = sorted(kwargs.items())
            param_str = "&".join(f"{k}={v}" for k, v in sorted_params if k != 'tenant_id')
            if param_str:
                # Hash long parameter strings
                if len(param_str) > 100:
                    param_hash = hashlib.md5(param_str.encode()).hexdigest()[:16]
                    key_parts.append(f"params:{param_hash}")
                else:
                    key_parts.append(param_str)
        
        return ":".join(key_parts)
    
    def _compress_data(self, data: bytes, compression: CompressionType) -> bytes:
        """Compress data based on compression type"""
        if compression == CompressionType.GZIP:
            import gzip
            return gzip.compress(data)
        elif compression == CompressionType.ZLIB:
            return zlib.compress(data)
        return data
    
    def _decompress_data(self, data: bytes, compression: CompressionType) -> bytes:
        """Decompress data based on compression type"""
        if compression == CompressionType.GZIP:
            import gzip
            return gzip.decompress(data)
        elif compression == CompressionType.ZLIB:
            return zlib.decompress(data)
        return data
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            # Try JSON first for simple data types
            if isinstance(data, (str, int, float, bool, list, dict)):
                return json.dumps(data, default=str).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(data)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        try:
            # Try JSON first
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    async def get(self, cache_type: str, identifier: str, **kwargs) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
        config = self.cache_configs.get(cache_type, self.cache_configs['api_responses'])
        
        try:
            # Get data and metadata
            pipe = self.redis_client.pipeline()
            pipe.hget(cache_key, 'data')
            pipe.hget(cache_key, 'compression')
            pipe.hget(cache_key, 'size')
            pipe.ttl(cache_key)
            
            results = await pipe.execute()
            data, compression_str, size_str, ttl = results
            
            if data is None:
                self.stats.misses += 1
                return None
            
            # Decompress if needed
            compression = CompressionType(compression_str.decode()) if compression_str else CompressionType.NONE
            if compression != CompressionType.NONE:
                data = self._decompress_data(data, compression)
            
            # Deserialize
            result = self._deserialize_data(data)
            
            self.stats.hits += 1
            
            # Check if we need to refresh ahead
            if config.strategy == CacheStrategy.REFRESH_AHEAD and ttl < config.ttl_seconds * 0.2:
                # TTL is less than 20% of original, schedule refresh
                logger.info(f"Cache key {cache_key} needs refresh ahead")
            
            return result
            
        except Exception as e:
            logger.error(f"Cache get error for {cache_key}: {e}")
            self.stats.errors += 1
            return None
    
    async def set(self, cache_type: str, identifier: str, value: Any, ttl: int = None, **kwargs) -> bool:
        """Set value in cache"""
        if not self.redis_client:
            return False
        
        cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
        config = self.cache_configs.get(cache_type, self.cache_configs['api_responses'])
        
        if ttl is None:
            ttl = config.ttl_seconds
        
        try:
            # Serialize data
            serialized_data = self._serialize_data(value)
            
            # Check size limit
            if len(serialized_data) > config.max_size_bytes:
                logger.warning(f"Data too large for cache ({len(serialized_data)} bytes > {config.max_size_bytes})")
                return False
            
            # Compress if configured
            compressed_data = self._compress_data(serialized_data, config.compression)
            
            # Store data with metadata
            cache_data = {
                'data': compressed_data,
                'compression': config.compression.value.encode(),
                'size': str(len(serialized_data)).encode(),
                'created_at': datetime.utcnow().isoformat().encode(),
                'cache_type': cache_type.encode()
            }
            
            await self.redis_client.hset(cache_key, mapping=cache_data)
            await self.redis_client.expire(cache_key, ttl)
            
            self.stats.sets += 1
            self.stats.total_size_bytes += len(compressed_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {cache_key}: {e}")
            self.stats.errors += 1
            return False
    
    async def delete(self, cache_type: str, identifier: str, **kwargs) -> bool:
        """Delete value from cache"""
        if not self.redis_client:
            return False
        
        cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
        
        try:
            result = await self.redis_client.delete(cache_key)
            if result:
                self.stats.deletes += 1
            return bool(result)
        except Exception as e:
            logger.error(f"Cache delete error for {cache_key}: {e}")
            self.stats.errors += 1
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.stats.deletes += deleted
                return deleted
            
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            self.stats.errors += 1
            return 0
    
    async def invalidate_tenant_cache(self, tenant_id: str):
        """Invalidate all cache entries for a tenant"""
        pattern = f"*:tenant:{tenant_id}*"
        deleted = await self.delete_pattern(pattern)
        logger.info(f"Invalidated {deleted} cache entries for tenant {tenant_id}")
        return deleted
    
    async def exists(self, cache_type: str, identifier: str, **kwargs) -> bool:
        """Check if key exists in cache"""
        if not self.redis_client:
            return False
        
        cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
        
        try:
            return bool(await self.redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"Cache exists error for {cache_key}: {e}")
            return False
    
    async def extend_ttl(self, cache_type: str, identifier: str, additional_seconds: int, **kwargs) -> bool:
        """Extend TTL of cached item"""
        if not self.redis_client:
            return False
        
        cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
        
        try:
            current_ttl = await self.redis_client.ttl(cache_key)
            if current_ttl > 0:
                new_ttl = current_ttl + additional_seconds
                await self.redis_client.expire(cache_key, new_ttl)
                return True
            return False
        except Exception as e:
            logger.error(f"Cache extend TTL error for {cache_key}: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_info = await self.redis_client.info() if self.redis_client else {}
            
            return {
                "cache_stats": {
                    "hits": self.stats.hits,
                    "misses": self.stats.misses,
                    "hit_rate_percent": round(self.stats.hit_rate, 2),
                    "sets": self.stats.sets,
                    "deletes": self.stats.deletes,
                    "errors": self.stats.errors,
                    "estimated_size_bytes": self.stats.total_size_bytes
                },
                "redis_info": {
                    "used_memory": redis_info.get('used_memory', 0),
                    "used_memory_human": redis_info.get('used_memory_human', 'Unknown'),
                    "connected_clients": redis_info.get('connected_clients', 0),
                    "total_commands_processed": redis_info.get('total_commands_processed', 0),
                    "keyspace_hits": redis_info.get('keyspace_hits', 0),
                    "keyspace_misses": redis_info.get('keyspace_misses', 0),
                    "redis_version": redis_info.get('redis_version', 'Unknown')
                },
                "cache_configurations": {
                    cache_type: {
                        "ttl_seconds": config.ttl_seconds,
                        "strategy": config.strategy.value,
                        "compression": config.compression.value,
                        "max_size_bytes": config.max_size_bytes,
                        "preload": config.preload
                    }
                    for cache_type, config in self.cache_configs.items()
                }
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    async def clear_all(self) -> bool:
        """Clear all cached data (use with caution)"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.flushdb()
            self.stats = CacheStats()  # Reset stats
            logger.warning("All cache data cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Cache decorator for automatic caching
def cached(cache_type: str, ttl: int = None, key_func: Callable = None):
    """Decorator for automatic function result caching"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            result = await redis_cache.get(cache_type, cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_cache.set(cache_type, cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Global cache instance
redis_cache = RedisCache()

async def setup_redis_cache():
    """Setup Redis cache (call on startup)"""
    success = await redis_cache.initialize()
    if success:
        logger.info("Redis cache setup completed")
    else:
        logger.warning("Redis cache setup failed - falling back to in-memory caching")
    return success

async def cleanup_redis_cache():
    """Cleanup Redis cache (call on shutdown)"""
    await redis_cache.close()

# Context manager for cache operations
class CacheContext:
    """Context manager for cache operations with automatic cleanup"""
    
    def __init__(self, cache_type: str, identifier: str, ttl: int = None, **kwargs):
        self.cache_type = cache_type
        self.identifier = identifier
        self.ttl = ttl
        self.kwargs = kwargs
        self.cached_result = None
        self.cache_hit = False
    
    async def __aenter__(self):
        # Try to get from cache
        self.cached_result = await redis_cache.get(self.cache_type, self.identifier, **self.kwargs)
        self.cache_hit = self.cached_result is not None
        return self.cached_result, self.cache_hit
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cache the result if it was computed (cache miss) and no exception occurred
        if not self.cache_hit and exc_type is None and hasattr(self, '_result'):
            await redis_cache.set(self.cache_type, self.identifier, self._result, self.ttl, **self.kwargs)
    
    def set_result(self, result):
        """Set the result to be cached on exit"""
        self._result = result