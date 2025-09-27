#!/usr/bin/env python3
"""
Phase 7: Rate Limiting Middleware
FastAPI middleware for automatic rate limiting with comprehensive request tracking
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

from rate_limiter import rate_limiter, RateLimitExceededException

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/health",
            "/api/performance/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        try:
            # Check rate limits
            allowed, headers = await rate_limiter.check_rate_limit(request)
            
            if allowed:
                # Process request
                start_time = time.time()
                response = await call_next(request)
                processing_time = time.time() - start_time
                
                # Add rate limit headers to response
                for header_name, header_value in headers.items():
                    response.headers[header_name] = header_value
                
                # Add performance headers
                response.headers["X-Processing-Time"] = f"{processing_time:.3f}"
                
                # Release concurrent slot
                await rate_limiter.release_concurrent_slot(request)
                
                return response
            
        except RateLimitExceededException as e:
            # Rate limit exceeded - return 429 with proper headers
            logger.warning(f"Rate limit exceeded for {rate_limiter.get_client_key(request)}: {e.detail}")
            
            return JSONResponse(
                status_code=e.status_code,
                content=e.detail,
                headers=e.headers
            )
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Continue without rate limiting if there's an error
            response = await call_next(request)
            response.headers["X-RateLimit-Error"] = "Rate limiting temporarily unavailable"
            return response