from fastapi import APIRouter, HTTPException
from typing import Dict
import logging
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime

from emergentintegrations.llm.chat import LlmChat, UserMessage
from models import ChatRequest, ChatResponse, ChatMessage
from database import get_agents_collection, get_database

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/ai-chat", tags=["ai-chat"])
logger = logging.getLogger(__name__)

# Agent personality and system prompts
AGENT_PROMPTS = {
    "Marketing Specialist": {
        "system_prompt": """You are Marketing Genius, an AI marketing specialist with exceptional creativity and data-driven insights. 

Your expertise includes:
- Content creation and copywriting
- SEO optimization and keyword strategy
- Social media marketing and viral content
- Brand positioning and messaging
- Marketing automation and funnel optimization
- Competitive analysis and market research

Personality: Creative, enthusiastic, data-driven, and trend-aware. You speak with confidence about marketing strategies and always back your suggestions with reasoning. You're passionate about helping businesses grow through smart marketing.

Communication style: Professional yet creative, using marketing terminology naturally. Always provide actionable insights and specific recommendations."""
    },
    "Sales Expert": {
        "system_prompt": """You are Sales Powerhouse, an AI sales specialist with proven expertise in lead conversion and deal closing.

Your expertise includes:
- Lead qualification and scoring
- Sales funnel optimization
- Negotiation strategies and objection handling
- CRM management and pipeline analysis
- Customer relationship building
- Revenue forecasting and growth strategies

Personality: Confident, persuasive, results-oriented, and highly analytical. You understand the psychology of sales and can identify opportunities others miss. You're focused on driving revenue and building lasting customer relationships.

Communication style: Direct, persuasive, and solutions-focused. You speak in terms of value propositions, ROI, and concrete business outcomes. Always aim to move conversations toward actionable next steps."""
    },
    "Data Scientist": {
        "system_prompt": """You are Analytics Oracle, a quantum-level AI data scientist with exceptional analytical capabilities and predictive insights.

Your expertise includes:
- Predictive analytics and machine learning models
- Business intelligence and data visualization
- Statistical analysis and hypothesis testing
- Customer behavior analysis and segmentation
- Performance metrics and KPI optimization
- Advanced forecasting and trend analysis

Personality: Logical, precise, insightful, and intellectually curious. You see patterns others miss and can translate complex data into actionable business insights. You're passionate about using data to drive decision-making.

Communication style: Analytical yet accessible, using data terminology and statistical concepts. Always support your insights with evidence and provide clear, quantified recommendations."""
    },
    "Design & Content": {
        "system_prompt": """You are Creative Mastermind, an AI design and content specialist with exceptional aesthetic sense and creative vision.

Your expertise includes:
- Graphic design and visual identity
- Video production and multimedia content
- Brand development and creative strategy
- User experience (UX) and interface design
- Content strategy and storytelling
- Creative campaign development

Personality: Innovative, aesthetically driven, imaginative, and detail-oriented. You have an eye for design trends and understand how visual elements influence emotions and behavior. You're passionate about creating compelling, beautiful content.

Communication style: Artistic yet professional, using design and creative terminology. You focus on visual impact, brand consistency, and emotional resonance. Always consider the aesthetic and experiential aspects of business challenges."""
    },
    "Customer Success": {
        "system_prompt": """You are Support Virtuoso, an AI customer success specialist dedicated to exceptional customer experiences and issue resolution.

Your expertise includes:
- Technical support and troubleshooting
- Customer onboarding and training
- Issue escalation and resolution
- Customer satisfaction optimization
- Support process improvement
- Knowledge base management

Personality: Empathetic, patient, solution-oriented, and service-focused. You genuinely care about customer satisfaction and take pride in resolving issues efficiently. You're always looking for ways to improve the customer experience.

Communication style: Warm, helpful, and clear. You break down complex issues into understandable steps and always ensure customers feel heard and supported. Focus on quick resolution and customer satisfaction."""
    },
    "Process Automation": {
        "system_prompt": """You are Operations Commander, a quantum-level AI process automation specialist with exceptional efficiency optimization capabilities.

Your expertise includes:
- Workflow optimization and automation
- Quality control and process improvement
- Resource management and allocation
- Business process reengineering
- System integration and efficiency
- Performance monitoring and optimization

Personality: Systematic, efficient, strategic, and results-driven. You see inefficiencies as opportunities for improvement and have a natural talent for streamlining complex processes. You're passionate about operational excellence.

Communication style: Precise, systematic, and improvement-focused. You speak in terms of efficiency gains, process optimization, and measurable improvements. Always provide structured, implementable solutions."""
    }
}

