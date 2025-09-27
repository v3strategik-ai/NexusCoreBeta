#!/usr/bin/env python3
"""
Phase 7: API Rate Limiting System
Per-tenant/user rate limiting with comprehensive quota management and scaling protection
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import redis.asyncio as redis
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import os
import json

logger = logging.getLogger(__name__)

class RateLimitTier(Enum):
    """Rate limiting tiers based on subscription plans"""
    TRIAL = "trial"
    STANDARD = "standard" 
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

@dataclass
class RateLimitConfig:
    """Rate limit configuration for different tiers"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_capacity: int
    concurrent_requests: int

@dataclass
class RateLimitStatus:
    """Current rate limit status for a client"""
    requests_this_minute: int = 0
    requests_this_hour: int = 0
    requests_this_day: int = 0
    current_concurrent: int = 0
    reset_times: Dict[str, datetime] = field(default_factory=dict)
    blocked_until: Optional[datetime] = None
    violations: int = 0

class RateLimitExceededException(HTTPException):
    """Custom exception for rate limit exceeded"""
    
    def __init__(self, limit_type: str, retry_after: int, headers: Dict[str, str]):
        super().__init__(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit_type": limit_type,
                "retry_after_seconds": retry_after,
                "message": f"Too many requests. Try again in {retry_after} seconds."
            },
            headers=headers
        )

