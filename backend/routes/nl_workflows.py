from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field
import json
import re
import os
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from database import get_workflows_collection
from .workflow_engine import (
    AdvancedWorkflow, WorkflowAction, WorkflowTrigger, WorkflowCondition,
    ActionType, TriggerType, ConditionOperator
)

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/nl-workflows", tags=["natural-language-workflows"])
logger = logging.getLogger(__name__)

# Pydantic Models
class NLWorkflowRequest(BaseModel):
    description: str = Field(description="Natural language description of the workflow")
    context: Optional[str] = Field(default=None, description="Additional context or requirements")
    creator_id: str = Field(description="ID of the user creating the workflow")
    
class NLWorkflowResponse(BaseModel):
    workflow: AdvancedWorkflow
    confidence: float = Field(ge=0, le=1, description="Confidence in the generated workflow")
    suggestions: List[str] = Field(default=[], description="Suggested improvements or alternatives")
    warnings: List[str] = Field(default=[], description="Potential issues or considerations")

class WorkflowTemplate(BaseModel):
    name: str
    description: str
    template_workflow: AdvancedWorkflow
    use_cases: List[str]
    difficulty: str = Field(description="easy, medium, hard")

class NaturalLanguageWorkflowEngine:
    """AI-powered natural language workflow creation system"""
    
    def __init__(self):
        self.api_key = os.getenv('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY environment variable is required")
        
        self.model_name = "gpt-4o"  # Use more capable model for workflow generation
        self.provider = "openai"
        
        # Workflow patterns and templates
        self.common_patterns = {
            "lead_follow_up": {
                "triggers": ["when a lead is created", "when lead score changes", "after X days"],
                "actions": ["send email", "assign agent", "update status", "create task"]
            },
            "approval_process": {
                "triggers": ["when document is created", "when deal value exceeds X", "manual trigger"],
                "actions": ["request approval", "send notification", "wait for response", "update status"]
            },
            "nurturing_sequence": {
                "triggers": ["when lead enters funnel", "time-based schedule", "behavior trigger"],
                "actions": ["send series of emails", "track engagement", "score lead", "move to next stage"]
            },
            "task_automation": {
                "triggers": ["when task is overdue", "when priority changes", "time-based"],
                "actions": ["reassign task", "escalate to manager", "send reminder", "update deadline"]
            }
        }
        
        # Action templates with parameters
        self.action_templates = {
            "send_email": {
                "type": ActionType.SEND_EMAIL,
                "required_params": ["to_email", "subject", "body"],
                "optional_params": ["template_id", "delay_minutes"]
            },
            "update_lead": {
                "type": ActionType.UPDATE_LEAD,
                "required_params": ["lead_id", "updates"],
                "optional_params": ["conditions"]
            },
            "assign_agent": {
                "type": ActionType.ASSIGN_AGENT,
                "required_params": ["agent_id"],
                "optional_params": ["lead_id", "criteria"]
            },
            "create_task": {
                "type": ActionType.CREATE_TASK,
                "required_params": ["title", "description"],
                "optional_params": ["assignee", "due_date", "priority"]
            },
            "wait_delay": {
                "type": ActionType.WAIT_DELAY,
                "required_params": ["delay_minutes"],
                "optional_params": ["condition_check"]
            },
            "webhook": {
                "type": ActionType.WEBHOOK_POST,
                "required_params": ["url", "payload"],
                "optional_params": ["headers", "authentication"]
            }
        }
    
    async def create_workflow_from_nl(self, request: NLWorkflowRequest) -> NLWorkflowResponse:
        """Create workflow from natural language description"""
        try:
            # Analyze the natural language description
            analysis = await self._analyze_workflow_description(request.description, request.context)
            
            # Generate workflow structure
            workflow = await self._generate_workflow_structure(analysis, request.creator_id)
            
            # Validate and optimize workflow
            validation_results = await self._validate_generated_workflow(workflow)
            
            return NLWorkflowResponse(
                workflow=workflow,
                confidence=analysis.get('confidence', 0.7),
                suggestions=analysis.get('suggestions', []),
                warnings=validation_results.get('warnings', [])
            )
            
        except Exception as e:
            logger.error(f"Error creating workflow from NL: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")
    
    async def _analyze_workflow_description(self, description: str, context: Optional[str]) -> Dict[str, Any]:
        """Analyze natural language description to extract workflow components"""
        try:
            # Build analysis prompt
            system_message = """You are an expert workflow automation analyst. Your task is to analyze natural language descriptions and extract structured workflow components.

Focus on identifying:
1. Trigger conditions (what starts the workflow)
2. Actions to perform (what the workflow does)
3. Conditional logic (if/then statements)
4. Timing and delays (when things happen)
5. Data requirements (what data is needed)
6. Success/failure handling

Provide analysis in JSON format with specific, actionable workflow components."""

            # Initialize chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"nl_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                system_message=system_message
            ).with_model(self.provider, self.model_name)
            
            analysis_prompt = f"""
Analyze this workflow description and extract structured components:

WORKFLOW DESCRIPTION:
"{description}"

{f'ADDITIONAL CONTEXT: {context}' if context else ''}

Provide detailed analysis in this JSON format:
{{
    "workflow_name": "suggested workflow name",
    "workflow_category": "lead_management|approval_process|nurturing|task_automation|custom",
    "confidence": 0.0-1.0,
    "trigger_analysis": {{
        "type": "manual|time_based|event_based|condition_based",
        "description": "what triggers this workflow",
        "schedule": "if time-based, the schedule (daily, hourly, etc.)",
        "conditions": [
            {{
                "field": "data field to check",
                "operator": "equals|greater_than|contains|etc.",
                "value": "value to compare",
                "description": "human readable condition"
            }}
        ]
    }},
    "actions_analysis": [
        {{
            "action_type": "send_email|update_lead|create_task|assign_agent|wait_delay|webhook_post|notification",
            "description": "what this action does",
            "parameters": {{
                "key": "value pairs for action configuration"
            }},
            "conditions": [
                "any conditions for this action"
            ],
            "order": 1,
            "delay_minutes": null
        }}
    ],
    "conditional_logic": [
        {{
            "if_condition": "condition description",
            "then_actions": ["list of action indices"],
            "else_actions": ["list of action indices"]
        }}
    ],
    "data_requirements": [
        "list of data fields needed (lead.email, agent.id, etc.)"
    ],
    "approval_required": true/false,
    "estimated_complexity": "low|medium|high",
    "suggestions": [
        "suggested improvements or alternatives"
    ],
    "potential_issues": [
        "potential problems or considerations"
    ]
}}

Focus on practical, implementable workflow components that align with business automation needs.
"""
            
            user_message = UserMessage(text=analysis_prompt)
            response = await chat.send_message(user_message)
            
            # Parse AI response
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse workflow analysis JSON: {response}")
                # Return fallback analysis
                return {
                    "workflow_name": "Custom Workflow",
                    "workflow_category": "custom",
                    "confidence": 0.5,
                    "trigger_analysis": {
                        "type": "manual",
                        "description": "Manual trigger",
                        "conditions": []
                    },
                    "actions_analysis": [
                        {
                            "action_type": "notification",
                            "description": "Send notification",
                            "parameters": {"message": "Workflow executed"},
                            "order": 1
                        }
                    ],
                    "conditional_logic": [],
                    "data_requirements": [],
                    "approval_required": False,
                    "estimated_complexity": "medium",
                    "suggestions": ["Review and customize the generated workflow"],
                    "potential_issues": ["AI analysis parsing failed"]
                }
                
        except Exception as e:
            logger.error(f"Error analyzing workflow description: {e}")
            raise
    
    async def _generate_workflow_structure(self, analysis: Dict[str, Any], creator_id: str) -> AdvancedWorkflow:
        """Generate AdvancedWorkflow object from analysis"""
        try:
            # Create trigger
            trigger_analysis = analysis.get('trigger_analysis', {})
            trigger = WorkflowTrigger(
                type=TriggerType(trigger_analysis.get('type', 'manual')),
                name=trigger_analysis.get('description', 'Workflow Trigger'),
                parameters={},
                schedule=trigger_analysis.get('schedule')
            )
            
            # Add trigger conditions
            for condition_data in trigger_analysis.get('conditions', []):
                condition = WorkflowCondition(
                    field=condition_data.get('field', 'lead.status'),
                    operator=ConditionOperator(condition_data.get('operator', 'equals')),
                    value=condition_data.get('value', ''),
                    data_type=self._infer_data_type(condition_data.get('value'))
                )
                trigger.conditions.append(condition)
            
            # Create actions
            actions = []
            actions_analysis = analysis.get('actions_analysis', [])
            
            for i, action_data in enumerate(actions_analysis):
                action_type_str = action_data.get('action_type', 'notification')
                
                # Map action type string to enum
                try:
                    action_type = ActionType(action_type_str)
                except ValueError:
                    action_type = ActionType.NOTIFICATION
                
                action = WorkflowAction(
                    type=action_type,
                    name=action_data.get('description', f'Action {i+1}'),
                    parameters=action_data.get('parameters', {}),
                    delay_minutes=action_data.get('delay_minutes')
                )
                
                # Add action conditions
                for condition_desc in action_data.get('conditions', []):
                    # Parse condition description into structured condition
                    condition = self._parse_condition_description(condition_desc)
                    if condition:
                        action.conditions.append(condition)
                
                actions.append(action)
            
            # Link actions (simple sequential for now)
            for i in range(len(actions) - 1):
                actions[i].on_success_action_id = actions[i + 1].id
            
            # Create workflow
            workflow = AdvancedWorkflow(
                name=analysis.get('workflow_name', 'Generated Workflow'),
                description=f"Auto-generated workflow from natural language description",
                trigger=trigger,
                actions=actions,
                created_by=creator_id,
                category=analysis.get('workflow_category', 'custom'),
                approval_required=analysis.get('approval_required', False),
                tags=['auto-generated', 'nl-created']
            )
            
            # Add conditional branches if specified
            conditional_logic = analysis.get('conditional_logic', [])
            for logic in conditional_logic:
                # Implement conditional branching logic
                # This would map conditions to specific action paths
                pass
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error generating workflow structure: {e}")
            raise
    
    def _parse_condition_description(self, description: str) -> Optional[WorkflowCondition]:
        """Parse natural language condition into structured condition"""
        try:
            # Simple pattern matching for common condition formats
            patterns = [
                (r'(\w+\.?\w*)\s*(equals?|is|==)\s*(["\']?)([^"\']+)\3', 'equals'),
                (r'(\w+\.?\w*)\s*(greater than|>)\s*(\d+\.?\d*)', 'greater_than'),
                (r'(\w+\.?\w*)\s*(less than|<)\s*(\d+\.?\d*)', 'less_than'),
                (r'(\w+\.?\w*)\s*(contains?)\s*(["\']?)([^"\']+)\3', 'contains'),
                (r'(\w+\.?\w*)\s*(is empty|empty)', 'is_empty')
            ]
            
            for pattern, operator in patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    field = match.group(1)
                    value = match.group(4) if len(match.groups()) >= 4 else match.group(3)
                    
                    return WorkflowCondition(
                        field=field,
                        operator=ConditionOperator(operator),
                        value=value,
                        data_type=self._infer_data_type(value)
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing condition description: {e}")
            return None
    
    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from value"""
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, str):
            # Try to detect if it's a number
            try:
                float(value)
                return "number"
            except ValueError:
                # Check if it's a boolean string
                if value.lower() in ['true', 'false', 'yes', 'no']:
                    return "boolean"
                return "string"
        else:
            return "string"
    
    async def _validate_generated_workflow(self, workflow: AdvancedWorkflow) -> Dict[str, Any]:
        """Validate the generated workflow and provide suggestions"""
        validation_results = {
            "valid": True,
            "warnings": [],
            "suggestions": [],
            "complexity_score": 0
        }
        
        # Check for common issues
        if not workflow.actions:
            validation_results["valid"] = False
            validation_results["warnings"].append("Workflow has no actions")
        
        # Check action parameters
        for action in workflow.actions:
            template = self.action_templates.get(action.type.value)
            if template:
                required_params = template.get('required_params', [])
                missing_params = [param for param in required_params if param not in action.parameters]
                if missing_params:
                    validation_results["warnings"].append(f"Action '{action.name}' missing required parameters: {missing_params}")
        
        # Calculate complexity
        complexity_factors = [
            len(workflow.actions),
            sum(len(action.conditions) for action in workflow.actions),
            len(workflow.conditional_branches),
            1 if workflow.approval_required else 0
        ]
        validation_results["complexity_score"] = sum(complexity_factors)
        
        # Generate suggestions
        if validation_results["complexity_score"] > 10:
            validation_results["suggestions"].append("Consider breaking this into smaller workflows")
        
        if not any(action.type == ActionType.NOTIFICATION for action in workflow.actions):
            validation_results["suggestions"].append("Consider adding notification actions to track workflow progress")
        
        return validation_results

# Global NL workflow engine instance
nl_workflow_engine = NaturalLanguageWorkflowEngine()

# API Endpoints
@router.post("/create", response_model=NLWorkflowResponse)
async def create_workflow_from_natural_language(request: NLWorkflowRequest):
    """Create a workflow from natural language description"""
    try:
        return await nl_workflow_engine.create_workflow_from_nl(request)
    except Exception as e:
        logger.error(f"Error creating workflow from NL: {e}")
        raise HTTPException(status_code=500, detail="Failed to create workflow from description")

@router.get("/templates")
async def get_workflow_templates():
    """Get available workflow templates for common use cases"""
    templates = [
        {
            "id": "lead_nurturing",
            "name": "Lead Nurturing Sequence",
            "description": "Automated email sequence for nurturing leads through the funnel",
            "example": "Send a welcome email when a new lead is created, wait 3 days, then send a product demo email if they haven't converted",
            "category": "lead_management",
            "difficulty": "easy"
        },
        {
            "id": "approval_workflow", 
            "name": "Multi-Step Approval Process",
            "description": "Route documents or deals through approval chains",
            "example": "When a deal value exceeds $10,000, request approval from sales manager, then from director if approved",
            "category": "approval_process",
            "difficulty": "medium"
        },
        {
            "id": "lead_scoring_automation",
            "name": "Lead Scoring Automation",
            "description": "Automatically score and route leads based on behavior",
            "example": "When lead score exceeds 75, assign to senior sales rep and send personalized email",
            "category": "lead_management", 
            "difficulty": "medium"
        },
        {
            "id": "task_escalation",
            "name": "Task Escalation Workflow",
            "description": "Escalate overdue tasks to managers",
            "example": "When a task is overdue by 2 days, send reminder to assignee, if still overdue after 1 more day, escalate to manager",
            "category": "task_automation",
            "difficulty": "easy"
        },
        {
            "id": "customer_onboarding",
            "name": "Customer Onboarding Sequence",
            "description": "Automated onboarding process for new customers",
            "example": "When customer signs up, send welcome email, create onboarding tasks, schedule check-in calls",
            "category": "customer_success",
            "difficulty": "hard"
        }
    ]
    
    return {
        "templates": templates,
        "categories": ["lead_management", "approval_process", "task_automation", "customer_success", "custom"],
        "difficulty_levels": ["easy", "medium", "hard"],
        "supported_patterns": list(nl_workflow_engine.common_patterns.keys())
    }

@router.post("/analyze")
async def analyze_workflow_description(description: str, context: Optional[str] = None):
    """Analyze a natural language workflow description without creating the workflow"""
    try:
        analysis = await nl_workflow_engine._analyze_workflow_description(description, context)
        return {
            "analysis": analysis,
            "feasibility": "high" if analysis.get('confidence', 0) > 0.7 else "medium" if analysis.get('confidence', 0) > 0.5 else "low",
            "estimated_setup_time": f"{analysis.get('estimated_complexity', 'medium')} complexity",
            "data_requirements": analysis.get('data_requirements', []),
            "suggestions": analysis.get('suggestions', [])
        }
    except Exception as e:
        logger.error(f"Error analyzing workflow description: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze workflow description")

@router.get("/examples")
async def get_nl_workflow_examples():
    """Get example natural language workflow descriptions"""
    examples = [
        {
            "category": "Lead Management",
            "examples": [
                "Send a follow-up email to leads who haven't responded in 3 days",
                "When a lead's score exceeds 80, assign them to our best sales rep",
                "Create a task for the sales team when a lead downloads a pricing guide",
                "Send a personalized demo invitation to leads from enterprise companies"
            ]
        },
        {
            "category": "Customer Success", 
            "examples": [
                "Send onboarding emails every 2 days for new customers for 2 weeks",
                "Create a check-in task 30 days after customer signup",
                "When customer usage drops below 50% of average, send re-engagement email",
                "Escalate to success manager if customer hasn't logged in for 14 days"
            ]
        },
        {
            "category": "Sales Process",
            "examples": [
                "When deal value exceeds $50K, require manager approval before closing",
                "Send contract reminders every 3 days until signed",
                "Create renewal task 60 days before contract expiration",
                "Update lead status to qualified when they attend a demo"
            ]
        },
        {
            "category": "Task Automation",
            "examples": [
                "Reassign overdue tasks to team lead after 2 days",
                "Send daily digest of pending approvals to managers",
                "Create follow-up task when meeting is marked as completed",
                "Notify team when high-priority task is created"
            ]
        }
    ]
    
    return {
        "examples": examples,
        "tips": [
            "Be specific about timing (e.g., '3 days', 'every week')",
            "Include conditions clearly (e.g., 'when score exceeds 80')",
            "Specify what actions to take (e.g., 'send email', 'create task')",
            "Mention any approvals or escalations needed",
            "Consider different scenarios (success/failure paths)"
        ],
        "common_triggers": [
            "when a new lead is created",
            "when lead score changes",
            "when task becomes overdue", 
            "when deal value exceeds amount",
            "on a schedule (daily, weekly, etc.)",
            "when status changes to X"
        ],
        "common_actions": [
            "send email to [recipient]",
            "create task for [assignee]",
            "update [field] to [value]",
            "assign [resource] to [person]",
            "send notification to [team]",
            "request approval from [approver]",
            "wait for [time period]",
            "call webhook [url]"
        ]
    }