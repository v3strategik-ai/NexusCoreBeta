import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog'
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  User, 
  Users, 
  Shield, 
  AlertCircle,
  Plus,
  Play,
  Pause,
  Settings,
  ArrowRight,
  ArrowDown,
  UserCheck,
  FileText
} from 'lucide-react'

export function MultiStepApprovalProcesses() {
  const [approvalProcesses, setApprovalProcesses] = useState([])
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [approvers, setApprovers] = useState([])
  const [loading, setLoading] = useState(false)
  const [newProcess, setNewProcess] = useState({
    name: '',
    description: '',
    steps: [],
    timeout_hours: 24,
    auto_escalate: true
  })
  const [newStep, setNewStep] = useState({
    name: '',
    approver_roles: [],
    required_approvals: 1,
    parallel: false
  })
  const [activeTab, setActiveTab] = useState('processes')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  const approverRoles = [
    { id: 'manager', name: 'Manager', description: 'Direct line manager' },
    { id: 'senior_manager', name: 'Senior Manager', description: 'Department head' },
    { id: 'finance', name: 'Finance', description: 'Financial approval' },
    { id: 'hr', name: 'HR', description: 'Human resources approval' },
    { id: 'legal', name: 'Legal', description: 'Legal compliance review' },
    { id: 'executive', name: 'Executive', description: 'C-level executive' }
  ]

  const processTemplates = [
    {
      name: 'Lead Qualification Approval',
      description: 'Multi-step approval for high-value lead qualification',
      steps: [
        { name: 'Sales Manager Review', roles: ['manager'], required: 1 },
        { name: 'Finance Approval', roles: ['finance'], required: 1 },
        { name: 'Executive Sign-off', roles: ['executive'], required: 1 }
      ]
    },
    {
      name: 'Agent Configuration Change',
      description: 'Approval process for AI agent configuration modifications',
      steps: [
        { name: 'Technical Review', roles: ['manager'], required: 1 },
        { name: 'Security Approval', roles: ['senior_manager', 'legal'], required: 1 }
      ]
    },
    {
      name: 'High-Value Deal Approval',
      description: 'Approval workflow for deals over threshold',
      steps: [
        { name: 'Sales Director', roles: ['senior_manager'], required: 1 },
        { name: 'Finance & Legal Review', roles: ['finance', 'legal'], required: 2, parallel: true },
        { name: 'Executive Approval', roles: ['executive'], required: 1 }
      ]
    }
  ]

  useEffect(() => {
    fetchApprovalProcesses()
    fetchPendingApprovals()
    fetchApprovers()
  }, [])

  const fetchApprovalProcesses = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/workflows?category=approval`)
      const data = await response.json()
      setApprovalProcesses(data.workflows || [])
    } catch (error) {
      console.error('Error fetching approval processes:', error)
    }
  }

  const fetchPendingApprovals = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-execution/executions?status=waiting`)
      const data = await response.json()
      setPendingApprovals(data.executions || [])
    } catch (error) {
      console.error('Error fetching pending approvals:', error)
    }
  }

  const fetchApprovers = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/agents`)
      const data = await response.json()
      setApprovers(data.agents || [])
    } catch (error) {
      console.error('Error fetching approvers:', error)
    }
  }

  const addApprovalStep = () => {
    if (newStep.name && newStep.approver_roles.length > 0) {
      setNewProcess({
        ...newProcess,
        steps: [...newProcess.steps, { ...newStep, id: Date.now().toString() }]
      })
      setNewStep({
        name: '',
        approver_roles: [],
        required_approvals: 1,
        parallel: false
      })
    }
  }

  const removeApprovalStep = (stepId) => {
    setNewProcess({
      ...newProcess,
      steps: newProcess.steps.filter(step => step.id !== stepId)
    })
  }

  const createApprovalProcess = async () => {
    if (!newProcess.name || newProcess.steps.length === 0) return

    setLoading(true)
    try {
      const approvalActions = newProcess.steps.map((step, index) => ({
        id: `approval_step_${index + 1}`,
        type: "approval_request",
        name: step.name,
        parameters: {
          approver_roles: step.approver_roles,
          required_approvals: step.required_approvals,
          parallel: step.parallel,
          step_order: index + 1
        },
        on_success_action_id: index < newProcess.steps.length - 1 ? `approval_step_${index + 2}` : null
      }))

      const workflowData = {
        name: newProcess.name,
        description: newProcess.description,
        status: "active",
        approval_required: true,
        approvers: newProcess.steps.flatMap(step => step.approver_roles),
        approval_timeout_hours: newProcess.timeout_hours,
        trigger: {
          type: "manual",
          name: "Manual Approval Trigger"
        },
        actions: [
          ...approvalActions,
          {
            id: "final_action",
            type: "notification",
            name: "Approval Complete",
            parameters: {
              message: "All approval steps completed successfully",
              type: "success"
            }
          }
        ],
        created_by: "approval_process_builder",
        category: "approval"
      }

      const response = await fetch(`${backendUrl}/api/workflow-engine/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflowData)
      })

      if (response.ok) {
        fetchApprovalProcesses()
        setNewProcess({
          name: '',
          description: '',
          steps: [],
          timeout_hours: 24,
          auto_escalate: true
        })
        alert('Approval process created successfully!')
      }
    } catch (error) {
      console.error('Error creating approval process:', error)
    } finally {
      setLoading(false)
    }
  }

  const approveRequest = async (executionId) => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-execution/executions/${executionId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          approved_by: 'current_user',
          comments: 'Approved via dashboard'
        })
      })
      
      if (response.ok) {
        fetchPendingApprovals()
        alert('Request approved successfully!')
      }
    } catch (error) {
      console.error('Error approving request:', error)
    }
  }

  const rejectRequest = async (executionId) => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-execution/executions/${executionId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          rejected_by: 'current_user',
          comments: 'Rejected via dashboard'
        })
      })
      
      if (response.ok) {
        fetchPendingApprovals()
        alert('Request rejected!')
      }
    } catch (error) {
      console.error('Error rejecting request:', error)
    }
  }

  const useTemplate = (template) => {
    setNewProcess({
      name: template.name,
      description: template.description,
      steps: template.steps.map((step, index) => ({
        id: Date.now().toString() + index,
        name: step.name,
        approver_roles: step.roles,
        required_approvals: step.required,
        parallel: step.parallel || false
      })),
      timeout_hours: 24,
      auto_escalate: true
    })
    setActiveTab('create')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Multi-Step Approval Processes</h2>
          <p className="text-muted-foreground">Create role-based approval workflows with sequential or parallel steps</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Shield className="w-3 h-3" />
            {approvalProcesses.length} Processes
          </Badge>
          <Badge variant="secondary" className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {pendingApprovals.length} Pending
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="processes">Active Processes</TabsTrigger>
          <TabsTrigger value="pending">Pending Approvals</TabsTrigger>
          <TabsTrigger value="create">Create Process</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          <div className="space-y-4">
            {pendingApprovals.map((approval) => (
              <Card key={approval.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">{approval.workflow_name}</CardTitle>
                      <CardDescription>
                        Requested by {approval.triggered_by} • {new Date(approval.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <Badge variant="secondary">
                      <Clock className="w-3 h-3 mr-1" />
                      Pending
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2">Request Details</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span>Status:</span>
                            <Badge variant="outline">{approval.status}</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span>Priority:</span>
                            <Badge variant="outline">Normal</Badge>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">Current Step</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span>Step:</span>
                            <span>{approval.current_step || 1}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Timeout:</span>
                            <span>24 hours</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <Button 
                        onClick={() => approveRequest(approval.id)}
                        variant="default"
                        size="sm"
                      >
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Approve
                      </Button>
                      <Button 
                        onClick={() => rejectRequest(approval.id)}
                        variant="destructive"
                        size="sm"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        Reject
                      </Button>
                      <Button variant="outline" size="sm">
                        <FileText className="w-4 h-4 mr-2" />
                        View Details
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {pendingApprovals.length === 0 && (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No Pending Approvals</h3>
                    <p className="text-muted-foreground">
                      All approval requests are up to date
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="create" className="space-y-6">
          {/* Create New Approval Process */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Create Approval Process
              </CardTitle>
              <CardDescription>
                Design multi-step approval workflows with role-based authorization
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="processName">Process Name</Label>
                  <Input
                    id="processName"
                    placeholder="High-Value Deal Approval"
                    value={newProcess.name}
                    onChange={(e) => setNewProcess({...newProcess, name: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="timeout">Timeout (hours)</Label>
                  <Input
                    id="timeout"
                    type="number"
                    value={newProcess.timeout_hours}
                    onChange={(e) => setNewProcess({...newProcess, timeout_hours: parseInt(e.target.value)})}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="processDescription">Description</Label>
                <Textarea
                  id="processDescription"
                  placeholder="Describe the approval process and when it should be used..."
                  value={newProcess.description}
                  onChange={(e) => setNewProcess({...newProcess, description: e.target.value})}
                />
              </div>

              {/* Add New Step */}
              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">Add Approval Step</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Step Name</Label>
                    <Input
                      placeholder="Manager Review"
                      value={newStep.name}
                      onChange={(e) => setNewStep({...newStep, name: e.target.value})}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Required Approvals</Label>
                    <Input
                      type="number"
                      min="1"
                      value={newStep.required_approvals}
                      onChange={(e) => setNewStep({...newStep, required_approvals: parseInt(e.target.value)})}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Approver Roles</Label>
                    <Select 
                      value={newStep.approver_roles[0] || ''} 
                      onValueChange={(value) => setNewStep({...newStep, approver_roles: [value]})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select role" />
                      </SelectTrigger>
                      <SelectContent>
                        {approverRoles.map((role) => (
                          <SelectItem key={role.id} value={role.id}>
                            {role.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button onClick={addApprovalStep} className="mt-3">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Step
                </Button>
              </div>

              {/* Current Steps */}
              {newProcess.steps.length > 0 && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">Approval Steps ({newProcess.steps.length})</h4>
                  <div className="space-y-3">
                    {newProcess.steps.map((step, index) => (
                      <div key={step.id} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <Badge variant="secondary">{index + 1}</Badge>
                          <div>
                            <div className="font-medium">{step.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {step.approver_roles.join(', ')} • {step.required_approvals} approval(s) required
                            </div>
                          </div>
                          {index < newProcess.steps.length - 1 && (
                            <ArrowDown className="w-4 h-4 text-muted-foreground" />
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeApprovalStep(step.id)}
                        >
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <Button 
                onClick={createApprovalProcess} 
                disabled={loading || !newProcess.name || newProcess.steps.length === 0}
                className="w-full"
              >
                <Play className="w-4 h-4 mr-2" />
                Create Approval Process
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="processes" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {approvalProcesses.map((process) => (
              <Card key={process.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{process.name}</CardTitle>
                    <Badge variant={process.status === 'active' ? 'default' : 'secondary'}>
                      {process.status}
                    </Badge>
                  </div>
                  <CardDescription>{process.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span>Steps:</span>
                      <Badge variant="outline">{process.actions?.length || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Approvers:</span>
                      <Badge variant="outline">{process.approvers?.length || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Timeout:</span>
                      <span>{process.approval_timeout_hours || 24}h</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Executions:</span>
                      <Badge variant="outline">{process.execution_count || 0}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {processTemplates.map((template, index) => (
              <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="text-base">{template.name}</CardTitle>
                  <CardDescription>{template.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm">
                      <div className="font-medium mb-2">{template.steps.length} Steps:</div>
                      {template.steps.map((step, stepIndex) => (
                        <div key={stepIndex} className="flex items-center gap-2 text-xs">
                          <Badge variant="outline" className="text-xs">{stepIndex + 1}</Badge>
                          <span>{step.name}</span>
                        </div>
                      ))}
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => useTemplate(template)}
                    >
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}