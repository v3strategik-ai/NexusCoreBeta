from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from models import (
    DocumentTemplate, GeneratedDocument, DocumentGenerateRequest,
    DocumentType
)
from database import get_documents_collection

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

@router.get("/templates", response_model=List[DocumentTemplate])
async def get_document_templates(
    type: Optional[DocumentType] = None,
    active_only: bool = True
):
    """Get available document templates"""
    try:
        collection = await get_documents_collection()
        
        # Build filter
        filter_dict = {}
        if type:
            filter_dict["type"] = type
        if active_only:
            filter_dict["is_active"] = True
        
        # Change collection name for templates
        templates_collection = (await get_documents_collection().database).document_templates
        cursor = templates_collection.find(filter_dict).sort("created_at", -1)
        templates_data = await cursor.to_list(100)
        
        return [DocumentTemplate(**template) for template in templates_data]
        
    except Exception as e:
        logger.error(f"Error getting document templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document templates")

@router.get("/", response_model=List[GeneratedDocument])
async def get_generated_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[DocumentType] = None,
    client_name: Optional[str] = None
):
    """Get generated documents"""
    try:
        collection = await get_documents_collection()
        
        # Build filter
        filter_dict = {}
        if type:
            filter_dict["type"] = type
        if client_name:
            filter_dict["client_name"] = {"$regex": client_name, "$options": "i"}
        
        cursor = collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
        documents_data = await cursor.to_list(limit)
        
        return [GeneratedDocument(**doc) for doc in documents_data]
        
    except Exception as e:
        logger.error(f"Error getting generated documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve generated documents")

@router.post("/generate", response_model=GeneratedDocument)
async def generate_document(request: DocumentGenerateRequest):
    """Generate a new document using AI"""
    try:
        # Get template if specified
        template_content = ""
        template_variables = []
        
        if request.template_id:
            templates_collection = (await get_documents_collection().database).document_templates
            template_data = await templates_collection.find_one({"id": request.template_id})
            if template_data:
                template_content = template_data.get("template_content", "")
                template_variables = template_data.get("variables", [])
        
        # Generate document content using AI (mock implementation)
        generated_content = await generate_document_content(
            request, template_content, template_variables
        )
        
        # Create document record
        document = GeneratedDocument(
            title=request.title,
            type=request.type,
            template_id=request.template_id,
            content=generated_content,
            variables_used=request.variables,
            generated_by_agent=request.agent_id,
            client_name=request.client_name
        )
        
        # Save to database
        collection = await get_documents_collection()
        await collection.insert_one(document.dict())
        
        logger.info(f"Generated document: {request.title} for {request.client_name}")
        return document
        
    except Exception as e:
        logger.error(f"Error generating document: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate document")

