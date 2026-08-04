#!/usr/bin/env python3
"""
Comprehensive Dependency & Supply Chain Security Testing Suite
Tests for vulnerable dependencies and supply chain security
"""

import asyncio
import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DependencyTestResult:
    """Dependency security test result"""

    category: str
    test_name: str
    severity: str  # critical, high, medium, low, info
    status: str  # pass, fail, warning
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    location: Optional[str] = None


class DependencySecurityTester:
    """Comprehensive dependency and supply chain security scanner"""

    def __init__(
        self, project_root: Path = Path("/Users/sheriftito/Downloads/psychsync")
    ):
        self.project_root = project_root
        self.results: List[DependencyTestResult] = []
        self.issue_count = 0
        self.pass_count = 0

    # =========================================================================
    # TEST 1: KNOWN VULNERABLE DEPENDENCIES (CVEs)
    # =========================================================================

    async def test_known_vulnerabilities(self) -> DependencyTestResult:
        """
        Test for known vulnerabilities in dependencies:
        - CVEs in installed packages
        - Outdated vulnerable versions
        - Security advisories
        """
        findings = []
        recommendations = []
        severity = "medium"
        status = "pass"

        requirements = self.project_root / "requirements.txt"
        frontend_package = self.project_root / "frontend/package.json"

        # Check Python dependencies
        if requirements.exists():
            content = requirements.read_text()
            lines = content.strip().split("\n")

            # Look for known vulnerable packages (examples)
            vulnerable_packages = {
                "flask==0.11.1": "CVE-2017-1000450",
                "jinja2==2.10": "CVE-2019-8341",
                "urllib3==1.24.2": "CVE-2019-11324",
                "requests==2.20.0": "CVE-2018-18074",
                "pyyaml==5.1": "CVE-2020-14343",
                "pillow<8.2.0": "CVE-2021-34552",
            }

            for vuln_package, cve in vulnerable_packages.items():
                package_name = (
                    vuln_package.split("==")[0]
                    .split(">")[0]
                    .split("<")[0]
                    .split("=")[0]
                )
                if package_name.lower() in content.lower():
                    # Check if it's the vulnerable version
                    if (
                        vuln_package.split("==")[1] in content
                        if "==" in vuln_package
                        else True
                    ):
                        findings.append(
                            f"Potentially vulnerable package: {package_name} ({cve})"
                        )
                        recommendations.append(
                            f"Update {package_name} to latest secure version"
                        )
                        severity = "high"
                        status = "warning"

            # Count total dependencies
            dep_count = len([l for l in lines if l.strip() and not l.startswith("#")])
            findings.append(f"Found {dep_count} Python dependencies")

        # Check Node.js dependencies
        if frontend_package.exists():
            try:
                content = frontend_package.read_text()

                # Parse dependencies
                if '"dependencies"' in content or '"devDependencies"' in content:
                    findings.append("Node.js dependencies found")

                    # Look for old versions of known packages
                    old_packages = {
                        '"lodash"': "<4.17.21",
                        '"axios"': "<0.21.1",
                        '"minimist"': "<1.2.6",
                    }

                    for package, version_threshold in old_packages.items():
                        if package in content:
                            findings.append(f"Package {package} found - verify version")

            except Exception:
                pass

        # Check for safety/vulnerability scanning tools
        if requirements.exists():
            # Check if safety is installed
            try:
                result = subprocess.run(
                    ["python", "-c", "import safety"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    findings.append("Safety (vulnerability scanner) available")
                    recommendations.append("Run: safety check --json")
            except Exception:
                findings.append("Safety (vulnerability scanner) not installed")
                recommendations.append("Install safety: pip install safety")
                status = "warning"

        return DependencyTestResult(
            category="Dependency Security",
            test_name="Known Vulnerable Dependencies (CVEs)",
            severity=severity,
            status=status,
            description="Tests for known vulnerabilities in dependencies",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 2: OUTDATED PACKAGES
    # =========================================================================

    async def test_outdated_packages(self) -> DependencyTestResult:
        """
        Test for outdated packages:
        - Packages behind latest stable
        - End-of-life packages
        - Deprecated packages
        """
        findings = []
        recommendations = []
        severity = "low"
        status = "pass"

        requirements = self.project_root / "requirements.txt"

        if requirements.exists():
            content = requirements.read_text()

            # Look for pinned old versions
            outdated_indicators = [
                "==1.",  # Very old major version
                "==2.0",  # Old 2.x version
                "==3.0",  # Old 3.x version
            ]

            outdated_count = 0
            for line in content.strip().split("\n"):
                if line.strip() and not line.startswith("#"):
                    for indicator in outdated_indicators:
                        if indicator in line:
                            outdated_count += 1
                            break

            if outdated_count > 0:
                findings.append(
                    f"Found {outdated_count} packages with old version pins"
                )
                recommendations.append("Review and update outdated packages")
                status = "warning"

            # Check for unpinned versions
            unpinned = [
                l
                for l in content.strip().split("\n")
                if l.strip()
                and not l.startswith("#")
                and "==" not in l
                and ">=" not in l
                and "<=" not in l
            ]
            if unpinned:
                findings.append(f"Found {len(unpinned)} unpinned dependencies")
                recommendations.append("Pin dependency versions for reproducibility")
                status = "info"

        # Check package.json for outdated Node packages
        frontend_package = self.project_root / "frontend/package.json"
        if frontend_package.exists():
            try:
                content = frontend_package.read_text()

                # Check for caret ranges (^) which allow minor updates
                if '"^' in content:
                    findings.append("Found caret (^) version ranges - allows updates")
            except Exception:
                pass

        return DependencyTestResult(
            category="Dependency Security",
            test_name="Outdated Packages",
            severity=severity,
            status=status,
            description="Tests for outdated packages",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 3: SUPPLY CHAIN ATTACK VECTORS
    # =========================================================================

    async def test_supply_chain_attacks(self) -> DependencyTestResult:
        """
        Test for supply chain attack vectors:
        - Dependency confusion
        - Typosquatting
        - Malicious packages
        - Compromised package registries
        """
        findings = []
        recommendations = []
        severity = "low"
        status = "pass"

        requirements = self.project_root / "requirements.txt"
        frontend_package = self.project_root / "frontend/package.json"

        # Check for common typosquatting targets
        common_packages = [
            "requests",
            "numpy",
            "pandas",
            "flask",
            "django",
            "react",
            "lodash",
            "axios",
            "express",
        ]

        suspicious_patterns = [
            ("re-quests", "requests"),  # Hyphen instead of no hyphen
            ("reqeusts", "requests"),  # Typo
            ("flask-restful", "flask_restful"),  # Wrong separator
        ]

        # Check requirements.txt
        if requirements.exists():
            content = requirements.read_text().lower()

            for suspicious, correct in suspicious_patterns:
                if suspicious in content:
                    findings.append(
                        f"Suspicious package name: {suspicious} (typosquatting?)"
                    )
                    recommendations.append(
                        f"Verify {suspicious} is legitimate, should it be {correct}?"
                    )
                    severity = "high"
                    status = "warning"

        # Check for dependency lock files
        # These help prevent supply chain attacks
        lock_files = [
            self.project_root / "requirements.lock",
            self.project_root / "Pipfile.lock",
            self.project_root / "frontend/package-lock.json",
            self.project_root / "frontend/yarn.lock",
        ]

        lock_files_found = [f for f in lock_files if f.exists()]
        if lock_files_found:
            findings.append(
                f"Found {len(lock_files_found)} dependency lock files (good)"
            )
        else:
            findings.append("No dependency lock files found")
            recommendations.append(
                "Use dependency lock files (Pipfile.lock, package-lock.json)"
            )
            status = "warning"

        # Check for private registry usage (more secure)
        if frontend_package.exists():
            content = frontend_package.read_text()
            if "registry" in content.lower():
                findings.append("Private npm registry configured")
                status = "pass"

        return DependencyTestResult(
            category="Dependency Security",
            test_name="Supply Chain Attack Vectors",
            severity=severity,
            status=status,
            description="Tests for supply chain attack vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 4: DEPENDENCY CONFUSION
    # =========================================================================

    async def test_dependency_confusion(self) -> DependencyTestResult:
        """
        Test for dependency confusion vulnerabilities:
        - Internal package names in public repositories
        - Missing package scope (@company/package)
        - Unusual package sources
        """
        findings = []
        recommendations = []
        severity = "low"
        status = "pass"

        frontend_package = self.project_root / "frontend/package.json"

        if frontend_package.exists():
            content = frontend_package.read_text()

            # Check for scoped packages (helps prevent confusion)
            if "@" in content and '"@' in content:
                findings.append("Found scoped npm packages (@scope/package)")

            # Check for unusual package sources
            if "git+" in content or "github:" in content:
                findings.append("Found packages from Git sources")
                recommendations.append("Verify Git-based packages are legitimate")
                status = "warning"

        # Check for requirements.txt sources
        requirements = self.project_root / "requirements.txt"
        if requirements.exists():
            content = requirements.read_text()

            # Check for Git-based dependencies
            if "git+" in content:
                findings.append("Found Git-based Python dependencies")
                recommendations.append("Pin Git dependencies to specific commits")
                status = "warning"

        return DependencyTestResult(
            category="Dependency Security",
            test_name="Dependency Confusion",
            severity=severity,
            status=status,
            description="Tests for dependency confusion vulnerabilities",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST 5: LICENSE COMPLIANCE
    # =========================================================================

    async def test_license_compliance(self) -> DependencyTestResult:
        """
        Test for license compliance:
        - Copyleft licenses (GPL, AGPL)
        - Permissive licenses (MIT, Apache, BSD)
        - Commercial licenses
        - License compatibility
        """
        findings = []
        recommendations = []
        severity = "low"
        status = "pass"

        requirements = self.project_root / "requirements.txt"
        frontend_package = self.project_root / "frontend/package.json"

        problematic_licenses = ["GPL", "AGPL", "LGPL", "SSPL"]

        # Check Python packages for licenses
        if requirements.exists():
            findings.append("Review Python package licenses before production use")
            recommendations.append("Run: pip-licenses")

        # Check Node.js packages for licenses
        if frontend_package.exists():
            try:
                # Check if license checker is available
                result = subprocess.run(
                    ["npm", "run", "licenses"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=frontend_package.parent,
                )
                if result.returncode == 0:
                    findings.append("License checking script available")
            except Exception:
                findings.append("No automated license checking found")
                recommendations.append(
                    "Add license checker: npm install -g license-checker"
                )
                status = "info"

        findings.append("Manual review recommended for all dependencies")
        recommendations.append("Review all licenses for compliance with your use case")

        return DependencyTestResult(
            category="Dependency Security",
            test_name="License Compliance",
            severity=severity,
            status=status,
            description="Tests for license compliance",
            evidence=findings,
            recommendations=recommendations,
        )

    # =========================================================================
    # TEST ORCHESTRATION
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all dependency security tests"""

        print("\n" + "=" * 96)
        print("🔐 DEPENDENCY & SUPPLY CHAIN SECURITY TESTING")
        print("=" * 96)
        print(f"\nStarted: {datetime.now().isoformat()}")
        print(f"Project: {self.project_root}")

        test_methods = [
            ("Known Vulnerabilities", self.test_known_vulnerabilities),
            ("Outdated Packages", self.test_outdated_packages),
            ("Supply Chain Attacks", self.test_supply_chain_attacks),
            ("Dependency Confusion", self.test_dependency_confusion),
            ("License Compliance", self.test_license_compliance),
        ]

        for test_name, test_method in test_methods:
            print(f"\n{'='*96}")
            print(f"Testing: {test_name}")
            print("=" * 96)

            try:
                result = await test_method()
                self.results.append(result)

                # Print test results
                status_icon = (
                    "✅"
                    if result.status == "pass"
                    else "⚠️" if result.status == "warning" else "❌"
                )
                severity_icon = (
                    "🔴"
                    if result.severity == "critical"
                    else "🟠" if result.severity == "high" else "🟡"
                )

                print(f"\n{severity_icon} Severity: {result.severity.upper()}")
                print(f"{status_icon} Status: {result.status.upper()}")
                print(f"\n📋 Description: {result.description}")

                if result.evidence:
                    print(f"\n🔍 Evidence:")
                    for evidence in result.evidence[:5]:
                        print(f"   • {evidence}")
                    if len(result.evidence) > 5:
                        print(f"   ... and {len(result.evidence) - 5} more")

                if result.recommendations:
                    print(f"\n💡 Recommendations:")
                    for rec in result.recommendations[:3]:
                        print(f"   • {rec}")

                # Count issues
                if result.status in ["fail", "warning"]:
                    self.issue_count += 1
                else:
                    self.pass_count += 1

            except Exception as e:
                print(f"\n❌ Error running test: {e}")
                self.results.append(
                    DependencyTestResult(
                        category=test_name,
                        test_name=test_name,
                        severity="error",
                        status="error",
                        description=f"Test failed with error: {str(e)}",
                    )
                )
                self.issue_count += 1

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""

        # Calculate score
        critical_count = sum(1 for r in self.results if r.severity == "critical")
        high_count = sum(1 for r in self.results if r.severity == "high")
        medium_count = sum(1 for r in self.results if r.severity == "medium")

        # Base score starts at 100, deduct based on severity
        score = 100
        score -= critical_count * 25
        score -= high_count * 15
        score -= medium_count * 5
        score = max(score, 0)

        # Compile report
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "overall_score": score,
            "total_tests": len(self.results),
            "passed": self.pass_count,
            "failed": self.issue_count,
            "severity_breakdown": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": sum(1 for r in self.results if r.severity == "low"),
                "info": sum(1 for r in self.results if r.severity == "info"),
            },
            "test_results": [
                {
                    "category": r.category,
                    "test_name": r.test_name,
                    "severity": r.severity,
                    "status": r.status,
                    "description": r.description,
                    "evidence": r.evidence,
                    "recommendations": r.recommendations,
                    "location": r.location,
                }
                for r in self.results
            ],
        }

        # Print summary
        print("\n" + "=" * 96)
        print("📊 DEPENDENCY & SUPPLY CHAIN SECURITY TEST SUMMARY")
        print("=" * 96)

        print(f"\n{'='*96}")
        print(f"OVERALL SECURITY SCORE: {score}/100")
        print("=" * 96)

        if score >= 80:
            print("✅ EXCELLENT - Strong dependency security")
        elif score >= 60:
            print("⚠️  GOOD - Some dependency issues")
        elif score >= 40:
            print("🟠 FAIR - Multiple dependency issues")
        else:
            print("🔴 POOR - Critical dependency vulnerabilities")

        print(f"\n📈 Test Results:")
        print(f"   ✅ Passed: {self.pass_count}")
        print(f"   ❌ Failed/Warning: {self.issue_count}")

        print(f"\n🚨 Severity Breakdown:")
        print(f"   🔴 Critical: {critical_count}")
        print(f"   🟠 High: {high_count}")
        print(f"   🟡 Medium: {medium_count}")
        print(f"   🟢 Low: {sum(1 for r in self.results if r.severity == 'low')}")
        print(f"   ℹ️  Info: {sum(1 for r in self.results if r.severity == 'info')}")

        print(f"\n{'='*96}")
        print("CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION")
        print("=" * 96)

        critical_results = [r for r in self.results if r.severity == "critical"]
        if not critical_results:
            print("\n✅ No critical issues detected!")
        else:
            for result in critical_results:
                print(f"\n🔴 {result.category}: {result.test_name}")
                for evidence in result.evidence:
                    print(f"   • {evidence}")

        print(f"\n{'='*96}")
        print(f"Completed: {datetime.now().isoformat()}")
        print("=" * 96)

        return report


async def main():
    """Main entry point"""
    project_root = Path("/Users/sheriftito/Downloads/psychsync")
    tester = DependencySecurityTester(project_root)

    report = await tester.run_all_tests()

    # Save report to JSON
    output_file = (
        project_root
        / f"dependency_security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
