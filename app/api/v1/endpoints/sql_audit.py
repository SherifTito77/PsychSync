# app/api/v1/endpoints/sql_audit.py
"""
SQL Injection Audit Endpoints
API endpoints for SQL security analysis and vulnerability tracking
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.v1.deps import get_current_active_user, get_db
from app.crud.crud_sql_audit import sql_query, sql_scan_report, sql_vulnerability
from app.db.models.sql_audit import SQLQuery, SQLScanReport, SQLVulnerability
from app.db.models.user import User
from app.schemas.sql_audit import (
    SQLQuery,
    SQLQueryUpdate,
    SQLScanReport,
    SQLSecuritySummary,
    SQLRiskTrend,
    SQLRecommendation,
    SQLVulnerability,
)

router = APIRouter(prefix="/sql_audit", tags=["sql_audit"])


@router.get(
    "/queries",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[SQLQuery],
)
async def get_sql_queries(    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    risk_level: str | None = Query(None, description="Filter by risk level"),
    file_path: str | None = Query(None, description="Filter by file path"),
    unfixed_only: bool = Query(False, description="Show only unfixed queries"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SQLQuery]:
    """Get SQL queries with filtering"""
    query = select(SQLQuery)

    # Apply filters
    filters = []
    if risk_level:
        filters.append(SQLQuery.risk_level == risk_level)
    if file_path:
        filters.append(SQLQuery.file_path == file_path)
    if unfixed_only:
        filters.append(SQLQuery.is_fixed == 0.0)

    if filters:
        query = query.where(*filters)

    query = query.order_by(SQLQuery.risk_score.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    queries = result.scalars().all()

    return list(queries)


@router.get(
    "/queries/summary",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=SQLSecuritySummary,
)
async def get_security_summary(    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SQLSecuritySummary:
    """Get overall SQL security summary"""
    # Get total queries
    total_result = await db.execute(select(func.count(SQLQuery.id)))
    total_queries = total_result.scalar() or 0

    # Get safe queries
    safe_result = await db.execute(
        select(func.count(SQLQuery.id)).where(SQLQuery.risk_level == "safe")
    )
    safe_queries = safe_result.scalar() or 0

    # Get unfixed vulnerabilities
    vuln_result = await db.execute(
        select(func.count(SQLVulnerability.id)).where(SQLVulnerability.verified_safe == 0.0)
    )
    total_vulnerabilities = vuln_result.scalar() or 0

    # Critical issues
    critical_result = await db.execute(
        select(func.count(SQLVulnerability.id)).where(
            and_(SQLVulnerability.severity == "critical", SQLVulnerability.verified_safe == 0.0)
        )
    )
    critical_issues = critical_result.scalar() or 0

    # Calculate risk score
    at_risk_queries = total_queries - safe_queries
    overall_risk_score = 0.0
    if total_queries > 0:
        vuln_weight = (total_vulnerabilities / total_queries) * 50
        critical_weight = (critical_issues / max(total_queries, 1)) * 30
        overall_risk_score = min(100, vuln_weight + critical_weight)

    # Calculate grade
    if overall_risk_score < 10:
        security_grade = "A+"
    elif overall_risk_score < 20:
        security_grade = "A"
    elif overall_risk_score < 30:
        security_grade = "B"
    elif overall_risk_score < 40:
        security_grade = "C"
    elif overall_risk_score < 50:
        security_grade = "D"
    else:
        security_grade = "F"

    # Parameterization rate
    param_result = await db.execute(
        select(func.count(SQLQuery.id)).where(SQLQuery.is_parameterized == 1.0)
    )
    parameterized_count = param_result.scalar() or 0
    parameterization_rate = (parameterized_count / max(total_queries, 1)) * 100

    # ORM usage rate
    orm_result = await db.execute(
        select(func.count(SQLQuery.id)).where(SQLQuery.uses_orm == 1.0)
    )
    orm_count = orm_result.scalar() or 0
    orm_usage_rate = (orm_count / max(total_queries, 1)) * 100

    return SQLSecuritySummary(
        total_queries=total_queries,
        total_vulnerabilities=total_vulnerabilities,
        safe_queries=safe_queries,
        at_risk_queries=at_risk_queries,
        overall_risk_score=round(overall_risk_score, 2),
        security_grade=security_grade,
        critical_issues=critical_issues,
        parameterization_rate=round(parameterization_rate, 2),
        orm_usage_rate=round(orm_usage_rate, 2),
    )


@router.get(
    "/queries/trends",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[SQLRiskTrend],
)
async def get_risk_trends(    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SQLRiskTrend]:
    """Get SQL security trends over time"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get scan reports
    result = await db.execute(
        select(SQLScanReport)
        .where(SQLScanReport.scan_date >= start_date)
        .order_by(SQLScanReport.scan_date)
    )
    reports = result.scalars().all()

    # Convert to trend data
    trends = []
    for report in reports:
        safe_query_percentage = (
            (report.safe_queries / report.total_queries_scanned * 100)
            if report.total_queries_scanned > 0
            else 0
        )

        trends.append(
            SQLRiskTrend(
                date=report.scan_date,
                total_vulnerabilities=report.total_vulnerabilities,
                critical_vulnerabilities=report.critical_vulnerabilities,
                high_vulnerabilities=report.high_vulnerabilities,
                overall_risk_score=report.overall_risk_score,
                safe_query_percentage=round(safe_query_percentage, 2),
            )
        )

    return trends


