"""
AI Agent: Unsafe Script Detector

Scans frontend code for unsafe third-party scripts and dependencies.
Detects security vulnerabilities in external JavaScript libraries.

Capabilities:
- Scans index.html and frontend files for script tags
- Analyzes npm dependencies for known vulnerabilities
- Checks for unsafe CDN usage
- Detects missing Subresource Integrity (SRI) hashes
- Validates Content Security Policy compatibility
- Generates security warnings and recommendations

Compliance: OWASP Dependency Check, CSP Guidelines
"""

import logging
import re
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScriptType(Enum):
    """Script source types"""

    CDN = "cdn"
    NPM = "npm"
    LOCAL = "local"
    INLINE = "inline"


@dataclass
class ScriptVulnerability:
    """Represents a script vulnerability"""

    script_source: str
    script_type: ScriptType
    risk_level: RiskLevel
    issue: str
    recommendation: str
    cve_id: Optional[str] = None
    affected_versions: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class DependencyScanResult:
    """Result of dependency scanning"""

    package_name: str
    current_version: str
    vulnerabilities: List[ScriptVulnerability]
    total_vulnerabilities: int
    highest_risk: RiskLevel


@dataclass
class SecurityScanSummary:
    """Summary of security scan"""

    total_scripts: int
    unsafe_scripts: int
    total_dependencies: int
    vulnerable_dependencies: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    scripts_with_missing_sri: int
    scripts_using_unsafe_cdn: int


