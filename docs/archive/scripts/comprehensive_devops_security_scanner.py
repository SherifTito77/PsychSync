#!/usr/bin/env python3
"""
COMPREHENSIVE DEVOPS SECURITY SCANNER
Scans Docker, Kubernetes, and local infrastructure for security issues

Adapted for local development environments while maintaining production standards.

Tests:
1. Scan S3 bucket permissions → Local file storage permissions
2. Test for public files in production → Check for exposed sensitive files
3. Check Dockerfile security
4. Scan container image for known vulnerabilities
5. Test Kubernetes RBAC configs → Docker Compose/K8s config security

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


@dataclass
class SecurityIssue:
    """Security finding"""

    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: str = ""
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None


@dataclass
class ScanResult:
    """Result of a security scan"""

    scan_name: str
    status: str  # PASS, FAIL, WARN, SKIP
    score: int  # 0-100
    issues: List[SecurityIssue]
    details: Dict[str, Any]
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "scan_name": self.scan_name,
            "status": self.status,
            "score": self.score,
            "issue_count": len(self.issues),
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "title": i.title,
                    "description": i.description,
                    "file": i.file_path,
                    "line": i.line_number,
                    "remediation": i.remediation,
                    "cve_id": i.cve_id,
                    "cvss_score": i.cvss_score,
                }
                for i in self.issues
            ],
            "details": self.details,
            "duration_seconds": self.duration_seconds,
        }


class DevOpsSecurityScanner:
    """Comprehensive DevOps security scanner"""

    def __init__(self):
        self.project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        self.results: List[ScanResult] = []

        # Sensitive patterns for scanning
        self.secret_patterns = {
            "aws_access_key": r'AWS_ACCESS_KEY[_ID]?.*=\s*["\']?[A-Z0-9]{20}["\']?',
            "aws_secret": r'AWS_SECRET[_ACCESS]?_KEY.*=\s*["\']?[A-Za-z0-9/+=]{40}["\']?',
            "api_key": r'API[_-]?KEY.*=\s*["\']?[A-Za-z0-9/_-]{20,}["\']?',
            "password": r'PASSWORD.*=\s*["\'][^"\']{8,}["\']',
            "token": r'TOKEN.*=\s*["\'][A-Za-z0-9/_-]{20,}["\']',
            "secret": r'SECRET.*=\s*["\'][A-Za-z0-9/_-]{16,}["\']',
            "private_key": r"-----BEGIN[A-Z0-9 ]*PRIVATE KEY-----",
            "database_url": r"DATABASE_URL.*=.*://[^:]+:[^@]+@",
            "connection_string": r'CONNECTION[_]?STRING.*=.*["\'].*;.*Password',
        }

        # Known vulnerable base images (simplified)
        self.vulnerable_base_images = {
            "node:14-alpine": "Outdated Node.js 14 - EOL",
            "python:3.7": "Python 3.7 is EOL",
            "ubuntu:18.04": "Ubuntu 18.04 is EOL",
            "alpine:3.12": "Alpine 3.12 is outdated",
        }

    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}{title}{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}")

    def print_issue(self, issue: SecurityIssue):
        """Print formatted security issue"""
        colors = {
            "critical": RED,
            "high": RED,
            "medium": YELLOW,
            "low": BLUE,
            "info": BLUE,
        }
        color = colors.get(issue.severity, BLUE)
        emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🔵",
            "info": "ℹ️ ",
        }

        emoji_sym = emoji.get(issue.severity, "⚠️ ")
        print(f"\n{color}{emoji_sym} [{issue.severity.upper()}] {issue.title}{RESET}")
        print(f"   Category: {issue.category}")
        if issue.file_path:
            location = f"{issue.file_path}"
            if issue.line_number:
                location += f":{issue.line_number}"
            print(f"   Location: {location}")
        print(f"   Description: {issue.description}")
        if issue.remediation:
            print(f"   Remediation: {issue.remediation}")
        if issue.cve_id:
            print(f"   CVE: {issue.cve_id}")
        if issue.cvss_score:
            print(f"   CVSS Score: {issue.cvss_score}")

    def run_all_scans(self) -> Dict[str, Any]:
        """Run all DevOps security scans"""
        self.print_header("🔍 COMPREHENSIVE DEVOPS SECURITY SCANNER")
        print(f"Project Root: {self.project_root}")
        print(f"Started at: {datetime.now().isoformat()}")

        # Run all scans
        self.scan_local_storage_permissions()
        self.scan_public_file_exposures()
        self.scan_dockerfile_security()
        self.scan_container_images()
        self.scan_docker_compose_security()
        self.scan_environment_files()
        self.scan_hardcoded_secrets()

        # Generate summary
        return self.generate_summary_report()

    # ========== SCAN 1: Local Storage Permissions (S3 Equivalent) ==========

    def scan_local_storage_permissions(self):
        """Scan 1: Check local storage permissions (S3 bucket permissions equivalent)"""
        print(f"\n{YELLOW}📁 SCAN 1: Local Storage Permissions{RESET}")
        print(f"Checking: Upload directories, data directories, log files...")

        issues = []
        details = {"scanned_directories": []}

        directories_to_check = ["uploads", "data", "logs", "certs", ".env"]

        insecure_perms = []
        secure_perms = []

        for dir_name in directories_to_check:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                continue

            details["scanned_directories"].append(dir_name)

            # Check directory permissions
            stat_info = dir_path.stat()
            mode = oct(stat_info.st_mode)[-3:]

            # Check if world-writable (bad)
            if mode.endswith(("0", "1", "2")):  # Last digit has write bit
                issues.append(
                    SecurityIssue(
                        severity="high",
                        category="storage_permissions",
                        title=f"World-writable directory: {dir_name}",
                        description=f"Directory {dir_name} has permissions {mode} and is writable by others",
                        file_path=str(dir_path),
                        remediation=f"Run: chmod o-w {dir_name}",
                    )
                )
                insecure_perms.append(dir_name)
            else:
                secure_perms.append(dir_name)

            # Check files in directory
            if dir_path.is_dir():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            file_stat = file_path.stat()
                            file_mode = oct(file_stat.st_mode)[-3:]

                            # Check for sensitive files with loose permissions
                            if any(
                                s in file_path.name.lower()
                                for s in [
                                    "key",
                                    "secret",
                                    "password",
                                    "token",
                                    "credential",
                                ]
                            ):
                                if file_mode in ["644", "666", "755"]:
                                    issues.append(
                                        SecurityIssue(
                                            severity="medium",
                                            category="storage_permissions",
                                            title=f"Insecure permissions on sensitive file",
                                            description=f"File {file_path.name} appears to contain sensitive data but has permissions {file_mode}",
                                            file_path=str(file_path),
                                            remediation=f"Run: chmod 600 {file_path}",
                                        )
                                    )
                        except Exception as e:
                            pass

        details["secure_count"] = len(secure_perms)
        details["insecure_count"] = len(insecure_perms)

        score = max(0, 100 - len(issues) * 20)
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "WARN"

        result = ScanResult(
            scan_name="Local Storage Permissions",
            status=status,
            score=score,
            issues=issues,
            details=details,
        )
        self.results.append(result)

        for issue in issues:
            self.print_issue(issue)

        print(f"\n✅ Scanned {len(details['scanned_directories'])} directories")
        print(f"📊 Score: {score}/100")

    # ========== SCAN 2: Public File Exposures ==========

    def scan_public_file_exposures(self):
        """Scan 2: Check for files that would be publicly accessible in production"""
        print(f"\n{YELLOW}🌐 SCAN 2: Public File Exposures{RESET}")
        print(f"Checking for files that might be exposed in production...")

        issues = []

        # Files that should never be in web-accessible directories
        sensitive_patterns = {
            ".env": "Environment file with credentials",
            ".env.*": "Environment file",
            "*.key": "Private key file",
            "*.pem": "Certificate/key file",
            "id_rsa": "SSH private key",
            "*.p12": "PKCS12 certificate",
            "*.pfx": "PKCS12 certificate",
            "secrets.yaml": "Kubernetes secrets file",
            "secrets.yml": "Kubernetes secrets file",
            "credentials.json": "Google Cloud credentials",
            "*.backup": "Backup file may contain sensitive data",
        }

        # Check frontend public directory
        public_dirs = [
            self.project_root / "frontend" / "public",
            self.project_root / "public",
            self.project_root / "static",
            self.project_root / "www",
        ]

        found_sensitive = []

        for public_dir in public_dirs:
            if not public_dir.exists():
                continue

            for pattern, description in sensitive_patterns.items():
                # Handle glob patterns
                if "*" in pattern:
                    parts = pattern.split("*")
                    for file_path in public_dir.rglob(
                        f"*{parts[1]}" if len(parts) > 1 else parts[0]
                    ):
                        if (
                            file_path.is_file()
                            and file_path.name not in found_sensitive
                        ):
                            issues.append(
                                SecurityIssue(
                                    severity="critical",
                                    category="public_exposure",
                                    title=f"Sensitive file in public directory",
                                    description=f"{description} found in web-accessible directory: {file_path.name}",
                                    file_path=str(file_path),
                                    remediation="Move sensitive files outside of public directories or add to .gitignore",
                                )
                            )
                            found_sensitive.append(file_path.name)
                else:
                    file_path = public_dir / pattern
                    if file_path.exists():
                        issues.append(
                            SecurityIssue(
                                severity="critical",
                                category="public_exposure",
                                title=f"Sensitive file in public directory",
                                description=f"{description} found in web-accessible directory",
                                file_path=str(file_path),
                                remediation="Move sensitive files outside of public directories",
                            )
                        )
                        found_sensitive.append(pattern)

        # Check for .env files in project root (should be gitignored)
        env_files = list(self.project_root.glob(".env*"))
        env_files = [
            f for f in env_files if f.is_file() and "example" not in f.name.lower()
        ]

        details = {"env_files_found": len(env_files)}

        if env_files:
            # Check if they're in .gitignore
            gitignore = self.project_root / ".gitignore"
            if gitignore.exists():
                gitignore_content = gitignore.read_text()
                env_protected = ".env" in gitignore_content
            else:
                env_protected = False

            if not env_protected:
                issues.append(
                    SecurityIssue(
                        severity="high",
                        category="public_exposure",
                        title=".env files not protected",
                        description=f"Found {len(env_files)} .env files but .gitignore doesn't contain .env pattern",
                        file_path=(
                            str(self.project_root / ".gitignore")
                            if gitignore.exists()
                            else None
                        ),
                        remediation="Add '.env' and '.env.*' to .gitignore",
                    )
                )

        score = max(0, 100 - len(issues) * 25)
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "WARN"

        result = ScanResult(
            scan_name="Public File Exposures",
            status=status,
            score=score,
            issues=issues,
            details=details,
        )
        self.results.append(result)

        for issue in issues:
            self.print_issue(issue)

        print(f"\n📊 Score: {score}/100")

    # ========== SCAN 3: Dockerfile Security ==========

    def scan_dockerfile_security(self):
        """Scan 3: Check Dockerfile security best practices"""
        print(f"\n{YELLOW}🐳 SCAN 3: Dockerfile Security{RESET}")
        print(f"Checking Dockerfiles for security best practices...")

        issues = []
        dockerfiles = list(self.project_root.rglob("Dockerfile*"))

        details = {"dockerfiles_scanned": len(dockerfiles), "findings": []}

        for dockerfile_path in dockerfiles:
            if not dockerfile_path.is_file():
                continue

            try:
                content = dockerfile_path.read_text()
                lines = content.split("\n")

                # Check for security issues
                for i, line in enumerate(lines, 1):
                    # Check for ADD instead of COPY
                    if line.strip().startswith("ADD "):
                        issues.append(
                            SecurityIssue(
                                severity="medium",
                                category="dockerfile_security",
                                title="Use COPY instead of ADD",
                                description="ADD can extract remote files and should be avoided unless necessary",
                                file_path=str(dockerfile_path),
                                line_number=i,
                                remediation="Replace ADD with COPY for local files",
                            )
                        )

                    # Check for --insecure-flags
                    if "--insecure" in line.lower():
                        issues.append(
                            SecurityIssue(
                                severity="high",
                                category="dockerfile_security",
                                title="Insecure flag detected",
                                description="Docker build contains insecure flags",
                                file_path=str(dockerfile_path),
                                line_number=i,
                                remediation="Remove insecure flags and use proper certificate verification",
                            )
                        )

                    # Check for latest tag
                    if line.startswith("FROM") and ":latest" in line:
                        issues.append(
                            SecurityIssue(
                                severity="medium",
                                category="dockerfile_security",
                                title="Using 'latest' tag",
                                description="Using 'latest' tag can lead to unpredictable builds",
                                file_path=str(dockerfile_path),
                                line_number=i,
                                remediation="Pin specific version tags (e.g., 'FROM python:3.11-slim')",
                            )
                        )

                    # Check for running as root
                    if "USER " not in content and "user" not in content.lower():
                        issues.append(
                            SecurityIssue(
                                severity="high",
                                category="dockerfile_security",
                                title="Container runs as root",
                                description="Dockerfile doesn't set USER directive, container will run as root",
                                file_path=str(dockerfile_path),
                                remediation="Add 'USER nobody' or create non-root user",
                            )
                        )

                    # Check for vulnerable base images
                    for vuln_image, reason in self.vulnerable_base_images.items():
                        if vuln_image in line:
                            issues.append(
                                SecurityIssue(
                                    severity="high",
                                    category="dockerfile_security",
                                    title=f"Vulnerable base image: {vuln_image}",
                                    description=reason,
                                    file_path=str(dockerfile_path),
                                    line_number=i,
                                    remediation=f"Update to latest stable version",
                                )
                            )

                    # Check for secrets in Dockerfile
                    for secret_type, pattern in self.secret_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(
                                SecurityIssue(
                                    severity="critical",
                                    category="dockerfile_security",
                                    title=f"Secret in Dockerfile: {secret_type}",
                                    description="Dockerfile contains hardcoded secrets",
                                    file_path=str(dockerfile_path),
                                    line_number=i,
                                    remediation="Use build arguments or environment variables instead",
                                )
                            )

            except Exception as e:
                issues.append(
                    SecurityIssue(
                        severity="info",
                        category="dockerfile_security",
                        title=f"Could not read Dockerfile",
                        description=str(e),
                        file_path=str(dockerfile_path),
                    )
                )

        score = max(0, 100 - len(issues) * 15)
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "WARN"

        result = ScanResult(
            scan_name="Dockerfile Security",
            status=status,
            score=score,
            issues=issues,
            details=details,
        )
        self.results.append(result)

        for issue in issues:
            self.print_issue(issue)

        print(f"\n✅ Scanned {len(dockerfiles)} Dockerfiles")
        print(f"📊 Score: {score}/100")

    # ========== SCAN 4: Container Image Vulnerabilities ==========

    def scan_container_images(self):
        """Scan 4: Scan container images for known vulnerabilities"""
        print(f"\n{YELLOW}🔒 SCAN 4: Container Image Vulnerability Scan{RESET}")
        print(f"Checking for container image scanners...")

        issues = []
        details = {
            "trivy_available": False,
            "grype_available": False,
            "images_scanned": [],
        }

        # Check if Trivy is available
        trivy_available = False
        try:
            result = subprocess.run(
                ["trivy", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                trivy_available = True
                details["trivy_available"] = True
                print(f"   ✅ Trivy scanner found: {result.stdout.split()[1]}")
        except Exception as e:
            print(f"   ⚠️  Trivy not found (install: brew install trivy)")

        # Check if Grype is available
        grype_available = False
        try:
            result = subprocess.run(
                ["grype", "version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                grype_available = True
                details["grype_available"] = True
                print(f"   ✅ Grype scanner found")
        except Exception as e:
            print(f"   ⚠️  Grype not found (install: brew install grype)")

        if not trivy_available and not grype_available:
            print(f"\n   💡 Install a vulnerability scanner:")
            print(f"      brew install trivy")
            print(f"      # or")
            print(f"      brew install grype")

            issues.append(
                SecurityIssue(
                    severity="info",
                    category="container_scanning",
                    title="No vulnerability scanner installed",
                    description="Install Trivy or Grype to scan container images for CVEs",
                    remediation="brew install trivy",
                )
            )

            score = 50  # Neutral score if can't scan
            status = "WARN"
        else:
            # Actually run scan if scanner available
            if trivy_available:
                # Scan images referenced in docker-compose files
                print(f"\n   🔍 Scanning images with Trivy...")
                images = self._extract_images_from_compose()

                for image in images[:3]:  # Limit to first 3
                    print(f"      Scanning: {image}...")
                    try:
                        result = subprocess.run(
                            ["trivy", "image", "--format", "json", image],
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )

                        if result.stdout:
                            try:
                                scan_data = json.loads(result.stdout)
                                vulns = scan_data.get("Results", [])

                                for vuln_result in vulns:
                                    for vuln in vuln_result.get("Vulnerabilities", []):
                                        severity = vuln.get(
                                            "Severity", "Unknown"
                                        ).lower()
                                        if severity in ["critical", "high"]:
                                            issues.append(
                                                SecurityIssue(
                                                    severity=severity,
                                                    category="container_vulnerability",
                                                    title=f"Vulnerability in {image}",
                                                    description=vuln.get(
                                                        "Title",
                                                        "Security vulnerability",
                                                    ),
                                                    cve_id=vuln.get("VulnerabilityID"),
                                                    cvss_score=vuln.get("CVSS", {}).get(
                                                        "V3Score"
                                                    ),
                                                    remediation=f"Update base image or run: apk upgrade / apt-get update",
                                                )
                                            )
                                            break  # Only report highest severity per image
                            except json.JSONDecodeError:
                                pass

                        details["images_scanned"].append(image)
                    except subprocess.TimeoutExpired:
                        print(f"      ⏱️  Timeout scanning {image}")
                    except Exception as e:
                        print(f"      ❌ Error scanning {image}: {e}")

            # Calculate score
            critical_count = sum(1 for i in issues if i.severity == "critical")
            high_count = sum(1 for i in issues if i.severity == "high")

            score = max(0, 100 - (critical_count * 30) - (high_count * 15))
            status = "PASS" if score >= 80 else "FAIL" if score < 50 else "WARN"

        result = ScanResult(
            scan_name="Container Image Vulnerabilities",
            status=status,
            score=score,
            issues=issues,
            details=details,
        )
        self.results.append(result)

        for issue in issues[:10]:  # Limit output
            self.print_issue(issue)

        if len(issues) > 10:
            print(f"\n   ... and {len(issues) - 10} more issues")

        print(f"\n📊 Score: {score}/100")

    def _extract_images_from_compose(self) -> List[str]:
        """Extract Docker images from compose files"""
        images = set()

        compose_files = list(self.project_root.rglob("docker-compose*.yml"))
        for compose_file in compose_files:
            try:
                content = compose_file.read_text()
                # Find image: lines
                for line in content.split("\n"):
                    if line.strip().startswith("image:"):
                        image = line.split("image:")[1].strip().strip("\"'")
                        if image and not any(x in image for x in ["${", "LOCAL"]):
                            images.add(image)
            except Exception as e:
                pass

        return list(images)

    # ========== SCAN 5: Docker Compose/K8s Config Security ==========

    def scan_docker_compose_security(self):
        """Scan 5: Check Docker Compose/Kubernetes configuration security"""
        print(f"\n{YELLOW}☸️  SCAN 5: Container Orchestration Security{RESET}")
        print(f"Checking Docker Compose/Kubernetes configs...")

        issues = []

        # Check Docker Compose files
        compose_files = list(self.project_root.rglob("docker-compose*.yml"))
        compose_files.extend(list(self.project_root.rglob("docker-compose*.yaml")))

        details = {"compose_files": len(compose_files), "k8s_files": 0, "findings": []}

        for compose_file in compose_files:
            if not compose_file.is_file():
                continue

            try:
                content = compose_file.read_text()

                # Check for exposed ports
                if "ports:" in content:
                    for line in content.split("\n"):
                        if (
                            '- "' in line
                            or "- '" in line
                            or '- "' in line
                            or ":80:" in line
                        ):
                            # Check for port bindings
                            if ":80:" in line or ":443:" in line or ":8000:" in line:
                                issues.append(
                                    SecurityIssue(
                                        severity="medium",
                                        category="orchestration_security",
                                        title="Potentially exposed service port",
                                        description="Service port may be exposed to host",
                                        file_path=str(compose_file),
                                        remediation="Consider using internal-only networks or limit to localhost",
                                    )
                                )

                # Check for privileged mode
                if "privileged: true" in content:
                    issues.append(
                        SecurityIssue(
                            severity="critical",
                            category="orchestration_security",
                            title="Privileged mode enabled",
                            description="Container running with privileged mode has full host access",
                            file_path=str(compose_file),
                            remediation="Remove privileged: true unless absolutely necessary",
                        )
                    )

                # Check for volume mounts
                if "/:/host" in content or "volumes:" in content:
                    for i, line in enumerate(content.split("\n")):
                        if ":/" in line and (
                            ":/host" in line
                            or ":/root" in line
                            or ":/var/run/docker.sock" in line
                        ):
                            issues.append(
                                SecurityIssue(
                                    severity="high",
                                    category="orchestration_security",
                                    title="Sensitive host directory mounted",
                                    description="Container has access to sensitive host directories",
                                    file_path=str(compose_file),
                                    line_number=i + 1,
                                    remediation="Avoid mounting host directories unless necessary",
                                )
                            )

                # Check for environment variables with secrets
                for i, line in enumerate(content.split("\n")):
                    for secret_type, pattern in self.secret_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            issues.append(
                                SecurityIssue(
                                    severity="high",
                                    category="orchestration_security",
                                    title=f"Secret in compose file: {secret_type}",
                                    description="Compose file contains hardcoded secrets",
                                    file_path=str(compose_file),
                                    line_number=i + 1,
                                    remediation="Use .env file or Docker secrets instead",
                                )
                            )

            except Exception as e:
                pass

        # Check for Kubernetes files
        k8s_files = list(self.project_root.rglob("*.yaml"))
        k8s_files = [f for f in k8s_files if "k8s" in str(f) or "kube" in str(f)]

        details["k8s_files"] = len(k8s_files)

        for k8s_file in k8s_files:
            try:
                content = k8s_file.read_text()

                # Check for RBAC issues
                if "kind: ClusterRole" in content or "kind: Role" in content:
                    if "verbs:" in content and "*" in content:
                        issues.append(
                            SecurityIssue(
                                severity="high",
                                category="rbac_security",
                                title="Overly permissive RBAC verbs",
                                description="Role/ClusterRole has wildcard (*) verbs",
                                file_path=str(k8s_file),
                                remediation="Use specific verbs (get, list, create, etc.) instead of wildcard",
                            )
                        )

            except Exception as e:
                pass

        score = max(0, 100 - len(issues) * 15)
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "WARN"

        result = ScanResult(
            scan_name="Container Orchestration Security",
            status=status,
            score=score,
            issues=issues,
            details=details,
        )
        self.results.append(result)

        for issue in issues:
            self.print_issue(issue)

        print(
            f"\n✅ Scanned {len(compose_files)} compose files, {len(k8s_files)} K8s files"
        )
        print(f"📊 Score: {score}/100")

    # ========== SCAN 6: Environment Files Security ==========

    def scan_environment_files(self):
        """Scan 6: Check environment file security"""
        print(f"\n{YELLOW}🔐 SCAN 6: Environment File Security{RESET}")
        print(f"Checking .env files for security issues...")

        issues = []

        # Find all .env files
        env_files = []
        for env_file in self.project_root.rglob(".env*"):
            if env_file.is_file() and "example" not in env_file.name.lower():
                env_files.append(env_file)

        details = {"env_files_found": len(env_files), "files_with_issues": 0}

        for env_file in env_files:
            try:
                content = env_file.read_text()
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Check for hardcoded secrets
                    for secret_type, pattern in self.secret_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            # Check if it looks like a real value (not placeholder)
                            if not any(
                                placeholder in line.lower()
                                for placeholder in [
                                    "change",
                                    "example",
                                    "your-",
                                    "placeholder",
                                    "xxx",
                                    "localhost",
                                ]
                            ):

                                severity = (
                                    "critical"
                                    if secret_type in ["private_key", "aws_secret"]
                                    else "high"
                                )

                                issues.append(
                                    SecurityIssue(
                                        severity=severity,
                                        category="env_security",
                                        title=f"Potential secret in .env file: {secret_type}",
                                        description=f".env file may contain hardcoded secrets",
                                        file_path=str(env_file),
                                        line_number=i,
                                        remediation="Ensure .env is in .gitignore and never committed",
                                    )
                                )
                                break

            except Exception as e:
                pass

        # Check .gitignore
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            gitignore_content = gitignore.read_text()
            if ".env" not in gitignore_content:
                issues.append(
                    SecurityIssue(
                        severity="high",
                        category="env_security",
                        title=".env files not in .gitignore",
                        description="Environment files should be excluded from version control",
                        file_path=str(gitignore),
                        remediation="Add '.env' and '.env.*' to .gitignore",
                    )
                )

        details["files_with_issues"] = len(set(i.file_path for i in issues))

        score = max(0, 100 - len(issues) * 20)
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "WARN"

        result = ScanResult(
            scan_name="Environment File Security",
            status=status,
            score=score,
            issues=issues,
            details=details,
        )
        self.results.append(result)

        for issue in issues[:15]:
            self.print_issue(issue)

        if len(issues) > 15:
            print(f"\n   ... and {len(issues) - 15} more issues")

        print(f"\n✅ Scanned {len(env_files)} .env files")
        print(f"📊 Score: {score}/100")

    # ========== SCAN 7: Hardcoded Secrets Scan ==========

    def scan_hardcoded_secrets(self):
        """Scan 7: Deep scan for hardcoded secrets in code"""
        print(f"\n{YELLOW}🔑 SCAN 7: Hardcoded Secrets Detection{RESET}")
        print(f"Scanning codebase for hardcoded secrets...")

        issues = []

        # File extensions to scan
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".yaml",
            ".yml",
            ".json",
            ".sh",
            ".md",
        }

        # Files to skip
        skip_patterns = {
            "node_modules",
            ".git",
            "venv",
            "__pycache__",
            ".pytest_cache",
            "dist",
            "build",
            ".next",
            "coverage",
            ".backup",
        }

        scanned_files = 0
        max_files = 100  # Limit scan for performance

        for file_path in self.project_root.rglob("*"):
            if scanned_files >= max_files:
                break

            # Skip directories
            if any(skip in str(file_path) for skip in skip_patterns):
                continue

            # Only scan code files
            if file_path.suffix not in code_extensions:
                continue

            if not file_path.is_file():
                continue

            try:
                content = file_path.read_text()
                lines = content.split("\n")

                for i, line in enumerate(lines, 1):
                    for secret_type, pattern in self.secret_patterns.items():
                        if re.search(pattern, line, re.IGNORECASE):
                            # Filter out common false positives
                            if self._is_false_positive(line):
                                continue

                            issues.append(
                                SecurityIssue(
                                    severity="high",
                                    category="hardcoded_secrets",
                                    title=f"Potential hardcoded secret: {secret_type}",
                                    description=f"Code may contain hardcoded {secret_type}",
                                    file_path=str(
                                        file_path.relative_to(self.project_root)
                                    ),
                                    line_number=i,
                                    remediation="Move secrets to environment variables or secret management system",
                                )
                            )
                            break  # Only report one issue per line

                scanned_files += 1

            except Exception as e:
                pass

        details = {"files_scanned": scanned_files}

        score = max(0, 100 - len(issues) * 10)
        status = "PASS" if score >= 80 else "FAIL" if score < 50 else "WARN"

        result = ScanResult(
            scan_name="Hardcoded Secrets Detection",
            status=status,
            score=score,
            issues=issues,
            details=details,
        )
        self.results.append(result)

        for issue in issues[:20]:
            self.print_issue(issue)

        if len(issues) > 20:
            print(f"\n   ... and {len(issues) - 20} more issues")

        print(f"\n✅ Scanned {scanned_files} files")
        print(f"📊 Score: {score}/100")

    def _is_false_positive(self, line: str) -> bool:
        """Check if line is a false positive"""
        false_positive_indicators = [
            "# TODO",
            "# FIXME",
            "# example",
            "# sample",
            "placeholder",
            "your-",
            "change-me",
            "xxx",
            "<",
            ">",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            '"',
            "'",  # Empty strings
        ]

        line_lower = line.lower()
        return any(indicator in line_lower for indicator in false_positive_indicators)

    # ========== SUMMARY REPORT ==========

    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        self.print_header("📋 SCAN SUMMARY REPORT")

        # Calculate totals
        total_score = sum(r.score for r in self.results)
        avg_score = total_score / len(self.results) if self.results else 0

        critical_count = sum(
            len([i for i in r.issues if i.severity == "critical"]) for r in self.results
        )
        high_count = sum(
            len([i for i in r.issues if i.severity == "high"]) for r in self.results
        )
        medium_count = sum(
            len([i for i in r.issues if i.severity == "medium"]) for r in self.results
        )
        low_count = sum(
            len([i for i in r.issues if i.severity == "low"]) for r in self.results
        )

        passed = sum(1 for r in self.results if r.status == "PASS")
        warned = sum(1 for r in self.results if r.status == "WARN")
        failed = sum(1 for r in self.results if r.status == "FAIL")

        # Print summary
        print(f"\nTotal Scans: {len(self.results)}")
        print(f"Passed: {passed} ✅")
        print(f"Warnings: {warned} ⚠️")
        print(f"Failed: {failed} ❌")
        print(f"\n{CYAN}Overall Security Score: {avg_score:.1f}/100{RESET}")

        # Severity breakdown
        print(f"\n🔴 Critical Issues: {critical_count}")
        print(f"🟠 High Issues: {high_count}")
        print(f"🟡 Medium Issues: {medium_count}")
        print(f"🔵 Low Issues: {low_count}")

        # Overall status
        if avg_score >= 80:
            overall_status = "SECURE ✅"
            status_color = GREEN
        elif avg_score >= 60:
            overall_status = "ADEQUATE ⚠️"
            status_color = YELLOW
        else:
            overall_status = "NEEDS IMPROVEMENT ❌"
            status_color = RED

        print(f"\n{status_color}Overall Status: {overall_status}{RESET}")
        print(f"Completed at: {datetime.now().isoformat()}")

        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": round(avg_score, 2),
            "overall_status": overall_status,
            "scan_results": [r.to_dict() for r in self.results],
            "summary": {
                "total_scans": len(self.results),
                "passed": passed,
                "warnings": warned,
                "failed": failed,
                "critical_issues": critical_count,
                "high_issues": high_count,
                "medium_issues": medium_count,
                "low_issues": low_count,
            },
        }

        report_file = self.project_root / "devops_security_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file.name}")

        return report


def main():
    """Main entry point"""
    scanner = DevOpsSecurityScanner()
    report = scanner.run_all_scans()

    # Exit with error if security is poor
    avg_score = report["overall_score"]
    if avg_score < 60:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
