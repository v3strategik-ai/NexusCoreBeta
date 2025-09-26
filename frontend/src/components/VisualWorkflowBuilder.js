import { useState, useCallback, useRef, useEffect } from 'react'
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState, 
  addEdge,
  MarkerType,
  Panel
} from 'reactflow'
import 'reactflow/dist/style.css'

import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Switch } from './ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from './ui/dialog'
import { 
  Play,
  Save,
  Download,
  Upload,
  Zap,
  Mail,
  FileText,
  Users,
  Clock,
  GitBranch,
  Settings,
  Plus,
  Trash2,
  Copy,
  Eye,
  RefreshCw,
  CheckCircle,
  AlertTriangle
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

// Custom node types
const nodeTypes = {
  trigger: TriggerNode,
  action: ActionNode,
  condition: ConditionNode,
  delay: DelayNode
}

// Node Components
function TriggerNode({ data, selected }) {
  return (
    <div className={`px-4 py-2 shadow-md rounded-md bg-gradient-to-r from-blue-500 to-cyan-500 border-2 ${selected ? 'border-white' : 'border-blue-600'} text-white min-w-[150px]`}>
      <div className="flex items-center gap-2">
        <Zap className="w-4 h-4" />
        <div className="font-bold">{data.label}</div>
      </div>
      <div className="text-xs opacity-90 mt-1">{data.trigger_type || 'Manual'}</div>
    </div>
  )
}

function ActionNode({ data, selected }) {
  const getActionIcon = (actionType) => {
    switch (actionType) {
      case 'send_email': return <Mail className="w-4 h-4" />
      case 'create_document': return <FileText className="w-4 h-4" />
      case 'update_lead': return <Users className="w-4 h-4" />
      case 'assign_agent': return <Users className="w-4 h-4" />
      default: return <Settings className="w-4 h-4" />
    }
  }

  return (
    <div className={`px-4 py-2 shadow-md rounded-md bg-gradient-to-r from-green-500 to-emerald-500 border-2 ${selected ? 'border-white' : 'border-green-600'} text-white min-w-[150px]`}>
      <div className="flex items-center gap-2">
        {getActionIcon(data.action_type)}
        <div className="font-bold">{data.label}</div>
      </div>
      <div className="text-xs opacity-90 mt-1">{(data.action_type || '').replace('_', ' ') || 'Action'}</div>
    </div>
  )
}

function ConditionNode({ data, selected }) {
  return (
    <div className={`px-4 py-2 shadow-md rounded-md bg-gradient-to-r from-yellow-500 to-orange-500 border-2 ${selected ? 'border-white' : 'border-yellow-600'} text-white min-w-[150px]`}>
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4" />
        <div className="font-bold">{data.label}</div>
      </div>
      <div className="text-xs opacity-90 mt-1">If/Then Logic</div>
    </div>
  )
}

function DelayNode({ data, selected }) {
  return (
    <div className={`px-4 py-2 shadow-md rounded-md bg-gradient-to-r from-purple-500 to-pink-500 border-2 ${selected ? 'border-white' : 'border-purple-600'} text-white min-w-[150px]`}>
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4" />
        <div className="font-bold">{data.label}</div>
      </div>
      <div className="text-xs opacity-90 mt-1">
        {data.delay_hours ? `${data.delay_hours}h` : data.delay_minutes ? `${data.delay_minutes}m` : 'Delay'}
      </div>
    </div>
  )
}

export function VisualWorkflowBuilder({ children, onWorkflowCreated }) {
  const [isOpen, setIsOpen] = useState(false)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [executionResults, setExecutionResults] = useState(null)
  
  const [workflowInfo, setWorkflowInfo] = useState({
    name: '',
    description: '',
    status: 'draft'
  })
  
  const [nodeConfig, setNodeConfig] = useState({
    label: '',
    type: 'action',
    trigger_type: 'manual',
    action_type: 'send_email',
    condition: {},
    parameters: {},
    delay_hours: 0,
    delay_minutes: 0
  })

  const [templates, setTemplates] = useState([])
  const [showTemplates, setShowTemplates] = useState(false)
  
  const reactFlowWrapper = useRef(null)
  const reactFlowInstance = useRef(null)

  useEffect(() => {
    if (isOpen) {
      loadWorkflowTemplates()
    }
  }, [isOpen])

  const loadWorkflowTemplates = async () => {
    try {
      const response = await axios.get(`${API}/workflows/advanced/templates/list`)
      setTemplates(response.data.templates || [])
    } catch (error) {
      console.error('Error loading workflow templates:', error)
    }
  }

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({
      ...params,
      type: 'smoothstep',
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed }
    }, eds)),
    [setEdges]
  )

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node)
    setNodeConfig({
      label: node.data.label || '',
      type: node.type || 'action',
      trigger_type: node.data.trigger_type || 'manual',
      action_type: node.data.action_type || 'send_email',
      condition: node.data.condition || {},
      parameters: node.data.parameters || {},
      delay_hours: node.data.delay_hours || 0,
      delay_minutes: node.data.delay_minutes || 0
    })
  }, [])

  const addNode = (type) => {
    const newNode = {
      id: `${type}_${Date.now()}`,
      type,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
      data: {
        label: `New ${type.charAt(0).toUpperCase() + type.slice(1)}`,
        ...(type === 'trigger' && { trigger_type: 'manual' }),
        ...(type === 'action' && { action_type: 'send_email' }),
        ...(type === 'delay' && { delay_hours: 1 })
      }
    }
    
    setNodes((nds) => nds.concat(newNode))
  }

  const updateSelectedNode = () => {
    if (!selectedNode) return

    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === selectedNode.id) {
          return {
            ...node,
            data: {
              ...node.data,
              label: nodeConfig.label,
              trigger_type: nodeConfig.trigger_type,
              action_type: nodeConfig.action_type,
              condition: nodeConfig.condition,
              parameters: nodeConfig.parameters,
              delay_hours: nodeConfig.delay_hours,
              delay_minutes: nodeConfig.delay_minutes
            }
          }
        }
        return node
      })
    )

    setSelectedNode(null)
  }

  const deleteSelectedNode = () => {
    if (!selectedNode) return

    setNodes((nds) => nds.filter((node) => node.id !== selectedNode.id))
    setEdges((eds) => eds.filter((edge) => 
      edge.source !== selectedNode.id && edge.target !== selectedNode.id
    ))
    setSelectedNode(null)
  }

  const saveWorkflow = async () => {
    if (!workflowInfo.name.trim()) {
      alert('Please enter a workflow name')
      return
    }

    if (nodes.length === 0) {
      alert('Please add at least one node to the workflow')
      return
    }

    setIsSaving(true)

    try {
      const workflowData = {
        name: workflowInfo.name,
        description: workflowInfo.description,
        status: workflowInfo.status,
        nodes: nodes.map(node => ({
          id: node.id,
          type: node.type,
          label: node.data.label,
          position: node.position,
          data: node.data
        })),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type || 'default',
          label: edge.label,
          data: edge.data || {}
        })),
        variables: {},
        tags: ['visual_builder', 'custom']
      }

      const response = await axios.post(`${API}/workflows/advanced/create`, workflowData)
      
      console.log('Workflow saved:', response.data)
      alert(`Workflow "${workflowInfo.name}" saved successfully!`)
      
      if (onWorkflowCreated) {
        onWorkflowCreated(response.data)
      }

      // Reset form
      setWorkflowInfo({ name: '', description: '', status: 'draft' })
      setNodes([])
      setEdges([])
      setSelectedNode(null)
      setIsOpen(false)

    } catch (error) {
      console.error('Error saving workflow:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to save workflow. Please try again.'
      alert(errorMessage)
    } finally {
      setIsSaving(false)
    }
  }

  const executeWorkflow = async () => {
    if (nodes.length === 0) {
      alert('No workflow to execute')
      return
    }

    // First save the workflow temporarily
    const tempWorkflowData = {
      name: workflowInfo.name || `Temp_${Date.now()}`,
      description: workflowInfo.description || 'Temporary workflow for testing',
      status: 'active',
      nodes: nodes.map(node => ({
        id: node.id,
        type: node.type,
        label: node.data.label,
        position: node.position,
        data: node.data
      })),
      edges: edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type || 'default',
        label: edge.label,
        data: edge.data || {}
      })),
      variables: { test_execution: true },
      tags: ['test', 'visual_builder']
    }

    setIsExecuting(true)

    try {
      // Create temporary workflow
      const createResponse = await axios.post(`${API}/workflows/advanced/create`, tempWorkflowData)
      const workflowId = createResponse.data.id

      // Execute the workflow
      const executeResponse = await axios.post(`${API}/workflows/advanced/${workflowId}/execute`, {
        type: 'manual',
        test_mode: true
      })

      setExecutionResults(executeResponse.data)
      alert('Workflow executed successfully! Check the execution results.')

    } catch (error) {
      console.error('Error executing workflow:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to execute workflow. Please try again.'
      alert(errorMessage)
    } finally {
      setIsExecuting(false)
    }
  }

  const loadFromTemplate = async (templateId) => {
    try {
      const response = await axios.post(`${API}/workflows/advanced/templates/${templateId}/create`, 
        `workflow_name=Template_${Date.now()}`, 
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      )

      const workflow = response.data
      
      // Load nodes and edges from template
      setNodes(workflow.nodes || [])
      setEdges(workflow.edges || [])
      setWorkflowInfo({
        name: workflow.name,
        description: workflow.description,
        status: workflow.status
      })

      setShowTemplates(false)
      alert('Template loaded successfully!')

    } catch (error) {
      console.error('Error loading template:', error)
      alert('Failed to load template. Please try again.')
    }
  }

  const clearWorkflow = () => {
    if (window.confirm('Are you sure you want to clear the workflow? This cannot be undone.')) {
      setNodes([])
      setEdges([])
      setSelectedNode(null)
      setWorkflowInfo({ name: '', description: '', status: 'draft' })
      setExecutionResults(null)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent 
        className="sm:max-w-7xl w-[95vw] h-[85vh] flex flex-col quantum-bg border border-primary/20 shadow-2xl"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          maxHeight: '90vh'
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-3">
            <GitBranch className="w-6 h-6 text-primary" />
            <div>
              <span className="gradient-text">Visual Workflow Builder</span>
              <div className="text-sm text-muted-foreground font-normal mt-1">
                Design automated workflows with drag-and-drop interface
              </div>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 flex gap-4 min-h-0">
          {/* Workflow Canvas */}
          <div className="flex-1 border border-border rounded-lg overflow-hidden">
            <div className="h-full" ref={reactFlowWrapper}>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                nodeTypes={nodeTypes}
                onInit={(instance) => (reactFlowInstance.current = instance)}
                className="bg-gray-50 dark:bg-gray-900"
                fitView
              >
                <Controls />
                <MiniMap />
                <Background variant="dots" gap={12} size={1} />
                
                {/* Toolbar Panel */}
                <Panel position="top-left" className="flex gap-2">
                  <Button size="sm" onClick={() => addNode('trigger')} className="bg-blue-500 hover:bg-blue-600">
                    <Zap className="w-4 h-4 mr-1" />
                    Trigger
                  </Button>
                  <Button size="sm" onClick={() => addNode('action')} className="bg-green-500 hover:bg-green-600">
                    <Settings className="w-4 h-4 mr-1" />
                    Action
                  </Button>
                  <Button size="sm" onClick={() => addNode('condition')} className="bg-yellow-500 hover:bg-yellow-600">
                    <GitBranch className="w-4 h-4 mr-1" />
                    Condition
                  </Button>
                  <Button size="sm" onClick={() => addNode('delay')} className="bg-purple-500 hover:bg-purple-600">
                    <Clock className="w-4 h-4 mr-1" />
                    Delay
                  </Button>
                </Panel>

                {/* Status Panel */}
                <Panel position="top-right" className="flex gap-2">
                  <Badge variant="outline">
                    {nodes.length} nodes, {edges.length} connections
                  </Badge>
                  {executionResults && (
                    <Badge variant={executionResults.status === 'completed' ? 'default' : 'destructive'}>
                      {executionResults.status}
                    </Badge>
                  )}
                </Panel>
              </ReactFlow>
            </div>
          </div>

          {/* Configuration Panel */}
          <div className="w-80 space-y-4 overflow-y-auto">
            <Tabs defaultValue="workflow">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="workflow">Workflow</TabsTrigger>
                <TabsTrigger value="node">Node Config</TabsTrigger>
              </TabsList>

              {/* Workflow Configuration */}
              <TabsContent value="workflow" className="space-y-4">
                <Card className="quantum-bg">
                  <CardHeader>
                    <CardTitle className="text-lg">Workflow Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="workflow-name">Workflow Name</Label>
                      <Input
                        id="workflow-name"
                        value={workflowInfo.name}
                        onChange={(e) => setWorkflowInfo(prev => ({...prev, name: e.target.value}))}
                        placeholder="Enter workflow name"
                      />
                    </div>

                    <div>
                      <Label htmlFor="workflow-description">Description</Label>
                      <Textarea
                        id="workflow-description"
                        value={workflowInfo.description}
                        onChange={(e) => setWorkflowInfo(prev => ({...prev, description: e.target.value}))}
                        placeholder="Describe what this workflow does"
                        rows={3}
                      />
                    </div>

                    <div>
                      <Label htmlFor="workflow-status">Status</Label>
                      <Select value={workflowInfo.status} onValueChange={(value) => setWorkflowInfo(prev => ({...prev, status: value}))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="draft">Draft</SelectItem>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="paused">Paused</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex gap-2">
                      <Button onClick={() => setShowTemplates(true)} variant="outline" size="sm" className="flex-1">
                        <Upload className="w-4 h-4 mr-1" />
                        Templates
                      </Button>
                      <Button onClick={clearWorkflow} variant="outline" size="sm" className="flex-1">
                        <Trash2 className="w-4 h-4 mr-1" />
                        Clear
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {executionResults && (
                  <Card className="quantum-bg">
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        {executionResults.status === 'completed' ? 
                          <CheckCircle className="w-5 h-5 text-green-400" /> :
                          <AlertTriangle className="w-5 h-5 text-red-400" />
                        }
                        Execution Results
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm space-y-2">
                        <div><strong>Status:</strong> {executionResults.status}</div>
                        <div><strong>Execution ID:</strong> {executionResults.execution_id}</div>
                        {executionResults.execution?.duration_seconds && (
                          <div><strong>Duration:</strong> {executionResults.execution.duration_seconds}s</div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              {/* Node Configuration */}
              <TabsContent value="node" className="space-y-4">
                {selectedNode ? (
                  <Card className="quantum-bg">
                    <CardHeader>
                      <CardTitle className="text-lg">Configure Node</CardTitle>
                      <CardDescription>{selectedNode.type} node settings</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <Label htmlFor="node-label">Label</Label>
                        <Input
                          id="node-label"
                          value={nodeConfig.label}
                          onChange={(e) => setNodeConfig(prev => ({...prev, label: e.target.value}))}
                          placeholder="Node label"
                        />
                      </div>

                      {selectedNode.type === 'trigger' && (
                        <div>
                          <Label htmlFor="trigger-type">Trigger Type</Label>
                          <Select value={nodeConfig.trigger_type} onValueChange={(value) => setNodeConfig(prev => ({...prev, trigger_type: value}))}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="manual">Manual</SelectItem>
                              <SelectItem value="lead_status_change">Lead Status Change</SelectItem>
                              <SelectItem value="time_based">Time Based</SelectItem>
                              <SelectItem value="document_generated">Document Generated</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      {selectedNode.type === 'action' && (
                        <div>
                          <Label htmlFor="action-type">Action Type</Label>
                          <Select value={nodeConfig.action_type} onValueChange={(value) => setNodeConfig(prev => ({...prev, action_type: value}))}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="send_email">Send Email</SelectItem>
                              <SelectItem value="create_document">Create Document</SelectItem>
                              <SelectItem value="update_lead">Update Lead</SelectItem>
                              <SelectItem value="assign_agent">Assign Agent</SelectItem>
                              <SelectItem value="send_notification">Send Notification</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      )}

                      {selectedNode.type === 'delay' && (
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <Label htmlFor="delay-hours">Hours</Label>
                            <Input
                              id="delay-hours"
                              type="number"
                              value={nodeConfig.delay_hours}
                              onChange={(e) => setNodeConfig(prev => ({...prev, delay_hours: parseInt(e.target.value) || 0}))}
                              min="0"
                              max="168"
                            />
                          </div>
                          <div>
                            <Label htmlFor="delay-minutes">Minutes</Label>
                            <Input
                              id="delay-minutes"
                              type="number"
                              value={nodeConfig.delay_minutes}
                              onChange={(e) => setNodeConfig(prev => ({...prev, delay_minutes: parseInt(e.target.value) || 0}))}
                              min="0"
                              max="59"
                            />
                          </div>
                        </div>
                      )}

                      <div className="flex gap-2">
                        <Button onClick={updateSelectedNode} size="sm" className="flex-1">
                          <Save className="w-4 h-4 mr-1" />
                          Update
                        </Button>
                        <Button onClick={deleteSelectedNode} variant="destructive" size="sm" className="flex-1">
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <Card className="quantum-bg">
                    <CardContent className="text-center py-8">
                      <Eye className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                      <p className="text-muted-foreground">Select a node to configure</p>
                    </CardContent>
                  </Card>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-between items-center pt-4 border-t border-border flex-shrink-0">
          <div className="flex gap-2">
            <Button variant="outline" onClick={executeWorkflow} disabled={isExecuting || nodes.length === 0}>
              {isExecuting ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Test Run
                </>
              )}
            </Button>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={saveWorkflow} disabled={isSaving || !workflowInfo.name.trim()}>
              {isSaving ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Save Workflow
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Templates Dialog */}
        <Dialog open={showTemplates} onOpenChange={setShowTemplates}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Workflow Templates</DialogTitle>
              <DialogDescription>Choose a template to get started quickly</DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
              {templates.map((template) => (
                <Card key={template.id} className="cursor-pointer hover:border-primary/50 transition-colors" onClick={() => loadFromTemplate(template.id)}>
                  <CardHeader>
                    <CardTitle className="text-base">{template.name}</CardTitle>
                    <CardDescription>{template.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-between items-center text-sm">
                      <Badge variant="outline">{template.category}</Badge>
                      <span className="text-muted-foreground">{template.complexity}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </DialogContent>
    </Dialog>
  )
}