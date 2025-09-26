from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field
import json
import uuid
from enum import Enum
import asyncio
from bson import ObjectId

from database import (
    get_leads_collection,
    get_activities_collection,
    get_agents_collection,
    get_workflows_collection,
    get_documents_collection
)

router = APIRouter(prefix="/workflow-engine", tags=["workflow-engine"])
logger = logging.getLogger(__name__)

# Enums for Workflow Engine
class TriggerType(str, Enum):
    MANUAL = "manual"
    TIME_BASED = "time_based"
    EVENT_BASED = "event_based"
    CONDITION_BASED = "condition_based"
    WEBHOOK = "webhook"
    API_CALL = "api_call"

class ActionType(str, Enum):
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    UPDATE_LEAD = "update_lead"
    ASSIGN_AGENT = "assign_agent"
    GENERATE_DOCUMENT = "generate_document"
    WAIT_DELAY = "wait_delay"
    WEBHOOK_POST = "webhook_post"
    API_REQUEST = "api_request"
    CONDITIONAL_BRANCH = "conditional_branch"
    APPROVAL_REQUEST = "approval_request"
    NOTIFICATION = "notification"

class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    MATCHES_REGEX = "matches_regex"

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"

class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"
    APPROVED = "approved"
    REJECTED = "rejected"

# Pydantic Models
class WorkflowCondition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    field: str = Field(description="Field to evaluate (e.g., 'lead.score', 'lead.status')")
    operator: ConditionOperator
    value: Union[str, int, float, bool, List[Any]] = Field(description="Value to compare against")
    data_type: str = Field(default="string", description="Data type: string, number, boolean, array")

class WorkflowAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ActionType
    name: str = Field(description="Human-readable action name")
    parameters: Dict[str, Any] = Field(default={}, description="Action-specific parameters")
    delay_minutes: Optional[int] = Field(default=None, description="Delay before executing this action")
    conditions: List[WorkflowCondition] = Field(default=[], description="Conditions for this action to execute")
    on_success_action_id: Optional[str] = Field(default=None, description="Next action on success")
    on_failure_action_id: Optional[str] = Field(default=None, description="Next action on failure")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

class WorkflowTrigger(BaseModel):
    type: TriggerType
    name: str
    parameters: Dict[str, Any] = Field(default={}, description="Trigger-specific parameters")
    conditions: List[WorkflowCondition] = Field(default=[], description="Conditions for trigger activation")
    schedule: Optional[str] = Field(default=None, description="Cron-like schedule for time-based triggers")

class AdvancedWorkflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    version: str = Field(default="1.0.0")
    status: WorkflowStatus = WorkflowStatus.DRAFT
    
    # Workflow Structure
    trigger: WorkflowTrigger
    actions: List[WorkflowAction]
    
    # Conditional Logic
    conditional_branches: Dict[str, List[str]] = Field(default={}, description="Condition ID -> Action IDs mapping")
    
    # Approval Process
    approval_required: bool = Field(default=False)
    approvers: List[str] = Field(default=[], description="List of user IDs who can approve")
    approval_timeout_hours: int = Field(default=24)
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None
    execution_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    
    # Configuration
    timeout_minutes: int = Field(default=60, description="Workflow execution timeout")
    max_concurrent_executions: int = Field(default=10)
    enabled: bool = Field(default=True)
    
    # Tags and Categories
    tags: List[str] = Field(default=[])
    category: str = Field(default="general")

class WorkflowExecution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    workflow_version: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    
    # Context Data
    context_data: Dict[str, Any] = Field(default={}, description="Data available to the workflow")
    triggered_by: str = Field(description="What triggered this execution")
    trigger_data: Dict[str, Any] = Field(default={})
    
    # Execution Tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_action_id: Optional[str] = None
    executed_actions: List[str] = Field(default=[])
    failed_actions: List[str] = Field(default=[])
    
    # Results and Logs
    results: Dict[str, Any] = Field(default={})
    execution_log: List[Dict[str, Any]] = Field(default=[])
    error_message: Optional[str] = None
    
    # Approval Tracking
    pending_approvals: List[str] = Field(default=[])
    approved_by: List[str] = Field(default=[])
    rejected_by: List[str] = Field(default=[])

