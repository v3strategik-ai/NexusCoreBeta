import { useState, useEffect } from 'react'
import { Button } from './ui/button'
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { 
  Edit, 
  Save, 
  Loader2,
  User,
  Brain,
  Settings,
  Target
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const AGENT_TYPES = [
  'Sales Representative',
  'Customer Support',
  'Marketing Specialist',
  'Data Analyst',
  'Content Creator',
  'Project Manager',
  'Research Assistant',
  'Lead Generator',
  'Quality Assurance',
  'Technical Support'
]

const AUTONOMY_LEVELS = [
  { value: 'Basic', label: 'Basic', description: 'Requires approval for most actions' },
  { value: 'Medium', label: 'Medium', description: 'Can handle routine tasks independently' },
  { value: 'High', label: 'High', description: 'Full autonomous operation with oversight' },
  { value: 'Quantum', label: 'Quantum', description: 'Advanced AI with self-optimization' }
]

export function EditAgentModal({ agent, onAgentUpdated, children }) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const [formData, setFormData] = useState({
    name: '',
    type: 'Sales Representative',
    personality: '',
    specialization: '',
    autonomy_level: 'Medium',
    description: '',
    goals: [],
    skills: []
  })

  useEffect(() => {
    if (agent && open) {
      setFormData({
        name: agent.name || '',
        type: agent.type || 'Sales Representative',
        personality: agent.personality || '',
        specialization: agent.specialization || '',
        autonomy_level: agent.autonomy_level || 'Medium',
        description: agent.description || '',
        goals: agent.goals || [],
        skills: agent.skills || []
      })
      setError('')
    }
  }, [agent, open])

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleArrayInputChange = (field, value) => {
    const items = value.split(',').map(item => item.trim()).filter(item => item)
    setFormData(prev => ({
      ...prev,
      [field]: items
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.name.trim()) {
      setError('Agent name is required')
      return
    }

    setLoading(true)
    setError('')

    try {
      const updateData = {
        ...formData,
        goals: formData.goals.filter(goal => goal.trim()),
        skills: formData.skills.filter(skill => skill.trim())
      }

      const response = await axios.put(`${API}/agents/${agent.id}`, updateData)
      
      console.log('Agent updated successfully:', response.data)
      
      // Call the callback to update the parent component
      if (onAgentUpdated) {
        onAgentUpdated(response.data)
      }
      
      setOpen(false)
      
      // Show success message
      alert(`Agent "${formData.name}" has been updated successfully!`)
      
    } catch (error) {
      console.error('Error updating agent:', error)
      setError(
        error.response?.data?.detail || 
        error.response?.data?.message || 
        'Failed to update agent. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Edit className="w-5 h-5" />
            Edit Agent: {agent?.name}
          </DialogTitle>
          <DialogDescription>
            Update the agent's profile, capabilities, and settings
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg">
              {error}
            </div>
          )}

          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <User className="w-5 h-5" />
                Basic Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="agent-name">Agent Name *</Label>
                  <Input
                    id="agent-name"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Enter agent name"
                    required
                  />
                </div>
                
                <div>
                  <Label htmlFor="agent-type">Agent Type</Label>
                  <Select value={formData.type} onValueChange={(value) => handleInputChange('type', value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AGENT_TYPES.map(type => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="agent-description">Description</Label>
                <Textarea
                  id="agent-description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe what this agent does"
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* Personality & Capabilities */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Brain className="w-5 h-5" />
                Personality & Capabilities
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="agent-personality">Personality</Label>
                <Textarea
                  id="agent-personality"
                  value={formData.personality}
                  onChange={(e) => handleInputChange('personality', e.target.value)}
                  placeholder="Describe the agent's personality traits"
                  rows={2}
                />
              </div>

              <div>
                <Label htmlFor="agent-specialization">Specialization</Label>
                <Textarea
                  id="agent-specialization"
                  value={formData.specialization}
                  onChange={(e) => handleInputChange('specialization', e.target.value)}
                  placeholder="What is this agent specialized in?"
                  rows={2}
                />
              </div>

              <div>
                <Label htmlFor="agent-autonomy">Autonomy Level</Label>
                <Select value={formData.autonomy_level} onValueChange={(value) => handleInputChange('autonomy_level', value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AUTONOMY_LEVELS.map(level => (
                      <SelectItem key={level.value} value={level.value}>
                        <div>
                          <div className="font-medium">{level.label}</div>
                          <div className="text-sm text-muted-foreground">{level.description}</div>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Goals & Skills */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Target className="w-5 h-5" />
                Goals & Skills
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="agent-goals">Goals (comma-separated)</Label>
                <Textarea
                  id="agent-goals"
                  value={formData.goals.join(', ')}
                  onChange={(e) => handleArrayInputChange('goals', e.target.value)}
                  placeholder="e.g. Increase sales conversion, Improve customer satisfaction, Generate qualified leads"
                  rows={2}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Separate multiple goals with commas
                </p>
              </div>

              <div>
                <Label htmlFor="agent-skills">Skills (comma-separated)</Label>
                <Textarea
                  id="agent-skills"
                  value={formData.skills.join(', ')}
                  onChange={(e) => handleArrayInputChange('skills', e.target.value)}
                  placeholder="e.g. Lead qualification, Email marketing, Data analysis, Customer communication"
                  rows={2}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Separate multiple skills with commas
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Current Status Display */}
          {agent && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Settings className="w-5 h-5" />
                  Current Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Status</div>
                    <Badge variant={agent.status === 'active' ? 'default' : 'secondary'}>
                      {agent.status}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Tasks Completed</div>
                    <div className="font-semibold">{agent.tasks_completed || 0}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Efficiency</div>
                    <div className="font-semibold">{agent.efficiency || 0}%</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Learning Progress</div>
                    <div className="font-semibold">{agent.learning_progress || 0}%</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setOpen(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Updating...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4 mr-2" />
                  Update Agent
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}