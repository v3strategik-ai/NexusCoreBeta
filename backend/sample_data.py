"""
Sample data loader for Nexus Core platform
Creates initial agents, leads, and knowledge base entries for demonstration
"""
import asyncio
from datetime import datetime, timedelta
import random

from database import connect_to_mongo, get_database
from models import (
    Agent, AgentStatus, AutonomyLevel,
    Lead, LeadStatus,
    KnowledgeBase,
    GeneratedDocument, DocumentType,
    AgentActivity
)

async def create_sample_agents():
    """Create sample digital employees/agents"""
    db = await get_database()
    agents_collection = db.agents
    
    sample_agents = [
        Agent(
            name="Marketing Genius",
            type="Marketing Specialist",
            status=AgentStatus.ACTIVE,
            personality="Creative & Data-Driven",
            specialization="Content Creation, SEO, Social Media",
            autonomy_level=AutonomyLevel.HIGH,
            efficiency=94.0,
            tasks_completed=15,
            learning_progress=87.0,
            knowledge_base=[],
            metrics={"campaigns_created": 8, "conversion_rate": 23.5}
        ),
        Agent(
            name="Sales Powerhouse",
            type="Sales Expert", 
            status=AgentStatus.ACTIVE,
            personality="Persuasive & Analytical",
            specialization="Lead Conversion, Negotiation, CRM Management",
            autonomy_level=AutonomyLevel.HIGH,
            efficiency=87.0,
            tasks_completed=23,
            learning_progress=92.0,
            knowledge_base=[],
            metrics={"deals_closed": 12, "revenue_generated": 145000}
        ),
        Agent(
            name="Support Virtuoso",
            type="Customer Success",
            status=AgentStatus.TRAINING,
            personality="Empathetic & Solution-Oriented", 
            specialization="Technical Support, Customer Onboarding, Issue Resolution",
            autonomy_level=AutonomyLevel.MEDIUM,
            efficiency=76.0,
            tasks_completed=8,
            learning_progress=65.0,
            knowledge_base=[],
            metrics={"tickets_resolved": 45, "satisfaction_score": 4.8}
        ),
        Agent(
            name="Analytics Oracle",
            type="Data Scientist",
            status=AgentStatus.ACTIVE,
            personality="Logical & Insightful",
            specialization="Predictive Analytics, Business Intelligence, Reporting",
            autonomy_level=AutonomyLevel.QUANTUM,
            efficiency=98.0,
            tasks_completed=31,
            learning_progress=95.0,
            knowledge_base=[],
            metrics={"models_created": 6, "accuracy_rate": 96.8}
        ),
        Agent(
            name="Creative Mastermind",
            type="Design & Content",
            status=AgentStatus.ACTIVE,
            personality="Innovative & Aesthetic",
            specialization="Graphic Design, Video Production, Brand Development",
            autonomy_level=AutonomyLevel.HIGH,
            efficiency=89.0,
            tasks_completed=12,
            learning_progress=78.0,
            knowledge_base=[],
            metrics={"designs_created": 24, "brand_consistency": 95.2}
        ),
        Agent(
            name="Operations Commander",
            type="Process Automation",
            status=AgentStatus.ACTIVE,
            personality="Systematic & Efficient",
            specialization="Workflow Optimization, Quality Control, Resource Management",
            autonomy_level=AutonomyLevel.QUANTUM,
            efficiency=96.0,
            tasks_completed=45,
            learning_progress=91.0,
            knowledge_base=[],
            metrics={"processes_optimized": 18, "efficiency_gained": 34.7}
        )
    ]
    
    # Clear existing agents
    await agents_collection.delete_many({})
    
    # Insert sample agents
    for agent in sample_agents:
        await agents_collection.insert_one(agent.dict())
    
    print(f"Created {len(sample_agents)} sample agents")

async def create_sample_leads():
    """Create sample leads"""
    db = await get_database()
    leads_collection = db.leads
    agents_collection = db.agents
    
    # Get agent IDs
    agents = await agents_collection.find({}).to_list(10)
    agent_ids = [agent["id"] for agent in agents]
    
    sample_leads = [
        Lead(
            name="Acme Corp",
            email="contact@acme.com",
            phone="+1-555-0123",
            company="Acme Corporation",
            status=LeadStatus.HOT,
            value=50000.0,
            source="Website Contact Form",
            assigned_agent_id=agent_ids[1] if agent_ids else None,
            assigned_agent_name="Sales Powerhouse",
            last_contact=datetime.utcnow() - timedelta(hours=2),
            notes=["Initial contact made", "Very interested in our AI solutions"],
            score=85.5,
            tags=["high-value", "enterprise", "ai-interested"]
        ),
        Lead(
            name="TechStart Inc",
            email="hello@techstart.com",
            company="TechStart Inc",
            status=LeadStatus.WARM,
            value=25000.0,
            source="LinkedIn Campaign",
            assigned_agent_id=agent_ids[0] if agent_ids else None,
            assigned_agent_name="Marketing Genius",
            last_contact=datetime.utcnow() - timedelta(days=1),
            notes=["Responded to marketing campaign", "Requested product demo"],
            score=72.3,
            tags=["startup", "demo-requested"]
        ),
        Lead(
            name="Global Solutions",
            email="info@global.com",
            phone="+1-555-0456", 
            company="Global Solutions Ltd",
            status=LeadStatus.COLD,
            value=75000.0,
            source="Trade Show",
            assigned_agent_id=agent_ids[1] if agent_ids else None,
            assigned_agent_name="Sales Powerhouse",
            last_contact=datetime.utcnow() - timedelta(days=5),
            notes=["Met at tech conference", "Collecting information on multiple vendors"],
            score=58.7,
            tags=["enterprise", "comparison-shopping"]
        ),
        Lead(
            name="Innovation Labs",
            email="team@innovation.com",
            company="Innovation Labs",
            status=LeadStatus.HOT,
            value=120000.0,
            source="Referral",
            assigned_agent_id=agent_ids[3] if agent_ids else None,
            assigned_agent_name="Analytics Oracle",
            last_contact=datetime.utcnow() - timedelta(minutes=30),
            notes=["Referral from existing client", "Ready to move forward quickly"],
            score=92.1,
            tags=["referral", "high-value", "hot-lead"]
        ),
        Lead(
            name="Digital Dynamics",
            email="contact@digitaldyn.com",
            company="Digital Dynamics",
            status=LeadStatus.CONVERTED,
            value=35000.0,
            source="Google Ads",
            assigned_agent_id=agent_ids[1] if agent_ids else None,
            assigned_agent_name="Sales Powerhouse", 
            last_contact=datetime.utcnow() - timedelta(hours=6),
            notes=["Contract signed!", "Implementation starting next week"],
            score=100.0,
            tags=["converted", "implementation-ready"]
        )
    ]
    
    # Clear existing leads
    await leads_collection.delete_many({})
    
    # Insert sample leads
    for lead in sample_leads:
        await leads_collection.insert_one(lead.dict())
    
    print(f"Created {len(sample_leads)} sample leads")

