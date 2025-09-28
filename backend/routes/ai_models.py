#!/usr/bin/env python3
"""
Phase 8A: Advanced AI & Automation - Multi-Model AI Integration
Intelligent AI model router with GPT-5, Claude Sonnet 4, and Gemini 2.0 Pro support
"""

import asyncio
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum

from database import get_database
from emergentintegrations.llm.chat import LlmChat, UserMessage
import dotenv

# Load environment variables
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

class AIProvider(str, Enum):
    """AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"

class AIModel(str, Enum):
    """Available AI models"""
    # OpenAI Models
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    O1 = "o1"
    O1_MINI = "o1-mini"
    
    # Anthropic Models
    CLAUDE_4_SONNET = "claude-4-sonnet-20250514"
    CLAUDE_4_OPUS = "claude-4-opus-20250514"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-20250219"
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022"
    
    # Google Models
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"

class TaskType(str, Enum):
    """Types of AI tasks for intelligent routing"""
    REASONING = "reasoning"           # Complex logical reasoning
    CREATIVE = "creative"            # Creative writing, content generation
    ANALYSIS = "analysis"            # Data analysis, research
    CODING = "coding"               # Programming, technical tasks
    CONVERSATION = "conversation"    # General chat, customer service
    TRANSLATION = "translation"     # Language translation
    SUMMARIZATION = "summarization" # Content summarization
    CLASSIFICATION = "classification" # Text classification, sentiment
    FORECASTING = "forecasting"     # Business forecasting
    MULTIMODAL = "multimodal"       # Text + image/voice processing

@dataclass
class ModelCapabilities:
    """AI model capabilities and performance metrics"""
    reasoning_score: float      # 0-1 rating for logical reasoning
    creativity_score: float     # 0-1 rating for creative tasks
    speed_score: float         # 0-1 rating for response speed
    cost_score: float          # 0-1 rating for cost efficiency (higher = cheaper)
    context_length: int        # Maximum context length
    multimodal: bool          # Supports images/voice
    specialties: List[TaskType] # Task types this model excels at

@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    model_used: str
    provider: str
    processing_time: float
    token_count: Optional[int] = None
    cost_estimate: Optional[float] = None
    confidence_score: Optional[float] = None

# Request/Response Models
class AIRequest(BaseModel):
    """Request for AI model processing"""
    message: str
    task_type: Optional[TaskType] = TaskType.CONVERSATION
    preferred_model: Optional[AIModel] = None
    preferred_provider: Optional[AIProvider] = None
    system_message: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096)
    enable_comparison: bool = False  # Compare multiple models
    session_id: Optional[str] = None

class ModelComparisonRequest(BaseModel):
    """Request for comparing multiple AI models"""
    message: str
    task_type: TaskType = TaskType.CONVERSATION
    models: List[AIModel] = Field(min_items=2, max_items=5)
    system_message: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class ModelPerformanceMetrics(BaseModel):
    """Model performance tracking"""
    model: str
    provider: str
    task_type: str
    response_time: float
    token_count: int
    cost_estimate: float
    success_rate: float
    user_rating: Optional[float] = None

# Router
router = APIRouter(prefix="/ai-models", tags=["Advanced AI Models"])

class AIModelRouter:
    """Intelligent AI model router with multi-model support"""
    
    def __init__(self):
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY not found in environment variables")
        
        # Model capabilities mapping
        self.model_capabilities = {
            # OpenAI GPT-5 - Best for complex reasoning
            AIModel.GPT_5: ModelCapabilities(
                reasoning_score=0.95, creativity_score=0.90, speed_score=0.70, cost_score=0.30,
                context_length=128000, multimodal=True,
                specialties=[TaskType.REASONING, TaskType.CODING, TaskType.ANALYSIS, TaskType.FORECASTING]
            ),
            
            # GPT-5 Mini - Balanced performance
            AIModel.GPT_5_MINI: ModelCapabilities(
                reasoning_score=0.85, creativity_score=0.80, speed_score=0.85, cost_score=0.70,
                context_length=128000, multimodal=True,
                specialties=[TaskType.CONVERSATION, TaskType.CLASSIFICATION, TaskType.SUMMARIZATION]
            ),
            
            # Claude 4 Sonnet - Best for creative and analysis tasks
            AIModel.CLAUDE_4_SONNET: ModelCapabilities(
                reasoning_score=0.90, creativity_score=0.95, speed_score=0.75, cost_score=0.40,
                context_length=200000, multimodal=True,
                specialties=[TaskType.CREATIVE, TaskType.ANALYSIS, TaskType.CONVERSATION]
            ),
            
            # Claude 4 Opus - Premium reasoning and creativity
            AIModel.CLAUDE_4_OPUS: ModelCapabilities(
                reasoning_score=0.98, creativity_score=0.98, speed_score=0.60, cost_score=0.20,
                context_length=200000, multimodal=True,
                specialties=[TaskType.REASONING, TaskType.CREATIVE, TaskType.CODING]
            ),
            
            # Gemini 2.5 Pro - Best for multimodal and analysis
            AIModel.GEMINI_2_5_PRO: ModelCapabilities(
                reasoning_score=0.88, creativity_score=0.85, speed_score=0.80, cost_score=0.50,
                context_length=1000000, multimodal=True,
                specialties=[TaskType.MULTIMODAL, TaskType.ANALYSIS, TaskType.TRANSLATION]
            ),
            
            # O1 - Specialized reasoning model
            AIModel.O1: ModelCapabilities(
                reasoning_score=0.99, creativity_score=0.70, speed_score=0.40, cost_score=0.25,
                context_length=128000, multimodal=False,
                specialties=[TaskType.REASONING, TaskType.CODING, TaskType.FORECASTING]
            )
        }
        
        # Task-to-model routing preferences
        self.task_routing = {
            TaskType.REASONING: [AIModel.O1, AIModel.CLAUDE_4_OPUS, AIModel.GPT_5],
            TaskType.CREATIVE: [AIModel.CLAUDE_4_SONNET, AIModel.CLAUDE_4_OPUS, AIModel.GPT_5],
            TaskType.ANALYSIS: [AIModel.GEMINI_2_5_PRO, AIModel.CLAUDE_4_SONNET, AIModel.GPT_5],
            TaskType.CODING: [AIModel.GPT_5, AIModel.O1, AIModel.CLAUDE_4_OPUS],
            TaskType.CONVERSATION: [AIModel.GPT_5_MINI, AIModel.CLAUDE_4_SONNET, AIModel.GEMINI_2_5_PRO],
            TaskType.MULTIMODAL: [AIModel.GEMINI_2_5_PRO, AIModel.GPT_5, AIModel.CLAUDE_4_SONNET],
            TaskType.FORECASTING: [AIModel.O1, AIModel.GPT_5, AIModel.GEMINI_2_5_PRO],
            TaskType.SUMMARIZATION: [AIModel.GPT_5_MINI, AIModel.CLAUDE_4_SONNET, AIModel.GEMINI_2_5_PRO],
            TaskType.CLASSIFICATION: [AIModel.GPT_5_MINI, AIModel.GEMINI_2_5_PRO, AIModel.CLAUDE_4_SONNET],
            TaskType.TRANSLATION: [AIModel.GEMINI_2_5_PRO, AIModel.GPT_5, AIModel.CLAUDE_4_SONNET]
        }
    
    def _get_provider_for_model(self, model: AIModel) -> AIProvider:
        """Get the provider for a given model"""
        if model.value.startswith('gpt') or model.value.startswith('o1'):
            return AIProvider.OPENAI
        elif model.value.startswith('claude'):
            return AIProvider.ANTHROPIC
        elif model.value.startswith('gemini'):
            return AIProvider.GOOGLE
        else:
            return AIProvider.OPENAI  # Default
    
    async def route_task(self, task_type: TaskType, message: str, 
                        preferred_model: Optional[AIModel] = None,
                        consider_cost: bool = False) -> AIModel:
        """Intelligently route task to best AI model"""
        try:
            if preferred_model:
                return preferred_model
            
            # Get candidate models for this task type
            candidates = self.task_routing.get(task_type, [AIModel.GPT_5_MINI])
            
            if consider_cost:
                # Sort by cost efficiency for budget-conscious routing
                candidates = sorted(candidates, 
                                  key=lambda m: self.model_capabilities[m].cost_score, 
                                  reverse=True)
            
            # For now, return the top candidate
            # Future: Could implement more sophisticated routing based on:
            # - Current model load/availability
            # - User history/preferences  
            # - Cost budgets
            # - Response time requirements
            
            selected_model = candidates[0] if candidates else AIModel.GPT_5_MINI
            
            logger.info(f"Routed {task_type} task to {selected_model}")
            return selected_model
            
        except Exception as e:
            logger.error(f"Error in task routing: {e}")
            return AIModel.GPT_5_MINI  # Safe default
    
    async def send_to_model(self, model: AIModel, message: str, 
                           system_message: str = None, temperature: float = 0.7,
                           session_id: str = None) -> AIResponse:
        """Send message to specific AI model"""
        try:
            provider = self._get_provider_for_model(model)
            
            # Create chat instance
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id or f"ai_router_{int(time.time())}",
                system_message=system_message or "You are a helpful AI assistant."
            ).with_model(provider.value, model.value)
            
            # Create user message
            user_message = UserMessage(text=message)
            
            # Track timing
            start_time = time.time()
            
            # Send message
            response = await chat.send_message(user_message)
            
            processing_time = time.time() - start_time
            
            # Create standardized response
            return AIResponse(
                content=response,
                model_used=model.value,
                provider=provider.value,
                processing_time=processing_time,
                token_count=len(response.split()) * 1.3,  # Rough estimate
                cost_estimate=self._estimate_cost(model, len(message), len(response))
            )
            
        except Exception as e:
            logger.error(f"Error sending to {model}: {e}")
            raise HTTPException(status_code=500, detail=f"AI model error: {str(e)}")
    
    def _estimate_cost(self, model: AIModel, input_length: int, output_length: int) -> float:
        """Estimate cost for AI model usage"""
        # Rough cost estimates (in cents)
        cost_per_1k_tokens = {
            AIModel.GPT_5: 3.0,
            AIModel.GPT_5_MINI: 0.5,
            AIModel.CLAUDE_4_OPUS: 15.0,
            AIModel.CLAUDE_4_SONNET: 3.0,
            AIModel.GEMINI_2_5_PRO: 1.25,
            AIModel.O1: 15.0
        }
        
        base_cost = cost_per_1k_tokens.get(model, 1.0)
        total_tokens = (input_length + output_length) / 4  # Rough token estimate
        return (total_tokens / 1000) * base_cost
    
    async def compare_models(self, models: List[AIModel], message: str,
                           system_message: str = None, temperature: float = 0.7) -> List[AIResponse]:
        """Compare responses from multiple AI models"""
        try:
            tasks = []
            session_id = f"comparison_{int(time.time())}"
            
            for model in models:
                task = self.send_to_model(
                    model=model,
                    message=message,
                    system_message=system_message,
                    temperature=temperature,
                    session_id=f"{session_id}_{model.value}"
                )
                tasks.append(task)
            
            # Execute all model requests concurrently
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful responses
            successful_responses = [
                resp for resp in responses 
                if isinstance(resp, AIResponse)
            ]
            
            return successful_responses
            
        except Exception as e:
            logger.error(f"Error in model comparison: {e}")
            raise HTTPException(status_code=500, detail=f"Model comparison failed: {str(e)}")
    
    async def log_performance(self, response: AIResponse, task_type: TaskType, 
                             user_rating: Optional[float] = None):
        """Log model performance metrics"""
        try:
            db = await get_database()
            
            performance_record = {
                "model": response.model_used,
                "provider": response.provider,
                "task_type": task_type.value,
                "response_time": response.processing_time,
                "token_count": response.token_count or 0,
                "cost_estimate": response.cost_estimate or 0.0,
                "user_rating": user_rating,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            }
            
            await db.ai_model_performance.insert_one(performance_record)
            
        except Exception as e:
            logger.error(f"Error logging performance: {e}")

# Global AI router instance
ai_router = AIModelRouter()

# API Endpoints
@router.get("/health", summary="AI models health check")
async def get_ai_models_health():
    """Get health status of AI models system"""
    try:
        api_key_configured = bool(ai_router.api_key)
        
        return {
            "status": "healthy" if api_key_configured else "degraded",
            "components": {
                "emergent_llm_key": "configured" if api_key_configured else "missing",
                "model_router": "healthy",
                "performance_tracking": "healthy"
            },
            "available_models": {
                "openai": [model.value for model in AIModel if model.value.startswith(('gpt', 'o1'))],
                "anthropic": [model.value for model in AIModel if model.value.startswith('claude')],
                "google": [model.value for model in AIModel if model.value.startswith('gemini')]
            },
            "supported_task_types": [task.value for task in TaskType],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"AI models health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/chat", summary="Send message to AI model with intelligent routing")
async def ai_chat(request: AIRequest, background_tasks: BackgroundTasks):
    """Send message to AI model with intelligent routing"""
    try:
        # Route to best model for the task
        selected_model = await ai_router.route_task(
            task_type=request.task_type,
            message=request.message,
            preferred_model=request.preferred_model
        )
        
        # Send to selected model
        response = await ai_router.send_to_model(
            model=selected_model,
            message=request.message,
            system_message=request.system_message,
            temperature=request.temperature,
            session_id=request.session_id
        )
        
        # Log performance in background
        background_tasks.add_task(
            ai_router.log_performance,
            response, 
            request.task_type
        )
        
        return {
            "response": response.content,
            "model_used": response.model_used,
            "provider": response.provider,
            "processing_time": response.processing_time,
            "task_type": request.task_type.value,
            "cost_estimate": response.cost_estimate,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}")

@router.post("/compare", summary="Compare responses from multiple AI models")
async def compare_models(request: ModelComparisonRequest):
    """Compare responses from multiple AI models"""
    try:
        responses = await ai_router.compare_models(
            models=request.models,
            message=request.message,
            system_message=request.system_message,
            temperature=request.temperature
        )
        
        # Prepare comparison results
        comparison_results = []
        for response in responses:
            comparison_results.append({
                "model": response.model_used,
                "provider": response.provider,
                "response": response.content,
                "processing_time": response.processing_time,
                "cost_estimate": response.cost_estimate,
                "performance_score": ai_router.model_capabilities.get(
                    AIModel(response.model_used), 
                    ModelCapabilities(0.5, 0.5, 0.5, 0.5, 4000, False, [])
                ).__dict__
            })
        
        return {
            "task_type": request.task_type.value,
            "models_compared": len(comparison_results),
            "results": comparison_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in model comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Model comparison failed: {str(e)}")

@router.get("/models", summary="Get available AI models and capabilities")
async def get_available_models():
    """Get list of available AI models and their capabilities"""
    try:
        models_info = {}
        
        for model, capabilities in ai_router.model_capabilities.items():
            provider = ai_router._get_provider_for_model(model)
            
            models_info[model.value] = {
                "provider": provider.value,
                "capabilities": {
                    "reasoning_score": capabilities.reasoning_score,
                    "creativity_score": capabilities.creativity_score,
                    "speed_score": capabilities.speed_score,
                    "cost_score": capabilities.cost_score,
                    "context_length": capabilities.context_length,
                    "multimodal": capabilities.multimodal,
                    "specialties": [s.value for s in capabilities.specialties]
                },
                "recommended_for": [s.value for s in capabilities.specialties]
            }
        
        return {
            "available_models": models_info,
            "task_routing": {
                task.value: [model.value for model in models] 
                for task, models in ai_router.task_routing.items()
            },
            "total_models": len(models_info),
            "providers": list(set([info["provider"] for info in models_info.values()]))
        }
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")

@router.get("/performance", summary="Get AI models performance metrics")
async def get_performance_metrics(days: int = 7):
    """Get AI models performance metrics"""
    try:
        db = await get_database()
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get performance data
        performance_data = await db.ai_model_performance.find({
            "timestamp": {"$gte": start_date.isoformat()}
        }).to_list(length=None)
        
        # Aggregate metrics by model
        model_metrics = {}
        for record in performance_data:
            model = record["model"]
            if model not in model_metrics:
                model_metrics[model] = {
                    "total_requests": 0,
                    "avg_response_time": 0,
                    "total_cost": 0,
                    "avg_rating": 0,
                    "success_rate": 0,
                    "task_types": {}
                }
            
            metrics = model_metrics[model]
            metrics["total_requests"] += 1
            metrics["avg_response_time"] += record.get("response_time", 0)
            metrics["total_cost"] += record.get("cost_estimate", 0)
            
            if record.get("user_rating"):
                metrics["avg_rating"] += record["user_rating"]
            
            task_type = record.get("task_type", "unknown")
            if task_type not in metrics["task_types"]:
                metrics["task_types"][task_type] = 0
            metrics["task_types"][task_type] += 1
        
        # Calculate averages
        for model, metrics in model_metrics.items():
            if metrics["total_requests"] > 0:
                metrics["avg_response_time"] /= metrics["total_requests"]
                metrics["avg_rating"] /= metrics["total_requests"]
                metrics["success_rate"] = 100.0  # Assuming all logged requests were successful
        
        return {
            "analysis_period_days": days,
            "total_requests": sum(m["total_requests"] for m in model_metrics.values()),
            "model_performance": model_metrics,
            "top_models_by_usage": sorted(
                model_metrics.items(),
                key=lambda x: x[1]["total_requests"],
                reverse=True
            )[:5],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")

@router.post("/route", summary="Get optimal model recommendation for task")
async def route_task(task_type: TaskType, message_preview: str, consider_cost: bool = False):
    """Get optimal model recommendation for a specific task"""
    try:
        recommended_model = await ai_router.route_task(
            task_type=task_type,
            message=message_preview,
            consider_cost=consider_cost
        )
        
        capabilities = ai_router.model_capabilities[recommended_model]
        provider = ai_router._get_provider_for_model(recommended_model)
        
        return {
            "recommended_model": recommended_model.value,
            "provider": provider.value,
            "task_type": task_type.value,
            "routing_reason": "Optimized for task type",
            "model_capabilities": {
                "reasoning_score": capabilities.reasoning_score,
                "creativity_score": capabilities.creativity_score,
                "speed_score": capabilities.speed_score,
                "cost_score": capabilities.cost_score,
                "context_length": capabilities.context_length,
                "multimodal": capabilities.multimodal
            },
            "alternative_models": [
                model.value for model in ai_router.task_routing.get(task_type, [])
            ][:3],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in task routing: {e}")
        raise HTTPException(status_code=500, detail=f"Task routing failed: {str(e)}")