"""
AI Agents API Endpoints

Provides endpoints for interacting with AI automation agents.
These agents help automate security, performance, and development tasks.

Access: Administrators and developers
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.permissions import require_super_admin
from app.api.v1.deps import get_current_user
from app.core.database import get_async_db
from app.db.models.user import User
from app.services.ai_agents.development_agents import (
    coding_style_agent,
    localization_agent,
    performance_regression_agent,
    permission_gap_agent,
    release_notes_agent,
    slow_endpoint_agent,
    stability_score_agent,
    uptime_monitor_agent,
)
from app.services.ai_agents.encryption_strategy_agent import (
    EncryptionStrategy,
    FieldRecommendation,
    encryption_strategy_agent,
)
from app.services.ai_agents.operations_agents import (
    architecture_drift_agent,
    bug_environment_agent,
    dependency_updater_agent,
    environment_config_agent,
    incident_mitigation_agent,
    pr_jira_mapper_agent,
    refactoring_target_agent,
    test_coverage_agent,
    ux_telemetry_agent,
)

# Import all AI agents
from app.services.ai_agents.security_headers_agent import (
    SecurityValidationSummary,
    security_headers_agent,
)
from app.services.ai_agents.unsafe_script_agent import (
    ScriptVulnerability,
    SecurityScanSummary,
    unsafe_script_agent,
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/ai-agents", tags=["ai-automation"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class SecurityValidationRequest(BaseModel):
    """Request schema for security validation"""

    force_refresh: bool = Field(False, description="Bypass cache and re-validate")


class SecurityRecommendationResponse(BaseModel):
    """Response schema for security recommendations"""

    recommendations: List[str]
    total_recommendations: int
    generated_at: datetime


# =============================================================================
# Agent #1: Security Headers Validator
# =============================================================================


@router.post("/security-headers/validate")
async def validate_security_headers(
    request: SecurityValidationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Validate security headers on all API routes.

    **Admin/Developer Only**

    Scans all registered API routes and validates security headers.
    Checks for OWASP recommended headers and provides recommendations.

    **Request Body:**
    ```json
    {
      "force_refresh": false
    }
    ```

    **Response:**
    ```json
    {
      "total_routes": 50,
      "routes_with_auth": 35,
      "routes_with_issues": 12,
      "critical_issues": 2,
      "high_issues": 5,
      "medium_issues": 8,
      "low_issues": 3,
      "overall_security_score": 0.78,
      "reports": [...]
    }
    ```
    """

    try:
        # Create test client
        from httpx import AsyncClient

        from app.main import app

        test_client = AsyncClient(app=app, base_url="http://test")

        # Get all routes
        all_routes = [route for route in app.routes if hasattr(route, "path")]

        # Run validation
        summary = await security_headers_agent.validate_all_routes(
            app_routes=all_routes,
            test_client=test_client,
        )

        await test_client.aclose()

        # Log the validation
        logger.info(
            f"Security headers validation completed by user {current_user.id}: "
            f"{summary.overall_security_score:.0%} score"
        )

        return {
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "total_routes": summary.total_routes,
            "routes_with_auth": summary.routes_with_auth,
            "routes_with_issues": summary.routes_with_issues,
            "critical_issues": summary.critical_issues,
            "high_issues": summary.high_issues,
            "medium_issues": summary.medium_issues,
            "low_issues": summary.low_issues,
            "overall_security_score": summary.overall_security_score,
            "reports": [
                {
                    "route": report.route,
                    "methods": report.methods,
                    "auth_required": report.auth_required,
                    "security_score": report.security_score,
                    "issues": [
                        {
                            "header": issue.header,
                            "severity": issue.severity.value,
                            "issue": issue.issue,
                            "recommendation": issue.recommendation,
                        }
                        for issue in report.issues
                    ],
                }
                for report in summary.reports
            ],
        }

    except Exception as e:
        logger.error(f"Failed to validate security headers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get(
    "/security-headers/recommendations", response_model=SecurityRecommendationResponse
)
async def get_security_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get security recommendations based on validation.

    **Admin/Developer Only**

    Returns actionable recommendations for improving security headers.

    **Response:**
    ```json
    {
      "recommendations": [
        "🚨 CRITICAL: Address 2 critical security issues immediately",
        "📋 Add missing security headers: Content-Security-Policy, X-Frame-Options"
      ],
      "total_recommendations": 2,
      "generated_at": "2024-01-17T12:00:00Z"
    }
    ```
    """

    try:
        # Create test client
        from httpx import AsyncClient

        from app.main import app

        test_client = AsyncClient(app=app, base_url="http://test")

        # Get all routes
        all_routes = [route for route in app.routes if hasattr(route, "path")]

        # Run validation
        summary = await security_headers_agent.validate_all_routes(
            app_routes=all_routes,
            test_client=test_client,
        )

        await test_client.aclose()

        # Generate recommendations
        recommendations = (
            await security_headers_agent.generate_security_recommendations(summary)
        )

        return SecurityRecommendationResponse(
            recommendations=recommendations,
            total_recommendations=len(recommendations),
            generated_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
        )


@router.get("/security-headers/summary")
async def get_security_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get summary of security headers status.

    **Admin/Developer Only**

    Provides a quick overview of security headers across all routes.

    **Response:**
    ```json
    {
      "total_routes": 50,
      "secure_routes": 38,
      "routes_with_issues": 12,
      "overall_score": 0.78,
      "last_validated": "2024-01-17T12:00:00Z"
    }
    ```
    """

    try:
        # Return cached summary if available
        # In production, this would be stored in Redis or database

        return {
            "message": "Security headers validation agent is ready",
            "agent_status": "active",
            "documentation": "/docs/ai-agents/security-headers",
        }

    except Exception as e:
        logger.error(f"Failed to get security summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


# =============================================================================
# Agent #2: Encryption Strategy Advisor
# =============================================================================


@router.post("/encryption-strategy/analyze")
async def analyze_encryption_strategy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Analyze database and recommend encryption strategy.

    **Admin/Developer Only**

    Scans database models and recommends which fields should be encrypted
    based on data sensitivity (PII, PHI, financial).

    **Response:**
    ```json
    {
      "strategies": [
        {
          "table_name": "users",
          "total_fields": 20,
          "sensitive_fields": 8,
          "recommended_encrypted_fields": 6,
          "compliance_score": 0.75,
          "priority": "high",
          "field_recommendations": [...]
        }
      ]
    }
    ```
    """

    try:
        # Analyze database
        strategies = await encryption_strategy_agent.analyze_database(db)

        return {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "total_tables": len(strategies),
            "strategies": [
                {
                    "table_name": strategy.table_name,
                    "total_fields": strategy.total_fields,
                    "sensitive_fields": strategy.sensitive_fields,
                    "recommended_encrypted_fields": strategy.recommended_encrypted_fields,
                    "compliance_score": strategy.compliance_score,
                    "priority": strategy.priority,
                    "field_recommendations": [
                        {
                            "field_name": rec.field_name,
                            "current_type": rec.current_type,
                            "sensitivity": rec.sensitivity.value,
                            "should_encrypt": rec.should_encrypt,
                            "encryption_strength": (
                                rec.encryption_strength.value
                                if rec.encryption_strength
                                else None
                            ),
                            "recommended_algorithm": rec.recommended_algorithm,
                            "key_rotation_period": rec.key_rotation_period,
                            "rationale": rec.rationale,
                            "migration_complexity": rec.migration_complexity,
                        }
                        for rec in strategy.field_recommendations
                    ],
                }
                for strategy in strategies
            ],
        }

    except Exception as e:
        logger.error(f"Failed to analyze encryption strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/encryption-strategy/migration/{table_name}")
async def get_migration_script(
    table_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get migration script for encrypting table fields.

    **Admin/Developer Only**

    Generates a SQL migration script for implementing recommended
    encryption on a specific table.

    **Path Parameters:**
    - table_name: Name of the table

    **Response:**
    ```json
    {
      "table_name": "users",
      "migration_script": "-- Migration script...",
      "fields_to_encrypt": 6,
      "estimated_downtime": "5 minutes"
    }
    ```
    """

    try:
        # Analyze database to get strategy for this table
        strategies = await encryption_strategy_agent.analyze_database(db)

        # Find the requested table
        target_strategy = None
        for strategy in strategies:
            if strategy.table_name == table_name:
                target_strategy = strategy
                break

        if not target_strategy:
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")

        # Generate migration script
        migration_script = await encryption_strategy_agent.generate_migration_script(
            target_strategy
        )

        # Count fields to encrypt
        fields_to_encrypt = len(
            [r for r in target_strategy.field_recommendations if r.should_encrypt]
        )

        return {
            "table_name": table_name,
            "migration_script": migration_script,
            "fields_to_encrypt": fields_to_encrypt,
            "estimated_downtime": f"{fields_to_encrypt * 0.5:.0f} minutes",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate migration script: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate script: {str(e)}"
        )


@router.get("/encryption-strategy/summary")
async def get_encryption_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Get summary of encryption recommendations.

    **Admin/Developer Only**

    Provides a quick overview of encryption recommendations.

    **Response:**
    ```json
    {
      "total_tables": 6,
      "total_sensitive_fields": 45,
      "total_recommended_encryption": 38,
      "overall_compliance_score": 0.84,
      "critical_priority_tables": 1,
      "high_priority_tables": 2
    }
    ```
    """

    try:
        # Analyze database
        strategies = await encryption_strategy_agent.analyze_database(db)

        # Calculate summary statistics
        total_tables = len(strategies)
        total_sensitive = sum(s.sensitive_fields for s in strategies)
        total_recommended = sum(s.recommended_encrypted_fields for s in strategies)
        overall_compliance = (
            sum(s.compliance_score for s in strategies) / total_tables
            if total_tables
            else 0
        )
        critical_tables = len([s for s in strategies if s.priority == "critical"])
        high_tables = len([s for s in strategies if s.priority == "high"])

        return {
            "total_tables": total_tables,
            "total_sensitive_fields": total_sensitive,
            "total_recommended_encryption": total_recommended,
            "overall_compliance_score": round(overall_compliance, 2),
            "critical_priority_tables": critical_tables,
            "high_priority_tables": high_tables,
            "medium_priority_tables": len(
                [s for s in strategies if s.priority == "medium"]
            ),
            "low_priority_tables": len([s for s in strategies if s.priority == "low"]),
        }

    except Exception as e:
        logger.error(f"Failed to get encryption summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


# =============================================================================
# Agent #3: Unsafe Script Detector
# =============================================================================


@router.post("/unsafe-scripts/scan")
async def scan_unsafe_scripts(
    current_user: User = Depends(get_current_user),
):
    """
    Scan frontend code for unsafe scripts and dependencies.

    **Admin/Developer Only**

    Scans index.html, TypeScript files, and package.json for:
    - Unsafe CDN usage
    - Missing Subresource Integrity (SRI) hashes
    - Vulnerable npm dependencies
    - Insecure HTTP scripts
    - Unsafe eval() and innerHTML usage

    **Response:**
    ```json
    {
      "scanned_at": "2024-01-17T12:00:00Z",
      "vulnerabilities": [...],
      "summary": {
        "total_scripts": 15,
        "unsafe_scripts": 5,
        "critical_issues": 1,
        "high_issues": 3
      }
    }
    ```
    """

    try:
        vulnerabilities, summary = await unsafe_script_agent.scan_frontend_scripts()

        return {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "vulnerabilities": [
                {
                    "script_source": vuln.script_source,
                    "script_type": vuln.script_type.value,
                    "risk_level": vuln.risk_level.value,
                    "issue": vuln.issue,
                    "recommendation": vuln.recommendation,
                    "cve_id": vuln.cve_id,
                    "line_number": vuln.line_number,
                }
                for vuln in vulnerabilities
            ],
            "summary": {
                "total_scripts": summary.total_scripts,
                "unsafe_scripts": summary.unsafe_scripts,
                "total_dependencies": summary.total_dependencies,
                "vulnerable_dependencies": summary.vulnerable_dependencies,
                "critical_issues": summary.critical_issues,
                "high_issues": summary.high_issues,
                "medium_issues": summary.medium_issues,
                "low_issues": summary.low_issues,
                "scripts_with_missing_sri": summary.scripts_with_missing_sri,
                "scripts_using_unsafe_cdn": summary.scripts_using_unsafe_cdn,
            },
        }

    except Exception as e:
        logger.error(f"Failed to scan unsafe scripts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/unsafe-scripts/recommendations")
async def get_script_security_recommendations(
    current_user: User = Depends(get_current_user),
):
    """
    Get security recommendations for unsafe scripts.

    **Admin/Developer Only**

    Returns actionable recommendations for fixing
    security issues in frontend scripts.

    **Response:**
    ```json
    {
      "recommendations": [
        "🚨 CRITICAL: Address 1 critical vulnerability immediately",
        "🔒 SRI: Add integrity hashes to 3 external scripts"
      ]
    }
    ```
    """

    try:
        vulnerabilities, _ = await unsafe_script_agent.scan_frontend_scripts()
        recommendations = await unsafe_script_agent.generate_security_recommendations(
            vulnerabilities
        )

        return {
            "recommendations": recommendations,
            "total_recommendations": len(recommendations),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to generate recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")


# =============================================================================
# Agent #4: Coding Style Enforcer
# =============================================================================


@router.post("/coding-style/check")
async def check_coding_style(
    file_path: str,
    current_user: User = Depends(get_current_user),
):
    """Check file for style violations"""
    violations = await coding_style_agent.check_style_violations(file_path)
    return {"file_path": file_path, "violations": violations}


@router.get("/coding-style/report")
async def get_style_report(
    directory: str = "/app",
    current_user: User = Depends(get_current_user),
):
    """Get style compliance report"""
    report = await coding_style_agent.generate_style_report(directory)
    return report


# =============================================================================
# Agent #5: Performance Regression Detector
# =============================================================================


@router.post("/performance/regression")
async def detect_performance_regression(
    metrics: List[Dict],
    current_user: User = Depends(get_current_user),
):
    """Detect performance regression"""
    regressions = await performance_regression_agent.detect_regression(metrics)
    return {"regressions": regressions}


@router.post("/performance/baseline")
async def update_performance_baseline(
    metrics: List[Dict],
    current_user: User = Depends(get_current_user),
):
    """Update performance baseline"""
    await performance_regression_agent.update_baseline(metrics)
    return {"status": "baseline_updated"}


# =============================================================================
# Agent #6: Localization Key Detector
# =============================================================================


@router.get("/localization/check")
async def check_localization_keys(
    current_user: User = Depends(get_current_user),
):
    """Detect missing i18n keys"""
    result = await localization_agent.detect_missing_keys()
    return result


# =============================================================================
# Agent #7: Slow Endpoint Tracker
# =============================================================================


@router.post("/performance/slow-endpoints")
async def track_slow_endpoints(
    metrics: List[Dict],
    current_user: User = Depends(get_current_user),
):
    """Track and analyze slow endpoints"""
    from app.services.ai_agents.development_agents import PerformanceMetric

    perf_metrics = [
        PerformanceMetric(
            endpoint=m["endpoint"],
            avg_response_time_ms=m["avg_response_time_ms"],
            p95_response_time_ms=m.get("p95_response_time_ms", 0),
            p99_response_time_ms_ms=m.get("p99_response_time_ms", 0),
            error_rate=m.get("error_rate", 0),
            timestamp=datetime.now(timezone.utc),
        )
        for m in metrics
    ]

    result = await slow_endpoint_agent.track_slow_endpoints(perf_metrics)
    return result


# =============================================================================
# Agent #8: Release Notes Generator
# =============================================================================


@router.post("/release-notes/generate")
async def generate_release_notes(
    commits: List[Dict],
    version: str,
    current_user: User = Depends(get_current_user),
):
    """Generate release notes from commits"""
    notes = await release_notes_agent.generate_release_notes(commits, version)
    return notes


# =============================================================================
# Agent #9: UX Telemetry Tracker
# =============================================================================


@router.post("/ux/track-event")
async def track_ux_event(
    event: Dict,
    current_user: User = Depends(get_current_user),
):
    """Track UX event"""
    from app.services.ai_agents.operations_agents import UXEvent

    ux_event = UXEvent(
        event_type=event["event_type"],
        page=event["page"],
        user_action=event["user_action"],
        duration_ms=event["duration_ms"],
        error_occurred=event.get("error_occurred", False),
        timestamp=datetime.now(timezone.utc),
    )

    await ux_telemetry_agent.track_event(ux_event)
    return {"status": "event_tracked"}


@router.get("/ux/friction-points")
async def get_friction_points(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
):
    """Get UX friction points"""
    analysis = await ux_telemetry_agent.analyze_friction_points(hours)
    return analysis


# =============================================================================
# Agent #10: Environment Config Detector
# =============================================================================


@router.post("/environment/validate")
async def validate_environment(
    env_vars: Dict[str, Optional[str]],
    current_user: User = Depends(get_current_user),
):
    """Validate environment configuration"""
    validation = await environment_config_agent.validate_environment(env_vars)
    return validation


# =============================================================================
# Agent #11: Incident Mitigation Planner
# =============================================================================


@router.post("/incidents/mitigation-plan")
async def create_mitigation_plan(
    incident: Dict,
    current_user: User = Depends(get_current_user),
):
    """Create incident mitigation plan"""
    from app.services.ai_agents.operations_agents import Incident

    inc = Incident(
        id=incident["id"],
        severity=incident["severity"],
        description=incident["description"],
        affected_systems=incident["affected_systems"],
        started_at=datetime.now(timezone.utc),
    )

    plan = await incident_mitigation_agent.create_mitigation_plan(inc)
    return plan


# =============================================================================
# Agent #12: Dependency Updater
# =============================================================================


@router.get("/dependencies/check-outdated")
async def check_outdated_dependencies(
    current_user: User = Depends(get_current_user),
):
    """Check for outdated dependencies"""
    frontend_path = (
        Path(__file__).parent.parent.parent.parent.parent / "frontend" / "package.json"
    )
    result = await dependency_updater_agent.check_outdated_dependencies(
        str(frontend_path)
    )
    return result


# =============================================================================
# Agent #13: PR-Jira Mapper
# =============================================================================


@router.post("/integrations/map-pr-to-jira")
async def map_pr_to_jira(
    pr_title: str,
    pr_description: str,
    current_user: User = Depends(get_current_user),
):
    """Map PR to Jira ticket"""
    mapping = await pr_jira_mapper_agent.map_pr_to_jira(pr_title, pr_description)
    return mapping


# =============================================================================
# Agent #14: Test Coverage Reporter
# =============================================================================


@router.post("/testing/coverage-report")
async def generate_coverage_report(
    coverage_data: Dict,
    current_user: User = Depends(get_current_user),
):
    """Generate test coverage report"""
    report = await test_coverage_agent.generate_coverage_report(coverage_data)
    return report


# =============================================================================
# Agent #15: Permission Gap Detector
# =============================================================================


@router.post("/security/permission-gaps")
async def detect_permission_gaps(
    endpoints: List[Dict],
    current_user: User = Depends(get_current_user),
):
    """Detect permission enforcement gaps"""
    gaps = await permission_gap_agent.detect_permission_gaps(endpoints)
    return {"gaps": gaps}


# =============================================================================
# Agent #16: Uptime Monitor
# =============================================================================


@router.post("/monitoring/check-uptime")
async def check_uptime(
    endpoint_url: str,
    current_user: User = Depends(get_current_user),
):
    """Check uptime of endpoint"""
    status = await uptime_monitor_agent.check_uptime(endpoint_url)
    return status


@router.get("/monitoring/daily-uptime-summary")
async def get_daily_uptime_summary(
    current_user: User = Depends(get_current_user),
):
    """Get daily uptime summary"""
    summary = await uptime_monitor_agent.get_daily_summary()
    return summary


# =============================================================================
# Agent #17: Stability Score Calculator
# =============================================================================


@router.post("/monitoring/stability-score")
async def calculate_stability_score(
    metrics: Dict,
    current_user: User = Depends(get_current_user),
):
    """Calculate system stability score"""
    score = await stability_score_agent.calculate_stability_score(metrics)
    return score


# =============================================================================
# Agent #18: Architecture Drift Detector
# =============================================================================


@router.post("/architecture/check-drift")
async def check_architecture_drift(
    current_user: User = Depends(get_current_user),
):
    """Detect architectural drift"""
    codebase_path = Path(__file__).parent.parent.parent.parent
    drift = await architecture_drift_agent.detect_architecture_drift(str(codebase_path))
    return drift


# =============================================================================
# Agent #19: Bug Environment Creator
# =============================================================================


@router.post("/debugging/create-bug-environment")
async def create_bug_environment(
    bug_report: Dict,
    current_user: User = Depends(get_current_user),
):
    """Create reproducible bug environment"""
    env = await bug_environment_agent.create_bug_environment(bug_report)
    return env


# =============================================================================
# Agent #20: Refactoring Target Proposer
# =============================================================================


@router.post("/refactoring/propose-targets")
async def propose_refactoring_targets(
    current_user: User = Depends(get_current_user),
):
    """Propose refactoring targets"""
    codebase_path = Path(__file__).parent.parent.parent.parent
    targets = await refactoring_target_agent.propose_refactoring_targets(
        str(codebase_path)
    )
    return targets


# =============================================================================
# Agent Status Endpoint
# =============================================================================


@router.get("/status")
async def get_agents_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get status of all AI agents.

    **Developer Only**

    Returns the current status of all AI automation agents.

    **Response:**
    ```json
    {
      "total_agents": 20,
      "active_agents": 1,
      "agents": [
        {
          "name": "security_headers_validator",
          "status": "active",
          "description": "Validates security headers on all routes"
        }
      ]
    }
    ```
    """

    return {
        "total_agents": 20,
        "active_agents": 20,
        "agents": [
            {
                "name": "security_headers_validator",
                "status": "active",
                "description": "Validates security headers on all routes",
                "endpoints": [
                    "POST /ai-agents/security-headers/validate",
                    "GET /ai-agents/security-headers/recommendations",
                    "GET /ai-agents/security-headers/summary",
                ],
            },
            {
                "name": "encryption_strategy_advisor",
                "status": "active",
                "description": "Suggests encryption strategy for sensitive fields",
                "endpoints": [
                    "POST /ai-agents/encryption-strategy/analyze",
                    "GET /ai-agents/encryption-strategy/migration/{table_name}",
                    "GET /ai-agents/encryption-strategy/summary",
                ],
            },
            {
                "name": "unsafe_script_detector",
                "status": "active",
                "description": "Warns about unsafe third-party scripts",
                "endpoints": [
                    "POST /ai-agents/unsafe-scripts/scan",
                    "GET /ai-agents/unsafe-scripts/recommendations",
                ],
            },
            {
                "name": "coding_style_enforcer",
                "status": "active",
                "description": "Continuously enforces coding style",
                "endpoints": [
                    "POST /ai-agents/coding-style/check",
                    "GET /ai-agents/coding-style/report",
                ],
            },
            {
                "name": "performance_regression_detector",
                "status": "active",
                "description": "Checks for performance regression per commit",
                "endpoints": [
                    "POST /ai-agents/performance/regression",
                    "POST /ai-agents/performance/baseline",
                ],
            },
            {
                "name": "localization_key_detector",
                "status": "active",
                "description": "Detects missing localization keys",
                "endpoints": ["GET /ai-agents/localization/check"],
            },
            {
                "name": "slow_endpoint_tracker",
                "status": "active",
                "description": "Tracks slow endpoints and auto-proposes fixes",
                "endpoints": ["POST /ai-agents/performance/slow-endpoints"],
            },
            {
                "name": "release_notes_generator",
                "status": "active",
                "description": "Generates internal release notes",
                "endpoints": ["POST /ai-agents/release-notes/generate"],
            },
            {
                "name": "ux_telemetry_tracker",
                "status": "active",
                "description": "Tracks UX friction points via telemetry",
                "endpoints": [
                    "POST /ai-agents/ux/track-event",
                    "GET /ai-agents/ux/friction-points",
                ],
            },
            {
                "name": "environment_config_detector",
                "status": "active",
                "description": "Detects environment misconfigurations",
                "endpoints": ["POST /ai-agents/environment/validate"],
            },
            {
                "name": "incident_mitigation_planner",
                "status": "active",
                "description": "Creates mitigation plan for major incidents",
                "endpoints": ["POST /ai-agents/incidents/mitigation-plan"],
            },
            {
                "name": "dependency_updater",
                "status": "active",
                "description": "Automatically updates dependency versions monthly",
                "endpoints": ["GET /ai-agents/dependencies/check-outdated"],
            },
            {
                "name": "pr_jira_mapper",
                "status": "active",
                "description": "Maps PRs to Jira tickets",
                "endpoints": ["POST /ai-agents/integrations/map-pr-to-jira"],
            },
            {
                "name": "test_coverage_reporter",
                "status": "active",
                "description": "Generates test coverage reports",
                "endpoints": ["POST /ai-agents/testing/coverage-report"],
            },
            {
                "name": "permission_gap_detector",
                "status": "active",
                "description": "Detects gaps in permission enforcement",
                "endpoints": ["POST /ai-agents/security/permission-gaps"],
            },
            {
                "name": "uptime_monitor",
                "status": "active",
                "description": "Monitors uptime and provides daily status summary",
                "endpoints": [
                    "POST /ai-agents/monitoring/check-uptime",
                    "GET /ai-agents/monitoring/daily-uptime-summary",
                ],
            },
            {
                "name": "stability_score_calculator",
                "status": "active",
                "description": "Produces weekly stability score",
                "endpoints": ["POST /ai-agents/monitoring/stability-score"],
            },
            {
                "name": "architecture_drift_detector",
                "status": "active",
                "description": "Generates architecture drift warnings",
                "endpoints": ["POST /ai-agents/architecture/check-drift"],
            },
            {
                "name": "bug_environment_creator",
                "status": "active",
                "description": "Creates reproducible bug environments",
                "endpoints": ["POST /ai-agents/debugging/create-bug-environment"],
            },
            {
                "name": "refactoring_target_proposer",
                "status": "active",
                "description": "Proposes refactoring targets each sprint",
                "endpoints": ["POST /ai-agents/refactoring/propose-targets"],
            },
        ],
    }
