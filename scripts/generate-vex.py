#!/usr/bin/env python3
"""
VEX (Vulnerability Exploitability Exchange) Generator

Generates VEX documents analyzing vulnerability exploitability in the context
of PsychSync's specific deployment and usage patterns.

OpenVEX Format: https://github.com/openvex/vex
CSAF VEX Format: https://www.oasis-open.org/committees/tc-home.php?wg_abbrev=csaf

Compliance:
- NIST SSDF PW.3.1: Monitor for vulnerabilities
- CISA SBOM guidance: Include VEX with SBOM
- Executive Order 14028: SBOM + VEX for critical software

Author: Security Team
Version: 1.0
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import re

logger = logging.getLogger(__name__)


class VEXStatus(Enum):
    """VEX analysis statuses per OpenVEX spec"""
    NOT_AFFECTED = "not_affected"
    AFFECTED = "affected"
    FIXED = "fixed"
    UNDER_INVESTIGATION = "under_investigation"


class NotAffectedReason(Enum):
    """Reasons why a vulnerability doesn't affect us"""
    COMPONENT_NOT_PRESENT = "component_not_present"
    VULNERABLE_CODE_NOT_PRESENT = "vulnerable_code_not_present"
    VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY = "vulnerable_code_cannot_be_controlled_by_adversary"
    VULNERABLE_CODE_NOT_IN_EXECUTE_PATH = "vulnerable_code_not_in_execute_path"
    INCOMPATIBLE_CONFIGURATION = "incompatible_configuration"
    PROTECTED_BY_COMPILER_OR_RUNTIME_MITIGATION = "protected_by_compiler_or_runtime_mitigation"
    PROTECTED_BY_AN_ENVIRONMENTAL_MITIGATION = "protected_by_an_environmental_mitigation"
    PROTECTED_BY_APPLICATION_SPECIFIC_MITIGATION = "protected_by_application_specific_mitigation"


@dataclass
class VEXStatement:
    """Single VEX statement about a vulnerability"""
    vulnerability_id: str  # CVE ID
    status: VEXStatus
    status_notes: str
    not_affected_reason: Optional[NotAffectedReason] = None
    affected_versions: Optional[List[str]] = None
    fixed_versions: Optional[List[str]] = None
    remediation: Optional[str] = None
    impact_statement: Optional[str] = None


