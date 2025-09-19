import { useState } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from './ui/dialog'
import { 
  Bot, 
  Loader2,
  Sparkles,
  Plus,
  CheckCircle
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const AGENT_TYPES = [
  'Marketing Specialist',
  'Sales Expert', 
  'Customer Success',
  'Data Scientist',
  'Design & Content',
  'Process Automation'
]

const AUTONOMY_LEVELS = [
  'Basic',
  'Medium', 
  'High',
  'Quantum'
]

const AGENT_SPECIALIZATIONS = {
  'Marketing Specialist': 'Content Creation, SEO, Social Media Marketing',
  'Sales Expert': 'Lead Conversion, Negotiation, CRM Management',
  'Customer Success': 'Technical Support, Customer Onboarding, Issue Resolution',
  'Data Scientist': 'Predictive Analytics, Business Intelligence, Reporting',
  'Design & Content': 'Graphic Design, Video Production, Brand Development', 
  'Process Automation': 'Workflow Optimization, Quality Control, Resource Management'
}

const AGENT_PERSONALITIES = {
  'Marketing Specialist': 'Creative & Data-Driven',
  'Sales Expert': 'Persuasive & Analytical',
  'Customer Success': 'Empathetic & Solution-Oriented', 
  'Data Scientist': 'Logical & Insightful',
  'Design & Content': 'Innovative & Aesthetic',
  'Process Automation': 'Systematic & Efficient'
}

export function CreateAgentModal({ children, onAgentCreated }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    type: '',
    personality: '',
    specialization: '',
    autonomy_level: 'High'
  })

  const handleInputChange = (field, value) => {
    setFormData(prev => {
      const updated = { ...prev, [field]: value }
      
      // Auto-populate personality and specialization based on type
      if (field === 'type') {
        updated.personality = AGENT_PERSONALITIES[value] || ''
        updated.specialization = AGENT_SPECIALIZATIONS[value] || ''
      }
      
      return updated
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.name || !formData.type) {
      alert('Please fill in all required fields')
      return
    }

    setIsLoading(true)

    try {
      const response = await axios.post(`${API}/agents/`, {
        name: formData.name,
        type: formData.type,
        personality: formData.personality,
        specialization: formData.specialization,
        autonomy_level: formData.autonomy_level,
        configuration: {}
      })

      console.log('Agent created successfully:', response.data)
      
      // Reset form
      setFormData({
        name: '',
        type: '',
        personality: '',
        specialization: '',
        autonomy_level: 'High'
      })
      
      // Close modal
      setIsOpen(false)
      
      // Notify parent to refresh agents list
      if (onAgentCreated) {
        onAgentCreated(response.data)
      }

    } catch (error) {
      console.error('Error creating agent:', error)
      alert('Failed to create digital employee. Please try again.')
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

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent 
        className="sm:max-w-2xl w-[95vw] max-h-[80vh] h-[600px] overflow-y-auto quantum-bg border border-primary/20 shadow-2xl"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          maxHeight: '85vh'
        }}
      >
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <div className="relative">
              <Bot className="w-6 h-6 text-primary" />
              <Sparkles className="w-3 h-3 absolute -top-1 -right-1 text-yellow-400" />
            </div>
            <span className="gradient-text">Create New Digital Employee</span>
          </DialogTitle>
          <DialogDescription>
            Design and configure your new AI-powered digital employee with specialized capabilities.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Agent Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Agent Name *</Label>
            <Input
              id="name"
              placeholder="e.g., Marketing Genius, Sales Powerhouse"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              required
            />
          </div>

          {/* Agent Type */}
          <div className="space-y-2">
            <Label htmlFor="type">Agent Type *</Label>
            <Select value={formData.type} onValueChange={(value) => handleInputChange('type', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select agent specialization" />
              </SelectTrigger>
              <SelectContent>
                {AGENT_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Autonomy Level */}
          <div className="space-y-2">
            <Label htmlFor="autonomy">Autonomy Level</Label>
            <Select value={formData.autonomy_level} onValueChange={(value) => handleInputChange('autonomy_level', value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {AUTONOMY_LEVELS.map((level) => (
                  <SelectItem key={level} value={level}>
                    <span className={getAutonomyColor(level)}>
                      {level} {level === 'Quantum' && '⚡'}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Higher autonomy levels enable more independent decision-making
            </p>
          </div>

          {/* Auto-populated fields */}
          {formData.type && (
            <>
              <div className="space-y-2">
                <Label htmlFor="personality">Personality Profile</Label>
                <Input
                  id="personality"
                  value={formData.personality}
                  onChange={(e) => handleInputChange('personality', e.target.value)}
                  placeholder="Agent personality traits"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="specialization">Specialization Areas</Label>
                <Textarea
                  id="specialization"
                  value={formData.specialization}
                  onChange={(e) => handleInputChange('specialization', e.target.value)}
                  placeholder="Key areas of expertise"
                  rows={3}
                />
              </div>
            </>
          )}

          {/* Preview Card */}
          {formData.name && formData.type && (
            <Card className="quantum-bg border-primary/20">
              <CardHeader>
                <CardTitle className="text-sm">Preview - {formData.name}</CardTitle>
                <CardDescription>{formData.type}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Autonomy:</span>
                    <span className={`ml-2 font-semibold ${getAutonomyColor(formData.autonomy_level)}`}>
                      {formData.autonomy_level}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Status:</span>
                    <span className="ml-2 text-yellow-400">Training</span>
                  </div>
                </div>
                {formData.personality && (
                  <p className="text-xs text-muted-foreground mt-2">
                    <strong>Personality:</strong> {formData.personality}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-2 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setIsOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              className="glow-effect"
              disabled={isLoading || !formData.name || !formData.type}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Agent...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Digital Employee
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}