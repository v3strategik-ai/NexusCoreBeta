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
  Webhook, 
  Globe, 
  Send, 
  Key, 
  Database, 
  Zap,
  Plus,
  Trash2,
  TestTube,
  CheckCircle,
  XCircle,
  Settings,
  Link,
  Code,
  Activity
} from 'lucide-react'

export function WebhookApiAutomation() {
  const [webhooks, setWebhooks] = useState([])
  const [apiConnections, setApiConnections] = useState([])
  const [loading, setLoading] = useState(false)
  const [newWebhook, setNewWebhook] = useState({
    name: '',
    url: '',
    method: 'POST',
    headers: {},
    secret: '',
    events: []
  })
  const [newApiConnection, setNewApiConnection] = useState({
    name: '',
    base_url: '',
    auth_type: 'api_key',
    api_key: '',
    headers: {}
  })
  const [testResult, setTestResult] = useState(null)
  const [activeTab, setActiveTab] = useState('webhooks')

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL

  const httpMethods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
  const authTypes = [
    { value: 'api_key', label: 'API Key' },
    { value: 'bearer_token', label: 'Bearer Token' },
    { value: 'basic_auth', label: 'Basic Authentication' },
    { value: 'oauth2', label: 'OAuth 2.0' },
    { value: 'none', label: 'No Authentication' }
  ]

  const eventTypes = [
    'lead.created', 'lead.updated', 'lead.qualified',
    'agent.created', 'agent.configured', 'agent.executed',
    'workflow.started', 'workflow.completed', 'workflow.failed',
    'document.generated', 'email.sent', 'approval.requested'
  ]

  const webhookTemplates = [
    {
      name: 'Slack Notification',
      description: 'Send notifications to Slack channel',
      url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      events: ['lead.qualified', 'workflow.completed']
    },
    {
      name: 'CRM Integration',
      description: 'Sync data with external CRM system',
      url: 'https://api.crm-system.com/webhooks',
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer YOUR_TOKEN' },
      events: ['lead.created', 'lead.updated']
    },
    {
      name: 'Analytics Tracker',
      description: 'Track events in analytics platform',
      url: 'https://analytics.example.com/track',
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      events: ['agent.executed', 'document.generated']
    }
  ]

  const apiTemplates = [
    {
      name: 'Salesforce API',
      description: 'Connect to Salesforce CRM',
      base_url: 'https://your-instance.salesforce.com/services/data/v58.0',
      auth_type: 'oauth2',
      headers: { 'Content-Type': 'application/json' }
    },
    {
      name: 'HubSpot API',
      description: 'Connect to HubSpot CRM',
      base_url: 'https://api.hubapi.com',
      auth_type: 'api_key',
      headers: { 'Content-Type': 'application/json' }
    },
    {
      name: 'Zapier Webhook',
      description: 'Trigger Zapier workflows',
      base_url: 'https://hooks.zapier.com/hooks/catch',
      auth_type: 'none',
      headers: { 'Content-Type': 'application/json' }
    }
  ]

  useEffect(() => {
    fetchWebhooks()
    fetchApiConnections()
  }, [])

  const fetchWebhooks = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/webhooks`)
      const data = await response.json()
      setWebhooks(data.webhooks || [])
    } catch (error) {
      console.error('Error fetching webhooks:', error)
    }
  }

  const fetchApiConnections = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/api-connections`)
      const data = await response.json()
      setApiConnections(data.connections || [])
    } catch (error) {
      console.error('Error fetching API connections:', error)
    }
  }

  const createWebhook = async () => {
    if (!newWebhook.name || !newWebhook.url) return

    setLoading(true)
    try {
      const webhookData = {
        name: newWebhook.name,
        url: newWebhook.url,
        method: newWebhook.method,
        headers: newWebhook.headers,
        secret: newWebhook.secret,
        events: newWebhook.events,
        enabled: true
      }

      const response = await fetch(`${backendUrl}/api/workflow-engine/webhooks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(webhookData)
      })

      if (response.ok) {
        fetchWebhooks()
        setNewWebhook({
          name: '',
          url: '',
          method: 'POST',
          headers: {},
          secret: '',
          events: []
        })
        alert('Webhook created successfully!')
      }
    } catch (error) {
      console.error('Error creating webhook:', error)
    } finally {
      setLoading(false)
    }
  }

  const createApiConnection = async () => {
    if (!newApiConnection.name || !newApiConnection.base_url) return

    setLoading(true)
    try {
      const connectionData = {
        name: newApiConnection.name,
        base_url: newApiConnection.base_url,
        auth_type: newApiConnection.auth_type,
        api_key: newApiConnection.api_key,
        headers: newApiConnection.headers,
        enabled: true
      }

      const response = await fetch(`${backendUrl}/api/workflow-engine/api-connections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(connectionData)
      })

      if (response.ok) {
        fetchApiConnections()
        setNewApiConnection({
          name: '',
          base_url: '',
          auth_type: 'api_key',
          api_key: '',
          headers: {}
        })
        alert('API connection created successfully!')
      }
    } catch (error) {
      console.error('Error creating API connection:', error)
    } finally {
      setLoading(false)
    }
  }

  const testWebhook = async (webhook) => {
    setLoading(true)
    try {
      const testPayload = {
        event: 'test.webhook',
        timestamp: new Date().toISOString(),
        data: {
          message: 'This is a test webhook call',
          source: 'nexus-core'
        }
      }

      const response = await fetch(`${backendUrl}/api/workflow-engine/webhooks/${webhook.id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testPayload)
      })

      const result = await response.json()
      setTestResult({
        webhook: webhook.name,
        success: response.ok,
        status: result.status || response.status,
        response: result.response || 'No response data'
      })
    } catch (error) {
      setTestResult({
        webhook: webhook.name,
        success: false,
        status: 'Error',
        response: error.message
      })
    } finally {
      setLoading(false)
    }
  }

  const testApiConnection = async (connection) => {
    setLoading(true)
    try {
      const response = await fetch(`${backendUrl}/api/workflow-engine/api-connections/${connection.id}/test`, {
        method: 'POST'
      })

      const result = await response.json()
      setTestResult({
        connection: connection.name,
        success: response.ok,
        status: result.status || response.status,
        response: result.response || 'Connection test completed'
      })
    } catch (error) {
      setTestResult({
        connection: connection.name,
        success: false,
        status: 'Error',
        response: error.message
      })
    } finally {
      setLoading(false)
    }
  }

  const useWebhookTemplate = (template) => {
    setNewWebhook({
      name: template.name,
      url: template.url,
      method: template.method,
      headers: template.headers,
      secret: '',
      events: template.events
    })
    setActiveTab('webhooks')
  }

  const useApiTemplate = (template) => {
    setNewApiConnection({
      name: template.name,
      base_url: template.base_url,
      auth_type: template.auth_type,
      api_key: '',
      headers: template.headers
    })
    setActiveTab('api-connections')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Webhook & API Automation</h2>
          <p className="text-muted-foreground">Connect external systems and automate data flows</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="flex items-center gap-1">
            <Webhook className="w-3 h-3" />
            {webhooks.length} Webhooks
          </Badge>
          <Badge variant="outline" className="flex items-center gap-1">
            <Globe className="w-3 h-3" />
            {apiConnections.length} APIs
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="webhooks">Webhooks</TabsTrigger>
          <TabsTrigger value="api-connections">API Connections</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="testing">Testing</TabsTrigger>
        </TabsList>

        <TabsContent value="webhooks" className="space-y-6">
          {/* Create Webhook */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Webhook className="w-5 h-5" />
                Create Webhook
              </CardTitle>
              <CardDescription>
                Configure outbound webhooks to send data to external systems
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="webhookName">Webhook Name</Label>
                  <Input
                    id="webhookName"
                    placeholder="Slack Notifications"
                    value={newWebhook.name}
                    onChange={(e) => setNewWebhook({...newWebhook, name: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label>HTTP Method</Label>
                  <Select value={newWebhook.method} onValueChange={(value) => setNewWebhook({...newWebhook, method: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {httpMethods.map((method) => (
                        <SelectItem key={method} value={method}>
                          {method}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="webhookUrl">Webhook URL</Label>
                <Input
                  id="webhookUrl"
                  placeholder="https://hooks.slack.com/services/..."
                  value={newWebhook.url}
                  onChange={(e) => setNewWebhook({...newWebhook, url: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="webhookSecret">Secret (Optional)</Label>
                <Input
                  id="webhookSecret"
                  type="password"
                  placeholder="Webhook verification secret"
                  value={newWebhook.secret}
                  onChange={(e) => setNewWebhook({...newWebhook, secret: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <Label>Trigger Events</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {eventTypes.map((event) => (
                    <label key={event} className="flex items-center space-x-2 text-sm">
                      <input
                        type="checkbox"
                        checked={newWebhook.events.includes(event)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setNewWebhook({...newWebhook, events: [...newWebhook.events, event]})
                          } else {
                            setNewWebhook({...newWebhook, events: newWebhook.events.filter(ev => ev !== event)})
                          }
                        }}
                      />
                      <span>{event}</span>
                    </label>
                  ))}
                </div>
              </div>

              <Button onClick={createWebhook} disabled={loading} className="w-full">
                <Plus className="w-4 h-4 mr-2" />
                Create Webhook
              </Button>
            </CardContent>
          </Card>

          {/* Active Webhooks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {webhooks.map((webhook) => (
              <Card key={webhook.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{webhook.name}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant={webhook.enabled ? 'default' : 'secondary'}>
                        {webhook.enabled ? 'Active' : 'Disabled'}
                      </Badge>
                      <Badge variant="outline">{webhook.method}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm">
                      <div className="font-medium">URL:</div>
                      <code className="text-xs bg-muted px-2 py-1 rounded block mt-1">
                        {webhook.url}
                      </code>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Events:</span>
                      <Badge variant="outline">{webhook.events?.length || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Calls:</span>
                      <Badge variant="outline">{webhook.call_count || 0}</Badge>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => testWebhook(webhook)}
                      disabled={loading}
                    >
                      <TestTube className="w-4 h-4 mr-2" />
                      Test Webhook
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="api-connections" className="space-y-6">
          {/* Create API Connection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5" />
                Create API Connection
              </CardTitle>
              <CardDescription>
                Set up connections to external APIs for data integration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="apiName">Connection Name</Label>
                  <Input
                    id="apiName"
                    placeholder="Salesforce CRM"
                    value={newApiConnection.name}
                    onChange={(e) => setNewApiConnection({...newApiConnection, name: e.target.value})}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Authentication Type</Label>
                  <Select value={newApiConnection.auth_type} onValueChange={(value) => setNewApiConnection({...newApiConnection, auth_type: value})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {authTypes.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="baseUrl">Base URL</Label>
                <Input
                  id="baseUrl"
                  placeholder="https://api.example.com/v1"
                  value={newApiConnection.base_url}
                  onChange={(e) => setNewApiConnection({...newApiConnection, base_url: e.target.value})}
                />
              </div>

              {newApiConnection.auth_type !== 'none' && (
                <div className="space-y-2">
                  <Label htmlFor="apiKey">
                    {newApiConnection.auth_type === 'api_key' ? 'API Key' :
                     newApiConnection.auth_type === 'bearer_token' ? 'Bearer Token' : 'Authentication Token'}
                  </Label>
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder="Your API key or token"
                    value={newApiConnection.api_key}
                    onChange={(e) => setNewApiConnection({...newApiConnection, api_key: e.target.value})}
                  />
                </div>
              )}

              <Button onClick={createApiConnection} disabled={loading} className="w-full">
                <Plus className="w-4 h-4 mr-2" />
                Create API Connection
              </Button>
            </CardContent>
          </Card>

          {/* Active API Connections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {apiConnections.map((connection) => (
              <Card key={connection.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{connection.name}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant={connection.enabled ? 'default' : 'secondary'}>
                        {connection.enabled ? 'Connected' : 'Disabled'}
                      </Badge>
                      <Badge variant="outline">{connection.auth_type}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="text-sm">
                      <div className="font-medium">Base URL:</div>
                      <code className="text-xs bg-muted px-2 py-1 rounded block mt-1">
                        {connection.base_url}
                      </code>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Requests:</span>
                      <Badge variant="outline">{connection.request_count || 0}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">Last Used:</span>
                      <span className="text-xs text-muted-foreground">
                        {connection.last_used ? new Date(connection.last_used).toLocaleDateString() : 'Never'}
                      </span>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => testApiConnection(connection)}
                      disabled={loading}
                    >
                      <TestTube className="w-4 h-4 mr-2" />
                      Test Connection
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="templates" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Webhook Templates */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Webhook Templates</h3>
              <div className="space-y-3">
                {webhookTemplates.map((template, index) => (
                  <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader>
                      <CardTitle className="text-base">{template.name}</CardTitle>
                      <CardDescription>{template.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="text-xs text-muted-foreground">
                          Method: {template.method} • Events: {template.events.length}
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="w-full"
                          onClick={() => useWebhookTemplate(template)}
                        >
                          Use Webhook Template
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* API Templates */}
            <div>
              <h3 className="text-lg font-semibold mb-4">API Templates</h3>
              <div className="space-y-3">
                {apiTemplates.map((template, index) => (
                  <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader>
                      <CardTitle className="text-base">{template.name}</CardTitle>
                      <CardDescription>{template.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="text-xs text-muted-foreground">
                          Auth: {template.auth_type}
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          className="w-full"
                          onClick={() => useApiTemplate(template)}
                        >
                          Use API Template
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="testing" className="space-y-4">
          {testResult && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {testResult.success ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500" />
                  )}
                  Test Result
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {testResult.webhook ? 'Webhook:' : 'API Connection:'}
                    </span>
                    <span>{testResult.webhook || testResult.connection}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Status:</span>
                    <Badge variant={testResult.success ? 'default' : 'destructive'}>
                      {testResult.status}
                    </Badge>
                  </div>
                  <div>
                    <div className="font-medium mb-2">Response:</div>
                    <code className="text-sm bg-muted p-3 rounded block">
                      {JSON.stringify(testResult.response, null, 2)}
                    </code>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {!testResult && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Activity className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Test Results</h3>
                  <p className="text-muted-foreground">
                    Test webhooks or API connections to see results here
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