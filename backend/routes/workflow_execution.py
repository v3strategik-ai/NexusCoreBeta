from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field
import json
import asyncio
import aiohttp
from bson import ObjectId

from database import (
    get_leads_collection,
    get_activities_collection,
    get_agents_collection,
    get_workflows_collection,
    get_documents_collection
)
from .workflow_engine import (
    AdvancedWorkflow, WorkflowExecution, WorkflowAction, ActionType, 
    ExecutionStatus, conditional_logic_engine
)

router = APIRouter(prefix="/workflow-execution", tags=["workflow-execution"])
logger = logging.getLogger(__name__)

# Pydantic Models for Execution
class WorkflowExecutionRequest(BaseModel):
    workflow_id: str
    context_data: Dict[str, Any] = Field(default={})
    triggered_by: str = "manual"
    priority: str = Field(default="normal", description="low, normal, high")

class ApprovalRequest(BaseModel):
    execution_id: str
    action_id: str
    approver_id: str
    decision: str = Field(description="approve or reject")
    comments: Optional[str] = None

class WorkflowExecutionEngine:
    """Advanced workflow execution engine with conditional logic and approvals"""
    
    def __init__(self):
        self.active_executions = {}
        self.execution_queue = asyncio.Queue()
        self.max_concurrent_executions = 10
        self.running = False
    
    async def start_engine(self):
        """Start the workflow execution engine"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting workflow execution engine")
        
        # Start execution workers
        for i in range(self.max_concurrent_executions):
            asyncio.create_task(self._execution_worker(f"worker-{i}"))
    
    async def stop_engine(self):
        """Stop the workflow execution engine"""
        self.running = False
        logger.info("Stopping workflow execution engine")
    
    async def execute_workflow(self, workflow_id: str, context_data: Dict[str, Any], 
                              triggered_by: str = "manual") -> str:
        """Start workflow execution"""
        try:
            # Get workflow definition
            workflows_collection = await get_workflows_collection()
            workflow_doc = await workflows_collection.find_one({"id": workflow_id})
            
            if not workflow_doc:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            workflow = AdvancedWorkflow(**workflow_doc)
            
            if workflow.status != "active":
                raise ValueError(f"Workflow {workflow_id} is not active")
            
            # Create execution record
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                workflow_version=workflow.version,
                context_data=context_data,
                triggered_by=triggered_by,
                trigger_data={"triggered_at": datetime.utcnow()}
            )
            
            # Add to execution queue
            await self.execution_queue.put(execution)
            logger.info(f"Queued workflow execution: {execution.id}")
            
            return execution.id
            
        except Exception as e:
            logger.error(f"Error starting workflow execution: {e}")
            raise
    
    async def _execution_worker(self, worker_name: str):
        """Worker to process workflow executions"""
        logger.info(f"Starting execution worker: {worker_name}")
        
        while self.running:
            try:
                # Get next execution from queue (with timeout)
                try:
                    execution = await asyncio.wait_for(self.execution_queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    continue
                
                logger.info(f"{worker_name} processing execution: {execution.id}")
                
                # Add to active executions
                self.active_executions[execution.id] = execution
                
                # Execute the workflow
                await self._process_workflow_execution(execution)
                
                # Remove from active executions
                self.active_executions.pop(execution.id, None)
                
                # Mark task as done
                self.execution_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in execution worker {worker_name}: {e}")
                await asyncio.sleep(1)
    
    async def _process_workflow_execution(self, execution: WorkflowExecution):
        """Process a single workflow execution"""
        try:
            # Update execution status
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = datetime.utcnow()
            
            # Get workflow definition
            workflows_collection = await get_workflows_collection()
            workflow_doc = await workflows_collection.find_one({"id": execution.workflow_id})
            workflow = AdvancedWorkflow(**workflow_doc)
            
            # Log execution start
            self._log_execution(execution, "info", "Workflow execution started")
            
            # Find starting action (first action or action specified by trigger)
            current_action = self._find_starting_action(workflow)
            
            # Execute actions sequentially
            while current_action:
                # Check timeout
                if self._is_execution_timeout(execution, workflow.timeout_minutes):
                    execution.status = ExecutionStatus.FAILED
                    execution.error_message = "Workflow execution timeout"
                    self._log_execution(execution, "error", "Execution timeout")
                    break
                
                # Execute current action
                success = await self._execute_action(execution, current_action, workflow)
                
                if not success:
                    execution.status = ExecutionStatus.FAILED
                    break
                
                # Find next action
                current_action = self._find_next_action(current_action, success, workflow)
            
            # Complete execution
            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                self._log_execution(execution, "info", "Workflow execution completed successfully")
            
            # Update workflow statistics
            await self._update_workflow_stats(workflow, execution.status == ExecutionStatus.COMPLETED)
            
            # Store execution results
            await self._store_execution_results(execution)
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            self._log_execution(execution, "error", f"Workflow execution failed: {e}")
            logger.error(f"Error processing workflow execution {execution.id}: {e}")
    
    async def _execute_action(self, execution: WorkflowExecution, action: WorkflowAction, 
                             workflow: AdvancedWorkflow) -> bool:
        """Execute a single workflow action"""
        try:
            execution.current_action_id = action.id
            self._log_execution(execution, "info", f"Executing action: {action.name}")
            
            # Check action conditions
            if action.conditions:
                conditions_met = conditional_logic_engine.evaluate_conditions(
                    action.conditions, execution.context_data
                )
                if not conditions_met:
                    self._log_execution(execution, "info", f"Action conditions not met, skipping: {action.name}")
                    return True  # Skip action but continue workflow
            
            # Apply delay if specified
            if action.delay_minutes:
                self._log_execution(execution, "info", f"Waiting {action.delay_minutes} minutes before action")
                await asyncio.sleep(action.delay_minutes * 60)
            
            # Check if approval required
            if workflow.approval_required and action.type in [ActionType.SEND_EMAIL, ActionType.UPDATE_LEAD]:
                return await self._handle_approval_action(execution, action, workflow)
            
            # Execute action based on type
            success = await self._execute_action_by_type(execution, action)
            
            if success:
                execution.executed_actions.append(action.id)
                self._log_execution(execution, "info", f"Action completed successfully: {action.name}")
            else:
                execution.failed_actions.append(action.id)
                self._log_execution(execution, "error", f"Action failed: {action.name}")
                
                # Retry logic
                if action.retry_count < action.max_retries:
                    action.retry_count += 1
                    self._log_execution(execution, "info", f"Retrying action {action.name} ({action.retry_count}/{action.max_retries})")
                    await asyncio.sleep(2 ** action.retry_count)  # Exponential backoff
                    return await self._execute_action(execution, action, workflow)
            
            return success
            
        except Exception as e:
            self._log_execution(execution, "error", f"Error executing action {action.name}: {e}")
            logger.error(f"Error executing action {action.id}: {e}")
            return False
    
    async def _execute_action_by_type(self, execution: WorkflowExecution, action: WorkflowAction) -> bool:
        """Execute action based on its type"""
        try:
            if action.type == ActionType.SEND_EMAIL:
                return await self._execute_send_email(execution, action)
            elif action.type == ActionType.UPDATE_LEAD:
                return await self._execute_update_lead(execution, action)
            elif action.type == ActionType.CREATE_TASK:
                return await self._execute_create_task(execution, action)
            elif action.type == ActionType.ASSIGN_AGENT:
                return await self._execute_assign_agent(execution, action)
            elif action.type == ActionType.GENERATE_DOCUMENT:
                return await self._execute_generate_document(execution, action)
            elif action.type == ActionType.WAIT_DELAY:
                return await self._execute_wait_delay(execution, action)
            elif action.type == ActionType.WEBHOOK_POST:
                return await self._execute_webhook_post(execution, action)
            elif action.type == ActionType.API_REQUEST:
                return await self._execute_api_request(execution, action)
            elif action.type == ActionType.NOTIFICATION:
                return await self._execute_notification(execution, action)
            else:
                logger.error(f"Unknown action type: {action.type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing action type {action.type}: {e}")
            return False
    
    async def _execute_send_email(self, execution: WorkflowExecution, action: WorkflowAction) -> bool:
        """Execute send email action"""
        try:
            params = action.parameters
            
            # Extract email details from parameters and context
            to_email = params.get('to_email') or execution.context_data.get('lead', {}).get('email')
            subject = params.get('subject', 'Automated Email')
            body = params.get('body', 'This is an automated email from your workflow.')
            
            # Template substitution
            context = execution.context_data
            subject = self._substitute_template_variables(subject, context)
            body = self._substitute_template_variables(body, context)
            
            if not to_email:
                self._log_execution(execution, "error", "No email address found for send email action")
                return False
            
            # In a real implementation, this would integrate with your email service
            # For now, we'll log the email and mark as successful
            execution.results[f"email_{action.id}"] = {
                "to": to_email,
                "subject": subject,
                "body": body,
                "sent_at": datetime.utcnow(),
                "status": "sent"
            }
            
            self._log_execution(execution, "info", f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def _execute_update_lead(self, execution: WorkflowExecution, action: WorkflowAction) -> bool:
        """Execute update lead action"""
        try:
            params = action.parameters
            lead_id = params.get('lead_id') or execution.context_data.get('lead', {}).get('id')
            
            if not lead_id:
                return False
            
            # Prepare updates
            updates = {}
            for key, value in params.get('updates', {}).items():
                # Substitute template variables
                if isinstance(value, str):
                    value = self._substitute_template_variables(value, execution.context_data)
                updates[key] = value
            
            if not updates:
                return False
            
            # Update lead in database
            leads_collection = await get_leads_collection()
            result = await leads_collection.update_one(
                {"id": lead_id},
                {"$set": {**updates, "updated_at": datetime.utcnow()}}
            )
            
            execution.results[f"lead_update_{action.id}"] = {
                "lead_id": lead_id,
                "updates": updates,
                "updated_at": datetime.utcnow(),
                "success": result.modified_count > 0
            }
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating lead: {e}")
            return False
    
    async def _execute_webhook_post(self, execution: WorkflowExecution, action: WorkflowAction) -> bool:
        """Execute webhook POST action"""
        try:
            params = action.parameters
            url = params.get('url')
            headers = params.get('headers', {})
            payload = params.get('payload', {})
            
            if not url:
                return False
            
            # Substitute template variables in payload
            payload = self._substitute_template_variables_recursive(payload, execution.context_data)
            
            # Make HTTP POST request
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_data = await response.text()
                    
                    execution.results[f"webhook_{action.id}"] = {
                        "url": url,
                        "status_code": response.status,
                        "response": response_data[:1000],  # Limit response size
                        "sent_at": datetime.utcnow()
                    }
                    
                    return 200 <= response.status < 300
            
        except Exception as e:
            logger.error(f"Error executing webhook: {e}")
            return False
    
    async def _execute_wait_delay(self, execution: WorkflowExecution, action: WorkflowAction) -> bool:
        """Execute wait/delay action"""
        try:
            delay_seconds = action.parameters.get('delay_seconds', 60)
            delay_minutes = action.parameters.get('delay_minutes', 0)
            
            total_delay = delay_seconds + (delay_minutes * 60)
            
            self._log_execution(execution, "info", f"Waiting {total_delay} seconds")
            await asyncio.sleep(total_delay)
            
            execution.results[f"delay_{action.id}"] = {
                "delay_seconds": total_delay,
                "completed_at": datetime.utcnow()
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Error in delay action: {e}")
            return False
    
    async def _execute_notification(self, execution: WorkflowExecution, action: WorkflowAction) -> bool:
        """Execute notification action"""
        try:
            params = action.parameters
            message = params.get('message', 'Workflow notification')
            notification_type = params.get('type', 'info')
            
            # Substitute template variables
            message = self._substitute_template_variables(message, execution.context_data)
            
            # Store notification (in real implementation, would send to notification system)
            execution.results[f"notification_{action.id}"] = {
                "message": message,
                "type": notification_type,
                "created_at": datetime.utcnow()
            }
            
            self._log_execution(execution, "info", f"Notification: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    async def _handle_approval_action(self, execution: WorkflowExecution, action: WorkflowAction, 
                                    workflow: AdvancedWorkflow) -> bool:
        """Handle action that requires approval"""
        # Add to pending approvals
        execution.pending_approvals.append(action.id)
        execution.status = ExecutionStatus.WAITING
        
        self._log_execution(execution, "info", f"Action {action.name} requires approval")
        
        # In a real implementation, this would:
        # 1. Send approval notifications to approvers
        # 2. Wait for approval response
        # 3. Continue or stop based on approval
        
        # For this demo, we'll simulate immediate approval
        execution.approved_by.append("system")
        execution.pending_approvals.remove(action.id)
        execution.status = ExecutionStatus.RUNNING
        
        self._log_execution(execution, "info", f"Action {action.name} approved (simulated)")
        return True
    
    def _substitute_template_variables(self, template: str, context: Dict[str, Any]) -> str:
        """Substitute template variables in string"""
        if not isinstance(template, str):
            return template
        
        import re
        
        # Find all {{variable}} patterns
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            value = self._extract_nested_value(var_path, context)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(pattern, replace_var, template)
    
    def _substitute_template_variables_recursive(self, data: Any, context: Dict[str, Any]) -> Any:
        """Recursively substitute template variables in nested data structures"""
        if isinstance(data, dict):
            return {k: self._substitute_template_variables_recursive(v, context) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_template_variables_recursive(item, context) for item in data]
        elif isinstance(data, str):
            return self._substitute_template_variables(data, context)
        else:
            return data
    
    def _extract_nested_value(self, path: str, data: Dict[str, Any]) -> Any:
        """Extract nested value using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _find_starting_action(self, workflow: AdvancedWorkflow) -> Optional[WorkflowAction]:
        """Find the starting action of the workflow"""
        if not workflow.actions:
            return None
        return workflow.actions[0]  # Simple: first action
    
    def _find_next_action(self, current_action: WorkflowAction, success: bool, 
                         workflow: AdvancedWorkflow) -> Optional[WorkflowAction]:
        """Find the next action to execute"""
        # Check for explicit next action references
        next_action_id = current_action.on_success_action_id if success else current_action.on_failure_action_id
        
        if next_action_id:
            for action in workflow.actions:
                if action.id == next_action_id:
                    return action
        
        # Sequential execution: find next action in list
        current_index = -1
        for i, action in enumerate(workflow.actions):
            if action.id == current_action.id:
                current_index = i
                break
        
        if current_index >= 0 and current_index + 1 < len(workflow.actions):
            return workflow.actions[current_index + 1]
        
        return None  # End of workflow
    
    def _is_execution_timeout(self, execution: WorkflowExecution, timeout_minutes: int) -> bool:
        """Check if execution has timed out"""
        if not execution.started_at:
            return False
        
        elapsed = datetime.utcnow() - execution.started_at
        return elapsed.seconds > (timeout_minutes * 60)
    
    def _log_execution(self, execution: WorkflowExecution, level: str, message: str):
        """Log execution event"""
        log_entry = {
            "timestamp": datetime.utcnow(),
            "level": level,
            "message": message,
            "action_id": execution.current_action_id
        }
        
        execution.execution_log.append(log_entry)
        
        # Also log to system logger
        if level == "error":
            logger.error(f"Execution {execution.id}: {message}")
        elif level == "warning":
            logger.warning(f"Execution {execution.id}: {message}")
        else:
            logger.info(f"Execution {execution.id}: {message}")
    
    async def _update_workflow_stats(self, workflow: AdvancedWorkflow, success: bool):
        """Update workflow execution statistics"""
        try:
            workflows_collection = await get_workflows_collection()
            
            updates = {
                "execution_count": workflow.execution_count + 1,
                "last_executed": datetime.utcnow()
            }
            
            if success:
                updates["success_count"] = workflow.success_count + 1
            else:
                updates["failure_count"] = workflow.failure_count + 1
            
            await workflows_collection.update_one(
                {"id": workflow.id},
                {"$set": updates}
            )
            
        except Exception as e:
            logger.error(f"Error updating workflow stats: {e}")
    
    async def _store_execution_results(self, execution: WorkflowExecution):
        """Store execution results in database"""
        try:
            # In a real implementation, this would save to an executions collection
            logger.info(f"Execution {execution.id} completed with status: {execution.status}")
            
            # Store basic execution info in activities
            activities_collection = await get_activities_collection()
            
            activity = {
                "activity_type": "workflow_execution",
                "workflow_id": execution.workflow_id,
                "execution_id": execution.id,
                "status": execution.status,
                "triggered_by": execution.triggered_by,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "duration_seconds": (execution.completed_at - execution.started_at).seconds if execution.completed_at and execution.started_at else None,
                "actions_executed": len(execution.executed_actions),
                "actions_failed": len(execution.failed_actions),
                "timestamp": datetime.utcnow()
            }
            
            await activities_collection.insert_one(activity)
            
        except Exception as e:
            logger.error(f"Error storing execution results: {e}")

