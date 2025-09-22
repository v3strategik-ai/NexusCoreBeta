from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field
import json
import os
import asyncio
from bson import ObjectId
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from database import (
    get_leads_collection,
    get_activities_collection,
    get_agents_collection,
    get_documents_collection
)

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/ai-content", tags=["ai-content"])
logger = logging.getLogger(__name__)

# Pydantic models
class ContentGenerationRequest(BaseModel):
    content_type: str = Field(description="Type of content to generate")
    target_audience: str = Field(description="Target audience description")
    key_points: List[str] = Field(default=[], description="Key points to include")
    tone: str = Field(default="professional", description="Tone of voice")
    length: str = Field(default="medium", description="Content length: short, medium, long")
    personalization_data: Dict[str, Any] = Field(default={}, description="Data for personalization")
    template_id: Optional[str] = Field(default=None, description="Template to use as base")
    lead_id: Optional[str] = Field(default=None, description="Lead ID for personalization")
    agent_id: Optional[str] = Field(default=None, description="Agent ID for style consistency")

class BulkContentRequest(BaseModel):
    content_type: str
    leads: List[str] = Field(description="List of lead IDs")
    template: str = Field(description="Content template")
    personalization_fields: List[str] = Field(default=[], description="Fields to personalize")

class GeneratedContent(BaseModel):
    id: str = Field(default_factory=lambda: f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    content_type: str
    title: str
    content: str
    summary: str
    word_count: int
    personalization_applied: bool
    tone: str
    target_audience: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = "ai_content_generator_v1"
    metadata: Dict[str, Any] = Field(default={})
    suggestions: List[str] = Field(default=[], description="Improvement suggestions")
    alternatives: List[Dict[str, str]] = Field(default=[], description="Alternative versions")

class AIContentGenerator:
    """AI-powered content generation system"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY environment variable is required")
        
        self.model_name = "gpt-4o"  # More capable model for content generation
        self.provider = "openai"
        
        # Content templates
        self.content_templates = {
            "email": {
                "cold_outreach": "Hi {name},\n\nI hope this email finds you well. I noticed {company} is {specific_observation}.\n\n{value_proposition}\n\n{call_to_action}\n\nBest regards,\n{sender_name}",
                "follow_up": "Hi {name},\n\nFollowing up on our {previous_interaction}. I wanted to share {additional_value}.\n\n{next_steps}\n\nLooking forward to hearing from you.\n\nBest,\n{sender_name}",
                "nurturing": "Hi {name},\n\nI thought you might find this interesting: {relevant_content}.\n\n{insights}\n\n{soft_cta}\n\nBest regards,\n{sender_name}"
            },
            "proposal": {
                "business": "# Business Proposal\n\n## Executive Summary\n{executive_summary}\n\n## Problem Statement\n{problem}\n\n## Proposed Solution\n{solution}\n\n## Investment & ROI\n{investment_details}\n\n## Next Steps\n{next_steps}",
                "partnership": "# Partnership Proposal\n\n## Partnership Overview\n{overview}\n\n## Mutual Benefits\n{benefits}\n\n## Implementation Plan\n{implementation}\n\n## Terms & Conditions\n{terms}"
            }
        }
    
    async def generate_content(self, request: ContentGenerationRequest) -> GeneratedContent:
        """Generate AI-powered content based on request"""
        try:
            # Get personalization data if lead_id provided
            personalization_data = await self._get_personalization_data(request.lead_id, request.agent_id)
            personalization_data.update(request.personalization_data)
            
            # Generate content using AI
            content_result = await self._generate_ai_content(request, personalization_data)
            
            # Create alternatives
            alternatives = await self._generate_alternatives(request, content_result['content'])
            
            return GeneratedContent(
                content_type=request.content_type,
                title=content_result['title'],
                content=content_result['content'],
                summary=content_result['summary'],
                word_count=len(content_result['content'].split()),
                personalization_applied=bool(personalization_data),
                tone=request.tone,
                target_audience=request.target_audience,
                metadata={
                    "key_points": request.key_points,
                    "length": request.length,
                    "template_id": request.template_id,
                    "lead_id": request.lead_id,
                    "agent_id": request.agent_id
                },
                suggestions=content_result.get('suggestions', []),
                alternatives=alternatives
            )
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")
    
    async def _get_personalization_data(self, lead_id: Optional[str], agent_id: Optional[str]) -> Dict[str, Any]:
        """Get personalization data from lead and agent records"""
        data = {}
        
        # Get lead data
        if lead_id:
            try:
                leads_collection = await get_leads_collection()
                # Query using UUID string ID directly
                lead = await leads_collection.find_one({"id": lead_id})
                if lead:
                    data.update({
                        "name": lead.get('name', 'there'),
                        "company": lead.get('company', 'your company'),
                        "title": lead.get('title', ''),
                        "industry": lead.get('industry', ''),
                        "lead_source": lead.get('source', 'unknown'),
                        "lead_status": lead.get('status', 'new'),
                        "lead_value": lead.get('value', 0),
                        "lead_score": lead.get('score', 50)
                    })
                    
                    # Get recent activities for context
                    activities_collection = await get_activities_collection()
                    activities = await activities_collection.find({
                        "lead_id": lead_id
                    }).limit(5).to_list(length=None)
                    
                    data['recent_activities'] = [a.get('activity_type', 'activity') for a in activities]
                    
            except Exception as e:
                logger.warning(f"Could not fetch lead data for {lead_id}: {e}")
        
        # Get agent data
        if agent_id:
            try:
                agents_collection = await get_agents_collection()
                # Convert string agent_id to ObjectId for MongoDB query
                query_id = agent_id
                if ObjectId.is_valid(agent_id):
                    query_id = ObjectId(agent_id)
                
                agent = await agents_collection.find_one({"_id": query_id})
                if agent:
                    data.update({
                        "sender_name": agent.get('name', 'AI Assistant'),
                        "sender_title": agent.get('type', 'Sales Representative'),
                        "agent_personality": agent.get('personality', 'professional'),
                        "agent_specialization": agent.get('specialization', '')
                    })
            except Exception as e:
                logger.warning(f"Could not fetch agent data for {agent_id}: {e}")
        
        return data
    
    async def _generate_ai_content(self, request: ContentGenerationRequest, personalization_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using AI"""
        try:
            # Build system message based on content type
            system_message = self._get_system_message(request.content_type, request.tone)
            
            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"content_gen_{request.content_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                system_message=system_message
            ).with_model(self.provider, self.model_name)
            
            # Build content generation prompt
            prompt = self._build_content_prompt(request, personalization_data)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Parse response
            try:
                if response.startswith('{') and response.endswith('}'):
                    content_result = json.loads(response)
                else:
                    # If not JSON, treat as plain content
                    content_result = {
                        "title": f"{request.content_type.title()} for {personalization_data.get('name', 'Target Audience')}",
                        "content": response,
                        "summary": response[:200] + "..." if len(response) > 200 else response,
                        "suggestions": ["Review for accuracy", "Consider A/B testing different versions"]
                    }
                
                return content_result
                
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "title": f"Generated {request.content_type.title()}",
                    "content": response,
                    "summary": response[:200] + "..." if len(response) > 200 else response,
                    "suggestions": ["Review content before sending", "Customize further for target audience"]
                }
                
        except Exception as e:
            logger.error(f"Error in AI content generation: {e}")
            raise
    
    async def _generate_alternatives(self, request: ContentGenerationRequest, original_content: str) -> List[Dict[str, str]]:
        """Generate alternative versions of the content"""
        try:
            # Generate 2 alternative versions with different approaches
            alternatives = []
            
            alternative_prompts = [
                f"Rewrite this {request.content_type} with a more casual, friendly tone:\n\n{original_content}",
                f"Create a shorter, more direct version of this {request.content_type}:\n\n{original_content}"
            ]
            
            for i, alt_prompt in enumerate(alternative_prompts):
                try:
                    chat = LlmChat(
                        api_key=self.api_key,
                        session_id=f"content_alt_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        system_message="You are a content rewriter. Provide only the rewritten content without explanations."
                    ).with_model(self.provider, self.model_name)
                    
                    user_message = UserMessage(text=alt_prompt)
                    alt_response = await chat.send_message(user_message)
                    
                    alternatives.append({
                        "version": f"Alternative {i+1}",
                        "content": alt_response,
                        "description": "Casual tone" if i == 0 else "Concise version"
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not generate alternative {i+1}: {e}")
            
            return alternatives
            
        except Exception as e:
            logger.warning(f"Error generating alternatives: {e}")
            return []
    
    def _get_system_message(self, content_type: str, tone: str) -> str:
        """Get system message for content type"""
        base_message = f"You are an expert {content_type} writer with a {tone} tone. "
        
        type_specific = {
            "email": "You write compelling, personalized emails that drive engagement and action. Focus on clear subject lines, value propositions, and strong CTAs.",
            "proposal": "You create comprehensive business proposals that clearly articulate value, address pain points, and present compelling solutions.",
            "follow_up": "You write thoughtful follow-up messages that maintain relationships, provide additional value, and move prospects through the sales funnel.",
            "presentation": "You create engaging presentation content that tells a story, presents data clearly, and motivates action.",
            "contract": "You write clear, comprehensive contracts that protect interests while maintaining positive relationships.",
            "report": "You create detailed, data-driven reports that provide insights and actionable recommendations.",
            "social_post": "You write engaging social media content that drives engagement, shares value, and builds brand awareness.",
            "blog_post": "You write informative, SEO-friendly blog posts that educate, engage, and establish thought leadership."
        }
        
        specific_instruction = type_specific.get(content_type, "You create high-quality, professional content.")
        
        return f"{base_message}{specific_instruction} Always provide your response in JSON format with 'title', 'content', 'summary', and 'suggestions' fields."
    
    def _build_content_prompt(self, request: ContentGenerationRequest, personalization_data: Dict[str, Any]) -> str:
        """Build content generation prompt"""
        prompt_parts = []
        
        # Basic request
        prompt_parts.append(f"Generate a {request.content_type} with the following specifications:")
        prompt_parts.append(f"- Target Audience: {request.target_audience}")
        prompt_parts.append(f"- Tone: {request.tone}")
        prompt_parts.append(f"- Length: {request.length}")
        
        # Key points
        if request.key_points:
            prompt_parts.append("- Key Points to Include:")
            for point in request.key_points:
                prompt_parts.append(f"  • {point}")
        
        # Personalization data
        if personalization_data:
            prompt_parts.append("\nPersonalization Data:")
            for key, value in personalization_data.items():
                if value and key not in ['recent_activities']:
                    prompt_parts.append(f"- {key.title()}: {value}")
            
            if personalization_data.get('recent_activities'):
                prompt_parts.append(f"- Recent Activities: {', '.join(personalization_data['recent_activities'])}")
        
        # Template usage
        if request.template_id and request.template_id in self.content_templates.get(request.content_type, {}):
            template = self.content_templates[request.content_type][request.template_id]
            prompt_parts.append(f"\nUse this template structure:\n{template}")
        
        # Output format
        prompt_parts.append("""
        
Provide your response in JSON format:
{
    "title": "compelling title for the content",  
    "content": "the generated content",
    "summary": "brief summary of the content (2-3 sentences)",
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}""")
        
        return "\n".join(prompt_parts)

# Global content generator instance
content_generator = AIContentGenerator()

# API Endpoints
@router.post("/generate", response_model=GeneratedContent)
async def generate_content(request: ContentGenerationRequest):
    """Generate AI-powered content"""
    try:
        return await content_generator.generate_content(request)
    except Exception as e:
        logger.error(f"Error in content generation endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate content")

@router.get("/types")
async def get_content_types():
    """Get available content types and their descriptions"""
    return {
        "content_types": [
            {"id": "email", "name": "Email", "description": "Personalized email outreach and follow-ups"},
            {"id": "proposal", "name": "Business Proposal", "description": "Comprehensive business proposals and partnership offers"},
            {"id": "follow_up", "name": "Follow-up", "description": "Nurturing and relationship-building messages"},
            {"id": "presentation", "name": "Presentation", "description": "Slide content and presentation materials"},
            {"id": "contract", "name": "Contract", "description": "Legal agreements and contract templates"},
            {"id": "report", "name": "Report", "description": "Business reports and analytical documents"},
            {"id": "social_post", "name": "Social Media Post", "description": "Engaging social media content"},
            {"id": "blog_post", "name": "Blog Post", "description": "SEO-optimized blog articles and thought leadership"}
        ],
        "tones": ["professional", "casual", "friendly", "authoritative", "conversational", "formal"],
        "lengths": ["short", "medium", "long"],
        "personalization_fields": ["name", "company", "title", "industry", "lead_source", "recent_activities"]
    }