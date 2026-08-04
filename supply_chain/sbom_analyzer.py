"""
SBOM Rapid Impact Assessment Tool
Analyzes Software Bill of Materials (SBOM) for security vulnerabilities and dependencies.

Features:
- CycloneDX and SPDX format support
- Dependency tree traversal
- Vulnerability scanning integration
- License compliance checking
- Hash verification
- Impact analysis by environment
- Rapid threat assessment

Author: PsychSync Security Team
Version: 1.0.0
"""

import hashlib
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

logger = logging.getLogger(__name__)


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class Dependency:
    """Represents a software dependency."""

    name: str
    version: str
    purl: Optional[str] = None  # Package URL
    type: str = "library"  # library, application, framework
    licenses: List[str] = field(default_factory=list)
    supplier: Optional[str] = None
    download_location: Optional[str] = None
    hashes: Dict[str, str] = field(default_factory=dict)  # alg -> hash
    dependencies: List[str] = field(default_factory=list)  # Child deps

    def __hash__(self):
        return hash((self.name, self.version))


@dataclass
class VulnerabilityInfo:
    """Vulnerability information from NVD or other sources."""

    cve_id: str
    severity: VulnerabilitySeverity
    cvss_score: Optional[float] = None
    description: str = ""
    affected_versions: List[str] = field(default_factory=list)
    patched_versions: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    published_date: Optional[str] = None
    modified_date: Optional[str] = None


@dataclass
class ImpactAssessment:
    """Impact assessment for a compromised dependency."""

    dependency: Dependency
    severity: VulnerabilitySeverity
    affected_services: List[str]
    affected_environments: List[str]  # dev, staging, production
    exploit_available: bool
    exploit_maturity: str  # none, poc, active, high
    has_patch: bool
    patch_version: Optional[str] = None
    cvss_score: Optional[float] = None
    attack_vector: Optional[str] = None  # network, adjacent, local, physical
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SBOMAnalysisReport:
    """Complete SBOM analysis report."""

    sbom_id: str
    analysis_timestamp: str
    total_dependencies: int
    transitive_dependencies: int
    vulnerabilities_found: int
    critical_vulnerabilities: int
    license_violations: int
    hash_mismatches: int
    impact_assessments: List[ImpactAssessment]
    dependency_tree: Dict[str, List[str]]
    compliance_status: Dict[str, bool]
    recommendations: List[str]

    def to_json(self) -> str:
        """Convert report to JSON."""
        return json.dumps(
            {
                "sbom_id": self.sbom_id,
                "analysis_timestamp": self.analysis_timestamp,
                "total_dependencies": self.total_dependencies,
                "transitive_dependencies": self.transitive_dependencies,
                "vulnerabilities_found": self.vulnerabilities_found,
                "critical_vulnerabilities": self.critical_vulnerabilities,
                "license_violations": self.license_violations,
                "hash_mismatches": self.hash_mismatches,
                "impact_assessments": [
                    {
                        "dependency": {
                            "name": i.dependency.name,
                            "version": i.dependency.version,
                            "purl": i.dependency.purl,
                            "type": i.dependency.type,
                        },
                        "severity": i.severity.value,
                        "affected_services": i.affected_services,
                        "affected_environments": i.affected_environments,
                        "exploit_available": i.exploit_available,
                        "exploit_maturity": i.exploit_maturity,
                        "has_patch": i.has_patch,
                        "patch_version": i.patch_version,
                        "cvss_score": i.cvss_score,
                        "attack_vector": i.attack_vector,
                        "recommendations": i.recommendations,
                    }
                    for i in self.impact_assessments
                ],
                "dependency_tree": self.dependency_tree,
                "compliance_status": self.compliance_status,
                "recommendations": self.recommendations,
            },
            indent=2,
        )