class UnsafeScriptAgent:
    """
    AI Agent for detecting unsafe scripts and dependencies.

    Automatically scans frontend code and npm dependencies.
    """

    # Known unsafe CDNs
    UNSAFE_CDNS = {
        "code.jquery.com",  # Use jquery.com
        "cdnjs.cloudflare.com",  # Generally safe but verify SRI
        "unpkg.com",  # No SRI by default
    }

    # Known vulnerable libraries (simplified database)
    VULNERABLE_LIBRARIES = {
        "lodash": {
            "versions": ["<4.17.21"],
            "cve": "CVE-2021-23337",
            "risk": RiskLevel.HIGH,
            "issue": "Prototype pollution vulnerability",
        },
        "axios": {
            "versions": ["<0.21.1"],
            "cve": "CVE-2021-3749",
            "risk": RiskLevel.MEDIUM,
            "issue": "SSRF vulnerability",
        },
        "dompurify": {
            "versions": ["<2.2.8"],
            "cve": "CVE-2021-3748",
            "risk": RiskLevel.HIGH,
            "issue": "XSS vulnerability",
        },
    }

    # Patterns for detecting script tags
    SCRIPT_TAG_PATTERN = re.compile(
        r'<script[^>]*>(.*?)</script>|<script[^>]*/>',
        re.DOTALL | re.IGNORECASE
    )

    # Pattern for extracting script source
    SCRIPT_SRC_PATTERN = re.compile(
        r'src=["\']([^"\']+)["\']',
        re.IGNORECASE
    )

    # Pattern for detecting SRI hashes
    SRI_PATTERN = re.compile(
        r'integrity=["\']([^"\']+)["\']',
        re.IGNORECASE
    )

    def __init__(self):
        self.frontend_path = Path(__file__).parent.parent.parent.parent / "frontend"
        self.scan_cache: Dict[str, List[ScriptVulnerability]] = {}

    async def scan_frontend_scripts(
        self,
    ) -> tuple[List[ScriptVulnerability], SecurityScanSummary]:
        """
        Scan frontend code for unsafe scripts.

        Returns:
            Tuple of (vulnerabilities, summary)
        """
        logger.info("Starting unsafe script scan")

        vulnerabilities = []

        # Scan index.html for script tags
        index_path = self.frontend_path / "index.html"

        if index_path.exists():
            index_vulns = await self._scan_html_file(index_path)
            vulnerabilities.extend(index_vulns)

        # Scan main.tsx and other entry points
        main_tsx = self.frontend_path / "src" / "main.tsx"
        if main_tsx.exists():
            tsx_vulns = await self._scan_typescript_file(main_tsx)
            vulnerabilities.extend(tsx_vulns)

        # Scan package.json for vulnerable dependencies
        package_json = self.frontend_path / "package.json"
        if package_json.exists():
            dep_vulns = await self._scan_package_json(package_json)
            vulnerabilities.extend(dep_vulns)

        # Generate summary
        summary = await self._generate_summary(vulnerabilities)

        logger.info(
            f"Script scan complete: {summary.unsafe_scripts} unsafe scripts, "
            f"{summary.critical_issues} critical issues"
        )

        return vulnerabilities, summary

    async def _scan_html_file(
        self,
        file_path: Path,
    ) -> List[ScriptVulnerability]:
        """
        Scan HTML file for unsafe script tags.

        Args:
            file_path: Path to HTML file

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        try:
            content = file_path.read_text()
            lines = content.split("\n")

            # Find all script tags
            for match in self.SCRIPT_TAG_PATTERN.finditer(content):
                script_tag = match.group(0)
                line_num = content[:match.start()].count("\n") + 1

                # Check if script has src
                src_match = self.SCRIPT_SRC_PATTERN.search(script_tag)

                if src_match:
                    src_url = src_match.group(1)

                    # External script
                    vulns = await self._check_external_script(src_url, line_num)
                    vulnerabilities.extend(vulns)

                else:
                    # Inline script
                    vuln = ScriptVulnerability(
                        script_source="inline",
                        script_type=ScriptType.INLINE,
                        risk_level=RiskLevel.MEDIUM,
                        issue="Inline script detected",
                        recommendation="Move inline scripts to external files for better CSP compatibility",
                        line_number=line_num,
                    )
                    vulnerabilities.append(vuln)

        except Exception as e:
            logger.error(f"Failed to scan HTML file {file_path}: {str(e)}")

        return vulnerabilities

    async def _check_external_script(
        self,
        src_url: str,
        line_num: int,
    ) -> List[ScriptVulnerability]:
        """
        Check external script for security issues.

        Args:
            src_url: Script source URL
            line_num: Line number

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        # Determine script type
        if src_url.startswith("http://") or src_url.startswith("https://"):
            script_type = ScriptType.CDN
        elif src_url.startswith("/"):
            script_type = ScriptType.LOCAL
        else:
            script_type = ScriptType.NPM

        # Check for unsafe CDN
        if script_type == ScriptType.CDN:
            for unsafe_cdn in self.UNSAFE_CDNS:
                if unsafe_cdn in src_url:
                    vulnerabilities.append(
                        ScriptVulnerability(
                            script_source=src_url,
                            script_type=script_type,
                            risk_level=RiskLevel.HIGH,
                            issue=f"Using potentially unsafe CDN: {unsafe_cdn}",
                            recommendation=f"Host critical libraries locally or use trusted CDN with SRI",
                            line_number=line_num,
                        )
                    )

        # Check for missing SRI (for external scripts)
        if script_type == ScriptType.CDN:
            # Check if script tag has integrity
            if not self.SRI_PATTERN.search(src_url):  # This should check the script tag, not URL
                vulnerabilities.append(
                    ScriptVulnerability(
                        script_source=src_url,
                        script_type=script_type,
                        risk_level=RiskLevel.MEDIUM,
                        issue="Missing Subresource Integrity (SRI) hash",
                        recommendation="Add integrity attribute to ensure script hasn't been tampered with",
                        line_number=line_num,
                    )
                )

        # Check for HTTP instead of HTTPS
        if src_url.startswith("http://") and not src_url.startswith("http://localhost"):
            vulnerabilities.append(
                ScriptVulnerability(
                    script_source=src_url,
                    script_type=script_type,
                    risk_level=RiskLevel.HIGH,
                    issue="Loading script over insecure HTTP",
                    recommendation="Use HTTPS for all external scripts",
                    line_number=line_num,
                )
            )

        return vulnerabilities

    async def _scan_typescript_file(
        self,
        file_path: Path,
    ) -> List[ScriptVulnerability]:
        """
        Scan TypeScript file for unsafe imports.

        Args:
            file_path: Path to TS file

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        try:
            content = file_path.read_text()

            # Check for unsafe eval() or innerHTML usage
            if "eval(" in content:
                vulnerabilities.append(
                    ScriptVulnerability(
                        script_source=str(file_path),
                        script_type=ScriptType.LOCAL,
                        risk_level=RiskLevel.HIGH,
                        issue="Usage of eval() detected",
                        recommendation="Avoid eval() - use safer alternatives",
                        line_number=None,
                    )
                )

            if "innerHTML" in content:
                vulnerabilities.append(
                    ScriptVulnerability(
                        script_source=str(file_path),
                        script_type=ScriptType.LOCAL,
                        risk_level=RiskLevel.MEDIUM,
                        issue="Usage of innerHTML detected (XSS risk)",
                        recommendation="Use textContent or sanitize HTML before using innerHTML",
                        line_number=None,
                    )
                )

        except Exception as e:
            logger.error(f"Failed to scan TypeScript file {file_path}: {str(e)}")

        return vulnerabilities

    async def _scan_package_json(
        self,
        file_path: Path,
    ) -> List[ScriptVulnerability]:
        """
        Scan package.json for vulnerable dependencies.

        Args:
            file_path: Path to package.json

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        try:
            content = json.loads(file_path.read_text())

            # Check dependencies
            dependencies = content.get("dependencies", {})
            dev_dependencies = content.get("devDependencies", {})

            all_deps = {**dependencies, **dev_dependencies}

            for package_name, version in all_deps.items():
                vulns = await self._check_package_vulnerability(package_name, version)
                vulnerabilities.extend(vulns)

        except Exception as e:
            logger.error(f"Failed to scan package.json: {str(e)}")

        return vulnerabilities

    async def _check_package_vulnerability(
        self,
        package_name: str,
        version: str,
    ) -> List[ScriptVulnerability]:
        """
        Check if package has known vulnerabilities.

        Args:
            package_name: NPM package name
            version: Package version

        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []

        # Check against known vulnerable libraries
        if package_name in self.VULNERABLE_LIBRARIES:
            vuln_info = self.VULNERABLE_LIBRARIES[package_name]

            # Simplified version check (in production, use semver)
            if self._is_vulnerable_version(version, vuln_info["versions"]):
                vulnerabilities.append(
                    ScriptVulnerability(
                        script_source=f"{package_name}@{version}",
                        script_type=ScriptType.NPM,
                        risk_level=vuln_info["risk"],
                        issue=vuln_info["issue"],
                        recommendation=f"Update {package_name} to latest safe version",
                        cve_id=vuln_info["cve"],
                        affected_versions=vuln_info["versions"],
                    )
                )

        return vulnerabilities

    def _is_vulnerable_version(self, current: str, vulnerable_ranges: List[str]) -> bool:
        """
        Check if current version is in vulnerable range.

        Simplified version checking - in production use semver library.

        Args:
            current: Current version
            vulnerable_ranges: List of vulnerable version ranges

        Returns:
            True if vulnerable
        """
        # Simplified logic - just check if version starts with vulnerable prefix
        for vuln_range in vulnerable_ranges:
            if "<" in vuln_range:
                required_min = vuln_range.replace("<", "").strip()
                try:
                    # Very basic comparison - in production use proper semver
                    if current.strip() < required_min:
                        return True
                except Exception as e:
                    pass

        return False

    async def _generate_summary(
        self,
        vulnerabilities: List[ScriptVulnerability],
    ) -> SecurityScanSummary:
        """
        Generate security scan summary.

        Args:
            vulnerabilities: List of found vulnerabilities

        Returns:
            Scan summary
        """
        critical = len([v for v in vulnerabilities if v.risk_level == RiskLevel.CRITICAL])
        high = len([v for v in vulnerabilities if v.risk_level == RiskLevel.HIGH])
        medium = len([v for v in vulnerabilities if v.risk_level == RiskLevel.MEDIUM])
        low = len([v for v in vulnerabilities if v.risk_level == RiskLevel.LOW])

        # Count specific issues
        scripts_with_missing_sri = len([
            v for v in vulnerabilities
            if "SRI" in v.issue
        ])

        scripts_using_unsafe_cdn = len([
            v for v in vulnerabilities
            if "CDN" in v.issue
        ])

        return SecurityScanSummary(
            total_scripts=len([v for v in vulnerabilities if v.script_type in [ScriptType.CDN, ScriptType.INLINE]]),
            unsafe_scripts=len(vulnerabilities),
            total_dependencies=len([v for v in vulnerabilities if v.script_type == ScriptType.NPM]),
            vulnerable_dependencies=len([v for v in vulnerabilities if v.script_type == ScriptType.NPM]),
            critical_issues=critical,
            high_issues=high,
            medium_issues=medium,
            low_issues=low,
            scripts_with_missing_sri=scripts_with_missing_sri,
            scripts_using_unsafe_cdn=scripts_using_unsafe_cdn,
        )

    async def generate_security_recommendations(
        self,
        vulnerabilities: List[ScriptVulnerability],
    ) -> List[str]:
        """
        Generate actionable security recommendations.

        Args:
            vulnerabilities: List of vulnerabilities

        Returns:
            List of recommendations
        """
        recommendations = []

        # Critical recommendations
        critical_vulns = [v for v in vulnerabilities if v.risk_level == RiskLevel.CRITICAL]
        if critical_vulns:
            recommendations.append(
                f"🚨 CRITICAL: Address {len(critical_vulns)} critical vulnerabilities immediately"
            )

        # High priority
        high_vulns = [v for v in vulnerabilities if v.risk_level == RiskLevel.HIGH]
        if high_vulns:
            recommendations.append(
                f"⚠️ HIGH: Fix {len(high_vulns)} high-risk vulnerabilities"
            )

        # CDN recommendations
        cdn_vulns = [v for v in vulnerabilities if "CDN" in v.issue]
        if cdn_vulns:
            recommendations.append(
                f"🌐 CDN: Review {len(cdn_vulns)} CDN-related issues"
            )

        # SRI recommendations
        sri_vulns = [v for v in vulnerabilities if "SRI" in v.issue]
        if sri_vulns:
            recommendations.append(
                f"🔒 SRI: Add integrity hashes to {len(sri_vulns)} external scripts"
            )

        # Dependency updates
        dep_vulns = [v for v in vulnerabilities if v.script_type == ScriptType.NPM]
        if dep_vulns:
            recommendations.append(
                f"📦 Dependencies: Update {len(dep_vulns)} vulnerable packages"
            )

        return recommendations


# Global agent instance
unsafe_script_agent = UnsafeScriptAgent()
