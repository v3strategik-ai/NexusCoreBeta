from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging
import json
import uuid
from enum import Enum
from pydantic import BaseModel, Field

from database import get_workflows_collection, get_activities_collection
from websocket import trigger_activity_broadcast, send_notification

router = APIRouter(prefix="/workflows/advanced", tags=["advanced_workflows"])
logger = logging.getLogger(__name__)

# Enums for workflow components
class TriggerType(str, Enum):
    MANUAL = "manual"
    TIME_BASED = "time_based"
    LEAD_STATUS_CHANGE = "lead_status_change"
    DOCUMENT_GENERATED = "document_generated"
    EMAIL_OPENED = "email_opened"
    AGENT_IDLE = "agent_idle"
    THRESHOLD_REACHED = "threshold_reached"
    WEBHOOK = "webhook"

class ActionType(str, Enum):
    SEND_EMAIL = "send_email"
    CREATE_DOCUMENT = "create_document"
    UPDATE_LEAD = "update_lead"
    ASSIGN_AGENT = "assign_agent"
    SEND_NOTIFICATION = "send_notification"
    WAIT_DELAY = "wait_delay"
    CONDITIONAL_BRANCH = "conditional_branch"
    WEBHOOK_CALL = "webhook_call"
    RUN_AGENT_TASK = "run_agent_task"

class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"

# Pydantic models for workflow components
class WorkflowNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # 'trigger', 'action', 'condition', 'delay'
    label: str
    position: Dict[str, float]  # {x: 100, y: 200}
    data: Dict[str, Any] = Field(default_factory=dict)

class WorkflowEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # Source node ID
    target: str  # Target node ID
    type: str = "default"
    label: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)

class TriggerConfig(BaseModel):
    type: TriggerType
    conditions: Dict[str, Any] = Field(default_factory=dict)
    schedule: Optional[str] = None  # Cron expression for time-based triggers

class ActionConfig(BaseModel):
    type: ActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = 3
    timeout_seconds: int = 300

class ConditionalBranch(BaseModel):
    condition: Dict[str, Any]
    true_path: str  # Node ID for true condition
    false_path: str  # Node ID for false condition

class AdvancedWorkflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    status: WorkflowStatus = WorkflowStatus.DRAFT
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    triggers: List[TriggerConfig] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    execution_count: int = 0
    last_executed: Optional[datetime] = None

class WorkflowExecution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    trigger_type: str
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    status: str = "running"  # running, completed, failed, cancelled
    current_node: Optional[str] = None
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None

class WorkflowTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    template_data: AdvancedWorkflow
    use_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Workflow execution engine
