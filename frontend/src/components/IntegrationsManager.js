import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog'
import { Label } from './ui/label'
import { Switch } from './ui/switch'
import { 
  Plug, 
  Plus, 
  Settings, 
  CheckCircle, 
  AlertCircle,
  RefreshCw,
  Trash2,
  Edit,
  ExternalLink,
  Key,
  Database,
  Mail,
  Calendar,
  Users,
  DollarSign,
  BarChart3,
  MessageSquare,
  Cloud,
  Smartphone,
  Globe,
  Zap,
  Shield,
  Bell,
  FileText,
  Search,
  Workflow
} from 'lucide-react'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL

const INTEGRATION_CATEGORIES = [
  { value: 'crm', label: 'CRM & Sales', icon: Users },
  { value: 'email', label: 'Email & Communication', icon: Mail },
  { value: 'calendar', label: 'Calendar & Scheduling', icon: Calendar },
  { value: 'payments', label: 'Payments & Finance', icon: DollarSign },
  { value: 'analytics', label: 'Analytics & Reporting', icon: BarChart3 },
  { value: 'messaging', label: 'Messaging & Chat', icon: MessageSquare },
  { value: 'cloud', label: 'Cloud Storage', icon: Cloud },
  { value: 'social', label: 'Social Media', icon: Globe },
  { value: 'automation', label: 'Automation Tools', icon: Zap },
  { value: 'security', label: 'Security & Auth', icon: Shield },
  { value: 'notifications', label: 'Notifications', icon: Bell },
  { value: 'documents', label: 'Document Management', icon: FileText },
  { value: 'other', label: 'Other', icon: Settings }
]