class ConditionalLogicEngine:
    """Advanced conditional logic engine for workflows"""
    
    def __init__(self):
        self.operators = {
            ConditionOperator.EQUALS: self._equals,
            ConditionOperator.NOT_EQUALS: self._not_equals,
            ConditionOperator.GREATER_THAN: self._greater_than,
            ConditionOperator.LESS_THAN: self._less_than,
            ConditionOperator.GREATER_EQUAL: self._greater_equal,
            ConditionOperator.LESS_EQUAL: self._less_equal,
            ConditionOperator.CONTAINS: self._contains,
            ConditionOperator.NOT_CONTAINS: self._not_contains,
            ConditionOperator.IN_LIST: self._in_list,
            ConditionOperator.NOT_IN_LIST: self._not_in_list,
            ConditionOperator.IS_EMPTY: self._is_empty,
            ConditionOperator.IS_NOT_EMPTY: self._is_not_empty,
            ConditionOperator.MATCHES_REGEX: self._matches_regex
        }
    
    def evaluate_condition(self, condition: WorkflowCondition, context_data: Dict[str, Any]) -> bool:
        """Evaluate a single condition against context data"""
        try:
            # Extract field value from context data
            field_value = self._extract_field_value(condition.field, context_data)
            
            # Get the appropriate operator function
            operator_func = self.operators.get(condition.operator)
            if not operator_func:
                logger.error(f"Unknown operator: {condition.operator}")
                return False
            
            # Convert values to appropriate types
            field_value = self._convert_value(field_value, condition.data_type)
            comparison_value = self._convert_value(condition.value, condition.data_type)
            
            # Evaluate condition
            result = operator_func(field_value, comparison_value)
            
            logger.debug(f"Condition evaluation: {condition.field} {condition.operator} {condition.value} = {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating condition {condition.id}: {e}")
            return False
    
    def evaluate_conditions(self, conditions: List[WorkflowCondition], context_data: Dict[str, Any], logic: str = "AND") -> bool:
        """Evaluate multiple conditions with AND/OR logic"""
        if not conditions:
            return True
        
        results = [self.evaluate_condition(condition, context_data) for condition in conditions]
        
        if logic.upper() == "AND":
            return all(results)
        elif logic.upper() == "OR":
            return any(results)
        else:
            logger.error(f"Unknown logic operator: {logic}")
            return False
    
    def _extract_field_value(self, field_path: str, context_data: Dict[str, Any]) -> Any:
        """Extract field value from context data using dot notation"""
        try:
            keys = field_path.split('.')
            value = context_data
            
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                elif hasattr(value, key):
                    value = getattr(value, key)
                else:
                    return None
            
            return value
        except Exception as e:
            logger.error(f"Error extracting field {field_path}: {e}")
            return None
    
    def _convert_value(self, value: Any, data_type: str) -> Any:
        """Convert value to appropriate data type"""
        if value is None:
            return None
        
        try:
            if data_type == "number":
                return float(value) if isinstance(value, (int, float, str)) else value
            elif data_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                return bool(value)
            elif data_type == "array":
                return list(value) if not isinstance(value, list) else value
            else:  # string or unknown
                return str(value) if not isinstance(value, str) else value
        except Exception as e:
            logger.error(f"Error converting value {value} to {data_type}: {e}")
            return value
    
    # Operator implementations
    def _equals(self, field_value, comparison_value):
        return field_value == comparison_value
    
    def _not_equals(self, field_value, comparison_value):
        return field_value != comparison_value
    
    def _greater_than(self, field_value, comparison_value):
        try:
            return float(field_value) > float(comparison_value)
        except (ValueError, TypeError):
            return str(field_value) > str(comparison_value)
    
    def _less_than(self, field_value, comparison_value):
        try:
            return float(field_value) < float(comparison_value)
        except (ValueError, TypeError):
            return str(field_value) < str(comparison_value)
    
    def _greater_equal(self, field_value, comparison_value):
        try:
            return float(field_value) >= float(comparison_value)
        except (ValueError, TypeError):
            return str(field_value) >= str(comparison_value)
    
    def _less_equal(self, field_value, comparison_value):
        try:
            return float(field_value) <= float(comparison_value)
        except (ValueError, TypeError):
            return str(field_value) <= str(comparison_value)
    
    def _contains(self, field_value, comparison_value):
        return str(comparison_value).lower() in str(field_value).lower()
    
    def _not_contains(self, field_value, comparison_value):
        return str(comparison_value).lower() not in str(field_value).lower()
    
    def _in_list(self, field_value, comparison_value):
        return field_value in comparison_value if isinstance(comparison_value, list) else False
    
    def _not_in_list(self, field_value, comparison_value):
        return field_value not in comparison_value if isinstance(comparison_value, list) else True
    
    def _is_empty(self, field_value, comparison_value):
        if field_value is None:
            return True
        if isinstance(field_value, (str, list, dict)):
            return len(field_value) == 0
        return False
    
    def _is_not_empty(self, field_value, comparison_value):
        return not self._is_empty(field_value, comparison_value)
    
    def _matches_regex(self, field_value, comparison_value):
        import re
        try:
            pattern = re.compile(str(comparison_value))
            return bool(pattern.search(str(field_value)))
        except re.error:
            return False