class SBOMAnalyzer:
    """
    Analyze SBOMs for security vulnerabilities and impact.

    Supports:
    - CycloneDX JSON format
    - SPDX JSON format
    - Dependency tree analysis
    - Vulnerability database queries (NVD, GitHub Advisories)
    - License compliance checking
    """

    # Vulnerability databases
    NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    GITHUB_ADVISORIES_URL = "https://github.com/advisories"
    PYSEC_DB = "https://pypi.org/pypi/{}/json"

    # License compliance (example allowlist)
    ALLOWED_LICENSES = {
        "MIT",
        "Apache-2.0",
        "Apache-1.1",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "ISC",
        "Python-2.0",
        "PSF-2.0",
        "0BSD",
    }

    # Prohibited licenses (copyleft that requires source disclosure)
    PROHIBITED_LICENSES = {"GPL-3.0", "AGPL-3.0", "SSPL", "MPL-2.0", "CDDL-1.0"}

    def __init__(
        self,
        enable_vuln_scan: bool = True,
        enable_license_check: bool = True,
        enable_hash_verify: bool = True,
        nvd_api_key: Optional[str] = None,
    ):
        """
        Initialize SBOM analyzer.

        Args:
            enable_vuln_scan: Enable vulnerability scanning
            enable_license_check: Enable license compliance checking
            enable_hash_verify: Enable hash verification
            nvd_api_key: NVD API key (optional, for higher rate limits)
        """
        self.enable_vuln_scan = enable_vuln_scan
        self.enable_license_check = enable_license_check
        self.enable_hash_verify = enable_hash_verify
        self.nvd_api_key = nvd_api_key

        self.session = requests.Session()
        if nvd_api_key:
            self.session.headers.update({"apiKey": nvd_api_key})

    def analyze_sbom(
        self,
        sbom_path: str,
        deployment_manifest: Optional[str] = None,
        baseline_sbom: Optional[str] = None,
    ) -> SBOMAnalysisReport:
        """
        Analyze SBOM for security issues and impact.

        Args:
            sbom_path: Path to SBOM file (CycloneDX or SPDX)
            deployment_manifest: Path to deployment manifest (K8s, docker-compose)
            baseline_sbom: Path to baseline SBOM for comparison

        Returns:
            SBOMAnalysisReport with complete analysis
        """
        # Load SBOM
        sbom = self._load_sbom(sbom_path)

        # Parse dependencies
        dependencies = self._parse_dependencies(sbom)

        # Build dependency tree
        dependency_tree = self._build_dependency_tree(dependencies)

        # Check for vulnerabilities
        impact_assessments = []
        vuln_count = 0
        critical_count = 0

        if self.enable_vuln_scan:
            for dep in dependencies:
                vulns = self._check_vulnerabilities(dep)
                vuln_count += len(vulns)

                for vuln in vulns:
                    if vuln.severity == VulnerabilitySeverity.CRITICAL:
                        critical_count += 1

                    if vulns:
                        impact = self._assess_impact(
                            dependency=dep,
                            vulnerability=vuln,
                            deployment_manifest=deployment_manifest,
                        )
                        impact_assessments.append(impact)

        # Check license compliance
        license_violations = 0
        compliance_status = {}

        if self.enable_license_check:
            license_check = self._check_licenses(dependencies)
            license_violations = license_check["violations"]
            compliance_status["license"] = license_check["compliant"]

        # Check hash integrity
        hash_mismatches = 0

        if self.enable_hash_verify and baseline_sbom:
            baseline = self._load_sbom(baseline_sbom)
            baseline_deps = self._parse_dependencies(baseline)
            hash_check = self._verify_hashes(dependencies, baseline_deps)
            hash_mismatches = hash_check["mismatches"]
            compliance_status["integrity"] = hash_check["verified"]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            vuln_count=vuln_count,
            critical_count=critical_count,
            license_violations=license_violations,
            hash_mismatches=hash_mismatches,
        )

        # Create report
        report = SBOMAnalysisReport(
            sbom_id=sbom.get("bom-id", sbom.get("SPDXID", "unknown")),
            analysis_timestamp=datetime.utcnow().isoformat(),
            total_dependencies=len(dependencies),
            transitive_dependencies=sum(len(deps) for deps in dependency_tree.values()),
            vulnerabilities_found=vuln_count,
            critical_vulnerabilities=critical_count,
            license_violations=license_violations,
            hash_mismatches=hash_mismatches,
            impact_assessments=impact_assessments,
            dependency_tree=dependency_tree,
            compliance_status=compliance_status,
            recommendations=recommendations,
        )

        logger.info(
            f"SBOM analysis complete: {vuln_count} vulnerabilities, "
            f"{critical_count} critical"
        )

        return report

    def _load_sbom(self, sbom_path: str) -> Dict[str, Any]:
        """Load SBOM from file (CycloneDX or SPDX)."""
        with open(sbom_path, "r") as f:
            data = json.load(f)

        # Detect format
        if "bomFormat" in data or "components" in data:
            # CycloneDX format
            logger.debug("Detected CycloneDX format")
            return data
        elif "SPDXID" in data or "spdxVersion" in data:
            # SPDX format
            logger.debug("Detected SPDX format")
            return data
        else:
            raise ValueError(f"Unknown SBOM format in {sbom_path}")

    def _parse_dependencies(self, sbom: Dict[str, Any]) -> List[Dependency]:
        """Parse dependencies from SBOM."""
        dependencies = []

        # CycloneDX format
        if "components" in sbom:
            for comp in sbom["components"]:
                dep = Dependency(
                    name=comp.get("name", ""),
                    version=comp.get("version", ""),
                    purl=comp.get("purl"),
                    type=comp.get("type", "library"),
                    licenses=self._extract_licenses(comp),
                    supplier=(
                        comp.get("supplier", {}).get("name")
                        if "supplier" in comp
                        else None
                    ),
                    download_location=(
                        comp.get("externalReferences", [{}])[0].get("url")
                        if comp.get("externalReferences")
                        else None
                    ),
                    hashes=self._extract_hashes(comp),
                    dependencies=[],  # Will fill later
                )
                dependencies.append(dep)

        # SPDX format
        elif "packages" in sbom:
            for pkg in sbom["packages"]:
                dep = Dependency(
                    name=pkg.get("name", ""),
                    version=pkg.get(
                        "versionInfo",
                        (
                            pkg.get("downloadLocation", "").split("@")[-1]
                            if pkg.get("downloadLocation")
                            else ""
                        ),
                    ),
                    purl=pkg.get(
                        "downloadLocation"
                    ),  # SPDX uses downloadLocation as purl
                    type="library",
                    licenses=self._extract_spdx_licenses(pkg),
                    supplier=pkg.get("supplier"),
                    download_location=pkg.get("downloadLocation"),
                    hashes={},  # SPDX format different
                    dependencies=[],
                )
                dependencies.append(dep)

        return dependencies

    def _extract_licenses(self, comp: Dict) -> List[str]:
        """Extract license information from CycloneDX component."""
        licenses = []

        if "licenses" in comp:
            for lic in comp["licenses"]:
                if "expression" in lic:
                    licenses.append(lic["expression"])
                elif "license" in lic:
                    licenses.append(lic["license"].get("id", ""))

        return licenses

    def _extract_spdx_licenses(self, pkg: Dict) -> List[str]:
        """Extract license information from SPDX package."""
        licenses = []

        if "licenseDeclared" in pkg:
            licenses.append(pkg["licenseDeclared"])

        if "licenseConcluded" in pkg:
            licenses.append(pkg["licenseConcluded"])

        return licenses

    def _extract_hashes(self, comp: Dict) -> Dict[str, str]:
        """Extract hash information from CycloneDX component."""
        hashes = {}

        if "hashes" in comp:
            for h in comp["hashes"]:
                alg = h.get("alg", "").lower()
                content = h.get("content", "")
                hashes[alg] = content

        return hashes

    def _build_dependency_tree(
        self, dependencies: List[Dependency]
    ) -> Dict[str, List[str]]:
        """Build dependency tree showing relationships."""
        tree = defaultdict(list)

        for dep in dependencies:
            # Map from dependency to its dependencies
            for child_dep in dep.dependencies:
                tree[dep.name + "@" + dep.version].append(child_dep)

        return dict(tree)

    def _check_vulnerabilities(self, dependency: Dependency) -> List[VulnerabilityInfo]:
        """Check for vulnerabilities in a dependency."""
        vulnerabilities = []

        # Query NVD (National Vulnerability Database)
        try:
            cves = self._query_nvd(dependency.name, dependency.version)
            vulnerabilities.extend(cves)
        except Exception as e:
            logger.warning(f"NVD query failed for {dependency.name}: {e}")

        # Query GitHub Security Advisories
        try:
            advisories = self._query_github_advisories(
                dependency.name, dependency.version
            )
            vulnerabilities.extend(advisories)
        except Exception as e:
            logger.warning(f"GitHub advisory query failed for {dependency.name}: {e}")

        # Query PyPI for Python packages
        if (
            dependency.type == "library"
            or dependency.purl
            and "pypi" in dependency.purl
        ):
            try:
                pysec = self._query_pypi(dependency.name, dependency.version)
                vulnerabilities.extend(pysec)
            except Exception as e:
                logger.warning(f"PyPI query failed for {dependency.name}: {e}")

        return vulnerabilities

    def _query_nvd(self, package_name: str, version: str) -> List[VulnerabilityInfo]:
        """Query NVD for CVEs affecting this package version."""
        vulnerabilities = []

        # Build CPE identifier
        cpe_string = f"cpe:2.3:a:{package_name}:{package_name}:{version}:*:*:*:*:*:*:*"

        try:
            # Search for CVEs
            params = {"cpeName": cpe_string, "resultsPerPage": 20}

            response = self.session.get(self.NVD_API_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "vulnerabilities" in data:
                for vuln_data in data["vulnerabilities"]:
                    cve = vuln_data["cve"]
                    metrics = vuln_data.get("metrics", [])

                    # Extract CVSS score
                    cvss_score = None
                    severity = VulnerabilitySeverity.UNKNOWN

                    for metric in metrics:
                        if "cvssMetricV31" in metric:
                            cvss_data = metric["cvssMetricV31"][0]["cvssData"]
                            cvss_score = cvss_data.get("baseScore")
                            severity_str = cvss_data.get("baseSeverity", "UNKNOWN")
                            severity = VulnerabilitySeverity(severity_str)
                        elif "cvssMetricV2" in metric:
                            cvss_data = metric["cvssMetricV2"][0]["cvssData"]
                            if not cvss_score:
                                cvss_score = cvss_data.get("baseScore")
                            severity_str = cvss_data.get("baseSeverity", "UNKNOWN")
                            if severity == VulnerabilitySeverity.UNKNOWN:
                                severity = VulnerabilitySeverity(severity_str)

                    vuln = VulnerabilityInfo(
                        cve_id=cve["id"],
                        severity=severity,
                        cvss_score=cvss_score,
                        description=cve.get("descriptions", [{}])[0].get("value", ""),
                        published_date=cve.get("published"),
                        modified_date=cve.get("lastModified"),
                    )
                    vulnerabilities.append(vuln)

        except Exception as e:
            logger.error(f"NVD query error: {e}")

        return vulnerabilities

    def _query_github_advisories(
        self, package_name: str, version: str
    ) -> List[VulnerabilityInfo]:
        """Query GitHub Security Advisories."""
        # This would require GitHub GraphQL API
        # Placeholder for now
        return []

    def _query_pypi(self, package_name: str, version: str) -> List[VulnerabilityInfo]:
        """Query PyPI for package vulnerabilities."""
        vulnerabilities = []

        try:
            response = self.session.get(
                f"https://pypi.org/pypi/{package_name}/json", timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Check for vulnerabilities in metadata
            vuln_data = data.get("vulnerabilities", [])

            for vuln in vuln_data:
                # Parse PyPI vulnerability format
                vulnerabilities.append(
                    VulnerabilityInfo(
                        cve_id=vuln.get("aliases", ["UNKNOWN"])[0],
                        severity=VulnerabilitySeverity(vuln.get("details", "UNKNOWN")),
                        cvss_score=None,
                        description=vuln.get("summary", vuln.get("details", "")),
                        affected_versions=vuln.get("affected_versions", []),
                        patched_versions=vuln.get("fixed_versions", []),
                    )
                )

        except Exception as e:
            logger.error(f"PyPI query error: {e}")

        return vulnerabilities

    def _assess_impact(
        self,
        dependency: Dependency,
        vulnerability: VulnerabilityInfo,
        deployment_manifest: Optional[str] = None,
    ) -> ImpactAssessment:
        """Assess the impact of a vulnerability."""
        # Determine affected services
        affected_services = []
        affected_environments = []

        if deployment_manifest:
            # Parse deployment manifest to find services using this dependency
            affected_services = self._find_affected_services(
                dependency, deployment_manifest
            )

        # Determine exploit availability
        exploit_available = self._check_exploit_available(vulnerability)

        # Check for patch
        has_patch = len(vulnerability.patched_versions) > 0

        # Determine recommendations
        recommendations = []
        if vulnerability.severity == VulnerabilitySeverity.CRITICAL:
            recommendations.append("🚨 CRITICAL: Immediate action required")
            recommendations.append("🚨 CRITICAL: Disable affected services")
            recommendations.append("🚨 CRITICAL: Apply patch immediately")

        if has_patch:
            recommendations.append(
                f"✅ Patch available: {vulnerability.patched_versions[0]}"
            )
            recommendations.append("🔄 Update to patched version")
        else:
            recommendations.append("⚠️  No patch available")
            recommendations.append("🛡️  Implement compensating controls")
            recommendations.append("🔍 Monitor for exploitation attempts")

        return ImpactAssessment(
            dependency=dependency,
            severity=vulnerability.severity,
            affected_services=affected_services,
            affected_environments=affected_environments,
            exploit_available=exploit_available,
            exploit_maturity="unknown",
            has_patch=has_patch,
            patch_version=vulnerability.patched_versions[0] if has_patch else None,
            cvss_score=vulnerability.cvss_score,
            attack_vector=None,
            recommendations=recommendations,
        )

    def _find_affected_services(
        self, dependency: Dependency, deployment_manifest: str
    ) -> List[str]:
        """Find services affected by a dependency."""
        # Placeholder implementation
        # In production, would parse K8s manifests, docker-compose, etc.
        return []

    def _check_exploit_available(self, vulnerability: VulnerabilityInfo) -> bool:
        """Check if exploit code is publicly available."""
        # This would integrate with exploit databases
        # Placeholder for now
        return False

    def _check_licenses(self, dependencies: List[Dependency]) -> Dict[str, Any]:
        """Check license compliance."""
        violations = 0
        compliant = True

        for dep in dependencies:
            for lic in dep.licenses:
                lic_normalized = self._normalize_license(lic)

                if lic_normalized in self.PROHIBITED_LICENSES:
                    violations += 1
                    logger.warning(f"Prohibited license found: {dep.name} - {lic}")
                    compliant = False

        return {"violations": violations, "compliant": compliant}

    def _normalize_license(self, license_str: str) -> str:
        """Normalize license string."""
        # Remove common variations
        license_str = license_str.upper()
        license_str = re.sub(r"\s+", "-", license_str)
        license_str = re.sub(r"^[-*]", "", license_str)
        license_str = license_str.split(" OR ")[0]  # Take first if multiple
        return license_str

    def _verify_hashes(
        self, current_deps: List[Dependency], baseline_deps: List[Dependency]
    ) -> Dict[str, Any]:
        """Verify hash integrity against baseline."""
        mismatches = 0
        verified = True

        baseline_map = {(d.name, d.version): d for d in baseline_deps}

        for dep in current_deps:
            key = (dep.name, dep.version)

            if key in baseline_map:
                baseline_dep = baseline_map[key]

                # Compare hashes
                for alg, hash_value in dep.hashes.items():
                    if baseline_dep.hashes.get(alg) != hash_value:
                        mismatches += 1
                        logger.error(
                            f"Hash mismatch for {dep.name}@{dep.version}: {alg}"
                        )
                        verified = False

        return {"mismatches": mismatches, "verified": verified}

    def _generate_recommendations(
        self,
        vuln_count: int,
        critical_count: int,
        license_violations: int,
        hash_mismatches: int,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if critical_count > 0:
            recommendations.append(
                f"🚨 {critical_count} CRITICAL vulnerabilities require immediate patching"
            )

        if vuln_count > 10:
            recommendations.append(
                f"⚠️  {vuln_count} total vulnerabilities found - prioritize patching"
            )

        if license_violations > 0:
            recommendations.append(
                f"📜 {license_violations} license violations require legal review"
            )

        if hash_mismatches > 0:
            recommendations.append(
                f"🔐 {hash_mismatches} hash mismatches indicate supply chain tampering"
            )

        if not any([critical_count, vuln_count, license_violations, hash_mismatches]):
            recommendations.append(
                "✅ No critical issues found - continue regular monitoring"
            )

        recommendations.append("📊 Generate SBOM for all builds")
        recommendations.append("🔍 Implement automated dependency scanning")
        recommendations.append("📧 Subscribe to vulnerability alerts for dependencies")

        return recommendations


# CLI interface
def main():
    """CLI for SBOM analysis."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze SBOM for security vulnerabilities"
    )
    parser.add_argument("--sbom", required=True, help="Path to SBOM file")
    parser.add_argument("--deployment", help="Path to deployment manifest")
    parser.add_argument("--baseline", help="Path to baseline SBOM")
    parser.add_argument("--output", help="Output path for report (JSON)")
    parser.add_argument("--nvd-key", help="NVD API key (for higher rate limits)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Run analysis
    analyzer = SBOMAnalyzer(nvd_api_key=args.nvd_key)
    report = analyzer.analyze_sbom(
        sbom_path=args.sbom,
        deployment_manifest=args.deployment,
        baseline_sbom=args.baseline,
    )

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report.to_json())
        print(f"Report saved to {args.output}")

        # Print summary
        print(f"\nSummary:")
        print(f"  Total Dependencies: {report.total_dependencies}")
        print(f"  Vulnerabilities: {report.vulnerabilities_found}")
        print(f"  Critical: {report.critical_vulnerabilities}")
        print(f"  License Violations: {report.license_violations}")
        print(f"  Hash Mismatches: {report.hash_mismatches}")
    else:
        print(report.to_json())


if __name__ == "__main__":
    main()
