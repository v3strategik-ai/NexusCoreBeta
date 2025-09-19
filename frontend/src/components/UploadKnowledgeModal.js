import { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Badge } from './ui/badge'
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from './ui/dialog'
import { 
  Upload, 
  File, 
  Loader2,
  BookOpen,
  CheckCircle,
  X
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const KNOWLEDGE_CATEGORIES = [
  'Training Materials',
  'Product Documentation', 
  'Sales Collateral',
  'Customer Support',
  'Marketing Content',
  'Technical Guides',
  'Business Processes',
  'Industry Research'
]

export function UploadKnowledgeModal({ children, agents, onKnowledgeUploaded }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    tags: '',
    selectedAgents: []
  })

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedFile(file)
      if (!formData.title) {
        // Auto-populate title from filename
        const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "")
        setFormData(prev => ({ ...prev, title: nameWithoutExt }))
      }
    }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const toggleAgentSelection = (agentId) => {
    setFormData(prev => ({
      ...prev,
      selectedAgents: prev.selectedAgents.includes(agentId)
        ? prev.selectedAgents.filter(id => id !== agentId)
        : [...prev.selectedAgents, agentId]
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!selectedFile || !formData.title || !formData.category) {
      alert('Please fill in all required fields and select a file')
      return
    }

    setIsUploading(true)

    try {
      // Create FormData for file upload
      const uploadData = new FormData()
      uploadData.append('file', selectedFile)
      uploadData.append('title', formData.title)
      uploadData.append('description', formData.description)
      uploadData.append('category', formData.category)
      uploadData.append('tags', formData.tags)
      uploadData.append('agent_ids', formData.selectedAgents.join(','))

      const response = await axios.post(`${API}/knowledge/upload`, uploadData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      console.log('Knowledge uploaded successfully:', response.data)
      
      // Reset form
      setSelectedFile(null)
      setFormData({
        title: '',
        description: '',
        category: '',
        tags: '',
        selectedAgents: []
      })
      
      // Reset file input
      const fileInput = document.getElementById('knowledge-file')
      if (fileInput) fileInput.value = ''
      
      // Close modal
      setIsOpen(false)
      
      // Notify parent
      if (onKnowledgeUploaded) {
        onKnowledgeUploaded(response.data)
      }

    } catch (error) {
      console.error('Error uploading knowledge:', error)
      alert('Failed to upload knowledge base file. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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
            <BookOpen className="w-6 h-6 text-primary" />
            <span className="gradient-text">Upload Knowledge Base</span>
          </DialogTitle>
          <DialogDescription>
            Upload documents, guides, and training materials to enhance your AI agents' knowledge.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* File Upload */}
          <div className="space-y-2">
            <Label htmlFor="knowledge-file">Select File *</Label>
            <div className="flex items-center justify-center w-full">
              <label htmlFor="knowledge-file" className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
                selectedFile ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50 hover:bg-muted/50'
              }`}>
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  {selectedFile ? (
                    <>
                      <CheckCircle className="w-8 h-8 mb-2 text-primary" />
                      <p className="text-sm font-medium">{selectedFile.name}</p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-8 h-8 mb-2 text-muted-foreground" />
                      <p className="mb-2 text-sm text-muted-foreground">
                        <span className="font-semibold">Click to upload</span> or drag and drop
                      </p>
                      <p className="text-xs text-muted-foreground">PDF, DOC, TXT, MD (MAX. 10MB)</p>
                    </>
                  )}
                </div>
                <input 
                  id="knowledge-file" 
                  type="file" 
                  className="hidden" 
                  onChange={handleFileSelect}
                  accept=".pdf,.doc,.docx,.txt,.md"
                />
              </label>
            </div>
          </div>

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Sales Training Manual, Product FAQ"
              value={formData.title}
              onChange={(e) => handleInputChange('title', e.target.value)}
              required
            />
          </div>

          {/* Category */}
          <div className="space-y-2">
            <Label htmlFor="category">Category *</Label>
            <Select value={formData.category} onValueChange={(value) => handleInputChange('category', value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select knowledge category" />
              </SelectTrigger>
              <SelectContent>
                {KNOWLEDGE_CATEGORIES.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Brief description of the knowledge content"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
            />
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags</Label>
            <Input
              id="tags"
              placeholder="training, sales, customer-service (comma-separated)"
              value={formData.tags}
              onChange={(e) => handleInputChange('tags', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Add comma-separated tags to help organize and search knowledge
            </p>
          </div>

          {/* Agent Assignment */}
          <div className="space-y-3">
            <Label>Assign to Digital Employees</Label>
            <p className="text-sm text-muted-foreground">
              Select which agents should have access to this knowledge
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-40 overflow-y-auto">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className={`flex items-center space-x-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    formData.selectedAgents.includes(agent.id)
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                  onClick={() => toggleAgentSelection(agent.id)}
                >
                  <div className={`w-4 h-4 border-2 rounded flex items-center justify-center ${
                    formData.selectedAgents.includes(agent.id)
                      ? 'border-primary bg-primary'
                      : 'border-border'
                  }`}>
                    {formData.selectedAgents.includes(agent.id) && (
                      <CheckCircle className="w-3 h-3 text-white" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{agent.name}</p>
                    <p className="text-xs text-muted-foreground truncate">{agent.type}</p>
                  </div>
                </div>
              ))}
            </div>
            {formData.selectedAgents.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.selectedAgents.map(agentId => {
                  const agent = agents.find(a => a.id === agentId)
                  return agent ? (
                    <Badge key={agentId} variant="secondary" className="flex items-center gap-1">
                      {agent.name}
                      <X 
                        className="w-3 h-3 cursor-pointer" 
                        onClick={() => toggleAgentSelection(agentId)}
                      />
                    </Badge>
                  ) : null
                })}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-2 pt-4">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setIsOpen(false)}
              disabled={isUploading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              className="glow-effect"
              disabled={isUploading || !selectedFile || !formData.title || !formData.category}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Knowledge
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}