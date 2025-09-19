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
  Mail, 
  Phone,
  Loader2,
  Send,
  MessageSquare,
  Calendar
} from 'lucide-react'

const CONTACT_METHODS = [
  { value: 'email', label: 'Email', icon: Mail },
  { value: 'phone', label: 'Phone Call', icon: Phone },
  { value: 'meeting', label: 'Schedule Meeting', icon: Calendar },
  { value: 'message', label: 'Direct Message', icon: MessageSquare }
]

const EMAIL_TEMPLATES = [
  {
    name: 'Introduction',
    subject: 'Introduction - Nexus Core Solutions',
    body: `Hi {name},

I hope this email finds you well. I'm reaching out from Nexus Core Solutions to introduce our AI-powered business automation platform.

Based on your company profile, I believe our solutions could help {company} streamline operations and increase efficiency by up to 40%.

Would you be interested in a brief 15-minute call to discuss how we can help {company} achieve its automation goals?

Best regards,
[Your Name]
Nexus Core Solutions`
  },
  {
    name: 'Follow-up',
    subject: 'Following up on our conversation',
    body: `Hi {name},

Thank you for taking the time to speak with me about {company}'s automation needs.

As discussed, I'm attaching some information about our AI-powered solutions that could address the challenges you mentioned.

I'd love to schedule a demo to show you how our platform can specifically benefit {company}.

Please let me know your availability for next week.

Best regards,
[Your Name]
Nexus Core Solutions`
  },
  {
    name: 'Proposal Follow-up',
    subject: 'Proposal for {company} - Next Steps',
    body: `Hi {name},

I wanted to follow up on the proposal I sent for {company}'s digital transformation project.

The solution we've outlined could deliver significant ROI within the first 6 months of implementation.

Do you have any questions about the proposal? I'm happy to discuss any aspects in detail.

Would you like to schedule a call to move forward with the next steps?

Best regards,
[Your Name]
Nexus Core Solutions`
  }
]

