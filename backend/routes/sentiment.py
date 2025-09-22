from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field
import json
import os
from statistics import mean
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from database import (
    get_leads_collection,
    get_activities_collection,
    get_documents_collection
)

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/sentiment", tags=["sentiment-analysis"])
logger = logging.getLogger(__name__)

# Pydantic models
class SentimentAnalysisRequest(BaseModel):
    text: str = Field(description="Text to analyze for sentiment")
    context: Optional[str] = Field(default=None, description="Additional context")
    lead_id: Optional[str] = Field(default=None, description="Associated lead ID")
    source_type: str = Field(default="general", description="Type of source: email, chat, call, note")

class SentimentResult(BaseModel):
    id: str = Field(default_factory=lambda: f"sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    text: str
    sentiment: str = Field(description="positive, negative, neutral")
    confidence: float = Field(ge=0, le=1, description="Confidence score")
    emotions: Dict[str, float] = Field(default={}, description="Detected emotions with scores")
    key_phrases: List[str] = Field(default=[], description="Important phrases")
    urgency_level: str = Field(default="low", description="low, medium, high")
    satisfaction_score: Optional[float] = Field(default=None, ge=0, le=10, description="Customer satisfaction (0-10)")
    intent: Optional[str] = Field(default=None, description="Detected intent")
    topics: List[str] = Field(default=[], description="Identified topics")
    action_required: bool = Field(default=False, description="Whether immediate action is needed")
    recommendations: List[str] = Field(default=[], description="Suggested actions")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    source_type: str = "general"
    lead_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default={})

class SentimentTrend(BaseModel):
    lead_id: str
    lead_name: str
    company: str
    overall_sentiment: str
    sentiment_score: float = Field(ge=-1, le=1, description="Average sentiment (-1 to 1)")
    total_interactions: int
    recent_trend: str = Field(description="improving, declining, stable")
    last_analysis: datetime
    risk_level: str = Field(description="low, medium, high")
    alerts: List[str] = Field(default=[], description="Active alerts")

class SentimentAnalyzer:
    """AI-powered sentiment analysis system"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY environment variable is required")
        
        self.model_name = "gpt-4o-mini"  # Efficient model for sentiment analysis
        self.provider = "openai"
    
    async def analyze_sentiment(self, request: SentimentAnalysisRequest) -> SentimentResult:
        """Analyze sentiment of text using AI"""
        try:
            # Get AI sentiment analysis
            analysis = await self._get_ai_sentiment_analysis(request.text, request.context, request.source_type)
            
            # Build result
            result = SentimentResult(
                text=request.text,
                sentiment=analysis.get('sentiment', 'neutral'),
                confidence=analysis.get('confidence', 0.5),
                emotions=analysis.get('emotions', {}),
                key_phrases=analysis.get('key_phrases', []),
                urgency_level=analysis.get('urgency_level', 'low'),
                satisfaction_score=analysis.get('satisfaction_score'),
                intent=analysis.get('intent'),
                topics=analysis.get('topics', []),
                action_required=analysis.get('action_required', False),
                recommendations=analysis.get('recommendations', []),
                source_type=request.source_type,
                lead_id=request.lead_id,
                metadata={
                    "context": request.context,
                    "analysis_model": "ai_sentiment_v1"
                }
            )
            
            # Store analysis if associated with a lead
            if request.lead_id:
                await self._store_sentiment_analysis(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to analyze sentiment: {str(e)}")
    
    async def _get_ai_sentiment_analysis(self, text: str, context: Optional[str], source_type: str) -> Dict[str, Any]:
        """Get AI-powered sentiment analysis"""
        try:
            # Build system message for sentiment analysis
            system_message = f"""You are an expert sentiment analysis AI specialized in {source_type} communications. 

Your task is to analyze text for:
1. Overall sentiment (positive, negative, neutral)
2. Confidence level (0.0-1.0)
3. Specific emotions and their intensities
4. Customer satisfaction indicators
5. Urgency level and action requirements
6. Key topics and intent
7. Actionable recommendations

Focus on business context, customer relationship implications, and actionable insights.
Provide analysis in JSON format with specific, practical recommendations."""
            
            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"sentiment_{source_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                system_message=system_message
            ).with_model(self.provider, self.model_name)
            
            # Build analysis prompt
            analysis_prompt = f"""
Analyze the sentiment of this {source_type} communication:

TEXT TO ANALYZE:
"{text}"

{f'CONTEXT: {context}' if context else ''}

Provide comprehensive sentiment analysis in this JSON format:
{{
    "sentiment": "positive|negative|neutral",
    "confidence": 0.0-1.0,
    "emotions": {{
        "joy": 0.0-1.0,
        "trust": 0.0-1.0,
        "fear": 0.0-1.0,
        "anger": 0.0-1.0
    }},
    "key_phrases": ["phrase1", "phrase2", "phrase3"],
    "urgency_level": "low|medium|high",
    "satisfaction_score": 0-10 or null,
    "intent": "inquiry|complaint|praise|request|cancellation|purchase|support|feedback|other",
    "topics": ["topic1", "topic2"],
    "action_required": true|false,
    "recommendations": ["recommendation1", "recommendation2"],
    "reasoning": "explanation of the analysis"
}}

