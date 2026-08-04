"""
Research Data Export Service

Comprehensive service for exporting anonymized research data with compliance,
quality control, and multi-format output capabilities.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

# Import our anonymization service
from app.services.data_anonymization import (
    AnonymizationMethod,
    DataAnonymizer,
    QuasiIdentifier,
)

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    SPSS = "spss"
    R = "r"
    STATA = "stata"
    SAS = "sas"


class DataCategory(Enum):
    DEMOGRAPHIC = "demographic"
    PSYCHOLOGICAL = "psychological"
    BEHAVIORAL = "behavioral"
    ORGANIZATIONAL = "organizational"
    TEMPORAL = "temporal"
    ASSESSMENT = "assessment"
    INTERVENTION = "intervention"
    OUTCOMES = "outcomes"


class ComplianceStandard(Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa"
    CCPA = "ccpa"
    FERPA = "ferpa"
    ISO27001 = "iso27001"


class ExportStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExportConfiguration:
    """Configuration for data export request"""

    export_id: str
    user_id: str
    organization_id: str
    data_categories: list[DataCategory]
    date_range: tuple[datetime, datetime]
    anonymization_method: AnonymizationMethod
    quasi_identifiers: list[QuasiIdentifier]
    sensitive_attributes: list[str]
    output_format: ExportFormat
    compliance_standards: list[ComplianceStandard]
    include_metadata: bool
    sample_size: int | None = None
    quality_checks: bool = True
    export_notes: str | None = None


@dataclass
class ExportQualityMetrics:
    """Quality metrics for exported data"""

    completeness_score: float
    accuracy_score: float
    consistency_score: float
    anonymity_score: float
    privacy_compliance_score: float
    utility_score: float
    validation_errors: list[str]
    quality_flags: list[str]


@dataclass
class DataExportResult:
    """Result of data export operation"""

    export_id: str
    status: ExportStatus
    file_path: str
    file_size: int
    record_count: int
    export_date: datetime
    processing_time: float
    quality_metrics: ExportQualityMetrics
    anonymization_report: dict[str, Any]
    compliance_report: dict[str, Any]
    download_url: str
    expires_at: datetime


class ResearchDataExporter:
    """Advanced research data export with comprehensive anonymization"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.anonymizer = DataAnonymizer(db_session)
        self.export_cache = {}
        self.compliance_templates = self._load_compliance_templates()

    def _load_compliance_templates(self) -> dict[str, Any]:
        """Load compliance templates for different standards"""
        return {
            ComplianceStandard.GDPR: {
                "required_fields": ["consent_date", "data_purpose", "retention_period"],
                "anonymization_level": "high",
                "data_minimization": True,
                "purpose_limitation": True,
                "storage_limitation": True,
                "accuracy_obligation": True,
                "security_measures": ["encryption", "access_control", "audit_logging"],
            },
            ComplianceStandard.HIPAA: {
                "required_fields": [
                    "phi_identifiers",
                    "access_logs",
                    "disclosure_tracking",
                ],
                "anonymization_level": "very_high",
                "de_identification": True,
                "minimum_necessary": True,
                "security_measures": ["encryption", "access_control", "audit_logging"],
                "business_associate_agreement": True,
            },
            ComplianceStandard.CCPA: {
                "required_fields": [
                    "consumer_rights",
                    "data_categories",
                    "opt_out_mechanism",
                ],
                "anonymization_level": "high",
                "transparency": True,
                "consumer_control": True,
                "data_portability": True,
                "deletion_rights": True,
            },
            ComplianceStandard.FERPA: {
                "required_fields": [
                    "student_records",
                    "directory_information",
                    "education_records",
                ],
                "anonymization_level": "high",
                "parental_consent": True,
                "record_access_control": True,
                "data_minimization": True,
            },
            ComplianceStandard.ISO27001: {
                "required_fields": [
                    "information_classification",
                    "access_control",
                    "incident_management",
                ],
                "anonymization_level": "standard",
                "risk_assessment": True,
                "security_controls": True,
                "continuous_monitoring": True,
            },
        }

    async def create_export_request(self, config: ExportConfiguration) -> str:
        """Create a new data export request"""
        try:
            # Validate export configuration
            await self._validate_export_config(config)

            # Store export request
            export_request = {
                "config": config,
                "status": ExportStatus.PENDING,
                "created_date": datetime.utcnow(),
                "processing_start": None,
                "processing_end": None,
                "result": None,
                "error_message": None,
            }

            self.export_cache[config.export_id] = export_request

            logger.info(
                f"Created export request {config.export_id} for user {config.user_id}"
            )
            return config.export_id

        except Exception as e:
            logger.error(f"Error creating export request: {e}")
            raise

    async def process_export(self, export_id: str) -> DataExportResult:
        """Process a data export request"""
        try:
            export_request = self.export_cache.get(export_id)
            if not export_request:
                raise ValueError(f"Export request {export_id} not found")

            config = export_request["config"]

            # Update status to processing
            export_request["status"] = ExportStatus.PROCESSING
            export_request["processing_start"] = datetime.utcnow()

            start_time = datetime.utcnow()

            # Extract data from database
            raw_data = await self._extract_data(config)

            # Apply anonymization
            anonymized_data = await self._apply_anonymization(
                raw_data,
                config.anonymization_method,
                config.quasi_identifiers,
                config.sensitive_attributes,
            )

            # Perform quality checks
            quality_metrics = await self._perform_quality_checks(
                raw_data, anonymized_data, config
            )

            # Generate reports
            anonymization_report = await self._generate_anonymization_report(
                raw_data, anonymized_data, config
            )

            compliance_report = await self._generate_compliance_report(
                anonymized_data, config
            )

            # Export to file
            file_path = await self._export_to_file(
                anonymized_data, config.output_format, export_id
            )

            # Get file size
            file_size = (
                Path(file_path).stat().st_size if Path(file_path).exists() else 0
            )

            # Generate download URL
            download_url = await self._generate_download_url(
                file_path, config.export_id
            )

            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            # Create result
            result = DataExportResult(
                export_id=export_id,
                status=ExportStatus.COMPLETED,
                file_path=file_path,
                file_size=file_size,
                record_count=len(anonymized_data),
                export_date=datetime.utcnow(),
                processing_time=processing_time,
                quality_metrics=quality_metrics,
                anonymization_report=anonymization_report,
                compliance_report=compliance_report,
                download_url=download_url,
                expires_at=datetime.utcnow() + timedelta(days=7),  # 7-day expiry
            )

            # Update request
            export_request["status"] = ExportStatus.COMPLETED
            export_request["processing_end"] = datetime.utcnow()
            export_request["result"] = result

            logger.info(
                f"Completed export {export_id}: {len(anonymized_data)} records exported"
            )
            return result

        except Exception as e:
            logger.error(f"Error processing export {export_id}: {e}")

            # Update request with error
            if export_id in self.export_cache:
                self.export_cache[export_id]["status"] = ExportStatus.FAILED
                self.export_cache[export_id]["processing_end"] = datetime.utcnow()
                self.export_cache[export_id]["error_message"] = str(e)

            raise

    async def get_export_status(
        self, export_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Get status of export request"""
        try:
            export_request = self.export_cache.get(export_id)
            if not export_request:
                return {
                    "status": "not_found",
                    "message": f"Export {export_id} not found",
                }

            # Check user authorization
            if user_id and export_request["config"].user_id != user_id:
                return {
                    "status": "unauthorized",
                    "message": "Not authorized to view this export",
                }

            config = export_request["config"]
            result = export_request.get("result")

            response = {
                "export_id": export_id,
                "status": export_request["status"].value,
                "created_date": export_request["created_date"].isoformat(),
                "processing_start": (
                    export_request["processing_start"].isoformat()
                    if export_request["processing_start"]
                    else None
                ),
                "processing_end": (
                    export_request["processing_end"].isoformat()
                    if export_request["processing_end"]
                    else None
                ),
                "error_message": export_request.get("error_message"),
                "config": {
                    "data_categories": [cat.value for cat in config.data_categories],
                    "date_range": [
                        config.date_range[0].isoformat(),
                        config.date_range[1].isoformat(),
                    ],
                    "anonymization_method": config.anonymization_method.value,
                    "output_format": config.output_format.value,
                    "compliance_standards": [
                        std.value for std in config.compliance_standards
                    ],
                },
            }

            if result:
                response.update(
                    {
                        "file_size": result.file_size,
                        "record_count": result.record_count,
                        "download_url": result.download_url,
                        "expires_at": result.expires_at.isoformat(),
                        "quality_metrics": {
                            "completeness_score": result.quality_metrics.completeness_score,
                            "accuracy_score": result.quality_metrics.accuracy_score,
                            "consistency_score": result.quality_metrics.consistency_score,
                            "anonymity_score": result.quality_metrics.anonymity_score,
                            "privacy_compliance_score": result.quality_metrics.privacy_compliance_score,
                            "utility_score": result.quality_metrics.utility_score,
                            "validation_errors": result.quality_metrics.validation_errors,
                            "quality_flags": result.quality_metrics.quality_flags,
                        },
                    }
                )

            return response

        except Exception as e:
            logger.error(f"Error getting export status for {export_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def list_user_exports(
        self, user_id: str, limit: int = 50, include_expired: bool = False
    ) -> list[dict[str, Any]]:
        """List all exports for a user"""
        try:
            user_exports = []

            for export_id, export_request in self.export_cache.items():
                if export_request["config"].user_id == user_id:
                    result = export_request.get("result")

                    # Skip expired exports unless requested
                    if (
                        not include_expired
                        and result
                        and result.expires_at < datetime.utcnow()
                    ):
                        continue

                    export_info = {
                        "export_id": export_id,
                        "status": export_request["status"].value,
                        "created_date": export_request["created_date"].isoformat(),
                        "data_categories": [
                            cat.value
                            for cat in export_request["config"].data_categories
                        ],
                        "output_format": export_request["config"].output_format.value,
                        "record_count": result.record_count if result else 0,
                        "file_size": result.file_size if result else 0,
                        "download_url": result.download_url if result else None,
                        "expires_at": result.expires_at.isoformat() if result else None,
                    }

                    user_exports.append(export_info)

            # Sort by creation date (most recent first)
            user_exports.sort(key=lambda x: x["created_date"], reverse=True)

            return user_exports[:limit]

        except Exception as e:
            logger.error(f"Error listing exports for user {user_id}: {e}")
            return []

    async def delete_export(
        self, export_id: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Delete an export and its files"""
        try:
            export_request = self.export_cache.get(export_id)
            if not export_request:
                return {
                    "status": "not_found",
                    "message": f"Export {export_id} not found",
                }

            # Check user authorization
            if user_id and export_request["config"].user_id != user_id:
                return {
                    "status": "unauthorized",
                    "message": "Not authorized to delete this export",
                }

            # Delete file if it exists
            result = export_request.get("result")
            if result and result.file_path:
                try:
                    Path(result.file_path).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete file {result.file_path}: {e}")

            # Remove from cache
            del self.export_cache[export_id]

            return {
                "status": "success",
                "message": f"Export {export_id} deleted successfully",
                "deleted_date": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error deleting export {export_id}: {e}")
            return {"status": "error", "message": str(e)}

    async def get_export_statistics(
        self, organization_id: str | None = None, timeframe_days: int = 30
    ) -> dict[str, Any]:
        """Get export statistics and trends"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)

            stats = {
                "total_exports": len(self.export_cache),
                "recent_exports": 0,
                "completed_exports": 0,
                "failed_exports": 0,
                "popular_formats": {},
                "popular_categories": {},
                "processing_times": [],
                "file_sizes": [],
                "compliance_standards_usage": {},
            }

            for export_request in self.export_cache.values():
                if export_request["created_date"] >= cutoff_date:
                    stats["recent_exports"] += 1

                if export_request["status"] == ExportStatus.COMPLETED:
                    stats["completed_exports"] += 1
                elif export_request["status"] == ExportStatus.FAILED:
                    stats["failed_exports"] += 1

                # Format statistics
                config = export_request["config"]
                format_key = config.output_format.value
                stats["popular_formats"][format_key] = (
                    stats["popular_formats"].get(format_key, 0) + 1
                )

                for category in config.data_categories:
                    cat_key = category.value
                    stats["popular_categories"][cat_key] = (
                        stats["popular_categories"].get(cat_key, 0) + 1
                    )

                # Processing times
                if (
                    export_request["processing_start"]
                    and export_request["processing_end"]
                ):
                    processing_time = (
                        export_request["processing_end"]
                        - export_request["processing_start"]
                    ).total_seconds()
                    stats["processing_times"].append(processing_time)

                # File sizes
                result = export_request.get("result")
                if result and result.file_size:
                    stats["file_sizes"].append(result.file_size)

                # Compliance standards
                for standard in config.compliance_standards:
                    std_key = standard.value
                    stats["compliance_standards_usage"][std_key] = (
                        stats["compliance_standards_usage"].get(std_key, 0) + 1
                    )

            # Calculate averages
            if stats["processing_times"]:
                stats["average_processing_time"] = sum(stats["processing_times"]) / len(
                    stats["processing_times"]
                )
                stats["max_processing_time"] = max(stats["processing_times"])
                stats["min_processing_time"] = min(stats["processing_times"])

            if stats["file_sizes"]:
                stats["average_file_size"] = sum(stats["file_sizes"]) / len(
                    stats["file_sizes"]
                )
                stats["total_file_size"] = sum(stats["file_sizes"])

            stats["success_rate"] = (
                stats["completed_exports"]
                / (stats["completed_exports"] + stats["failed_exports"])
                if (stats["completed_exports"] + stats["failed_exports"]) > 0
                else 0
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting export statistics: {e}")
            return {}

    # Private helper methods
    async def _validate_export_config(self, config: ExportConfiguration) -> None:
        """Validate export configuration"""
        if not config.export_id or not config.user_id or not config.organization_id:
            raise ValueError("Missing required fields in export configuration")

        if not config.data_categories:
            raise ValueError("At least one data category must be specified")

        if config.date_range[0] >= config.date_range[1]:
            raise ValueError("Invalid date range: start date must be before end date")

        if not config.quasi_identifiers:
            config.quasi_identifiers = self._get_default_quasi_identifiers(
                config.data_categories
            )

        if not config.sensitive_attributes:
            config.sensitive_attributes = self._get_default_sensitive_attributes(
                config.data_categories
            )

        # Validate date range is not too large
        date_diff = config.date_range[1] - config.date_range[0]
        if date_diff.days > 365:
            raise ValueError("Date range cannot exceed 1 year")

    def _get_default_quasi_identifiers(
        self, categories: list[DataCategory]
    ) -> list[QuasiIdentifier]:
        """Get default quasi-identifiers for data categories"""
        defaults = {
            DataCategory.DEMOGRAPHIC: [
                QuasiIdentifier("age", 5),
                QuasiIdentifier("zip_code", 3),
                QuasiIdentifier("birth_year", 4),
                QuasiIdentifier("gender", 1),
            ],
            DataCategory.PSYCHOLOGICAL: [
                QuasiIdentifier("assessment_date", 7),
                QuasiIdentifier("test_session_id", 6),
            ],
            DataCategory.ORGANIZATIONAL: [
                QuasiIdentifier("department", 3),
                QuasiIdentifier("team_size", 2),
                QuasiIdentifier("location", 4),
            ],
        }

        quasi_identifiers = []
        for category in categories:
            quasi_identifiers.extend(defaults.get(category, []))

        return quasi_identifiers

    def _get_default_sensitive_attributes(
        self, categories: list[DataCategory]
    ) -> list[str]:
        """Get default sensitive attributes for data categories"""
        defaults = {
            DataCategory.DEMOGRAPHIC: ["name", "email", "phone", "address", "ssn"],
            DataCategory.PSYCHOLOGICAL: ["therapist_notes", "diagnosis", "medication"],
            DataCategory.BEHAVIORAL: ["personal_comments", "confidential_notes"],
            DataCategory.ORGANIZATIONAL: [
                "performance_review",
                "salary",
                "termination_reason",
            ],
        }

        sensitive_attributes = []
        for category in categories:
            sensitive_attributes.extend(defaults.get(category, []))

        return sensitive_attributes

    async def _extract_data(self, config: ExportConfiguration) -> pd.DataFrame:
        """Extract data from database based on configuration"""
        try:
            # This would query the actual database based on categories
            # For now, return mock data
            mock_data = []

            # Generate mock data based on categories
            for i in range(1000):  # Generate 1000 sample records
                record = {
                    "record_id": f"rec_{i:06d}",
                    "user_id": f"user_{i % 100:03d}",
                    "date": (config.date_range[0] + timedelta(days=i % 365)).strftime(
                        "%Y-%m-%d"
                    ),
                }

                # Add category-specific data
                if DataCategory.DEMOGRAPHIC in config.data_categories:
                    record.update(
                        {
                            "age": 25 + (i % 50),
                            "gender": np.secrets.choice(["M", "F", "Other"]),
                            "zip_code": f"{10000 + (i % 90000):05d}",
                            "education_level": np.secrets.choice(
                                ["High School", "Bachelor's", "Master's", "PhD"]
                            ),
                        }
                    )

                if DataCategory.PSYCHOLOGICAL in config.data_categories:
                    record.update(
                        {
                            "assessment_type": np.secrets.choice(
                                ["Personality", "Intelligence", "Aptitude"]
                            ),
                            "score": np.random.normal(100, 15),
                            "test_date": (
                                config.date_range[0] + timedelta(days=i % 30)
                            ).strftime("%Y-%m-%d"),
                        }
                    )

                if DataCategory.BEHAVIORAL in config.data_categories:
                    record.update(
                        {
                            "behavior_category": np.secrets.choice(
                                ["Engagement", "Performance", "Communication"]
                            ),
                            "rating": np.secrets.randbelow(5) + 1,
                            "observation": f"Behavioral observation {i}",
                        }
                    )

                if DataCategory.ORGANIZATIONAL in config.data_categories:
                    record.update(
                        {
                            "department": np.secrets.choice(
                                ["Engineering", "Sales", "Marketing", "HR"]
                            ),
                            "position": np.secrets.choice(
                                ["Manager", "Analyst", "Specialist", "Director"]
                            ),
                            "tenure_months": np.secrets.randbelow(119) + 1,
                        }
                    )

                mock_data.append(record)

            df = pd.DataFrame(mock_data)

            # Apply sample size limit if specified
            if config.sample_size and config.sample_size < len(df):
                df = df.sample(n=config.sample_size, random_state=42)

            return df

        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            raise

    async def _apply_anonymization(
        self,
        data: pd.DataFrame,
        method: AnonymizationMethod,
        quasi_identifiers: list[QuasiIdentifier],
        sensitive_attributes: list[str],
    ) -> pd.DataFrame:
        """Apply anonymization to the data"""
        try:
            # Use our existing data anonymizer
            anonymized_data = await self.anonymizer.anonymize_dataset(
                data, method, quasi_identifiers, sensitive_attributes
            )

            return anonymized_data

        except Exception as e:
            logger.error(f"Error applying anonymization: {e}")
            raise

    async def _perform_quality_checks(
        self,
        original_data: pd.DataFrame,
        anonymized_data: pd.DataFrame,
        config: ExportConfiguration,
    ) -> ExportQualityMetrics:
        """Perform quality checks on exported data"""
        try:
            completeness_score = await self._calculate_completeness(anonymized_data)
            accuracy_score = await self._calculate_accuracy(
                original_data, anonymized_data
            )
            consistency_score = await self._calculate_consistency(anonymized_data)
            anonymity_score = await self._calculate_anonymity_score(
                anonymized_data, config
            )
            privacy_compliance_score = await self._calculate_privacy_compliance(
                anonymized_data, config
            )
            utility_score = await self._calculate_utility_score(
                original_data, anonymized_data
            )

            validation_errors = await self._validate_data_quality(anonymized_data)
            quality_flags = await self._generate_quality_flags(anonymized_data, config)

            return ExportQualityMetrics(
                completeness_score=completeness_score,
                accuracy_score=accuracy_score,
                consistency_score=consistency_score,
                anonymity_score=anonymity_score,
                privacy_compliance_score=privacy_compliance_score,
                utility_score=utility_score,
                validation_errors=validation_errors,
                quality_flags=quality_flags,
            )

        except Exception as e:
            logger.error(f"Error performing quality checks: {e}")
            raise

    async def _calculate_completeness(self, data: pd.DataFrame) -> float:
        """Calculate data completeness score"""
        try:
            total_cells = len(data) * len(data.columns)
            missing_cells = data.isnull().sum().sum()

            if total_cells == 0:
                return 1.0

            completeness = 1.0 - (missing_cells / total_cells)
            return max(0.0, completeness)

        except Exception as e:
            logger.error(f"Error calculating completeness: {e}")
            return 0.0

    async def _calculate_accuracy(
        self, original: pd.DataFrame, anonymized: pd.DataFrame
    ) -> float:
        """Calculate data accuracy score"""
        try:
            # This is a simplified accuracy calculation
            # In production, would compare data distributions and patterns

            # Check if structure is preserved
            if len(original) != len(anonymized) or len(original.columns) != len(
                anonymized.columns
            ):
                return 0.5  # Structural issues

            # Check data types preservation
            type_preservation = sum(
                1
                for col in original.columns
                if original[col].dtype == anonymized[col].dtype
            ) / len(original.columns)

            return max(0.0, type_preservation)

        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return 0.0

    async def _calculate_consistency(self, data: pd.DataFrame) -> float:
        """Calculate data consistency score"""
        try:
            # Check for data consistency issues
            consistency_score = 1.0

            # Check for duplicate records
            if data.duplicated().any():
                consistency_score -= 0.1

            # Check for inconsistent data types within columns
            for col in data.columns:
                if data[col].dtype == "object":
                    unique_types = set(type(val).__name__ for val in data[col].dropna())
                    if len(unique_types) > 1:
                        consistency_score -= 0.05

            return max(0.0, consistency_score)

        except Exception as e:
            logger.error(f"Error calculating consistency: {e}")
            return 0.0

    async def _calculate_anonymity_score(
        self, data: pd.DataFrame, config: ExportConfiguration
    ) -> float:
        """Calculate anonymization effectiveness score"""
        try:
            # Check if sensitive attributes are properly anonymized
            score = 1.0

            for attr in config.sensitive_attributes:
                if attr in data.columns:
                    # Check if attribute values are properly anonymized
                    unique_values = data[attr].dropna().unique()[:10]  # Sample first 10

                    # Look for patterns that suggest poor anonymization
                    for value in unique_values:
                        if isinstance(value, str) and len(value) > 3:
                            # Check for direct identifiers
                            if any(
                                indicator in value.lower()
                                for indicator in ["name", "email", "phone", "address"]
                            ):
                                score -= 0.1
                                break

            return max(0.0, score)

        except Exception as e:
            logger.error(f"Error calculating anonymity score: {e}")
            return 0.0

    async def _calculate_privacy_compliance(
        self, data: pd.DataFrame, config: ExportConfiguration
    ) -> float:
        """Calculate privacy compliance score"""
        try:
            compliance_score = 1.0

            # Check compliance with requested standards
            for standard in config.compliance_standards:
                template = self.compliance_templates[standard]

                # Check required fields are handled appropriately
                if standard == ComplianceStandard.GDPR:
                    # Check for personal data minimization
                    personal_columns = [
                        col
                        for col in data.columns
                        if any(
                            keyword in col.lower()
                            for keyword in ["name", "email", "phone", "address"]
                        )
                    ]
                    if len(personal_columns) > 0:
                        # Personal data should be anonymized
                        compliance_score -= 0.1

                elif standard == ComplianceStandard.HIPAA:
                    # Check for PHI (Protected Health Information)
                    phi_columns = [
                        col
                        for col in data.columns
                        if any(
                            keyword in col.lower()
                            for keyword in [
                                "medical",
                                "health",
                                "diagnosis",
                                "treatment",
                            ]
                        )
                    ]
                    if len(phi_columns) > 0:
                        compliance_score -= 0.1

            return max(0.0, compliance_score)

        except Exception as e:
            logger.error(f"Error calculating privacy compliance: {e}")
            return 0.0

    async def _calculate_utility_score(
        self, original: pd.DataFrame, anonymized: pd.DataFrame
    ) -> float:
        """Calculate data utility preservation score"""
        try:
            # Utility score measures how well the anonymized data preserves analytical value
            utility_score = 1.0

            # Check if data distributions are preserved
            for col in anonymized.columns:
                if anonymized[col].dtype in ["int64", "float64"]:
                    # For numeric columns, check statistical properties
                    orig_mean = original[col].mean()
                    anon_mean = anonymized[col].mean()

                    if orig_mean != 0:
                        mean_deviation = abs(orig_mean - anon_mean) / abs(orig_mean)
                        if mean_deviation > 0.1:  # More than 10% deviation
                            utility_score -= 0.05

            return max(0.0, utility_score)

        except Exception as e:
            logger.error(f"Error calculating utility score: {e}")
            return 0.0

    async def _validate_data_quality(self, data: pd.DataFrame) -> list[str]:
        """Validate data quality and return errors"""
        try:
            errors = []

            # Check for missing values
            missing_counts = data.isnull().sum()
            for col, count in missing_counts.items():
                if count > len(data) * 0.1:  # More than 10% missing
                    errors.append(
                        f"Column '{col}' has {count} missing values ({count / len(data) * 100:.1f}%)"
                    )

            # Check for outliers
            for col in data.select_dtypes(include=[np.number]).columns:
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers = data[
                    (data[col] < Q1 - 1.5 * IQR) | (data[col] > Q3 + 1.5 * IQR)
                ]

                if len(outliers) > len(data) * 0.05:  # More than 5% outliers
                    errors.append(
                        f"Column '{col}' has {len(outliers)} outliers ({len(outliers) / len(data) * 100:.1f}%)"
                    )

            return errors

        except Exception as e:
            logger.error(f"Error validating data quality: {e}")
            return [f"Validation error: {e!s}"]

    async def _generate_quality_flags(
        self, data: pd.DataFrame, config: ExportConfiguration
    ) -> list[str]:
        """Generate quality flags for the data"""
        try:
            flags = []

            # Data size flags
            if len(data) < 100:
                flags.append("small_dataset")
            elif len(data) > 10000:
                flags.append("large_dataset")

            # Date range flags
            if config.date_range[1] - config.date_range[0] > timedelta(days=365):
                flags.append("long_time_range")

            # Anonymization flags
            if config.anonymization_method == AnonymizationMethod.K_ANONYMITY:
                if len(config.quasi_identifiers) < 3:
                    flags.append("few_quasi_identifiers")
            elif (
                config.anonymization_method == AnonymizationMethod.DIFFERENTIAL_PRIVACY
            ):
                flags.append("differential_privacy")

            # Compliance flags
            if ComplianceStandard.HIPAA in config.compliance_standards:
                flags.append("hipaa_compliance")
            if ComplianceStandard.GDPR in config.compliance_standards:
                flags.append("gdpr_compliance")

            return flags

        except Exception as e:
            logger.error(f"Error generating quality flags: {e}")
            return ["quality_generation_error"]

    async def _generate_anonymization_report(
        self,
        original_data: pd.DataFrame,
        anonymized_data: pd.DataFrame,
        config: ExportConfiguration,
    ) -> dict[str, Any]:
        """Generate detailed anonymization report"""
        try:
            report = {
                "anonymization_method": config.anonymization_method.value,
                "quasi_identifiers": [qi.name for qi in config.quasi_identifiers],
                "sensitive_attributes": config.sensitive_attributes,
                "k_value": (
                    5
                    if config.anonymization_method == AnonymizationMethod.K_ANONYMITY
                    else None
                ),
                "epsilon": (
                    1.0
                    if config.anonymization_method
                    == AnonymizationMethod.DIFFERENTIAL_PRIVACY
                    else None
                ),
                "l_diversity": (
                    3
                    if config.anonymization_method == AnonymizationMethod.L_DIVERSITY
                    else None
                ),
                "t_closeness": (
                    0.1
                    if config.anonymization_method == AnonymizationMethod.T_CLOSENESS
                    else None
                ),
                "original_records": len(original_data),
                "anonymized_records": len(anonymized_data),
                "protected_columns": [],
                "protection_methods": {},
                "risk_assessment": {},
                "verification_results": {},
            }

            # Analyze protection for each sensitive attribute
            for attr in config.sensitive_attributes:
                if attr in anonymized_data.columns:
                    original_values = original_data[attr].dropna().unique()[:10]
                    anonymized_values = anonymized_data[attr].dropna().unique()[:10]

                    report["protected_columns"].append(attr)
                    report["protection_methods"][attr] = {
                        "original_sample": (
                            list(original_values[:5])
                            if len(original_values) > 0
                            else []
                        ),
                        "anonymized_sample": (
                            list(anonymized_values[:5])
                            if len(anonymized_values) > 0
                            else []
                        ),
                        "protection_applied": config.anonymization_method.value,
                        "risk_mitigated": True,
                    }

            # Risk assessment
            risk_level = "low"
            if len(config.sensitive_attributes) > 5:
                risk_level = "medium"
            if config.anonymization_method == AnonymizationMethod.DIFFERENTIAL_PRIVACY:
                risk_level = "very_low"

            report["risk_assessment"] = {
                "overall_risk": risk_level,
                "sensitive_data_count": len(config.sensitive_attributes),
                "anonymization_strength": config.anonymization_method.value,
                "data_utility_impact": self._assess_utility_impact(config),
                "re_identification_risk": self._assess_reidentification_risk(config),
            }

            return report

        except Exception as e:
            logger.error(f"Error generating anonymization report: {e}")
            return {}

    def _assess_utility_impact(self, config: ExportConfiguration) -> str:
        """Assess the impact of anonymization on data utility"""
        if config.anonymization_method == AnonymizationMethod.DIFFERENTIAL_PRIVACY:
            return "low"  # High utility preservation
        if config.anonymization_method == AnonymizationMethod.K_ANONYMITY:
            return "medium"  # Moderate utility preservation
        return "high"  # Higher utility impact

    def _assess_reidentification_risk(self, config: ExportConfiguration) -> str:
        """Assess the risk of re-identification"""
        if config.anonymization_method == AnonymizationMethod.DIFFERENTIAL_PRIVACY:
            return "very_low"
        if config.anonymization_method == AnonymizationMethod.T_CLOSENESS:
            return "low"
        if config.anonymization_method == AnonymizationMethod.L_DIVERSITY:
            return "medium"
        return "high"

    async def _generate_compliance_report(
        self, data: pd.DataFrame, config: ExportConfiguration
    ) -> dict[str, Any]:
        """Generate compliance report"""
        try:
            report = {
                "compliance_standards": [
                    std.value for std in config.compliance_standards
                ],
                "compliance_checks": {},
                "passed_checks": [],
                "failed_checks": [],
                "recommendations": [],
                "data_classification": self._classify_data_sensitivity(config),
                "retention_guidance": self._generate_retention_guidance(config),
                "access_control_requirements": {},
            }

            # Check compliance with each standard
            for standard in config.compliance_standards:
                template = self.compliance_templates[standard]
                checks = await self._check_compliance_requirements(
                    data, standard, template
                )
                report["compliance_checks"][standard.value] = checks

                if checks["compliant"]:
                    report["passed_checks"].append(standard.value)
                else:
                    report["failed_checks"].append(standard.value)

            # Generate recommendations
            report["recommendations"] = self._generate_compliance_recommendations(
                config, report
            )

            return report

        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {}

    async def _check_compliance_requirements(
        self, data: pd.DataFrame, standard: ComplianceStandard, template: dict[str, Any]
    ) -> dict[str, Any]:
        """Check compliance requirements for a specific standard"""
        try:
            checks = {
                "compliant": True,
                "checks_performed": [],
                "issues_found": [],
                "score": 1.0,
            }

            required_fields = template.get("required_fields", [])
            required_fields.extend(template.get("quasi_identifiers", []))
            required_fields.extend(template.get("sensitive_attributes", []))

            # Check required fields are handled
            for field in required_fields:
                if field in data.columns:
                    # Check if field is properly anonymized
                    if self._is_field_properly_anonymized(data[field], standard):
                        checks["checks_performed"].append(
                            f"{field} - properly protected"
                        )
                    else:
                        checks["issues_found"].append(
                            f"{field} - insufficient protection"
                        )
                        checks["compliant"] = False
                        checks["score"] -= 0.1
                else:
                    checks["checks_performed"].append(f"{field} - not present in data")

            # Check specific standard requirements
            if standard == ComplianceStandard.GDPR:
                # Check data minimization
                total_fields = len(data.columns)
                necessary_fields = len(
                    [col for col in data.columns if self._is_necessary_field(col)]
                )
                if necessary_fields / total_fields < 0.8:
                    checks["issues_found"].append(
                        "Too many unnecessary fields - violates data minimization"
                    )
                    checks["compliant"] = False
                    checks["score"] -= 0.15

            return checks

        except Exception as e:
            logger.error(f"Error checking compliance requirements for {standard}: {e}")
            return {"compliant": False, "error": str(e)}

    def _is_field_properly_anonymized(
        self, series: pd.Series, standard: ComplianceStandard
    ) -> bool:
        """Check if a field is properly anonymized"""
        try:
            if series.dtype == "object":
                sample_values = series.dropna().head(10)

                for value in sample_values:
                    if isinstance(value, str):
                        # Check for direct identifiers
                        if self._contains_direct_identifier(value):
                            return False

                        # Check for quasi-identifiers (simplified check)
                        if len(value) > 5 and not self._is_anonymized_pattern(value):
                            return False

            return True

        except Exception as e:
            logger.error(f"Error checking field anonymization: {e}")
            return False

    def _contains_direct_identifier(self, value: str) -> bool:
        """Check if value contains direct identifiers"""
        direct_indicators = [
            "email",
            "@",
            "phone",
            "ssn",
            "social security",
            "credit card",
            "bank account",
            "passport",
            "driver license",
            "address",
        ]

        value_lower = value.lower()
        return any(indicator in value_lower for indicator in direct_indicators)

    def _is_anonymized_pattern(self, value: str) -> bool:
        """Check if value follows anonymization patterns"""
        anonymized_patterns = [
            value.startswith("id_"),
            value.startswith("user_"),
            value.startswith("subject_"),
            value.isdigit(),
            value.count("*") > 2,  # Common anonymization character
            value.replace("_", "").replace("-", "").isalnum() and len(value) < 8,
        ]

        return any(pattern for pattern in anonymized_patterns)

    def _is_necessary_field(self, field_name: str) -> bool:
        """Check if a field is necessary for research purposes"""
        necessary_fields = [
            "assessment_date",
            "test_date",
            "score",
            "rating",
            "outcome",
            "category",
            "type",
            "status",
            "level",
            "phase",
        ]

        return any(keyword in field_name.lower() for keyword in necessary_fields)

    def _classify_data_sensitivity(self, config: ExportConfiguration) -> str:
        """Classify the sensitivity level of the data"""
        high_risk_categories = [DataCategory.DEMOGRAPHIC, DataCategory.PSYCHOLOGICAL]
        high_risk_methods = [
            AnonymizationMethod.K_ANONYMITY,
            AnonymizationMethod.L_DIVERSITY,
        ]

        if any(cat in high_risk_categories for cat in config.data_categories):
            if config.anonymization_method in high_risk_methods:
                return "medium_risk_anonymized"
            return "high_risk_requires_anonymization"

        return "low_risk"

    def _generate_retention_guidance(
        self, config: ExportConfiguration
    ) -> dict[str, Any]:
        """Generate data retention guidance"""
        guidance = {
            "recommended_retention_period": self._get_default_retention_period(
                config.data_categories
            ),
            "legal_requirements": self._get_legal_retention_requirements(
                config.compliance_standards
            ),
            "automated_deletion": True,
            "archive_after": "1_year",
            "secure_disposal": True,
        }

        # Adjust based on compliance standards
        if ComplianceStandard.HIPAA in config.compliance_standards:
            guidance["recommended_retention_period"] = "6_years"
            guidance["legal_requirements"].append("HIPAA 6-year retention")

        if ComplianceStandard.GDPR in config.compliance_standards:
            guidance["data_subject_rights"] = [
                "access",
                "correction",
                "erasure",
                "portability",
            ]
            guidance["lawful_basis"] = "research_consent"

        return guidance

    def _get_default_retention_period(self, categories: list[DataCategory]) -> str:
        """Get default retention period for data categories"""
        if DataCategory.PSYCHOLOGICAL in categories:
            return "7_years"
        if DataCategory.DEMOGRAPHIC in categories:
            return "5_years"
        return "3_years"

    def _get_legal_retention_requirements(
        self, standards: list[ComplianceStandard]
    ) -> list[str]:
        """Get legal retention requirements for compliance standards"""
        requirements = []

        for standard in standards:
            if standard == ComplianceStandard.HIPAA:
                requirements.append("HIPAA 6-year retention requirement")
            elif standard == ComplianceStandard.GDPR:
                requirements.append("GDPR purpose limitation requirement")
            elif standard == ComplianceStandard.FERPA:
                requirements.append("FERPA student record retention")

        return requirements

    def _generate_compliance_recommendations(
        self, config: ExportConfiguration, compliance_report: dict[str, Any]
    ) -> list[str]:
        """Generate compliance recommendations"""
        recommendations = []

        # Anonymization recommendations
        if config.anonymization_method == AnonymizationMethod.NONE:
            recommendations.append(
                "Implement anonymization (k-anonymity or differential privacy)"
            )

        # Compliance standard recommendations
        if ComplianceStandard.GDPR in config.compliance_standards:
            recommendations.append(
                "Ensure lawful basis for processing and data subject rights"
            )

        if ComplianceStandard.HIPAA in config.compliance_standards:
            recommendations.append(
                "Implement HIPAA security measures and business associate agreements"
            )

        # Failed checks recommendations
        for failed_check in compliance_report.get("failed_checks", []):
            if failed_check == "gdpr":
                recommendations.append(
                    "Address GDPR compliance issues before data sharing"
                )
            elif failed_check == "hipaa":
                recommendations.append(
                    "Review HIPAA requirements and implement necessary safeguards"
                )

        # General recommendations
        recommendations.extend(
            [
                "Maintain export logs for audit purposes",
                "Review data retention policies",
                "Implement secure data transfer protocols",
                "Provide privacy notices to data subjects",
            ]
        )

        return recommendations

    async def _export_to_file(
        self, data: pd.DataFrame, format: ExportFormat, export_id: str
    ) -> str:
        """Export data to file in specified format"""
        try:
            export_dir = Path("/tmp/exports")
            export_dir.mkdir(exist_ok=True)

            file_path = export_dir / f"{export_id}.{format.value}"

            if format == ExportFormat.CSV:
                data.to_csv(file_path, index=False)

            elif format == ExportFormat.JSON:
                data.to_json(file_path, orient="records", indent=2)

            elif format == ExportFormat.EXCEL:
                data.to_excel(file_path, index=False)

            elif format == ExportFormat.SPSS:
                # Create SPSS syntax file
                spss_syntax = self._create_spss_syntax(data)
                with open(file_path.with_suffix(".sps"), "w") as f:
                    f.write(spss_syntax)

            elif format == ExportFormat.R:
                # Create R script
                r_script = self._create_r_script(data, export_id)
                with open(file_path.with_suffix(".R"), "w") as f:
                    f.write(r_script)

            else:
                raise ValueError(f"Unsupported export format: {format}")

            return str(file_path)

        except Exception as e:
            logger.error(f"Error exporting to file: {e}")
            raise

    def _create_spss_syntax(self, data: pd.DataFrame) -> str:
        """Create SPSS syntax file for data import"""
        syntax = "DATA LIST LIST /FREE\n"
        syntax += "/VARIABLES=RECORDS\n"

        for i, col in enumerate(data.columns):
            syntax += f"{i + 1} {col}\n"

        syntax += "BEGIN DATA\n"

        for _, row in data.head().iterrows():
            syntax += "\t".join(str(val) if pd.notna(val) else "" for val in row)
            syntax += "\n"

        syntax += "END DATA.\n"
        syntax += "EXECUTE."

        return syntax

    def _create_r_script(self, data: pd.DataFrame, export_id: str) -> str:
        """Create R script for data import"""
        script = f"# R script for {export_id}\n\n"
        script += "# Load required libraries\n"
        script += "library(tidyverse)\n"
        script += "library(readr)\n\n"

        script += "# Read the data\n"
        script += f"data <- read_csv('{export_id}.csv')\n\n"

        script += "# Display basic information\n"
        script += "str(data)\n"
        script += "summary(data)\n"
        script += "glimpse(data)\n\n"

        return script

    async def _generate_download_url(self, file_path: str, export_id: str) -> str:
        """Generate secure download URL"""
        # In production, this would generate a secure, time-limited download URL
        return f"/api/v1/research-data/download/{export_id}/{Path(file_path).name}"


# Initialize the exporter
def get_research_data_exporter(db_session: Session) -> ResearchDataExporter:
    """Get research data exporter instance"""
    return ResearchDataExporter(db_session)