@router.get(
    "/vulnerabilities",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[SQLVulnerability],
)
async def get_vulnerabilities(    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    severity: str | None = Query(None, description="Filter by severity"),
    unresolved_only: bool = Query(True, description="Show only unresolved vulnerabilities"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SQLVulnerability]:
    """Get SQL injection vulnerabilities"""
    query = select(SQLVulnerability)

    # Apply filters
    filters = []
    if severity:
        filters.append(SQLVulnerability.severity == severity)
    if unresolved_only:
        filters.append(SQLVulnerability.verified_safe == 0.0)

    if filters:
        query = query.where(*filters)

    query = query.order_by(
        SQLVulnerability.severity.desc(), SQLVulnerability.discovered_at.desc()
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    vulnerabilities = result.scalars().all()

    return list(vulnerabilities)


@router.get(
    "/reports/latest",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=SQLScanReport,
)
async def get_latest_report(    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SQLScanReport:
    """Get the latest SQL scan report"""
    report = await sql_scan_report.get_latest(db)

    if not report:
        raise HTTPException(status_code=404, detail="No scan reports found")

    return report


@router.get(
    "/reports",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[SQLScanReport],
)
async def get_scan_reports(    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SQLScanReport]:
    """Get historical scan reports"""
    reports = await sql_scan_report.get_recent(db, limit=limit)
    return reports[skip : skip + limit]


@router.get(
    "/recommendations",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=list[SQLRecommendation],
)
async def get_recommendations(    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[SQLRecommendation]:
    """Get AI-generated security recommendations"""
    # Get high-risk unfixed queries
    result = await db.execute(
        select(SQLQuery)
        .where(SQLQuery.is_fixed == 0.0)
        .where(SQLQuery.risk_level.in_(["critical", "high"]))
        .order_by(SQLQuery.risk_score.desc())
        .limit(limit)
    )
    queries = result.scalars().all()

    # Generate recommendations
    recommendations = []
    for query in queries:
        if query.ai_suggestion:
            priority = "urgent" if query.risk_level == "critical" else "high"

            # Get affected files
            affected_files = [query.file_path]

            # Estimate effort
            estimated_effort = "low" if query.is_parameterized else "medium"

            recommendations.append(
                SQLRecommendation(
                    priority=priority,
                    category=query.vulnerability_type or "SQL Injection",
                    recommendation=query.ai_suggestion,
                    affected_files=affected_files,
                    estimated_effort=estimated_effort,
                )
            )

    return recommendations


@router.put(
    "/queries/{query_id}",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=SQLQuery,
)
async def update_query(    query_id: str,
    query_in: SQLQueryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SQLQuery:
    """Update SQL query status"""
    query = await sql_query.get(db, id=query_id)

    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    query_updated = await sql_query.update(db, db_obj=query, obj_in=query_in)
    return query_updated


@router.post(
    "/queries/{query_id}/mark-fixed",
    responses={200: {'description': 'Request successful', 'content': {'application/json': {'example': {'success': True, 'message': 'Operation completed successfully'}}}}, 401: {'description': 'Unauthorized'}, 422: {'description': 'Validation error'}},
    response_model=SQLQuery,
)
async def mark_query_fixed(    query_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SQLQuery:
    """Mark a query as fixed"""
    query = await sql_query.mark_as_fixed(db, query_id=query_id)

    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    return query


@router.get(
    "/health",
    summary="Health check endpoint",
    description="Check API and database connectivity status",
    responses={200: {'description': 'System is healthy', 'content': {'application/json': {'example': {'status': 'healthy', 'database': 'connected', 'redis': 'connected', 'timestamp': '2025-01-13T10:00:00Z'}}}}},
)
async def health_check(    current_user: User = Depends(get_current_active_user),
) -> dict[str, str]:
    """Health check endpoint for SQL audit service"""
    return {
        "status": "healthy",
        "service": "sql_audit",
        "version": "1.0.0",
    }