class WorkflowExecutor:
    """Advanced workflow execution engine with conditional logic"""
    
    def __init__(self):
        self.running_executions: Dict[str, WorkflowExecution] = {}
    
    async def execute_workflow(
        self, 
        workflow: AdvancedWorkflow, 
        trigger_data: Dict[str, Any] = None,
        background_tasks: BackgroundTasks = None
    ) -> WorkflowExecution:
        """Execute a workflow with conditional logic and branching"""
        
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            trigger_type=trigger_data.get('type', 'manual') if trigger_data else 'manual',
            trigger_data=trigger_data or {},
            variables={**workflow.variables, **(trigger_data or {})}
        )
        
        self.running_executions[execution.id] = execution
        
        try:
            # Find starting node (trigger node)
            trigger_nodes = [node for node in workflow.nodes if node.type == 'trigger']
            if not trigger_nodes:
                raise ValueError("No trigger node found in workflow")
            
            start_node = trigger_nodes[0]
            
            # Execute workflow starting from trigger
            await self._execute_node(workflow, execution, start_node.id)
            
            # Mark as completed
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
            # Update workflow execution count
            collection = await get_workflows_collection()
            await collection.update_one(
                {"id": workflow.id},
                {
                    "$inc": {"execution_count": 1},
                    "$set": {"last_executed": execution.completed_at}
                }
            )
            
            # Log successful execution
            await self._log_execution_activity(execution, "Workflow completed successfully")
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (execution.completed_at - execution.started_at).total_seconds()
            
            logger.error(f"Workflow execution failed: {e}")
            await self._log_execution_activity(execution, f"Workflow failed: {str(e)}")
        
        finally:
            # Remove from running executions
            if execution.id in self.running_executions:
                del self.running_executions[execution.id]
        
        return execution
    
    async def _execute_node(self, workflow: AdvancedWorkflow, execution: WorkflowExecution, node_id: str):
        """Execute a specific node in the workflow"""
        
        # Find the node
        node = next((n for n in workflow.nodes if n.id == node_id), None)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        execution.current_node = node_id
        execution.execution_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'node_id': node_id,
            'node_type': node.type,
            'action': 'started',
            'data': node.data
        })
        
        try:
            # Execute based on node type
            if node.type == 'trigger':
                await self._execute_trigger_node(workflow, execution, node)
            elif node.type == 'action':
                await self._execute_action_node(workflow, execution, node)
            elif node.type == 'condition':
                await self._execute_condition_node(workflow, execution, node)
            elif node.type == 'delay':
                await self._execute_delay_node(workflow, execution, node)
            else:
                logger.warning(f"Unknown node type: {node.type}")
            
            # Log successful execution
            execution.execution_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'node_id': node_id,
                'node_type': node.type,
                'action': 'completed',
                'result': 'success'
            })
            
            # Find and execute next nodes
            await self._execute_next_nodes(workflow, execution, node_id)
            
        except Exception as e:
            execution.execution_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'node_id': node_id,
                'node_type': node.type,
                'action': 'failed',
                'error': str(e)
            })
            raise
    
    async def _execute_trigger_node(self, workflow: AdvancedWorkflow, execution: WorkflowExecution, node: WorkflowNode):
        """Execute trigger node logic"""
        # Triggers are mostly passive - they initiate the workflow
        # The actual trigger logic is handled by the trigger system
        pass
    
    async def _execute_action_node(self, workflow: AdvancedWorkflow, execution: WorkflowExecution, node: WorkflowNode):
        """Execute action node logic"""
        action_type = node.data.get('action_type')
        parameters = node.data.get('parameters', {})
        
        # Replace variables in parameters
        processed_parameters = self._process_variables(parameters, execution.variables)
        
        if action_type == ActionType.SEND_EMAIL:
            await self._execute_send_email(processed_parameters, execution)
        elif action_type == ActionType.CREATE_DOCUMENT:
            await self._execute_create_document(processed_parameters, execution)
        elif action_type == ActionType.UPDATE_LEAD:
            await self._execute_update_lead(processed_parameters, execution)
        elif action_type == ActionType.SEND_NOTIFICATION:
            await self._execute_send_notification(processed_parameters, execution)
        elif action_type == ActionType.ASSIGN_AGENT:
            await self._execute_assign_agent(processed_parameters, execution)
        else:
            logger.warning(f"Unknown action type: {action_type}")
    
    async def _execute_condition_node(self, workflow: AdvancedWorkflow, execution: WorkflowExecution, node: WorkflowNode):
        """Execute conditional logic node"""
        condition = node.data.get('condition', {})
        
        # Evaluate condition
        result = self._evaluate_condition(condition, execution.variables)
        
        # Store result in execution variables
        execution.variables[f"{node.id}_result"] = result
        
        # The actual branching is handled in _execute_next_nodes
    
    async def _execute_delay_node(self, workflow: AdvancedWorkflow, execution: WorkflowExecution, node: WorkflowNode):
        """Execute delay node"""
        delay_seconds = node.data.get('delay_seconds', 0)
        delay_minutes = node.data.get('delay_minutes', 0)
        delay_hours = node.data.get('delay_hours', 0)
        
        total_delay = delay_seconds + (delay_minutes * 60) + (delay_hours * 3600)
        
        if total_delay > 0:
            # For demo purposes, we'll just log the delay
            # In production, this would schedule the continuation
            execution.execution_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'delay_simulated',
                'delay_seconds': total_delay,
                'note': 'Delay simulated for demo - would normally pause execution'
            })
    
    async def _execute_next_nodes(self, workflow: AdvancedWorkflow, execution: WorkflowExecution, current_node_id: str):
        """Find and execute the next nodes in the workflow"""
        
        # Find outgoing edges from current node
        outgoing_edges = [edge for edge in workflow.edges if edge.source == current_node_id]
        
        for edge in outgoing_edges:
            # Check if edge has conditions
            if edge.data.get('condition'):
                # Evaluate edge condition
                condition_result = self._evaluate_condition(edge.data['condition'], execution.variables)
                if not condition_result:
                    continue  # Skip this edge
            
            # Execute target node
            await self._execute_node(workflow, execution, edge.target)
    
    def _evaluate_condition(self, condition: Dict[str, Any], variables: Dict[str, Any]) -> bool:
        """Evaluate a condition against execution variables"""
        try:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if not field or not operator:
                return True  # Invalid condition, default to true
            
            # Get field value from variables
            field_value = variables.get(field)
            
            # Evaluate based on operator
            if operator == ConditionOperator.EQUALS:
                return field_value == value
            elif operator == ConditionOperator.NOT_EQUALS:
                return field_value != value
            elif operator == ConditionOperator.GREATER_THAN:
                return float(field_value or 0) > float(value)
            elif operator == ConditionOperator.LESS_THAN:
                return float(field_value or 0) < float(value)
            elif operator == ConditionOperator.CONTAINS:
                return str(value).lower() in str(field_value or '').lower()
            elif operator == ConditionOperator.NOT_CONTAINS:
                return str(value).lower() not in str(field_value or '').lower()
            elif operator == ConditionOperator.IN_LIST:
                return field_value in (value if isinstance(value, list) else [value])
            elif operator == ConditionOperator.NOT_IN_LIST:
                return field_value not in (value if isinstance(value, list) else [value])
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False
    
    def _process_variables(self, data: Any, variables: Dict[str, Any]) -> Any:
        """Replace variable placeholders in data with actual values"""
        if isinstance(data, str):
            # Replace {{variable}} patterns
            for var_name, var_value in variables.items():
                data = data.replace(f"{{{{{var_name}}}}}", str(var_value))
            return data
        elif isinstance(data, dict):
            return {key: self._process_variables(value, variables) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._process_variables(item, variables) for item in data]
        else:
            return data
    
    async def _execute_send_email(self, parameters: Dict[str, Any], execution: WorkflowExecution):
        """Execute send email action"""
        # This would integrate with the email system
        execution.execution_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'send_email',
            'parameters': parameters,
            'status': 'simulated'  # Would be 'sent' in production
        })
    
    async def _execute_create_document(self, parameters: Dict[str, Any], execution: WorkflowExecution):
        """Execute create document action"""
        # This would integrate with the document generation system
        execution.execution_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'create_document',
            'parameters': parameters,
            'status': 'simulated'  # Would be 'created' in production
        })
    
    async def _execute_update_lead(self, parameters: Dict[str, Any], execution: WorkflowExecution):
        """Execute update lead action"""
        # This would integrate with the CRM system
        execution.execution_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'update_lead',
            'parameters': parameters,
            'status': 'simulated'  # Would be 'updated' in production
        })
    
    async def _execute_send_notification(self, parameters: Dict[str, Any], execution: WorkflowExecution):
        """Execute send notification action"""
        await send_notification(
            title=parameters.get('title', 'Workflow Notification'),
            message=parameters.get('message', 'Notification from workflow'),
            type=parameters.get('type', 'info')
        )
        
        execution.execution_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'send_notification',
            'parameters': parameters,
            'status': 'sent'
        })
    
    async def _execute_assign_agent(self, parameters: Dict[str, Any], execution: WorkflowExecution):
        """Execute assign agent action"""
        # This would integrate with the agent assignment system
        execution.execution_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'assign_agent',
            'parameters': parameters,
            'status': 'simulated'  # Would be 'assigned' in production
        })
    
    async def _log_execution_activity(self, execution: WorkflowExecution, message: str):
        """Log workflow execution activity"""
        try:
            activity_data = {
                'agent_name': 'Workflow Engine',
                'activity_type': 'workflow_execution',
                'description': message,
                'timestamp': datetime.utcnow(),
                'metadata': {
                    'workflow_id': execution.workflow_id,
                    'execution_id': execution.id,
                    'status': execution.status,
                    'duration_seconds': execution.duration_seconds
                }
            }
            
            activities_collection = await get_activities_collection()
            await activities_collection.insert_one(activity_data)
            
            # Broadcast to real-time system
            await trigger_activity_broadcast(activity_data)
            
        except Exception as e:
            logger.error(f"Error logging execution activity: {e}")

