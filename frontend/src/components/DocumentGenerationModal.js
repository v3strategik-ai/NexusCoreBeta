import { useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
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
  FileText, 
  Sparkles,
  Download,
  Copy,
  Loader2, 
  Save,
  Wand2,
  DollarSign,
  Briefcase,
  BarChart3,
  Mail,
  FileCheck,
  Bot
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const DOCUMENT_TYPES = [
  { 
    value: 'proposal', 
    label: 'Business Proposal', 
    icon: Briefcase, 
    description: 'Professional project proposals',
    color: 'text-blue-400',
    variables: ['client_name', 'project_description', 'project_value', 'timeline', 'deliverables']
  },
  { 
    value: 'invoice', 
    label: 'Invoice', 
    icon: DollarSign, 
    description: 'Professional invoices',
    color: 'text-green-400',
    variables: ['client_name', 'invoice_number', 'amount', 'due_date', 'services', 'payment_terms']
  },
  { 
    value: 'business_plan', 
    label: 'Business Plan', 
    icon: BarChart3, 
    description: 'Comprehensive business plans',
    color: 'text-purple-400',
    variables: ['company_name', 'executive_summary', 'target_market', 'financial_projections', 'strategy']
  },
  { 
    value: 'report', 
    label: 'Analytics Report', 
    icon: FileCheck, 
    description: 'Data-driven business reports',
    color: 'text-orange-400',
    variables: ['report_title', 'time_period', 'key_metrics', 'insights', 'recommendations']
  },
  { 
    value: 'contract', 
    label: 'Contract', 
    icon: FileText, 
    description: 'Legal contracts and agreements',
    color: 'text-red-400',
    variables: ['party_1', 'party_2', 'scope_of_work', 'payment_terms', 'duration', 'terms_conditions']
  },
  { 
    value: 'marketing', 
    label: 'Marketing Content', 
    icon: Mail, 
    description: 'Marketing materials and copy',
    color: 'text-pink-400',
    variables: ['campaign_name', 'target_audience', 'key_message', 'call_to_action', 'brand_guidelines']
  }
]

export function DocumentGenerationModal({ children, agents, onDocumentGenerated, defaultType }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [selectedType, setSelectedType] = useState(defaultType || '')
  const [formData, setFormData] = useState({
    title: '',
    type: defaultType || '',
    client_name: '',
    agent_id: 'auto_select',
    custom_instructions: '',
    variables: {}
  })
  const [generatedDocument, setGeneratedDocument] = useState(null)

  const selectedDocType = DOCUMENT_TYPES.find(type => type.value === selectedType)

  const handleTypeSelection = (type) => {
    setSelectedType(type)
    setFormData(prev => ({
      ...prev,
      type: type,
      title: `${DOCUMENT_TYPES.find(t => t.value === type)?.label} - ${new Date().toLocaleDateString()}`,
      variables: {}
    }))
  }

  const handleVariableChange = (variable, value) => {
    setFormData(prev => ({
      ...prev,
      variables: { ...prev.variables, [variable]: value }
    }))
  }

  const getRecommendedAgent = () => {
    if (!selectedDocType) return null
    
    // AI logic to recommend best agent for document type
    const recommendations = {
      'proposal': agents?.find(a => a.type?.includes('Sales') || a.type?.includes('Marketing')),
      'invoice': agents?.find(a => a.type?.includes('Sales') || a.type?.includes('Process')),
      'business_plan': agents?.find(a => a.type?.includes('Data') || a.type?.includes('Analytics')),
      'report': agents?.find(a => a.type?.includes('Data') || a.type?.includes('Analytics')),
      'contract': agents?.find(a => a.type?.includes('Process') || a.type?.includes('Sales')),
      'marketing': agents?.find(a => a.type?.includes('Marketing') || a.type?.includes('Design'))
    }
    
    return recommendations[selectedType] || agents?.[0]
  }

  const handleGenerate = async () => {
    if (!selectedType || !formData.title) {
      alert('Please fill in all required fields')
      return
    }

    setIsGenerating(true)

    try {
      // Get the recommended agent or use selected agent
      const recommendedAgent = getRecommendedAgent()
      const agentId = formData.agent_id === 'auto_select' ? recommendedAgent?.id : formData.agent_id

      // First, generate content using AI agent chat
      let documentContent = ''
      
      if (agentId) {
        const prompt = `Generate a professional ${selectedDocType.label.toLowerCase()} with the following details:
        
Title: ${formData.title}
Client: ${formData.client_name || 'Valued Client'}

Variables:
${Object.entries(formData.variables).map(([key, value]) => `${key}: ${value}`).join('\n')}

Additional Instructions: ${formData.custom_instructions}

Please create a comprehensive, professional document that follows industry standards.`

        const chatResponse = await axios.post(`${API}/ai-chat/chat`, {
          agent_id: agentId,
          message: prompt
        })
        
        documentContent = chatResponse.data.response
      }

      // Save the generated document
      const documentData = {
        title: formData.title,
        type: selectedType,
        client_name: formData.client_name,
        variables: formData.variables,
        agent_id: agentId,
        custom_instructions: formData.custom_instructions
      }

      const response = await axios.post(`${API}/documents/generate`, documentData)
      
      // Update the response with AI-generated content
      const finalDocument = {
        ...response.data,
        content: documentContent || response.data.content
      }
      
      setGeneratedDocument(finalDocument)
      
      if (onDocumentGenerated) {
        onDocumentGenerated(finalDocument)
      }

      console.log('Document generated successfully:', finalDocument)

    } catch (error) {
      console.error('Error generating document:', error)
      alert('Failed to generate document. Please try again.')
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = () => {
    if (generatedDocument?.content) {
      navigator.clipboard.writeText(generatedDocument.content)
      alert('Document content copied to clipboard!')
    }
  }

  const downloadDocument = () => {
    if (generatedDocument?.content) {
      const blob = new Blob([generatedDocument.content], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${generatedDocument.title}.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  const resetForm = () => {
    setSelectedType('')
    setFormData({
      title: '',
      type: '',
      client_name: '',
      agent_id: 'auto_select',
      custom_instructions: '',
      variables: {}
    })
    setGeneratedDocument(null)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent 
        className="sm:max-w-4xl w-[95vw] max-h-[85vh] h-[700px] flex flex-col quantum-bg border border-primary/20 shadow-2xl"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          maxHeight: '90vh'
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-3">
            <Wand2 className="w-6 h-6 text-primary" />
            <span className="gradient-text">AI Document Generation</span>
          </DialogTitle>
          <DialogDescription>
            Generate professional business documents with AI-powered content creation
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto">
          {!selectedType ? (
            /* Document Type Selection */
            <div className="space-y-6">
              <div className="text-center">
                <h3 className="text-lg font-semibold mb-2">Choose Document Type</h3>
                <p className="text-sm text-muted-foreground">Select the type of document you want to generate</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {DOCUMENT_TYPES.map((docType) => (
                  <Card 
                    key={docType.value}
                    className="quantum-bg cursor-pointer hover:border-primary/50 transition-all duration-300 hover:scale-105 glow-effect"
                    onClick={() => handleTypeSelection(docType.value)}
                  >
                    <CardContent className="p-6 text-center">
                      <docType.icon className={`w-12 h-12 mx-auto mb-4 ${docType.color}`} />
                      <h3 className="font-semibold mb-2">{docType.label}</h3>
                      <p className="text-sm text-muted-foreground">{docType.description}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : !generatedDocument ? (
            /* Document Configuration Form */
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <selectedDocType.icon className={`w-6 h-6 ${selectedDocType.color}`} />
                  <div>
                    <h3 className="text-lg font-semibold">{selectedDocType.label}</h3>
                    <p className="text-sm text-muted-foreground">{selectedDocType.description}</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" onClick={resetForm}>
                  Back to Types
                </Button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Basic Information */}
                <Card className="quantum-bg">
                  <CardHeader>
                    <CardTitle className="text-base">Document Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="doc_title">Document Title *</Label>
                      <Input
                        id="doc_title"
                        value={formData.title}
                        onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="Enter document title"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="client_name">Client/Company Name</Label>
                      <Input
                        id="client_name"
                        value={formData.client_name}
                        onChange={(e) => setFormData(prev => ({ ...prev, client_name: e.target.value }))}
                        placeholder="Enter client or company name"
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="assigned_agent">AI Agent</Label>
                      <Select 
                        value={formData.agent_id} 
                        onValueChange={(value) => setFormData(prev => ({ ...prev, agent_id: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="auto_select">
                            <div className="flex items-center gap-2">
                              <Sparkles className="w-4 h-4" />
                              Auto-select best agent
                            </div>
                          </SelectItem>
                          {agents?.map((agent) => (
                            <SelectItem key={agent.id} value={agent.id}>
                              <div className="flex items-center gap-2">
                                <Bot className="w-4 h-4" />
                                {agent.name} - {agent.type}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {formData.agent_id === 'auto_select' && getRecommendedAgent() && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Recommended: {getRecommendedAgent().name} ({getRecommendedAgent().type})
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* Dynamic Variables */}
                <Card className="quantum-bg">
                  <CardHeader>
                    <CardTitle className="text-base">Content Variables</CardTitle>
                    <CardDescription>Customize the document content</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {selectedDocType.variables.map((variable) => (
                      <div key={variable}>
                        <Label htmlFor={variable} className="capitalize">
                          {variable.replace('_', ' ')}
                        </Label>
                        {['description', 'summary', 'instructions', 'details'].some(keyword => 
                          variable.includes(keyword)) ? (
                          <Textarea
                            id={variable}
                            value={formData.variables[variable] || ''}
                            onChange={(e) => handleVariableChange(variable, e.target.value)}
                            placeholder={`Enter ${variable.replace('_', ' ')}`}
                            rows={3}
                          />
                        ) : (
                          <Input
                            id={variable}
                            value={formData.variables[variable] || ''}
                            onChange={(e) => handleVariableChange(variable, e.target.value)}
                            placeholder={`Enter ${variable.replace('_', ' ')}`}
                          />
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>

              {/* Custom Instructions */}
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="text-base">Additional Instructions</CardTitle>
                  <CardDescription>Any specific requirements or formatting preferences</CardDescription>
                </CardHeader>
                <CardContent>
                  <Textarea
                    value={formData.custom_instructions}
                    onChange={(e) => setFormData(prev => ({ ...prev, custom_instructions: e.target.value }))}
                    placeholder="Enter any specific instructions for the AI agent..."
                    rows={3}
                  />
                </CardContent>
              </Card>
            </div>
          ) : (
            /* Generated Document Display */
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileCheck className="w-6 h-6 text-green-400" />
                  <div>
                    <h3 className="text-lg font-semibold">Document Generated Successfully!</h3>
                    <p className="text-sm text-muted-foreground">{generatedDocument.title}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={copyToClipboard}>
                    <Copy className="w-4 h-4 mr-2" />
                    Copy
                  </Button>
                  <Button variant="outline" size="sm" onClick={downloadDocument}>
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                  <Button variant="outline" size="sm" onClick={resetForm}>
                    Generate New
                  </Button>
                </div>
              </div>

              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="text-base">Generated Content</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted/20 p-4 rounded-lg max-h-96 overflow-y-auto">
                    <pre className="whitespace-pre-wrap text-sm font-mono">
                      {generatedDocument.content}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-2 pt-4 border-t border-border flex-shrink-0">
          <Button 
            variant="outline" 
            onClick={() => setIsOpen(false)}
            disabled={isGenerating}
          >
            {generatedDocument ? 'Close' : 'Cancel'}
          </Button>
          {selectedType && !generatedDocument && (
            <Button 
              onClick={handleGenerate}
              disabled={isGenerating || !formData.title}
              className="glow-effect"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4 mr-2" />
                  Generate Document
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}