async def create_agent_activities():
    """Create sample agent activities"""
    db = await get_database()
    activities_collection = db.activities
    agents_collection = db.agents
    
    # Get agents
    agents = await agents_collection.find({}).to_list(10)
    
    activities = []
    for agent in agents[:4]:  # Create activities for first 4 agents
        if agent["name"] == "Analytics Oracle":
            activities.append(AgentActivity(
                agent_id=agent["id"],
                agent_name=agent["name"],
                activity_type="model_training",
                description="Completed predictive model training with 96.8% accuracy",
                timestamp=datetime.utcnow() - timedelta(seconds=15),
                autonomy_level="Quantum"
            ))
        elif agent["name"] == "Sales Powerhouse":
            activities.append(AgentActivity(
                agent_id=agent["id"],
                agent_name=agent["name"],
                activity_type="deal_closed",
                description="Closed $35K deal with Digital Dynamics autonomously",
                timestamp=datetime.utcnow() - timedelta(minutes=2),
                autonomy_level="High"
            ))
        elif agent["name"] == "Marketing Genius":
            activities.append(AgentActivity(
                agent_id=agent["id"],
                agent_name=agent["name"],
                activity_type="campaign_launch",
                description="Launched viral social media campaign with 47% engagement rate",
                timestamp=datetime.utcnow() - timedelta(minutes=5),
                autonomy_level="High"
            ))
        elif agent["name"] == "Operations Commander":
            activities.append(AgentActivity(
                agent_id=agent["id"],
                agent_name=agent["name"],
                activity_type="process_optimization",
                description="Optimized 12 business workflows, improved efficiency by 34%",
                timestamp=datetime.utcnow() - timedelta(minutes=8),
                autonomy_level="Quantum"
            ))
    
    # Clear existing activities
    await activities_collection.delete_many({})
    
    # Insert activities
    for activity in activities:
        await activities_collection.insert_one(activity.dict())
    
    print(f"Created {len(activities)} agent activities")

async def create_sample_documents():
    """Create sample generated documents"""
    db = await get_database()
    documents_collection = db.documents
    
    sample_docs = [
        GeneratedDocument(
            title="Business Proposal - Acme Corp AI Integration",
            type=DocumentType.PROPOSAL,
            content="Comprehensive AI integration proposal for Acme Corporation...",
            variables_used={"client_name": "Acme Corp", "project_value": "50000"},
            generated_by_agent="Sales Powerhouse",
            client_name="Acme Corp"
        ),
        GeneratedDocument(
            title="Q4 2024 Performance Analytics Report", 
            type=DocumentType.REPORT,
            content="Detailed analytics report showing 45% growth in key metrics...",
            variables_used={"quarter": "Q4 2024", "growth_rate": "45%"},
            generated_by_agent="Analytics Oracle",
            client_name="Internal"
        ),
        GeneratedDocument(
            title="Invoice - Digital Dynamics Implementation",
            type=DocumentType.INVOICE,
            content="Professional services invoice for AI platform implementation...",
            variables_used={"amount": "35000", "client": "Digital Dynamics"},
            generated_by_agent="Operations Commander",
            client_name="Digital Dynamics"
        )
    ]
    
    # Clear existing documents
    await documents_collection.delete_many({})
    
    # Insert sample documents
    for doc in sample_docs:
        await documents_collection.insert_one(doc.dict())
    
    print(f"Created {len(sample_docs)} sample documents")

async def main():
    """Load all sample data"""
    try:
        await connect_to_mongo()
        print("Connected to MongoDB")
        
        await create_sample_agents()
        await create_sample_leads()
        await create_agent_activities()
        await create_sample_documents()
        
        print("\n✅ Sample data loaded successfully!")
        print("🚀 Nexus Core platform is ready with demo data")
        
    except Exception as e:
        print(f"❌ Error loading sample data: {e}")

if __name__ == "__main__":
    asyncio.run(main())