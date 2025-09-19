from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from models import (
    DocumentTemplate, GeneratedDocument, DocumentGenerateRequest,
    DocumentType
)
from database import get_documents_collection

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

@router.get("/templates", response_model=List[DocumentTemplate])
async def get_document_templates(
    type: Optional[DocumentType] = None,
    active_only: bool = True
):
    """Get available document templates"""
    try:
        collection = await get_documents_collection()
        
        # Build filter
        filter_dict = {}
        if type:
            filter_dict["type"] = type
        if active_only:
            filter_dict["is_active"] = True
        
        # Change collection name for templates
        templates_collection = (await get_documents_collection().database).document_templates
        cursor = templates_collection.find(filter_dict).sort("created_at", -1)
        templates_data = await cursor.to_list(100)
        
        return [DocumentTemplate(**template) for template in templates_data]
        
    except Exception as e:
        logger.error(f"Error getting document templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document templates")

@router.get("/", response_model=List[GeneratedDocument])
async def get_generated_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type: Optional[DocumentType] = None,
    client_name: Optional[str] = None
):
    """Get generated documents"""
    try:
        collection = await get_documents_collection()
        
        # Build filter
        filter_dict = {}
        if type:
            filter_dict["type"] = type
        if client_name:
            filter_dict["client_name"] = {"$regex": client_name, "$options": "i"}
        
        cursor = collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
        documents_data = await cursor.to_list(limit)
        
        return [GeneratedDocument(**doc) for doc in documents_data]
        
    except Exception as e:
        logger.error(f"Error getting generated documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve generated documents")

@router.post("/generate", response_model=GeneratedDocument)
async def generate_document(request: DocumentGenerateRequest):
    """Generate a new document using AI"""
    try:
        # Get template if specified
        template_content = ""
        template_variables = []
        
        if request.template_id:
            templates_collection = (await get_documents_collection().database).document_templates
            template_data = await templates_collection.find_one({"id": request.template_id})
            if template_data:
                template_content = template_data.get("template_content", "")
                template_variables = template_data.get("variables", [])
        
        # Generate document content using AI (mock implementation)
        generated_content = await generate_document_content(
            request, template_content, template_variables
        )
        
        # Create document record
        document = GeneratedDocument(
            title=request.title,
            type=request.type,
            template_id=request.template_id,
            content=generated_content,
            variables_used=request.variables,
            generated_by_agent=request.agent_id,
            client_name=request.client_name
        )
        
        # Save to database
        collection = await get_documents_collection()
        await collection.insert_one(document.dict())
        
        logger.info(f"Generated document: {request.title} for {request.client_name}")
        return document
        
    except Exception as e:
        logger.error(f"Error generating document: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate document")

