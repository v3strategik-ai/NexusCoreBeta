from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enterprise Enums for Phase 6C
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"

class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

# Enums for various status and types
class AgentStatus(str, Enum):
    ACTIVE = "active"
    TRAINING = "training"
    IDLE = "idle"
    OFFLINE = "offline"

class AutonomyLevel(str, Enum):
    BASIC = "Basic"
    MEDIUM = "Medium"
    HIGH = "High"
    QUANTUM = "Quantum"

class LeadStatus(str, Enum):
    COLD = "cold"
    WARM = "warm"
    HOT = "hot"
    CONVERTED = "converted"
    LOST = "lost"

class DocumentType(str, Enum):
    PROPOSAL = "proposal"
    INVOICE = "invoice"
    BUSINESS_PLAN = "business_plan"
    REPORT = "report"
    CONTRACT = "contract"
    MARKETING = "marketing"

class WorkflowStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

# Base Models
class BaseEntity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Enterprise Models for Phase 6C: Multi-Tenancy & RBAC
class Tenant(BaseEntity):
    name: str = Field(description="Tenant organization name")
    subdomain: str = Field(description="Unique subdomain for tenant")
    status: TenantStatus = TenantStatus.ACTIVE
    plan_type: str = Field(default="standard", description="Subscription plan")
    max_users: int = Field(default=50, description="Maximum allowed users")
    max_agents: int = Field(default=20, description="Maximum allowed AI agents")
    
    # White-label customization
    branding: Dict[str, Any] = Field(default={}, description="Custom branding settings")
    settings: Dict[str, Any] = Field(default={}, description="Tenant-specific settings")
    
    # Contact and billing
    admin_email: str
    billing_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    
    # Usage tracking
    current_users: int = Field(default=0)
    current_agents: int = Field(default=0)
    storage_used_mb: float = Field(default=0.0)

class Permission(BaseModel):
    resource: str = Field(description="Resource name (e.g., 'agents', 'workflows')")
    action: PermissionType = Field(description="Permission type")
    
class Role(BaseModel):
    name: UserRole
    display_name: str
    description: str
    permissions: List[Permission] = Field(default=[])
    is_system_role: bool = Field(default=True, description="System-defined or custom role")

class User(BaseEntity):
    tenant_id: str = Field(description="Tenant this user belongs to")
    email: str = Field(unique=True, description="User email address")
    username: str = Field(description="Display username")
    password_hash: str = Field(description="Hashed password")
    
    # Profile information
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    
    # Role and permissions
    role: UserRole = UserRole.EMPLOYEE
    permissions: List[Permission] = Field(default=[])
    
    # Status and settings
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default={})
    
    # Activity tracking
    login_count: int = Field(default=0)
    failed_login_attempts: int = Field(default=0)
    last_failed_login: Optional[datetime] = None

class AuditLog(BaseEntity):
    tenant_id: str = Field(description="Tenant for this audit entry")
    user_id: str = Field(description="User who performed the action")
    user_email: str = Field(description="Email of user who performed action")
    
    # Action details
    action: str = Field(description="Action performed (e.g., 'create_agent', 'delete_lead')")
    resource_type: str = Field(description="Type of resource affected")
    resource_id: Optional[str] = Field(description="ID of affected resource")
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    
    # Changes tracking
    old_values: Optional[Dict[str, Any]] = Field(default=None)
    new_values: Optional[Dict[str, Any]] = Field(default=None)
    
    # Metadata
    success: bool = Field(default=True)
    error_message: Optional[str] = None
    session_id: Optional[str] = None

# Tenant-aware Base Model
class TenantEntity(BaseEntity):
    tenant_id: str = Field(description="Tenant this entity belongs to")
    created_by: str = Field(description="User ID who created this entity")
    updated_by: Optional[str] = Field(description="User ID who last updated this entity")

# Digital Employee (AI Agent) Models
class KnowledgeFile(BaseModel):
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    file_path: str
    processed: bool = False

class Agent(TenantEntity):
    name: str
    type: str
    status: AgentStatus
    personality: str
    specialization: str
    autonomy_level: AutonomyLevel
    efficiency: float = 0.0
    tasks_completed: int = 0
    learning_progress: float = 0.0
    knowledge_base: List[KnowledgeFile] = []
    last_active: datetime = Field(default_factory=datetime.utcnow)
    configuration: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}

