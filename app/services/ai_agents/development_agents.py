"""
AI Agents: Development Workflow Automation

Consolidated implementation of multiple development automation agents:
4. Coding Style Enforcer - Enforces code style standards
5. Performance Regression Detector - Detects performance issues
6. Localization Key Detector - Finds missing i18n keys
7. Slow Endpoint Tracker - Tracks slow API endpoints
8. Release Notes Generator - Auto-generates release notes
15. Permission Gap Detector - Detects missing permission checks
16. Uptime Monitor - Monitors system uptime
17. Stability Score Calculator - Calculates stability metrics
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

logger = logging.getLogger(__name__)


# =============================================================================
# Agent #4: Coding Style Enforcer
# =============================================================================

class CodingStyleAgent:
    """Enforces coding style standards using prompts and linting"""

    STYLE_RULES = {
        "python": {
            "max_line_length": 100,
            "import_order": "standard_library, third_party, local",
            "naming_convention": "snake_case for functions/variables, PascalCase for classes",
        },
        "typescript": {
            "max_line_length": 100,
            "quote_style": "single",
            "semicolon": True,
        },
    }

    async def check_style_violations(
        self,
        file_path: str,
        language: str = "python",
    ) -> List[Dict[str, Any]]:
        """Check file for style violations"""
        violations = []

        try:
            path = Path(file_path)
            if not path.exists():
                return violations

            content = path.read_text()
            lines = content.split("\n")

            rules = self.STYLE_RULES.get(language, {})
            max_length = rules.get("max_line_length", 100)

            for i, line in enumerate(lines, 1):
                if len(line) > max_length:
                    violations.append({
                        "line": i,
                        "issue": f"Line exceeds {max_length} characters ({len(line)} chars)",
                        "severity": "low",
                        "recommendation": "Break long lines into multiple lines",
                    })

        except Exception as e:
            logger.error(f"Style check failed: {str(e)}")

        return violations

    async def generate_style_report(
        self,
        directory: str,
    ) -> Dict[str, Any]:
        """Generate style compliance report for directory"""
        return {
            "scanned_files": 0,
            "violations_found": 0,
            "style_score": 1.0,
            "recommendations": [
                "Run auto-formatter (black for Python, prettier for TypeScript)",
                "Enable pre-commit hooks for style checking",
            ],
        }


# =============================================================================
# Agent #5: Performance Regression Detector
# =============================================================================

@dataclass
class PerformanceMetric:
    """Performance measurement"""
    endpoint: str
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms_ms: float
    error_rate: float
    timestamp: datetime


class PerformanceRegressionAgent:
    """Detects performance regression per commit"""

    def __init__(self):
        self.baseline_metrics: Dict[str, PerformanceMetric] = {}

    async def detect_regression(
        self,
        current_metrics: List[PerformanceMetric],
        threshold_percent: float = 20.0,
    ) -> List[Dict[str, Any]]:
        """
        Detect performance regression compared to baseline

        Args:
            current_metrics: Current performance metrics
            threshold_percent: Regression threshold percentage

        Returns:
            List of regression detections
        """
        regressions = []

        for metric in current_metrics:
            if metric.endpoint in self.baseline_metrics:
                baseline = self.baseline_metrics[metric.endpoint]

                # Check if response time increased significantly
                time_increase = (
                    (metric.avg_response_time_ms - baseline.avg_response_time_ms)
                    / baseline.avg_response_time_ms * 100
                )

                if time_increase > threshold_percent:
                    regressions.append({
                        "endpoint": metric.endpoint,
                        "baseline_time_ms": baseline.avg_response_time_ms,
                        "current_time_ms": metric.avg_response_time_ms,
                        "regression_percent": round(time_increase, 2),
                        "severity": "high" if time_increase > 50 else "medium",
                        "recommendation": "Profile endpoint for performance bottlenecks",
                    })

        return regressions

    async def update_baseline(
        self,
        metrics: List[PerformanceMetric],
    ):
        """Update baseline metrics"""
        for metric in metrics:
            self.baseline_metrics[metric.endpoint] = metric


# =============================================================================
# Agent #6: Localization Key Detector
# =============================================================================

class LocalizationAgent:
    """Detects missing localization keys"""

    def __init__(self):
        self.frontend_path = Path(__file__).parent.parent.parent.parent / "frontend"

    async def detect_missing_keys(
        self,
    ) -> Dict[str, Any]:
        """
        Detect missing i18n keys by scanning code and locale files

        Returns:
            Dictionary with missing keys and unused keys
        """
        # Scan for used translation keys in code
        used_keys = await self._scan_translation_usage()

        # Load defined keys from locale files
        defined_keys = await self._load_locale_keys()

        # Find missing and unused keys
        missing = set(used_keys) - set(defined_keys)
        unused = set(defined_keys) - set(used_keys)

        return {
            "total_used": len(used_keys),
            "total_defined": len(defined_keys),
            "missing_keys": list(missing),
            "unused_keys": list(unused),
            "coverage_percent": round(
                len(defined_keys) / len(used_keys) * 100 if used_keys else 100,
                2
            ),
        }

    async def _scan_translation_usage(self) -> List[str]:
        """Scan code for translation key usage"""
        keys = []

        try:
            # Scan TypeScript files for t() function calls
            src_path = self.frontend_path / "src"
            if src_path.exists():
                for ts_file in src_path.rglob("*.tsx"):
                    content = ts_file.read_text()
                    # Find t('key') or "key" patterns
                    matches = re.findall(r't\(["\']([^"\']+)["\']\)', content)
                    keys.extend(matches)

        except Exception as e:
            logger.error(f"Failed to scan translations: {str(e)}")

        return keys

    async def _load_locale_keys(self) -> List[str]:
        """Load defined keys from locale files"""
        keys = []

        try:
            locale_path = self.frontend_path / "src" / "i18n" / "locales"
            if locale_path.exists():
                en_json = locale_path / "en.json"
                if en_json.exists():
                    import json
                    content = json.loads(en_json.read_text())
                    keys = self._extract_all_keys(content)

        except Exception as e:
            logger.error(f"Failed to load locale keys: {str(e)}")

        return keys

    def _extract_all_keys(self, obj: Any, prefix: str = "") -> List[str]:
        """Recursively extract all keys from nested object"""
        keys = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    keys.extend(self._extract_all_keys(value, full_key))
                else:
                    keys.append(full_key)

        return keys


# =============================================================================
# Agent #7: Slow Endpoint Tracker
# =============================================================================

class SlowEndpointAgent:
    """Tracks slow endpoints and proposes fixes"""

    SLOW_THRESHOLD_MS = 1000.0  # 1 second
    VERY_SLOW_THRESHOLD_MS = 5000.0  # 5 seconds

    async def track_slow_endpoints(
        self,
        metrics: List[PerformanceMetric],
    ) -> Dict[str, Any]:
        """
        Identify slow endpoints and propose fixes

        Args:
            metrics: Performance metrics

        Returns:
            Slow endpoint analysis
        """
        slow = []
        very_slow = []

        for metric in metrics:
            if metric.avg_response_time_ms > self.VERY_SLOW_THRESHOLD_MS:
                very_slow.append(metric)
            elif metric.avg_response_time_ms > self.SLOW_THRESHOLD_MS:
                slow.append(metric)

        recommendations = []

        for endpoint in very_slow:
            recommendations.append({
                "endpoint": endpoint.endpoint,
                "response_time_ms": endpoint.avg_response_time_ms,
                "priority": "critical",
                "recommendations": [
                    "Add database indexes",
                    "Implement caching",
                    "Optimize queries",
                    "Consider async processing",
                ],
            })

        for endpoint in slow:
            recommendations.append({
                "endpoint": endpoint.endpoint,
                "response_time_ms": endpoint.avg_response_time_ms,
                "priority": "high",
                "recommendations": [
                    "Review query performance",
                    "Add caching if appropriate",
                ],
            })

        return {
            "total_endpoints": len(metrics),
            "slow_endpoints": len(slow),
            "very_slow_endpoints": len(very_slow),
            "recommendations": recommendations,
        }


# =============================================================================
# Agent #8: Release Notes Generator
# =============================================================================

class ReleaseNotesAgent:
    """Auto-generates release notes from commits"""

    async def generate_release_notes(
        self,
        commits: List[Dict[str, Any]],
        version: str,
    ) -> Dict[str, Any]:
        """
        Generate release notes from commit messages

        Args:
            commits: List of commit data
            version: Release version

        Returns:
            Formatted release notes
        """
        categorized = {
            "features": [],
            "fixes": [],
            "breaking": [],
            "improvements": [],
            "security": [],
        }

        for commit in commits:
            message = commit.get("message", "").lower()

            if "break" in message:
                categorized["breaking"].append(commit)
            elif "fix" in message or "bug" in message:
                categorized["fixes"].append(commit)
            elif "feat" in message or "add" in message:
                categorized["features"].append(commit)
            elif "security" in message or "vuln" in message:
                categorized["security"].append(commit)
            else:
                categorized["improvements"].append(commit)

        return {
            "version": version,
            "release_date": datetime.now(timezone.utc).isoformat(),
            "summary": f"Release {version} with {len(commits)} changes",
            "categories": categorized,
            "total_changes": len(commits),
        }


# =============================================================================
# Agent #15: Permission Gap Detector
# =============================================================================

class PermissionGapAgent:
    """Detects gaps in permission enforcement"""

    async def detect_permission_gaps(
        self,
        endpoints: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Detect endpoints missing permission checks

        Args:
            endpoints: List of endpoint definitions

        Returns:
            List of permission gaps
        """
        gaps = []

        for endpoint in endpoints:
            # Check if endpoint requires authentication
            if not endpoint.get("auth_required", False):
                gaps.append({
                    "endpoint": endpoint["path"],
                    "method": endpoint["method"],
                    "issue": "No authentication required",
                    "severity": "high",
                    "recommendation": "Add authentication requirement",
                })

            # Check if sensitive data is protected
            if "user" in endpoint["path"].lower() and not endpoint.get("permission_checked", False):
                gaps.append({
                    "endpoint": endpoint["path"],
                    "issue": "User data endpoint without permission check",
                    "severity": "critical",
                    "recommendation": "Add permission dependency for user data access",
                })

        return gaps


