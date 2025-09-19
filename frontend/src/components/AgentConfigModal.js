import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Slider } from './ui/slider'
import { Switch } from './ui/switch'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from './ui/dialog'
import { 
  Settings, 
  Brain, 
  Zap, 
  Target,
  Shield,
  Gauge,
  BookOpen,
  MessageSquare,
  Loader2,
  Save,
  RotateCcw,
  Lightbulb,
  Clock,
  Database,
  Cpu
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const AI_MODELS = [
  { value: 'gpt-4o', label: 'GPT-4o (Recommended)', provider: 'OpenAI' },
  { value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet', provider: 'Anthropic' },
  { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash', provider: 'Google' }
]

const AUTONOMY_LEVELS = [
  { value: 'Basic', label: 'Basic', description: 'Requires approval for most actions' },
  { value: 'Medium', label: 'Medium', description: 'Can handle routine tasks independently' },
  { value: 'High', label: 'High', description: 'Advanced decision-making capabilities' },
  { value: 'Quantum', label: 'Quantum', description: 'Full autonomous operation' }
]

const PERFORMANCE_PRESETS = {
  'Conservative': { creativity: 0.3, responsiveness: 0.7, accuracy: 0.9 },
  'Balanced': { creativity: 0.6, responsiveness: 0.8, accuracy: 0.8 },
  'Creative': { creativity: 0.9, responsiveness: 0.8, accuracy: 0.7 },
  'Speed': { creativity: 0.5, responsiveness: 1.0, accuracy: 0.7 }
}

export function AgentConfigModal({ children, agent, onConfigUpdated }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('general')
  
  const [config, setConfig] = useState({
    // General Settings
    name: agent?.name || '',
    type: agent?.type || '',
    personality: agent?.personality || '',
    specialization: agent?.specialization || '',
    autonomy_level: agent?.autonomy_level || 'High',
    
    // AI Configuration
    ai_model: 'gpt-4o',
    temperature: 0.7,
    max_tokens: 1000,
    system_instructions: '',
    
    // Performance Tuning
    creativity: 0.6,
    responsiveness: 0.8,
    accuracy: 0.8,
    learning_rate: 0.5,
    
    // Behavior Settings
    proactive_mode: true,
    auto_learn: true,
    context_memory: true,
    task_prioritization: true,
    
    // Security & Limits
    max_daily_tasks: 100,
    allowed_actions: ['chat', 'research', 'document_generation'],
    restricted_topics: '',
    
    // Integration Settings
    email_integration: false,
    calendar_integration: false,
    crm_integration: true,
    document_access: true
  })

  useEffect(() => {
    if (agent && isOpen) {
      setConfig(prev => ({
        ...prev,
        name: agent.name,
        type: agent.type,
        personality: agent.personality,
        specialization: agent.specialization,
        autonomy_level: agent.autonomy_level,
        system_instructions: agent.configuration?.system_instructions || '',
        // Load other config from agent.configuration
        ...agent.configuration
      }))
    }
  }, [agent, isOpen])

  const handleConfigChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }))
  }

  const applyPerformancePreset = (preset) => {
    const settings = PERFORMANCE_PRESETS[preset]
    setConfig(prev => ({
      ...prev,
      ...settings
    }))
  }

  const handleSave = async () => {
    setIsLoading(true)
    
    try {
      const updateData = {
        name: config.name,
        type: config.type,
        personality: config.personality,
        specialization: config.specialization,
        autonomy_level: config.autonomy_level,
        configuration: {
          ai_model: config.ai_model,
          temperature: config.temperature,
          max_tokens: config.max_tokens,
          system_instructions: config.system_instructions,
          creativity: config.creativity,
          responsiveness: config.responsiveness,
          accuracy: config.accuracy,
          learning_rate: config.learning_rate,
          proactive_mode: config.proactive_mode,
          auto_learn: config.auto_learn,
          context_memory: config.context_memory,
          task_prioritization: config.task_prioritization,
          max_daily_tasks: config.max_daily_tasks,
          allowed_actions: config.allowed_actions,
          restricted_topics: config.restricted_topics,
          integrations: {
            email: config.email_integration,
            calendar: config.calendar_integration,
            crm: config.crm_integration,
            documents: config.document_access
          }
        }
      }

      const response = await axios.put(`${API}/agents/${agent.id}`, updateData)
      
      console.log('Agent configuration updated:', response.data)
      
      if (onConfigUpdated) {
        onConfigUpdated(response.data)
      }
      
      setIsOpen(false)

    } catch (error) {
      console.error('Error updating agent configuration:', error)
      alert('Failed to update agent configuration. Please try again.')
    } finally {
      setIsLoading(false)
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

  if (!agent) return null

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-4xl w-[95vw] h-[80vh] flex flex-col quantum-bg">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-primary" />
            <div>
              <span className="gradient-text">Configure {agent.name}</span>
              <div className="text-sm text-muted-foreground font-normal mt-1">
                Advanced AI agent settings and optimization
              </div>
            </div>
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
          <TabsList className="grid w-full grid-cols-5 mb-4">
            <TabsTrigger value="general" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              General
            </TabsTrigger>
            <TabsTrigger value="ai" className="flex items-center gap-2">
              <Brain className="w-4 h-4" />
              AI Model
            </TabsTrigger>
            <TabsTrigger value="performance" className="flex items-center gap-2">
              <Gauge className="w-4 h-4" />
              Performance
            </TabsTrigger>
            <TabsTrigger value="behavior" className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Behavior
            </TabsTrigger>
            <TabsTrigger value="security" className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Security
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto">
            {/* General Settings Tab */}
            <TabsContent value="general" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Agent Identity
                  </CardTitle>
                  <CardDescription>Core agent information and specialization</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Agent Name</Label>
                      <Input
                        id="name"
                        value={config.name}
                        onChange={(e) => handleConfigChange('name', e.target.value)}
                      />
                    </div>
                    <div>
                      <Label htmlFor="type">Agent Type</Label>
                      <Input
                        id="type"
                        value={config.type}
                        onChange={(e) => handleConfigChange('type', e.target.value)}
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="personality">Personality Profile</Label>
                    <Textarea
                      id="personality"
                      value={config.personality}
                      onChange={(e) => handleConfigChange('personality', e.target.value)}
                      rows={2}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="specialization">Specialization Areas</Label>
                    <Textarea
                      id="specialization"
                      value={config.specialization}
                      onChange={(e) => handleConfigChange('specialization', e.target.value)}
                      rows={3}
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="autonomy">Autonomy Level</Label>
                    <Select value={config.autonomy_level} onValueChange={(value) => handleConfigChange('autonomy_level', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {AUTONOMY_LEVELS.map((level) => (
                          <SelectItem key={level.value} value={level.value}>
                            <div className="flex flex-col">
                              <span className={getAutonomyColor(level.value)}>
                                {level.label} {level.value === 'Quantum' && '⚡'}
                              </span>
                              <span className="text-xs text-muted-foreground">{level.description}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* AI Model Configuration Tab */}
            <TabsContent value="ai" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5" />
                    AI Model Settings
                  </CardTitle>
                  <CardDescription>Configure the underlying AI model and parameters</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="ai_model">AI Model</Label>
                    <Select value={config.ai_model} onValueChange={(value) => handleConfigChange('ai_model', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {AI_MODELS.map((model) => (
                          <SelectItem key={model.value} value={model.value}>
                            <div className="flex flex-col">
                              <span>{model.label}</span>
                              <span className="text-xs text-muted-foreground">{model.provider}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-3">
                    <div>
                      <Label>Temperature: {config.temperature}</Label>
                      <p className="text-xs text-muted-foreground mb-2">Controls creativity vs consistency</p>
                      <Slider
                        value={[config.temperature]}
                        onValueChange={([value]) => handleConfigChange('temperature', value)}
                        max={1}
                        min={0}
                        step={0.1}
                        className="w-full"
                      />
                    </div>
                    
                    <div>
                      <Label>Max Tokens: {config.max_tokens}</Label>
                      <p className="text-xs text-muted-foreground mb-2">Maximum response length</p>
                      <Slider
                        value={[config.max_tokens]}
                        onValueChange={([value]) => handleConfigChange('max_tokens', value)}
                        max={2000}
                        min={100}
                        step={100}
                        className="w-full"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="system_instructions">Custom System Instructions</Label>
                    <Textarea
                      id="system_instructions"
                      value={config.system_instructions}
                      onChange={(e) => handleConfigChange('system_instructions', e.target.value)}
                      placeholder="Additional instructions for the AI agent..."
                      rows={4}
                    />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Performance Tuning Tab */}
            <TabsContent value="performance" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Gauge className="w-5 h-5" />
                    Performance Optimization
                  </CardTitle>
                  <CardDescription>Fine-tune agent performance characteristics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                    {Object.keys(PERFORMANCE_PRESETS).map((preset) => (
                      <Button
                        key={preset}
                        variant="outline"
                        size="sm"
                        onClick={() => applyPerformancePreset(preset)}
                        className="text-xs"
                      >
                        {preset}
                      </Button>
                    ))}
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div>
                        <Label>Creativity: {Math.round(config.creativity * 100)}%</Label>
                        <Slider
                          value={[config.creativity]}
                          onValueChange={([value]) => handleConfigChange('creativity', value)}
                          max={1}
                          min={0}
                          step={0.1}
                        />
                      </div>
                      
                      <div>
                        <Label>Responsiveness: {Math.round(config.responsiveness * 100)}%</Label>
                        <Slider
                          value={[config.responsiveness]}
                          onValueChange={([value]) => handleConfigChange('responsiveness', value)}
                          max={1}
                          min={0}
                          step={0.1}
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div>
                        <Label>Accuracy: {Math.round(config.accuracy * 100)}%</Label>
                        <Slider
                          value={[config.accuracy]}
                          onValueChange={([value]) => handleConfigChange('accuracy', value)}
                          max={1}
                          min={0}
                          step={0.1}
                        />
                      </div>
                      
                      <div>
                        <Label>Learning Rate: {Math.round(config.learning_rate * 100)}%</Label>
                        <Slider
                          value={[config.learning_rate]}
                          onValueChange={([value]) => handleConfigChange('learning_rate', value)}
                          max={1}
                          min={0}
                          step={0.1}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Behavior Settings Tab */}
            <TabsContent value="behavior" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="w-5 h-5" />
                    Behavior Configuration
                  </CardTitle>
                  <CardDescription>Control how your agent behaves and learns</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Proactive Mode</Label>
                          <p className="text-xs text-muted-foreground">Agent initiates tasks</p>
                        </div>
                        <Switch
                          checked={config.proactive_mode}
                          onCheckedChange={(checked) => handleConfigChange('proactive_mode', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Auto Learning</Label>
                          <p className="text-xs text-muted-foreground">Learn from interactions</p>
                        </div>
                        <Switch
                          checked={config.auto_learn}
                          onCheckedChange={(checked) => handleConfigChange('auto_learn', checked)}
                        />
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Context Memory</Label>
                          <p className="text-xs text-muted-foreground">Remember conversations</p>
                        </div>
                        <Switch
                          checked={config.context_memory}
                          onCheckedChange={(checked) => handleConfigChange('context_memory', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Task Prioritization</Label>
                          <p className="text-xs text-muted-foreground">Smart task ordering</p>
                        </div>
                        <Switch
                          checked={config.task_prioritization}
                          onCheckedChange={(checked) => handleConfigChange('task_prioritization', checked)}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Security Settings Tab */}
            <TabsContent value="security" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    Security & Limitations
                  </CardTitle>
                  <CardDescription>Configure security policies and operational limits</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>Max Daily Tasks: {config.max_daily_tasks}</Label>
                    <Slider
                      value={[config.max_daily_tasks]}
                      onValueChange={([value]) => handleConfigChange('max_daily_tasks', value)}
                      max={500}
                      min={10}
                      step={10}
                      className="w-full mt-2"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="restricted_topics">Restricted Topics</Label>
                    <Textarea
                      id="restricted_topics"
                      value={config.restricted_topics}  
                      onChange={(e) => handleConfigChange('restricted_topics', e.target.value)}
                      placeholder="Topics or keywords the agent should avoid..."
                      rows={3}
                    />
                  </div>
                  
                  <div>
                    <Label className="text-base font-medium mb-3 block">Integration Permissions</Label>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center justify-between">
                        <Label>Email Access</Label>
                        <Switch
                          checked={config.email_integration}
                          onCheckedChange={(checked) => handleConfigChange('email_integration', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Label>Calendar Access</Label>
                        <Switch
                          checked={config.calendar_integration}
                          onCheckedChange={(checked) => handleConfigChange('calendar_integration', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Label>CRM Access</Label>
                        <Switch
                          checked={config.crm_integration}
                          onCheckedChange={(checked) => handleConfigChange('crm_integration', checked)}
                        />
                      </div>
                      
                      <div className="flex items-center justify-between">
                        <Label>Document Access</Label>
                        <Switch
                          checked={config.document_access}
                          onCheckedChange={(checked) => handleConfigChange('document_access', checked)}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </div>
        </Tabs>

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
            variant="outline"
            onClick={() => setConfig(prev => ({ ...prev, ...agent }))}
            disabled={isLoading}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
          <Button 
            onClick={handleSave}
            disabled={isLoading}
            className="glow-effect"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Configuration
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}