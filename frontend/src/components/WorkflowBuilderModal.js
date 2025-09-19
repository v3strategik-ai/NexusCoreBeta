import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from './ui/dialog'
import { 
  Workflow, 
  Plus, 
  Trash2, 
  Play,
  Pause,
  Settings,
  Clock,
  Zap,
  Mail,
  FileText,
  Database,
  ChevronDown,
  ChevronRight,
  Loader2,
  Save,
  ArrowDown,
  ArrowRight
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const TRIGGER_TYPES = [
  { value: 'manual', label: 'Manual Trigger', description: 'Start workflow manually' },
  { value: 'scheduled', label: 'Time-based', description: 'Run on schedule' },
  { value: 'event_based', label: 'Event-based', description: 'Trigger on events' },
  { value: 'data_based', label: 'Data-based', description: 'Trigger on data changes' }
]

const ACTION_TYPES = [
  { 
    value: 'send_email', 
    label: 'Send Email', 
    icon: Mail, 
    description: 'Send automated email',
    fields: ['recipient', 'subject', 'body']
  },
  { 
    value: 'update_crm', 
    label: 'Update CRM', 
    icon: Database, 
    description: 'Update lead or contact',
    fields: ['lead_id', 'field', 'value']
  },
  { 
    value: 'generate_document', 
    label: 'Generate Document', 
    icon: FileText, 
    description: 'Create AI document',
    fields: ['document_type', 'template', 'variables']
  },
  { 
    value: 'assign_task', 
    label: 'Assign Task', 
    icon: Zap, 
    description: 'Assign task to agent',
    fields: ['agent_id', 'task_description', 'priority']
  },
  { 
    value: 'wait', 
    label: 'Wait/Delay', 
    icon: Clock, 
    description: 'Add time delay',
    fields: ['duration', 'unit']
  },
  { 
    value: 'condition', 
    label: 'Condition', 
    icon: Settings, 
    description: 'Branch based on condition',
    fields: ['condition', 'true_action', 'false_action']
  }
]

export function WorkflowBuilderModal({ children, agents, onWorkflowCreated }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [workflow, setWorkflow] = useState({
    name: '',
    description: '',
    trigger_type: 'manual',
    trigger_config: {},
    steps: [
      {
        id: 'step_1',
        name: 'Start',
        type: 'start',
        configuration: {},
        order: 0
      }
    ],
    agent_id: ''
  })

  const addStep = (afterStepId = null) => {
    const newStep = {
      id: `step_${Date.now()}`,
      name: 'New Step',
      type: 'send_email',
      configuration: {},
      order: afterStepId ? workflow.steps.find(s => s.id === afterStepId)?.order + 1 : workflow.steps.length
    }

    // Reorder steps if inserting in middle
    const updatedSteps = workflow.steps.map(step => 
      afterStepId && step.order >= newStep.order 
        ? { ...step, order: step.order + 1 }
        : step
    )

    setWorkflow(prev => ({
      ...prev,
      steps: [...updatedSteps, newStep].sort((a, b) => a.order - b.order)
    }))
  }

  const removeStep = (stepId) => {
    const stepToRemove = workflow.steps.find(s => s.id === stepId)
    if (stepToRemove?.type === 'start') return // Can't remove start step

    setWorkflow(prev => ({
      ...prev,
      steps: prev.steps
        .filter(s => s.id !== stepId)
        .map(step => 
          step.order > stepToRemove.order 
            ? { ...step, order: step.order - 1 }
            : step
        )
    }))
  }

  const updateStep = (stepId, updates) => {
    setWorkflow(prev => ({
      ...prev,
      steps: prev.steps.map(step => 
        step.id === stepId ? { ...step, ...updates } : step
      )
    }))
  }

  const handleSave = async () => {
    if (!workflow.name) {
      alert('Please enter a workflow name')
      return
    }

    setIsLoading(true)

    try {
      const workflowData = {
        name: workflow.name,
        description: workflow.description,
        trigger_type: workflow.trigger_type,
        trigger_config: workflow.trigger_config,
        steps: workflow.steps.filter(s => s.type !== 'start'), // Remove start step for backend
        agent_id: workflow.agent_id || null
      }

      const response = await axios.post(`${API}/workflows/`, workflowData)
      
      console.log('Workflow created:', response.data)
      
      if (onWorkflowCreated) {
        onWorkflowCreated(response.data)
      }
      
      setIsOpen(false)
      
      // Reset form
      setWorkflow({
        name: '',
        description: '',
        trigger_type: 'manual',
        trigger_config: {},
        steps: [
          {
            id: 'step_1',
            name: 'Start',
            type: 'start',
            configuration: {},
            order: 0
          }
        ],
        agent_id: 'no_agent'
      })

    } catch (error) {
      console.error('Error creating workflow:', error)
      alert('Failed to create workflow. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const StepCard = ({ step, index }) => {
    const actionType = ACTION_TYPES.find(t => t.type === step.type)
    const isStart = step.type === 'start'
    
    return (
      <div className="relative">
        <Card className={`quantum-bg border-2 ${isStart ? 'border-green-500' : 'border-primary/20'} hover:border-primary/50 transition-colors`}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isStart ? (
                  <Play className="w-5 h-5 text-green-400" />
                ) : actionType ? (
                  <actionType.icon className="w-5 h-5 text-primary" />
                ) : (
                  <Settings className="w-5 h-5 text-muted-foreground" />
                )}
                <CardTitle className="text-sm">
                  {isStart ? 'Workflow Start' : step.name}
                </CardTitle>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  Step {step.order + 1}
                </Badge>
                {!isStart && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeStep(step.id)}
                    className="h-6 w-6 p-0 text-red-400 hover:text-red-600"
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                )}
              </div>
            </div>
            <CardDescription className="text-xs">
              {isStart ? 'Workflow begins here' : actionType?.description || 'Configure this step'}
            </CardDescription>
          </CardHeader>
          
          {!isStart && (
            <CardContent className="pt-0 space-y-3">
              <div>
                <Label className="text-xs">Action Type</Label>
                <Select 
                  value={step.type} 
                  onValueChange={(value) => updateStep(step.id, { type: value, name: ACTION_TYPES.find(t => t.value === value)?.label || 'New Step' })}
                >
                  <SelectTrigger className="h-8">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ACTION_TYPES.map((action) => (
                      <SelectItem key={action.value} value={action.value}>
                        <div className="flex items-center gap-2">
                          <action.icon className="w-4 h-4" />
                          <span>{action.label}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Dynamic configuration fields based on action type */}
              {actionType?.fields?.map((field) => (
                <div key={field}>
                  <Label className="text-xs capitalize">{field.replace('_', ' ')}</Label>
                  <Input
                    className="h-8 text-xs"
                    placeholder={`Enter ${field.replace('_', ' ')}`}
                    value={step.configuration[field] || ''}
                    onChange={(e) => updateStep(step.id, {
                      configuration: { ...step.configuration, [field]: e.target.value }
                    })}
                  />
                </div>
              ))}
            </CardContent>
          )}
        </Card>
        
        {/* Arrow to next step */}
        {index < workflow.steps.length - 1 && (
          <div className="flex justify-center my-2">
            <ArrowDown className="w-5 h-5 text-primary" />
          </div>
        )}
        
        {/* Add step button */}
        {!isStart && (
          <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => addStep(step.id)}
              className="h-6 w-6 p-0 rounded-full border-dashed border-primary/50 hover:border-primary"
            >
              <Plus className="w-3 h-3" />
            </Button>
          </div>
        )}
      </div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-6xl w-[95vw] h-[85vh] flex flex-col quantum-bg">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-3">
            <Workflow className="w-6 h-6 text-primary" />
            <span className="gradient-text">Workflow Builder</span>
          </DialogTitle>
          <DialogDescription>
            Create automated workflows to streamline your business processes
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 flex gap-6 min-h-0">
          {/* Workflow Configuration Panel */}
          <div className="w-1/3 space-y-4 overflow-y-auto">
            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="text-base">Workflow Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="workflow_name">Workflow Name</Label>
                  <Input
                    id="workflow_name"
                    value={workflow.name}
                    onChange={(e) => setWorkflow(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., Lead Nurturing Sequence"
                  />
                </div>
                
                <div>
                  <Label htmlFor="workflow_description">Description</Label>
                  <Textarea
                    id="workflow_description"
                    value={workflow.description}
                    onChange={(e) => setWorkflow(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe what this workflow does..."
                    rows={3}
                  />
                </div>
                
                <div>
                  <Label htmlFor="trigger_type">Trigger Type</Label>
                  <Select 
                    value={workflow.trigger_type} 
                    onValueChange={(value) => setWorkflow(prev => ({ ...prev, trigger_type: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TRIGGER_TYPES.map((trigger) => (
                        <SelectItem key={trigger.value} value={trigger.value}>
                          <div className="flex flex-col">
                            <span>{trigger.label}</span>
                            <span className="text-xs text-muted-foreground">{trigger.description}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label htmlFor="assigned_agent">Assigned Agent</Label>
                  <Select 
                    value={workflow.agent_id} 
                    onValueChange={(value) => setWorkflow(prev => ({ ...prev, agent_id: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select agent (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="no_agent">No specific agent</SelectItem>
                      {agents?.map((agent) => (
                        <SelectItem key={agent.id} value={agent.id}>
                          {agent.name} - {agent.type}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Workflow Statistics */}
            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="text-base">Workflow Stats</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-2xl font-bold gradient-text">{workflow.steps.length - 1}</div>
                    <p className="text-xs text-muted-foreground">Steps</p>
                  </div>
                  <div>
                    <div className="text-2xl font-bold gradient-text">
                      {workflow.trigger_type === 'manual' ? 'Manual' : 'Auto'}
                    </div>
                    <p className="text-xs text-muted-foreground">Trigger</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Workflow Visual Builder */}
          <div className="flex-1 overflow-y-auto">
            <div className="space-y-4 pb-20">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold gradient-text">Workflow Steps</h3>
                <Button
                  onClick={() => addStep()}
                  className="glow-effect"
                  size="sm"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Step
                </Button>
              </div>

              {workflow.steps
                .sort((a, b) => a.order - b.order)
                .map((step, index) => (
                  <StepCard key={step.id} step={step} index={index} />
                ))
              }
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-2 pt-4 border-t border-border flex-shrink-0">
          <Button 
            variant="outline" 
            onClick={() => setIsOpen(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSave}
            disabled={isLoading || !workflow.name}
            className="glow-effect"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Create Workflow
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}