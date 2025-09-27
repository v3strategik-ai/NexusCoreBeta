from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os
import json
import csv
import io
import zipfile
import uuid
from pydantic import BaseModel, Field
from bson import ObjectId
import asyncio

from database import get_database

router = APIRouter(prefix="/data-export", tags=["data-export"])
logger = logging.getLogger(__name__)

# Pydantic Models for Data Export API
class ExportRequest(BaseModel):
    tenant_id: str = Field(description="Tenant ID for data export")
    export_type: str = Field(description="Type of export: full, agents, leads, workflows, audit")
    format: str = Field(default="json", description="Export format: json, csv, excel")
    date_range: Optional[Dict[str, str]] = Field(default=None, description="Date range for export")
    include_metadata: bool = Field(default=True, description="Include metadata in export")
    compress: bool = Field(default=True, description="Compress export file")

class BackupRequest(BaseModel):
    tenant_id: str = Field(description="Tenant ID for backup")
    backup_type: str = Field(default="full", description="Type of backup: full, incremental")
    include_audit_logs: bool = Field(default=True, description="Include audit logs in backup")
    retention_days: int = Field(default=90, description="Backup retention in days")

class ExportStatus(BaseModel):
    export_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None

class BackupStatus(BaseModel):
    backup_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    created_at: datetime
    completed_at: Optional[datetime] = None
    backup_path: Optional[str] = None
    backup_size: Optional[int] = None
    error_message: Optional[str] = None

# In-memory storage for export/backup status (use Redis in production)
export_jobs = {}
backup_jobs = {}

# Helper Functions
def serialize_document(doc):
    """Convert MongoDB document to JSON serializable format"""
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                result['id'] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                result[key] = serialize_document(value)
            elif isinstance(value, list):
                result[key] = [serialize_document(item) if isinstance(item, (dict, list)) else item for item in value]
            else:
                result[key] = value
        return result
    elif isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    else:
        return doc

async def export_collection_data(collection_name: str, tenant_id: str, date_range: Optional[Dict] = None):
    """Export data from a specific collection"""
    try:
        db = await get_database()
        collection = db[collection_name]
        
        # Build query
        query = {"tenant_id": tenant_id}
        
        if date_range and 'start_date' in date_range and 'end_date' in date_range:
            query["created_at"] = {
                "$gte": datetime.fromisoformat(date_range['start_date']),
                "$lte": datetime.fromisoformat(date_range['end_date'])
            }
        
        # Get documents
        cursor = collection.find(query)
        documents = []
        
        async for doc in cursor:
            documents.append(serialize_document(doc))
        
        return documents
        
    except Exception as e:
        logger.error(f"Error exporting collection {collection_name}: {e}")
        return []

async def create_export_file(export_id: str, export_data: Dict, format: str, compress: bool = True):
    """Create export file in specified format"""
    try:
        export_dir = "/tmp/exports"
        os.makedirs(export_dir, exist_ok=True)
        
        if format == "json":
            file_path = f"{export_dir}/{export_id}.json"
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        
        elif format == "csv":
            file_path = f"{export_dir}/{export_id}.csv"
            # For CSV, we'll need to flatten the data structure
            with open(file_path, 'w', newline='') as csvfile:
                if export_data and len(export_data) > 0:
                    # Get all possible fieldnames from all records
                    fieldnames = set()
                    for category_data in export_data.values():
                        if isinstance(category_data, list) and category_data:
                            for record in category_data:
                                if isinstance(record, dict):
                                    fieldnames.update(record.keys())
                    
                    writer = csv.DictWriter(csvfile, fieldnames=list(fieldnames))
                    writer.writeheader()
                    
                    # Write data from all categories
                    for category, data in export_data.items():
                        if isinstance(data, list):
                            for record in data:
                                if isinstance(record, dict):
                                    # Flatten nested objects
                                    flattened_record = {}
                                    for key, value in record.items():
                                        if isinstance(value, (dict, list)):
                                            flattened_record[key] = json.dumps(value)
                                        else:
                                            flattened_record[key] = value
                                    writer.writerow(flattened_record)
        
        # Compress if requested
        if compress and format in ["json", "csv"]:
            zip_path = f"{file_path}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, os.path.basename(file_path))
            
            # Remove original file and use zip
            os.remove(file_path)
            file_path = zip_path
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return file_path, file_size
        
    except Exception as e:
        logger.error(f"Error creating export file: {e}")
        raise

