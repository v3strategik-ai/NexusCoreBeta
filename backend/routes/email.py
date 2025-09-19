from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Subject

from models import (
    Lead, Agent, GeneratedDocument
)
from database import get_leads_collection, get_agents_collection, get_activities_collection

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/email", tags=["email"])
logger = logging.getLogger(__name__)

# Email Templates
EMAIL_TEMPLATES = {
    "lead_welcome": {
        "name": "Lead Welcome",
        "subject": "Welcome to Nexus Core - Your AI Business Automation Partner",
        "html_content": """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">Welcome to Nexus Core!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your AI Business Automation Journey Begins</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Hello {name}!</h2>
                    
                    <p style="color: #555; line-height: 1.6;">Thank you for your interest in Nexus Core's AI Business Automation Platform. We're excited to help {company} streamline operations and boost productivity with intelligent automation.</p>
                    
                    <h3 style="color: #667eea; margin-top: 25px;">What's Next?</h3>
                    <ul style="color: #555; line-height: 1.8;">
                        <li><strong>Consultation Call:</strong> Our team will reach out within 24 hours to schedule a personalized demo</li>
                        <li><strong>Custom Solution:</strong> We'll design an AI automation strategy tailored to your business needs</li>
                        <li><strong>Implementation:</strong> Get up and running with your digital workforce in just weeks</li>
                    </ul>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #667eea;">
                        <h4 style="margin: 0 0 10px 0; color: #333;">Your Potential ROI</h4>
                        <p style="margin: 0; color: #555;">Based on your project value of <strong>${value:,}</strong>, our AI automation typically delivers 3-5x ROI within the first year.</p>
                    </div>
                    
                    <p style="color: #555; line-height: 1.6;">Questions? Reply to this email or call us at <strong>+1 (555) 123-4567</strong>.</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="https://nexuscore.ai/demo" style="background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Schedule Your Demo</a>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #888; font-size: 12px;">
                    <p>Nexus Core Solutions | AI Business Automation Platform</p>
                    <p>You received this email because you expressed interest in our AI automation services.</p>
                </div>
            </body>
        </html>
        """
    },
    
    "lead_followup": {
        "name": "Lead Follow-up",
        "subject": "Following up on your AI automation inquiry - Next Steps",
        "html_content": """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">Let's Continue Your AI Journey</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Hi {name},</h2>
                    
                    <p style="color: #555; line-height: 1.6;">I hope this email finds you well. I wanted to follow up on your recent inquiry about AI business automation for {company}.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #f5576c;">
                        <h4 style="margin: 0 0 15px 0; color: #333;">Quick Recap of Your Project:</h4>
                        <ul style="margin: 0; color: #555; line-height: 1.6;">
                            <li><strong>Company:</strong> {company}</li>
                            <li><strong>Project Value:</strong> ${value:,}</li>
                            <li><strong>Status:</strong> {status}</li>
                            <li><strong>Source:</strong> {source}</li>
                        </ul>
                    </div>
                    
                    <h3 style="color: #f5576c; margin-top: 25px;">Why Act Now?</h3>
                    <ul style="color: #555; line-height: 1.8;">
                        <li><strong>Limited Availability:</strong> Our Q1 implementation slots are filling up fast</li>
                        <li><strong>Special Pricing:</strong> Lock in early-adopter rates before they increase</li>
                        <li><strong>Competitive Advantage:</strong> Be first in your industry with advanced AI automation</li>
                    </ul>
                    
                    <p style="color: #555; line-height: 1.6;">I have some time available this week for a 15-minute call to discuss your specific automation needs. Would you prefer:</p>
                    
                    <div style="text-align: center; margin: 25px 0;">
                        <a href="https://nexuscore.ai/schedule-call" style="background: #f5576c; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin: 0 10px;">Schedule Call</a>
                        <a href="https://nexuscore.ai/demo" style="background: transparent; color: #f5576c; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; border: 2px solid #f5576c; margin: 0 10px;">Watch Demo</a>
                    </div>
                    
                    <p style="color: #555; line-height: 1.6;">Best regards,<br><strong>Your Nexus Core Team</strong></p>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #888; font-size: 12px;">
                    <p>Nexus Core Solutions | AI Business Automation Platform</p>
                </div>
            </body>
        </html>
        """
    },
    
    "lead_proposal": {
        "name": "Proposal Ready",
        "subject": "Your Custom AI Automation Proposal is Ready - {company}",
        "html_content": """
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🎉 Your Proposal is Ready!</h1>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
                    <h2 style="color: #333; margin-top: 0;">Exciting news, {name}!</h2>
                    
                    <p style="color: #555; line-height: 1.6;">We've completed the custom AI automation proposal for {company}. Our team has carefully analyzed your requirements and designed a solution that will transform your business operations.</p>
                    
                    <div style="background: white; padding: 25px; border-radius: 8px; margin: 25px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h3 style="margin: 0 0 15px 0; color: #4facfe; text-align: center;">Proposal Highlights</h3>
                        <div style="display: flex; justify-content: space-around; text-align: center;">
                            <div>
                                <div style="font-size: 24px; font-weight: bold; color: #333;">${value:,}</div>
                                <div style="color: #666; font-size: 14px;">Project Investment</div>
                            </div>
                            <div>
                                <div style="font-size: 24px; font-weight: bold; color: #333;">12-16</div>
                                <div style="color: #666; font-size: 14px;">Weeks Timeline</div>
                            </div>
                            <div>
                                <div style="font-size: 24px; font-weight: bold; color: #333;">300%+</div>
                                <div style="color: #666; font-size: 14px;">Expected ROI</div>
                            </div>
                        </div>
                    </div>
                    
                    <h3 style="color: #4facfe; margin-top: 25px;">What's Included:</h3>
                    <ul style="color: #555; line-height: 1.8;">
                        <li><strong>AI Digital Employees:</strong> Custom-trained agents for your specific workflows</li>
                        <li><strong>Automation Workflows:</strong> End-to-end process automation</li>
                        <li><strong>CRM Integration:</strong> Intelligent lead management and scoring</li>
                        <li><strong>Document Generation:</strong> Automated proposal, contract, and report creation</li>
                        <li><strong>Analytics Dashboard:</strong> Real-time performance monitoring</li>
                    </ul>
                    
                    <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #4facfe;">
                        <h4 style="margin: 0 0 10px 0; color: #333;">⏰ Limited Time Offer</h4>
                        <p style="margin: 0; color: #555;">Sign by month-end and receive <strong>20% off implementation</strong> plus 3 months of free premium support!</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://nexuscore.ai/proposal/{lead_id}" style="background: #4facfe; color: white; padding: 15px 35px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">View Full Proposal</a>
                    </div>
                    
                    <p style="color: #555; line-height: 1.6;">Ready to discuss the next steps? I'm available for a call this week to walk through the proposal and answer any questions.</p>
                    
                    <p style="color: #555; line-height: 1.6;">Best regards,<br><strong>Your Nexus Core Implementation Team</strong></p>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #888; font-size: 12px;">
                    <p>Nexus Core Solutions | AI Business Automation Platform</p>
                </div>
            </body>
        </html>
        """
    }
}

