from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List, Optional
import os
import uuid
import logging
from datetime import datetime

from models import (
    KnowledgeBase, KnowledgeBaseCreate, KnowledgeCategory,
    KnowledgeFile
)
from database import get_knowledge_collection, get_agents_collection

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = logging.getLogger(__name__)

# Create upload directory if it doesn't exist
UPLOAD_DIR = "/app/uploads/knowledge"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[KnowledgeBase])
async def get_knowledge_base(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """Get knowledge base files with filtering"""
    try:
        collection = await get_knowledge_collection()
        
        # Build filter
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if search:
            filter_dict["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
                {"tags": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
        knowledge_data = await cursor.to_list(limit)
        
        return [KnowledgeBase(**kb) for kb in knowledge_data]
        
    except Exception as e:
        logger.error(f"Error getting knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve knowledge base")

@router.get("/categories", response_model=List[KnowledgeCategory])
async def get_knowledge_categories():
    """Get all knowledge categories with file counts"""
    try:
        collection = await get_knowledge_collection()
        
        # Aggregate categories with counts
        pipeline = [
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = await collection.aggregate(pipeline).to_list(100)
        
        categories = []
        for result in results:
            categories.append(KnowledgeCategory(
                name=result["_id"],
                description=f"Knowledge files in {result['_id']} category",
                file_count=result["count"]
            ))
        
        return categories
        
    except Exception as e:
        logger.error(f"Error getting knowledge categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve categories")

@router.post("/upload", response_model=KnowledgeBase)
async def upload_knowledge_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    tags: str = Form(""),  # Comma-separated tags
    agent_ids: str = Form("")  # Comma-separated agent IDs
):
    """Upload a new knowledge file"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse tags and agent IDs
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        agent_ids_list = [aid.strip() for aid in agent_ids.split(",") if aid.strip()]
        
        # Create knowledge base entry
        kb_data = KnowledgeBaseCreate(
            title=title,
            description=description,
            category=category,
            file_type=file.content_type or "application/octet-stream",
            tags=tags_list,
            agent_ids=agent_ids_list
        )
        
        knowledge_entry = KnowledgeBase(
            **kb_data.dict(),
            file_size=len(content),
            file_path=file_path,
            content_preview=generate_content_preview(content, file.content_type),
            processed=False
        )
        
        # Save to database
        collection = await get_knowledge_collection()
        await collection.insert_one(knowledge_entry.dict())
        
        # Update agent knowledge bases
        if agent_ids_list:
            await update_agent_knowledge_bases(agent_ids_list, knowledge_entry)
        
        logger.info(f"Uploaded knowledge file: {title} ({unique_filename})")
        return knowledge_entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading knowledge file: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload knowledge file")

@router.get("/{knowledge_id}", response_model=KnowledgeBase)
async def get_knowledge_item(knowledge_id: str):
    """Get a specific knowledge base item"""
    try:
        collection = await get_knowledge_collection()
        kb_data = await collection.find_one({"id": knowledge_id})
        
        if not kb_data:
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        
        return KnowledgeBase(**kb_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge item {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve knowledge item")

@router.delete("/{knowledge_id}")
async def delete_knowledge_item(knowledge_id: str):
    """Delete a knowledge base item"""
    try:
        collection = await get_knowledge_collection()
        
        # Get knowledge item
        kb_data = await collection.find_one({"id": knowledge_id})
        if not kb_data:
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        
        # Delete file from filesystem
        try:
            if os.path.exists(kb_data["file_path"]):
                os.remove(kb_data["file_path"])
        except Exception as e:
            logger.warning(f"Failed to delete file {kb_data['file_path']}: {e}")
        
        # Delete from database
        await collection.delete_one({"id": knowledge_id})
        
        # Remove from agent knowledge bases
        if kb_data.get("agent_ids"):
            await remove_from_agent_knowledge_bases(kb_data["agent_ids"], knowledge_id)
        
        return {"message": "Knowledge item deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge item {knowledge_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete knowledge item")

@router.post("/{knowledge_id}/assign-agents")
async def assign_knowledge_to_agents(knowledge_id: str, agent_ids: List[str]):
    """Assign knowledge item to specific agents"""
    try:
        collection = await get_knowledge_collection()
        
        # Check if knowledge item exists
        kb_data = await collection.find_one({"id": knowledge_id})
        if not kb_data:
            raise HTTPException(status_code=404, detail="Knowledge item not found")
        
        # Update knowledge item with new agent assignments
        await collection.update_one(
            {"id": knowledge_id},
            {
                "$set": {
                    "agent_ids": agent_ids,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update agent knowledge bases
        knowledge_entry = KnowledgeBase(**kb_data)
        await update_agent_knowledge_bases(agent_ids, knowledge_entry)
        
        return {"message": "Knowledge assigned to agents successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning knowledge to agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign knowledge to agents")

@router.get("/stats/summary")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        collection = await get_knowledge_collection()
        
        # Total files
        total_files = await collection.count_documents({})
        
        # Files by category
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_stats = await collection.aggregate(category_pipeline).to_list(100)
        
        # Total file size
        size_pipeline = [
            {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}}}
        ]
        size_result = await collection.aggregate(size_pipeline).to_list(1)
        total_size = size_result[0]["total_size"] if size_result else 0
        
        # Processed vs unprocessed
        processed_count = await collection.count_documents({"processed": True})
        unprocessed_count = await collection.count_documents({"processed": False})
        
        return {
            "total_files": total_files,
            "categories": {item["_id"]: item["count"] for item in category_stats},
            "total_size_bytes": total_size,
            "processed_files": processed_count,
            "unprocessed_files": unprocessed_count,
            "knowledge_utilization": 98.5  # Mock value
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve knowledge statistics")

async def update_agent_knowledge_bases(agent_ids: List[str], knowledge_entry: KnowledgeBase):
    """Update agent knowledge bases with new knowledge file"""
    try:
        agents_collection = await get_agents_collection()
        
        knowledge_file = KnowledgeFile(
            filename=knowledge_entry.title,
            file_type=knowledge_entry.file_type,
            file_size=knowledge_entry.file_size,
            file_path=knowledge_entry.file_path
        )
        
        # Add knowledge file to each agent
        for agent_id in agent_ids:
            await agents_collection.update_one(
                {"id": agent_id},
                {
                    "$push": {"knowledge_base": knowledge_file.dict()},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
    except Exception as e:
        logger.error(f"Error updating agent knowledge bases: {e}")

async def remove_from_agent_knowledge_bases(agent_ids: List[str], knowledge_id: str):
    """Remove knowledge file from agent knowledge bases"""
    try:
        agents_collection = await get_agents_collection()
        
        for agent_id in agent_ids:
            await agents_collection.update_one(
                {"id": agent_id},
                {
                    "$pull": {"knowledge_base": {"filename": knowledge_id}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
    except Exception as e:
        logger.error(f"Error removing from agent knowledge bases: {e}")

def generate_content_preview(content: bytes, content_type: str) -> str:
    """Generate a preview of the file content"""
    try:
        if content_type and content_type.startswith("text/"):
            # For text files, return first 200 characters
            text_content = content.decode("utf-8", errors="ignore")
            return text_content[:200] + "..." if len(text_content) > 200 else text_content
        else:
            # For binary files, return basic info
            return f"Binary file ({len(content)} bytes)"
    except Exception:
        return "Unable to generate preview"