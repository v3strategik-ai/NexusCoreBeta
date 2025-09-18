import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Switch } from '@/components/ui/switch.jsx'
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
  Cpu, 
  Network, 
  Bot,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Globe,
  Lock,
  Workflow,
  Play,
  Pause,
  Upload,
  Download,
  MessageSquare,
  Calendar,
  DollarSign,
  TrendingUp,
  Activity,
  AlertTriangle,
  Plus,
  Edit,
  Trash2,
  Search,
  Filter,
  MoreVertical,
  Home,
  Briefcase,
  Target,
  PieChart,
  LineChart,
  BookOpen,
  Mic,
  Video,
  Eye,
  Layers,
  Lightbulb,
  Rocket,
  Star,
  Award,
  Gauge,
  Headphones,
  Monitor,
  Smartphone,
  Wifi,
  CloudUpload,
  HardDrive,
  Server,
  Code,
  Palette,
  Camera,
  Music,
  FileImage,
  File,
  FileSpreadsheet,
  FileVideo,
  Folder,
  FolderOpen,
  Link,
  ExternalLink,
  RefreshCw,
  Power,
  Maximize,
  Minimize,
  Volume2,
  VolumeX
} from 'lucide-react'
import './App.css'
import logoFrame3 from './assets/logo_frame_3.png'
import logoVideo from './assets/nexus_core_logo_animation.MP4'