class TimeBasedTriggerEngine:
    """Time-based trigger management for workflows"""
    
    def __init__(self):
        self.scheduled_workflows = {}
        self.running = False
    
    async def start_scheduler(self):
        """Start the time-based trigger scheduler"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting time-based trigger scheduler")
        
        # In a production environment, this would use a proper job scheduler like Celery
        # For this implementation, we'll use a simple background task
        asyncio.create_task(self._scheduler_loop())
    
    async def stop_scheduler(self):
        """Stop the time-based trigger scheduler"""
        self.running = False
        logger.info("Stopping time-based trigger scheduler")
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                await self._check_scheduled_workflows()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_scheduled_workflows(self):
        """Check for workflows that need to be triggered"""
        try:
            workflows_collection = await get_workflows_collection()
            
            # Find active workflows with time-based triggers
            active_workflows = await workflows_collection.find({
                "status": WorkflowStatus.ACTIVE,
                "trigger.type": TriggerType.TIME_BASED,
                "enabled": True
            }).to_list(length=None)
            
            for workflow_doc in active_workflows:
                await self._evaluate_time_trigger(workflow_doc)
                
        except Exception as e:
            logger.error(f"Error checking scheduled workflows: {e}")
    
    async def _evaluate_time_trigger(self, workflow_doc: Dict[str, Any]):
        """Evaluate if a time-based trigger should fire"""
        try:
            workflow = AdvancedWorkflow(**workflow_doc)
            trigger = workflow.trigger
            
            # Check if it's time to trigger based on schedule
            should_trigger = await self._should_trigger_now(trigger, workflow.last_executed)
            
            if should_trigger:
                logger.info(f"Triggering time-based workflow: {workflow.name}")
                # Trigger workflow execution
                await self._trigger_workflow_execution(workflow, "time_scheduler", {
                    "triggered_at": datetime.utcnow(),
                    "trigger_type": "time_based"
                })
        
        except Exception as e:
            logger.error(f"Error evaluating time trigger: {e}")
    
    async def _should_trigger_now(self, trigger: WorkflowTrigger, last_executed: Optional[datetime]) -> bool:
        """Determine if trigger should fire now based on schedule"""
        # Simple implementation - in production would use proper cron parsing
        schedule = trigger.schedule
        if not schedule:
            return False
        
        now = datetime.utcnow()
        
        # Basic schedule parsing (extend this for full cron support)
        if schedule == "daily":
            if not last_executed:
                return True
            return (now - last_executed).days >= 1
        elif schedule == "hourly":
            if not last_executed:
                return True
            return (now - last_executed).seconds >= 3600
        elif schedule.startswith("every_"):
            # Parse "every_X_minutes" format
            try:
                parts = schedule.split("_")
                if len(parts) == 3 and parts[2] == "minutes":
                    minutes = int(parts[1])
                    if not last_executed:
                        return True
                    return (now - last_executed).seconds >= (minutes * 60)
            except ValueError:
                pass
        
        return False
    
    async def _trigger_workflow_execution(self, workflow: AdvancedWorkflow, triggered_by: str, trigger_data: Dict[str, Any]):
        """Trigger a workflow execution"""
        # This would be implemented in the WorkflowExecutionEngine
        logger.info(f"Would trigger workflow {workflow.id} (triggered by: {triggered_by})")
        pass

# Global engine instances
conditional_logic_engine = ConditionalLogicEngine()
time_trigger_engine = TimeBasedTriggerEngine()

# API Endpoints
@router.get("/workflows", response_model=Dict[str, Any])
async def get_workflows():
    """Get all workflows from the workflow engine"""
    try:
        workflows_collection = await get_workflows_collection()
        
        # Get workflows created by workflow engine components
        workflows_cursor = workflows_collection.find({
            "created_by": {"$in": [
                "conditional_logic_builder",
                "time_trigger_builder", 
                "approval_process_builder",
                "webhook_automation_builder",
                "nl_workflow_generator"
            ]}
        })
        
        workflows = []
        async for workflow in workflows_cursor:
            workflow["id"] = str(workflow["_id"])
            workflow.pop("_id", None)
            workflows.append(workflow)
        
        return {
            "workflows": workflows,
            "count": len(workflows),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        return {
            "workflows": [],
            "count": 0,
            "status": "error",
            "message": str(e)
        }

@router.post("/workflows", response_model=Dict[str, Any])
async def create_advanced_workflow(workflow: AdvancedWorkflow):
    """Create a new advanced workflow with conditional logic"""
    try:
        workflows_collection = await get_workflows_collection()
        
        # Validate workflow structure
        if not workflow.actions:
            raise HTTPException(status_code=400, detail="Workflow must have at least one action")
        
        # Validate conditional logic
        for action in workflow.actions:
            for condition in action.conditions:
                # Basic validation - could be enhanced
                if not condition.field or not condition.operator:
                    raise HTTPException(status_code=400, detail="Invalid condition in workflow")
        
        # Save workflow
        workflow_doc = workflow.dict()
        workflow_doc["created_at"] = datetime.utcnow()
        
        await workflows_collection.insert_one(workflow_doc)
        
        return {
            "workflow_id": workflow.id,
            "message": "Advanced workflow created successfully",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")

@router.get("/workflows/{workflow_id}/validate")
async def validate_workflow_logic(workflow_id: str):
    """Validate workflow conditional logic and structure"""
    try:
        workflows_collection = await get_workflows_collection()
        workflow_doc = await workflows_collection.find_one({"id": workflow_id})
        
        if not workflow_doc:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow = AdvancedWorkflow(**workflow_doc)
        
        # Calculate total condition count across all workflow components
        trigger_conditions = len(workflow.trigger.conditions) if workflow.trigger.conditions else 0
        action_conditions = sum(len(action.conditions) for action in workflow.actions)
        total_condition_count = trigger_conditions + action_conditions
        
        # Validation results
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "action_count": len(workflow.actions),
            "condition_count": total_condition_count,
            "trigger_conditions": trigger_conditions,
            "action_conditions": action_conditions,
            "has_approval_process": workflow.approval_required,
            "estimated_complexity": "low"
        }
        
        # Validate action references
        action_ids = {action.id for action in workflow.actions}
        for action in workflow.actions:
            if action.on_success_action_id and action.on_success_action_id not in action_ids:
                validation_results["issues"].append(f"Action {action.name} references invalid success action")
                validation_results["valid"] = False
            
            if action.on_failure_action_id and action.on_failure_action_id not in action_ids:
                validation_results["issues"].append(f"Action {action.name} references invalid failure action")
                validation_results["valid"] = False
        
        # Check for circular references (basic check)
        if len(workflow.actions) > 10:
            validation_results["warnings"].append("Complex workflow with many actions - consider splitting")
            validation_results["estimated_complexity"] = "high"
        
        # Validate conditional branches
        for condition_id, action_ids_list in workflow.conditional_branches.items():
            for action_id in action_ids_list:
                if action_id not in action_ids:
                    validation_results["issues"].append(f"Conditional branch references invalid action: {action_id}")
                    validation_results["valid"] = False
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate workflow")

@router.post("/conditions/test")
async def test_condition(condition: WorkflowCondition, context_data: Dict[str, Any]):
    """Test a single condition against sample data"""
    try:
        result = conditional_logic_engine.evaluate_condition(condition, context_data)
        
        return {
            "condition_result": result,
            "field_value": conditional_logic_engine._extract_field_value(condition.field, context_data),
            "comparison_value": condition.value,
            "operator": condition.operator,
            "evaluation_details": {
                "field_path": condition.field,
                "data_type": condition.data_type,
                "context_keys": list(context_data.keys())
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing condition: {e}")
        raise HTTPException(status_code=500, detail="Failed to test condition")

@router.get("/triggers/scheduler/status")
async def get_scheduler_status():
    """Get status of the time-based trigger scheduler"""
    return {
        "running": time_trigger_engine.running,
        "scheduled_workflows": len(time_trigger_engine.scheduled_workflows),
        "supported_schedules": [
            "daily", "hourly", "every_X_minutes", 
            "0 9 * * 1-5 (cron format - coming soon)"
        ]
    }

@router.post("/triggers/scheduler/start")
async def start_scheduler():
    """Start the time-based trigger scheduler"""
    try:
        await time_trigger_engine.start_scheduler()
        return {
            "message": "Scheduler started successfully",
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail="Failed to start scheduler")

@router.get("/conditions/operators")
async def get_condition_operators():
    """Get available condition operators and their descriptions"""
    operators = [
        {"operator": "equals", "description": "Field equals value", "data_types": ["string", "number", "boolean"]},
        {"operator": "not_equals", "description": "Field does not equal value", "data_types": ["string", "number", "boolean"]},
        {"operator": "greater_than", "description": "Field is greater than value", "data_types": ["number", "string"]},
        {"operator": "less_than", "description": "Field is less than value", "data_types": ["number", "string"]},
        {"operator": "greater_equal", "description": "Field is greater than or equal to value", "data_types": ["number", "string"]},
        {"operator": "less_equal", "description": "Field is less than or equal to value", "data_types": ["number", "string"]},
        {"operator": "contains", "description": "Field contains value (case-insensitive)", "data_types": ["string"]},
        {"operator": "not_contains", "description": "Field does not contain value", "data_types": ["string"]},
        {"operator": "in_list", "description": "Field value is in provided list", "data_types": ["array"]},
        {"operator": "not_in_list", "description": "Field value is not in provided list", "data_types": ["array"]},
        {"operator": "is_empty", "description": "Field is empty or null", "data_types": ["string", "array"]},
        {"operator": "is_not_empty", "description": "Field is not empty", "data_types": ["string", "array"]},
        {"operator": "matches_regex", "description": "Field matches regular expression", "data_types": ["string"]}
    ]
    
    return {
        "operators": operators,
        "data_types": ["string", "number", "boolean", "array"],
        "common_fields": [
            "lead.score", "lead.status", "lead.value", "lead.source",
            "agent.efficiency", "agent.status",
            "activity.type", "activity.timestamp"
        ]
    }