class VEXAnalyzer:
    """
    Analyzes vulnerabilities and generates VEX statements
    """

    def __init__(self):
        """Initialize VEX analyzer"""
        self.psychsync_specific_context = {
            # Deployment context
            "deployment": "containerized_docker",
            "runtime": "python_3.11",
            "database": "postgresql_15",
            "exposed_to_internet": True,
            "handles_pii": True,
            "authentication_required": True,

            # Mitigations we have in place
            "mitigations": [
                "input_validation",
                "output_encoding",
                "prepared_statements",
                "csrf_protection",
                "rate_limiting",
                "authentication_required",
                "authorization_checks",
                "encryption_at_rest",
                "encryption_in_transit",
                "rbac_abac"
            ]
        }

    def analyze_vulnerability(
        self,
        cve_id: str,
        package_name: str,
        installed_version: str,
        vulnerable_versions: List[str],
        description: str,
        cvss_score: Optional[float] = None,
        cwe_id: Optional[str] = None
    ) -> VEXStatement:
        """
        Analyze a vulnerability in the context of PsychSync

        Args:
            cve_id: CVE identifier (e.g., CVE-2023-1234)
            package_name: Package name
            installed_version: Version we have installed
            vulnerable_versions: List of vulnerable version ranges
            description: Vulnerability description
            cvss_score: CVSS score if available
            cwe_id: CWE identifier if available

        Returns:
            VEXStatement with analysis
        """
        logger.info(f"Analyzing {cve_id} for {package_name} {installed_version}")

        # Check if version is in vulnerable range
        is_vulnerable_version = self._is_version_vulnerable(
            installed_version,
            vulnerable_versions
        )

        # Determine status based on context
        if not is_vulnerable_version:
            return VEXStatement(
                vulnerability_id=cve_id,
                status=VEXStatus.NOT_AFFECTED,
                status_notes=f"Installed version {installed_version} is not in vulnerable range {vulnerable_versions}",
                not_affected_reason=NotAffectedReason.COMPONENT_NOT_PRESENT
            )

        # Check for environmental mitigations
        mitigation = self._check_mitigations(cwe_id, description, cvss_score)

        if mitigation:
            return VEXStatement(
                vulnerability_id=cve_id,
                status=VEXStatus.NOT_AFFECTED,
                status_notes=f"Vulnerable version present but mitigated: {mitigation}",
                not_affected_reason=NotAffectedReason.PROTECTED_BY_APPLICATION_SPECIFIC_MITIGATION,
                affected_versions=vulnerable_versions,
                remediation="Continue monitoring and update when available"
            )

        # Check if vulnerable code is in execution path
        execution_path = self._check_execution_path(package_name, description)

        if not execution_path:
            return VEXStatement(
                vulnerability_id=cve_id,
                status=VEXStatus.NOT_AFFECTED,
                status_notes=f"Vulnerable code not in execution path for PsychSync usage",
                not_affected_reason=NotAffectedReason.VULNERABLE_CODE_NOT_IN_EXECUTE_PATH,
                affected_versions=vulnerable_versions,
                remediation="Update when convenient"
            )

        # If we get here, we're affected
        impact = self._assess_impact(cvss_score, cwe_id, description)

        return VEXStatement(
            vulnerability_id=cve_id,
            status=VEXStatus.AFFECTED,
            status_notes=f"Vulnerable version {installed_version} is affected. {impact}",
            affected_versions=vulnerable_versions,
            impact_statement=impact,
            remediation=f"Update {package_name} to latest secure version"
        )

    def _is_version_vulnerable(
        self,
        installed_version: str,
        vulnerable_versions: List[str]
    ) -> bool:
        """
        Check if installed version is in vulnerable range

        Simplified version comparison - in production use packaging.version
        """
        for vuln_range in vulnerable_versions:
            # Simple contains check for now
            if installed_version in vuln_range:
                return True

        return False

    def _check_mitigations(
        self,
        cwe_id: Optional[str],
        description: str,
        cvss_score: Optional[float]
    ) -> Optional[str]:
        """
        Check if we have mitigations in place

        Returns mitigation description if mitigated, None if not
        """
        desc_lower = description.lower()

        # SQL Injection mitigations
        if cwe_id == "CWE-89" or "sql injection" in desc_lower:
            if "prepared_statements" in self.psychsync_specific_context["mitigations"]:
                return "All database queries use SQLAlchemy with prepared statements"

        # XSS mitigations
        if cwe_id == "CWE-79" or "cross-site scripting" in desc_lower:
            if "output_encoding" in self.psychsync_specific_context["mitigations"]:
                return "React framework provides automatic output encoding"

        # CSRF mitigations
        if cwe_id == "CWE-352" or "csrf" in desc_lower:
            if "csrf_protection" in self.psychsync_specific_context["mitigations"]:
                return "FastAPI CSRF middleware enabled on all mutation endpoints"

        # Authentication bypass
        if "authentication" in desc_lower or "auth bypass" in desc_lower:
            if "authentication_required" in self.psychsync_specific_context["mitigations"]:
                return "Multi-layer authentication (JWT + MFA) required for all endpoints"

        # Authorization bypass
        if "authorization" in desc_lower or "access control" in desc_lower:
            if "authorization_checks" in self.psychsync_specific_context["mitigations"]:
                return "RBAC + ABAC layered authorization on all endpoints"

        return None

    def _check_execution_path(self, package_name: str, description: str) -> bool:
        """
        Check if vulnerable code is in our execution path
        """
        # Critical packages always in execution path
        critical_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "pydantic",
            "python-jose", "passlib", "bcrypt"
        ]

        if package_name in critical_packages:
            return True

        # Check description for execution context clues
        desc_lower = description.lower()

        # If only affects CLI, not in our web execution path
        if "cli" in desc_lower and "web" not in desc_lower:
            return False

        # If only affects specific features we don't use
        if "websocket" in desc_lower and package_name not in ["fastapi", "uvicorn"]:
            return False

        # Default to True (conservative)
        return True

    def _assess_impact(
        self,
        cvss_score: Optional[float],
        cwe_id: Optional[str],
        description: str
    ) -> str:
        """Assess impact of vulnerability"""
        if cvss_score:
            if cvss_score >= 9.0:
                return "CRITICAL: Exploitation would lead to complete system compromise"
            elif cvss_score >= 7.0:
                return "HIGH: Exploitation could lead to data exposure or unauthorized access"
            elif cvss_score >= 4.0:
                return "MEDIUM: Exploitation has limited impact"
            else:
                return "LOW: Minimal impact expected"

        # Fallback to CWE-based assessment
        if cwe_id:
            critical_cwes = ["CWE-79", "CWE-89", "CWE-120", "CWE-125", "CWE-190"]
            if cwe_id in critical_cwes:
                return "HIGH impact based on CWE category"

        return "Impact assessment pending detailed analysis"

    def analyze_sbom_vulnerabilities(self, sbom_data: Dict) -> List[VEXStatement]:
        """
        Analyze all vulnerabilities in an SBOM

        Args:
            sbom_data: CycloneDX SBOM data

        Returns:
            List of VEX statements
        """
        statements = []

        # Extract components from SBOM
        components = sbom_data.get("components", [])

        for component in components:
            vulns = component.get("vulnerabilities", [])

            for vuln in vulns:
                cve_id = vuln.get("id", "UNKNOWN")
                description = vuln.get("description", "")
                ratings = vuln.get("ratings", [])
                cvss_score = None

                for rating in ratings:
                    if "score" in rating:
                        cvss_score = rating["score"]
                        break

                # Get affected versions
                affected = []
                for affect in vuln.get("affects", []):
                    affected.append(affect.get("version", ""))

                statement = self.analyze_vulnerability(
                    cve_id=cve_id,
                    package_name=component.get("name", ""),
                    installed_version=component.get("version", ""),
                    vulnerable_versions=affected,
                    description=description,
                    cvss_score=cvss_score
                )

                statements.append(statement)

        return statements