function App() {
  const [currentTab, setCurrentTab] = useState('dashboard')
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [agents, setAgents] = useState([
    { 
      id: 1, 
      name: 'Marketing Genius', 
      type: 'Marketing Specialist',
      status: 'active', 
      tasks: 15, 
      efficiency: 94,
      personality: 'Creative & Data-Driven',
      specialization: 'Content Creation, SEO, Social Media',
      knowledgeBase: ['Marketing Strategies.pdf', 'Brand Guidelines.docx', 'Customer Personas.xlsx'],
      learningProgress: 87,
      autonomyLevel: 'High',
      lastActive: '2 minutes ago'
    },
    { 
      id: 2, 
      name: 'Sales Powerhouse', 
      type: 'Sales Expert',
      status: 'active', 
      tasks: 23, 
      efficiency: 87,
      personality: 'Persuasive & Analytical',
      specialization: 'Lead Conversion, Negotiation, CRM Management',
      knowledgeBase: ['Sales Playbook.pdf', 'Product Catalog.pdf', 'Pricing Strategy.xlsx'],
      learningProgress: 92,
      autonomyLevel: 'High',
      lastActive: '1 minute ago'
    },
    { 
      id: 3, 
      name: 'Support Virtuoso', 
      type: 'Customer Success',
      status: 'training', 
      tasks: 8, 
      efficiency: 76,
      personality: 'Empathetic & Solution-Oriented',
      specialization: 'Technical Support, Customer Onboarding, Issue Resolution',
      knowledgeBase: ['Support Manual.pdf', 'FAQ Database.json', 'Product Documentation.md'],
      learningProgress: 65,
      autonomyLevel: 'Medium',
      lastActive: '5 minutes ago'
    },
    { 
      id: 4, 
      name: 'Analytics Oracle', 
      type: 'Data Scientist',
      status: 'active', 
      tasks: 31, 
      efficiency: 98,
      personality: 'Logical & Insightful',
      specialization: 'Predictive Analytics, Business Intelligence, Reporting',
      knowledgeBase: ['Data Models.py', 'Analytics Framework.pdf', 'KPI Definitions.xlsx'],
      learningProgress: 95,
      autonomyLevel: 'Quantum',
      lastActive: '30 seconds ago'
    },
    { 
      id: 5, 
      name: 'Creative Mastermind', 
      type: 'Design & Content',
      status: 'active', 
      tasks: 12, 
      efficiency: 89,
      personality: 'Innovative & Aesthetic',
      specialization: 'Graphic Design, Video Production, Brand Development',
      knowledgeBase: ['Design System.figma', 'Brand Assets.zip', 'Creative Brief.pdf'],
      learningProgress: 78,
      autonomyLevel: 'High',
      lastActive: '3 minutes ago'
    },
    { 
      id: 6, 
      name: 'Operations Commander', 
      type: 'Process Automation',
      status: 'active', 
      tasks: 45, 
      efficiency: 96,
      personality: 'Systematic & Efficient',
      specialization: 'Workflow Optimization, Quality Control, Resource Management',
      knowledgeBase: ['Process Maps.pdf', 'SOP Manual.docx', 'Automation Scripts.py'],
      learningProgress: 91,
      autonomyLevel: 'Quantum',
      lastActive: '1 minute ago'
    }
  ])
  
  const [leads, setLeads] = useState([
    { id: 1, name: 'Acme Corp', email: 'contact@acme.com', status: 'hot', value: 50000, lastContact: '2024-01-15', assignedAgent: 'Sales Powerhouse' },
    { id: 2, name: 'TechStart Inc', email: 'hello@techstart.com', status: 'warm', value: 25000, lastContact: '2024-01-14', assignedAgent: 'Marketing Genius' },
    { id: 3, name: 'Global Solutions', email: 'info@global.com', status: 'cold', value: 75000, lastContact: '2024-01-10', assignedAgent: 'Sales Powerhouse' },
    { id: 4, name: 'Innovation Labs', email: 'team@innovation.com', status: 'hot', value: 120000, lastContact: '2024-01-16', assignedAgent: 'Analytics Oracle' }
  ])
  
  const [showVideo, setShowVideo] = useState(true)

  useEffect(() => {
    // Auto-hide video after 8 seconds (duration of the video)
    const timer = setTimeout(() => {
      setShowVideo(false)
    }, 8000)
    return () => clearTimeout(timer)
  }, [])

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
            <div className="text-2xl font-bold">{agent.tasks}</div>
            <p className="text-xs text-muted-foreground">Active Tasks</p>
          </div>
          <div>
            <div className="text-2xl font-bold">{agent.efficiency}%</div>
            <p className="text-xs text-muted-foreground">Efficiency</p>
          </div>
        </div>
        
        <div>
          <div className="flex items-center justify-between text-sm mb-2">
            <span>Learning Progress</span>
            <span>{agent.learningProgress}%</span>
          </div>
          <Progress value={agent.learningProgress} className="h-2" />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Autonomy Level:</span>
            <span className={`font-semibold ${getAutonomyColor(agent.autonomyLevel)}`}>
              {agent.autonomyLevel}
            </span>
          </div>
          <div className="text-xs text-muted-foreground">
            <strong>Personality:</strong> {agent.personality}
          </div>
          <div className="text-xs text-muted-foreground">
            <strong>Specialization:</strong> {agent.specialization}
          </div>
          <div className="text-xs text-muted-foreground">
            <strong>Last Active:</strong> {agent.lastActive}
          </div>
        </div>

        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => setSelectedAgent(agent)}>
            <BookOpen className="w-4 h-4 mr-1" />
            Knowledge Base
          </Button>
          <Button size="sm" variant="outline">
            <Settings className="w-4 h-4 mr-1" />
            Configure
          </Button>
          <Button size="sm" variant="outline">
            <BarChart3 className="w-4 h-4 mr-1" />
            Analytics
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const LeadCard = ({ lead }) => (
    <Card className="bg-card/50 backdrop-blur-sm border-border/50 quantum-bg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{lead.name}</CardTitle>
        <Badge variant={lead.status === 'hot' ? 'destructive' : lead.status === 'warm' ? 'default' : 'secondary'}>
          {lead.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="text-sm text-muted-foreground mb-2">{lead.email}</div>
        <div className="text-2xl font-bold">${lead.value.toLocaleString()}</div>
        <p className="text-xs text-muted-foreground mb-2">Potential Value</p>
        <div className="text-xs text-muted-foreground mb-4">
          <strong>Assigned to:</strong> {lead.assignedAgent}
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline">
            <Mail className="w-4 h-4 mr-1" />
            Contact
          </Button>
          <Button size="sm" variant="outline">
            <Edit className="w-4 h-4 mr-1" />
            Edit
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  const KnowledgeBaseModal = ({ agent, onClose }) => {
    if (!agent) return null;
    
    return (
      <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
        <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto quantum-bg">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="gradient-text">{agent.name} - Knowledge Base</CardTitle>
              <CardDescription>Upload and manage specific information for this digital employee</CardDescription>
            </div>
            <Button variant="outline" onClick={onClose}>
              <Minimize className="w-4 h-4" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Current Knowledge Base */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Database className="w-5 h-5" />
                Current Knowledge Base
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {agent.knowledgeBase.map((file, index) => (
                  <Card key={index} className="p-4 bg-muted/20">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {file.includes('.pdf') && <File className="w-5 h-5 text-red-400" />}
                        {file.includes('.docx') && <FileText className="w-5 h-5 text-blue-400" />}
                        {file.includes('.xlsx') && <FileSpreadsheet className="w-5 h-5 text-green-400" />}
                        {file.includes('.py') && <Code className="w-5 h-5 text-yellow-400" />}
                        {file.includes('.json') && <Database className="w-5 h-5 text-purple-400" />}
                        {file.includes('.figma') && <Palette className="w-5 h-5 text-pink-400" />}
                        {file.includes('.zip') && <Folder className="w-5 h-5 text-orange-400" />}
                        {file.includes('.md') && <FileText className="w-5 h-5 text-gray-400" />}
                        <span className="text-sm font-medium">{file}</span>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="outline">
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>

            {/* Upload New Knowledge */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <CloudUpload className="w-5 h-5" />
                Upload New Knowledge
              </h3>
              <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                <CloudUpload className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">Drag & drop files here</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Support for PDF, DOCX, XLSX, TXT, JSON, CSV, and more
                </p>
                <Button className="glow-effect">
                  <Upload className="w-4 h-4 mr-2" />
                  Choose Files
                </Button>
              </div>
            </div>

            {/* Knowledge Categories */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Layers className="w-5 h-5" />
                Knowledge Categories
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="p-4 text-center cursor-pointer hover:border-primary/50 transition-colors">
                  <FileText className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                  <p className="text-sm font-medium">Documents</p>
                  <p className="text-xs text-muted-foreground">12 files</p>
                </Card>
                <Card className="p-4 text-center cursor-pointer hover:border-primary/50 transition-colors">
                  <Database className="w-8 h-8 mx-auto mb-2 text-green-400" />
                  <p className="text-sm font-medium">Data Sets</p>
                  <p className="text-xs text-muted-foreground">5 files</p>
                </Card>
                <Card className="p-4 text-center cursor-pointer hover:border-primary/50 transition-colors">
                  <Code className="w-8 h-8 mx-auto mb-2 text-yellow-400" />
                  <p className="text-sm font-medium">Scripts</p>
                  <p className="text-xs text-muted-foreground">8 files</p>
                </Card>
                <Card className="p-4 text-center cursor-pointer hover:border-primary/50 transition-colors">
                  <FileImage className="w-8 h-8 mx-auto mb-2 text-purple-400" />
                  <p className="text-sm font-medium">Media</p>
                  <p className="text-xs text-muted-foreground">15 files</p>
                </Card>
              </div>
            </div>

            {/* Training Instructions */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Custom Training Instructions
              </h3>
              <Textarea 
                placeholder="Provide specific instructions on how this agent should use the uploaded knowledge..."
                rows={4}
                className="mb-4"
              />
              <div className="flex gap-2">
                <Button className="glow-effect">
                  <Sparkles className="w-4 h-4 mr-2" />
                  Start Training
                </Button>
                <Button variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retrain Agent
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background neural-pattern">
      {/* Video Overlay */}
      {showVideo && (
        <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center">
          <video 
            autoPlay 
            muted 
            className="max-w-full max-h-full"
            onEnded={() => setShowVideo(false)}
          >
            <source src={logoVideo} type="video/mp4" />
          </video>
        </div>
      )}

      {/* Knowledge Base Modal */}
      {selectedAgent && (
        <KnowledgeBaseModal 
          agent={selectedAgent} 
          onClose={() => setSelectedAgent(null)} 
        />
      )}

      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-sm bg-background/80 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img 
              src={logoFrame3} 
              alt="Nexus Core" 
              className="w-8 h-8 quantum-pulse cursor-pointer"
              onClick={() => setShowVideo(true)}
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
            <Button variant="outline" size="sm">
              <Upload className="w-4 h-4 mr-2" />
              Upload Knowledge
            </Button>
            <Button size="sm" className="glow-effect">
              <Plus className="w-4 h-4 mr-2" />
              New Digital Employee
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        <Tabs value={currentTab} onValueChange={setCurrentTab} className="w-full">
          <TabsList className="grid w-full grid-cols-7 mb-6">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <Home className="w-4 h-4" />
              Command Center
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center gap-2">
              <Bot className="w-4 h-4" />
              Digital Employees
            </TabsTrigger>
            <TabsTrigger value="knowledge" className="flex items-center gap-2">
              <BookOpen className="w-4 h-4" />
              Knowledge Hub
            </TabsTrigger>
            <TabsTrigger value="crm" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              CRM Intelligence
            </TabsTrigger>
            <TabsTrigger value="automation" className="flex items-center gap-2">
              <Workflow className="w-4 h-4" />
              Automation
            </TabsTrigger>
            <TabsTrigger value="documents" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Documents
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Neural Config
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
                  <div className="text-3xl font-bold gradient-text">6</div>
                  <p className="text-xs text-muted-foreground">+2 quantum-level agents</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
                  <CheckCircle className="h-4 w-4 text-muted-foreground quantum-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">2,847</div>
                  <p className="text-xs text-muted-foreground">+45% autonomous completion</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Revenue Generated</CardTitle>
                  <DollarSign className="h-4 w-4 text-muted-foreground quantum-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">$145,231</div>
                  <p className="text-xs text-muted-foreground">+67% from AI automation</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Quantum Efficiency</CardTitle>
                  <Gauge className="h-4 w-4 text-muted-foreground quantum-pulse" />
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">98.7%</div>
                  <p className="text-xs text-muted-foreground">Peak performance achieved</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5" />
                    Real-Time Agent Activity
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center space-x-4">
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Analytics Oracle completed predictive model training</p>
                        <p className="text-xs text-muted-foreground">15 seconds ago • Quantum Level</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Sales Powerhouse closed $50K deal autonomously</p>
                        <p className="text-xs text-muted-foreground">2 minutes ago • High Autonomy</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="w-3 h-3 bg-purple-500 rounded-full animate-pulse"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Marketing Genius launched viral campaign</p>
                        <p className="text-xs text-muted-foreground">5 minutes ago • Creative Mode</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">Operations Commander optimized 12 workflows</p>
                        <p className="text-xs text-muted-foreground">8 minutes ago • System Enhancement</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

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
                        <span>87%</span>
                      </div>
                      <Progress value={87} className="h-3" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Knowledge Base Utilization</span>
                        <span>94%</span>
                      </div>
                      <Progress value={94} className="h-3" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Autonomous Decision Rate</span>
                        <span>98%</span>
                      </div>
                      <Progress value={98} className="h-3" />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Learning Acceleration</span>
                        <span>76%</span>
                      </div>
                      <Progress value={76} className="h-3" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quantum Performance Metrics */}
            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Star className="w-5 h-5" />
                  Quantum Performance Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-4xl font-bold gradient-text mb-2">99.2%</div>
                    <p className="text-sm text-muted-foreground">Autonomous Success Rate</p>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-bold gradient-text mb-2">847ms</div>
                    <p className="text-sm text-muted-foreground">Average Response Time</p>
                  </div>
                  <div className="text-center">
                    <div className="text-4xl font-bold gradient-text mb-2">24/7</div>
                    <p className="text-sm text-muted-foreground">Continuous Operation</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Digital Employees Tab */}
          <TabsContent value="agents" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">Digital Employees Management</h2>
                <p className="text-muted-foreground">Your autonomous workforce of quantum-level AI agents</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <Upload className="w-4 h-4 mr-2" />
                  Bulk Train
                </Button>
                <Button className="glow-effect">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Digital Employee
                </Button>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              {agents.map(agent => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>

            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Rocket className="w-5 h-5" />
                  Advanced Digital Employee Creator
                </CardTitle>
                <CardDescription>Create specialized autonomous agents with quantum-level capabilities</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Employee Name</label>
                    <Input placeholder="e.g., Revenue Optimizer, Content Virtuoso" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Specialization</label>
                    <Input placeholder="e.g., Sales & Revenue, Marketing & Growth" />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Autonomy Level</label>
                    <Input placeholder="Quantum, High, Medium, Basic" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Personality Type</label>
                    <Input placeholder="Analytical, Creative, Empathetic, Strategic" />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Core Capabilities & Training Instructions</label>
                  <Textarea 
                    placeholder="Define what this digital employee should excel at, their decision-making parameters, and how they should interact with customers and other systems..."
                    rows={4}
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <Button className="glow-effect">
                    <Brain className="w-4 h-4 mr-2" />
                    Create & Train Agent
                  </Button>
                  <Button variant="outline">
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Knowledge Base
                  </Button>
                  <Button variant="outline">
                    <Sparkles className="w-4 h-4 mr-2" />
                    AI-Assisted Setup
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Knowledge Hub Tab */}
          <TabsContent value="knowledge" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">Knowledge Hub</h2>
                <p className="text-muted-foreground">Centralized knowledge management for all digital employees</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <Search className="w-4 h-4 mr-2" />
                  Search Knowledge
                </Button>
                <Button className="glow-effect">
                  <CloudUpload className="w-4 h-4 mr-2" />
                  Upload Knowledge
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="quantum-bg text-center p-6">
                <Database className="w-12 h-12 mx-auto mb-4 text-blue-400" />
                <h3 className="text-2xl font-bold">247</h3>
                <p className="text-sm text-muted-foreground">Knowledge Files</p>
              </Card>
              <Card className="quantum-bg text-center p-6">
                <BookOpen className="w-12 h-12 mx-auto mb-4 text-green-400" />
                <h3 className="text-2xl font-bold">15</h3>
                <p className="text-sm text-muted-foreground">Knowledge Categories</p>
              </Card>
              <Card className="quantum-bg text-center p-6">
                <Brain className="w-12 h-12 mx-auto mb-4 text-purple-400" />
                <h3 className="text-2xl font-bold">98.5%</h3>
                <p className="text-sm text-muted-foreground">Knowledge Utilization</p>
              </Card>
              <Card className="quantum-bg text-center p-6">
                <Lightbulb className="w-12 h-12 mx-auto mb-4 text-yellow-400" />
                <h3 className="text-2xl font-bold">1,247</h3>
                <p className="text-sm text-muted-foreground">AI Insights Generated</p>
              </Card>
            </div>

            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Quick Upload
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                  <CloudUpload className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">Drop files here to upload</p>
                  <p className="text-sm text-muted-foreground mb-4">
                    Supports all document types, images, videos, and data files
                  </p>
                  <Button className="glow-effect">
                    <Upload className="w-4 h-4 mr-2" />
                    Browse Files
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* CRM Tab */}
          <TabsContent value="crm" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">CRM Intelligence</h2>
                <p className="text-muted-foreground">AI-powered customer relationship management with predictive insights</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <Search className="w-4 h-4 mr-2" />
                  AI Lead Search
                </Button>
                <Button className="glow-effect">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Lead
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Total Leads</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">1,247</div>
                  <p className="text-xs text-muted-foreground">+89 AI-generated this week</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">AI Conversion Rate</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">34.7%</div>
                  <p className="text-xs text-muted-foreground">+12.3% with AI assistance</p>
                </CardContent>
              </Card>
              
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">Pipeline Value</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">$2.8M</div>
                  <p className="text-xs text-muted-foreground">+45% from AI optimization</p>
                </CardContent>
              </Card>

              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="text-sm">AI Predictions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold gradient-text">97.2%</div>
                  <p className="text-xs text-muted-foreground">Accuracy rate</p>
                </CardContent>
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {leads.map(lead => (
                <LeadCard key={lead.id} lead={lead} />
              ))}
            </div>

            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  AI-Powered Lead Generation & Website Scraper
                </CardTitle>
                <CardDescription>Advanced web scraping with AI-powered lead qualification and scoring</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Target Website/Domain</label>
                    <Input placeholder="https://example.com or industry domain" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Industry/Sector</label>
                    <Input placeholder="Technology, Healthcare, Finance, etc." />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Company Size</label>
                    <Input placeholder="Startup, Small, Medium, Large, Enterprise" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Revenue Range</label>
                    <Input placeholder="Under $1M, $1M-$10M, $10M-$50M, etc." />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">AI Search Criteria & Qualification Parameters</label>
                  <Textarea 
                    placeholder="Define specific criteria for lead qualification, decision-maker roles, pain points to identify, and any specific technologies or keywords to look for..."
                    rows={4}
                  />
                </div>

                <div className="flex gap-2">
                  <Button className="glow-effect">
                    <Target className="w-4 h-4 mr-2" />
                    Start AI Lead Generation
                  </Button>
                  <Button variant="outline">
                    <Globe className="w-4 h-4 mr-2" />
                    Bulk Website Scraping
                  </Button>
                  <Button variant="outline">
                    <Brain className="w-4 h-4 mr-2" />
                    AI Lead Scoring
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Automation Tab */}
          <TabsContent value="automation" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">Quantum Automation</h2>
                <p className="text-muted-foreground">Advanced workflow automation with self-healing capabilities</p>
              </div>
              <Button className="glow-effect">
                <Plus className="w-4 h-4 mr-2" />
                Create Quantum Workflow
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="w-5 h-5" />
                    Email Automation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">AI-powered email campaigns with personalization</p>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Status</span>
                    <Switch defaultChecked />
                  </div>
                  <div className="text-xs text-muted-foreground mb-4">
                    <strong>Performance:</strong> 47% open rate, 12% CTR
                  </div>
                  <Button variant="outline" size="sm">Configure</Button>
                </CardContent>
              </Card>

              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="w-5 h-5" />
                    Website Scraping
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">Intelligent web scraping for lead generation and data extraction</p>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Status</span>
                    <Switch defaultChecked />
                  </div>
                  <div className="text-xs text-muted-foreground mb-4">
                    <strong>Last Run:</strong> 247 leads extracted
                  </div>
                  <Button variant="outline" size="sm">Configure</Button>
                </CardContent>
              </Card>

              <Card className="quantum-bg glow-effect">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Anomaly Detection
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">AI-powered system monitoring and threat detection</p>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">Status</span>
                    <Switch defaultChecked />
                  </div>
                  <div className="text-xs text-muted-foreground mb-4">
                    <strong>Threats Blocked:</strong> 23 this week
                  </div>
                  <Button variant="outline" size="sm">Configure</Button>
                </CardContent>
              </Card>
            </div>

            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Self-Healing Quantum Systems
                </CardTitle>
                <CardDescription>Autonomous system maintenance and optimization with quantum-level intelligence</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Quantum Auto-backup</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Neural Performance Optimization</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Predictive Error Recovery</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Autonomous Code Debugging</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Quantum Security Monitoring</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Intelligent Resource Scaling</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Predictive Maintenance</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Self-Sustaining Operations</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-bold gradient-text">Quantum Document Center</h2>
                <p className="text-muted-foreground">AI-powered document generation with 20+ templates and intelligent automation</p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload
                </Button>
                <Button className="glow-effect">
                  <Plus className="w-4 h-4 mr-2" />
                  AI Document
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { icon: FileText, title: 'AI Proposals', desc: 'Generate winning proposals with AI', color: 'text-blue-400' },
                { icon: DollarSign, title: 'Smart Invoices', desc: 'Automated invoicing with payment tracking', color: 'text-green-400' },
                { icon: Briefcase, title: 'Business Plans', desc: 'Comprehensive AI-generated business plans', color: 'text-purple-400' },
                { icon: BarChart3, title: 'Analytics Reports', desc: 'Data-driven insights and visualizations', color: 'text-orange-400' },
                { icon: Users, title: 'HR Documents', desc: 'Employee contracts and policies', color: 'text-pink-400' },
                { icon: Shield, title: 'Legal Docs', desc: 'Compliance and legal documentation', color: 'text-red-400' },
                { icon: Target, title: 'Marketing Materials', desc: 'Campaigns and promotional content', color: 'text-yellow-400' },
                { icon: Settings, title: 'Technical Specs', desc: 'Product and system documentation', color: 'text-gray-400' }
              ].map((doc, index) => (
                <Card key={index} className="quantum-bg cursor-pointer hover:border-primary/50 transition-all duration-300 hover:scale-105 glow-effect">
                  <CardContent className="p-6 text-center">
                    <doc.icon className={`w-12 h-12 mx-auto mb-4 ${doc.color}`} />
                    <h3 className="font-semibold mb-2">{doc.title}</h3>
                    <p className="text-sm text-muted-foreground">{doc.desc}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="quantum-bg">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  Quantum Quoting Tool
                </CardTitle>
                <CardDescription>AI-powered quote generation with intelligent pricing and proposal optimization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Client/Company Name</label>
                    <Input placeholder="Enter client name" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Project Type</label>
                    <Input placeholder="Web Development, AI Solution, Consulting, etc." />
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Project Complexity</label>
                    <Input placeholder="Basic, Intermediate, Advanced, Enterprise" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Timeline</label>
                    <Input placeholder="Rush, Standard, Extended, Ongoing" />
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Project Requirements & Specifications</label>
                  <Textarea 
                    placeholder="Describe the project requirements, features needed, technical specifications, and any special considerations..."
                    rows={4}
                  />
                </div>

                <div className="flex gap-2">
                  <Button className="glow-effect">
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generate AI Quote
                  </Button>
                  <Button variant="outline">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Price Analysis
                  </Button>
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Export PDF
                  </Button>
                  <Button variant="outline">
                    <Mail className="w-4 h-4 mr-2" />
                    Send to Client
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold gradient-text">Neural Configuration Center</h2>
              <p className="text-muted-foreground">Advanced quantum-level system configuration and optimization</p>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5" />
                    Quantum Agent Configuration
                  </CardTitle>
                  <CardDescription>Fine-tune neural network parameters and behavior patterns</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Neural Learning Rate</label>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm">Conservative</span>
                      <div className="flex-1">
                        <Progress value={75} />
                      </div>
                      <span className="text-sm">Aggressive</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Current: Quantum Adaptive (75%)</p>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium mb-2 block">Decision Autonomy Level</label>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm">Guided</span>
                      <div className="flex-1">
                        <Progress value={90} />
                      </div>
                      <span className="text-sm">Full Autonomy</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Current: Quantum Level (90%)</p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>Quantum Auto-optimization</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Predictive Learning</span>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Cross-Agent Knowledge Sharing</span>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />
                    Advanced Communication Center
                  </CardTitle>
                  <CardDescription>Team messaging, video conferencing, and AI-powered collaboration</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 gap-6">
                    <div className="space-y-4">
                      <h4 className="font-semibold flex items-center gap-2">
                        <MessageSquare className="w-4 h-4" />
                        Quantum Messaging & Video
                      </h4>
                      <div className="flex items-center justify-between">
                        <span>Real-time notifications</span>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <span>AI message summarization</span>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <span>4K video conferencing</span>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <span>AI meeting transcription</span>
                        <Switch defaultChecked />
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 mt-6">
                    <Button className="glow-effect">
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Open Quantum Chat
                    </Button>
                    <Button variant="outline">
                      <Video className="w-4 h-4 mr-2" />
                      Start Video Conference
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App

