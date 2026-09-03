# app/schemas/sql_audit.py
"""
Pydantic schemas for SQL Injection Audit
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# SQL Query Schemas
class SQLQueryBase(BaseModel):
    """SQLQueryBase class.

    Description of class purpose and functionality.
    """

    query_text: str
    file_path: str = Field(..., min_length=1, max_length=500)
    line_number: int = Field(..., ge=1)
    risk_level: str = Field(..., pattern="^(critical|high|medium|low|safe)$")
    risk_score: float = Field(..., ge=0, le=100)
    vulnerability_type: Optional[str] = None
    is_parameterized: bool = False
    uses_orm: bool = False
    has_user_input: bool = False


class SQLQueryCreate(SQLQueryBase):
    """Schema definition for SQLQuery.

    Validates and serializes data for API requests/responses.
    """

    query_hash: str
    ai_suggestion: Optional[str] = None
    safe_example: Optional[str] = None
    reference_url: Optional[str] = None
    fix_priority: Optional[str] = None


class SQLQueryUpdate(BaseModel):
    """Schema definition for SQLQuery.

    Validates and serializes data for API requests/responses.
    """

    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    is_fixed: Optional[bool] = None
    fix_priority: Optional[str] = None
    ai_suggestion: Optional[str] = None
    safe_example: Optional[str] = None


class SQLQueryInDB(SQLQueryBase):
    """SQLQueryInDB class.

    Description of class purpose and functionality.
    """

    id: UUID
    query_hash: str
    ai_suggestion: Optional[str] = None
    safe_example: Optional[str] = None
    reference_url: Optional[str] = None
    is_fixed: bool
    fix_priority: Optional[str] = None
    complexity_score: Optional[float] = None
    scanned_at: datetime
    last_scanned: datetime

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class SQLQuery(SQLQueryInDB):
    """SQLQuery class.

    Description of class purpose and functionality.
    """

    pass


# SQL Vulnerability Schemas
class SQLVulnerabilityBase(BaseModel):
    """SQLVulnerabilityBase class.

    Description of class purpose and functionality.
    """

    vulnerability_type: str
    severity: str = Field(..., pattern="^(critical|high|medium|low)$")
    description: str
    injection_point: Optional[str] = None
    exploit_example: Optional[str] = None
    impact_description: Optional[str] = None


class SQLVulnerabilityCreate(SQLVulnerabilityBase):
    """Schema definition for SQLVulnerability.

    Validates and serializes data for API requests/responses.
    """

    query_id: UUID
    remediation_steps: Optional[str] = None
    code_fix: Optional[str] = None


class SQLVulnerabilityUpdate(BaseModel):
    """Schema definition for SQLVulnerability.

    Validates and serializes data for API requests/responses.
    """

    severity: Optional[str] = None
    verified_safe: Optional[bool] = None
    remediation_steps: Optional[str] = None
    code_fix: Optional[str] = None
    resolved_at: Optional[datetime] = None


class SQLVulnerabilityInDB(SQLVulnerabilityBase):
    """SQLVulnerabilityInDB class.

    Description of class purpose and functionality.
    """

    id: UUID
    query_id: UUID
    remediation_steps: Optional[str] = None
    code_fix: Optional[str] = None
    verified_safe: bool
    discovered_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class SQLVulnerability(SQLVulnerabilityInDB):
    """SQLVulnerability class.

    Description of class purpose and functionality.
    """

    pass


# SQL Scan Report Schemas
class SQLScanReportBase(BaseModel):
    """SQLScanReportBase class.

    Description of class purpose and functionality.
    """

    scan_date: datetime
    total_queries_scanned: int
    total_vulnerabilities: int
    critical_vulnerabilities: int = 0
    high_vulnerabilities: int = 0
    medium_vulnerabilities: int = 0
    low_vulnerabilities: int = 0


class SQLScanReportInDB(SQLScanReportBase):
    """SQLScanReportInDB class.

    Description of class purpose and functionality.
    """

    id: UUID
    safe_queries: int
    parameterized_queries: int
    orm_queries: int
    vulnerability_breakdown: Optional[dict[str, int]] = None
    ai_summary: Optional[str] = None
    ai_insights: Optional[dict[str, Any]] = None
    overall_risk_score: float
    risk_trend: Optional[str] = None
    vulnerabilities_trend: Optional[str] = None
    top_risk_files: Optional[list[dict[str, Any]]] = None
    top_vulnerability_types: Optional[list[dict[str, Any]]] = None

    class Config:
        """Config class.

        Description of class purpose and functionality.
        """

        from_attributes = True


class SQLScanReport(SQLScanReportInDB):
    """SQLScanReport class.

    Description of class purpose and functionality.
    """

    pass


# Summary and Trend Schemas
class SQLRiskTrend(BaseModel):
    """SQLRiskTrend class.

    Description of class purpose and functionality.
    """

    date: datetime
    total_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    overall_risk_score: float
    safe_query_percentage: float


class SQLSecuritySummary(BaseModel):
    """SQLSecuritySummary class.

    Description of class purpose and functionality.
    """

    total_queries: int
    total_vulnerabilities: int
    safe_queries: int
    at_risk_queries: int
    overall_risk_score: float
    security_grade: str  # A+ to F
    critical_issues: int
    parameterization_rate: float  # Percentage of queries using parameters
    orm_usage_rate: float  # Percentage of queries using ORM


class SQLRecommendation(BaseModel):
    """SQLRecommendation class.

    Description of class purpose and functionality.
    """

    priority: str
    category: str
    recommendation: str
    affected_files: list[str]
    estimated_effort: str  # low, medium, high