async def process_export_job(export_id: str, export_request: ExportRequest):
    """Background task to process export job"""
    try:
        # Update status to processing
        export_jobs[export_id]["status"] = "processing"
        export_jobs[export_id]["progress"] = 10
        
        db = await get_database()
        export_data = {}
        
        # Determine collections to export based on type
        collections_to_export = []
        
        if export_request.export_type == "full":
            collections_to_export = ["agents", "leads", "workflows", "documents", "users", "audit_logs"]
        elif export_request.export_type == "agents":
            collections_to_export = ["agents"]
        elif export_request.export_type == "leads":
            collections_to_export = ["leads"]
        elif export_request.export_type == "workflows":
            collections_to_export = ["workflows"]
        elif export_request.export_type == "audit":
            collections_to_export = ["audit_logs"]
        
        # Export each collection
        progress_increment = 70 // len(collections_to_export) if collections_to_export else 0
        
        for i, collection_name in enumerate(collections_to_export):
            logger.info(f"Exporting collection: {collection_name}")
            
            collection_data = await export_collection_data(
                collection_name, 
                export_request.tenant_id, 
                export_request.date_range
            )
            
            export_data[collection_name] = collection_data
            
            # Update progress
            export_jobs[export_id]["progress"] = 10 + ((i + 1) * progress_increment)
        
        # Add metadata if requested
        if export_request.include_metadata:
            export_data["metadata"] = {
                "export_id": export_id,
                "tenant_id": export_request.tenant_id,
                "export_type": export_request.export_type,
                "format": export_request.format,
                "created_at": export_jobs[export_id]["created_at"].isoformat(),
                "date_range": export_request.date_range,
                "total_records": sum(len(data) if isinstance(data, list) else 0 for data in export_data.values()),
                "collections_included": list(export_data.keys())
            }
        
        # Create export file
        export_jobs[export_id]["progress"] = 85
        
        file_path, file_size = await create_export_file(
            export_id, 
            export_data, 
            export_request.format, 
            export_request.compress
        )
        
        # Update job status
        export_jobs[export_id].update({
            "status": "completed",
            "progress": 100,
            "completed_at": datetime.utcnow(),
            "file_path": file_path,
            "file_size": file_size
        })
        
        logger.info(f"Export job {export_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Export job {export_id} failed: {e}")
        export_jobs[export_id].update({
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.utcnow()
        })

async def process_backup_job(backup_id: str, backup_request: BackupRequest):
    """Background task to process backup job"""
    try:
        # Update status to processing
        backup_jobs[backup_id]["status"] = "processing"
        backup_jobs[backup_id]["progress"] = 10
        
        # Create backup directory
        backup_dir = f"/tmp/backups/{backup_id}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Determine what to backup
        collections_to_backup = ["tenants", "users", "agents", "leads", "workflows", "documents", "knowledge_files"]
        
        if backup_request.include_audit_logs:
            collections_to_backup.append("audit_logs")
        
        # Backup each collection
        progress_increment = 70 // len(collections_to_backup)
        
        for i, collection_name in enumerate(collections_to_backup):
            logger.info(f"Backing up collection: {collection_name}")
            
            if backup_request.backup_type == "full":
                # Full backup - export all data for tenant
                collection_data = await export_collection_data(collection_name, backup_request.tenant_id)
            else:
                # Incremental backup - only recent changes (last 24 hours)
                date_range = {
                    "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                    "end_date": datetime.utcnow().isoformat()
                }
                collection_data = await export_collection_data(collection_name, backup_request.tenant_id, date_range)
            
            # Save collection data to separate file
            collection_file = f"{backup_dir}/{collection_name}.json"
            with open(collection_file, 'w') as f:
                json.dump(collection_data, f, indent=2, default=str)
            
            # Update progress
            backup_jobs[backup_id]["progress"] = 10 + ((i + 1) * progress_increment)
        
        # Create backup metadata
        backup_metadata = {
            "backup_id": backup_id,
            "tenant_id": backup_request.tenant_id,
            "backup_type": backup_request.backup_type,
            "created_at": backup_jobs[backup_id]["created_at"].isoformat(),
            "collections": collections_to_backup,
            "retention_days": backup_request.retention_days,
            "include_audit_logs": backup_request.include_audit_logs
        }
        
        metadata_file = f"{backup_dir}/backup_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(backup_metadata, f, indent=2)
        
        # Create compressed backup archive
        backup_jobs[backup_id]["progress"] = 85
        
        backup_archive = f"/tmp/backups/{backup_id}.zip"
        with zipfile.ZipFile(backup_archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_dir)
                    zipf.write(file_path, arcname)
        
        # Get backup size
        backup_size = os.path.getsize(backup_archive)
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(backup_dir)
        
        # Update job status
        backup_jobs[backup_id].update({
            "status": "completed",
            "progress": 100,
            "completed_at": datetime.utcnow(),
            "backup_path": backup_archive,
            "backup_size": backup_size
        })
        
        logger.info(f"Backup job {backup_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Backup job {backup_id} failed: {e}")
        backup_jobs[backup_id].update({
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.utcnow()
        })

# API Endpoints

