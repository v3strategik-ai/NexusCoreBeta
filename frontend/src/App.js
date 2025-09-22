import { useState, useEffect } from 'react'
import { Button } from './components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { Badge } from './components/ui/badge'
import { Input } from './components/ui/input'
import { Textarea } from './components/ui/textarea'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import { Progress } from './components/ui/progress'
import { Switch } from './components/ui/switch'
import { AgentChatModal } from './components/AgentChatModal'
import { CreateAgentModal } from './components/CreateAgentModal'
import { UploadKnowledgeModal } from './components/UploadKnowledgeModal'
import { AddLeadModal } from './components/AddLeadModal'
import { EditLeadModal } from './components/EditLeadModal'
import { ContactLeadModal } from './components/ContactLeadModal'
import { AgentConfigModal } from './components/AgentConfigModal'
import { WorkflowBuilderModal } from './components/WorkflowBuilderModal'
import { DocumentGenerationModal } from './components/DocumentGenerationModal'
import { EmailAutomationModal } from './components/EmailAutomationModal'
import { RealTimeDashboard } from './components/RealTimeDashboard'
import { VisualWorkflowBuilder } from './components/VisualWorkflowBuilder'
import { NotificationSystem, useNotifications } from './components/NotificationSystem'
import { 
  Brain, 
  Zap, 
  Shield, 
  Database, 
  Mail, 
  FileText, 
  BarChart3, 
  Settings, 
  Users, 
  Bot,
  Sparkles,
  CheckCircle,
  Globe,
  Workflow,
  Plus,
  Edit,
  Home,
  Briefcase,
  Target,
  BookOpen,
  Upload,
  Download,
  Search,
  CloudUpload,
  Rocket,
  Star,
  Activity,
  DollarSign,
  Gauge,
  Server,
  Lightbulb,
  Play,
  Pause,
  Power,
  MessageSquare,
  Video,
  Eye,
  Layers,
  Trash2,
  RefreshCw,
  Minimize
} from 'lucide-react'
import axios from 'axios'
import './App.css'
import logoFrame3 from './assets/logo_frame_3.png'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