const POPULAR_INTEGRATIONS = [
  {
    id: 'salesforce',
    name: 'Salesforce',
    category: 'crm',
    description: 'World\'s #1 CRM platform for sales and customer management',
    icon: '🏢',
    status: 'available',
    difficulty: 'medium',
    setup_time: '10-15 minutes',
    features: ['Lead Management', 'Contact Sync', 'Opportunity Tracking', 'Custom Fields'],
    auth_type: 'oauth2',
    docs_url: 'https://developer.salesforce.com/docs',
    popular: true
  },
  {
    id: 'hubspot',
    name: 'HubSpot CRM',
    category: 'crm',
    description: 'Inbound marketing, sales, and service software',
    icon: '🧲',
    status: 'available',
    difficulty: 'easy',
    setup_time: '5-10 minutes',
    features: ['Contact Management', 'Deal Pipeline', 'Email Tracking', 'Analytics'],
    auth_type: 'api_key',
    docs_url: 'https://developers.hubspot.com',
    popular: true
  },
  {
    id: 'gmail',
    name: 'Gmail',
    category: 'email',
    description: 'Google email service integration',
    icon: '📧',
    status: 'available',
    difficulty: 'easy',
    setup_time: '2-5 minutes',
    features: ['Email Sync', 'Auto-Reply', 'Template Management', 'Contact Import'],
    auth_type: 'oauth2',
    docs_url: 'https://developers.google.com/gmail',
    popular: true
  },
  {
    id: 'outlook',
    name: 'Microsoft Outlook',
    category: 'email',
    description: 'Microsoft email and calendar service',
    icon: '📨',
    status: 'available',
    difficulty: 'medium',
    setup_time: '5-10 minutes',
    features: ['Email Integration', 'Calendar Sync', 'Contact Management', 'Meeting Scheduling'],
    auth_type: 'oauth2',
    docs_url: 'https://docs.microsoft.com/en-us/graph',
    popular: true
  },
  {
    id: 'slack',
    name: 'Slack',
    category: 'messaging',
    description: 'Team communication and collaboration platform',
    icon: '💬',
    status: 'available',
    difficulty: 'easy',
    setup_time: '3-5 minutes',
    features: ['Channel Notifications', 'Bot Messages', 'File Sharing', 'Workflow Triggers'],
    auth_type: 'oauth2',
    docs_url: 'https://api.slack.com',
    popular: true
  },
  {
    id: 'teams',
    name: 'Microsoft Teams',
    category: 'messaging',
    description: 'Microsoft collaboration platform',
    icon: '👥',
    status: 'available',
    difficulty: 'medium',
    setup_time: '5-10 minutes',
    features: ['Team Chat', 'Meeting Integration', 'File Collaboration', 'Bot Framework'],
    auth_type: 'oauth2',
    docs_url: 'https://docs.microsoft.com/en-us/microsoftteams',
    popular: true
  },
  {
    id: 'stripe',
    name: 'Stripe',
    category: 'payments',
    description: 'Online payment processing platform',
    icon: '💳',
    status: 'available',
    difficulty: 'medium',
    setup_time: '10-15 minutes',
    features: ['Payment Processing', 'Subscription Management', 'Invoice Generation', 'Analytics'],
    auth_type: 'api_key',
    docs_url: 'https://stripe.com/docs',
    popular: true
  },
  {
    id: 'paypal',
    name: 'PayPal',
    category: 'payments',
    description: 'Digital payment platform',
    icon: '💰',
    status: 'available',
    difficulty: 'medium',
    setup_time: '10-15 minutes',
    features: ['Payment Processing', 'Invoicing', 'Subscription Billing', 'Reporting'],
    auth_type: 'oauth2',
    docs_url: 'https://developer.paypal.com',
    popular: false
  },
  {
    id: 'google-analytics',
    name: 'Google Analytics',
    category: 'analytics',
    description: 'Web analytics and reporting platform',
    icon: '📊',
    status: 'available',
    difficulty: 'medium',
    setup_time: '5-10 minutes',
    features: ['Traffic Analytics', 'Goal Tracking', 'Custom Reports', 'Real-time Data'],
    auth_type: 'oauth2',
    docs_url: 'https://developers.google.com/analytics',
    popular: true
  },
  {
    id: 'zapier',
    name: 'Zapier',
    category: 'automation',
    description: 'Workflow automation platform',
    icon: '⚡',
    status: 'available',
    difficulty: 'easy',
    setup_time: '5-10 minutes',
    features: ['Workflow Automation', 'App Connections', 'Trigger Actions', 'Custom Logic'],
    auth_type: 'api_key',
    docs_url: 'https://zapier.com/developer',
    popular: true
  },
  {
    id: 'dropbox',
    name: 'Dropbox',
    category: 'cloud',
    description: 'Cloud storage and file sharing',
    icon: '📁',
    status: 'available',
    difficulty: 'easy',
    setup_time: '3-5 minutes',
    features: ['File Storage', 'Document Sync', 'Sharing', 'Version Control'],
    auth_type: 'oauth2',
    docs_url: 'https://www.dropbox.com/developers',
    popular: false
  },
  {
    id: 'google-drive',
    name: 'Google Drive',
    category: 'cloud',
    description: 'Google cloud storage service',
    icon: '💾',
    status: 'available',
    difficulty: 'easy',
    setup_time: '3-5 minutes',
    features: ['File Storage', 'Document Creation', 'Real-time Collaboration', 'Sharing'],
    auth_type: 'oauth2',
    docs_url: 'https://developers.google.com/drive',
    popular: true
  }
]