Focus on practical business insights and actionable recommendations.
"""
            
            user_message = UserMessage(text=analysis_prompt)
            response = await chat.send_message(user_message)
            
            # Parse AI response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse sentiment analysis JSON: {response}")
                # Fallback analysis
                return {
                    "sentiment": "neutral",
                    "confidence": 0.5,
                    "emotions": {},
                    "key_phrases": [],
                    "urgency_level": "medium",
                    "satisfaction_score": None,
                    "intent": "general",
                    "topics": [],
                    "action_required": False,
                    "recommendations": ["Manual review recommended"],
                    "reasoning": "AI analysis parsing failed"
                }
                
        except Exception as e:
            logger.error(f"Error in AI sentiment analysis: {e}")
            # Return fallback analysis
            return {
                "sentiment": "neutral",
                "confidence": 0.3,
                "emotions": {},
                "key_phrases": [],
                "urgency_level": "medium",
                "satisfaction_score": None,
                "intent": "unknown",
                "topics": [],
                "action_required": True,
                "recommendations": ["Manual review required due to analysis error"],
                "reasoning": "Analysis failed, requires manual review"
            }
    
    async def _store_sentiment_analysis(self, result: SentimentResult):
        """Store sentiment analysis result"""
        try:
            # Store in activities collection as sentiment analysis activity
            activities_collection = await get_activities_collection()
            
            activity = {
                "activity_type": "sentiment_analysis",
                "lead_id": result.lead_id,
                "timestamp": result.analyzed_at,
                "data": {
                    "sentiment": result.sentiment,
                    "confidence": result.confidence,
                    "emotions": result.emotions,
                    "satisfaction_score": result.satisfaction_score,
                    "urgency_level": result.urgency_level,
                    "intent": result.intent,
                    "action_required": result.action_required,
                    "source_type": result.source_type
                },
                "description": f"Sentiment analysis: {result.sentiment} ({result.confidence:.2f} confidence)",
                "created_at": datetime.utcnow()
            }
            
            await activities_collection.insert_one(activity)
            
            # Update lead with latest sentiment data
            if result.lead_id:
                leads_collection = await get_leads_collection()
                await leads_collection.update_one(
                    {"_id": result.lead_id},
                    {
                        "$set": {
                            "latest_sentiment": {
                                "sentiment": result.sentiment,
                                "confidence": result.confidence,
                                "satisfaction_score": result.satisfaction_score,
                                "urgency_level": result.urgency_level,
                                "analyzed_at": result.analyzed_at,
                                "action_required": result.action_required
                            },
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
        except Exception as e:
            logger.warning(f"Failed to store sentiment analysis: {e}")

# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()

# API Endpoints
@router.post("/analyze", response_model=SentimentResult)
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """Analyze sentiment of text"""
    try:
        return await sentiment_analyzer.analyze_sentiment(request)
    except Exception as e:
        logger.error(f"Error in sentiment analysis endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze sentiment")

@router.get("/dashboard")
async def get_sentiment_dashboard():
    """Get sentiment analysis dashboard data"""
    try:
        # Get recent sentiment analyses
        activities_collection = await get_activities_collection()
        start_date = datetime.utcnow() - timedelta(days=30)
        
        activities = await activities_collection.find({
            "activity_type": "sentiment_analysis",
            "timestamp": {"$gte": start_date}
        }).to_list(length=None)
        
        if not activities:
            return {
                "summary": {
                    "total_analyses": 0,
                    "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                    "average_confidence": 0,
                    "high_urgency_count": 0
                },
                "recent_analyses": []
            }
        
        # Calculate summary statistics
        sentiments = [a['data']['sentiment'] for a in activities]
        confidences = [a['data']['confidence'] for a in activities]
        urgencies = [a['data'].get('urgency_level', 'low') for a in activities]
        
        return {
            "summary": {
                "total_analyses": len(activities),
                "sentiment_distribution": {
                    "positive": sentiments.count('positive'),
                    "negative": sentiments.count('negative'),
                    "neutral": sentiments.count('neutral')
                },
                "average_confidence": round(mean(confidences), 3) if confidences else 0,
                "high_urgency_count": urgencies.count('high')
            },
            "recent_analyses": [
                {
                    "lead_id": a.get('lead_id'),
                    "sentiment": a['data']['sentiment'],
                    "confidence": a['data']['confidence'],
                    "urgency_level": a['data'].get('urgency_level'),
                    "timestamp": a['timestamp'],
                    "action_required": a['data'].get('action_required', False)
                }
                for a in sorted(activities, key=lambda x: x['timestamp'], reverse=True)[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting sentiment dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sentiment dashboard")