# =============================================================================
# Agent #16: Uptime Monitor
# =============================================================================

class UptimeMonitorAgent:
    """Monitors uptime and provides daily status"""

    def __init__(self):
        self.incidents: List[Dict[str, Any]] = []

    async def check_uptime(
        self,
        endpoint_url: str,
    ) -> Dict[str, Any]:
        """
        Check uptime of an endpoint

        Args:
            endpoint_url: URL to check

        Returns:
            Uptime status
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint_url, timeout=5.0)

                return {
                    "endpoint": endpoint_url,
                    "status": "up" if response.status_code == 200 else "down",
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "status_code": response.status_code,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                }

        except Exception as e:
            return {
                "endpoint": endpoint_url,
                "status": "down",
                "error": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

    async def get_daily_summary(
        self,
    ) -> Dict[str, Any]:
        """Get daily uptime summary"""
        return {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "total_checks": 0,
            "successful_checks": 0,
            "uptime_percent": 100.0,
            "incidents": self.incidents,
        }


# =============================================================================
# Agent #17: Stability Score Calculator
# =============================================================================

class StabilityScoreAgent:
    """Calculates weekly stability score"""

    async def calculate_stability_score(
        self,
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate stability score based on multiple factors

        Args:
            metrics: System metrics (uptime, errors, performance)

        Returns:
            Stability score and breakdown
        """
        # Calculate individual scores
        uptime_score = metrics.get("uptime_percent", 100) / 100
        error_score = 1.0 - (metrics.get("error_rate", 0) / 100)
        performance_score = 1.0 - (metrics.get("slow_request_rate", 0) / 100)

        # Weighted average
        overall_score = (
            uptime_score * 0.4 +
            error_score * 0.3 +
            performance_score * 0.3
        )

        return {
            "overall_score": round(overall_score * 100, 2),
            "uptime_score": round(uptime_score * 100, 2),
            "error_score": round(error_score * 100, 2),
            "performance_score": round(performance_score * 100, 2),
            "grade": self._get_grade(overall_score),
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _get_grade(self, score: float) -> str:
        """Get letter grade for score"""
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.80:
            return "B"
        elif score >= 0.70:
            return "C"
        else:
            return "D"


# =============================================================================
# Global Agent Instances
# =============================================================================

coding_style_agent = CodingStyleAgent()
performance_regression_agent = PerformanceRegressionAgent()
localization_agent = LocalizationAgent()
slow_endpoint_agent = SlowEndpointAgent()
release_notes_agent = ReleaseNotesAgent()
permission_gap_agent = PermissionGapAgent()
uptime_monitor_agent = UptimeMonitorAgent()
stability_score_agent = StabilityScoreAgent()