export function IntegrationsManager() {
  const [activeIntegrations, setActiveIntegrations] = useState([])
  const [availableIntegrations, setAvailableIntegrations] = useState(POPULAR_INTEGRATIONS)
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [showAddDialog, setShowAddDialog] = useState(false)
  const [selectedIntegration, setSelectedIntegration] = useState(null)
  const [newIntegration, setNewIntegration] = useState({
    name: '',
    category: 'other',
    description: '',
    auth_type: 'api_key',
    api_key: '',
    api_url: '',
    webhook_url: '',
    settings: {}
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Load active integrations (in a real app, this would fetch from backend)
    const mockActiveIntegrations = [
      {
        id: 'gmail-1',
        integration_id: 'gmail',
        name: 'Gmail Integration',
        status: 'connected',
        connected_at: '2024-01-15',
        last_sync: '2024-01-20',
        settings: { auto_sync: true, sync_frequency: '15min' }
      },
      {
        id: 'slack-1',
        integration_id: 'slack',
        name: 'Team Slack',
        status: 'connected',
        connected_at: '2024-01-10',
        last_sync: '2024-01-20',
        settings: { notifications: true, channel: '#general' }
      }
    ]
    setActiveIntegrations(mockActiveIntegrations)
  }, [])

  const filteredIntegrations = availableIntegrations.filter(integration => {
    const matchesCategory = selectedCategory === 'all' || integration.category === selectedCategory
    const matchesSearch = integration.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         integration.description.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const popularIntegrations = availableIntegrations.filter(int => int.popular)

  const handleConnectIntegration = (integration) => {
    setSelectedIntegration(integration)
    setShowAddDialog(true)
  }

  const handleDisconnectIntegration = (integrationId) => {
    setActiveIntegrations(prev => prev.filter(int => int.id !== integrationId))
  }

  const handleSaveIntegration = () => {
    if (selectedIntegration) {
      // Connect existing integration
      const newConnection = {
        id: `${selectedIntegration.id}-${Date.now()}`,
        integration_id: selectedIntegration.id,
        name: `${selectedIntegration.name} Integration`,
        status: 'connected',
        connected_at: new Date().toISOString().split('T')[0],
        last_sync: new Date().toISOString().split('T')[0],
        settings: newIntegration.settings
      }
      setActiveIntegrations(prev => [...prev, newConnection])
    } else {
      // Create custom integration
      const customIntegration = {
        ...newIntegration,
        id: `custom-${Date.now()}`,
        status: 'connected',
        connected_at: new Date().toISOString().split('T')[0],
        last_sync: new Date().toISOString().split('T')[0]
      }
      setActiveIntegrations(prev => [...prev, customIntegration])
    }
    
    setShowAddDialog(false)
    setSelectedIntegration(null)
    setNewIntegration({
      name: '',
      category: 'other',
      description: '',
      auth_type: 'api_key',
      api_key: '',
      api_url: '',
      webhook_url: '',
      settings: {}
    })
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'text-green-600'
      case 'error':
        return 'text-red-600'
      case 'pending':
        return 'text-yellow-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      case 'pending':
        return <RefreshCw className="w-4 h-4 text-yellow-600 animate-spin" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />
    }
  }

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy':
        return 'bg-green-100 text-green-800'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'hard':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold gradient-text">Integrations</h2>
          <p className="text-muted-foreground">
            Connect your favorite tools and platforms to automate workflows
          </p>
        </div>
        <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Integration
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                {selectedIntegration ? `Connect ${selectedIntegration.name}` : 'Add Custom Integration'}
              </DialogTitle>
              <DialogDescription>
                {selectedIntegration 
                  ? `Configure your ${selectedIntegration.name} integration settings`
                  : 'Add a custom integration for platforms not in our catalog'
                }
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              {selectedIntegration ? (
                // Existing integration setup
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl">{selectedIntegration.icon}</div>
                    <div>
                      <h3 className="font-semibold">{selectedIntegration.name}</h3>
                      <p className="text-sm text-muted-foreground">{selectedIntegration.description}</p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Setup Time:</span>
                      <span className="ml-2 font-medium">{selectedIntegration.setup_time}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Difficulty:</span>
                      <Badge className={`ml-2 ${getDifficultyColor(selectedIntegration.difficulty)}`}>
                        {selectedIntegration.difficulty}
                      </Badge>
                    </div>
                  </div>

                  <div>
                    <Label>Features Included</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selectedIntegration.features.map((feature, index) => (
                        <Badge key={index} variant="outline">{feature}</Badge>
                      ))}
                    </div>
                  </div>

                  {selectedIntegration.auth_type === 'api_key' ? (
                    <div>
                      <Label htmlFor="api-key">API Key</Label>
                      <Input
                        id="api-key"
                        type="password"
                        placeholder="Enter your API key"
                        value={newIntegration.api_key}
                        onChange={(e) => setNewIntegration({ ...newIntegration, api_key: e.target.value })}
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        Get your API key from <a href={selectedIntegration.docs_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                          {selectedIntegration.name} Developer Portal <ExternalLink className="w-3 h-3 inline" />
                        </a>
                      </p>
                    </div>
                  ) : (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Shield className="w-5 h-5 text-blue-600" />
                        <span className="font-medium">OAuth 2.0 Authentication</span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        You'll be redirected to {selectedIntegration.name} to authorize the connection securely.
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                // Custom integration setup
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="integration-name">Integration Name</Label>
                      <Input
                        id="integration-name"
                        placeholder="e.g. Custom CRM"
                        value={newIntegration.name}
                        onChange={(e) => setNewIntegration({ ...newIntegration, name: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label>Category</Label>
                      <Select 
                        value={newIntegration.category} 
                        onValueChange={(value) => setNewIntegration({ ...newIntegration, category: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {INTEGRATION_CATEGORIES.map(cat => (
                            <SelectItem key={cat.value} value={cat.value}>
                              {cat.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="integration-description">Description</Label>
                    <Textarea
                      id="integration-description"
                      placeholder="Describe what this integration does"
                      value={newIntegration.description}
                      onChange={(e) => setNewIntegration({ ...newIntegration, description: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="api-url">API Base URL</Label>
                    <Input
                      id="api-url"
                      placeholder="https://api.example.com"
                      value={newIntegration.api_url}
                      onChange={(e) => setNewIntegration({ ...newIntegration, api_url: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="api-key">API Key / Token</Label>
                    <Input
                      id="api-key"
                      type="password"
                      placeholder="Enter your API key or token"
                      value={newIntegration.api_key}
                      onChange={(e) => setNewIntegration({ ...newIntegration, api_key: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="webhook-url">Webhook URL (Optional)</Label>
                    <Input
                      id="webhook-url"
                      placeholder="https://your-domain.com/webhooks"
                      value={newIntegration.webhook_url}
                      onChange={(e) => setNewIntegration({ ...newIntegration, webhook_url: e.target.value })}
                    />
                  </div>
                </div>
              )}
              
              <div className="flex justify-end gap-3 pt-4">
                <Button 
                  variant="outline" 
                  onClick={() => setShowAddDialog(false)}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleSaveIntegration}
                  disabled={selectedIntegration ? !newIntegration.api_key : !newIntegration.name || !newIntegration.api_url}
                >
                  {selectedIntegration && selectedIntegration.auth_type === 'oauth2' ? 'Authorize' : 'Connect'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="active" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="active">Active ({activeIntegrations.length})</TabsTrigger>
          <TabsTrigger value="popular">Popular</TabsTrigger>
          <TabsTrigger value="browse">Browse All</TabsTrigger>
          <TabsTrigger value="custom">Custom</TabsTrigger>
        </TabsList>

        {/* Active Integrations Tab */}
        <TabsContent value="active" className="space-y-6">
          {activeIntegrations.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <Plug className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No Active Integrations</h3>
                  <p className="text-muted-foreground mb-4">
                    Connect your first integration to start automating workflows
                  </p>
                  <Button onClick={() => setShowAddDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Integration
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {activeIntegrations.map(integration => {
                const baseIntegration = availableIntegrations.find(ai => ai.id === integration.integration_id)
                return (
                  <Card key={integration.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between text-lg">
                        <div className="flex items-center gap-2">
                          <div className="text-xl">{baseIntegration?.icon || '🔌'}</div>
                          {integration.name}
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusIcon(integration.status)}
                        </div>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="text-sm space-y-2">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Status:</span>
                            <span className={`font-medium ${getStatusColor(integration.status)}`}>
                              {integration.status}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Connected:</span>
                            <span>{integration.connected_at}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Last Sync:</span>
                            <span>{integration.last_sync}</span>
                          </div>
                        </div>

                        {baseIntegration?.features && (
                          <div>
                            <div className="text-sm font-medium mb-2">Features:</div>
                            <div className="flex flex-wrap gap-1">
                              {baseIntegration.features.slice(0, 3).map((feature, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {feature}
                                </Badge>
                              ))}
                              {baseIntegration.features.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{baseIntegration.features.length - 3} more
                                </Badge>
                              )}
                            </div>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <Button size="sm" variant="outline">
                            <Settings className="w-4 h-4 mr-1" />
                            Settings
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleDisconnectIntegration(integration.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4 mr-1" />
                            Disconnect
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </TabsContent>

        {/* Popular Integrations Tab */}
        <TabsContent value="popular" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {popularIntegrations.map(integration => (
              <Card key={integration.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <div className="text-xl">{integration.icon}</div>
                    {integration.name}
                  </CardTitle>
                  <CardDescription>{integration.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Setup Time:</span>
                      <span>{integration.setup_time}</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Difficulty:</span>
                      <Badge className={getDifficultyColor(integration.difficulty)}>
                        {integration.difficulty}
                      </Badge>
                    </div>

                    <div>
                      <div className="text-sm font-medium mb-2">Key Features:</div>
                      <div className="flex flex-wrap gap-1">
                        {integration.features.slice(0, 3).map((feature, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {feature}
                          </Badge>
                        ))}
                        {integration.features.length > 3 && (
                          <Badge variant="outline" className="text-xs">
                            +{integration.features.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>

                    <Button 
                      className="w-full" 
                      onClick={() => handleConnectIntegration(integration)}
                    >
                      <Plug className="w-4 h-4 mr-2" />
                      Connect
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Browse All Tab */}
        <TabsContent value="browse" className="space-y-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                <Input
                  placeholder="Search integrations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {INTEGRATION_CATEGORIES.map(cat => {
                  const IconComponent = cat.icon
                  return (
                    <SelectItem key={cat.value} value={cat.value}>
                      <div className="flex items-center gap-2">
                        <IconComponent className="w-4 h-4" />
                        {cat.label}
                      </div>
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredIntegrations.map(integration => (
              <Card key={integration.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between text-lg">
                    <div className="flex items-center gap-2">
                      <div className="text-xl">{integration.icon}</div>
                      {integration.name}
                    </div>
                    {integration.popular && (
                      <Badge className="bg-yellow-100 text-yellow-800">Popular</Badge>
                    )}
                  </CardTitle>
                  <CardDescription>{integration.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Category:</span>
                      <Badge variant="outline">
                        {INTEGRATION_CATEGORIES.find(cat => cat.value === integration.category)?.label}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Setup Time:</span>
                      <span>{integration.setup_time}</span>
                    </div>

                    <Button 
                      className="w-full" 
                      onClick={() => handleConnectIntegration(integration)}
                    >
                      <Plug className="w-4 h-4 mr-2" />
                      Connect
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredIntegrations.length === 0 && (
            <div className="text-center py-8">
              <Search className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No integrations found</h3>
              <p className="text-muted-foreground">
                Try adjusting your search or category filter
              </p>
            </div>
          )}
        </TabsContent>

        {/* Custom Integrations Tab */}
        <TabsContent value="custom" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Custom Integrations
              </CardTitle>
              <CardDescription>
                Create custom integrations for platforms not available in our catalog
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { icon: '🔌', title: 'REST API', description: 'Connect to any REST API endpoint' },
                    { icon: '🌐', title: 'GraphQL', description: 'Integrate with GraphQL APIs' },
                    { icon: '📡', title: 'Webhooks', description: 'Receive real-time data via webhooks' },
                    { icon: '🔄', title: 'Database', description: 'Direct database connections' }
                  ].map((type, index) => (
                    <Card key={index} className="cursor-pointer hover:border-primary/50 transition-colors">
                      <CardContent className="pt-6">
                        <div className="text-center">
                          <div className="text-3xl mb-2">{type.icon}</div>
                          <h3 className="font-semibold mb-1">{type.title}</h3>
                          <p className="text-sm text-muted-foreground">{type.description}</p>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
                
                <div className="text-center pt-4">
                  <Button onClick={() => setShowAddDialog(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Custom Integration
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}