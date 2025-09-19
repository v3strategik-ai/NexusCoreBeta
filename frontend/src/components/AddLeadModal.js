import { useState } from 'react'
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
import { 
  Users, 
  Loader2,
  Plus,
  DollarSign
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const LEAD_STATUSES = [
  { value: 'cold', label: 'Cold', color: 'text-blue-400' },
  { value: 'warm', label: 'Warm', color: 'text-yellow-400' },
  { value: 'hot', label: 'Hot', color: 'text-red-400' }
]

const LEAD_SOURCES = [
  'Website Contact Form',
  'LinkedIn Campaign', 
  'Google Ads',
  'Trade Show',
  'Referral',
  'Cold Outreach',
  'Social Media',
  'Content Marketing',
  'Email Campaign',
  'Other'
]

export function AddLeadModal({ children, agents, onLeadAdded }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    status: 'cold',
    value: '',
    source: '',
    assigned_agent_id: '',
    notes: ''
  })

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.name || !formData.email) {
      alert('Please fill in all required fields')
      return
    }

    setIsLoading(true)

    try {
      const submitData = {
        ...formData,
        value: parseFloat(formData.value) || 0,
        notes: formData.notes ? [formData.notes] : [],
        tags: []
      }

      const response = await axios.post(`${API}/crm/leads`, submitData)

      console.log('Lead created successfully:', response.data)
      
      // Reset form
      setFormData({
        name: '',
        email: '',
        phone: '',
        company: '',
        status: 'cold',
        value: '',
        source: '',
        assigned_agent_id: 'unassigned',
        notes: ''
      })
      
      // Close modal
      setIsOpen(false)
      
      // Notify parent to refresh leads list
      if (onLeadAdded) {
        onLeadAdded(response.data)
      }

    } catch (error) {
      console.error('Error creating lead:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to create lead. Please try again.'
      alert(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status) => {
    const statusObj = LEAD_STATUSES.find(s => s.value === status)
    return statusObj?.color || 'text-gray-400'
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}  
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto quantum-bg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Users className="w-6 h-6 text-primary" />
            <span className="gradient-text">Add New Lead</span>
          </DialogTitle>
          <DialogDescription>
            Add a new lead to your CRM pipeline with AI-powered scoring and assignment.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Contact Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Contact Name *</Label>
              <Input
                id="name"
                placeholder="John Smith"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email Address *</Label>
              <Input
                id="email"
                type="email"
                placeholder="john@company.com"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                placeholder="+1-555-0123"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="company">Company</Label>
              <Input
                id="company"
                placeholder="Acme Corporation"
                value={formData.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
              />
            </div>
          </div>

          {/* Lead Details */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="status">Lead Status</Label>
              <Select value={formData.status} onValueChange={(value) => handleInputChange('status', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LEAD_STATUSES.map((status) => (
                    <SelectItem key={status.value} value={status.value}>
                      <span className={status.color}>
                        {status.label}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="value">Potential Value ($)</Label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="value"
                  type="number"
                  placeholder="50000"
                  className="pl-10"
                  value={formData.value}
                  onChange={(e) => handleInputChange('value', e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="source">Lead Source</Label>
              <Select value={formData.source} onValueChange={(value) => handleInputChange('source', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select source" />
                </SelectTrigger>
                <SelectContent>
                  {LEAD_SOURCES.map((source) => (
                    <SelectItem key={source} value={source}>
                      {source}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Agent Assignment */}
          <div className="space-y-2">
            <Label htmlFor="agent">Assign to Digital Employee</Label>
            <Select value={formData.assigned_agent_id} onValueChange={(value) => handleInputChange('assigned_agent_id', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select an agent (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="unassigned">No assignment</SelectItem>
                {agents.map((agent) => (
                  <SelectItem key={agent.id} value={agent.id}>
                    {agent.name} - {agent.type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              placeholder="Initial conversation notes, requirements, or other relevant information..."
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              rows={3}
            />
          </div>

          {/* Preview */}
          {formData.name && formData.email && (
            <div className="p-4 border border-primary/20 rounded-lg quantum-bg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">{formData.name}</h4>
                <span className={`text-sm font-medium ${getStatusColor(formData.status)}`}>
                  {LEAD_STATUSES.find(s => s.value === formData.status)?.label}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">{formData.email}</p>
              {formData.company && (
                <p className="text-sm text-muted-foreground">{formData.company}</p>
              )}
              {formData.value && (
                <p className="text-sm font-medium mt-2">
                  Potential Value: ${parseFloat(formData.value).toLocaleString()}
                </p>
              )}
            </div>
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
              disabled={isLoading || !formData.name || !formData.email}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating Lead...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Lead
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}