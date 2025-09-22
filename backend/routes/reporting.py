from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import logging
import json
import uuid
from enum import Enum
from pydantic import BaseModel, Field
import csv
from io import StringIO

from database import (
    get_leads_collection,
    get_agents_collection, 
    get_activities_collection,
    get_documents_collection,
    get_workflows_collection
)

router = APIRouter(prefix="/reporting", tags=["reporting"])
logger = logging.getLogger(__name__)

# Enums for reporting
class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    DONUT = "donut"
    HEATMAP = "heatmap"

class DataSource(str, Enum):
    LEADS = "leads"
    AGENTS = "agents"
    ACTIVITIES = "activities"
    DOCUMENTS = "documents"
    WORKFLOWS = "workflows"
    CUSTOM_QUERY = "custom_query"

class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"

class AggregationType(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    DISTINCT_COUNT = "distinct_count"

# Pydantic models for reporting
class ChartConfig(BaseModel):
    chart_type: ChartType
    title: str
    x_axis_field: str
    y_axis_field: str
    color_field: Optional[str] = None
    aggregation: AggregationType = AggregationType.COUNT
    sort_by: Optional[str] = None
    sort_order: str = "desc"  # asc or desc
    limit: Optional[int] = None

class FilterConfig(BaseModel):
    field: str
    operator: str  # equals, not_equals, greater_than, less_than, contains, in, between
    value: Union[str, int, float, List[Any]]
    condition: str = "AND"  # AND or OR

class CustomReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    data_source: DataSource
    fields: List[str]  # Fields to include in the report
    filters: List[FilterConfig] = Field(default_factory=list)
    charts: List[ChartConfig] = Field(default_factory=list)
    schedule: Optional[str] = None  # Cron expression for scheduled reports
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    is_public: bool = False

class ReportData(BaseModel):
    report_id: str
    data: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    summary: Dict[str, Any]
    generated_at: datetime
    total_records: int
    filters_applied: List[FilterConfig]

class DashboardWidget(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    widget_type: str  # chart, metric, table, text
    data_source: DataSource
    configuration: Dict[str, Any]
    position: Dict[str, int]  # {x: 0, y: 0, width: 4, height: 3}
    refresh_interval: int = 300  # seconds

class CustomDashboard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    widgets: List[DashboardWidget] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    is_public: bool = False

class ReportingEngine:
    """Advanced reporting engine for custom reports and dashboards"""
    
    def __init__(self):
        self.collection_mapping = {
            DataSource.LEADS: get_leads_collection,
            DataSource.AGENTS: get_agents_collection,
            DataSource.ACTIVITIES: get_activities_collection,
            DataSource.DOCUMENTS: get_documents_collection,
            DataSource.WORKFLOWS: get_workflows_collection
        }
    
    async def generate_report_data(self, report: CustomReport) -> ReportData:
        """Generate data for a custom report"""
        try:
            # Get the appropriate collection
            if report.data_source not in self.collection_mapping:
                raise ValueError(f"Unsupported data source: {report.data_source}")
            
            collection = await self.collection_mapping[report.data_source]()
            
            # Build MongoDB query from filters
            query = self._build_query_from_filters(report.filters)
            
            # Get data with field projection
            projection = {field: 1 for field in report.fields} if report.fields else None
            cursor = collection.find(query, projection)
            
            # Apply sorting and limiting if needed
            # For now, we'll get all data and process it
            raw_data = await cursor.to_list(1000)  # Limit to 1000 records for performance
            
            # Process data for charts
            chart_data = []
            for chart_config in report.charts:
                chart_result = await self._generate_chart_data(raw_data, chart_config)
                chart_data.append(chart_result)
            
            # Generate summary statistics
            summary = self._generate_summary_stats(raw_data, report.fields)
            
            return ReportData(
                report_id=report.id,
                data=raw_data,
                charts=chart_data,
                summary=summary,
                generated_at=datetime.utcnow(),
                total_records=len(raw_data),
                filters_applied=report.filters
            )
            
        except Exception as e:
            logger.error(f"Error generating report data: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate report data")
    
    async def _generate_chart_data(self, data: List[Dict], chart_config: ChartConfig) -> Dict[str, Any]:
        """Generate chart data from raw data"""
        try:
            chart_data = {
                "chart_type": chart_config.chart_type.value,
                "title": chart_config.title,
                "data": [],
                "config": chart_config.dict()
            }
            
            if chart_config.chart_type == ChartType.PIE or chart_config.chart_type == ChartType.DONUT:
                # For pie/donut charts, group by x_axis_field and count/sum
                grouped_data = {}
                for item in data:
                    key = str(item.get(chart_config.x_axis_field, 'Unknown'))
                    if key not in grouped_data:
                        grouped_data[key] = []
                    grouped_data[key].append(item)
                
                for key, items in grouped_data.items():
                    if chart_config.aggregation == AggregationType.COUNT:
                        value = len(items)
                    elif chart_config.aggregation == AggregationType.SUM:
                        value = sum(item.get(chart_config.y_axis_field, 0) for item in items)
                    elif chart_config.aggregation == AggregationType.AVERAGE:
                        values = [item.get(chart_config.y_axis_field, 0) for item in items]
                        value = sum(values) / len(values) if values else 0
                    else:
                        value = len(items)
                    
                    chart_data["data"].append({
                        "name": key,
                        "value": round(value, 2) if isinstance(value, float) else value
                    })
            
            elif chart_config.chart_type in [ChartType.LINE, ChartType.BAR, ChartType.AREA]:
                # For line/bar/area charts, use x and y axis fields
                processed_data = []
                for item in data:
                    x_value = item.get(chart_config.x_axis_field)
                    y_value = item.get(chart_config.y_axis_field, 0)
                    
                    # Handle date formatting
                    if isinstance(x_value, datetime):
                        x_value = x_value.strftime("%Y-%m-%d")
                    
                    processed_data.append({
                        "x": str(x_value) if x_value is not None else "Unknown",
                        "y": y_value,
                        **({chart_config.color_field: item.get(chart_config.color_field)} if chart_config.color_field else {})
                    })
                
                # Sort if specified
                if chart_config.sort_by:
                    reverse = chart_config.sort_order == "desc"
                    processed_data.sort(key=lambda x: x.get(chart_config.sort_by, 0), reverse=reverse)
                
                # Limit if specified
                if chart_config.limit:
                    processed_data = processed_data[:chart_config.limit]
                
                chart_data["data"] = processed_data
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error generating chart data: {e}")
            return {
                "chart_type": chart_config.chart_type.value,
                "title": chart_config.title,
                "data": [],
                "error": str(e)
            }
    
    def _build_query_from_filters(self, filters: List[FilterConfig]) -> Dict[str, Any]:
        """Build MongoDB query from filter configurations"""
        if not filters:
            return {}
        
        query_parts = []
        
        for filter_config in filters:
            field = filter_config.field
            operator = filter_config.operator
            value = filter_config.value
            
            if operator == "equals":
                query_parts.append({field: value})
            elif operator == "not_equals":
                query_parts.append({field: {"$ne": value}})
            elif operator == "greater_than":
                query_parts.append({field: {"$gt": value}})
            elif operator == "less_than":
                query_parts.append({field: {"$lt": value}})
            elif operator == "contains":
                query_parts.append({field: {"$regex": str(value), "$options": "i"}})
            elif operator == "in":
                query_parts.append({field: {"$in": value if isinstance(value, list) else [value]}})
            elif operator == "between" and isinstance(value, list) and len(value) == 2:
                query_parts.append({field: {"$gte": value[0], "$lte": value[1]}})
        
        # For now, combine all filters with AND logic
        if len(query_parts) == 1:
            return query_parts[0]
        elif len(query_parts) > 1:
            return {"$and": query_parts}
        else:
            return {}
    
    def _generate_summary_stats(self, data: List[Dict], fields: List[str]) -> Dict[str, Any]:
        """Generate summary statistics for the report data"""
        if not data:
            return {"total_records": 0}
        
        summary = {
            "total_records": len(data),
            "field_stats": {}
        }
        
        for field in fields:
            values = [item.get(field) for item in data if item.get(field) is not None]
            
            if values:
                if all(isinstance(v, (int, float)) for v in values):
                    # Numeric field
                    summary["field_stats"][field] = {
                        "type": "numeric",
                        "count": len(values),
                        "sum": sum(values),
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
                else:
                    # Text/other field
                    unique_values = set(str(v) for v in values)
                    summary["field_stats"][field] = {
                        "type": "categorical",
                        "count": len(values),
                        "unique_count": len(unique_values),
                        "most_common": max(unique_values, key=lambda x: sum(1 for v in values if str(v) == x))
                    }
        
        return summary
    
    async def export_report_data(self, report_data: ReportData, format: ReportFormat) -> str:
        """Export report data to specified format"""
        try:
            if format == ReportFormat.JSON:
                return json.dumps(report_data.dict(), indent=2, default=str)
            
            elif format == ReportFormat.CSV:
                if not report_data.data:
                    return "No data available"
                
                output = StringIO()
                if report_data.data:
                    fieldnames = report_data.data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in report_data.data:
                        # Convert datetime objects to strings
                        cleaned_row = {}
                        for k, v in row.items():
                            if isinstance(v, datetime):
                                cleaned_row[k] = v.isoformat()
                            else:
                                cleaned_row[k] = v
                        writer.writerow(cleaned_row)
                
                return output.getvalue()
            
            else:
                return f"Export format {format} not yet implemented"
                
        except Exception as e:
            logger.error(f"Error exporting report data: {e}")
            raise HTTPException(status_code=500, detail="Failed to export report data")

# Global reporting engine instance
reporting_engine = ReportingEngine()

# API Endpoints
@router.post("/reports", response_model=CustomReport)
async def create_custom_report(report: CustomReport):
    """Create a new custom report"""
    try:
        # In a real implementation, this would save to database
        # For now, we'll just validate and return the report
        
        logger.info(f"Created custom report: {report.name}")
        return report
        
    except Exception as e:
        logger.error(f"Error creating custom report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create custom report")

@router.get("/reports")
async def get_custom_reports():
    """Get all custom reports (placeholder - would query database)"""
    try:
        # Sample reports for demonstration
        sample_reports = [
            {
                "id": "rpt_lead_analysis",
                "name": "Lead Analysis Report",
                "description": "Comprehensive analysis of lead generation and conversion",
                "data_source": "leads",
                "created_at": datetime.utcnow().isoformat(),
                "is_public": True
            },
            {
                "id": "rpt_agent_performance",
                "name": "Agent Performance Report",
                "description": "Performance metrics for all digital employees",
                "data_source": "agents",
                "created_at": datetime.utcnow().isoformat(),
                "is_public": True
            },
            {
                "id": "rpt_revenue_analysis",
                "name": "Revenue Analysis",
                "description": "Revenue tracking and forecasting report",
                "data_source": "leads",
                "created_at": datetime.utcnow().isoformat(),
                "is_public": False
            }
        ]
        
        return {"reports": sample_reports}
        
    except Exception as e:
        logger.error(f"Error getting custom reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve custom reports")

@router.post("/reports/{report_id}/generate", response_model=ReportData)
async def generate_report(report_id: str, report: CustomReport):
    """Generate data for a specific report"""
    try:
        return await reporting_engine.generate_report_data(report)
        
    except Exception as e:
        logger.error(f"Error generating report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

@router.post("/reports/{report_id}/export")
async def export_report(
    report_id: str, 
    report_data: ReportData,
    format: ReportFormat = ReportFormat.JSON
):
    """Export report data in specified format"""
    try:
        exported_data = await reporting_engine.export_report_data(report_data, format)
        
        return {
            "report_id": report_id,
            "format": format.value,
            "data": exported_data,
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting report {report_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to export report")

@router.get("/data-sources")
async def get_available_data_sources():
    """Get available data sources and their fields"""
    try:
        data_sources = {
            "leads": {
                "name": "Leads",
                "fields": ["id", "name", "email", "phone", "company", "status", "value", "source", "created_at", "assigned_agent_id", "score"],
                "description": "Lead and prospect data"
            },
            "agents": {
                "name": "Digital Employees",
                "fields": ["id", "name", "type", "status", "autonomy_level", "created_at", "metrics"],
                "description": "AI agent information and performance"
            },
            "activities": {
                "name": "Activities",
                "fields": ["id", "agent_name", "activity_type", "description", "timestamp", "metadata"],
                "description": "System activities and interactions"
            },
            "documents": {
                "name": "Documents",
                "fields": ["id", "title", "type", "created_at", "client_name", "metadata"],
                "description": "Generated documents and templates"
            },
            "workflows": {
                "name": "Workflows",
                "fields": ["id", "name", "description", "status", "created_at", "execution_count"],
                "description": "Automation workflows and executions"
            }
        }
        
        return {
            "data_sources": data_sources,
            "chart_types": [chart_type.value for chart_type in ChartType],
            "aggregation_types": [agg_type.value for agg_type in AggregationType],
            "export_formats": [format_type.value for format_type in ReportFormat]
        }
        
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve data sources")

@router.post("/dashboards", response_model=CustomDashboard)
async def create_custom_dashboard(dashboard: CustomDashboard):
    """Create a new custom dashboard"""
    try:
        # In a real implementation, this would save to database
        logger.info(f"Created custom dashboard: {dashboard.name}")
        return dashboard
        
    except Exception as e:
        logger.error(f"Error creating custom dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to create custom dashboard")

@router.get("/dashboards")
async def get_custom_dashboards():
    """Get all custom dashboards"""
    try:
        # Sample dashboards for demonstration
        sample_dashboards = [
            {
                "id": "dash_executive",
                "name": "Executive Dashboard",
                "description": "High-level overview for executives",
                "widgets": [
                    {
                        "id": "widget_revenue",
                        "title": "Revenue Overview",
                        "widget_type": "chart",
                        "data_source": "leads",
                        "configuration": {"chart_type": "line"},
                        "position": {"x": 0, "y": 0, "width": 6, "height": 4}
                    },
                    {
                        "id": "widget_kpis",
                        "title": "Key Metrics",
                        "widget_type": "metric",
                        "data_source": "leads",
                        "configuration": {"metrics": ["conversion_rate", "total_leads"]},
                        "position": {"x": 6, "y": 0, "width": 6, "height": 4}
                    }
                ],
                "created_at": datetime.utcnow().isoformat(),
                "is_public": True
            },
            {
                "id": "dash_sales",
                "name": "Sales Performance",  
                "description": "Detailed sales analytics and forecasts",
                "widgets": [],
                "created_at": datetime.utcnow().isoformat(),
                "is_public": False
            }
        ]
        
        return {"dashboards": sample_dashboards}
        
    except Exception as e:
        logger.error(f"Error getting custom dashboards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve custom dashboards")

@router.get("/templates")
async def get_report_templates():
    """Get predefined report templates"""
    try:
        templates = [
            {
                "id": "template_lead_conversion",
                "name": "Lead Conversion Analysis",
                "description": "Track lead conversion rates and identify trends",
                "data_source": "leads",
                "recommended_charts": ["line", "pie", "bar"],
                "key_metrics": ["conversion_rate", "total_leads", "pipeline_value"],
                "category": "Sales"
            },
            {
                "id": "template_agent_productivity",
                "name": "Agent Productivity Report",
                "description": "Monitor digital employee performance and efficiency",
                "data_source": "agents",
                "recommended_charts": ["bar", "scatter", "heatmap"],
                "key_metrics": ["tasks_completed", "response_time", "success_rate"],
                "category": "Operations"
            },
            {
                "id": "template_revenue_forecast",
                "name": "Revenue Forecasting",
                "description": "Project future revenue based on current pipeline",
                "data_source": "leads",
                "recommended_charts": ["line", "area"],
                "key_metrics": ["projected_revenue", "pipeline_value", "close_rate"],
                "category": "Finance"
            },
            {
                "id": "template_activity_summary",
                "name": "Activity Summary Report",
                "description": "Overview of all system activities and interactions",
                "data_source": "activities",
                "recommended_charts": ["bar", "pie", "line"],
                "key_metrics": ["total_activities", "activity_types", "daily_volume"],
                "category": "Operations"
            }
        ]
        
        return {
            "templates": templates,
            "categories": list(set(t["category"] for t in templates))
        }
        
    except Exception as e:
        logger.error(f"Error getting report templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report templates")

@router.post("/templates/{template_id}/create")
async def create_report_from_template(template_id: str, report_name: str):
    """Create a new report from a predefined template"""
    try:
        # Sample template instantiation
        template_configs = {
            "template_lead_conversion": CustomReport(
                name=report_name,
                description="Lead conversion tracking report created from template",
                data_source=DataSource.LEADS,
                fields=["name", "status", "value", "created_at", "source"],
                charts=[
                    ChartConfig(
                        chart_type=ChartType.PIE,
                        title="Leads by Status",
                        x_axis_field="status",
                        y_axis_field="value",
                        aggregation=AggregationType.COUNT
                    ),
                    ChartConfig(
                        chart_type=ChartType.LINE,
                        title="Lead Generation Over Time",
                        x_axis_field="created_at",
                        y_axis_field="value",
                        aggregation=AggregationType.COUNT
                    )
                ]
            ),
            "template_agent_productivity": CustomReport(
                name=report_name,
                description="Agent productivity report created from template",
                data_source=DataSource.AGENTS,
                fields=["name", "type", "status", "created_at", "metrics"],
                charts=[
                    ChartConfig(
                        chart_type=ChartType.BAR,
                        title="Agents by Type",
                        x_axis_field="type",
                        y_axis_field="name",
                        aggregation=AggregationType.COUNT
                    )
                ]
            )
        }
        
        if template_id not in template_configs:
            raise HTTPException(status_code=404, detail="Template not found")
        
        report = template_configs[template_id]
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating report from template {template_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create report from template")