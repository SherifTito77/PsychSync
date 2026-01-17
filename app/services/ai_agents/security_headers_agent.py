"""
AI Agent: Security Headers Validator

Automatically validates security headers on all API routes.
Checks for OWASP recommended headers and provides recommendations.

Capabilities:
- Scans all registered API routes
- Validates presence of security headers
- Tests CORS configuration
- Checks CSP (Content Security Policy)
- Validates authentication requirements
- Generates security scorecards

Compliance: OWASP Security Headers Guidelines
"""

import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from fastapi import Request, Response
from fastapi.routing import APIRoute
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SecurityHeader(str):
    """Security header types"""

    # OWASP recommended headers
    STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"
    X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
    X_FRAME_OPTIONS = "X-Frame-Options"
    X_XSS_PROTECTION = "X-XSS-Protection"
    CONTENT_SECURITY_POLICY = "Content-Security-Policy"
    REFERRER_POLICY = "Referrer-Policy"
    PERMISSIONS_POLICY = "Permissions-Policy"
    CROSS_ORIGIN_OPENER_POLICY = "Cross-Origin-Opener-Policy"
    CROSS_ORIGIN_RESOURCE_POLICY = "Cross-Origin-Resource-Policy"


class SecurityLevel(Enum):
    """Security assessment levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityIssue:
    """Represents a security header issue"""

    route: str
    header: str
    severity: SecurityLevel
    issue: str
    recommendation: str
    current_value: Optional[str] = None


@dataclass
class RouteSecurityReport:
    """Security report for a single route"""

    route: str
    methods: List[str]
    auth_required: bool
    security_headers: Dict[str, Optional[str]]
    issues: List[SecurityIssue]
    security_score: float  # 0.0 to 1.0


@dataclass
class SecurityValidationSummary:
    """Summary of security validation"""

    total_routes: int
    routes_with_auth: int
    routes_with_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    overall_security_score: float
    reports: List[RouteSecurityReport]


class SecurityHeadersAgent:
    """
    AI Agent for validating security headers across all routes.

    Automatically scans and validates security configurations.
    """

    # Required security headers with their recommended values
    REQUIRED_HEADERS = {
        SecurityHeader.STRICT_TRANSPORT_SECURITY: {
            "recommended": "max-age=31536000; includeSubDomains",
            "description": "Enforces HTTPS connections",
            "severity": SecurityLevel.CRITICAL,
        },
        SecurityHeader.X_CONTENT_TYPE_OPTIONS: {
            "recommended": "nosniff",
            "description": "Prevents MIME type sniffing",
            "severity": SecurityLevel.HIGH,
        },
        SecurityHeader.X_FRAME_OPTIONS: {
            "recommended": "DENY",
            "description": "Prevents clickjacking attacks",
            "severity": SecurityLevel.HIGH,
        },
        SecurityHeader.CONTENT_SECURITY_POLICY: {
            "recommended": "default-src 'self'",
            "description": "Prevents XSS attacks",
            "severity": SecurityLevel.HIGH,
        },
        SecurityHeader.X_XSS_PROTECTION: {
            "recommended": "1; mode=block",
            "description": "XSS protection (legacy browsers)",
            "severity": SecurityLevel.MEDIUM,
        },
        SecurityHeader.REFERRER_POLICY: {
            "recommended": "strict-origin-when-cross-origin",
            "description": "Controls referrer information",
            "severity": SecurityLevel.MEDIUM,
        },
        SecurityHeader.PERMISSIONS_POLICY: {
            "recommended": "geolocation=(), microphone=(), camera=()",
            "description": "Controls browser features",
            "severity": SecurityLevel.MEDIUM,
        },
    }

    def __init__(self):
        self.validation_cache: Dict[str, RouteSecurityReport] = {}

    async def validate_all_routes(
        self,
        app_routes: List[APIRoute],
        test_client: Any,
    ) -> SecurityValidationSummary:
        """
        Validate security headers across all routes.

        Args:
            app_routes: List of FastAPI routes
            test_client: Test client for making requests

        Returns:
            Security validation summary
        """
        logger.info(f"Starting security headers validation for {len(app_routes)} routes")

        reports = []
        critical_issues = 0
        high_issues = 0
        medium_issues = 0
        low_issues = 0
        routes_with_auth = 0
        routes_with_issues = 0

        for route in app_routes:
            if not hasattr(route, "path") or not route.path.startswith("/api"):
                continue

            report = await self._validate_route(route, test_client)
            reports.append(report)

            # Count issues
            for issue in report.issues:
                if issue.severity == SecurityLevel.CRITICAL:
                    critical_issues += 1
                elif issue.severity == SecurityLevel.HIGH:
                    high_issues += 1
                elif issue.severity == SecurityLevel.MEDIUM:
                    medium_issues += 1
                elif issue.severity == SecurityLevel.LOW:
                    low_issues += 1

            if report.issues:
                routes_with_issues += 1

            if report.auth_required:
                routes_with_auth += 1

        # Calculate overall security score
        total_issues = critical_issues * 10 + high_issues * 5 + medium_issues * 2 + low_issues
        max_possible_issues = len(reports) * 7  # 7 required headers per route
        overall_score = max(0.0, 1.0 - (total_issues / max_possible_issues))

        summary = SecurityValidationSummary(
            total_routes=len(reports),
            routes_with_auth=routes_with_auth,
            routes_with_issues=routes_with_issues,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            overall_security_score=round(overall_score, 2),
            reports=reports,
        )

        logger.info(
            f"Security validation complete: {summary.overall_security_score:.0%} score, "
            f"{critical_issues} critical, {high_issues} high, {medium_issues} medium issues"
        )

        return summary

    async def _validate_route(
        self,
        route: APIRoute,
        test_client: Any,
    ) -> RouteSecurityReport:
        """
        Validate a single route.

        Args:
            route: FastAPI route
            test_client: Test client for making requests

        Returns:
            Route security report
        """
        route_path = route.path
        methods = [m for m in route.methods if m in ["GET", "POST", "PUT", "DELETE", "PATCH"]]

        # Check if route requires authentication
        auth_required = await self._check_auth_required(route)

        # Try to make a test request to check headers
        security_headers = {}
        issues = []

        try:
            # Make OPTIONS request to check headers
            response = await test_client.options(route_path)

            # Extract security headers
            for header in SecurityHeader:
                header_value = response.headers.get(header)
                security_headers[header] = header_value

                # Validate header
                header_issues = await self._validate_header(
                    route_path,
                    header,
                    header_value,
                )
                issues.extend(header_issues)

        except Exception as e:
            logger.warning(f"Could not validate route {route_path}: {str(e)}")
            # Add issue for unreachable route
            issues.append(
                SecurityIssue(
                    route=route_path,
                    header="N/A",
                    severity=SecurityLevel.MEDIUM,
                    issue="Route could not be accessed for validation",
                    recommendation="Ensure route is accessible and properly configured",
                )
            )

        # Check for CORS issues
        cors_issues = await self._check_cors_configuration(route_path, test_client)
        issues.extend(cors_issues)

        # Calculate security score for this route
        security_score = await self._calculate_route_score(issues, auth_required)

        return RouteSecurityReport(
            route=route_path,
            methods=methods,
            auth_required=auth_required,
            security_headers=security_headers,
            issues=issues,
            security_score=security_score,
        )

    async def _validate_header(
        self,
        route: str,
        header: str,
        value: Optional[str],
    ) -> List[SecurityIssue]:
        """
        Validate a security header.

        Args:
            route: Route path
            header: Header name
            value: Header value

        Returns:
            List of issues found
        """
        issues = []

        if header not in self.REQUIRED_HEADERS:
            return issues

        header_config = self.REQUIRED_HEADERS[header]

        # Check if header is missing
        if not value:
            issues.append(
                SecurityIssue(
                    route=route,
                    header=header,
                    severity=header_config["severity"],
                    issue=f"Missing {header} header",
                    recommendation=f"Add {header}: {header_config['recommended']}",
                    current_value=None,
                )
            )
            return issues

        # Validate header value
        recommended = header_config["recommended"]

        if header == SecurityHeader.STRICT_TRANSPORT_SECURITY:
            if "max-age" not in value.lower():
                issues.append(
                    SecurityIssue(
                        route=route,
                        header=header,
                        severity=SecurityLevel.HIGH,
                        issue=f"{header} missing max-age directive",
                        recommendation=f"Set {header} to: {recommended}",
                        current_value=value,
                    )
                )

        elif header == SecurityHeader.X_FRAME_OPTIONS:
            if value.upper() not in ["DENY", "SAMEORIGIN"]:
                issues.append(
                    SecurityIssue(
                        route=route,
                        header=header,
                        severity=SecurityLevel.HIGH,
                        issue=f"{header} allows framing",
                        recommendation=f"Set {header} to DENY or SAMEORIGIN",
                        current_value=value,
                    )
                )

        elif header == SecurityHeader.CONTENT_SECURITY_POLICY:
            if "default-src" not in value.lower():
                issues.append(
                    SecurityIssue(
                        route=route,
                        header=header,
                        severity=SecurityLevel.HIGH,
                        issue=f"{header} missing default-src directive",
                        recommendation=f"Include default-src in {header}",
                        current_value=value,
                    )
                )

        return issues

    async def _check_cors_configuration(
        self,
        route: str,
        test_client: Any,
    ) -> List[SecurityIssue]:
        """
        Check CORS configuration for security issues.

        Args:
            route: Route path
            test_client: Test client

        Returns:
            List of CORS-related issues
        """
        issues = []

        try:
            # Make request with Origin header
            response = await test_client.options(
                route,
                headers={"Origin": "https://malicious-site.com"}
            )

            # Check Access-Control-Allow-Origin
            allowed_origin = response.headers.get("Access-Control-Allow-Origin")

            if allowed_origin == "*" or allowed_origin == "null":
                issues.append(
                    SecurityIssue(
                        route=route,
                        header="Access-Control-Allow-Origin",
                        severity=SecurityLevel.HIGH,
                        issue="CORS allows any origin",
                        recommendation="Restrict CORS to specific trusted origins",
                        current_value=allowed_origin,
                    )
                )

            # Check for credential leaks
            allow_credentials = response.headers.get("Access-Control-Allow-Credentials")
            if allow_credentials == "true" and allowed_origin == "*":
                issues.append(
                    SecurityIssue(
                        route=route,
                        header="Access-Control-Allow-Credentials",
                        severity=SecurityLevel.CRITICAL,
                        issue="CORS credentials exposed to any origin",
                        recommendation="Remove 'Access-Control-Allow-Credentials: true' or restrict origins",
                        current_value="true with * origin",
                    )
                )

        except Exception:
            pass

        return issues

    async def _check_auth_required(self, route: APIRoute) -> bool:
        """
        Check if route requires authentication.

        Args:
            route: FastAPI route

        Returns:
            True if authentication required
        """
        # Check dependencies for authentication
        for depend in route.dependencies:
            depend_name = str(depend.dependency.__name__) if hasattr(depend.dependency, "__name__") else ""

            if "auth" in depend_name.lower() or "token" in depend_name.lower() or "user" in depend_name.lower():
                return True

        return False

    async def _calculate_route_score(
        self,
        issues: List[SecurityIssue],
        has_auth: bool,
    ) -> float:
        """
        Calculate security score for a route.

        Args:
            issues: List of security issues
            has_auth: Whether route requires authentication

        Returns:
            Security score (0.0 to 1.0)
        """
        score = 1.0

        # Deduct points for issues
        for issue in issues:
            if issue.severity == SecurityLevel.CRITICAL:
                score -= 0.25
            elif issue.severity == SecurityLevel.HIGH:
                score -= 0.15
            elif issue.severity == SecurityLevel.MEDIUM:
                score -= 0.05
            elif issue.severity == SecurityLevel.LOW:
                score -= 0.02

        # Bonus for having authentication
        if has_auth:
            score += 0.1

        return max(0.0, min(1.0, score))

    async def generate_security_recommendations(
        self,
        summary: SecurityValidationSummary,
    ) -> List[str]:
        """
        Generate actionable security recommendations.

        Args:
            summary: Security validation summary

        Returns:
            List of recommendations
        """
        recommendations = []

        # Overall recommendations
        if summary.critical_issues > 0:
            recommendations.append(
                f"🚨 CRITICAL: Address {summary.critical_issues} critical security issues immediately"
            )

        if summary.overall_security_score < 0.7:
            recommendations.append(
                f"⚠️ Security score ({summary.overall_security_score:.0%}) below 70% - prioritize security improvements"
            )

        if summary.routes_with_auth < summary.total_routes * 0.8:
            recommendations.append(
                f"🔒 Only {summary.routes_with_auth}/{summary.total_routes} routes require authentication - consider protecting more endpoints"
            )

        # Specific header recommendations
        missing_headers = set()
        for report in summary.reports:
            for issue in report.issues:
                if "Missing" in issue.issue and issue.header != "N/A":
                    missing_headers.add(issue.header)

        if missing_headers:
            recommendations.append(
                f"📋 Add missing security headers: {', '.join(sorted(missing_headers))}"
            )

        # CORS recommendations
        cors_issues = [
            issue for report in summary.reports
            for issue in report.issues
            if "CORS" in issue.issue
        ]

        if cors_issues:
            recommendations.append(
                f"🌐 Fix {len(cors_issues)} CORS misconfigurations to prevent data leaks"
            )

        return recommendations


# Global agent instance
security_headers_agent = SecurityHeadersAgent()
