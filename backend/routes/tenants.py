from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field
import uuid
from bson import ObjectId

from database import get_database
from models import Tenant, TenantStatus, User, UserRole

router = APIRouter(prefix="/tenants", tags=["tenants"])
logger = logging.getLogger(__name__)

# Pydantic Models for API
class TenantCreate(BaseModel):
    name: str = Field(description="Tenant organization name")
    subdomain: str = Field(description="Unique subdomain")
    admin_email: str = Field(description="Admin user email")
    admin_first_name: str = Field(description="Admin first name")
    admin_last_name: str = Field(description="Admin last name")
    plan_type: str = Field(default="standard", description="Subscription plan")
    max_users: int = Field(default=50, description="Maximum users allowed")
    max_agents: int = Field(default=20, description="Maximum agents allowed")

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[TenantStatus] = None
    plan_type: Optional[str] = None
    max_users: Optional[int] = None
    max_agents: Optional[int] = None
    branding: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    billing_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None

class TenantResponse(BaseModel):
    id: str
    name: str
    subdomain: str
    status: TenantStatus
    plan_type: str
    max_users: int
    max_agents: int
    current_users: int
    current_agents: int
    storage_used_mb: float
    admin_email: str
    created_at: datetime
    branding: Dict[str, Any]

# Helper Functions
async def get_tenant_by_subdomain(subdomain: str) -> Optional[Tenant]:
    """Get tenant by subdomain"""
    try:
        db = await get_database()
        tenant_doc = await db.tenants.find_one({"subdomain": subdomain})
        if tenant_doc:
            tenant_doc["id"] = str(tenant_doc["_id"])
            tenant_doc.pop("_id", None)
            return Tenant(**tenant_doc)
        return None
    except Exception as e:
        logger.error(f"Error getting tenant by subdomain: {e}")
        return None

async def validate_subdomain_unique(subdomain: str, exclude_id: str = None) -> bool:
    """Check if subdomain is unique"""
    try:
        db = await get_database()
        query = {"subdomain": subdomain}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        
        existing = await db.tenants.find_one(query)
        return existing is None
    except Exception as e:
        logger.error(f"Error validating subdomain: {e}")
        return False

# API Endpoints
@router.post("/", response_model=TenantResponse)
async def create_tenant(tenant_data: TenantCreate):
    """Create a new tenant (Super Admin only)"""
    try:
        # Validate subdomain is unique
        if not await validate_subdomain_unique(tenant_data.subdomain):
            raise HTTPException(status_code=400, detail="Subdomain already exists")
        
        db = await get_database()
        
        # Create tenant
        tenant = Tenant(
            name=tenant_data.name,
            subdomain=tenant_data.subdomain,
            admin_email=tenant_data.admin_email,
            plan_type=tenant_data.plan_type,
            max_users=tenant_data.max_users,
            max_agents=tenant_data.max_agents,
            status=TenantStatus.ACTIVE,
            current_users=1,  # Admin user
            branding={
                "company_name": tenant_data.name,
                "primary_color": "#3b82f6",
                "logo_url": None
            }
        )
        
        # Insert tenant
        tenant_dict = tenant.dict()
        tenant_dict.pop("id")
        result = await db.tenants.insert_one(tenant_dict)
        tenant_id = str(result.inserted_id)
        
        # Create admin user for the tenant
        admin_user = User(
            tenant_id=tenant_id,
            email=tenant_data.admin_email,
            username=f"{tenant_data.admin_first_name.lower()}.{tenant_data.admin_last_name.lower()}",
            password_hash="temp_hash_needs_proper_implementation",  # TODO: Implement proper password hashing
            first_name=tenant_data.admin_first_name,
            last_name=tenant_data.admin_last_name,
            role=UserRole.TENANT_ADMIN,
            is_active=True,
            is_verified=True
        )
        
        # Insert admin user
        user_dict = admin_user.dict()
        user_dict.pop("id")
        await db.users.insert_one(user_dict)
        
        # Return created tenant
        created_tenant = await db.tenants.find_one({"_id": result.inserted_id})
        created_tenant["id"] = str(created_tenant["_id"])
        created_tenant.pop("_id", None)
        
        return TenantResponse(**created_tenant)
        
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create tenant")

