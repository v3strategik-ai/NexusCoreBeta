from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field
import uuid
import random
from enum import Enum
from statistics import mean
import math

from database import (
    get_leads_collection,
    get_activities_collection,
    get_workflows_collection
)

router = APIRouter(prefix="/ab-testing", tags=["ab-testing"])
logger = logging.getLogger(__name__)

# Enums for A/B Testing
class TestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"

class TestType(str, Enum):
    EMAIL_CAMPAIGN = "email_campaign"
    WORKFLOW = "workflow"
    LEAD_SCORING = "lead_scoring"
    AGENT_CONFIGURATION = "agent_configuration"
    UI_COMPONENT = "ui_component"

class VariantType(str, Enum):
    CONTROL = "control"
    VARIANT = "variant"

class MetricType(str, Enum):
    CONVERSION_RATE = "conversion_rate"
    CLICK_RATE = "click_rate"
    OPEN_RATE = "open_rate"
    COMPLETION_RATE = "completion_rate"
    REVENUE = "revenue"
    ENGAGEMENT = "engagement"

# Pydantic models for A/B Testing
class ABTestVariant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    variant_type: VariantType
    configuration: Dict[str, Any]  # Specific config for this variant
    traffic_percentage: float = Field(ge=0, le=100)  # Percentage of traffic to this variant
    is_active: bool = True

class ABTestMetric(BaseModel):
    metric_type: MetricType
    name: str
    description: str
    target_value: Optional[float] = None
    is_primary: bool = False  # Primary metric for statistical significance

class ABTest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    test_type: TestType
    status: TestStatus = TestStatus.DRAFT
    variants: List[ABTestVariant]
    metrics: List[ABTestMetric]
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_sample_size: int = 100  # Minimum sample size per variant
    confidence_level: float = 0.95  # Statistical confidence level
    target_audience: Dict[str, Any] = {}  # Filters for target audience
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_at: Optional[datetime] = None

class ABTestResult(BaseModel):
    test_id: str
    variant_id: str
    variant_name: str
    metric_type: MetricType
    metric_name: str
    sample_size: int
    conversions: int
    conversion_rate: float
    confidence_interval: List[float]  # [lower_bound, upper_bound]
    statistical_significance: bool
    p_value: Optional[float] = None