function App() {
  const [currentTab, setCurrentTab] = useState('dashboard')
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [agents, setAgents] = useState([])
  const [leads, setLeads] = useState([])
  const [workflows, setWorkflows] = useState([])
  
  // Initialize notification system
  const { 
    notifications, 
    addNotification, 
    markAsRead, 
    dismissNotification,
    clearAll,
    markAllAsRead,
    unreadCount 
  } = useNotifications()

  // Add real-time features
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(true)
  const [connectionStatus, setConnectionStatus] = useState('disconnected')
  
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateAgent, setShowCreateAgent] = useState(false)
  const [showAddLead, setShowAddLead] = useState(false)
  const [showUploadKnowledge, setShowUploadKnowledge] = useState(false)

  // Fetch data from backend
  useEffect(() => {
    fetchDashboardData()
    fetchAgents()
    fetchLeads()
    fetchWorkflows()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/metrics`)
      setDashboardData(response.data)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      setError('Failed to load dashboard data')
    }
  }

  const fetchAgents = async () => {
    try {
      const response = await axios.get(`${API}/agents/`)
      setAgents(response.data.agents || [])
      setLoading(false)
    } catch (error) {
      console.error('Error fetching agents:', error)
      setError('Failed to load agents')
      setLoading(false)
    }
  }

  const fetchLeads = async () => {
    try {
      const response = await axios.get(`${API}/crm/leads`)
      setLeads(response.data.leads || [])
    } catch (error) {
      console.error('Error fetching leads:', error)
      setError('Failed to load leads')
    }
  }

  const fetchWorkflows = async () => {
    try {
      const response = await axios.get(`${API}/workflows/`)
      setWorkflows(response.data || [])
    } catch (error) {
      console.error('Error fetching workflows:', error)
      // Don't set error state for workflows as it's not critical
    }
  }

  const getAutonomyColor = (level) => {
    switch(level) {
      case 'Quantum': return 'text-purple-400'
      case 'High': return 'text-green-400'
      case 'Medium': return 'text-yellow-400'
      default: return 'text-gray-400'
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'active': return 'bg-green-500'
      case 'training': return 'bg-yellow-500'
      case 'idle': return 'bg-gray-500'
      default: return 'bg-gray-500'
    }
  }

  const getLeadStatusColor = (status) => {
    switch(status) {
      case 'hot': return 'destructive'
      case 'warm': return 'default'
      case 'converted': return 'default'
      default: return 'secondary'
    }
  }

  // Event handlers for buttons
  const handleAgentCreated = (newAgent) => {
    setAgents(prev => [...prev, newAgent])
    console.log('New agent created:', newAgent.name)
  }

  const handleAgentConfigured = (updatedAgent) => {
    setAgents(prev => prev.map(agent => 
      agent.id === updatedAgent.id ? updatedAgent : agent
    ))
    console.log('Agent configured:', updatedAgent.name)
  }

  const handleKnowledgeUploaded = (knowledgeData) => {
    console.log('Knowledge uploaded:', knowledgeData.title)
    // Optionally refresh data or show success message
  }

  const handleLeadAdded = (newLead) => {
    setLeads(prev => [...prev, newLead])
    console.log('New lead added:', newLead.name)
  }

  const handleWorkflowCreated = (newWorkflow) => {
    setWorkflows(prev => [...prev, newWorkflow])
    console.log('New workflow created:', newWorkflow.name)
  }

  const handleDocumentGenerated = (generatedDocument) => {
    console.log('Document generated:', generatedDocument.title)
    // Optionally refresh data or show success message
    alert(`Document "${generatedDocument.title}" generated successfully!`)
  }

  const handleLeadUpdated = (updatedLead) => {
    setLeads(prev => prev.map(lead => 
      lead.id === updatedLead.id ? updatedLead : lead
    ))
    console.log('Lead updated:', updatedLead.name)
  }

  const handleLeadDeleted = (deletedLeadId) => {
    setLeads(prev => prev.filter(lead => lead.id !== deletedLeadId))
    console.log('Lead deleted:', deletedLeadId)
  }

  const handleContactLogged = (contactActivity) => {
    console.log('Contact logged:', contactActivity)
    // Optionally refresh lead data or show notification
  }

  const handleAgentConfigUpdated = (updatedAgent) => {
    setAgents(prev => prev.map(agent => 
      agent.id === updatedAgent.id ? updatedAgent : agent
    ))
    console.log('Agent configuration updated:', updatedAgent.name)
    
    // Show success notification
    alert(`Configuration updated for ${updatedAgent.name}!\n\nKey changes:\n- Configuration complexity: ${updatedAgent.metrics?.configuration_complexity || 0}\n- Readiness score: ${updatedAgent.metrics?.readiness_score || 0}%`)
  }

  const handleEmailSent = (emailInfo) => {
    console.log('Email sent:', emailInfo)
    
    // Show success notification based on email type
    let message = ''
    if (emailInfo.type === 'single') {
      const lead = leads.find(l => l.id === emailInfo.lead_id)
      message = `Email sent to ${lead?.name || 'lead'} using ${emailInfo.template} template!`
    } else if (emailInfo.type === 'bulk') {
      message = `Bulk email sent to ${emailInfo.count} leads using ${emailInfo.template} template!`
    }
    
    if (message) {
      alert(message)
    }
  }

  const handleCreateAgent = () => {
    // This will be handled by the modal
    console.log('Create new digital employee clicked')
  }

  const handleUploadKnowledge = () => {
    // This will be handled by the modal  
    console.log('Upload knowledge clicked')
  }

  const handleAddLead = () => {
    // This will be handled by the modal
    console.log('Add lead clicked')
  }

  const handleGenerateDocument = (documentType) => {
    console.log('Generate document clicked:', documentType)
    alert(`Document generation for ${documentType} - Coming soon!`)
  }

  const handleConfigureAgent = (agent) => {
    // This will be handled by the AgentConfigModal
    console.log('Configure agent clicked:', agent.name)
  }

  const handleEditLead = (lead) => {
    console.log('Edit lead clicked:', lead.name)
    // This will now be handled by the EditLeadModal
  }

  const handleContactLead = (lead) => {
    console.log('Contact lead clicked:', lead.name)
    // This will now be handled by the ContactLeadModal
  }

  const AgentCard = ({ agent }) => (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 hover:border-primary/50 transition-all duration-300 hover:scale-105 quantum-bg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)} animate-pulse`}></div>
          </div>
          <div>
            <CardTitle className="text-lg font-bold gradient-text">{agent.name}</CardTitle>
            <p className="text-sm text-muted-foreground">{agent.type}</p>
          </div>
        </div>
        <Badge variant={agent.status === 'active' ? 'default' : 'secondary'} className="quantum-pulse">
          {agent.status}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-2xl font-bold">{agent.tasks_completed}</div>
            <p className="text-xs text-muted-foreground">Tasks Completed</p>
          </div>
          <div>
            <div className="text-2xl font-bold">{agent.efficiency}%</div>
            <p className="text-xs text-muted-foreground">Efficiency</p>
          </div>
        </div>
        
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span>Learning Progress</span>
            <span>{agent.learning_progress}%</span>
          </div>
          <Progress value={agent.learning_progress} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Autonomy Level:</span>
            <span className={`font-semibold ${getAutonomyColor(agent.autonomy_level)}`}>
              {agent.autonomy_level}
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            <strong>Personality:</strong> {agent.personality}
          </div>
          <div className="text-xs text-muted-foreground">
            <strong>Specialization:</strong> {agent.specialization}
          </div>
        </div>

        <div className="flex gap-2">
          <AgentChatModal agent={agent}>
            <Button size="sm" variant="outline" className="glow-effect">
              <MessageSquare className="w-4 h-4 mr-1" />
              Chat
            </Button>
          </AgentChatModal>
          <Button size="sm" variant="outline" onClick={() => setSelectedAgent(agent)}>
            <BookOpen className="w-4 h-4 mr-1" />
            Details
          </Button>
          <AgentConfigModal agent={agent} onConfigUpdated={handleAgentConfigUpdated}>
            <Button size="sm" variant="outline">
              <Settings className="w-4 h-4 mr-1" />
              Configure  
            </Button>
          </AgentConfigModal>
        </div>
      </CardContent>
    </Card>
  )

  const LeadCard = ({ lead }) => (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 quantum-bg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{lead.name}</CardTitle>
        <Badge variant={getLeadStatusColor(lead.status)}>
          {lead.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground mb-2">{lead.email}</div>
        <div className="text-2xl font-bold">${lead.value?.toLocaleString()}</div>
        <p className="text-xs text-muted-foreground mb-2">Potential Value</p>
        <div className="text-xs text-muted-foreground mb-4">
          <strong>Assigned to:</strong> {lead.assigned_agent_name || 'Unassigned'}
        </div>
        <div className="flex gap-2">
          <ContactLeadModal 
            lead={lead} 
            onContactLogged={handleContactLogged}
          >
            <Button size="sm" variant="outline">
              <Mail className="w-4 h-4 mr-1" />
              Contact
            </Button>
          </ContactLeadModal>
          <EditLeadModal 
            lead={lead} 
            agents={agents}
            onLeadUpdated={handleLeadUpdated}
            onLeadDeleted={handleLeadDeleted}
          >
            <Button size="sm" variant="outline">
              <Edit className="w-4 h-4 mr-1" />
              Edit
            </Button>
          </EditLeadModal>
        </div>
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="min-h-screen bg-background neural-pattern flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading Nexus Core...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background neural-pattern flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background neural-pattern">
      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-sm bg-background/80 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img 
              src={logoFrame3} 
              alt="Nexus Core" 
              className="w-8 h-8 quantum-pulse"
            />
            <div>
              <h1 className="text-xl font-bold gradient-text">Nexus Core</h1>
              <p className="text-xs text-muted-foreground">Autonomous Digital Employees Powerhouse</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="quantum-pulse">
              <Rocket className="w-3 h-3 mr-1" />
              Quantum Level
            </Badge>
            <UploadKnowledgeModal agents={agents} onKnowledgeUploaded={handleKnowledgeUploaded}>
              <Button variant="outline" size="sm">
                <Upload className="w-4 h-4 mr-2" />
                Upload Knowledge
              </Button>
            </UploadKnowledgeModal>
            <CreateAgentModal onAgentCreated={handleAgentCreated}>
              <Button size="sm" className="glow-effect">
                <Plus className="w-4 h-4 mr-2" />
                New Digital Employee
              </Button>  
            </CreateAgentModal>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="w-full">
          <TabsList className="grid w-full grid-cols-6 mb-6">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <Home className="w-4 h-4" />
              Command Center
            </TabsTrigger>
            <TabsTrigger value="realtime" className="flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Real-Time Intelligence
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center gap-2">
              <Bot className="w-4 h-4" />
              Digital Employees
            </TabsTrigger>
            <TabsTrigger value="crm" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              CRM Intelligence
            </TabsTrigger>
            <TabsTrigger value="workflows" className="flex items-center gap-2">
              <Workflow className="w-4 h-4" />
              Workflows
            </TabsTrigger>
            <TabsTrigger value="documents" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Documents
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold gradient-text mb-2">Quantum Command Center</h2>
              <p className="text-muted-foreground">Monitor and control your autonomous digital workforce</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="quantum-bg glow-effect">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Digital Employees</CardTitle>
                  <Bot className="h-4 w-4 text-muted-foreground quantum-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">{dashboardData?.active_agents || 0}</div>
                  <p className="text-xs text-muted-foreground">Quantum-level autonomous</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground quantum-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">{dashboardData?.total_tasks_completed || 0}</div>
                  <p className="text-xs text-muted-foreground">Autonomous completion</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Revenue Generated</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground quantum-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">${dashboardData?.total_revenue_generated?.toLocaleString() || '0'}</div>
                  <p className="text-xs text-muted-foreground">AI-driven revenue</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">System Efficiency</CardTitle>
                  <Gauge className="h-4 w-4 text-muted-foreground quantum-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">{dashboardData?.system_efficiency || 0}%</div>
                  <p className="text-xs text-muted-foreground">Peak performance</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Server className="w-5 h-5" />
                    Quantum System Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Neural Processing Power</span>
                        <span>{dashboardData?.neural_processing_power || 0}%</span>
                      </div>
                      <Progress value={dashboardData?.neural_processing_power || 0} className="h-3" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Knowledge Base Utilization</span>
                        <span>{dashboardData?.knowledge_base_utilization || 0}%</span>
                      </div>
                      <Progress value={dashboardData?.knowledge_base_utilization || 0} className="h-3" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Autonomous Decision Rate</span>
                        <span>{dashboardData?.autonomous_decision_rate || 0}%</span>
                      </div>
                      <Progress value={dashboardData?.autonomous_decision_rate || 0} className="h-3" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    System Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span>Total Digital Employees</span>
                      <span className="font-bold">{agents.length}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Active Leads</span>
                      <span className="font-bold">{leads.length}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Learning Acceleration</span>
                      <span className="font-bold">{dashboardData?.learning_acceleration || 0}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span>Platform Status</span>
                      <Badge variant="default" className="quantum-pulse">Operational</Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Real-Time Intelligence Tab */}
          <TabsContent value="realtime" className="space-y-6">
            <RealTimeDashboard 
              agents={agents}
              leads={leads}
              workflows={workflows}
              isRealTimeEnabled={isRealTimeEnabled}
              setIsRealTimeEnabled={setIsRealTimeEnabled}
              connectionStatus={connectionStatus}
              setConnectionStatus={setConnectionStatus}
              notifications={notifications}
              addNotification={addNotification}
              markAsRead={markAsRead}
              dismissNotification={dismissNotification}
              clearAll={clearAll}
              markAllAsRead={markAllAsRead}
              unreadCount={unreadCount}
            />
          </TabsContent>

          {/* Digital Employees Tab */}
          <TabsContent value="agents" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">Digital Employees Management</h2>
                <p className="text-muted-foreground">Your autonomous workforce of quantum-level AI agents</p>
              </div>
              <CreateAgentModal onAgentCreated={handleAgentCreated}>
                <Button className="glow-effect">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Digital Employee
                </Button>
              </CreateAgentModal>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {agents.map(agent => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
          </TabsContent>

          {/* CRM Tab */}
          <TabsContent value="crm" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">CRM Intelligence</h2>
                <p className="text-muted-foreground">AI-powered customer relationship management</p>
              </div>
              <AddLeadModal agents={agents} onLeadAdded={handleLeadAdded}>
                <Button className="glow-effect">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Lead
                </Button>
              </AddLeadModal>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Total Leads</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">{leads.length}</div>
                  <p className="text-xs text-muted-foreground">Active pipeline</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Hot Leads</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">
                    {leads.filter(lead => lead.status === 'hot').length}
                  </div>
                  <p className="text-xs text-muted-foreground">Ready to convert</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Pipeline Value</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">
                    ${leads.reduce((sum, lead) => sum + (lead.value || 0), 0).toLocaleString()}
                  </div>
                  <p className="text-xs text-muted-foreground">Total potential</p>
                </CardContent>
              </Card>

              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Converted</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">
                    {leads.filter(lead => lead.status === 'converted').length}
                  </div>
                  <p className="text-xs text-muted-foreground">Successful deals</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {leads.map(lead => (
                <LeadCard key={lead.id} lead={lead} />
              ))}
            </div>
          </TabsContent>

          {/* Workflows Tab */}
          <TabsContent value="workflows" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">Advanced Workflows</h2>
                <p className="text-muted-foreground">Automate business processes with intelligent workflows</p>
              </div>
              <div className="flex gap-2">
                <EmailAutomationModal leads={leads} onEmailSent={handleEmailSent}>
                  <Button className="glow-effect">
                    <Mail className="w-4 h-4 mr-2" />
                    Email Automation
                  </Button>
                </EmailAutomationModal>
                <VisualWorkflowBuilder onWorkflowCreated={handleWorkflowCreated}>
                  <Button className="glow-effect">
                    <Plus className="w-4 h-4 mr-2" />
                    Visual Workflow Builder
                  </Button>
                </VisualWorkflowBuilder>
                <WorkflowBuilderModal agents={agents} onWorkflowCreated={handleWorkflowCreated}>
                  <Button variant="outline">
                    <Settings className="w-4 h-4 mr-2" />
                    Simple Builder
                  </Button>
                </WorkflowBuilderModal>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Total Workflows</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">{workflows.length}</div>
                  <p className="text-xs text-muted-foreground">Active automations</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Running Now</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">
                    {workflows.filter(w => w.status === 'active').length}
                  </div>
                  <p className="text-xs text-muted-foreground">Currently executing</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Time Saved</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">147h</div>
                  <p className="text-xs text-muted-foreground">This month</p>
                </CardContent>
              </Card>

              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Success Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">98.5%</div>
                  <p className="text-xs text-muted-foreground">Execution success</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {workflows.length === 0 ? (
                <div className="col-span-full text-center py-12">
                  <Workflow className="w-16 h-16 mx-auto mb-4 opacity-30" />
                  <h3 className="text-lg font-semibold mb-2">No Workflows Yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Create your first automated workflow to streamline business processes
                  </p>
                  <WorkflowBuilderModal agents={agents} onWorkflowCreated={handleWorkflowCreated}>
                    <Button className="glow-effect">
                      <Plus className="w-4 h-4 mr-2" />
                      Create Your First Workflow
                    </Button>
                  </WorkflowBuilderModal>
                </div>
              ) : (
                workflows.map(workflow => (
                  <Card key={workflow.id} className="quantum-bg">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-semibold">{workflow.name}</CardTitle>
                        <Badge variant={workflow.status === 'active' ? 'default' : 'secondary'}>
                          {workflow.status}
                        </Badge>
                      </div>
                      <CardDescription className="text-xs">{workflow.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="text-sm">
                          <span className="text-muted-foreground">Trigger:</span>
                          <span className="ml-2 capitalize">{workflow.trigger_type.replace('_', ' ')}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-muted-foreground">Steps:</span>
                          <span className="ml-2">{workflow.steps?.length || 0}</span>
                        </div>
                        <div className="text-sm">
                          <span className="text-muted-foreground">Runs:</span>
                          <span className="ml-2">{workflow.run_count || 0}</span>
                        </div>
                        <div className="flex gap-2 mt-4">
                          <Button size="sm" variant="outline">
                            <Play className="w-3 h-3 mr-1" />
                            Run
                          </Button>
                          <Button size="sm" variant="outline">
                            <Settings className="w-3 h-3 mr-1" />
                            Edit
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">Document Generation</h2>
                <p className="text-muted-foreground">AI-powered business document creation</p>
              </div>
              <DocumentGenerationModal agents={agents} onDocumentGenerated={handleDocumentGenerated}>
                <Button className="glow-effect">
                  <Plus className="w-4 h-4 mr-2" />
                  Generate Document
                </Button>
              </DocumentGenerationModal>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { icon: FileText, title: 'AI Proposals', desc: 'Generate winning proposals', color: 'text-blue-400', type: 'proposal' },
                { icon: DollarSign, title: 'Smart Invoices', desc: 'Automated invoicing', color: 'text-green-400', type: 'invoice' },
                { icon: Briefcase, title: 'Business Plans', desc: 'Comprehensive plans', color: 'text-purple-400', type: 'business_plan' },
                { icon: BarChart3, title: 'Analytics Reports', desc: 'Data-driven insights', color: 'text-orange-400', type: 'report' }
              ].map((doc, index) => (
                <DocumentGenerationModal 
                  key={index} 
                  agents={agents} 
                  onDocumentGenerated={handleDocumentGenerated}
                  defaultType={doc.type}
                >
                  <Card 
                    className="quantum-bg cursor-pointer hover:border-primary/50 transition-all duration-300 hover:scale-105 glow-effect"
                  >
                    <CardContent className="p-6 text-center">
                      <doc.icon className={`w-12 h-12 mx-auto mb-4 ${doc.color}`} />
                      <h3 className="font-semibold mb-2">{doc.title}</h3>
                      <p className="text-sm text-muted-foreground">{doc.desc}</p>
                    </CardContent>
                  </Card>
                </DocumentGenerationModal>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App