export function ContactLeadModal({ children, lead, onContactLogged }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [contactMethod, setContactMethod] = useState('email')
  const [formData, setFormData] = useState({
    subject: '',
    message: '',
    template: '',
    scheduledTime: '',
    notes: ''
  })

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleTemplateChange = (templateName) => {
    const template = EMAIL_TEMPLATES.find(t => t.name === templateName)
    if (template) {
      const processedSubject = template.subject
        .replace('{name}', lead.name)
        .replace('{company}', lead.company || 'your company')
      
      const processedBody = template.body
        .replace(/{name}/g, lead.name)
        .replace(/{company}/g, lead.company || 'your company')
      
      setFormData(prev => ({
        ...prev,
        template: templateName,
        subject: processedSubject,
        message: processedBody
      }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (contactMethod === 'email' && (!formData.subject || !formData.message)) {
      alert('Please fill in subject and message for email contact')
      return
    }

    setIsLoading(true)

    try {
      // In a real implementation, this would:
      // 1. Send the actual email/make the call/schedule meeting
      // 2. Log the contact activity in the CRM
      // 3. Update lead's last_contact timestamp
      
      // For now, we'll simulate the contact logging
      const contactActivity = {
        lead_id: lead.id,
        contact_method: contactMethod,
        subject: formData.subject,
        message: formData.message,
        scheduled_time: formData.scheduledTime,
        notes: formData.notes,
        timestamp: new Date().toISOString()
      }

      console.log('Contact activity logged:', contactActivity)
      
      // Show success message based on contact method
      let successMessage = ''
      switch (contactMethod) {
        case 'email':
          successMessage = `Email sent to ${lead.name} at ${lead.email}`
          break
        case 'phone':
          successMessage = `Phone call logged for ${lead.name} (${lead.phone || 'No phone number'})`
          break
        case 'meeting':
          successMessage = `Meeting scheduled with ${lead.name} for ${formData.scheduledTime}`
          break
        case 'message':
          successMessage = `Direct message sent to ${lead.name}`
          break
        default:
          successMessage = `Contact activity logged for ${lead.name}`
      }

      alert(successMessage)
      
      // Reset form
      setFormData({
        subject: '',
        message: '',
        template: '',
        scheduledTime: '',
        notes: ''
      })
      
      // Close modal
      setIsOpen(false)
      
      // Notify parent component
      if (onContactLogged) {
        onContactLogged(contactActivity)
      }

    } catch (error) {
      console.error('Error logging contact activity:', error)
      alert('Failed to log contact activity. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const getContactMethodIcon = (method) => {
    const methodObj = CONTACT_METHODS.find(m => m.value === method)
    return methodObj?.icon || Mail
  }

  const ContactIcon = getContactMethodIcon(contactMethod)

  if (!lead) return null

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
            <ContactIcon className="w-6 h-6 text-primary" />
            <span className="gradient-text">Contact: {lead.name}</span>
          </DialogTitle>
          <DialogDescription>
            Reach out to {lead.name} at {lead.company || 'their company'} and log the interaction.
          </DialogDescription>
        </DialogHeader>

        {/* Lead Info Banner */}
        <div className="p-4 border border-primary/20 rounded-lg quantum-bg mb-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Email:</span>
              <span className="ml-2 font-medium">{lead.email}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Phone:</span>
              <span className="ml-2 font-medium">{lead.phone || 'Not provided'}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Company:</span>
              <span className="ml-2 font-medium">{lead.company || 'Not specified'}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Status:</span>
              <span className="ml-2 font-medium capitalize">{lead.status}</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Contact Method Selection */}
          <div className="space-y-2">
            <Label htmlFor="method">Contact Method</Label>
            <Select value={contactMethod} onValueChange={setContactMethod}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CONTACT_METHODS.map((method) => (
                  <SelectItem key={method.value} value={method.value}>
                    <div className="flex items-center gap-2">
                      <method.icon className="w-4 h-4" />
                      {method.label}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Email-specific fields */}
          {contactMethod === 'email' && (
            <>
              {/* Email Template Selection */}
              <div className="space-y-2">
                <Label htmlFor="template">Email Template (Optional)</Label>
                <Select value={formData.template} onValueChange={handleTemplateChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a template or write custom email" />
                  </SelectTrigger>
                  <SelectContent>
                    {EMAIL_TEMPLATES.map((template) => (
                      <SelectItem key={template.name} value={template.name}>
                        {template.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Email Subject */}
              <div className="space-y-2">
                <Label htmlFor="subject">Subject *</Label>
                <Input
                  id="subject"
                  placeholder="Email subject"
                  value={formData.subject}
                  onChange={(e) => handleInputChange('subject', e.target.value)}
                  required
                />
              </div>

              {/* Email Message */}
              <div className="space-y-2">
                <Label htmlFor="message">Message *</Label>
                <Textarea
                  id="message"
                  placeholder="Email message content..."
                  value={formData.message}
                  onChange={(e) => handleInputChange('message', e.target.value)}
                  rows={8}
                  required
                />
              </div>
            </>
          )}

          {/* Meeting-specific fields */}
          {contactMethod === 'meeting' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="scheduledTime">Scheduled Time</Label>
                <Input
                  id="scheduledTime"
                  type="datetime-local"
                  value={formData.scheduledTime}
                  onChange={(e) => handleInputChange('scheduledTime', e.target.value)}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="message">Meeting Agenda</Label>
                <Textarea
                  id="message"
                  placeholder="Meeting topics and agenda..."
                  value={formData.message}
                  onChange={(e) => handleInputChange('message', e.target.value)}
                  rows={4}
                />
              </div>
            </>
          )}

          {/* Phone/Message fields */}
          {(contactMethod === 'phone' || contactMethod === 'message') && (
            <div className="space-y-2">
              <Label htmlFor="message">
                {contactMethod === 'phone' ? 'Call Notes' : 'Message Content'}
              </Label>
              <Textarea
                id="message"
                placeholder={
                  contactMethod === 'phone' 
                    ? "Call agenda, talking points, or call summary..." 
                    : "Direct message content..."
                }
                value={formData.message}
                onChange={(e) => handleInputChange('message', e.target.value)}
                rows={4}
              />
            </div>
          )}

          {/* Additional Notes */}
          <div className="space-y-2">
            <Label htmlFor="notes">Additional Notes</Label>
            <Textarea
              id="notes"
              placeholder="Any additional notes about this contact attempt..."
              value={formData.notes}
              onChange={(e) => handleInputChange('notes', e.target.value)}
              rows={2}
            />
          </div>

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
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  {contactMethod === 'email' ? 'Send Email' : 
                   contactMethod === 'phone' ? 'Log Call' :
                   contactMethod === 'meeting' ? 'Schedule Meeting' : 'Send Message'}
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}