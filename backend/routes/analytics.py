from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field
import math
from statistics import mean, median, stdev
from enum import Enum

from database import (
    get_leads_collection,
    get_agents_collection, 
    get_activities_collection,
    get_documents_collection,
    get_workflows_collection
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

# Enums for analytics
class MetricType(str, Enum):
    REVENUE = "revenue"
    CONVERSION = "conversion"
    EFFICIENCY = "efficiency"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"

class TimeRange(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"

class TrendDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

# Pydantic models for analytics
class KPIMetric(BaseModel):
    name: str
    value: Union[float, int]
    previous_value: Optional[Union[float, int]] = None
    change_percentage: Optional[float] = None
    trend: Optional[TrendDirection] = None
    target: Optional[Union[float, int]] = None
    target_percentage: Optional[float] = None
    unit: str = ""
    format_type: str = "number"  # number, currency, percentage, time

class ROIAnalysis(BaseModel):
    investment: float
    revenue: float
    roi_percentage: float
    roi_ratio: str
    payback_period_months: Optional[float] = None
    net_profit: float
    margin_percentage: float

class PerformanceForecast(BaseModel):
    metric_name: str
    current_value: float
    forecasted_values: List[Dict[str, Any]]  # [{"date": "2024-01-01", "value": 100, "confidence": 0.85}]
    trend_analysis: str
    confidence_score: float
    recommendations: List[str]

class CustomKPI(BaseModel):
    id: str = Field(default_factory=lambda: f"kpi_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    name: str
    description: str
    formula: str  # Simple formula like "leads_converted / total_leads * 100"
    category: str
    target_value: Optional[float] = None
    unit: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

class ReportType(str, Enum):
    PERFORMANCE = "performance"
    REVENUE = "revenue"
    CONVERSION = "conversion"
    PIPELINE = "pipeline"
    AGENT_ACTIVITY = "agent_activity"
    CUSTOM = "custom"

class ReportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"

class ReportFilter(BaseModel):
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, nin
    value: Any

class CustomReport(BaseModel):
    id: str = Field(default_factory=lambda: f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    name: str
    description: str
    report_type: ReportType
    data_sources: List[str]  # Collections to query: leads, agents, activities, etc.
    metrics: List[str]  # Specific metrics to include
    filters: List[ReportFilter] = []
    time_range: TimeRange = TimeRange.LAST_30_DAYS
    custom_start_date: Optional[datetime] = None
    custom_end_date: Optional[datetime] = None
    grouping: Optional[str] = None  # Group by field (e.g., "status", "agent_id")
    sorting: Optional[Dict[str, str]] = None  # {"field": "asc/desc"}
    visualization_config: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    is_scheduled: bool = False
    schedule_frequency: Optional[str] = None  # daily, weekly, monthly

class ReportResult(BaseModel):
    report_id: str
    report_name: str
    generated_at: datetime
    data: List[Dict[str, Any]]
    summary: Dict[str, Any]
    total_records: int
    filters_applied: List[ReportFilter]
    metadata: Dict[str, Any]

class AnalyticsEngine:
    """Advanced analytics engine for business intelligence"""
    
    def __init__(self):
        self.supported_metrics = [
            "total_leads", "hot_leads", "converted_leads", "conversion_rate",
            "pipeline_value", "average_deal_size", "sales_velocity",
            "agent_efficiency", "document_generation_rate", "email_open_rate",
            "workflow_success_rate", "customer_acquisition_cost", "lifetime_value"
        ]
    
    async def calculate_kpi_metrics(self, time_range: TimeRange = TimeRange.LAST_30_DAYS) -> List[KPIMetric]:
        """Calculate comprehensive KPI metrics for the given time range"""
        try:
            # Get date range
            end_date = datetime.utcnow()
            start_date = self._get_start_date(time_range, end_date)
            
            # Get previous period for comparison
            period_length = end_date - start_date
            previous_start = start_date - period_length
            previous_end = start_date
            
            # Get collections
            leads_collection = await get_leads_collection()
            agents_collection = await get_agents_collection()
            activities_collection = await get_activities_collection()
            documents_collection = await get_documents_collection()
            
            kpis = []
            
            # Lead Metrics
            total_leads = await leads_collection.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            prev_total_leads = await leads_collection.count_documents({
                "created_at": {"$gte": previous_start, "$lte": previous_end}
            })
            
            kpis.append(KPIMetric(
                name="Total Leads",
                value=total_leads,
                previous_value=prev_total_leads,
                change_percentage=self._calculate_change_percentage(total_leads, prev_total_leads),
                trend=self._calculate_trend(total_leads, prev_total_leads),
                unit="leads",
                format_type="number"
            ))
            
            # Conversion Rate
            converted_leads = await leads_collection.count_documents({
                "status": "converted",
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            prev_converted = await leads_collection.count_documents({
                "status": "converted", 
                "created_at": {"$gte": previous_start, "$lte": previous_end}
            })
            
            conversion_rate = (converted_leads / max(total_leads, 1)) * 100
            prev_conversion_rate = (prev_converted / max(prev_total_leads, 1)) * 100
            
            kpis.append(KPIMetric(
                name="Conversion Rate",
                value=round(conversion_rate, 2),
                previous_value=round(prev_conversion_rate, 2),
                change_percentage=self._calculate_change_percentage(conversion_rate, prev_conversion_rate),
                trend=self._calculate_trend(conversion_rate, prev_conversion_rate),
                target=15.0,
                target_percentage=round((conversion_rate / 15.0) * 100, 1) if conversion_rate > 0 else 0,
                unit="%",
                format_type="percentage"
            ))
            
            # Pipeline Value
            pipeline_result = await leads_collection.aggregate([
                {"$match": {
                    "status": {"$in": ["warm", "hot"]},
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$value"}}}
            ]).to_list(1)
            
            prev_pipeline_result = await leads_collection.aggregate([
                {"$match": {
                    "status": {"$in": ["warm", "hot"]},
                    "created_at": {"$gte": previous_start, "$lte": previous_end}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$value"}}}
            ]).to_list(1)
            
            pipeline_value = pipeline_result[0]["total"] if pipeline_result else 0
            prev_pipeline_value = prev_pipeline_result[0]["total"] if prev_pipeline_result else 0
            
            kpis.append(KPIMetric(
                name="Pipeline Value",
                value=pipeline_value,
                previous_value=prev_pipeline_value,
                change_percentage=self._calculate_change_percentage(pipeline_value, prev_pipeline_value),
                trend=self._calculate_trend(pipeline_value, prev_pipeline_value),
                unit="$",
                format_type="currency"
            ))
            
            # Average Deal Size
            if converted_leads > 0:
                avg_deal_result = await leads_collection.aggregate([
                    {"$match": {
                        "status": "converted",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }},
                    {"$group": {"_id": None, "avg": {"$avg": "$value"}}}
                ]).to_list(1)
                
                prev_avg_deal_result = await leads_collection.aggregate([
                    {"$match": {
                        "status": "converted",
                        "created_at": {"$gte": previous_start, "$lte": previous_end}
                    }},
                    {"$group": {"_id": None, "avg": {"$avg": "$value"}}}
                ]).to_list(1)
                
                avg_deal_size = avg_deal_result[0]["avg"] if avg_deal_result else 0
                prev_avg_deal_size = prev_avg_deal_result[0]["avg"] if prev_avg_deal_result else 0
                
                kpis.append(KPIMetric(
                    name="Average Deal Size",
                    value=round(avg_deal_size, 2),
                    previous_value=round(prev_avg_deal_size, 2),
                    change_percentage=self._calculate_change_percentage(avg_deal_size, prev_avg_deal_size),
                    trend=self._calculate_trend(avg_deal_size, prev_avg_deal_size),
                    unit="$",
                    format_type="currency"
                ))
            
            # Agent Efficiency
            total_agents = await agents_collection.count_documents({"status": "active"})
            if total_agents > 0:
                agent_activities = await activities_collection.count_documents({
                    "timestamp": {"$gte": start_date, "$lte": end_date},
                    "activity_type": {"$in": ["lead_created", "email_sent", "document_generated"]}
                })
                prev_agent_activities = await activities_collection.count_documents({
                    "timestamp": {"$gte": previous_start, "$lte": previous_end},
                    "activity_type": {"$in": ["lead_created", "email_sent", "document_generated"]}
                })
                
                efficiency = agent_activities / total_agents
                prev_efficiency = prev_agent_activities / total_agents
                
                kpis.append(KPIMetric(
                    name="Agent Efficiency",
                    value=round(efficiency, 2),
                    previous_value=round(prev_efficiency, 2),
                    change_percentage=self._calculate_change_percentage(efficiency, prev_efficiency),
                    trend=self._calculate_trend(efficiency, prev_efficiency),
                    unit="tasks/agent",
                    format_type="number"
                ))
            
            # Document Generation Rate
            documents_generated = await documents_collection.count_documents({
                "created_at": {"$gte": start_date, "$lte": end_date}
            })
            prev_documents = await documents_collection.count_documents({
                "created_at": {"$gte": previous_start, "$lte": previous_end}
            })
            
            days_in_period = max((end_date - start_date).days, 1)
            doc_rate = documents_generated / days_in_period
            prev_doc_rate = prev_documents / days_in_period
            
            kpis.append(KPIMetric(
                name="Document Generation Rate",
                value=round(doc_rate, 2),
                previous_value=round(prev_doc_rate, 2),
                change_percentage=self._calculate_change_percentage(doc_rate, prev_doc_rate),
                trend=self._calculate_trend(doc_rate, prev_doc_rate),
                unit="docs/day",
                format_type="number"
            ))
            
            # Sales Velocity (deals closed per day)
            velocity = converted_leads / days_in_period
            prev_velocity = prev_converted / days_in_period
            
            kpis.append(KPIMetric(
                name="Sales Velocity",
                value=round(velocity, 2),
                previous_value=round(prev_velocity, 2),
                change_percentage=self._calculate_change_percentage(velocity, prev_velocity),
                trend=self._calculate_trend(velocity, prev_velocity),
                target=0.5,
                target_percentage=round((velocity / 0.5) * 100, 1) if velocity > 0 else 0,
                unit="deals/day",
                format_type="number"
            ))
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculating KPI metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to calculate KPI metrics")
    
    async def calculate_roi_analysis(
        self, 
        investment_amount: float = None,
        time_range: TimeRange = TimeRange.LAST_30_DAYS
    ) -> ROIAnalysis:
        """Calculate comprehensive ROI analysis"""
        try:
            # Get date range
            end_date = datetime.utcnow()
            start_date = self._get_start_date(time_range, end_date)
            
            leads_collection = await get_leads_collection()
            
            # Calculate revenue from converted leads
            revenue_result = await leads_collection.aggregate([
                {"$match": {
                    "status": "converted",
                    "created_at": {"$gte": start_date, "$lte": end_date}
                }},
                {"$group": {"_id": None, "total_revenue": {"$sum": "$value"}}}
            ]).to_list(1)
            
            total_revenue = revenue_result[0]["total_revenue"] if revenue_result else 0
            
            # Estimate investment if not provided
            if investment_amount is None:
                # Estimate based on operational costs
                total_leads = await leads_collection.count_documents({
                    "created_at": {"$gte": start_date, "$lte": end_date}
                })
                # Estimate $50 per lead for marketing/operational costs
                investment_amount = total_leads * 50
            
            # Calculate ROI metrics
            net_profit = total_revenue - investment_amount
            roi_percentage = ((total_revenue - investment_amount) / max(investment_amount, 1)) * 100
            roi_ratio = f"1:{round(total_revenue / max(investment_amount, 1), 2)}"
            margin_percentage = (net_profit / max(total_revenue, 1)) * 100
            
            # Calculate payback period (simplified)
            days_in_period = (end_date - start_date).days
            if total_revenue > 0:
                daily_revenue = total_revenue / days_in_period
                payback_days = investment_amount / daily_revenue if daily_revenue > 0 else None
                payback_months = payback_days / 30 if payback_days else None
            else:
                payback_months = None
            
            return ROIAnalysis(
                investment=investment_amount,
                revenue=total_revenue,
                roi_percentage=round(roi_percentage, 2),
                roi_ratio=roi_ratio,
                payback_period_months=round(payback_months, 1) if payback_months else None,
                net_profit=net_profit,
                margin_percentage=round(margin_percentage, 2)
            )
            
        except Exception as e:
            logger.error(f"Error calculating ROI analysis: {e}")
            raise HTTPException(status_code=500, detail="Failed to calculate ROI analysis")
    
    async def generate_performance_forecast(
        self, 
        metric_name: str,
        forecast_days: int = 30
    ) -> PerformanceForecast:
        """Generate performance forecast using historical data"""
        try:
            # Get historical data for the last 60 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=60)
            
            leads_collection = await get_leads_collection()
            
            # Get daily metrics for forecasting
            daily_metrics = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                if metric_name == "conversion_rate":
                    total = await leads_collection.count_documents({
                        "created_at": {"$gte": current_date, "$lt": next_date}
                    })
                    converted = await leads_collection.count_documents({
                        "status": "converted",
                        "created_at": {"$gte": current_date, "$lt": next_date}
                    })
                    value = (converted / max(total, 1)) * 100
                    
                elif metric_name == "lead_generation":
                    value = await leads_collection.count_documents({
                        "created_at": {"$gte": current_date, "$lt": next_date}
                    })
                    
                elif metric_name == "pipeline_value":
                    result = await leads_collection.aggregate([
                        {"$match": {
                            "status": {"$in": ["warm", "hot"]},
                            "created_at": {"$gte": current_date, "$lt": next_date}
                        }},
                        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
                    ]).to_list(1)
                    value = result[0]["total"] if result else 0
                    
                else:
                    value = 0  # Default for unknown metrics
                
                daily_metrics.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "value": value
                })
                
                current_date = next_date
            
            # Simple trend analysis and forecasting
            values = [m["value"] for m in daily_metrics[-30:]]  # Last 30 days
            
            if len(values) > 1:
                # Calculate trend
                avg_change = sum(values[i] - values[i-1] for i in range(1, len(values))) / (len(values) - 1)
                current_value = values[-1]
                
                # Generate forecast
                forecasted_values = []
                forecast_value = current_value
                confidence = 0.9  # Start with high confidence, decrease over time
                
                for i in range(1, forecast_days + 1):
                    forecast_value += avg_change
                    confidence = max(0.3, confidence - (i * 0.02))  # Decrease confidence over time
                    
                    forecast_date = end_date + timedelta(days=i)
                    forecasted_values.append({
                        "date": forecast_date.strftime("%Y-%m-%d"),
                        "value": round(max(0, forecast_value), 2),
                        "confidence": round(confidence, 2)
                    })
                
                # Generate trend analysis
                if avg_change > 0:
                    trend_analysis = f"Positive trend detected. Average daily increase of {abs(avg_change):.2f}."
                elif avg_change < 0:
                    trend_analysis = f"Negative trend detected. Average daily decrease of {abs(avg_change):.2f}."
                else:
                    trend_analysis = "Stable trend with minimal fluctuation."
                
                # Generate recommendations
                recommendations = []
                if avg_change > 0:
                    recommendations.append("Continue current strategies as they show positive results")
                    recommendations.append("Consider scaling successful campaigns")
                else:
                    recommendations.append("Review and optimize current strategies")
                    recommendations.append("Consider A/B testing new approaches")
                
                recommendations.append("Monitor key performance indicators closely")
                recommendations.append("Set up automated alerts for significant changes")
                
                return PerformanceForecast(
                    metric_name=metric_name,
                    current_value=current_value,
                    forecasted_values=forecasted_values,
                    trend_analysis=trend_analysis,
                    confidence_score=round(mean([f["confidence"] for f in forecasted_values]), 2),
                    recommendations=recommendations
                )
            else:
                # Not enough data for forecasting
                return PerformanceForecast(
                    metric_name=metric_name,
                    current_value=0,
                    forecasted_values=[],
                    trend_analysis="Insufficient historical data for trend analysis",
                    confidence_score=0.1,
                    recommendations=["Collect more data over time", "Focus on data consistency"]
                )
            
        except Exception as e:
            logger.error(f"Error generating performance forecast: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate performance forecast")
    
    def _get_start_date(self, time_range: TimeRange, end_date: datetime) -> datetime:
        """Get start date based on time range"""
        if time_range == TimeRange.TODAY:
            return end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == TimeRange.YESTERDAY:
            yesterday = end_date - timedelta(days=1)
            return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == TimeRange.LAST_7_DAYS:
            return end_date - timedelta(days=7)
        elif time_range == TimeRange.LAST_30_DAYS:
            return end_date - timedelta(days=30)
        elif time_range == TimeRange.LAST_90_DAYS:
            return end_date - timedelta(days=90)
        elif time_range == TimeRange.LAST_YEAR:
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=30)  # Default to last 30 days
    
    def _calculate_change_percentage(self, current: float, previous: float) -> float:
        """Calculate percentage change between two values"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)
    
    def _calculate_trend(self, current: float, previous: float) -> TrendDirection:
        """Calculate trend direction"""
        if current > previous:
            return TrendDirection.UP
        elif current < previous:
            return TrendDirection.DOWN
        else:
            return TrendDirection.STABLE

# Global analytics engine instance
analytics_engine = AnalyticsEngine()

# API Endpoints
@router.get("/kpis", response_model=List[KPIMetric])
async def get_kpi_metrics(time_range: TimeRange = TimeRange.LAST_30_DAYS):
    """Get comprehensive KPI metrics for the specified time range"""
    try:
        return await analytics_engine.calculate_kpi_metrics(time_range)
    except Exception as e:
        logger.error(f"Error getting KPI metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve KPI metrics")

@router.get("/roi", response_model=ROIAnalysis)
async def get_roi_analysis(
    investment: Optional[float] = Query(None, description="Investment amount (auto-calculated if not provided)"),
    time_range: TimeRange = TimeRange.LAST_30_DAYS
):
    """Get comprehensive ROI analysis"""
    try:
        return await analytics_engine.calculate_roi_analysis(investment, time_range)
    except Exception as e:
        logger.error(f"Error getting ROI analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ROI analysis")

@router.get("/forecast/{metric_name}", response_model=PerformanceForecast)
async def get_performance_forecast(
    metric_name: str,
    forecast_days: int = Query(30, ge=1, le=365, description="Number of days to forecast")
):
    """Get performance forecast for a specific metric"""
    try:
        return await analytics_engine.generate_performance_forecast(metric_name, forecast_days)
    except Exception as e:
        logger.error(f"Error getting performance forecast: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance forecast")

@router.get("/metrics/available")
async def get_available_metrics():
    """Get list of available metrics for analytics"""
    return {
        "metrics": analytics_engine.supported_metrics,
        "time_ranges": [range_type.value for range_type in TimeRange],
        "metric_types": [metric_type.value for metric_type in MetricType]
    }

@router.get("/dashboard/summary")
async def get_analytics_dashboard_summary(time_range: TimeRange = TimeRange.LAST_30_DAYS):
    """Get comprehensive analytics dashboard summary"""
    try:
        # Get KPIs
        kpis = await analytics_engine.calculate_kpi_metrics(time_range)
        
        # Get ROI analysis
        roi = await analytics_engine.calculate_roi_analysis(time_range=time_range)
        
        # Get key forecasts
        conversion_forecast = await analytics_engine.generate_performance_forecast("conversion_rate", 14)
        lead_forecast = await analytics_engine.generate_performance_forecast("lead_generation", 14)
        
        return {
            "kpis": kpis,
            "roi_analysis": roi,
            "forecasts": {
                "conversion_rate": conversion_forecast,
                "lead_generation": lead_forecast
            },
            "summary_insights": {
                "top_performing_kpi": max(kpis, key=lambda x: x.change_percentage or 0).name if kpis else None,
                "roi_status": "positive" if roi.roi_percentage > 0 else "negative",
                "forecast_confidence": round(mean([conversion_forecast.confidence_score, lead_forecast.confidence_score]), 2),
                "recommendations_count": len(conversion_forecast.recommendations) + len(lead_forecast.recommendations)
            },
            "timestamp": datetime.utcnow().isoformat(),
            "time_range": time_range.value
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics dashboard summary")