class EmailService:
    """Email service using SendGrid for automated business communications"""
    
    def __init__(self):
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@nexuscore.ai')
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not found in environment variables")
        
        self.sg = SendGridAPIClient(self.api_key) if self.api_key else None
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """Send email using SendGrid"""
        
        if not self.sg:
            logger.error("SendGrid not configured - missing API key")
            return False
        
        try:
            # Create the email
            from_email_obj = Email(
                email=from_email or self.sender_email,
                name=from_name or "Nexus Core Team"
            )
            to_email_obj = To(to_email)
            subject_obj = Subject(subject)
            content_obj = Content("text/html", html_content)
            
            mail = Mail(from_email_obj, to_email_obj, subject_obj, content_obj)
            
            # Send the email
            response = self.sg.send(mail)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    async def send_lead_email(
        self, 
        lead: Lead, 
        template_key: str, 
        additional_context: Dict[str, Any] = None
    ) -> bool:
        """Send templated email to a lead"""
        
        if template_key not in EMAIL_TEMPLATES:
            logger.error(f"Unknown email template: {template_key}")
            return False
        
        template = EMAIL_TEMPLATES[template_key]
        
        # Prepare template context
        context = {
            "name": lead.name,
            "company": lead.company or "your organization",
            "value": lead.value,
            "status": lead.status.title(),
            "source": lead.source or "website",
            "lead_id": lead.id,
            **(additional_context or {})
        }
        
        # Replace template variables
        subject = template["subject"].format(**context)
        html_content = template["html_content"].format(**context)
        
        return await self.send_email(lead.email, subject, html_content)

# Initialize email service
email_service = EmailService()

# Pydantic models for email requests
from pydantic import BaseModel, EmailStr

