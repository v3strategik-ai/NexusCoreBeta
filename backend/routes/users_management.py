from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field
import uuid
import hashlib
from bson import ObjectId

from database import get_database
from models import User, UserRole, Permission, PermissionType, AuditLog

router = APIRouter(prefix="/users", tags=["user-management"])
logger = logging.getLogger(__name__)

# Pydantic Models for API
class UserCreate(BaseModel):
    tenant_id: str
    email: str
    username: str
    first_name: str
    last_name: str
    password: str
    role: UserRole = UserRole.EMPLOYEE
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    username: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    login_count: int

class PasswordReset(BaseModel):
    current_password: str
    new_password: str

class RolePermissions(BaseModel):
    role: UserRole
    permissions: List[str]

# Permission Definitions
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [
        "tenants.read", "tenants.write", "tenants.delete", "tenants.admin",
        "users.read", "users.write", "users.delete", "users.admin",
        "agents.read", "agents.write", "agents.delete", "agents.admin",
        "leads.read", "leads.write", "leads.delete", "leads.admin",
        "workflows.read", "workflows.write", "workflows.delete", "workflows.admin",
        "analytics.read", "analytics.admin", "audit.read", "system.admin"
    ],
    UserRole.TENANT_ADMIN: [
        "users.read", "users.write", "users.delete",
        "agents.read", "agents.write", "agents.delete", "agents.admin",
        "leads.read", "leads.write", "leads.delete", "leads.admin",
        "workflows.read", "workflows.write", "workflows.delete", "workflows.admin",
        "analytics.read", "analytics.admin", "audit.read", "tenant.admin"
    ],
    UserRole.MANAGER: [
        "users.read", "agents.read", "agents.write", "agents.admin",
        "leads.read", "leads.write", "leads.admin",
        "workflows.read", "workflows.write", "workflows.admin",
        "analytics.read", "reports.read"
    ],
    UserRole.EMPLOYEE: [
        "agents.read", "leads.read", "leads.write",
        "workflows.read", "workflows.write",
        "analytics.read"
    ]
}

# Helper Functions
def hash_password(password: str) -> str:
    """Simple password hashing (use proper bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

async def check_user_permissions(user_id: str, required_permission: str) -> bool:
    """Check if user has required permission"""
    try:
        db = await get_database()
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user_doc:
            return False
        
        user_role = user_doc.get("role")
        role_permissions = ROLE_PERMISSIONS.get(user_role, [])
        
        return required_permission in role_permissions
        
    except Exception as e:
        logger.error(f"Error checking permissions: {e}")
        return False

async def log_user_action(user_id: str, tenant_id: str, action: str, resource_type: str, 
                         resource_id: str = None, old_values: Dict = None, 
                         new_values: Dict = None, success: bool = True, 
                         error_message: str = None):
    """Log user action to audit trail"""
    try:
        db = await get_database()
        
        # Get user details
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        user_email = user_doc.get("email", "unknown") if user_doc else "unknown"
        
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            success=success,
            error_message=error_message
        )
        
        audit_dict = audit_log.dict()
        audit_dict.pop("id")
        await db.audit_logs.insert_one(audit_dict)
        
    except Exception as e:
        logger.error(f"Error logging user action: {e}")

# API Endpoints
@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Create a new user (Admin only)"""
    try:
        db = await get_database()
        
        # Check if email already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Verify tenant exists
        tenant = await db.tenants.find_one({"_id": ObjectId(user_data.tenant_id)})
        if not tenant:
            raise HTTPException(status_code=400, detail="Invalid tenant")
        
        # Check tenant user limit
        current_users = await db.users.count_documents({"tenant_id": user_data.tenant_id, "is_active": True})
        if current_users >= tenant.get("max_users", 50):
            raise HTTPException(status_code=400, detail="Tenant user limit exceeded")
        
        # Create user
        user = User(
            tenant_id=user_data.tenant_id,
            email=user_data.email,
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            role=user_data.role,
            is_active=True,
            is_verified=True
        )
        
        # Insert user
        user_dict = user.dict()
        user_dict.pop("id")
        result = await db.users.insert_one(user_dict)
        
        # Update tenant user count
        await db.tenants.update_one(
            {"_id": ObjectId(user_data.tenant_id)},
            {"$inc": {"current_users": 1}}
        )
        
        # Return created user (without password)
        created_user = await db.users.find_one({"_id": result.inserted_id})
        created_user["id"] = str(created_user["_id"])
        created_user.pop("_id", None)
        created_user.pop("password_hash", None)
        
        return UserResponse(**created_user)
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")