class AgentCreate(BaseModel):
    name: str
    type: str
    personality: str
    specialization: str
    autonomy_level: AutonomyLevel
    configuration: Optional[Dict[str, Any]] = {}

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[AgentStatus] = None
    personality: Optional[str] = None
    specialization: Optional[str] = None
    autonomy_level: Optional[AutonomyLevel] = None
    efficiency: Optional[float] = None
    learning_progress: Optional[float] = None
    configuration: Optional[Dict[str, Any]] = None

# CRM Models
class Lead(BaseEntity):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    status: LeadStatus
    value: float = 0.0
    source: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    last_contact: Optional[datetime] = None
    notes: List[str] = []
    score: float = 0.0  # AI-generated lead score
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}

class LeadCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    status: LeadStatus = LeadStatus.COLD
    value: float = 0.0
    source: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    notes: List[str] = []
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: Optional[LeadStatus] = None
    value: Optional[float] = None
    source: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    notes: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None

# Knowledge Hub Models
class KnowledgeCategory(BaseModel):
    name: str
    description: str
    file_count: int = 0
    icon: str = "folder"

class KnowledgeBase(BaseEntity):
    title: str
    description: Optional[str] = None
    category: str
    file_type: str
    file_size: int
    file_path: str
    content_preview: Optional[str] = None
    tags: List[str] = []
    processed: bool = False
    agent_ids: List[str] = []  # Which agents have access to this knowledge
    metadata: Dict[str, Any] = {}

class KnowledgeBaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    file_type: str
    tags: List[str] = []
    agent_ids: List[str] = []

# Document Generation Models
class DocumentTemplate(BaseEntity):
    name: str
    type: DocumentType
    description: str
    template_content: str
    variables: List[str] = []  # Variables that can be filled
    is_active: bool = True

class GeneratedDocument(BaseEntity):
    title: str
    type: DocumentType
    template_id: Optional[str] = None
    content: str
    variables_used: Dict[str, Any] = {}
    generated_by_agent: Optional[str] = None
    client_name: Optional[str] = None
    file_path: Optional[str] = None

class DocumentGenerateRequest(BaseModel):
    title: str
    type: DocumentType
    template_id: Optional[str] = None
    variables: Dict[str, Any] = {}
    client_name: Optional[str] = None
    agent_id: Optional[str] = None
    custom_instructions: Optional[str] = None

# Automation Workflow Models
class WorkflowStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str  # "email", "api_call", "data_processing", etc.
    configuration: Dict[str, Any] = {}
    order: int = 0

class Workflow(BaseEntity):
    name: str
    description: str
    status: WorkflowStatus
    trigger_type: str  # "manual", "scheduled", "event_based"
    trigger_config: Dict[str, Any] = {}
    steps: List[WorkflowStep] = []
    agent_id: Optional[str] = None
    last_run: Optional[datetime] = None
    run_count: int = 0
    success_rate: float = 0.0

class WorkflowCreate(BaseModel):
    name: str
    description: str
    trigger_type: str
    trigger_config: Dict[str, Any] = {}
    steps: List[WorkflowStep] = []
    agent_id: Optional[str] = None

# Analytics and Metrics Models
class SystemMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    active_agents: int = 0
    total_tasks_completed: int = 0
    total_revenue_generated: float = 0.0
    system_efficiency: float = 0.0
    neural_processing_power: float = 0.0
    knowledge_base_utilization: float = 0.0
    autonomous_decision_rate: float = 0.0
    learning_acceleration: float = 0.0

class AgentActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    agent_name: str
    activity_type: str
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    autonomy_level: str
    metadata: Dict[str, Any] = {}

# User and Authentication Models
class User(BaseEntity):
    username: str
    email: str
    full_name: str
    is_active: bool = True
    is_admin: bool = False
    preferences: Dict[str, Any] = {}

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None

# Response Models
class AgentListResponse(BaseModel):
    agents: List[Agent]
    total: int

class LeadListResponse(BaseModel):
    leads: List[Lead]
    total: int

class SystemDashboard(BaseModel):
    metrics: SystemMetrics
    recent_activities: List[AgentActivity]
    agent_summary: Dict[str, Any]
    revenue_summary: Dict[str, Any]

# AI Chat Models
class ChatMessage(BaseEntity):
    agent_id: str
    user_message: str
    ai_response: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class ChatRequest(BaseModel):
    agent_id: str
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent_name: str
    agent_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)