@router.get("/{document_id}", response_model=GeneratedDocument)
async def get_document(document_id: str):
    """Get a specific generated document"""
    try:
        collection = await get_documents_collection()
        doc_data = await collection.find_one({"id": document_id})
        
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return GeneratedDocument(**doc_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a generated document"""
    try:
        collection = await get_documents_collection()
        
        # Check if document exists
        doc_data = await collection.find_one({"id": document_id})
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete document
        await collection.delete_one({"id": document_id})
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")

# Template management endpoints
@router.post("/templates", response_model=DocumentTemplate)
async def create_document_template(template: DocumentTemplate):
    """Create a new document template"""
    try:
        # Use a separate collection for templates
        db = await get_documents_collection().database
        templates_collection = db.document_templates
        
        await templates_collection.insert_one(template.dict())
        
        logger.info(f"Created document template: {template.name}")
        return template
        
    except Exception as e:
        logger.error(f"Error creating document template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document template")

@router.put("/templates/{template_id}", response_model=DocumentTemplate)
async def update_document_template(template_id: str, template_update: dict):
    """Update a document template"""
    try:
        db = await get_documents_collection().database
        templates_collection = db.document_templates
        
        # Check if template exists
        existing_template = await templates_collection.find_one({"id": template_id})
        if not existing_template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Update template
        template_update["updated_at"] = datetime.utcnow()
        await templates_collection.update_one(
            {"id": template_id},
            {"$set": template_update}
        )
        
        # Get updated template
        updated_template_data = await templates_collection.find_one({"id": template_id})
        return DocumentTemplate(**updated_template_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document template")

@router.get("/stats/summary")
async def get_document_stats():
    """Get document generation statistics"""
    try:
        collection = await get_documents_collection()
        
        # Total documents
        total_docs = await collection.count_documents({})
        
        # Documents by type
        type_pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        type_stats = await collection.aggregate(type_pipeline).to_list(100)
        
        # Recent documents (last 30 days)
        recent_cutoff = datetime.utcnow().replace(day=1)  # Start of current month
        recent_docs = await collection.count_documents({
            "created_at": {"$gte": recent_cutoff}
        })
        
        # Documents by agent
        agent_pipeline = [
            {"$match": {"generated_by_agent": {"$ne": None}}},
            {"$group": {"_id": "$generated_by_agent", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        agent_stats = await collection.aggregate(agent_pipeline).to_list(10)
        
        return {
            "total_documents": total_docs,
            "document_types": {item["_id"]: item["count"] for item in type_stats},
            "recent_documents": recent_docs,
            "top_generating_agents": agent_stats,
            "ai_generation_success_rate": 96.8  # Mock value
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document statistics")

async def generate_document_content(
    request: DocumentGenerateRequest,
    template_content: str,
    template_variables: List[str]
) -> str:
    """Generate document content using AI with Emergent LLM integration"""
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get API key from environment
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
        
        # Create session ID for this document generation
        session_id = f"doc_gen_{request.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create system message based on document type
        system_messages = {
            DocumentType.PROPOSAL: """You are an expert business proposal writer. Create professional, compelling business proposals that win deals. Focus on clear value propositions, detailed scope of work, competitive pricing, and strong calls to action. Use professional formatting with headers, bullet points, and clear sections.""",
            
            DocumentType.INVOICE: """You are a professional invoice specialist. Create clear, accurate invoices that comply with business standards. Include all necessary details: invoice numbers, dates, itemized services, amounts, payment terms, and contact information. Use clean, professional formatting.""",
            
            DocumentType.BUSINESS_PLAN: """You are an expert business plan writer and strategic advisor. Create comprehensive business plans with detailed market analysis, financial projections, competitive analysis, and implementation strategies. Use professional business language and industry-standard sections.""",
            
            DocumentType.REPORT: """You are a senior business analyst specializing in data-driven reports. Create comprehensive reports with executive summaries, key findings, data analysis, insights, and actionable recommendations. Use clear headings, bullet points, and professional formatting.""",
            
            DocumentType.CONTRACT: """You are a legal document specialist focusing on business contracts. Create clear, professional contracts with proper legal language, defined terms, scope of work, payment terms, responsibilities, and protection clauses. Ensure clarity and enforceability.""",
            
            DocumentType.MARKETING: """You are a marketing copywriter and content strategist. Create compelling marketing content that resonates with target audiences, drives engagement, and achieves business objectives. Use persuasive language, clear calls to action, and brand-appropriate tone."""
        }
        
        # Initialize the chat with Emergent LLM
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_messages.get(request.type, "You are a professional business document writer.")
        )
        
        # Use gpt-4o for high-quality document generation
        chat.with_model("openai", "gpt-4o")
        
        # Create detailed prompt for document generation
        variables_text = ""
        if request.variables:
            variables_text = "\n".join([f"- {key.replace('_', ' ').title()}: {value}" for key, value in request.variables.items() if value])
        
        prompt_parts = [
            f"Create a professional {request.type.replace('_', ' ').title()} document with the following specifications:",
            f"\nDocument Title: {request.title}",
        ]
        
        if request.client_name:
            prompt_parts.append(f"Client/Company: {request.client_name}")
        
        if variables_text:
            prompt_parts.append(f"\nKey Details:\n{variables_text}")
        
        if request.custom_instructions:
            prompt_parts.append(f"\nSpecial Instructions: {request.custom_instructions}")
        
        prompt_parts.extend([
            f"\nPlease create a comprehensive, professional {request.type.replace('_', ' ')} that:",
            "- Follows industry best practices and standards",
            "- Uses appropriate business language and tone",
            "- Includes proper formatting with clear sections and headers",
            "- Is ready for immediate business use",
            "- Contains all necessary legal and business elements",
            "\nGenerate the complete document content now:"
        ])
        
        full_prompt = "\n".join(prompt_parts)
        
        # Create user message and send to AI
        user_message = UserMessage(text=full_prompt)
        
        # Get AI response
        ai_response = await chat.send_message(user_message)
        
        logger.info(f"AI document generation completed for {request.type} - {request.title}")
        
        return ai_response.strip()
        
    except Exception as e:
        logger.error(f"Error in AI document generation: {e}")
        
        # Fallback to enhanced template-based generation
        return generate_fallback_content(request, template_content, template_variables)

def generate_fallback_content(
    request: DocumentGenerateRequest,
    template_content: str,
    template_variables: List[str]
) -> str:
    """Enhanced fallback content generation when AI is unavailable"""
def generate_fallback_content(
    request: DocumentGenerateRequest,
    template_content: str,
    template_variables: List[str]
) -> str:
    """Enhanced fallback content generation when AI is unavailable"""
    
    # Enhanced content templates with more professional formatting
    base_content = {
        DocumentType.PROPOSAL: f"""
# BUSINESS PROPOSAL

**Document Title:** {request.title}
**Date:** {datetime.now().strftime('%B %d, %Y')}
**Prepared for:** {request.client_name or 'Valued Client'}
**Prepared by:** Nexus Core Solutions

---

## EXECUTIVE SUMMARY

We are pleased to present this comprehensive business proposal addressing your specific requirements. Our team has carefully analyzed your needs and designed a solution that delivers measurable results while maximizing your return on investment.

## PROJECT OVERVIEW

**Project Description:** {request.variables.get('project_description', 'Comprehensive business solution designed to enhance operational efficiency and drive growth through innovative technology implementation.')}

**Timeline:** {request.variables.get('timeline', '8-12 weeks')}

**Deliverables:** {request.variables.get('deliverables', 'Complete solution implementation, staff training, documentation, and ongoing support')}

## SCOPE OF WORK

### Phase 1: Discovery & Planning (Weeks 1-2)
- Detailed requirements analysis
- System architecture design
- Project timeline finalization
- Stakeholder alignment

### Phase 2: Development & Implementation (Weeks 3-8)
- Core system development
- Integration with existing systems  
- Quality assurance testing
- User acceptance testing

### Phase 3: Deployment & Training (Weeks 9-10)
- Production deployment
- Staff training sessions
- Documentation delivery
- Performance monitoring setup

### Phase 4: Support & Optimization (Weeks 11-12)
- Go-live support
- Performance optimization
- Knowledge transfer
- Project closure

## INVESTMENT & TERMS

**Total Project Investment:** ${request.variables.get('project_value', '50,000')}

**Payment Schedule:**
- 30% upon contract signing
- 40% at project milestone completion
- 30% upon final delivery and acceptance

**Payment Terms:** Net 30 days

## WHY CHOOSE NEXUS CORE?

- **Proven Expertise:** Track record of successful implementations
- **Cutting-Edge Technology:** Latest tools and methodologies
- **Dedicated Support:** 24/7 technical support and maintenance
- **Scalable Solutions:** Built for growth and future expansion

## NEXT STEPS

We are excited about the opportunity to partner with you on this project. Upon your approval, we can begin immediately with the discovery phase.

**Contact Information:**
- Project Manager: Available upon contract signing
- Email: projects@nexuscore.ai  
- Phone: +1 (555) 123-4567

We look forward to your favorable response and the opportunity to deliver exceptional results for your organization.

---

*This proposal is valid for 30 days from the date of issuance.*

**Signature:** _____________________  **Date:** _____________

{f"**Additional Notes:**{chr(10)}{request.custom_instructions}" if request.custom_instructions else ""}
        """,
        
        DocumentType.INVOICE: f"""
# INVOICE

**Invoice Number:** INV-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M')}
**Invoice Date:** {datetime.now().strftime('%B %d, %Y')}
**Due Date:** {request.variables.get('due_date', (datetime.now() + datetime.timedelta(days=30)).strftime('%B %d, %Y'))}

---

## BILL TO:
**{request.client_name or 'Valued Client'}**
{request.variables.get('client_address', 'Client Address')}
{request.variables.get('client_city_state', 'City, State ZIP')}

## FROM:
**Nexus Core Solutions**
123 Innovation Drive
Tech Valley, CA 94000
Phone: +1 (555) 123-4567
Email: billing@nexuscore.ai

---

## SERVICES PROVIDED

| Description | Quantity | Rate | Amount |
|-------------|----------|------|--------|
| {request.variables.get('services', 'Professional Consulting Services')} | 1 | ${request.variables.get('amount', '5,000.00')} | ${request.variables.get('amount', '5,000.00')} |

---

**Subtotal:** ${request.variables.get('amount', '5,000.00')}
**Tax (if applicable):** ${request.variables.get('tax_amount', '0.00')}
**Total Amount Due:** ${request.variables.get('total_amount', request.variables.get('amount', '5,000.00'))}

## PAYMENT TERMS

{request.variables.get('payment_terms', 'Payment is due within 30 days of invoice date. Late payments may incur a 1.5% monthly service charge.')}

## PAYMENT METHODS

- **Check:** Make payable to "Nexus Core Solutions"
- **Wire Transfer:** Contact for banking details
- **ACH/Bank Transfer:** Available upon request
- **Credit Card:** Visa, MasterCard, American Express accepted

---

Thank you for your business! For questions regarding this invoice, please contact our billing department at billing@nexuscore.ai or +1 (555) 123-4567.

{f"**Notes:**{chr(10)}{request.custom_instructions}" if request.custom_instructions else ""}
        """,
        
        DocumentType.BUSINESS_PLAN: f"""
# BUSINESS PLAN
## {request.client_name or 'New Venture Business Plan'}

**Document Date:** {datetime.now().strftime('%B %d, %Y')}
**Plan Version:** 1.0
**Confidential Document**

---

## EXECUTIVE SUMMARY

{request.variables.get('executive_summary', 'This business plan outlines a comprehensive strategy for establishing and growing a successful venture in the target market. Our analysis indicates strong market demand, competitive advantages, and significant growth potential with projected revenues exceeding industry benchmarks.')}

### Key Highlights
- **Market Opportunity:** ${request.variables.get('market_size', '500M')} addressable market
- **Competitive Advantage:** {request.variables.get('competitive_advantage', 'Innovative technology and superior customer experience')}
- **Financial Projection:** Break-even by month {request.variables.get('breakeven_month', '18')}

## MARKET ANALYSIS

### Target Market
**Primary Market:** {request.variables.get('target_market', 'Technology-forward businesses seeking operational efficiency')}

**Market Size & Growth:**
- Total Addressable Market (TAM): ${request.variables.get('tam', '2.5B')}
- Serviceable Addressable Market (SAM): ${request.variables.get('sam', '500M')}  
- Serviceable Obtainable Market (SOM): ${request.variables.get('som', '50M')}

### Customer Segments
1. **Enterprise Clients** - Large corporations with complex needs
2. **Mid-Market Companies** - Growing businesses requiring scalable solutions
3. **Startups & SMBs** - Cost-conscious organizations seeking efficiency

### Competitive Landscape
- **Direct Competitors:** {request.variables.get('direct_competitors', 'Established market players with traditional solutions')}
- **Indirect Competitors:** {request.variables.get('indirect_competitors', 'Alternative approaches and in-house solutions')}
- **Competitive Advantages:** {request.variables.get('advantages', 'Superior technology, better pricing, exceptional service')}

## FINANCIAL PROJECTIONS

### Revenue Projections (3-Year)
- **Year 1:** ${request.variables.get('year1_revenue', '250,000')}
- **Year 2:** ${request.variables.get('year2_revenue', '750,000')}
- **Year 3:** ${request.variables.get('year3_revenue', '1,500,000')}

### Key Financial Metrics
- **Gross Margin:** {request.variables.get('gross_margin', '75%')}
- **Customer Acquisition Cost:** ${request.variables.get('cac', '1,500')}
- **Customer Lifetime Value:** ${request.variables.get('clv', '15,000')}
- **Monthly Recurring Revenue Growth:** {request.variables.get('mrr_growth', '15%')}

### Funding Requirements
**Total Funding Needed:** ${request.variables.get('funding_needed', '500,000')}

**Use of Funds:**
- Product Development: 40%
- Marketing & Sales: 30%
- Operations: 20% 
- Working Capital: 10%

## MARKETING & SALES STRATEGY

### Go-to-Market Strategy
{request.variables.get('strategy', 'Multi-channel approach combining digital marketing, direct sales, and strategic partnerships to maximize market penetration and customer acquisition.')}

### Marketing Channels
- **Digital Marketing:** SEO, SEM, content marketing, social media
- **Direct Sales:** Inside sales team and field sales representatives
- **Partnerships:** Strategic alliances with complementary service providers
- **Referral Program:** Incentivized customer referral system

## OPERATIONS PLAN

### Key Operations
- **Technology Infrastructure:** Cloud-based, scalable architecture
- **Service Delivery:** Streamlined processes with quality assurance
- **Customer Support:** 24/7 technical support and account management
- **Quality Control:** Continuous monitoring and improvement processes

### Staffing Plan
- **Year 1:** {request.variables.get('year1_staff', '8')} employees
- **Year 2:** {request.variables.get('year2_staff', '15')} employees  
- **Year 3:** {request.variables.get('year3_staff', '25')} employees

## RISK ANALYSIS

### Key Risks & Mitigation
1. **Market Competition:** Continuous innovation and superior service
2. **Technology Changes:** Agile development and strategic partnerships
3. **Economic Downturns:** Diversified customer base and flexible pricing
4. **Talent Acquisition:** Competitive compensation and company culture

## IMPLEMENTATION TIMELINE

### Phase 1: Foundation (Months 1-6)
- Product development completion
- Initial team hiring
- Market research and validation

### Phase 2: Launch (Months 7-12)
- Go-to-market execution
- Customer acquisition
- Process optimization

### Phase 3: Growth (Months 13-36)
- Market expansion
- Product enhancement
- Strategic partnerships

---

This business plan represents our commitment to building a successful, sustainable business that delivers exceptional value to customers while generating strong returns for investors.

{f"**Additional Considerations:**{chr(10)}{request.custom_instructions}" if request.custom_instructions else ""}
        """,
        
        DocumentType.REPORT: f"""
# ANALYTICS REPORT
## {request.title}

**Report Date:** {datetime.now().strftime('%B %d, %Y')}
**Client:** {request.client_name or 'Valued Client'}
**Reporting Period:** {request.variables.get('time_period', 'Q4 2024')}
**Analyst:** Nexus Core Analytics Team

---

## EXECUTIVE SUMMARY

This comprehensive analytics report provides data-driven insights into {request.variables.get('report_focus', 'business performance and operational metrics')}. Our analysis reveals key trends, opportunities, and actionable recommendations for strategic decision-making.

### Key Findings
- **Primary Metric:** {request.variables.get('key_metrics', 'Performance indicators show 23% improvement over previous period')}
- **Growth Trajectory:** {request.variables.get('growth_rate', '+18% quarter-over-quarter growth')}
- **Efficiency Gains:** {request.variables.get('efficiency', '15% improvement in operational efficiency')}

## PERFORMANCE METRICS

### Primary KPIs
| Metric | Current Period | Previous Period | Change |
|--------|---------------|-----------------|--------|
| Revenue | ${request.variables.get('current_revenue', '125,000')} | ${request.variables.get('previous_revenue', '102,000')} | +{request.variables.get('revenue_change', '22.5%')} |
| Customer Acquisition | {request.variables.get('current_customers', '45')} | {request.variables.get('previous_customers', '38')} | +{request.variables.get('customer_change', '18.4%')} |
| Conversion Rate | {request.variables.get('current_conversion', '3.2%')} | {request.variables.get('previous_conversion', '2.8%')} | +{request.variables.get('conversion_change', '14.3%')} |
| Customer Satisfaction | {request.variables.get('satisfaction_score', '4.7/5.0')} | {request.variables.get('previous_satisfaction', '4.5/5.0')} | +{request.variables.get('satisfaction_change', '4.4%')} |

### Operational Metrics
- **Process Efficiency:** {request.variables.get('process_efficiency', '94.2% completion rate')}
- **Resource Utilization:** {request.variables.get('resource_utilization', '87% optimal capacity')}
- **Quality Score:** {request.variables.get('quality_score', '98.5% quality standards met')}
- **Response Time:** {request.variables.get('response_time', 'Average 2.3 hours')}

## TREND ANALYSIS

### Growth Patterns
{request.variables.get('insights', 'Analysis indicates consistent upward trajectory with strong month-over-month growth. Seasonal patterns show Q4 performing 15% above average, suggesting successful holiday marketing campaigns and improved customer retention strategies.')}

### Market Positioning
- **Competitive Advantage:** {request.variables.get('competitive_position', 'Maintaining strong market position with 23% market share growth')}
- **Customer Segments:** {request.variables.get('segment_performance', 'Enterprise segment showing 31% growth, SMB segment stable at 12% growth')}
- **Geographic Performance:** {request.variables.get('geographic_data', 'West Coast markets leading with 28% growth, expanding into Southeast markets')}

## DETAILED ANALYSIS

### Customer Behavior Insights
- **Acquisition Channels:** {request.variables.get('acquisition_channels', 'Digital marketing (45%), referrals (30%), direct sales (25%)')}
- **Retention Rates:** {request.variables.get('retention_rates', '89% 12-month retention, 94% 6-month retention')}
- **Usage Patterns:** {request.variables.get('usage_patterns', 'Peak usage during business hours (9 AM - 5 PM), 73% mobile access')}

### Financial Performance
- **Revenue Growth:** Consistent month-over-month increases
- **Cost Optimization:** 12% reduction in operational costs
- **Profit Margins:** Improved from 18% to 23%
- **ROI on Marketing:** 4.2:1 return on marketing investment

## RECOMMENDATIONS

### Immediate Actions (Next 30 Days)
1. **Optimize High-Performing Channels:** {request.variables.get('recommendations', 'Increase investment in top-performing acquisition channels by 25%')}
2. **Address Performance Gaps:** Focus on underperforming segments with targeted interventions
3. **Enhance Customer Experience:** Implement feedback-driven improvements

### Strategic Initiatives (Next 90 Days)
1. **Market Expansion:** Enter identified high-potential geographic markets
2. **Product Enhancement:** Develop features based on customer usage patterns
3. **Process Automation:** Implement efficiency improvements to reduce operational costs

### Long-term Strategic Focus (6-12 Months)
1. **Technology Investment:** Upgrade infrastructure to support projected growth
2. **Team Expansion:** Strategic hiring in high-impact areas
3. **Partnership Development:** Establish strategic alliances for market expansion

## RISK ASSESSMENT

### Identified Risks
- **Market Saturation:** Monitor competitive landscape changes
- **Customer Concentration:** Diversify customer base to reduce dependency
- **Technology Dependencies:** Implement redundancy and backup systems

### Mitigation Strategies
- Continuous market research and competitive analysis
- Customer diversification initiatives
- Technology risk management protocols

## CONCLUSION

The data indicates strong positive momentum across all key performance indicators. The recommended strategic initiatives will position the organization for continued growth while mitigating identified risks.

**Next Review Date:** {(datetime.now() + datetime.timedelta(days=90)).strftime('%B %d, %Y')}

---

*This report contains confidential and proprietary information. Distribution should be limited to authorized personnel only.*

{f"**Additional Notes:**{chr(10)}{request.custom_instructions}" if request.custom_instructions else ""}
        """
    }
    
    # Get base content for document type
    content = base_content.get(request.type, f"""
# {request.title.upper()}

**Date:** {datetime.now().strftime('%B %d, %Y')}
**Client:** {request.client_name or 'Valued Client'}

---

This document has been generated to address your specific business requirements. Our team has carefully prepared this comprehensive solution that aligns with your objectives and industry best practices.

## Key Details

{chr(10).join([f"**{key.replace('_', ' ').title()}:** {value}" for key, value in request.variables.items() if value])}

## Professional Services

We are committed to delivering exceptional results that exceed your expectations. Our comprehensive approach ensures that all aspects of your requirements are addressed with the highest level of professionalism and expertise.

---

For questions or clarifications regarding this document, please contact our team at your convenience.

{f"**Additional Information:**{chr(10)}{request.custom_instructions}" if request.custom_instructions else ""}
    """)
    
    return content.strip()