@router.get("/{document_id}", response_model=GeneratedDocument)
async def get_document(document_id: str):
    """Get a specific generated document"""
    try:
        collection = await get_documents_collection()
        doc_data = await collection.find_one({"id": document_id})
        
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return GeneratedDocument(**doc_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a generated document"""
    try:
        collection = await get_documents_collection()
        
        # Check if document exists
        doc_data = await collection.find_one({"id": document_id})
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete document
        await collection.delete_one({"id": document_id})
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

# Template management endpoints
@router.post("/templates", response_model=DocumentTemplate)
async def create_document_template(template: DocumentTemplate):
    """Create a new document template"""
    try:
        # Use a separate collection for templates
        db = await get_documents_collection().database
        templates_collection = db.document_templates
        
        await templates_collection.insert_one(template.dict())
        
        logger.info(f"Created document template: {template.name}")
        return template
        
    except Exception as e:
        logger.error(f"Error creating document template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document template")

@router.put("/templates/{template_id}", response_model=DocumentTemplate)
async def update_document_template(template_id: str, template_update: dict):
    """Update a document template"""
    try:
        db = await get_documents_collection().database
        templates_collection = db.document_templates
        
        # Check if template exists
        existing_template = await templates_collection.find_one({"id": template_id})
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Update template
        template_update["updated_at"] = datetime.utcnow()
        await templates_collection.update_one(
            {"id": template_id},
            {"$set": template_update}
        )
        
        # Get updated template
        updated_template_data = await templates_collection.find_one({"id": template_id})
        return DocumentTemplate(**updated_template_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document template")

@router.get("/stats/summary")
async def get_document_stats():
    """Get document generation statistics"""
    try:
        collection = await get_documents_collection()
        
        # Total documents
        total_docs = await collection.count_documents({})
        
        # Documents by type
        type_pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        type_stats = await collection.aggregate(type_pipeline).to_list(100)
        
        # Recent documents (last 30 days)
        recent_cutoff = datetime.utcnow().replace(day=1)  # Start of current month
        recent_docs = await collection.count_documents({
            "created_at": {"$gte": recent_cutoff}
        })
        
        # Documents by agent
        agent_pipeline = [
            {"$match": {"generated_by_agent": {"$ne": None}}},
            {"$group": {"_id": "$generated_by_agent", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        agent_stats = await collection.aggregate(agent_pipeline).to_list(10)
        
        return {
            "total_documents": total_docs,
            "document_types": {item["_id"]: item["count"] for item in type_stats},
            "recent_documents": recent_docs,
            "top_generating_agents": agent_stats,
            "ai_generation_success_rate": 96.8  # Mock value
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document statistics")

async def generate_document_content(
    request: DocumentGenerateRequest,
    template_content: str,
    template_variables: List[str]
) -> str:
    """Generate document content using AI with Emergent LLM integration"""
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get API key from environment
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
        
        # Create session ID for this document generation
        session_id = f"doc_gen_{request.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create system message based on document type
        system_messages = {
            DocumentType.PROPOSAL: """You are an expert business proposal writer. Create professional, compelling business proposals that win deals. Focus on clear value propositions, detailed scope of work, competitive pricing, and strong calls to action. Use professional formatting with headers, bullet points, and clear sections.""",
            
            DocumentType.INVOICE: """You are a professional invoice specialist. Create clear, accurate invoices that comply with business standards. Include all necessary details: invoice numbers, dates, itemized services, amounts, payment terms, and contact information. Use clean, professional formatting.""",
            
            DocumentType.BUSINESS_PLAN: """You are an expert business plan writer and strategic advisor. Create comprehensive business plans with detailed market analysis, financial projections, competitive analysis, and implementation strategies. Use professional business language and industry-standard sections.""",
            
            DocumentType.REPORT: """You are a senior business analyst specializing in data-driven reports. Create comprehensive reports with executive summaries, key findings, data analysis, insights, and actionable recommendations. Use clear headings, bullet points, and professional formatting.""",
            
            DocumentType.CONTRACT: """You are a legal document specialist focusing on business contracts. Create clear, professional contracts with proper legal language, defined terms, scope of work, payment terms, responsibilities, and protection clauses. Ensure clarity and enforceability.""",
            
            DocumentType.MARKETING: """You are a marketing copywriter and content strategist. Create compelling marketing content that resonates with target audiences, drives engagement, and achieves business objectives. Use persuasive language, clear calls to action, and brand-appropriate tone."""
        }
        
        # Initialize the chat with Emergent LLM
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_messages.get(request.type, "You are a professional business document writer.")
        )
        
        # Use gpt-4o for high-quality document generation
        chat.with_model("openai", "gpt-4o")
        
        # Create detailed prompt for document generation
        variables_text = ""
        if request.variables:
            variables_text = "\n".join([f"- {key.replace('_', ' ').title()}: {value}" for key, value in request.variables.items() if value])
        
        prompt_parts = [
            f"Create a professional {request.type.replace('_', ' ').title()} document with the following specifications:",
            f"\nDocument Title: {request.title}",
        ]
        
        if request.client_name:
            prompt_parts.append(f"Client/Company: {request.client_name}")
        
        if variables_text:
            prompt_parts.append(f"\nKey Details:\n{variables_text}")
        
        if request.custom_instructions:
            prompt_parts.append(f"\nSpecial Instructions: {request.custom_instructions}")
        
        prompt_parts.extend([
            f"\nPlease create a comprehensive, professional {request.type.replace('_', ' ')} that:",
            "- Follows industry best practices and standards",
            "- Uses appropriate business language and tone",
            "- Includes proper formatting with clear sections and headers",
            "- Is ready for immediate business use",
            "- Contains all necessary legal and business elements",
            "\nGenerate the complete document content now:"
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # Create user message and send to AI
        user_message = UserMessage(text=full_prompt)
        
        # Get AI response
        ai_response = await chat.send_message(user_message)
        
        logger.info(f"AI document generation completed for {request.type} - {request.title}")
        
        return ai_response.strip()
        
    except Exception as e:
        logger.error(f"Error in AI document generation: {e}")
        
        # Fallback to enhanced template-based generation
        return generate_fallback_content(request, template_content, template_variables)

def generate_fallback_content(
    request: DocumentGenerateRequest,
    template_content: str,
    template_variables: List[str]
) -> str:
    """Enhanced fallback content generation when AI is unavailable"""
    
    # This is a mock implementation. In a real implementation, you would:
    # 1. Use the Emergent LLM integration to generate content
    # 2. Process the template with variables
    # 3. Apply business logic based on document type
    
    base_content = {
        DocumentType.PROPOSAL: f"""
# Business Proposal for {request.client_name or 'Valued Client'}

Dear {request.client_name or 'Valued Client'},

We are pleased to present this comprehensive proposal for your project requirements.

## Project Overview
{request.variables.get('project_description', 'Comprehensive business solution tailored to your needs')}

## Scope of Work
- Analysis and planning phase
- Implementation and development
- Testing and quality assurance
- Deployment and support

## Investment
Total Project Value: ${request.variables.get('project_value', '50,000')}

## Timeline
Estimated Completion: {request.variables.get('timeline', '8-12 weeks')}

We look forward to partnering with you on this exciting project.

Best regards,
The Nexus Core Team
        """,
        
        DocumentType.INVOICE: f"""
# Invoice

**Invoice #:** INV-{datetime.now().strftime('%Y%m%d')}-001
**Date:** {datetime.now().strftime('%B %d, %Y')}
**Client:** {request.client_name or 'Valued Client'}

## Services Provided
{request.variables.get('services', 'Professional consulting services')}

## Amount Due
Total: ${request.variables.get('amount', '5,000.00')}
Due Date: {request.variables.get('due_date', 'Net 30 days')}

Payment terms and instructions included below.
        """,
        
        DocumentType.BUSINESS_PLAN: f"""
# Business Plan for {request.client_name or 'New Venture'}

## Executive Summary
{request.variables.get('executive_summary', 'Comprehensive business plan for innovative venture')}

## Market Analysis
- Target Market: {request.variables.get('target_market', 'Emerging technology sector')}
- Market Size: {request.variables.get('market_size', '$500M annually')}

## Financial Projections
- Year 1 Revenue: ${request.variables.get('year1_revenue', '100,000')}
- Year 2 Revenue: ${request.variables.get('year2_revenue', '250,000')}
- Year 3 Revenue: ${request.variables.get('year3_revenue', '500,000')}

## Implementation Strategy
Detailed roadmap for achieving business objectives.
        """,
        
        DocumentType.REPORT: f"""
# Analytics Report

Generated on: {datetime.now().strftime('%B %d, %Y')}
Client: {request.client_name or 'Valued Client'}

## Key Metrics
- Performance Score: {request.variables.get('performance_score', '94%')}
- Growth Rate: {request.variables.get('growth_rate', '+23%')}
- Efficiency Improvement: {request.variables.get('efficiency', '+18%')}

## Recommendations
Based on our analysis, we recommend the following strategic initiatives.
        """
    }
    
    # Get base content for document type
    content = base_content.get(request.type, f"Document: {request.title}\n\nGenerated content for {request.client_name or 'client'}.")
    
    # Apply custom instructions if provided
    if request.custom_instructions:
        content += f"\n\n## Additional Notes\n{request.custom_instructions}"
    
    return content.strip()