# Global execution engine instance
execution_engine = WorkflowExecutionEngine()

# API Endpoints
@router.post("/execute", response_model=Dict[str, Any])
async def execute_workflow(request: WorkflowExecutionRequest):
    """Execute a workflow with given context data"""
    try:
        execution_id = await execution_engine.execute_workflow(
            request.workflow_id,
            request.context_data,
            request.triggered_by
        )
        
        return {
            "execution_id": execution_id,
            "status": "queued",
            "message": "Workflow execution started"
        }
        
    except Exception as e:
        logger.error(f"Error starting workflow execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get status of a workflow execution"""
    try:
        # Check active executions
        if execution_id in execution_engine.active_executions:
            execution = execution_engine.active_executions[execution_id]
            return {
                "execution_id": execution_id,
                "status": execution.status,
                "current_action": execution.current_action_id,
                "progress": {
                    "executed_actions": len(execution.executed_actions),
                    "failed_actions": len(execution.failed_actions),
                    "pending_approvals": len(execution.pending_approvals)
                },
                "started_at": execution.started_at,
                "runtime_seconds": (datetime.utcnow() - execution.started_at).seconds if execution.started_at else 0
            }
        
        # Check completed executions in activities
        activities_collection = await get_activities_collection()
        activity = await activities_collection.find_one({
            "activity_type": "workflow_execution",
            "execution_id": execution_id
        })
        
        if activity:
            return {
                "execution_id": execution_id,
                "status": activity.get("status", "unknown"),
                "completed": True,
                "started_at": activity.get("started_at"),
                "completed_at": activity.get("completed_at"),
                "duration_seconds": activity.get("duration_seconds"),
                "actions_executed": activity.get("actions_executed", 0),
                "actions_failed": activity.get("actions_failed", 0)
            }
        
        raise HTTPException(status_code=404, detail="Execution not found")
        
    except Exception as e:
        logger.error(f"Error getting execution status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get execution status")

@router.post("/engine/start")
async def start_execution_engine():
    """Start the workflow execution engine"""
    try:
        await execution_engine.start_engine()
        return {
            "message": "Workflow execution engine started",
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Error starting execution engine: {e}")
        raise HTTPException(status_code=500, detail="Failed to start execution engine")

@router.get("/engine/status")
async def get_engine_status():
    """Get status of the workflow execution engine"""
    return {
        "running": execution_engine.running,
        "active_executions": len(execution_engine.active_executions),
        "queue_size": execution_engine.execution_queue.qsize(),
        "max_concurrent": execution_engine.max_concurrent_executions,
        "worker_count": execution_engine.max_concurrent_executions
    }