class RateLimiter:
    """Comprehensive rate limiting system with Redis backend"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self.fallback_storage: Dict[str, RateLimitStatus] = {}
        self.use_redis = True
        
        # Rate limit configurations by tier
        self.tier_configs = {
            RateLimitTier.TRIAL: RateLimitConfig(
                requests_per_minute=50,
                requests_per_hour=500,
                requests_per_day=2000,
                burst_capacity=10,
                concurrent_requests=5
            ),
            RateLimitTier.STANDARD: RateLimitConfig(
                requests_per_minute=200,
                requests_per_hour=2000,
                requests_per_day=10000,
                burst_capacity=25,
                concurrent_requests=15
            ),
            RateLimitTier.PROFESSIONAL: RateLimitConfig(
                requests_per_minute=500,
                requests_per_hour=5000,
                requests_per_day=50000,
                burst_capacity=50,
                concurrent_requests=30
            ),
            RateLimitTier.ENTERPRISE: RateLimitConfig(
                requests_per_minute=2000,
                requests_per_hour=20000,
                requests_per_day=200000,
                burst_capacity=100,
                concurrent_requests=100
            )
        }
        
        # Endpoint-specific multipliers
        self.endpoint_multipliers = {
            # High-cost AI operations
            '/api/ai-content/generate': 5,
            '/api/lead-scoring/score': 3,
            '/api/sentiment/analyze': 3,
            '/api/nl-workflows/create-from-description': 4,
            '/api/advanced-voice/realtime-chat': 10,
            
            # Medium-cost operations
            '/api/analytics/dashboard-summary': 2,
            '/api/data-export/create-job': 2,
            '/api/workflows/execute': 2,
            
            # Standard operations (1x - default)
            '/api/leads': 1,
            '/api/agents': 1,
            '/api/users': 1,
            '/api/tenants': 1
        }
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            await self.redis_client.ping()
            self.use_redis = True
            logger.info("Rate limiter initialized with Redis backend")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis, using in-memory fallback: {e}")
            self.use_redis = False
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def get_client_key(self, request: Request) -> str:
        """Generate client key from request (tenant_id or user_id)"""
        # Try to get tenant_id from headers, query params, or JWT token
        tenant_id = (
            request.headers.get('x-tenant-id') or
            request.query_params.get('tenant_id') or
            getattr(request.state, 'tenant_id', None)
        )
        
        user_id = (
            request.headers.get('x-user-id') or
            request.query_params.get('user_id') or
            getattr(request.state, 'user_id', None)
        )
        
        # Prefer tenant-based limiting, fallback to user, then IP
        if tenant_id:
            return f"tenant:{tenant_id}"
        elif user_id:
            return f"user:{user_id}"
        else:
            # Fallback to IP-based limiting
            return f"ip:{request.client.host}"
    
    def get_client_tier(self, request: Request) -> RateLimitTier:
        """Determine client's rate limiting tier"""
        tier = (
            request.headers.get('x-subscription-tier') or
            getattr(request.state, 'subscription_tier', None)
        )
        
        try:
            if tier:
                return RateLimitTier(tier.lower())
        except ValueError:
            pass
        
        # Default to trial tier
        return RateLimitTier.TRIAL
    
    def get_endpoint_cost(self, endpoint: str) -> int:
        """Get cost multiplier for endpoint"""
        # Find best match for endpoint
        for pattern, cost in self.endpoint_multipliers.items():
            if endpoint.startswith(pattern):
                return cost
        return 1  # Default cost
    
    async def _get_rate_limit_status(self, client_key: str) -> RateLimitStatus:
        """Get current rate limit status from storage"""
        if self.use_redis and self.redis_client:
            try:
                data = await self.redis_client.hgetall(f"ratelimit:{client_key}")
                if data:
                    status = RateLimitStatus(
                        requests_this_minute=int(data.get('requests_this_minute', 0)),
                        requests_this_hour=int(data.get('requests_this_hour', 0)),
                        requests_this_day=int(data.get('requests_this_day', 0)),
                        current_concurrent=int(data.get('current_concurrent', 0)),
                        violations=int(data.get('violations', 0))
                    )
                    
                    # Parse reset times
                    if 'reset_times' in data:
                        reset_data = json.loads(data['reset_times'])
                        status.reset_times = {
                            k: datetime.fromisoformat(v) for k, v in reset_data.items()
                        }
                    
                    # Parse blocked until
                    if 'blocked_until' in data and data['blocked_until']:
                        status.blocked_until = datetime.fromisoformat(data['blocked_until'])
                    
                    return status
            except Exception as e:
                logger.error(f"Redis error getting rate limit status: {e}")
                # Fall back to in-memory storage
                pass
        
        # Use in-memory storage
        return self.fallback_storage.get(client_key, RateLimitStatus())
    
    async def _set_rate_limit_status(self, client_key: str, status: RateLimitStatus):
        """Save rate limit status to storage"""
        if self.use_redis and self.redis_client:
            try:
                data = {
                    'requests_this_minute': status.requests_this_minute,
                    'requests_this_hour': status.requests_this_hour,
                    'requests_this_day': status.requests_this_day,
                    'current_concurrent': status.current_concurrent,
                    'violations': status.violations,
                    'reset_times': json.dumps({
                        k: v.isoformat() for k, v in status.reset_times.items()
                    })
                }
                
                if status.blocked_until:
                    data['blocked_until'] = status.blocked_until.isoformat()
                
                await self.redis_client.hset(f"ratelimit:{client_key}", mapping=data)
                await self.redis_client.expire(f"ratelimit:{client_key}", 86400)  # 24 hours
                return
            except Exception as e:
                logger.error(f"Redis error setting rate limit status: {e}")
                # Fall back to in-memory storage
                pass
        
        # Use in-memory storage
        self.fallback_storage[client_key] = status
    
    def _reset_counters(self, status: RateLimitStatus, current_time: datetime):
        """Reset counters based on time windows"""
        now = current_time
        
        # Reset minute counter
        minute_reset = status.reset_times.get('minute')
        if not minute_reset or now >= minute_reset:
            status.requests_this_minute = 0
            status.reset_times['minute'] = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Reset hour counter
        hour_reset = status.reset_times.get('hour')
        if not hour_reset or now >= hour_reset:
            status.requests_this_hour = 0
            status.reset_times['hour'] = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        # Reset day counter
        day_reset = status.reset_times.get('day')
        if not day_reset or now >= day_reset:
            status.requests_this_day = 0
            status.reset_times['day'] = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    def _calculate_retry_after(self, status: RateLimitStatus, config: RateLimitConfig) -> int:
        """Calculate retry after seconds"""
        now = datetime.utcnow()
        
        # If blocked, return time until block expires
        if status.blocked_until and now < status.blocked_until:
            return int((status.blocked_until - now).total_seconds())
        
        # Return time until next reset window
        retry_times = []
        
        if status.requests_this_minute >= config.requests_per_minute:
            minute_reset = status.reset_times.get('minute', now + timedelta(minutes=1))
            retry_times.append(int((minute_reset - now).total_seconds()))
        
        if status.requests_this_hour >= config.requests_per_hour:
            hour_reset = status.reset_times.get('hour', now + timedelta(hours=1))
            retry_times.append(int((hour_reset - now).total_seconds()))
        
        if status.requests_this_day >= config.requests_per_day:
            day_reset = status.reset_times.get('day', now + timedelta(days=1))
            retry_times.append(int((day_reset - now).total_seconds()))
        
        return min(retry_times) if retry_times else 60
    
    def _create_rate_limit_headers(self, config: RateLimitConfig, status: RateLimitStatus) -> Dict[str, str]:
        """Create rate limit headers"""
        return {
            'X-RateLimit-Limit-Minute': str(config.requests_per_minute),
            'X-RateLimit-Limit-Hour': str(config.requests_per_hour),
            'X-RateLimit-Limit-Day': str(config.requests_per_day),
            'X-RateLimit-Remaining-Minute': str(max(0, config.requests_per_minute - status.requests_this_minute)),
            'X-RateLimit-Remaining-Hour': str(max(0, config.requests_per_hour - status.requests_this_hour)),
            'X-RateLimit-Remaining-Day': str(max(0, config.requests_per_day - status.requests_this_day)),
            'X-RateLimit-Reset-Minute': str(int(status.reset_times.get('minute', datetime.utcnow()).timestamp())),
            'X-RateLimit-Reset-Hour': str(int(status.reset_times.get('hour', datetime.utcnow()).timestamp())),
            'X-RateLimit-Reset-Day': str(int(status.reset_times.get('day', datetime.utcnow()).timestamp()))
        }
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, str]]:
        """Check if request is within rate limits"""
        client_key = self.get_client_key(request)
        client_tier = self.get_client_tier(request)
        config = self.tier_configs[client_tier]
        
        # Get endpoint cost
        endpoint = request.url.path
        cost = self.get_endpoint_cost(endpoint)
        
        current_time = datetime.utcnow()
        status = await self._get_rate_limit_status(client_key)
        
        # Reset counters if needed
        self._reset_counters(status, current_time)
        
        # Check if client is blocked
        if status.blocked_until and current_time < status.blocked_until:
            retry_after = int((status.blocked_until - current_time).total_seconds())
            headers = self._create_rate_limit_headers(config, status)
            headers['Retry-After'] = str(retry_after)
            raise RateLimitExceededException("blocked", retry_after, headers)
        
        # Check concurrent requests
        if status.current_concurrent >= config.concurrent_requests:
            retry_after = 5  # Short retry for concurrent limit
            headers = self._create_rate_limit_headers(config, status)
            headers['Retry-After'] = str(retry_after)
            raise RateLimitExceededException("concurrent", retry_after, headers)
        
        # Check rate limits (apply cost multiplier)
        effective_cost = cost
        
        # Check minute limit
        if status.requests_this_minute + effective_cost > config.requests_per_minute:
            retry_after = self._calculate_retry_after(status, config)
            headers = self._create_rate_limit_headers(config, status)
            headers['Retry-After'] = str(retry_after)
            
            # Increment violation counter
            status.violations += 1
            
            # Block repeat violators
            if status.violations >= 5:
                status.blocked_until = current_time + timedelta(minutes=15)
                await self._set_rate_limit_status(client_key, status)
                logger.warning(f"Client {client_key} blocked for 15 minutes due to repeated violations")
                raise RateLimitExceededException("blocked", 900, headers)
            
            await self._set_rate_limit_status(client_key, status)
            raise RateLimitExceededException("minute", retry_after, headers)
        
        # Check hour limit
        if status.requests_this_hour + effective_cost > config.requests_per_hour:
            retry_after = self._calculate_retry_after(status, config)
            headers = self._create_rate_limit_headers(config, status)
            headers['Retry-After'] = str(retry_after)
            await self._set_rate_limit_status(client_key, status)
            raise RateLimitExceededException("hour", retry_after, headers)
        
        # Check day limit
        if status.requests_this_day + effective_cost > config.requests_per_day:
            retry_after = self._calculate_retry_after(status, config)
            headers = self._create_rate_limit_headers(config, status)
            headers['Retry-After'] = str(retry_after)
            await self._set_rate_limit_status(client_key, status)
            raise RateLimitExceededException("day", retry_after, headers)
        
        # Request is allowed - increment counters
        status.requests_this_minute += effective_cost
        status.requests_this_hour += effective_cost
        status.requests_this_day += effective_cost
        status.current_concurrent += 1
        
        await self._set_rate_limit_status(client_key, status)
        
        headers = self._create_rate_limit_headers(config, status)
        return True, headers
    
    async def release_concurrent_slot(self, request: Request):
        """Release concurrent request slot after request completion"""
        client_key = self.get_client_key(request)
        status = await self._get_rate_limit_status(client_key)
        
        if status.current_concurrent > 0:
            status.current_concurrent -= 1
            await self._set_rate_limit_status(client_key, status)
    
    async def get_rate_limit_stats(self, client_key: str = None) -> Dict[str, Any]:
        """Get rate limiting statistics"""
        if client_key:
            status = await self._get_rate_limit_status(client_key)
            return {
                "client_key": client_key,
                "requests_this_minute": status.requests_this_minute,
                "requests_this_hour": status.requests_this_hour,
                "requests_this_day": status.requests_this_day,
                "current_concurrent": status.current_concurrent,
                "violations": status.violations,
                "blocked_until": status.blocked_until.isoformat() if status.blocked_until else None,
                "reset_times": {
                    k: v.isoformat() for k, v in status.reset_times.items()
                }
            }
        else:
            # Global statistics
            total_clients = len(self.fallback_storage) if not self.use_redis else "unknown"
            return {
                "total_tracked_clients": total_clients,
                "storage_backend": "redis" if self.use_redis else "memory",
                "tier_configurations": {
                    tier.value: {
                        "requests_per_minute": config.requests_per_minute,
                        "requests_per_hour": config.requests_per_hour,
                        "requests_per_day": config.requests_per_day,
                        "burst_capacity": config.burst_capacity,
                        "concurrent_requests": config.concurrent_requests
                    }
                    for tier, config in self.tier_configs.items()
                },
                "endpoint_costs": self.endpoint_multipliers
            }

# Global rate limiter instance
rate_limiter = RateLimiter()

async def setup_rate_limiter():
    """Setup rate limiter (call on startup)"""
    await rate_limiter.initialize()

async def cleanup_rate_limiter():
    """Cleanup rate limiter (call on shutdown)"""
    await rate_limiter.close()