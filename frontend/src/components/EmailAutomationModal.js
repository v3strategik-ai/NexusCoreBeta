import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Textarea } from './ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
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
  Mail, 
  Send, 
  Users, 
  Target,
  Clock,
  Zap,
  BarChart3,
  Settings,
  Loader2,
  CheckCircle,
  AlertCircle,
  Calendar,
  Filter
} from 'lucide-react'
import axios from 'axios'

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL
const API = `${BACKEND_URL}/api`

const EMAIL_TEMPLATES = [
  { key: 'lead_welcome', name: 'Lead Welcome', description: 'Welcome new leads with professional introduction' },
  { key: 'lead_followup', name: 'Lead Follow-up', description: 'Follow up with warm leads to maintain engagement' },
  { key: 'lead_proposal', name: 'Proposal Ready', description: 'Notify leads when their custom proposal is ready' }
]

const TRIGGER_TYPES = [
  { value: 'lead_status_change', label: 'Lead Status Change', icon: Target },
  { value: 'time_based', label: 'Time-Based', icon: Clock },
  { value: 'manual', label: 'Manual Send', icon: Send }
]

const LEAD_STATUSES = ['cold', 'warm', 'hot', 'converted', 'lost']

export function EmailAutomationModal({ children, leads, onEmailSent }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('send')
  const [templates, setTemplates] = useState(EMAIL_TEMPLATES)
  const [stats, setStats] = useState(null)
  
  const [singleEmailForm, setSingleEmailForm] = useState({
    lead_id: '',
    template_key: 'lead_welcome',
    additional_context: {}
  })
  
  const [bulkEmailForm, setBulkEmailForm] = useState({
    lead_ids: [],
    template_key: 'lead_welcome',
    filter_by_status: '',
    additional_context: {}
  })
  
  const [automationForm, setAutomationForm] = useState({
    trigger_type: 'lead_status_change',
    conditions: {
      from_status: 'cold',
      to_status: 'warm'
    },
    email_template: 'lead_welcome',
    delay_hours: 0
  })

  useEffect(() => {
    if (isOpen) {
      loadEmailStats()
    }
  }, [isOpen])

  const loadEmailStats = async () => {
    try {
      const response = await axios.get(`${API}/email/stats`)
      setStats(response.data)
    } catch (error) {
      console.error('Error loading email stats:', error)
    }
  }

  const handleSingleEmailSend = async () => {
    if (!singleEmailForm.lead_id || !singleEmailForm.template_key) {
      alert('Please select a lead and template')
      return
    }

    setIsLoading(true)
    
    try {
      const response = await axios.post(`${API}/email/send-to-lead`, singleEmailForm)
      
      console.log('Email sent:', response.data)
      alert('Email sent successfully!')
      
      if (onEmailSent) {
        onEmailSent({
          type: 'single',
          lead_id: singleEmailForm.lead_id,
          template: singleEmailForm.template_key
        })
      }
      
      // Reset form
      setSingleEmailForm({
        lead_id: '',
        template_key: 'lead_welcome',
        additional_context: {}
      })
      
    } catch (error) {
      console.error('Error sending email:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to send email. Please try again.'
      alert(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleBulkEmailSend = async () => {
    let selectedLeadIds = bulkEmailForm.lead_ids

    // Filter leads by status if specified
    if (bulkEmailForm.filter_by_status) {
      const filteredLeads = leads.filter(lead => lead.status === bulkEmailForm.filter_by_status)
      selectedLeadIds = filteredLeads.map(lead => lead.id)
    }

    if (selectedLeadIds.length === 0) {
      alert('Please select leads or apply a status filter')
      return
    }

    setIsLoading(true)
    
    try {
      const response = await axios.post(`${API}/email/bulk-send`, {
        lead_ids: selectedLeadIds,
        template_key: bulkEmailForm.template_key,
        additional_context: bulkEmailForm.additional_context
      })
      
      console.log('Bulk emails sent:', response.data)
      alert(`Bulk email sent to ${response.data.count} leads successfully!`)
      
      if (onEmailSent) {
        onEmailSent({
          type: 'bulk',
          count: response.data.count,
          template: bulkEmailForm.template_key
        })
      }
      
      // Reset form
      setBulkEmailForm({
        lead_ids: [],
        template_key: 'lead_welcome',
        filter_by_status: '',
        additional_context: {}
      })
      
    } catch (error) {
      console.error('Error sending bulk emails:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to send bulk emails. Please try again.'
      alert(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAutomationSetup = async () => {
    setIsLoading(true)
    
    try {
      const response = await axios.post(`${API}/email/automation/setup`, automationForm)
      
      console.log('Automation setup:', response.data)
      alert('Email automation configured successfully!')
      
      // Reset form
      setAutomationForm({
        trigger_type: 'lead_status_change',
        conditions: {
          from_status: 'cold',
          to_status: 'warm'
        },
        email_template: 'lead_welcome',
        delay_hours: 0
      })
      
    } catch (error) {
      console.error('Error setting up automation:', error)
      const errorMessage = error.response?.data?.detail || 'Failed to setup automation. Please try again.'
      alert(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const getLeadById = (leadId) => {
    return leads.find(lead => lead.id === leadId)
  }

  const getStatusColor = (status) => {
    const colors = {
      cold: 'text-blue-400',
      warm: 'text-yellow-400', 
      hot: 'text-red-400',
      converted: 'text-green-400',
      lost: 'text-gray-400'
    }
    return colors[status] || 'text-gray-400'
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent 
        className="sm:max-w-4xl w-[95vw] h-[80vh] max-h-[700px] flex flex-col quantum-bg border border-primary/20 shadow-2xl"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          maxHeight: '85vh'
        }}
      >
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-3">
            <Mail className="w-6 h-6 text-primary" />
            <div>
              <span className="gradient-text">Email Automation Center</span>
              <div className="text-sm text-muted-foreground font-normal mt-1">
                Automated email campaigns and lead communication
              </div>
            </div>
          </DialogTitle>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
          <TabsList className="grid w-full grid-cols-4 mb-4">
            <TabsTrigger value="send" className="flex items-center gap-2">
              <Send className="w-4 h-4" />
              Send Emails
            </TabsTrigger>
            <TabsTrigger value="bulk" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Bulk Send
            </TabsTrigger>
            <TabsTrigger value="automation" className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Automation
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Analytics
            </TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-y-auto">
            {/* Send Single Email Tab */}
            <TabsContent value="send" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Send className="w-5 h-5" />
                    Send Email to Lead
                  </CardTitle>
                  <CardDescription>Send personalized emails to individual leads</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="lead-select">Select Lead</Label>
                      <Select value={singleEmailForm.lead_id} onValueChange={(value) => setSingleEmailForm(prev => ({...prev, lead_id: value}))}>
                        <SelectTrigger>
                          <SelectValue placeholder="Choose a lead" />
                        </SelectTrigger>
                        <SelectContent>
                          {leads.map((lead) => (
                            <SelectItem key={lead.id} value={lead.id}>
                              <div className="flex flex-col">
                                <span>{lead.name} - {lead.company || 'No Company'}</span>
                                <span className="text-xs text-muted-foreground">{lead.email}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="template-select">Email Template</Label>
                      <Select value={singleEmailForm.template_key} onValueChange={(value) => setSingleEmailForm(prev => ({...prev, template_key: value}))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {templates.map((template) => (
                            <SelectItem key={template.key} value={template.key}>
                              <div className="flex flex-col">
                                <span>{template.name}</span>
                                <span className="text-xs text-muted-foreground">{template.description}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {singleEmailForm.lead_id && (
                    <div className="p-4 border border-primary/20 rounded-lg quantum-bg">
                      <h4 className="font-semibold mb-2">Lead Preview</h4>
                      {(() => {
                        const lead = getLeadById(singleEmailForm.lead_id)
                        return lead ? (
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div><span className="text-muted-foreground">Name:</span> <span className="font-medium">{lead.name}</span></div>
                            <div><span className="text-muted-foreground">Email:</span> <span className="font-medium">{lead.email}</span></div>
                            <div><span className="text-muted-foreground">Company:</span> <span className="font-medium">{lead.company || 'N/A'}</span></div>
                            <div><span className="text-muted-foreground">Status:</span> <span className={`font-medium ${getStatusColor(lead.status)}`}>{lead.status.toUpperCase()}</span></div>
                            <div><span className="text-muted-foreground">Value:</span> <span className="font-medium">${lead.value?.toLocaleString() || '0'}</span></div>
                            <div><span className="text-muted-foreground">Source:</span> <span className="font-medium">{lead.source || 'N/A'}</span></div>
                          </div>
                        ) : null
                      })()}
                    </div>
                  )}

                  <Button 
                    onClick={handleSingleEmailSend}
                    disabled={isLoading || !singleEmailForm.lead_id}
                    className="w-full glow-effect"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Send Email
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Bulk Email Tab */}
            <TabsContent value="bulk" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Bulk Email Campaign
                  </CardTitle>
                  <CardDescription>Send emails to multiple leads at once</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="bulk-template">Email Template</Label>
                      <Select value={bulkEmailForm.template_key} onValueChange={(value) => setBulkEmailForm(prev => ({...prev, template_key: value}))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {templates.map((template) => (
                            <SelectItem key={template.key} value={template.key}>
                              <div className="flex flex-col">
                                <span>{template.name}</span>
                                <span className="text-xs text-muted-foreground">{template.description}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="status-filter">Filter by Status</Label>
                      <Select value={bulkEmailForm.filter_by_status} onValueChange={(value) => setBulkEmailForm(prev => ({...prev, filter_by_status: value}))}>
                        <SelectTrigger>
                          <SelectValue placeholder="All leads" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">All leads</SelectItem>
                          {LEAD_STATUSES.map((status) => (
                            <SelectItem key={status} value={status}>
                              <span className={getStatusColor(status)}>
                                {status.toUpperCase()}
                              </span>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="p-4 border border-primary/20 rounded-lg quantum-bg">
                    <h4 className="font-semibold mb-2">Target Audience</h4>
                    <div className="text-sm text-muted-foreground">
                      {bulkEmailForm.filter_by_status ? (
                        <span>
                          Sending to all <span className={`font-medium ${getStatusColor(bulkEmailForm.filter_by_status)}`}>
                            {bulkEmailForm.filter_by_status.toUpperCase()}
                          </span> leads: {leads.filter(lead => lead.status === bulkEmailForm.filter_by_status).length} recipients
                        </span>
                      ) : (
                        <span>Sending to all leads: {leads.length} recipients</span>
                      )}
                    </div>
                  </div>

                  <Button 
                    onClick={handleBulkEmailSend}
                    disabled={isLoading || leads.length === 0}
                    className="w-full glow-effect"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>
                        <Users className="w-4 h-4 mr-2" />
                        Send Bulk Email
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Automation Tab */}
            <TabsContent value="automation" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Zap className="w-5 h-5" />
                    Email Automation Rules
                  </CardTitle>
                  <CardDescription>Set up automated email triggers and workflows</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="trigger-type">Trigger Type</Label>
                    <Select value={automationForm.trigger_type} onValueChange={(value) => setAutomationForm(prev => ({...prev, trigger_type: value}))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {TRIGGER_TYPES.map((trigger) => (
                          <SelectItem key={trigger.value} value={trigger.value}>
                            <div className="flex items-center gap-2">
                              <trigger.icon className="w-4 h-4" />
                              {trigger.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {automationForm.trigger_type === 'lead_status_change' && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>From Status</Label>
                        <Select value={automationForm.conditions.from_status} onValueChange={(value) => setAutomationForm(prev => ({...prev, conditions: {...prev.conditions, from_status: value}}))}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {LEAD_STATUSES.map((status) => (
                              <SelectItem key={status} value={status}>
                                <span className={getStatusColor(status)}>
                                  {status.toUpperCase()}
                                </span>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label>To Status</Label>
                        <Select value={automationForm.conditions.to_status} onValueChange={(value) => setAutomationForm(prev => ({...prev, conditions: {...prev.conditions, to_status: value}}))}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {LEAD_STATUSES.map((status) => (
                              <SelectItem key={status} value={status}>
                                <span className={getStatusColor(status)}>
                                  {status.toUpperCase()}
                                </span>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="email-template">Email Template</Label>
                      <Select value={automationForm.email_template} onValueChange={(value) => setAutomationForm(prev => ({...prev, email_template: value}))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {templates.map((template) => (
                            <SelectItem key={template.key} value={template.key}>
                              {template.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="delay">Delay (hours)</Label>
                      <Input
                        type="number"
                        value={automationForm.delay_hours}
                        onChange={(e) => setAutomationForm(prev => ({...prev, delay_hours: parseInt(e.target.value) || 0}))}
                        min="0"
                        max="168"
                      />
                    </div>
                  </div>

                  <div className="p-4 border border-primary/20 rounded-lg quantum-bg">
                    <h4 className="font-semibold mb-2">Automation Summary</h4>
                    <div className="text-sm text-muted-foreground">
                      When a lead changes from <span className={`font-medium ${getStatusColor(automationForm.conditions.from_status)}`}>
                        {automationForm.conditions.from_status?.toUpperCase()}
                      </span> to <span className={`font-medium ${getStatusColor(automationForm.conditions.to_status)}`}>
                        {automationForm.conditions.to_status?.toUpperCase()}
                      </span>, send "{templates.find(t => t.key === automationForm.email_template)?.name}" email
                      {automationForm.delay_hours > 0 && ` after ${automationForm.delay_hours} hours delay`}.
                    </div>
                  </div>

                  <Button 
                    onClick={handleAutomationSetup}
                    disabled={isLoading}
                    className="w-full glow-effect"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Setting up...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 mr-2" />
                        Setup Automation
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Analytics Tab */}
            <TabsContent value="analytics" className="space-y-6">
              <Card className="quantum-bg">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    Email Performance Analytics
                  </CardTitle>
                  <CardDescription>Track email campaign performance and engagement</CardDescription>
                </CardHeader>
                <CardContent>
                  {stats ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">{stats.total_sent}</div>
                        <div className="text-sm text-muted-foreground">Total Sent</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">{stats.delivery_rate}%</div>
                        <div className="text-sm text-muted-foreground">Delivery Rate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">{stats.open_rate}%</div>
                        <div className="text-sm text-muted-foreground">Open Rate</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-400">{stats.click_rate}%</div>
                        <div className="text-sm text-muted-foreground">Click Rate</div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-muted-foreground">
                      Loading analytics...
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </div>
        </Tabs>

        {/* Close Button */}
        <div className="flex justify-end pt-4 border-t border-border flex-shrink-0">
          <Button 
            variant="outline" 
            onClick={() => setIsOpen(false)}
            disabled={isLoading}
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}