# Global workflow executor instance
workflow_executor = WorkflowExecutor()

# API Endpoints
@router.post("/create", response_model=AdvancedWorkflow)
async def create_advanced_workflow(workflow: AdvancedWorkflow):
    """Create a new advanced workflow with visual builder support"""
    try:
        collection = await get_workflows_collection()
        
        workflow_dict = workflow.dict()
        await collection.insert_one(workflow_dict)
        
        logger.info(f"Created advanced workflow: {workflow.name}")
        
        return workflow
        
    except Exception as e:
        logger.error(f"Error creating advanced workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow")

@router.get("/", response_model=List[AdvancedWorkflow])
async def get_advanced_workflows(
    status: Optional[WorkflowStatus] = None,
    limit: int = 50
):
    """Get all advanced workflows with optional filtering"""
    try:
        collection = await get_workflows_collection()
        
        query = {}
        if status:
            query["status"] = status
        
        workflows_data = await collection.find(query).limit(limit).to_list(limit)
        workflows = [AdvancedWorkflow(**workflow) for workflow in workflows_data]
        
        return workflows
        
    except Exception as e:
        logger.error(f"Error getting advanced workflows: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflows")

@router.get("/{workflow_id}", response_model=AdvancedWorkflow)
async def get_advanced_workflow(workflow_id: str):
    """Get a specific advanced workflow"""
    try:
        collection = await get_workflows_collection()
        
        workflow_data = await collection.find_one({"id": workflow_id})
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return AdvancedWorkflow(**workflow_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow")

@router.put("/{workflow_id}", response_model=AdvancedWorkflow)
async def update_advanced_workflow(workflow_id: str, workflow_update: AdvancedWorkflow):
    """Update an advanced workflow"""
    try:
        collection = await get_workflows_collection()
        
        workflow_update.id = workflow_id
        workflow_update.updated_at = datetime.utcnow()
        
        result = await collection.replace_one(
            {"id": workflow_id},
            workflow_update.dict()
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(f"Updated advanced workflow: {workflow_id}")
        
        return workflow_update
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update workflow")

@router.post("/{workflow_id}/execute")
async def execute_advanced_workflow(
    workflow_id: str, 
    trigger_data: Optional[Dict[str, Any]] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Execute an advanced workflow"""
    try:
        collection = await get_workflows_collection()
        
        workflow_data = await collection.find_one({"id": workflow_id})
        if not workflow_data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow = AdvancedWorkflow(**workflow_data)
        
        if workflow.status != WorkflowStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Workflow is not active")
        
        # Execute workflow in background
        execution = await workflow_executor.execute_workflow(
            workflow, 
            trigger_data or {},
            background_tasks
        )
        
        return {
            'execution_id': execution.id,
            'status': execution.status,
            'message': 'Workflow execution started',
            'execution': execution.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute workflow")

@router.get("/{workflow_id}/executions")
async def get_workflow_executions(
    workflow_id: str,
    limit: int = 20
):
    """Get execution history for a workflow (placeholder - would store in database)"""
    try:
        # In production, this would query a workflow_executions collection
        # For now, returning simulated data
        
        return {
            'workflow_id': workflow_id,
            'executions': [
                {
                    'id': f"exec_{i}",
                    'status': 'completed' if i % 3 != 0 else 'failed',
                    'started_at': (datetime.now() - timedelta(days=i)).isoformat(),
                    'duration_seconds': 30 + (i * 5)
                }
                for i in range(min(limit, 10))
            ],
            'total_executions': 25,
            'success_rate': 85.5
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow executions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow executions")

@router.get("/templates/list")
async def get_workflow_templates():
    """Get available workflow templates"""
    try:
        # Predefined workflow templates
        templates = [
            {
                'id': 'lead_nurture_sequence',
                'name': 'Lead Nurturing Sequence',
                'description': 'Automated email sequence for nurturing leads through the sales funnel',
                'category': 'Sales & Marketing',
                'complexity': 'Medium',
                'estimated_setup_time': '15 minutes'
            },
            {
                'id': 'document_approval_flow',
                'name': 'Document Approval Workflow',
                'description': 'Multi-step approval process for generated documents',
                'category': 'Document Management',
                'complexity': 'Advanced',
                'estimated_setup_time': '25 minutes'
            },
            {
                'id': 'agent_task_automation',
                'name': 'Agent Task Automation',
                'description': 'Automatically assign and monitor agent tasks based on workload',
                'category': 'Agent Management',
                'complexity': 'Simple',
                'estimated_setup_time': '10 minutes'
            },
            {
                'id': 'lead_scoring_automation',
                'name': 'Automated Lead Scoring',
                'description': 'Automatically score and categorize leads based on behavior and data',
                'category': 'CRM & Sales',
                'complexity': 'Advanced',
                'estimated_setup_time': '30 minutes'
            }
        ]
        
        return {
            'templates': templates,
            'categories': list(set(t['category'] for t in templates)),
            'total_templates': len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow templates")

@router.post("/templates/{template_id}/create")
async def create_from_template(template_id: str, workflow_name: str):
    """Create a new workflow from a template"""
    try:
        # This would load actual template data and create a workflow
        # For now, returning a basic workflow structure
        
        template_workflows = {
            'lead_nurture_sequence': AdvancedWorkflow(
                name=workflow_name,
                description="Lead nurturing sequence created from template",
                status=WorkflowStatus.DRAFT,
                nodes=[
                    WorkflowNode(
                        id="trigger_1",
                        type="trigger",
                        label="New Lead Created",
                        position={"x": 100, "y": 100},
                        data={"trigger_type": "lead_status_change"}
                    ),
                    WorkflowNode(
                        id="action_1",
                        type="action",
                        label="Send Welcome Email",
                        position={"x": 300, "y": 100},
                        data={
                            "action_type": "send_email",
                            "parameters": {
                                "template": "lead_welcome",
                                "to": "{{lead_email}}"
                            }
                        }
                    ),
                    WorkflowNode(
                        id="delay_1",
                        type="delay",
                        label="Wait 3 Days",
                        position={"x": 500, "y": 100},
                        data={"delay_hours": 72}
                    ),
                    WorkflowNode(
                        id="action_2",
                        type="action",
                        label="Send Follow-up Email",
                        position={"x": 700, "y": 100},
                        data={
                            "action_type": "send_email",
                            "parameters": {
                                "template": "lead_followup",
                                "to": "{{lead_email}}"
                            }
                        }
                    )
                ],
                edges=[
                    WorkflowEdge(source="trigger_1", target="action_1"),
                    WorkflowEdge(source="action_1", target="delay_1"),
                    WorkflowEdge(source="delay_1", target="action_2")
                ],
                tags=["template", "lead_nurturing", "email_automation"]
            )
        }
        
        if template_id not in template_workflows:
            raise HTTPException(status_code=404, detail="Template not found")
        
        workflow = template_workflows[template_id]
        
        # Save to database
        collection = await get_workflows_collection()
        await collection.insert_one(workflow.dict())
        
        return workflow
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow from template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow from template")

@router.delete("/{workflow_id}")
async def delete_advanced_workflow(workflow_id: str):
    """Delete an advanced workflow"""
    try:
        collection = await get_workflows_collection()
        
        result = await collection.delete_one({"id": workflow_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logger.info(f"Deleted advanced workflow: {workflow_id}")
        
        return {"message": "Workflow deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workflow")