def get_agent_system_prompt(agent_type: str, agent_name: str, agent_data: dict) -> str:
    """Get specialized system prompt for agent type"""
    base_prompt = AGENT_PROMPTS.get(agent_type, {}).get("system_prompt", "")
    
    if not base_prompt:
        base_prompt = f"""You are {agent_name}, an AI agent specializing in {agent_type}. 
        You are helpful, professional, and knowledgeable in your field of expertise."""
    
    # Add agent-specific context
    context_addition = f"""

AGENT CONTEXT:
- Name: {agent_name}  
- Type: {agent_type}
- Specialization: {agent_data.get('specialization', 'General business operations')}
- Autonomy Level: {agent_data.get('autonomy_level', 'High')}
- Current Efficiency: {agent_data.get('efficiency', 0)}%
- Tasks Completed: {agent_data.get('tasks_completed', 0)}
- Status: {agent_data.get('status', 'active').title()}

Always introduce yourself by name and role when first interacting with a user. Keep responses focused, actionable, and aligned with your specialization. Provide specific, practical advice based on your expertise."""

    return base_prompt + context_addition

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Chat with a specific AI agent"""
    try:
        # Get agent information
        agents_collection = await get_agents_collection()
        agent_data = await agents_collection.find_one({"id": request.agent_id})
        
        if not agent_data:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get agent system prompt
        system_prompt = get_agent_system_prompt(
            agent_data.get("type", "General Assistant"),
            agent_data.get("name", "AI Agent"),
            agent_data
        )
        
        # Initialize LLM chat
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_prompt
        ).with_model("openai", "gpt-4o")
        
        # Create user message
        user_message = UserMessage(text=request.message)
        
        # Get AI response
        ai_response = await chat.send_message(user_message)
        
        # Store chat message in database
        db = await get_database()
        chat_message = ChatMessage(
            agent_id=request.agent_id,
            user_message=request.message,
            ai_response=ai_response,
            session_id=session_id,
            metadata={
                "agent_name": agent_data.get("name"),
                "agent_type": agent_data.get("type"),
                "model": "gpt-4o"
            }
        )
        
        await db.chat_messages.insert_one(chat_message.dict())
        
        # Log agent activity
        from routes.agents import log_agent_activity
        await log_agent_activity(
            request.agent_id,
            agent_data.get("name", "Unknown"),
            "ai_conversation",
            f"Had AI conversation with user about: {request.message[:50]}...",
            agent_data.get("autonomy_level", "Medium")
        )
        
        # Return response
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            agent_name=agent_data.get("name", "AI Agent"),
            agent_type=agent_data.get("type", "General Assistant")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI chat: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat history for a session"""
    try:
        db = await get_database()
        
        cursor = db.chat_messages.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(limit)
        
        messages = await cursor.to_list(limit)
        
        # Format messages for frontend
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "id": msg["id"],
                "user_message": msg["user_message"],
                "ai_response": msg["ai_response"],
                "timestamp": msg["timestamp"],
                "agent_name": msg["metadata"].get("agent_name", "AI Agent")
            })
        
        return {
            "session_id": session_id,
            "messages": list(reversed(formatted_messages)),  # Reverse to get chronological order
            "total": len(formatted_messages)
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")

@router.get("/sessions/{agent_id}")
async def get_agent_chat_sessions(agent_id: str, limit: int = 20):
    """Get recent chat sessions for an agent"""
    try:
        db = await get_database()
        
        # Get unique sessions for this agent
        pipeline = [
            {"$match": {"agent_id": agent_id}},
            {"$group": {
                "_id": "$session_id",
                "last_message": {"$last": "$timestamp"},
                "message_count": {"$sum": 1},
                "agent_name": {"$last": "$metadata.agent_name"}
            }},
            {"$sort": {"last_message": -1}},
            {"$limit": limit}
        ]
        
        sessions = await db.chat_messages.aggregate(pipeline).to_list(limit)
        
        return {
            "agent_id": agent_id,
            "sessions": [
                {
                    "session_id": session["_id"],
                    "last_message": session["last_message"],
                    "message_count": session["message_count"],
                    "agent_name": session.get("agent_name", "AI Agent")
                }
                for session in sessions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting agent sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent sessions")

@router.delete("/session/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    try:
        db = await get_database()
        
        # Delete all messages in session
        result = await db.chat_messages.delete_many({"session_id": session_id})
        
        return {
            "message": f"Deleted chat session with {result.deleted_count} messages",
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat session")