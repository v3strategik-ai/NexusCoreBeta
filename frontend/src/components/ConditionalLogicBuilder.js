import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
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
  Plus, 
  Trash2, 
  Play, 
  Settings, 
  Code, 
  Workflow,
  TestTube,
  CheckCircle,
  XCircle,
  GitBranch,
  Zap
} from 'lucide-react'

export function ConditionalLogicBuilder() {
  const [conditions, setConditions] = useState([])
  const [operators, setOperators] = useState([])
  const [dataTypes, setDataTypes] = useState([])
  const [workflows, setWorkflows] = useState([])
  const [loading, setLoading] = useState(false)
  const [newCondition, setNewCondition] = useState({
    field: '',
    operator: '',
    value: '',
    data_type: 'string'
  })
  const [testResult, setTestResult] = useState(null)
  const [activeTab, setActiveTab] = useState('builder')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  useEffect(() => {
    fetchOperators()
    fetchWorkflows()
  }, [])

  const fetchOperators = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/conditions/operators`)
      const data = await response.json()
      setOperators(data.operators || [])
      setDataTypes(data.data_types || [])
    } catch (error) {
      console.error('Error fetching operators:', error)
    }
  }

  const fetchWorkflows = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/workflows`)
      const data = await response.json()
      setWorkflows(data.workflows || [])
    } catch (error) {
      console.error('Error fetching workflows:', error)
    }
  }

  const addCondition = () => {
    if (newCondition.field && newCondition.operator && newCondition.value) {
      const condition = {
        id: Date.now().toString(),
        ...newCondition
      }
      setConditions([...conditions, condition])
      setNewCondition({
        field: '',
        operator: '',
        value: '',
        data_type: 'string'
      })
    }
  }

  const removeCondition = (id) => {
    setConditions(conditions.filter(c => c.id !== id))
  }

  const testConditions = async () => {
    if (conditions.length === 0) return

    setLoading(true)
    const results = []

    try {
      for (const condition of conditions) {
        const testData = {
          condition: {
            field: condition.field,
            operator: condition.operator,
            value: condition.value,
            data_type: condition.data_type
          },
          context_data: {
            lead: { score: 85, status: "hot", value: 50000 },
            agent: { performance: 92, availability: true },
            activity: { count: 15, last_contact: "2024-01-15" }
          }
        }

        const response = await fetch(`${backendUrl}/api/workflow-engine/conditions/test`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(testData)
        })

        const result = await response.json()
        results.push({
          condition: condition,
          result: result.condition_result,
          field_value: result.field_value,
          details: result
        })
      }

      setTestResult(results)
    } catch (error) {
      console.error('Error testing conditions:', error)
    } finally {
      setLoading(false)
    }
  }

  const createWorkflow = async () => {
    if (conditions.length === 0) return

    setLoading(true)
    try {
      const workflowData = {
        name: `Conditional Workflow ${Date.now()}`,
        description: "Workflow with conditional logic",
        status: "active",
        trigger: {
          type: "condition_based",
          name: "Multi-Condition Trigger",
          conditions: conditions.map(c => ({
            field: c.field,
            operator: c.operator,
            value: c.value,
            data_type: c.data_type
          }))
        },
        actions: [
          {
            type: "notification",
            name: "Conditional Action",
            parameters: {
              message: "Conditions met: {{trigger.details}}",
              type: "success"
            }
          }
        ],
        created_by: "conditional_logic_builder",
        category: "automation"
      }

      const response = await fetch(`${backendUrl}/api/workflow-engine/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflowData)
      })

      if (response.ok) {
        fetchWorkflows()
        setConditions([])
        alert('Workflow created successfully!')
      }
    } catch (error) {
      console.error('Error creating workflow:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Conditional Logic Builder</h2>
          <p className="text-muted-foreground">Create complex conditional workflows with visual logic</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <GitBranch className="w-3 h-3" />
            {conditions.length} Conditions
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Workflow className="w-3 h-3" />
            {workflows.length} Workflows
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="builder">Condition Builder</TabsTrigger>
          <TabsTrigger value="workflows">Active Workflows</TabsTrigger>
          <TabsTrigger value="testing">Testing Lab</TabsTrigger>
        </TabsList>

        <TabsContent value="builder" className="space-y-6">
          {/* New Condition Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="w-5 h-5" />
                Add New Condition
              </CardTitle>
              <CardDescription>
                Define when this condition should trigger based on data fields and values
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="field">Field Path</Label>
                  <Input
                    id="field"
                    placeholder="lead.score"
                    value={newCondition.field}
                    onChange={(e) => setNewCondition({...newCondition, field: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Operator</Label>
                  <Select value={newCondition.operator} onValueChange={(value) => setNewCondition({...newCondition, operator: value})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select operator" />
                    </SelectTrigger>
                    <SelectContent>
                      {(operators || []).filter(op => op && typeof op === 'string').map((op) => (
                        <SelectItem key={op} value={op}>
                          {op.replace(/_/g, ' ').toUpperCase()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="value">Value</Label>
                  <Input
                    id="value"
                    placeholder="75"
                    value={newCondition.value}
                    onChange={(e) => setNewCondition({...newCondition, value: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Data Type</Label>
                  <Select value={newCondition.data_type} onValueChange={(value) => setNewCondition({...newCondition, data_type: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {dataTypes.map((type) => (
                        <SelectItem key={type} value={type}>
                          {(type || '').charAt(0).toUpperCase() + (type || '').slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button onClick={addCondition} className="w-full">
                <Plus className="w-4 h-4 mr-2" />
                Add Condition
              </Button>
            </CardContent>
          </Card>

          {/* Current Conditions */}
          {conditions.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="w-5 h-5" />
                  Current Conditions ({conditions.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {conditions.map((condition, index) => (
                    <div key={condition.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Badge variant="secondary">{index + 1}</Badge>
                        <code className="text-sm bg-muted px-2 py-1 rounded">
                          {condition.field} {(condition.operator || '').replace(/_/g, ' ')} {condition.value}
                        </code>
                        <Badge variant="outline">{condition.data_type}</Badge>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeCondition(condition.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>

                <div className="flex gap-3 mt-4">
                  <Button onClick={testConditions} disabled={loading} variant="outline">
                    <TestTube className="w-4 h-4 mr-2" />
                    Test Conditions
                  </Button>
                  <Button onClick={createWorkflow} disabled={loading}>
                    <Zap className="w-4 h-4 mr-2" />
                    Create Workflow
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="workflows" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workflows.map((workflow) => (
              <Card key={workflow.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{workflow.name}</CardTitle>
                    <Badge variant={workflow.status === 'active' ? 'default' : 'secondary'}>
                      {workflow.status}
                    </Badge>
                  </div>
                  <CardDescription>{workflow.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span>Actions:</span>
                      <Badge variant="outline">{workflow.actions?.length || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Conditions:</span>
                      <Badge variant="outline">{workflow.trigger?.conditions?.length || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Executions:</span>
                      <Badge variant="outline">{workflow.execution_count || 0}</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="testing" className="space-y-4">
          {testResult && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Test Results</h3>
              {testResult.map((result, index) => (
                <Card key={index}>
                  <CardContent className="pt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {result.result ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-500" />
                        )}
                        <code className="text-sm">
                          {result.condition.field} {(result.condition.operator || '').replace(/_/g, ' ')} {result.condition.value}
                        </code>
                      </div>
                      <div className="text-right">
                        <Badge variant={result.result ? 'default' : 'secondary'}>
                          {result.result ? 'PASS' : 'FAIL'}
                        </Badge>
                        <p className="text-xs text-muted-foreground mt-1">
                          Field Value: {result.field_value}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {!testResult && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <TestTube className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Test Results</h3>
                  <p className="text-muted-foreground">
                    Add conditions and run tests to see results here
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}