@router.get("/tenant/{tenant_id}", response_model=List[UserResponse])
async def get_tenant_users(tenant_id: str, skip: int = 0, limit: int = 100):
    """Get all users for a tenant"""
    try:
        db = await get_database()
        
        cursor = db.users.find({"tenant_id": tenant_id}).skip(skip).limit(limit)
        users = []
        
        async for user_doc in cursor:
            user_doc["id"] = str(user_doc["_id"])
            user_doc.pop("_id", None)
            user_doc.pop("password_hash", None)  # Don't return password hash
            users.append(UserResponse(**user_doc))
        
        return users
        
    except Exception as e:
        logger.error(f"Error fetching tenant users: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get specific user details"""
    try:
        db = await get_database()
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_doc["id"] = str(user_doc["_id"])
        user_doc.pop("_id", None)
        user_doc.pop("password_hash", None)
        
        return UserResponse(**user_doc)
        
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, update_data: UserUpdate):
    """Update user information"""
    try:
        db = await get_database()
        
        # Check if user exists
        existing_user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update dict
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update user
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_dict}
        )
        
        # Log the action
        await log_user_action(
            user_id=user_id,
            tenant_id=existing_user["tenant_id"],
            action="update_user",
            resource_type="user",
            resource_id=user_id,
            old_values={"role": existing_user.get("role")},
            new_values=update_dict
        )
        
        # Return updated user
        updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
        updated_user["id"] = str(updated_user["_id"])
        updated_user.pop("_id", None)
        updated_user.pop("password_hash", None)
        
        return UserResponse(**updated_user)
        
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Delete/deactivate user"""
    try:
        db = await get_database()
        
        # Check if user exists
        existing_user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Deactivate instead of delete to preserve audit trail
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        # Update tenant user count
        await db.tenants.update_one(
            {"_id": ObjectId(existing_user["tenant_id"])},
            {"$inc": {"current_users": -1}}
        )
        
        # Log the action
        await log_user_action(
            user_id=user_id,
            tenant_id=existing_user["tenant_id"],
            action="delete_user",
            resource_type="user",
            resource_id=user_id
        )
        
        return {"message": "User deactivated successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user")

@router.post("/{user_id}/reset-password")
async def reset_password(user_id: str, password_data: PasswordReset):
    """Reset user password"""
    try:
        db = await get_database()
        
        # Get user
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not verify_password(password_data.current_password, user_doc["password_hash"]):
            raise HTTPException(status_code=400, detail="Invalid current password")
        
        # Update password
        new_hash = hash_password(password_data.new_password)
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"password_hash": new_hash, "updated_at": datetime.utcnow()}}
        )
        
        # Log the action
        await log_user_action(
            user_id=user_id,
            tenant_id=user_doc["tenant_id"],
            action="reset_password",
            resource_type="user",
            resource_id=user_id
        )
        
        return {"message": "Password reset successfully"}
        
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset password")

@router.get("/roles/permissions", response_model=Dict[UserRole, List[str]])
async def get_role_permissions():
    """Get all role permissions"""
    return ROLE_PERMISSIONS

@router.get("/{user_id}/permissions", response_model=List[str])
async def get_user_permissions(user_id: str):
    """Get user's effective permissions"""
    try:
        db = await get_database()
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_role = user_doc.get("role")
        return ROLE_PERMISSIONS.get(user_role, [])
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get permissions")

@router.post("/{user_id}/login")
async def log_user_login(user_id: str, login_data: Dict[str, Any]):
    """Log user login activity"""
    try:
        db = await get_database()
        
        # Update user login stats
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {"last_login": datetime.utcnow()},
                "$inc": {"login_count": 1}
            }
        )
        
        # Log the action
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        if user_doc:
            await log_user_action(
                user_id=user_id,
                tenant_id=user_doc["tenant_id"],
                action="user_login",
                resource_type="user",
                resource_id=user_id
            )
        
        return {"message": "Login logged successfully"}
        
    except Exception as e:
        logger.error(f"Error logging login: {e}")
        raise HTTPException(status_code=500, detail="Failed to log login")