from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from models import (
    Lead, LeadCreate, LeadUpdate, LeadListResponse, LeadStatus
)
from database import get_leads_collection, get_agents_collection

router = APIRouter(prefix="/crm", tags=["crm"])
logger = logging.getLogger(__name__)

@router.get("/leads", response_model=LeadListResponse)
async def get_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[LeadStatus] = None,
    assigned_agent_id: Optional[str] = None,
    search: Optional[str] = None
):
    """Get list of all leads with filtering options"""
    try:
        collection = await get_leads_collection()
        
        # Build filter
        filter_dict = {}
        if status:
            filter_dict["status"] = status
        if assigned_agent_id:
            filter_dict["assigned_agent_id"] = assigned_agent_id
        if search:
            filter_dict["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}}
            ]
        
        # Get total count
        total = await collection.count_documents(filter_dict)
        
        # Get leads with pagination
        cursor = collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
        leads_data = await cursor.to_list(limit)
        
        leads = [Lead(**lead) for lead in leads_data]
        
        return LeadListResponse(leads=leads, total=total)
        
    except Exception as e:
        logger.error(f"Error getting leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve leads")

@router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(lead_id: str):
    """Get a specific lead by ID"""
    try:
        collection = await get_leads_collection()
        lead_data = await collection.find_one({"id": lead_id})
        
        if not lead_data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        return Lead(**lead_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve lead")

@router.post("/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate):
    """Create a new lead"""
    try:
        collection = await get_leads_collection()
        
        # Check if email already exists
        existing_lead = await collection.find_one({"email": lead_data.email})
        if existing_lead:
            raise HTTPException(status_code=400, detail="Lead with this email already exists")
        
        # Get agent name if agent is assigned
        assigned_agent_name = None
        if lead_data.assigned_agent_id:
            agents_collection = await get_agents_collection()
            agent = await agents_collection.find_one({"id": lead_data.assigned_agent_id})
            if agent:
                assigned_agent_name = agent.get("name")
        
        # Create lead object with AI score (mock for now)
        lead = Lead(
            **lead_data.dict(),
            assigned_agent_name=assigned_agent_name,
            score=calculate_lead_score(lead_data),  # AI scoring function
            last_contact=datetime.utcnow() if lead_data.assigned_agent_id else None
        )
        
        # Insert into database
        await collection.insert_one(lead.dict())
        
        logger.info(f"Created new lead: {lead.name} ({lead.email})")
        return lead
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead")

@router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(lead_id: str, lead_update: LeadUpdate):
    """Update a lead"""
    try:
        collection = await get_leads_collection()
        
        # Get existing lead
        existing_lead = await collection.find_one({"id": lead_id})
        if not existing_lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Prepare update data
        update_data = {k: v for k, v in lead_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        # Get agent name if agent is assigned
        if "assigned_agent_id" in update_data and update_data["assigned_agent_id"]:
            agents_collection = await get_agents_collection()
            agent = await agents_collection.find_one({"id": update_data["assigned_agent_id"]})
            if agent:
                update_data["assigned_agent_name"] = agent.get("name")
                update_data["last_contact"] = datetime.utcnow()
        
        # Recalculate AI score if relevant fields changed
        if any(field in update_data for field in ["value", "status", "company"]):
            # Create temporary lead object for scoring
            temp_lead_data = {**existing_lead, **update_data}
            temp_lead = LeadCreate(**{k: v for k, v in temp_lead_data.items() if k in LeadCreate.__fields__})
            update_data["score"] = calculate_lead_score(temp_lead)
        
        # Update lead
        await collection.update_one(
            {"id": lead_id},
            {"$set": update_data}
        )
        
        # Get updated lead
        updated_lead_data = await collection.find_one({"id": lead_id})
        updated_lead = Lead(**updated_lead_data)
        
        logger.info(f"Updated lead: {lead_id}")
        return updated_lead
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update lead")

@router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    """Delete a lead"""
    try:
        collection = await get_leads_collection()
        
        # Check if lead exists
        lead_data = await collection.find_one({"id": lead_id})
        if not lead_data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Delete lead
        await collection.delete_one({"id": lead_id})
        
        logger.info(f"Deleted lead: {lead_id}")
        return {"message": "Lead deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete lead")

@router.post("/leads/{lead_id}/assign-agent")
async def assign_agent_to_lead(lead_id: str, agent_id: str):
    """Assign an agent to a lead"""
    try:
        leads_collection = await get_leads_collection()
        agents_collection = await get_agents_collection()
        
        # Check if lead exists
        lead = await leads_collection.find_one({"id": lead_id})
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Check if agent exists
        agent = await agents_collection.find_one({"id": agent_id})
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Update lead
        await leads_collection.update_one(
            {"id": lead_id},
            {
                "$set": {
                    "assigned_agent_id": agent_id,
                    "assigned_agent_name": agent.get("name"),
                    "last_contact": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": f"Lead assigned to agent {agent.get('name')} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning agent to lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign agent to lead")

@router.get("/analytics/summary")
async def get_crm_analytics():
    """Get CRM analytics summary"""
    try:
        collection = await get_leads_collection()
        
        # Get total leads count
        total_leads = await collection.count_documents({})
        
        # Get leads by status
        status_counts = {}
        for status in LeadStatus:
            count = await collection.count_documents({"status": status})
            status_counts[status] = count
        
        # Calculate total pipeline value
        pipeline = collection.aggregate([
            {"$group": {"_id": None, "total_value": {"$sum": "$value"}}}
        ])
        pipeline_result = await pipeline.to_list(1)
        total_pipeline_value = pipeline_result[0]["total_value"] if pipeline_result else 0
        
        # Calculate average lead score
        score_pipeline = collection.aggregate([
            {"$group": {"_id": None, "avg_score": {"$avg": "$score"}}}
        ])
        score_result = await score_pipeline.to_list(1)
        avg_score = score_result[0]["avg_score"] if score_result else 0
        
        # Get conversion rate (mock calculation)
        converted_count = status_counts.get(LeadStatus.CONVERTED, 0)
        conversion_rate = (converted_count / total_leads * 100) if total_leads > 0 else 0
        
        return {
            "total_leads": total_leads,
            "status_breakdown": status_counts,
            "total_pipeline_value": total_pipeline_value,
            "average_lead_score": round(avg_score, 2),
            "conversion_rate": round(conversion_rate, 2),
            "ai_predictions_accuracy": 97.2  # Mock value
        }
        
    except Exception as e:
        logger.error(f"Error getting CRM analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve CRM analytics")

def calculate_lead_score(lead_data: LeadCreate) -> float:
    """Calculate AI-powered lead score (simplified algorithm)"""
    score = 0.0
    
    # Base score based on status
    status_scores = {
        LeadStatus.HOT: 80,
        LeadStatus.WARM: 60,
        LeadStatus.COLD: 30,
        LeadStatus.CONVERTED: 100,
        LeadStatus.LOST: 0
    }
    score += status_scores.get(lead_data.status, 30)
    
    # Value-based scoring
    if lead_data.value > 100000:
        score += 15
    elif lead_data.value > 50000:
        score += 10
    elif lead_data.value > 10000:
        score += 5
    
    # Company presence bonus
    if lead_data.company:
        score += 5
    
    # Phone number bonus
    if lead_data.phone:
        score += 5
    
    # Ensure score is between 0 and 100
    return min(max(score, 0), 100)