@router.post("/export", response_model=ExportStatus)
async def create_export_job(export_request: ExportRequest, background_tasks: BackgroundTasks):
    """Create a new data export job"""
    try:
        export_id = str(uuid.uuid4())
        
        # Initialize export job
        export_job = {
            "export_id": export_id,
            "status": "pending",
            "progress": 0,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "file_path": None,
            "file_size": None,
            "error_message": None
        }
        
        export_jobs[export_id] = export_job
        
        # Start background processing
        background_tasks.add_task(process_export_job, export_id, export_request)
        
        return ExportStatus(**export_job)
        
    except Exception as e:
        logger.error(f"Error creating export job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create export job")

@router.get("/export/{export_id}/status", response_model=ExportStatus)
async def get_export_status(export_id: str):
    """Get export job status"""
    try:
        if export_id not in export_jobs:
            raise HTTPException(status_code=404, detail="Export job not found")
        
        return ExportStatus(**export_jobs[export_id])
        
    except Exception as e:
        logger.error(f"Error getting export status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get export status")

@router.get("/export/{export_id}/download")
async def download_export_file(export_id: str):
    """Download completed export file"""
    try:
        if export_id not in export_jobs:
            raise HTTPException(status_code=404, detail="Export job not found")
        
        job = export_jobs[export_id]
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Export job is {job['status']}, not ready for download")
        
        if not job["file_path"] or not os.path.exists(job["file_path"]):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        filename = os.path.basename(job["file_path"])
        
        return FileResponse(
            job["file_path"],
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"Error downloading export file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download export file")

@router.post("/backup", response_model=BackupStatus)
async def create_backup_job(backup_request: BackupRequest, background_tasks: BackgroundTasks):
    """Create a new backup job"""
    try:
        backup_id = str(uuid.uuid4())
        
        # Initialize backup job
        backup_job = {
            "backup_id": backup_id,
            "status": "pending", 
            "progress": 0,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "backup_path": None,
            "backup_size": None,
            "error_message": None
        }
        
        backup_jobs[backup_id] = backup_job
        
        # Start background processing
        background_tasks.add_task(process_backup_job, backup_id, backup_request)
        
        return BackupStatus(**backup_job)
        
    except Exception as e:
        logger.error(f"Error creating backup job: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup job")

@router.get("/backup/{backup_id}/status", response_model=BackupStatus)
async def get_backup_status(backup_id: str):
    """Get backup job status"""
    try:
        if backup_id not in backup_jobs:
            raise HTTPException(status_code=404, detail="Backup job not found")
        
        return BackupStatus(**backup_jobs[backup_id])
        
    except Exception as e:
        logger.error(f"Error getting backup status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backup status")

@router.get("/backup/{backup_id}/download")
async def download_backup_file(backup_id: str):
    """Download completed backup file"""
    try:
        if backup_id not in backup_jobs:
            raise HTTPException(status_code=404, detail="Backup job not found")
        
        job = backup_jobs[backup_id]
        
        if job["status"] != "completed":
            raise HTTPException(status_code=400, detail=f"Backup job is {job['status']}, not ready for download")
        
        if not job["backup_path"] or not os.path.exists(job["backup_path"]):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        filename = f"backup_{backup_id}.zip"
        
        return FileResponse(
            job["backup_path"],
            filename=filename,
            media_type="application/zip"
        )
        
    except Exception as e:
        logger.error(f"Error downloading backup file: {e}")
        raise HTTPException(status_code=500, detail="Failed to download backup file")

@router.get("/jobs")
async def get_all_jobs(tenant_id: Optional[str] = Query(None)):
    """Get all export and backup jobs"""
    try:
        result = {
            "export_jobs": list(export_jobs.values()),
            "backup_jobs": list(backup_jobs.values())
        }
        
        # Filter by tenant if provided
        if tenant_id:
            # Note: We'd need to store tenant_id with jobs to filter properly
            pass
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get jobs")

@router.delete("/cleanup")
async def cleanup_old_files(days_to_keep: int = Query(7)):
    """Clean up old export and backup files"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        cleaned_exports = 0
        cleaned_backups = 0
        
        # Clean up export files
        for export_id, job in list(export_jobs.items()):
            if job["created_at"] < cutoff_date:
                if job.get("file_path") and os.path.exists(job["file_path"]):
                    os.remove(job["file_path"])
                del export_jobs[export_id]
                cleaned_exports += 1
        
        # Clean up backup files
        for backup_id, job in list(backup_jobs.items()):
            if job["created_at"] < cutoff_date:
                if job.get("backup_path") and os.path.exists(job["backup_path"]):
                    os.remove(job["backup_path"])
                del backup_jobs[backup_id]
                cleaned_backups += 1
        
        return {
            "message": "Cleanup completed",
            "cleaned_exports": cleaned_exports,
            "cleaned_backups": cleaned_backups,
            "cutoff_date": cutoff_date
        }
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup files")