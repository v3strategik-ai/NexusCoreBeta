import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Badge } from './ui/badge'
import { Textarea } from './ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Progress } from './ui/progress'
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog'
import { 
  Brain, 
  Sparkles, 
  MessageSquare, 
  Wand2, 
  CheckCircle, 
  AlertTriangle,
  Lightbulb,
  Plus,
  Play,
  Edit,
  Trash2,
  Code,
  Zap,
  FileText,
  Bot
} from 'lucide-react'

export function NaturalLanguageWorkflows() {
  const [workflows, setWorkflows] = useState([])
  const [templates, setTemplates] = useState([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [nlRequest, setNlRequest] = useState({
    description: '',
    context: '',
    creator_id: 'nl_builder_user'
  })
  const [generationResult, setGenerationResult] = useState(null)
  const [activeTab, setActiveTab] = useState('create')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  const examplePrompts = [
    {
      title: "Lead Follow-up Automation",
      description: "When a new lead is created, wait 2 hours then send a follow-up email, and if no response after 24 hours, assign to a senior sales agent",
      context: "High-priority lead management process"
    },
    {
      title: "Document Approval Process",
      description: "When a document is generated, send it for manager approval, if approved send to client, if rejected send back to agent for revision",
      context: "Client document workflow with approval gates"
    },
    {
      title: "Performance Monitoring",
      description: "Every morning at 9 AM, check if any agents have performance below 80%, send notification to manager and create improvement task",
      context: "Daily performance monitoring and management"
    },
    {
      title: "Escalation Workflow", 
      description: "When a lead score exceeds 90, immediately assign to top performer agent and notify sales manager, create priority task",
      context: "High-value lead escalation process"
    }
  ]

  const workflowSuggestions = [
    "Automatically follow up with leads who haven't responded in 3 days",
    "Send weekly performance reports to managers every Friday at 5 PM",
    "When a deal is closed, update CRM and send celebration notification to team",
    "If an agent is inactive for 30 minutes during business hours, send reminder",
    "Escalate leads with budget over $50,000 to senior sales director"
  ]

  useEffect(() => {
    fetchWorkflows()
    fetchTemplates()
  }, [])

  const fetchWorkflows = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/nl-workflows/workflows`)
      const data = await response.json()
      setWorkflows(data.workflows || [])
    } catch (error) {
      console.error('Error fetching workflows:', error)
    }
  }

  const fetchTemplates = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/nl-workflows/templates`)
      const data = await response.json()
      setTemplates(data.templates || [])
    } catch (error) {
      console.error('Error fetching templates:', error)
    }
  }

  const generateWorkflow = async () => {
    if (!nlRequest.description.trim()) return

    setGenerating(true)
    setGenerationResult(null)

    try {
      const response = await fetch(`${backendUrl}/api/nl-workflows/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nlRequest)
      })

      if (response.ok) {
        const result = await response.json()
        setGenerationResult(result)
        
        // Clear the form after successful generation
        setNlRequest({
          description: '',
          context: '',
          creator_id: 'nl_builder_user'
        })
      } else {
        const error = await response.json()
        alert(`Error generating workflow: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error generating workflow:', error)
      alert('Failed to generate workflow. Please try again.')
    } finally {
      setGenerating(false)
    }
  }

  const deployWorkflow = async (workflow) => {
    setLoading(true)
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/workflows`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...workflow,
          status: 'active',
          created_by: 'nl_workflow_generator'
        })
      })

      if (response.ok) {
        fetchWorkflows()
        setGenerationResult(null)
        alert('Workflow deployed successfully!')
      } else {
        alert('Failed to deploy workflow')
      }
    } catch (error) {
      console.error('Error deploying workflow:', error)
      alert('Failed to deploy workflow')
    } finally {
      setLoading(false)
    }
  }

  const useExample = (example) => {
    setNlRequest({
      description: example.description,
      context: example.context,
      creator_id: 'nl_builder_user'
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Natural Language Workflows</h2>
          <p className="text-muted-foreground">Create sophisticated workflows using simple English descriptions</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Brain className="w-3 h-3" />
            AI-Powered
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Zap className="w-3 h-3" />
            {workflows.length} Generated
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="create">Create Workflow</TabsTrigger>
          <TabsTrigger value="generated">Generated Workflows</TabsTrigger>
          <TabsTrigger value="templates">AI Templates</TabsTrigger>
          <TabsTrigger value="examples">Examples</TabsTrigger>
        </TabsList>

        <TabsContent value="create" className="space-y-6">
          {/* AI Workflow Generator */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                AI Workflow Generator
              </CardTitle>
              <CardDescription>
                Describe your workflow in plain English and let AI create the automation for you
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="description">Workflow Description *</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what you want the workflow to do..."
                  value={nlRequest.description}
                  onChange={(e) => setNlRequest({...nlRequest, description: e.target.value})}
                  className="min-h-[120px]"
                />
                <p className="text-xs text-muted-foreground">
                  Be specific about triggers, conditions, and actions. Example: "When a lead score exceeds 80, assign to senior agent and send email notification"
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="context">Additional Context (Optional)</Label>
                <Textarea
                  id="context"
                  placeholder="Provide additional context or requirements..."
                  value={nlRequest.context}
                  onChange={(e) => setNlRequest({...nlRequest, context: e.target.value})}
                  className="min-h-[80px]"
                />
              </div>

              <div className="flex gap-3">
                <Button 
                  onClick={generateWorkflow} 
                  disabled={generating || !nlRequest.description.trim()}
                  className="flex-1"
                >
                  {generating ? (
                    <>
                      <Bot className="w-4 h-4 mr-2 animate-pulse" />
                      AI Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Workflow
                    </>
                  )}
                </Button>
              </div>

              {generating && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 animate-pulse" />
                    <span className="text-sm">AI is analyzing your request...</span>
                  </div>
                  <Progress value={65} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Suggestions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5" />
                Quick Suggestions
              </CardTitle>
              <CardDescription>
                Click on any suggestion to get started quickly
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {workflowSuggestions.map((suggestion, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="h-auto p-3 text-left justify-start"
                    onClick={() => setNlRequest({...nlRequest, description: suggestion})}
                  >
                    <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                    <span className="text-sm">{suggestion}</span>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Generation Result */}
          {generationResult && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  Generated Workflow
                </CardTitle>
                <CardDescription>
                  AI has created a workflow based on your description
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Confidence Score</div>
                    <div className="flex items-center gap-2">
                      <Progress value={generationResult.confidence * 100} className="flex-1" />
                      <span className="text-sm">{Math.round(generationResult.confidence * 100)}%</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Actions</div>
                    <Badge variant="outline">{generationResult.workflow.actions?.length || 0} Steps</Badge>
                  </div>
                  <div className="space-y-2">
                    <div className="text-sm font-medium">Trigger Type</div>
                    <Badge variant="outline">{generationResult.workflow.trigger?.type || 'Unknown'}</Badge>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <h4 className="font-medium mb-2">Workflow Details</h4>
                    <div className="bg-muted p-3 rounded-lg">
                      <div className="font-medium">{generationResult.workflow.name}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {generationResult.workflow.description}
                      </div>
                    </div>
                  </div>

                  {generationResult.suggestions && generationResult.suggestions.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">AI Suggestions</h4>
                      <div className="space-y-2">
                        {generationResult.suggestions.map((suggestion, index) => (
                          <div key={index} className="flex items-start gap-2 text-sm">
                            <Lightbulb className="w-4 h-4 mt-0.5 text-yellow-500 flex-shrink-0" />
                            <span>{suggestion}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {generationResult.warnings && generationResult.warnings.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-2">Warnings</h4>
                      <div className="space-y-2">
                        {generationResult.warnings.map((warning, index) => (
                          <div key={index} className="flex items-start gap-2 text-sm">
                            <AlertTriangle className="w-4 h-4 mt-0.5 text-yellow-500 flex-shrink-0" />
                            <span>{warning}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-3 border-t">
                  <Button 
                    onClick={() => deployWorkflow(generationResult.workflow)}
                    disabled={loading}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Deploy Workflow
                  </Button>
                  <Button variant="outline" disabled={loading}>
                    <Edit className="w-4 h-4 mr-2" />
                    Edit & Customize
                  </Button>
                  <Button variant="outline" onClick={() => setGenerationResult(null)}>
                    <Trash2 className="w-4 h-4 mr-2" />
                    Discard
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="generated" className="space-y-4">
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
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span>Generated:</span>
                      <span>{new Date(workflow.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Actions:</span>
                      <Badge variant="outline">{workflow.actions?.length || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Executions:</span>
                      <Badge variant="outline">{workflow.execution_count || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span>Success Rate:</span>
                      <Badge variant="outline">
                        {workflow.execution_count > 0 
                          ? Math.round((workflow.success_count / workflow.execution_count) * 100)
                          : 0}%
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {workflows.length === 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Bot className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Generated Workflows</h3>
                  <p className="text-muted-foreground mb-4">
                    Create your first AI-generated workflow to see it here
                  </p>
                  <Button onClick={() => setActiveTab('create')}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Workflow
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((template) => (
              <Card key={template.name} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="text-base">{template.name}</CardTitle>
                  <CardDescription>{template.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span>Difficulty:</span>
                      <Badge variant={template.difficulty === 'easy' ? 'default' : 
                                   template.difficulty === 'medium' ? 'secondary' : 'destructive'}>
                        {template.difficulty}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Use Cases: {template.use_cases?.join(', ') || 'General automation'}
                    </div>
                    <Button variant="outline" size="sm" className="w-full">
                      <Wand2 className="w-4 h-4 mr-2" />
                      Use Template
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="examples" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {examplePrompts.map((example, index) => (
              <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="text-base">{example.title}</CardTitle>
                  <CardDescription>{example.context}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm bg-muted p-3 rounded-lg">
                      "{example.description}"
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => useExample(example)}
                    >
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Use This Example
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Tips for Writing Effective Descriptions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                  <span>Be specific about triggers: "When lead score > 80" instead of "for good leads"</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                  <span>Include timing: "wait 2 hours", "every Monday at 9 AM", "after 24 hours"</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                  <span>Specify conditions: "if no response", "when approved", "unless already assigned"</span>
                </div>
                <div className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                  <span>Define actions clearly: "send email to manager", "create task", "update lead status"</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}