@router.get("/", response_model=List[TenantResponse])
async def get_tenants(skip: int = 0, limit: int = 100):
    """Get all tenants (Super Admin only)"""
    try:
        db = await get_database()
        
        cursor = db.tenants.find().skip(skip).limit(limit)
        tenants = []
        
        async for tenant_doc in cursor:
            tenant_doc["id"] = str(tenant_doc["_id"])
            tenant_doc.pop("_id", None)
            tenants.append(TenantResponse(**tenant_doc))
        
        return tenants
        
    except Exception as e:
        logger.error(f"Error fetching tenants: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tenants")

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str):
    """Get specific tenant details"""
    try:
        db = await get_database()
        tenant_doc = await db.tenants.find_one({"_id": ObjectId(tenant_id)})
        
        if not tenant_doc:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant_doc["id"] = str(tenant_doc["_id"])
        tenant_doc.pop("_id", None)
        
        return TenantResponse(**tenant_doc)
        
    except Exception as e:
        logger.error(f"Error fetching tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tenant")

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, update_data: TenantUpdate):
    """Update tenant information (Super Admin or Tenant Admin only)"""
    try:
        db = await get_database()
        
        # Check if tenant exists
        existing_tenant = await db.tenants.find_one({"_id": ObjectId(tenant_id)})
        if not existing_tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Validate subdomain uniqueness if being updated
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        if "subdomain" in update_dict:
            if not await validate_subdomain_unique(update_dict["subdomain"], tenant_id):
                raise HTTPException(status_code=400, detail="Subdomain already exists")
        
        # Add updated timestamp
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update tenant
        await db.tenants.update_one(
            {"_id": ObjectId(tenant_id)},
            {"$set": update_dict}
        )
        
        # Return updated tenant
        updated_tenant = await db.tenants.find_one({"_id": ObjectId(tenant_id)})
        updated_tenant["id"] = str(updated_tenant["_id"])
        updated_tenant.pop("_id", None)
        
        return TenantResponse(**updated_tenant)
        
    except Exception as e:
        logger.error(f"Error updating tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to update tenant")

@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """Delete tenant (Super Admin only)"""
    try:
        db = await get_database()
        
        # Check if tenant exists
        existing_tenant = await db.tenants.find_one({"_id": ObjectId(tenant_id)})
        if not existing_tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # TODO: Implement proper tenant deletion with data cleanup
        # This should delete all tenant-related data (users, agents, leads, etc.)
        
        # For now, just mark as suspended
        await db.tenants.update_one(
            {"_id": ObjectId(tenant_id)},
            {"$set": {"status": TenantStatus.SUSPENDED, "updated_at": datetime.utcnow()}}
        )
        
        return {"message": "Tenant suspended successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting tenant: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete tenant")

@router.get("/subdomain/{subdomain}", response_model=TenantResponse)
async def get_tenant_by_subdomain_endpoint(subdomain: str):
    """Get tenant by subdomain (for login/routing purposes)"""
    try:
        tenant = await get_tenant_by_subdomain(subdomain)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Convert to response format
        return TenantResponse(**tenant.dict())
        
    except Exception as e:
        logger.error(f"Error getting tenant by subdomain: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch tenant")

@router.post("/{tenant_id}/usage/update")
async def update_tenant_usage(tenant_id: str, usage_data: Dict[str, Any]):
    """Update tenant usage statistics"""
    try:
        db = await get_database()
        
        # Count current users and agents
        current_users = await db.users.count_documents({"tenant_id": tenant_id, "is_active": True})
        current_agents = await db.agents.count_documents({"tenant_id": tenant_id})
        
        # Update usage
        await db.tenants.update_one(
            {"_id": ObjectId(tenant_id)},
            {
                "$set": {
                    "current_users": current_users,
                    "current_agents": current_agents,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Usage updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating tenant usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to update usage")