class EmailSendRequest(BaseModel):
    to_email: EmailStr
    subject: str
    html_content: str
    from_name: Optional[str] = "Nexus Core Team"

class LeadEmailRequest(BaseModel):
    lead_id: str
    template_key: str
    additional_context: Optional[Dict[str, Any]] = None

class BulkEmailRequest(BaseModel):
    lead_ids: List[str]
    template_key: str
    additional_context: Optional[Dict[str, Any]] = None

class EmailAutomationRequest(BaseModel):
    trigger_type: str  # "lead_status_change", "time_based", "manual"
    conditions: Dict[str, Any]
    email_template: str
    delay_hours: Optional[int] = 0

# API Endpoints
@router.post("/send")
async def send_custom_email(request: EmailSendRequest, background_tasks: BackgroundTasks):
    """Send a custom email"""
    try:
        background_tasks.add_task(
            email_service.send_email,
            request.to_email,
            request.subject,
            request.html_content,
            from_name=request.from_name
        )
        
        return {"status": "success", "message": "Email queued for delivery"}
        
    except Exception as e:
        logger.error(f"Error queueing email: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue email")

@router.post("/send-to-lead")
async def send_lead_email(request: LeadEmailRequest, background_tasks: BackgroundTasks):
    """Send templated email to a specific lead"""
    try:
        # Get lead from database
        collection = await get_leads_collection()
        lead_data = await collection.find_one({"id": request.lead_id})
        
        if not lead_data:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        lead = Lead(**lead_data)
        
        # Send email in background
        background_tasks.add_task(
            email_service.send_lead_email,
            lead,
            request.template_key,
            request.additional_context
        )
        
        # Log activity
        activities_collection = await get_activities_collection()
        await activities_collection.insert_one({
            "lead_id": request.lead_id,
            "activity_type": "email_sent",
            "description": f"Email sent using template: {request.template_key}",
            "timestamp": datetime.utcnow(),
            "metadata": {
                "template": request.template_key,
                "recipient": lead.email
            }
        })
        
        return {"status": "success", "message": f"Email queued for delivery to {lead.name}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending lead email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send lead email")

@router.post("/bulk-send")
async def send_bulk_emails(request: BulkEmailRequest, background_tasks: BackgroundTasks):
    """Send templated emails to multiple leads"""
    try:
        # Get leads from database
        collection = await get_leads_collection()
        leads_data = await collection.find({"id": {"$in": request.lead_ids}}).to_list(len(request.lead_ids))
        
        if not leads_data:
            raise HTTPException(status_code=404, detail="No leads found")
        
        sent_count = 0
        for lead_data in leads_data:
            lead = Lead(**lead_data)
            
            # Send email in background
            background_tasks.add_task(
                email_service.send_lead_email,
                lead,
                request.template_key,
                request.additional_context
            )
            sent_count += 1
        
        return {
            "status": "success", 
            "message": f"Bulk email queued for {sent_count} leads",
            "count": sent_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending bulk emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to send bulk emails")

@router.get("/templates")
async def get_email_templates():
    """Get available email templates"""
    templates = []
    for key, template in EMAIL_TEMPLATES.items():
        templates.append({
            "key": key,
            "name": template["name"],
            "subject": template["subject"]
        })
    
    return {"templates": templates}

@router.post("/automation/setup")
async def setup_email_automation(request: EmailAutomationRequest):
    """Set up automated email triggers (placeholder for workflow integration)"""
    try:
        # This would integrate with the workflow system
        # For now, we'll log the automation setup
        
        logger.info(f"Email automation setup: {request.trigger_type} -> {request.email_template}")
        
        # In a full implementation, this would:
        # 1. Create workflow trigger
        # 2. Set up conditions monitoring
        # 3. Schedule email sending based on triggers
        
        return {
            "status": "success",
            "message": "Email automation configured",
            "automation_id": f"auto_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
    except Exception as e:
        logger.error(f"Error setting up email automation: {e}")
        raise HTTPException(status_code=500, detail="Failed to setup email automation")

@router.get("/stats")
async def get_email_stats():
    """Get email sending statistics"""
    try:
        # In a full implementation, this would query email logs
        # For now, return placeholder stats
        
        return {
            "total_sent": 156,
            "delivered": 152,
            "opened": 89,
            "clicked": 34,
            "bounced": 2,
            "delivery_rate": 97.4,
            "open_rate": 58.6,
            "click_rate": 22.4
        }
        
    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get email statistics")