class VEXGenerator:
    """Generate VEX documents in OpenVEX format"""

    def __init__(self):
        """Initialize VEX generator"""
        self.analyzer = VEXAnalyzer()

    def generate_openvex(
        self,
        statements: List[VEXStatement],
        product_id: str = "psychsync",
        product_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        Generate OpenVEX document

        Format: https://github.com/openvex/vex
        """
        now = datetime.now(timezone.utc).isoformat()

        vex_doc = {
            "@context": [
                "https://openvex.dev/ns/vex"
            ],
            "id": f"{product_id}-vex-{int(datetime.now().timestamp())}",
            "author": "PsychSync Security Team <security@psychsync.com>",
            "timestamp": now,
            "version": "1",
            "statements": []
        }

        for statement in statements:
            vex_statement = {
                "vulnerability": statement.vulnerability_id,
                "timestamp": now,
                "products": [
                    {
                        "product": product_id,
                        "subcomponents": [
                            {
                                "id": f"{product_id}-{product_version}"
                            }
                        ]
                    }
                ]
            }

            # Add status-specific fields
            if statement.status == VEXStatus.NOT_AFFECTED:
                vex_statement["status"] = "not_affected"
                if statement.not_affected_reason:
                    vex_statement["justification"] = statement.not_affected_reason.value
                vex_statement["impact_statement"] = statement.status_notes

            elif statement.status == VEXStatus.AFFECTED:
                vex_statement["status"] = "affected"
                vex_statement["impact_statement"] = statement.impact_statement or statement.status_notes
                if statement.remediation:
                    vex_statement["action_statement"] = statement.remediation

            elif statement.status == VEXStatus.FIXED:
                vex_statement["status"] = "fixed"
                if statement.fixed_versions:
                    vex_statement["action_statement"] = f"Update to version: {', '.join(statement.fixed_versions)}"

            elif statement.status == VEXStatus.UNDER_INVESTIGATION:
                vex_statement["status"] = "under_investigation"
                vex_statement["status_notes"] = statement.status_notes

            vex_doc["statements"].append(vex_statement)

        return vex_doc

    def generate_csaf_vex(
        self,
        statements: List[VEXStatement],
        product_id: str = "psychsync",
        product_version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        Generate CSAF VEX document

        Format: https://www.oasis-open.org/committees/tc-home.php?wg_abbrev=csaf
        """
        now = datetime.now(timezone.utc).isoformat()

        csaf_doc = {
            "document": {
                "category": "vex",
                "csaf_version": "2.0",
                "title": f"VEX Analysis for {product_id} {product_version}",
                "publisher": {
                    "category": "vendor",
                    "name": "PsychSync",
                    "contact_details": "security@psychsync.com"
                },
                "tracking": {
                    "id": f"{product_id}-vex-{int(datetime.now().timestamp())}",
                    "current_release_date": now,
                    "initial_release_date": now,
                    "revision_history": [],
                    "status": "final",
                    "version": "1"
                }
            },
            "vulnerabilities": []
        }

        for statement in statements:
            vuln = {
                "CVE": statement.vulnerability_id,
                "product_status": {
                    "known_affected": [],
                    "known_not_affected": [],
                    "under_investigation": [],
                    "fixed": []
                },
                "threats": []
            }

            # Add product status
            if statement.status == VEXStatus.AFFECTED:
                vuln["product_status"]["known_affected"].append(f"{product_id}@{product_version}")

                if statement.impact_statement:
                    vuln["threats"].append({
                        "category": "impact",
                        "details": statement.impact_statement
                    })

                if statement.remediation:
                    vuln["threats"].append({
                        "category": "remediation",
                        "details": statement.remediation
                    })

            elif statement.status == VEXStatus.NOT_AFFECTED:
                vuln["product_status"]["known_not_affected"].append(f"{product_id}@{product_version}")

                if statement.not_affected_reason:
                    vuln["threats"].append({
                        "category": "impact",
                        "details": f"Justification: {statement.not_affected_reason.value}. {statement.status_notes}"
                    })

            elif statement.status == VEXStatus.UNDER_INVESTIGATION:
                vuln["product_status"]["under_investigation"].append(f"{product_id}@{product_version}")

            elif statement.status == VEXStatus.FIXED:
                vuln["product_status"]["fixed"].append(f"{product_id}@{product_version}")

                if statement.fixed_versions:
                    vuln["threats"].append({
                        "category": "remediation",
                        "details": f"Update to: {', '.join(statement.fixed_versions)}"
                    })

            csaf_doc["vulnerabilities"].append(vuln)

        return csaf_doc


def main():
    """CLI interface for VEX generation"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate VEX documents")
    parser.add_argument("--sbom", required=True, help="Path to SBOM JSON file")
    parser.add_argument("--output", required=True, help="Output VEX file")
    parser.add_argument("--format", default="openvex", choices=["openvex", "csaf"], help="VEX format")
    parser.add_argument("--product", default="psychsync", help="Product identifier")
    parser.add_argument("--version", default="1.0.0", help="Product version")

    args = parser.parse_args()

    # Load SBOM
    try:
        with open(args.sbOM, 'r') as f:
            sbom_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load SBOM: {e}")
        sys.exit(1)

    # Analyze vulnerabilities
    generator = VEXGenerator()
    statements = generator.analyzer.analyze_sbom_vulnerabilities(sbom_data)

    # Generate VEX
    if args.format == "openvex":
        vex_doc = generator.generate_openvex(statements, args.product, args.version)
    else:
        vex_doc = generator.generate_csaf_vex(statements, args.product, args.version)

    # Write output
    with open(args.output, 'w') as f:
        json.dump(vex_doc, f, indent=2)

    logger.info(f"Generated VEX document with {len(statements)} statements: {args.output}")

    # Print summary
    print(f"\nVEX Analysis Summary:")
    print(f"  Total statements: {len(statements)}")
    status_counts = {}
    for stmt in statements:
        status_counts[stmt.status.value] = status_counts.get(stmt.status.value, 0) + 1
    for status, count in status_counts.items():
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
