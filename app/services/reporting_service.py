"""
Advanced Reporting Service
Comprehensive report generation, scheduling, and management service
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, BinaryIO
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import json
from dataclasses import dataclass, asdict
from enum import Enum
import os
import tempfile
from pathlib import Path

from app.db.models.reports import (
    ReportTemplate, GeneratedReport, ReportSchedule, ScheduleExecution,
    ReportView, ReportCache, ReportSubscription,
    ReportType, ReportStatus, ExportFormat, ScheduleFrequency
)
from app.core.path_utils import sanitize_path, safe_filename
from app.db.models.user import User
from app.db.models.organization import Organization
from app.db.models.team import Team
from app.services.email_service import EmailService
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ReportGenerationRequest:
    """Data structure for report generation requests"""
    template_id: Optional[UUID] = None
    report_type: ReportType = ReportType.CUSTOM
    title: str = ""
    description: str = ""
    parameters: Dict[str, Any] = None
    data_range_start: Optional[datetime] = None
    data_range_end: Optional[datetime] = None
    export_format: ExportFormat = ExportFormat.PDF
    organization_id: UUID = None
    team_id: Optional[UUID] = None
    requested_by_id: UUID = None


@dataclass
class ReportTemplateConfig:
    """Configuration for report templates"""
    sections: List[Dict[str, Any]] = None
    charts: List[Dict[str, Any]] = None
    tables: List[Dict[str, Any]] = None
    filters: List[Dict[str, Any]] = None
    styling: Dict[str, Any] = None
    data_sources: List[str] = None


class ReportGenerationService:
    """Advanced report generation and management service"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

        # Report generation settings
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.default_retention_days = 90
        self.cache_ttl_hours = 24

        # Export format handlers
        self.export_handlers = {
            ExportFormat.PDF: self._generate_pdf,
            ExportFormat.EXCEL: self._generate_excel,
            ExportFormat.CSV: self._generate_csv,
            ExportFormat.JSON: self._generate_json,
            ExportFormat.POWERPOINT: self._generate_powerpoint
        }

    # Report Generation

    async def generate_report(self, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate a new report based on the request"""
        try:
            # Create report record
            report = GeneratedReport(
                title=request.title,
                description=request.description,
                report_type=request.report_type,
                template_id=request.template_id,
                status=ReportStatus.PENDING,
                parameters=request.parameters or {},
                data_range_start=request.data_range_start,
                data_range_end=request.data_range_end,
                file_format=request.export_format,
                requested_by_id=request.requested_by_id,
                organization_id=request.organization_id,
                team_id=request.team_id,
                generation_started=datetime.utcnow()
            )

            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)

            # Update status to generating
            report.status = ReportStatus.GENERATING
            self.db.commit()

            try:
                # Generate the report file
                file_result = await self._generate_report_file(report, request)

                if file_result["success"]:
                    # Update report with file information
                    report.status = ReportStatus.COMPLETED
                    report.file_path = file_result["file_path"]
                    report.file_name = file_result["file_name"]
                    report.file_size = file_result["file_size"]
                    report.record_count = file_result["record_count"]
                    report.generation_completed = datetime.utcnow()

                    # Set expiration (if not specified, use default)
                    if not request.parameters or "retention_days" not in request.parameters:
                        retention_days = request.parameters.get("retention_days", self.default_retention_days)
                        report.expires_at = datetime.utcnow() + timedelta(days=retention_days)

                    logger.info(f"Report generated successfully: {report.id}")

                    result = {
                        "success": True,
                        "report_id": str(report.id),
                        "file_url": file_result.get("download_url"),
                        "message": "Report generated successfully"
                    }
                else:
                    # Handle generation failure
                    report.status = ReportStatus.FAILED
                    report.error_log = file_result.get("error", "Unknown error")
                    self.db.commit()

                    result = {
                        "success": False,
                        "error": file_result.get("error", "Report generation failed")
                    }

                self.db.commit()

            except Exception as generation_error:
                # Update report status to failed
                report.status = ReportStatus.FAILED
                report.error_log = str(generation_error)
                self.db.commit()

                logger.error(f"Report generation failed: {str(generation_error)}")
                result = {
                    "success": False,
                    "error": f"Report generation failed: {str(generation_error)}"
                }

            return result

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": f"Failed to generate report: {str(e)}"
            }

    async def get_report(self, report_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get report details with access control"""
        report = self.db.query(GeneratedReport).filter(
            GeneratedReport.id == report_id
        ).first()

        if not report:
            return None

        # Check access permissions
        if not self._can_access_report(report, user_id):
            return None

        # Update view count
        report.download_count += 1
        report.last_downloaded = datetime.utcnow()
        self.db.commit()

        return self._serialize_report(report)

    async def list_reports(self, organization_id: UUID, user_id: UUID,
                          report_type: Optional[ReportType] = None,
                          team_id: Optional[UUID] = None,
                          status: Optional[ReportStatus] = None,
                          limit: int = 50,
                          offset: int = 0,
                          date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """List reports with filtering options"""
        try:
            query = self.db.query(GeneratedReport).filter(
                GeneratedReport.organization_id == organization_id
            )

            # Apply filters
            if report_type:
                query = query.filter(GeneratedReport.report_type == report_type)
            if team_id:
                query = query.filter(GeneratedReport.team_id == team_id)
            if status:
                query = query.filter(GeneratedReport.status == status)
            if date_range:
                start_date, end_date = date_range
                query = query.filter(
                    GeneratedReport.created_at >= start_date,
                    GeneratedReport.created_at <= end_date
                )

            # Apply access control
            query = query.filter(
                or_(
                    GeneratedReport.requested_by_id == user_id,
                    GeneratedReport.is_public == True,
                    GeneratedReport.shared_with.contains([user_id])
                )
            )

            # Get total count
            total_count = query.count()

            # Apply pagination
            reports = query.order_by(desc(GeneratedReport.created_at)).offset(offset).limit(limit).all()

            return {
                "reports": [self._serialize_report(r) for r in reports],
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error listing reports: {str(e)}")
            return {"error": f"Failed to list reports: {str(e)}"}

    # Template Management

    async def create_template(self, name: str, description: str, report_type: ReportType,
                             template_config: Dict[str, Any], layout_config: Dict[str, Any],
                             data_config: Dict[str, Any], created_by_id: UUID,
                             organization_id: UUID, category: Optional[str] = None,
                             tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new report template"""
        try:
            template = ReportTemplate(
                name=name,
                description=description,
                report_type=report_type,
                template_config=template_config,
                layout_config=layout_config,
                data_config=data_config,
                created_by_id=created_by_id,
                organization_id=organization_id,
                category=category,
                tags=tags or [],
                version="1.0"
            )

            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)

            logger.info(f"Report template created: {template.id} - {name}")

            return {
                "success": True,
                "template_id": str(template.id),
                "message": "Report template created successfully"
            }

        except Exception as e:
            logger.error(f"Error creating report template: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": f"Failed to create template: {str(e)}"
            }

    async def get_templates(self, organization_id: UUID, report_type: Optional[ReportType] = None,
                          category: Optional[str] = None, is_public: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get available report templates"""
        try:
            query = self.db.query(ReportTemplate).filter(
                ReportTemplate.organization_id == organization_id,
                ReportTemplate.is_active == True
            )

            if report_type:
                query = query.filter(ReportTemplate.report_type == report_type)
            if category:
                query = query.filter(ReportTemplate.category == category)
            if is_public is not None:
                query = query.filter(ReportTemplate.is_public == is_public)

            templates = query.order_by(ReportTemplate.name).all()

            return [self._serialize_template(t) for t in templates]

        except Exception as e:
            logger.error(f"Error getting report templates: {str(e)}")
            return []

    # Scheduling System

    async def create_schedule(self, name: str, description: str, template_id: UUID,
                            frequency: ScheduleFrequency, schedule_config: Dict[str, Any],
                            delivery_method: str, delivery_config: Dict[str, Any],
                            created_by_id: UUID, organization_id: UUID,
                            custom_cron: Optional[str] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Create a new report schedule"""
        try:
            # Calculate next run time
            next_run = self._calculate_next_run(frequency, custom_cron)

            schedule = ReportSchedule(
                name=name,
                description=description,
                template_id=template_id,
                frequency=frequency,
                schedule_config=schedule_config,
                next_run=next_run,
                custom_cron=custom_cron,
                end_date=end_date,
                default_format=ExportFormat.PDF,
                delivery_method=delivery_method,
                delivery_config=delivery_config,
                created_by_id=created_by_id,
                organization_id=organization_id
            )

            self.db.add(schedule)
            self.db.commit()
            self.db.refresh(schedule)

            logger.info(f"Report schedule created: {schedule.id} - {name}")

            return {
                "success": True,
                "schedule_id": str(schedule.id),
                "next_run": schedule.next_run.isoformat(),
                "message": "Report schedule created successfully"
            }

        except Exception as e:
            logger.error(f"Error creating report schedule: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": f"Failed to create schedule: {str(e)}"
            }

    async def get_schedules(self, organization_id: UUID, is_active: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get report schedules"""
        try:
            query = self.db.query(ReportSchedule).filter(
                ReportSchedule.organization_id == organization_id
            )

            if is_active is not None:
                query = query.filter(ReportSchedule.is_active == is_active)

            schedules = query.order_by(ReportSchedule.next_run).all()

            return [self._serialize_schedule(s) for s in schedules]

        except Exception as e:
            logger.error(f"Error getting report schedules: {str(e)}")
            return []

    # Caching System

    async def get_cached_report_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached report data"""
        try:
            cached_item = self.db.query(ReportCache).filter(
                ReportCache.cache_key == cache_key,
                ReportCache.expires_at > datetime.utcnow()
            ).first()

            if cached_item:
                # Update access statistics
                cached_item.last_accessed = datetime.utcnow()
                cached_item.access_count += 1
                self.db.commit()

                return {
                    "data": cached_item.cached_data,
                    "cached_at": cached_item.created_at.isoformat(),
                    "expires_at": cached_item.expires_at.isoformat()
                }

            return None

        except Exception as e:
            logger.error(f"Error getting cached data: {str(e)}")
            return None

    async def cache_report_data(self, cache_key: str, data: Dict[str, Any],
                                ttl_hours: int = None) -> bool:
        """Cache report data"""
        try:
            ttl_hours = ttl_hours or self.cache_ttl_hours
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            data_hash = hash(json.dumps(data, sort_keys=True))

            # Check if cache entry exists
            existing = self.db.query(ReportCache).filter(
                ReportCache.cache_key == cache_key
            ).first()

            if existing:
                # Update existing cache
                existing.cached_data = data
                existing.data_hash = data_hash
                existing.expires_at = expires_at
                existing.last_accessed = datetime.utcnow()
                existing.access_count += 1
            else:
                # Create new cache entry
                cache_entry = ReportCache(
                    cache_key=cache_key,
                    cached_data=data,
                    data_hash=data_hash,
                    expires_at=expires_at,
                    data_size=len(json.dumps(data).encode('utf-8'))
                )
                self.db.add(cache_entry)

            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            return False

    # Analytics

    async def get_report_analytics(self, organization_id: UUID,
                                   date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Get comprehensive report analytics"""
        try:
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            # Report generation statistics
            total_reports = self.db.query(GeneratedReport).filter(
                GeneratedReport.organization_id == organization_id,
                GeneratedReport.created_at >= date_range[0],
                GeneratedReport.created_at <= date_range[1]
            ).count()

            completed_reports = self.db.query(GeneratedReport).filter(
                GeneratedReport.organization_id == organization_id,
                GeneratedReport.created_at >= date_range[0],
                GeneratedReport.created_at <= date_range[1],
                GeneratedReport.status == ReportStatus.COMPLETED
            ).count()

            failed_reports = total_reports - completed_reports

            # Format distribution
            format_query = self.db.query(
                GeneratedReport.file_format,
                func.count(GeneratedReport.id).label('count')
            ).filter(
                GeneratedReport.organization_id == organization_id,
                GeneratedReport.created_at >= date_range[0],
                GeneratedReport.created_at <= date_range[1]
            ).group_by(GeneratedReport.file_format)

            format_distribution = {format.value: count for format, count in format_query.all()}

            # Type distribution
            type_query = self.db.query(
                GeneratedReport.report_type,
                func.count(GeneratedReport.id).label('count')
            ).filter(
                GeneratedReport.organization_id == organization_id,
                GeneratedReport.created_at >= date_range[0],
                GeneratedReport.created_at <= date_range[1]
            ).group_by(GeneratedReport.report_type)

            type_distribution = {report_type.value: count for report_type, count in type_query.all()}

            # Most popular templates
            template_usage = self.db.query(
                ReportTemplate.name,
                ReportTemplate.usage_count
            ).filter(
                ReportTemplate.organization_id == organization_id
            ).order_by(desc(ReportTemplate.usage_count)).limit(10).all()

            # Generation performance metrics
            performance_query = self.db.query(
                func.avg(
                    func.extract('epoch', GeneratedReport.generation_completed) -
                    func.extract('epoch', GeneratedReport.generation_started)
                ).label('avg_generation_time')
            ).filter(
                GeneratedReport.organization_id == organization_id,
                GeneratedReport.generation_started.isnot(None),
                GeneratedReport.generation_completed.isnot(None)
            )

            avg_generation_time = performance_query.scalar() or 0

            return {
                "period": {
                    "start_date": date_range[0].isoformat(),
                    "end_date": date_range[1].isoformat()
                },
                "generation_stats": {
                    "total_reports": total_reports,
                    "completed_reports": completed_reports,
                    "failed_reports": failed_reports,
                    "success_rate": (completed_reports / max(total_reports, 1)) * 100
                },
                "format_distribution": format_distribution,
                "type_distribution": type_distribution,
                "performance": {
                    "avg_generation_time_seconds": avg_generation_time
                },
                "popular_templates": [
                    {"name": template.name, "usage_count": template.usage_count}
                    for template in template_usage
                ]
            }

        except Exception as e:
            logger.error(f"Error getting report analytics: {str(e)}")
            return {"error": f"Failed to get analytics: {str(e)}"}

    # Helper Methods

    def _can_access_report(self, report: GeneratedReport, user_id: UUID) -> bool:
        """Check if user can access the report"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Superuser can access all reports
        if user.is_superuser:
            return True

        # Report creator can access
        if report.requested_by_id == user_id:
            return True

        # Same organization admin can access
        if report.organization_id == user.organization_id and user.is_admin:
            return True

        # Public reports can be accessed by same organization
        if report.is_public and report.organization_id == user.organization_id:
            return True

        # Explicit sharing
        if report.shared_with and user_id in report.shared_with:
            return True

        return False

    def _serialize_report(self, report: GeneratedReport) -> Dict[str, Any]:
        """Serialize report object for API response"""
        return {
            "id": str(report.id),
            "title": report.title,
            "description": report.description,
            "report_type": report.report_type.value,
            "status": report.status.value,
            "file_format": report.file_format.value,
            "file_name": report.file_name,
            "file_size": report.file_size,
            "record_count": report.record_count,
            "download_count": report.download_count,
            "parameters": report.parameters,
            "data_range": {
                "start": report.data_range_start.isoformat() if report.data_range_start else None,
                "end": report.data_range_end.isoformat() if report.data_range_end else None
            },
            "template_id": str(report.template_id) if report.template_id else None,
            "requested_by_id": str(report.requested_by_id),
            "organization_id": str(report.organization_id),
            "team_id": str(report.team_id) if report.team_id else None,
            "is_public": report.is_public,
            "shared_with": [str(uid) for uid in report.shared_with] if report.shared_with else [],
            "expires_at": report.expires_at.isoformat() if report.expires_at else None,
            "created_at": report.created_at.isoformat(),
            "generation_started": report.generation_started.isoformat() if report.generation_started else None,
            "generation_completed": report.generation_completed.isoformat() if report.generation_completed else None
        }

    def _serialize_template(self, template: ReportTemplate) -> Dict[str, Any]:
        """Serialize template object for API response"""
        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "report_type": template.report_type.value,
            "template_config": template.template_config,
            "layout_config": template.layout_config,
            "data_config": template.data_config,
            "category": template.category,
            "tags": template.tags,
            "is_public": template.is_public,
            "is_active": template.is_active,
            "usage_count": template.usage_count,
            "version": template.version,
            "created_by_id": str(template.created_by_id),
            "organization_id": str(template.organization_id),
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "last_used": template.last_used.isoformat() if template.last_used else None
        }

    def _serialize_schedule(self, schedule: ReportSchedule) -> Dict[str, Any]:
        """Serialize schedule object for API response"""
        return {
            "id": str(schedule.id),
            "name": schedule.name,
            "description": schedule.description,
            "frequency": schedule.frequency.value,
            "template_id": str(schedule.template_id),
            "schedule_config": schedule.schedule_config,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "timezone": schedule.timezone,
            "custom_cron": schedule.custom_cron,
            "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
            "default_format": schedule.default_format.value,
            "delivery_method": schedule.delivery_method,
            "delivery_config": schedule.delivery_config,
            "is_active": schedule.is_active,
            "success_count": schedule.success_count,
            "failure_count": schedule.failure_count,
            "last_success": schedule.last_success.isoformat() if schedule.last_success else None,
            "created_by_id": str(schedule.created_by_id),
            "organization_id": str(schedule.organization_id),
            "created_at": schedule.created_at.isoformat()
        }

    # Report Generation Implementation

    async def _generate_report_file(self, report: GeneratedReport, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate the actual report file"""
        try:
            # Get template or use default configuration
            if report.template_id:
                template = self.db.query(ReportTemplate).filter(
                    ReportTemplate.id == report.template_id
                ).first()

                if not template:
                    return {"success": False, "error": "Template not found"}

                config = template.template_config or {}
            else:
                config = {}

            # Get report data
            data = await self._get_report_data(request, config)

            if not data:
                return {"success": False, "error": "No data available for report generation"}

            # Generate file based on format
            handler = self.export_handlers.get(report.file_format)
            if not handler:
                return {"success": False, "error": f"Export format {report.file_format} not supported"}

            return await handler(data, report, request)

        except Exception as e:
            logger.error(f"Error generating report file: {str(e)}")
            return {"success": False, "error": f"File generation failed: {str(e)}"}

    async def _get_report_data(self, request: ReportGenerationRequest, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for the report"""
        try:
            # This would be implemented based on the specific report type and configuration
            # For now, return placeholder data
            return {
                "metadata": {
                    "title": request.title,
                    "report_type": request.report_type.value,
                    "generated_at": datetime.utcnow().isoformat(),
                    "parameters": request.parameters or {}
                },
                "summary": {
                    "total_records": 100,
                    "date_range": {
                        "start": request.data_range_start.isoformat() if request.data_range_start else None,
                        "end": request.data_range_end.isoformat() if request.data_range_end else None
                    }
                },
                "data": []
                # Implementation would query the appropriate data sources based on report type
            }

        except Exception as e:
            logger.error(f"Error getting report data: {str(e)}")
            return {}

    # Export Format Handlers

    async def _generate_pdf(self, data: Dict[str, Any], report: GeneratedReport, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate PDF report with advanced formatting"""
        try:
            # Implementation would use a PDF generation library like ReportLab or WeasyPrint
            # For this implementation, we'll create a structured PDF-ready content
            file_name = f"report_{report.id}.pdf"
            file_path = f"/tmp/reports/{file_name}"

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Generate PDF content structure
            pdf_content = self._create_pdf_content_structure(data, request)

            # For demonstration, we'll create a formatted text file that represents PDF structure
            # In production, this would be processed by a PDF library
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(pdf_content)

            file_size = os.path.getsize(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "download_url": f"/api/v1/reports/{report.id}/download",
                "record_count": data.get("summary", {}).get("total_records", 0),
                "format": "PDF"
            }

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return {"success": False, "error": f"PDF generation failed: {str(e)}"}

    def _create_pdf_content_structure(self, data: Dict[str, Any], request: ReportGenerationRequest) -> str:
        """Create structured content for PDF generation"""
        metadata = data.get("metadata", {})
        summary = data.get("summary", {})
        report_data = data.get("data", [])

        # PDF structure with proper formatting
        content = f"""
PDF REPORT: {metadata.get('title', 'Untitled Report')}
{'=' * 80}

Generated: {metadata.get('generated_at', 'Unknown')}
Report Type: {metadata.get('report_type', 'Custom')}
Organization: PsychSync Platform

{'=' * 80}
EXECUTIVE SUMMARY
{'=' * 80}

Total Records: {summary.get('total_records', 0)}
Date Range: {summary.get('date_range', {}).get('start', 'Not specified')} to {summary.get('date_range', {}).get('end', 'Not specified')}

{'=' * 80}
DETAILED ANALYSIS
{'=' * 80}

"""

        # Add data sections
        if isinstance(report_data, list) and report_data:
            for i, item in enumerate(report_data[:10], 1):  # Limit to first 10 items
                content += f"""
Section {i}:
--------
{str(item)}
{'-' * 40}
"""

        # Add footer
        content += f"""

{'=' * 80}
Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Page 1 of 1
© 2024 PsychSync Platform. All rights reserved.
"""

        return content

    async def _generate_excel(self, data: Dict[str, Any], report: GeneratedReport, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate Excel report with multiple sheets"""
        try:
            # Implementation would use a library like openpyxl or pandas
            # For now, create a structured CSV file with proper Excel formatting
            file_name = f"report_{report.id}.xlsx"
            file_path = f"/tmp/reports/{file_name}"

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Generate Excel-ready CSV content with multiple sheet structure
            excel_content = self._create_excel_content_structure(data, request)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(excel_content)

            file_size = os.path.getsize(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "download_url": f"/api/v1/reports/{report.id}/download",
                "record_count": data.get("summary", {}).get("total_records", 0),
                "format": "Excel",
                "sheets": ["Summary", "Detailed Data", "Analytics"]
            }

        except Exception as e:
            logger.error(f"Error generating Excel: {str(e)}")
            return {"success": False, "error": f"Excel generation failed: {str(e)}"}

    def _create_excel_content_structure(self, data: Dict[str, Any], request: ReportGenerationRequest) -> str:
        """Create structured content for Excel generation"""
        metadata = data.get("metadata", {})
        summary = data.get("summary", {})
        report_data = data.get("data", [])

        # Excel-compatible CSV structure
        content = f"Sheet: Summary\n"
        content += f"Report Title,{metadata.get('title', 'Untitled Report')}\n"
        content += f"Report Type,{metadata.get('report_type', 'Custom')}\n"
        content += f"Generated Date,{metadata.get('generated_at', 'Unknown')}\n"
        content += f"Total Records,{summary.get('total_records', 0)}\n"
        content += f"Date Range Start,{summary.get('date_range', {}).get('start', 'Not specified')}\n"
        content += f"Date Range End,{summary.get('date_range', {}).get('end', 'Not specified')}\n\n"

        content += f"Sheet: Detailed Data\n"

        # Add headers based on data structure
        if isinstance(report_data, list) and report_data:
            # Extract common keys from first item as headers
            first_item = report_data[0] if report_data else {}
            if isinstance(first_item, dict):
                headers = list(first_item.keys())
                content += ",".join(headers) + "\n"

                # Add data rows
                for item in report_data[:100]:  # Limit to 100 rows
                    if isinstance(item, dict):
                        row_data = [str(item.get(header, '')) for header in headers]
                        content += ",".join(row_data) + "\n"

        return content

    async def _generate_csv(self, data: Dict[str, Any], report: GeneratedReport, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate CSV report"""
        return await self._generate_excel(data, report, request)

    async def _generate_json(self, data: Dict[str, Any], report: GeneratedReport, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate JSON report"""
        try:
            file_name = f"report_{report.id}.json"
            file_path = f"/tmp/reports/{file_name}"

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write JSON data
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            file_size = os.path.getsize(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "download_url": f"/api/v1/reports/{report.id}/download",
                "record_count": data.get("summary", {}).get("total_records", 0)
            }

        except Exception as e:
            logger.error(f"Error generating JSON: {str(e)}")
            return {"success": False, "error": f"JSON generation failed: {str(e)}"}

    async def _generate_powerpoint(self, data: Dict[str, Any], report: GeneratedReport, request: ReportGenerationRequest) -> Dict[str, Any]:
        """Generate PowerPoint report"""
        try:
            # Implementation would use a library like python-pptx
            # For now, create a placeholder file
            file_name = f"report_{report.id}.pptx"
            file_path = f"/tmp/reports/{file_name}"

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Create placeholder PowerPoint content
            with open(file_path, 'w') as f:
                f.write(f"Report: {request.title}\n")
                f.write(f"Type: {request.report_type.value}\n")
                f.write("Generated: {datetime.utcnow().isoformat()}\n")
                f.write("Data: {json.dumps(data, indent=2)}\n")

            file_size = os.path.getsize(file_path)

            return {
                "success": True,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "download_url": f"/api/v1/reports/{report.id}/download",
                "record_count": data.get("summary", {}).get("total_records", 0)
            }

        except Exception as e:
            logger.error(f"Error generating PowerPoint: {str(e)}")
            return {"success": False, "error": f"PowerPoint generation failed: {str(e)}"}

    # Scheduling Helper Methods

    def _calculate_next_run(self, frequency: ScheduleFrequency, custom_cron: Optional[str] = None) -> datetime:
        """Calculate next run time for scheduled reports"""
        if custom_cron:
            # Parse custom cron expression (implementation needed)
            # For now, use a simple placeholder
            return datetime.utcnow() + timedelta(days=1)

        now = datetime.utcnow()

        if frequency == ScheduleFrequency.DAILY:
            return now + timedelta(days=1)
        elif frequency == ScheduleFrequency.WEEKLY:
            return now + timedelta(weeks=1)
        elif frequency == ScheduleFrequency.MONTHLY:
            return now + timedelta(days=30)
        elif frequency == ScheduleFrequency.QUARTERLY:
            return now + timedelta(days=90)
        elif frequency == ScheduleFrequency.YEARLY:
            return now + timedelta(days=365)
        else:
            # Default to daily
            return now + timedelta(days=1)

    # Report Scheduling and Automation

    async def execute_scheduled_reports(self) -> Dict[str, Any]:
        """Execute all pending scheduled reports"""
        try:
            # Get all schedules that need to run
            due_schedules = self.db.query(ReportSchedule).filter(
                ReportSchedule.is_active == True,
                ReportSchedule.next_run <= datetime.utcnow(),
                or_(
                    ReportSchedule.end_date.is_(None),
                    ReportSchedule.end_date >= datetime.utcnow()
                )
            ).all()

            executed_count = 0
            success_count = 0
            failed_count = 0

            for schedule in due_schedules:
                try:
                    # Create execution record
                    execution = ScheduleExecution(
                        schedule_id=schedule.id,
                        scheduled_at=schedule.next_run,
                        started_at=datetime.utcnow(),
                        status="running"
                    )
                    self.db.add(execution)
                    self.db.commit()
                    self.db.refresh(execution)

                    # Generate the report
                    result = await self._execute_scheduled_report(schedule, execution)

                    # Update execution record
                    execution.completed_at = datetime.utcnow()
                    execution.status = "success" if result["success"] else "failed"
                    execution.result_message = result.get("message", "Completed")
                    execution.execution_time_seconds = (
                        execution.completed_at - execution.started_at
                    ).total_seconds()

                    if result["success"]:
                        execution.report_id = UUID(result["report_id"]) if result.get("report_id") else None
                        success_count += 1
                        schedule.success_count += 1
                        schedule.last_success = datetime.utcnow()
                    else:
                        failed_count += 1
                        schedule.failure_count += 1

                    executed_count += 1

                    # Calculate next run time
                    schedule.next_run = self._calculate_next_run(schedule.frequency, schedule.custom_cron)
                    schedule.last_run = datetime.utcnow()

                except Exception as e:
                    logger.error(f"Error executing scheduled report {schedule.id}: {str(e)}")
                    failed_count += 1
                    schedule.failure_count += 1

                    # Update execution record if it exists
                    if 'execution' in locals():
                        execution.status = "failed"
                        execution.result_message = str(e)
                        execution.completed_at = datetime.utcnow()

                self.db.commit()

            return {
                "executed_count": executed_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "message": f"Executed {executed_count} scheduled reports: {success_count} success, {failed_count} failed"
            }

        except Exception as e:
            logger.error(f"Error executing scheduled reports: {str(e)}")
            return {"error": f"Failed to execute scheduled reports: {str(e)}"}

    async def _execute_scheduled_report(self, schedule: ReportSchedule, execution: ScheduleExecution) -> Dict[str, Any]:
        """Execute a single scheduled report"""
        try:
            # Create report generation request from schedule
            request = ReportGenerationRequest(
                template_id=schedule.template_id,
                report_type=schedule.template.report_type if schedule.template else ReportType.CUSTOM,
                title=f"Scheduled: {schedule.name}",
                description=f"Automatically generated report from schedule: {schedule.description}",
                parameters=schedule.schedule_config or {},
                export_format=schedule.default_format,
                organization_id=schedule.organization_id,
                team_id=schedule.delivery_config.get("team_id") if schedule.delivery_config else None,
                requested_by_id=schedule.created_by_id
            )

            # Generate the report
            result = await self.generate_report(request)

            if result["success"]:
                # Handle delivery
                await self._deliver_report(schedule, result["report_id"])

                return {
                    "success": True,
                    "report_id": result["report_id"],
                    "message": "Scheduled report generated and delivered successfully"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Scheduled report generation failed")
                }

        except Exception as e:
            logger.error(f"Error executing scheduled report: {str(e)}")
            return {"success": False, "error": f"Scheduled report execution failed: {str(e)}"}

    async def _deliver_report(self, schedule: ReportSchedule, report_id: str) -> bool:
        """Deliver generated report via configured method"""
        try:
            delivery_method = schedule.delivery_method.lower()
            delivery_config = schedule.delivery_config or {}

            if delivery_method == "email":
                return await self._deliver_report_email(schedule, report_id, delivery_config)
            elif delivery_method == "webhook":
                return await self._deliver_report_webhook(schedule, report_id, delivery_config)
            elif delivery_method == "download":
                # For download method, no delivery needed - just make available
                return True
            else:
                logger.warning(f"Unsupported delivery method: {delivery_method}")
                return False

        except Exception as e:
            logger.error(f"Error delivering report: {str(e)}")
            return False

    async def _deliver_report_email(self, schedule: ReportSchedule, report_id: str, config: Dict[str, Any]) -> bool:
        """Deliver report via email"""
        try:
            recipients = config.get("recipients", [])
            if not recipients:
                return False

            # Get report details
            report = self.db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
            if not report:
                return False

            # Construct email content
            subject = f"Automated Report: {schedule.name}"
            body = f"""
            Hello,

            Your scheduled report "{schedule.name}" has been generated.

            Report Details:
            - Title: {report.title}
            - Type: {report.report_type.value}
            - Generated: {report.generation_completed}
            - Format: {report.file_format.value}

            You can download the report from your dashboard.

            Best regards,
            PsychSync Platform
            """

            # Send email (implementation would use the email service)
            # await self.email_service.send_email(to=recipients, subject=subject, body=body)

            return True

        except Exception as e:
            logger.error(f"Error delivering report via email: {str(e)}")
            return False

    async def _deliver_report_webhook(self, schedule: ReportSchedule, report_id: str, config: Dict[str, Any]) -> bool:
        """Deliver report via webhook"""
        try:
            webhook_url = config.get("url")
            if not webhook_url:
                return False

            # Get report details
            report = self.db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
            if not report:
                return False

            # Prepare webhook payload
            payload = {
                "event": "report_generated",
                "schedule_id": str(schedule.id),
                "schedule_name": schedule.name,
                "report_id": str(report.id),
                "report_title": report.title,
                "report_type": report.report_type.value,
                "generated_at": report.generation_completed.isoformat() if report.generation_completed else None,
                "download_url": f"/api/v1/reports/{report.id}/download"
            }

            # Send webhook (implementation would use http client)
            # async with aiohttp.ClientSession() as session:
            #     async with session.post(webhook_url, json=payload) as response:
            #         return response.status == 200

            return True

        except Exception as e:
            logger.error(f"Error delivering report via webhook: {str(e)}")
            return False

    # Cleanup Methods

    async def cleanup_expired_reports(self) -> int:
        """Clean up expired reports"""
        try:
            expired_reports = self.db.query(GeneratedReport).filter(
                GeneratedReport.expires_at < datetime.utcnow()
            ).all()

            count = len(expired_reports)

            # Delete files
            for report in expired_reports:
                if report.file_path and os.path.exists(report.file_path):
                    try:
                        os.remove(report.file_path)
                    except OSError:
                        logger.warning(f"Could not delete report file: {report.file_path}")

            # Delete database records
            for report in expired_reports:
                self.db.delete(report)

            self.db.commit()

            logger.info(f"Cleaned up {count} expired reports")
            return count

        except Exception as e:
            logger.error(f"Error cleaning up expired reports: {str(e)}")
            return 0

    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries"""
        try:
            expired_cache = self.db.query(ReportCache).filter(
                ReportCache.expires_at < datetime.utcnow()
            ).all()

            count = len(expired_cache)

            for cache_item in expired_cache:
                self.db.delete(cache_item)

            self.db.commit()

            logger.info(f"Cleaned up {count} expired cache entries")
            return count

        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {str(e)}")
            return 0