class ABTestAnalysis(BaseModel):
    test_id: str
    test_name: str
    status: TestStatus
    duration_days: int
    total_participants: int
    results: List[ABTestResult]
    winner: Optional[str] = None  # Variant ID of the winner
    statistical_power: float
    recommendations: List[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ABTestAssignment(BaseModel):
    user_id: str
    test_id: str
    variant_id: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    has_converted: bool = False
    conversion_value: Optional[float] = None
    metadata: Dict[str, Any] = {}

class ABTestingEngine:
    """Advanced A/B testing engine for experimentation"""
    
    def __init__(self):
        self.active_tests = {}  # Cache for active tests
        self.assignments = {}   # Cache for user assignments
    
    async def create_test(self, test: ABTest) -> str:
        """Create a new A/B test"""
        try:
            # Validate test configuration
            if len(test.variants) < 2:
                raise ValueError("A/B test must have at least 2 variants")
            
            total_traffic = sum(variant.traffic_percentage for variant in test.variants)
            if abs(total_traffic - 100) > 0.01:  # Allow small floating point differences
                raise ValueError(f"Variant traffic percentages must sum to 100%, got {total_traffic}%")
            
            # Ensure there's exactly one control variant
            control_variants = [v for v in test.variants if v.variant_type == VariantType.CONTROL]
            if len(control_variants) != 1:
                raise ValueError("Test must have exactly one control variant")
            
            # In a real implementation, save to database
            # For now, store in memory cache
            self.active_tests[test.id] = test
            
            return test.id
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""
        try:
            if test_id not in self.active_tests:
                raise ValueError("Test not found")
            
            test = self.active_tests[test_id]
            if test.status != TestStatus.DRAFT:
                raise ValueError("Only draft tests can be started")
            
            # Update test status and timing
            test.status = TestStatus.RUNNING
            test.start_date = datetime.utcnow()
            test.updated_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting A/B test: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def assign_variant(self, test_id: str, user_id: str) -> ABTestAssignment:
        """Assign a user to a test variant"""
        try:
            if test_id not in self.active_tests:
                raise ValueError("Test not found or not active")
            
            test = self.active_tests[test_id]
            if test.status != TestStatus.RUNNING:
                raise ValueError("Test is not currently running")
            
            # Check if user already assigned
            assignment_key = f"{test_id}:{user_id}"
            if assignment_key in self.assignments:
                return self.assignments[assignment_key]
            
            # Assign variant based on traffic percentages
            variant = self._select_variant(test.variants, user_id)
            
            assignment = ABTestAssignment(
                user_id=user_id,
                test_id=test_id,
                variant_id=variant.id
            )
            
            # Cache assignment
            self.assignments[assignment_key] = assignment
            
            return assignment
            
        except Exception as e:
            logger.error(f"Error assigning variant: {e}")
            raise HTTPException(status_code=500, detail="Failed to assign variant")
    
    async def record_conversion(
        self, 
        test_id: str, 
        user_id: str, 
        metric_type: MetricType,
        conversion_value: Optional[float] = None
    ) -> bool:
        """Record a conversion event for A/B test analysis"""
        try:
            assignment_key = f"{test_id}:{user_id}"
            if assignment_key not in self.assignments:
                # User not in test, ignore conversion
                return False
            
            assignment = self.assignments[assignment_key]
            assignment.has_converted = True
            assignment.conversion_value = conversion_value
            assignment.metadata[f"{metric_type.value}_converted_at"] = datetime.utcnow().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording conversion: {e}")
            return False
    
    async def analyze_test(self, test_id: str) -> ABTestAnalysis:
        """Analyze A/B test results and statistical significance"""
        try:
            if test_id not in self.active_tests:
                raise ValueError("Test not found")
            
            test = self.active_tests[test_id]
            
            # Calculate duration
            start_date = test.start_date or test.created_at
            duration_days = (datetime.utcnow() - start_date).days
            
            # Get all assignments for this test
            test_assignments = [
                assignment for assignment in self.assignments.values()
                if assignment.test_id == test_id
            ]
            
            results = []
            variant_stats = {}
            
            # Calculate results for each variant and metric
            for variant in test.variants:
                variant_assignments = [a for a in test_assignments if a.variant_id == variant.id]
                
                for metric in test.metrics:
                    sample_size = len(variant_assignments)
                    conversions = len([a for a in variant_assignments if a.has_converted])
                    conversion_rate = (conversions / max(sample_size, 1)) * 100
                    
                    # Calculate confidence interval (simplified)
                    confidence_interval = self._calculate_confidence_interval(
                        conversions, sample_size, test.confidence_level
                    )
                    
                    # Store for statistical significance testing
                    variant_stats[variant.id] = {
                        "sample_size": sample_size,
                        "conversions": conversions,
                        "conversion_rate": conversion_rate
                    }
                    
                    results.append(ABTestResult(
                        test_id=test_id,
                        variant_id=variant.id,
                        variant_name=variant.name,
                        metric_type=metric.metric_type,
                        metric_name=metric.name,
                        sample_size=sample_size,
                        conversions=conversions,
                        conversion_rate=round(conversion_rate, 2),
                        confidence_interval=confidence_interval,
                        statistical_significance=sample_size >= test.min_sample_size,
                        p_value=None  # Would calculate actual p-value in real implementation
                    ))
            
            # Determine winner (simplified - based on primary metric)
            winner = self._determine_winner(test, variant_stats)
            
            # Calculate statistical power (simplified)
            total_sample_size = sum(stats["sample_size"] for stats in variant_stats.values())
            statistical_power = min(0.95, total_sample_size / (test.min_sample_size * len(test.variants)))
            
            # Generate recommendations
            recommendations = self._generate_recommendations(test, variant_stats, statistical_power)
            
            return ABTestAnalysis(
                test_id=test_id,
                test_name=test.name,
                status=test.status,
                duration_days=duration_days,
                total_participants=len(test_assignments),
                results=results,
                winner=winner,
                statistical_power=round(statistical_power, 2),
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing test: {e}")
            raise HTTPException(status_code=500, detail="Failed to analyze test")
    
    def _select_variant(self, variants: List[ABTestVariant], user_id: str) -> ABTestVariant:
        """Select variant based on traffic percentages and user ID"""
        # Use user ID for consistent assignment
        random.seed(hash(user_id) % (2**32))
        rand_value = random.uniform(0, 100)
        
        cumulative_percentage = 0
        for variant in variants:
            cumulative_percentage += variant.traffic_percentage
            if rand_value <= cumulative_percentage:
                return variant
        
        # Fallback to last variant
        return variants[-1]
    
    def _calculate_confidence_interval(
        self, 
        conversions: int, 
        sample_size: int, 
        confidence_level: float
    ) -> List[float]:
        """Calculate confidence interval for conversion rate"""
        if sample_size == 0:
            return [0.0, 0.0]
        
        conversion_rate = conversions / sample_size
        
        # Using normal approximation for binomial distribution
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%
        
        margin_of_error = z_score * math.sqrt(
            (conversion_rate * (1 - conversion_rate)) / sample_size
        )
        
        lower_bound = max(0, conversion_rate - margin_of_error)
        upper_bound = min(1, conversion_rate + margin_of_error)
        
        return [round(lower_bound * 100, 2), round(upper_bound * 100, 2)]
    
    def _determine_winner(self, test: ABTest, variant_stats: Dict[str, Dict]) -> Optional[str]:
        """Determine winning variant based on primary metrics"""
        # Find primary metric
        primary_metrics = [m for m in test.metrics if m.is_primary]
        if not primary_metrics:
            return None
        
        # Simple winner determination - highest conversion rate with sufficient sample size
        best_variant = None
        best_rate = -1
        
        for variant_id, stats in variant_stats.items():
            if stats["sample_size"] >= test.min_sample_size:
                if stats["conversion_rate"] > best_rate:
                    best_rate = stats["conversion_rate"]
                    best_variant = variant_id
        
        return best_variant
    
    def _generate_recommendations(
        self, 
        test: ABTest, 
        variant_stats: Dict[str, Dict], 
        statistical_power: float
    ) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check sample size
        total_sample = sum(stats["sample_size"] for stats in variant_stats.values())
        min_total_sample = test.min_sample_size * len(test.variants)
        
        if total_sample < min_total_sample:
            recommendations.append(f"Increase sample size. Current: {total_sample}, Recommended: {min_total_sample}")
        
        # Check statistical power
        if statistical_power < 0.8:
            recommendations.append("Consider running test longer to achieve adequate statistical power (80%+)")
        
        # Check for clear winner
        rates = [stats["conversion_rate"] for stats in variant_stats.values()]
        if max(rates) - min(rates) < 5:  # Less than 5% difference
            recommendations.append("Results are very close. Consider running test longer or testing more distinct variants")
        
        # General recommendations
        recommendations.append("Monitor test regularly for any technical issues")
        recommendations.append("Document learnings for future test planning")
        
        return recommendations

# Global A/B testing engine instance
ab_testing_engine = ABTestingEngine()

# API Endpoints
@router.post("/tests/create", response_model=dict)
async def create_ab_test(test: ABTest):
    """Create a new A/B test"""
    try:
        test_id = await ab_testing_engine.create_test(test)
        return {
            "test_id": test_id,
            "message": "A/B test created successfully",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise HTTPException(status_code=500, detail="Failed to create A/B test")

@router.post("/tests/{test_id}/start")
async def start_ab_test(test_id: str):
    """Start an A/B test"""
    try:
        success = await ab_testing_engine.start_test(test_id)
        return {
            "test_id": test_id,
            "message": "A/B test started successfully",
            "status": "running" if success else "failed"
        }
    except Exception as e:
        logger.error(f"Error starting A/B test: {e}")
        raise HTTPException(status_code=500, detail="Failed to start A/B test")

@router.post("/tests/{test_id}/assign", response_model=ABTestAssignment)
async def assign_test_variant(test_id: str, user_id: str):
    """Assign a user to a test variant"""
    try:
        return await ab_testing_engine.assign_variant(test_id, user_id)
    except Exception as e:
        logger.error(f"Error assigning test variant: {e}")
        raise HTTPException(status_code=500, detail="Failed to assign test variant")

@router.post("/tests/{test_id}/conversion")
async def record_test_conversion(
    test_id: str,
    user_id: str,
    metric_type: MetricType,
    conversion_value: Optional[float] = None
):
    """Record a conversion event for A/B test analysis"""
    try:
        success = await ab_testing_engine.record_conversion(
            test_id, user_id, metric_type, conversion_value
        )
        return {
            "test_id": test_id,
            "user_id": user_id,
            "metric_type": metric_type.value,
            "recorded": success,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error recording conversion: {e}")
        raise HTTPException(status_code=500, detail="Failed to record conversion")

@router.get("/tests/{test_id}/analysis", response_model=ABTestAnalysis)
async def get_test_analysis(test_id: str):
    """Get comprehensive analysis of A/B test results"""
    try:
        return await ab_testing_engine.analyze_test(test_id)
    except Exception as e:
        logger.error(f"Error getting test analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get test analysis")

@router.get("/tests/active")
async def get_active_tests():
    """Get list of currently active A/B tests"""
    try:
        active_tests = [
            {
                "id": test.id,
                "name": test.name,
                "test_type": test.test_type.value,
                "status": test.status.value,
                "start_date": test.start_date.isoformat() if test.start_date else None,
                "variants_count": len(test.variants),
                "metrics_count": len(test.metrics)
            }
            for test in ab_testing_engine.active_tests.values()
            if test.status == TestStatus.RUNNING
        ]
        
        return {
            "active_tests": active_tests,
            "total_count": len(active_tests)
        }
    except Exception as e:
        logger.error(f"Error getting active tests: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active tests")

@router.get("/tests/templates")
async def get_test_templates():
    """Get predefined A/B test templates"""
    templates = [
        {
            "id": "email_subject_test",
            "name": "Email Subject Line Test",
            "description": "Test different email subject lines for open rates",
            "test_type": "email_campaign",
            "suggested_metrics": ["open_rate", "click_rate"],
            "min_sample_size": 200,
            "estimated_duration_days": 7
        },
        {
            "id": "workflow_optimization",
            "name": "Workflow Optimization Test",
            "description": "Test different workflow configurations for completion rates",
            "test_type": "workflow",
            "suggested_metrics": ["completion_rate", "conversion_rate"],
            "min_sample_size": 150,
            "estimated_duration_days": 14
        },
        {
            "id": "lead_scoring_model",
            "name": "Lead Scoring Model Test",
            "description": "Compare different lead scoring algorithms",
            "test_type": "lead_scoring",
            "suggested_metrics": ["conversion_rate", "revenue"],
            "min_sample_size": 300,
            "estimated_duration_days": 21
        },
        {
            "id": "agent_configuration",
            "name": "Agent Configuration Test",
            "description": "Test different AI agent configurations for performance",
            "test_type": "agent_configuration",
            "suggested_metrics": ["engagement", "completion_rate"],
            "min_sample_size": 100,
            "estimated_duration_days": 10
        }
    ]
    
    return {
        "templates": templates,
        "available_test_types": [test_type.value for test_type in TestType],
        "available_metrics": [metric.value for metric in MetricType],
        "confidence_levels": [0.90, 0.95, 0.99]
    }