#!/usr/bin/env python3
"""
COMPREHENSIVE FILE SYSTEM & STORAGE SECURITY TESTING SUITE
Tests file system security for unauthorized access and data exposure

Author: Security Team
Version: 1.0
Date: December 23, 2024

Tests:
1. Directory traversal vulnerabilities
2. Publicly accessible temp directories
3. Leftover deployment artifacts
4. .env file exposure
5. Logs containing API keys/secrets
"""

import os
import sys
import re
import json
import ast
import time
import hashlib
import secrets
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import mimetypes

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

project_root = Path(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class SecurityIssue:
    """Represents a security issue found during testing"""
    category: str
    severity: str  # critical, high, medium, low
    title: str
    description: str
    location: str
    evidence: str = ""
    remediation: str = ""
    cvss_score: float = 0.0


@dataclass
class TestResult:
    """Represents the result of a security test"""
    test_name: str
    passed: bool
    score: float  # 0-100
    issues: List[SecurityIssue] = field(default_factory=list)
    details: str = ""


class FilesystemSecurityTester:
    """Comprehensive file system security testing suite"""

    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.test_results: List[TestResult] = []
        self.start_time = datetime.now()

    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}{title}{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}\n")

    def print_test_header(self, test_name: str):
        """Print test section header"""
        print(f"\n{MAGENTA}🔍 {test_name}{RESET}")
        print(f"{MAGENTA}{'-' * 80}{RESET}")

    # =========================================================================
    # TEST 1: Directory Traversal Vulnerabilities
    # =========================================================================

    async def test_directory_traversal(self) -> TestResult:
        """Test for directory traversal vulnerabilities in API endpoints"""
        self.print_test_header("TEST 1: Directory Traversal Vulnerabilities")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning API endpoints for path traversal protection...{RESET}")

        # Scan API endpoint files for path handling
        api_endpoints = list((project_root / "app/api/v1/endpoints").rglob("*.py"))

        vulnerable_patterns = []
        safe_patterns = []

        for endpoint_file in api_endpoints:
            try:
                content = endpoint_file.read_text()
                filename = endpoint_file.relative_to(project_root)

                # Check for file operations
                file_operations = [
                    (r'open\(', 'Direct open() call'),
                    (r'Path\(', 'Path() construction'),
                    (r'Path\.open\(', 'Path.open() call'),
                    (r'os\.path\.join', 'os.path.join()'),
                    (r'read_text\(\)', 'read_text() call'),
                    (r'read_bytes\(\)', 'read_bytes() call'),
                ]

                for pattern, desc in file_operations:
                    if pattern in content:
                        # Check if there's validation
                        function_code = self._extract_function_with_pattern(content, pattern)

                        if function_code:
                            # Check for path validation
                            has_validation = self._check_path_validation(function_code)

                            if not has_validation:
                                vulnerable_patterns.append((filename, desc, pattern))
                                details.append(f"{RED}⚠️  {desc} in {filename} (no validation detected){RESET}")
                            else:
                                safe_patterns.append((filename, desc))

            except Exception as e:
                details.append(f"{YELLOW}⚠️  Error scanning {endpoint_file.name}: {e}{RESET}")

        # Check for common traversal payloads in code
        print(f"\n{BLUE}Checking for hardcoded file paths...{RESET}")

        risky_paths = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e',
            r'..%2f',
            r'..%5c',
            r'/etc/passwd',
            r'C:\\Windows',
        ]

        for py_file in project_root.rglob("*.py"):
            if "test" in str(py_file).lower():
                continue  # Skip test files

            try:
                content = py_file.read_text()
                for risky in risky_paths:
                    if risky in content:
                        # Check if it's in a comment or string literal
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if risky in line:
                                # Check if it's a comment
                                if line.strip().startswith('#'):
                                    continue
                                vulnerable_patterns.append((py_file.relative_to(project_root), f"Risky path: {risky}", risky))
                                details.append(f"{YELLOW}⚠️  Risky path in {py_file.name}:{i} - {risky}{RESET}")
            except Exception:
                pass

        # Check for static file serving configuration
        print(f"\n{BLUE}Checking static file serving configuration...{RESET}")

        static_configs = [
            "app/main.py",
            "app/__init__.py",
            "vite.config.ts",
            "nginx.conf",
            "nginx/nginx.conf"
        ]

        for config_file in static_configs:
            config_path = project_root / config_file
            if config_path.exists():
                content = config_path.read_text()

                # Check for static file mounting
                if "StaticFiles" in content or "static" in content.lower():
                    # Check if it's properly configured
                    if "/static" in content or "staticfiles" in content.lower():
                        details.append(f"{GREEN}✅ Static files configured in {config_file}{RESET}")
                    else:
                        # Check for root mounting
                        if '"/"' in content or 'path="/"' in content:
                            vulnerable_patterns.append((config_file, "Root static file mounting", '"/"'))
                            details.append(f"{RED}❌ CRITICAL: Root static mounting in {config_file}{RESET}")
                            score -= 30

        # Check for file upload endpoints
        print(f"\n{BLUE}Checking file upload endpoints...{RESET}")

        upload_endpoints = []
        for endpoint_file in api_endpoints:
            try:
                content = endpoint_file.read_text()
                if "upload" in content.lower() and "file" in content.lower():
                    # Check for filename sanitization
                    if "safe_filename" not in content.lower() and "sanitize" not in content.lower():
                        upload_endpoints.append((endpoint_file.name, "No filename sanitization"))
                        details.append(f"{YELLOW}⚠️  Upload endpoint without filename sanitization: {endpoint_file.name}{RESET}")
                        score -= 15
                    else:
                        details.append(f"{GREEN}✅ Upload endpoint has sanitization: {endpoint_file.name}{RESET}")
            except Exception:
                pass

        # Calculate final score
        if vulnerable_patterns:
            severity_reduction = min(len(vulnerable_patterns) * 10, 70)
            score -= severity_reduction
            score = max(score, 0)

            issues.append(SecurityIssue(
                category="directory_traversal",
                severity="critical" if score < 50 else "high",
                title=f"Directory Traversal Vulnerabilities Found ({len(vulnerable_patterns)})",
                description=f"Found {len(vulnerable_patterns)} potential directory traversal vulnerabilities",
                location="app/api/v1/endpoints/",
                remediation="Add path validation:\n"
                          "- Use pathlib.Path.resolve() to normalize paths\n"
                          "- Verify resolved path is within allowed directory\n"
                          "- Reject paths containing .. or absolute paths\n"
                          "- Use whitelist of allowed file extensions\n"
                          "- Never use user input directly in file paths",
                cvss_score=7.5 if score < 50 else 5.5
            ))
        else:
            details.append(f"{GREEN}✅ No directory traversal vulnerabilities detected{RESET}")

        # Output results
        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details[:20]:  # Limit output
            print(f"   {detail}")

        if len(details) > 20:
            print(f"   ... and {len(details) - 20} more")

        print(f"\n{CYAN}Score: {score:.1f}/100{RESET}")

        return TestResult(
            test_name="Directory Traversal Protection",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    def _extract_function_with_pattern(self, content: str, pattern: str) -> Optional[str]:
        """Extract function code containing a pattern"""
        lines = content.split('\n')
        pattern_line = None

        for i, line in enumerate(lines):
            if pattern in line:
                pattern_line = i
                break

        if pattern_line is None:
            return None

        # Find function start
        func_start = pattern_line
        for i in range(pattern_line, max(0, pattern_line - 50), -1):
            if lines[i].strip().startswith('def ') or lines[i].strip().startswith('async def '):
                func_start = i
                break

        # Find function end
        func_end = pattern_line + 50
        for i in range(pattern_line, min(len(lines), pattern_line + 50)):
            if lines[i].strip().startswith('def ') or lines[i].strip().startswith('async def '):
                if i != pattern_line:
                    func_end = i
                    break

        return '\n'.join(lines[func_start:func_end])

    def _check_path_validation(self, code: str) -> bool:
        """Check if code has path validation"""
        validation_patterns = [
            r'resolve\(\)',
            r'sanitize',
            r'safe_filename',
            r'\.exists\(\)',
            r'is_absolute\(\)',
            r'\.\./',
            r'path\.startswith',
            r'allowed_path',
            r'whitelist',
        ]

        for pattern in validation_patterns:
            if re.search(pattern, code):
                return True

        return False

    # =========================================================================
    # TEST 2: Publicly Accessible Temp Directories
    # =========================================================================

    async def test_temp_directories(self) -> TestResult:
        """Test for publicly accessible temp directories"""
        self.print_test_header("TEST 2: Publicly Accessible Temp Directories")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning for temporary directories...{RESET}")

        # Common temp directory locations
        temp_dirs = [
            "/tmp",
            "/var/tmp",
            "temp",
            "tmp",
            "uploads",
            "cache",
            ".cache",
            "uploads/tmp",
        ]

        exposed_temp_dirs = []

        # Check if temp directories exist and are accessible
        for temp_dir in temp_dirs:
            temp_path = project_root / temp_dir
            if temp_path.exists():
                # Check if it's in web-accessible location
                if self._is_web_accessible(temp_path):
                    exposed_temp_dirs.append(temp_path)
                    details.append(f"{RED}❌ CRITICAL: Web-accessible temp directory: {temp_dir}{RESET}")
                    score -= 25
                else:
                    details.append(f"{GREEN}✅ Temp directory not web-accessible: {temp_dir}{RESET}")

        # Check for uploaded files in public directories
        print(f"\n{BLUE}Checking for uploaded files in public directories...{RESET}")

        public_dirs = [
            "frontend/public",
            "frontend/dist",
            "static",
            "media",
            "uploads",
        ]

        for public_dir in public_dirs:
            public_path = project_root / public_dir
            if public_path.exists():
                # Look for suspicious files
                for file_path in public_path.rglob("*"):
                    if file_path.is_file():
                        # Check for executable scripts
                        if file_path.suffix in ['.php', '.sh', '.bash', '.py']:
                            details.append(f"{RED}❌ CRITICAL: Executable script in public dir: {file_path.relative_to(project_root)}{RESET}")
                            score -= 15

                        # Check for sensitive file extensions
                        if file_path.suffix in ['.env', '.key', '.pem', '.sql']:
                            details.append(f"{RED}❌ CRITICAL: Sensitive file in public dir: {file_path.name}{RESET}")
                            score -= 20

        # Check nginx config for improper temp directory serving
        print(f"\n{BLUE}Checking web server configuration...{RESET}")

        nginx_configs = list(project_root.rglob("nginx*.conf"))
        nginx_configs.extend(list((project_root / "nginx").rglob("*.conf")))

        for config in nginx_configs:
            try:
                content = config.read_text()

                # Check for temp directory location blocks
                if "location" in content and ("tmp" in content.lower() or "temp" in content.lower()):
                    details.append(f"{YELLOW}⚠️  Nginx config may serve temp directory: {config.relative_to(project_root)}{RESET}")
                    score -= 15

                # Check for autoindex on
                if "autoindex on" in content.lower():
                    details.append(f"{YELLOW}⚠️  Directory listing enabled in: {config.relative_to(project_root)}{RESET}")
                    score -= 10
            except Exception:
                pass

        # Calculate final score
        if exposed_temp_dirs:
            issues.append(SecurityIssue(
                category="temp_directories",
                severity="critical",
                title="Publicly Accessible Temp Directories",
                description=f"Found {len(exposed_temp_dirs)} web-accessible temp directories",
                location=str(exposed_temp_dirs),
                remediation="Move temp directories outside web root:\n"
                          "- Store uploads in /var/uploads or /tmp\n"
                          "- Serve uploads through API, not direct URLs\n"
                          "- Add .htaccess or nginx deny rules for temp dirs\n"
                          "- Use random filenames instead of user-provided names\n"
                          "- Set proper file permissions (600/644)",
                cvss_score=7.5
            ))

        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details[:20]:
            print(f"   {detail}")

        if len(details) > 20:
            print(f"   ... and {len(details) - 20} more")

        print(f"\n{CYAN}Score: {score:.1f}/100{RESET}")

        return TestResult(
            test_name="Temp Directory Security",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    def _is_web_accessible(self, path: Path) -> bool:
        """Check if a path is web-accessible"""
        # Handle paths outside project root
        try:
            path_str = str(path.relative_to(project_root))
        except ValueError:
            # Path is outside project root
            return False

        # Check if it's in frontend/public or similar
        web_accessible_prefixes = [
            "frontend/public",
            "frontend/dist",
            "static",
            "media",
            "uploads",
        ]

        for prefix in web_accessible_prefixes:
            if path_str.startswith(prefix):
                return True

        return False

    # =========================================================================
    # TEST 3: Leftover Deployment Artifacts
    # =========================================================================

    async def test_deployment_artifacts(self) -> TestResult:
        """Test for leftover deployment artifacts"""
        self.print_test_header("TEST 3: Leftover Deployment Artifacts")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning for deployment artifacts...{RESET}")

        # Common deployment artifacts that should not be in production
        artifact_patterns = {
            '.git': 'Git repository',
            '.env.local': 'Local environment file',
            '.env.development': 'Development environment',
            '.env.test': 'Test environment',
            'node_modules': 'Node dependencies (should be in container)',
            '__pycache__': 'Python cache files',
            '.pyc': 'Python bytecode',
            '.pytest_cache': 'Pytest cache',
            '.coverage': 'Coverage reports',
            '.DS_Store': 'macOS metadata',
            'Thumbs.db': 'Windows thumbnail cache',
            '*.log': 'Log files',
            '*.sql.backup': 'SQL backup files',
            '*.bak': 'Backup files',
            '*.swp': 'Vim swap files',
            '*.swo': 'Vim swap files',
            '*~': 'Backup files',
            '.DS_Store': 'macOS files',
        }

        artifacts_found = []

        # Check for common artifacts
        for artifact_name, description in artifact_patterns.items():
            if artifact_name.startswith('*'):
                # Glob pattern
                for match in project_root.rglob(artifact_name[1:]):
                    if match.is_file():
                        rel_path = match.relative_to(project_root)
                        artifacts_found.append((rel_path, description))
                        details.append(f"{YELLOW}⚠️  Found artifact: {rel_path} ({description}){RESET}")
                        score -= 2
            else:
                # Direct path
                artifact_path = project_root / artifact_name
                if artifact_path.exists():
                    rel_path = artifact_path.relative_to(project_root)
                    artifacts_found.append((rel_path, description))
                    details.append(f"{YELLOW}⚠️  Found artifact: {rel_path} ({description}){RESET}")
                    score -= 5

        # Check for development/testing files in production areas
        print(f"\n{BLUE}Checking for development files...{RESET}")

        dev_files = [
            "dev.sh",
            "development.py",
            "test_*.py",
            "*_test.py",
            "conftest.py",
            "pytest.ini",
            ".flake8",
            ".pylintrc",
            "TODO.md",
            "NOTES.md",
        ]

        for pattern in dev_files:
            if '*' in pattern:
                matches = list(project_root.rglob(pattern))
            else:
                matches = [project_root / pattern] if (project_root / pattern).exists() else []

            for match in matches:
                if match.is_file():
                    rel_path = match.relative_to(project_root)
                    # Skip if it's in tests directory
                    if "tests/" not in str(rel_path):
                        details.append(f"{YELLOW}⚠️  Development file in root: {rel_path}{RESET}")
                        score -= 3

        # Check for backup files
        print(f"\n{BLUE}Scanning for backup files...{RESET}")

        backup_patterns = [
            "*.backup",
            "*.bak",
            "*.old",
            "*~",
            '*.orig',
        ]

        for pattern in backup_patterns:
            for match in project_root.rglob(pattern):
                if match.is_file():
                    rel_path = match.relative_to(project_root)
                    size = match.stat().st_size
                    details.append(f"{RED}❌ Backup file: {rel_path} ({size} bytes){RESET}")
                    score -= 5

        # Check for .git in production builds
        if (project_root / ".git").exists():
            details.append(f"{YELLOW}⚠️  .git directory present (OK for development, remove for production){RESET}")
            score -= 10

        # Check for build artifacts
        print(f"\n{BLUE}Checking for build artifacts...{RESET}")

        build_dirs = [
            "build",
            "dist",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            "node_modules",
            ".next",
            ".nuxt",
            "coverage",
        ]

        for build_dir in build_dirs:
            build_path = project_root / build_dir
            if build_path.exists():
                # Check if it should be gitignored
                gitignore = project_root / ".gitignore"
                if gitignore.exists():
                    gitignore_content = gitignore.read_text()
                    if build_dir not in gitignore_content:
                        details.append(f"{YELLOW}⚠️  Build dir not in .gitignore: {build_dir}{RESET}")
                        score -= 5
                    else:
                        details.append(f"{GREEN}✅ Build dir in .gitignore: {build_dir}{RESET}")

        # Calculate final score
        score = max(score, 0)

        if artifacts_found:
            if score < 50:
                severity = "critical"
            elif score < 70:
                severity = "high"
            else:
                severity = "medium"

            issues.append(SecurityIssue(
                category="deployment_artifacts",
                severity=severity,
                title=f"Leftover Deployment Artifacts ({len(artifacts_found)})",
                description=f"Found {len(artifacts_found)} deployment artifacts that should be removed",
                location="project_root",
                remediation="Clean deployment artifacts:\n"
                          "- Add patterns to .gitignore\n"
                          "- Use .dockerignore to exclude from containers\n"
                          "- Run: find . -name '*.pyc' -delete\n"
                          "- Run: find . -name '__pycache__' -type d -exec rm -rf {} +\n"
                          "- Remove .env.local, .env.development before deploy\n"
                          "- Use multi-stage builds to exclude dev files",
                cvss_score=5.0
            ))

        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details[:20]:
            print(f"   {detail}")

        if len(details) > 20:
            print(f"   ... and {len(details) - 20} more")

        print(f"\n{CYAN}Score: {score:.1f}/100{RESET}")

        return TestResult(
            test_name="Deployment Artifacts Cleanup",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # TEST 4: .env File Exposure
    # =========================================================================

    async def test_env_file_exposure(self) -> TestResult:
        """Test for .env file exposure"""
        self.print_test_header("TEST 4: .env File Exposure")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning for .env files...{RESET}")

        # Find all .env files
        env_files = list(project_root.glob(".env*"))
        env_files.extend(list(project_root.rglob(".env*")))

        # Remove duplicates
        env_files = list(set(env_files))

        exposed_env_files = []

        for env_file in env_files:
            rel_path = env_file.relative_to(project_root)

            # Check if it's in a public location
            if self._is_web_accessible(env_file.parent):
                details.append(f"{RED}❌ CRITICAL: .env file in web-accessible location: {rel_path}{RESET}")
                score -= 40
                exposed_env_files.append(env_file)
            else:
                # Check if it contains sensitive data
                try:
                    content = env_file.read_text()

                    # Check for secrets
                    secret_patterns = {
                        'SECRET': 'Secret key',
                        'PASSWORD': 'Password',
                        'API_KEY': 'API key',
                        'TOKEN': 'Token',
                        'PRIVATE_KEY': 'Private key',
                        'DATABASE_URL': 'Database URL',
                        'STRIPE_SECRET': 'Stripe secret',
                    }

                    secrets_found = []
                    for pattern, desc in secret_patterns.items():
                        if pattern in content:
                            # Check if it's just a comment
                            lines_with_secret = [line for line in content.split('\n') if pattern in line and not line.strip().startswith('#')]
                            if lines_with_secret:
                                secrets_found.append(desc)

                    if secrets_found:
                        details.append(f"{YELLOW}⚠️  {rel_path} contains: {', '.join(secrets_found)}{RESET}")

                        # Check if it's the example/template
                        if 'example' in str(env_file).lower() or 'template' in str(env_file).lower():
                            details.append(f"{GREEN}  → Appears to be a template (safe){RESET}")
                        else:
                            details.append(f"{RED}  → Contains actual secrets{RESET}")
                            score -= 10

                except Exception:
                    pass

        # Check .gitignore for .env patterns
        print(f"\n{BLUE}Checking .gitignore for .env patterns...{RESET}")

        gitignore = project_root / ".gitignore"
        if gitignore.exists():
            gitignore_content = gitignore.read_text()

            required_patterns = ['.env', '.env.*', '.env.local']
            missing_patterns = []

            for pattern in required_patterns:
                if pattern not in gitignore_content:
                    missing_patterns.append(pattern)

            if missing_patterns:
                details.append(f"{YELLOW}⚠️  .gitignore missing: {', '.join(missing_patterns)}{RESET}")
                score -= 15
            else:
                details.append(f"{GREEN}✅ .gitignore has .env patterns{RESET}")
        else:
            details.append(f"{RED}❌ CRITICAL: No .gitignore file found{RESET}")
            score -= 30

        # Check if .env files are in version control
        print(f"\n{BLUE}Checking if .env files are tracked by git...{RESET}")

        try:
            import subprocess
            result = subprocess.run(
                ['git', 'ls-files', '.env*'],
                cwd=project_root,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                tracked_env_files = result.stdout.strip().split('\n')
                details.append(f"{RED}❌ CRITICAL: .env files tracked by git: {', '.join(tracked_env_files)}{RESET}")
                score -= 30

                for env_file in tracked_env_files:
                    issues.append(SecurityIssue(
                        category="env_exposure",
                        severity="critical",
                        title=f".env File in Git: {env_file}",
                        description=f"Environment file tracked in version control",
                        location=env_file,
                        remediation="Remove .env from git:\n"
                                  "- Run: git rm --cached .env\n"
                                  "- Add .env to .gitignore\n"
                                  "- Rotate all exposed secrets\n"
                                  "- Use .env.example as template",
                        cvss_score=9.0
                    ))
            else:
                details.append(f"{GREEN}✅ No .env files tracked by git{RESET}")
        except Exception:
            details.append(f"{YELLOW}⚠️  Could not check git status{RESET}")

        # Check for hardcoded secrets in code
        print(f"\n{BLUE}Scanning for hardcoded secrets in Python files...{RESET}")

        secret_patterns = [
            (r'(SECRET|PASSWORD|API_KEY|TOKEN)\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret'),
            (r'stripe\.sk_(test|live)_', 'Stripe secret key'),
            (r'postgresql://.*:.*@', 'PostgreSQL connection string with password'),
            (r'mysql://.*:.*@', 'MySQL connection string with password'),
            (r'mongodb://.*:.*@', 'MongoDB connection string with password'),
            (r'AIza[A-Za-z0-9_-]{35}', 'Google API key'),
            (r'AKIA[0-9A-Z]{16}', 'AWS access key'),
        ]

        for py_file in project_root.rglob("*.py"):
            if "test" in str(py_file).lower() or "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()

                for pattern, desc in secret_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        line = content.split('\n')[line_num - 1].strip()

                        # Skip if it's a comment
                        if line.startswith('#'):
                            continue

                        details.append(f"{RED}❌ Hardcoded {desc} in {py_file.relative_to(project_root)}:{line_num}{RESET}")
                        score -= 5
            except Exception:
                pass

        # Calculate final score
        score = max(score, 0)

        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details[:30]:
            print(f"   {detail}")

        if len(details) > 30:
            print(f"   ... and {len(details) - 30} more")

        print(f"\n{CYAN}Score: {score:.1f}/100{RESET}")

        return TestResult(
            test_name=".env File Security",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # TEST 5: Logs Containing API Keys
    # =========================================================================

    async def test_log_secrets(self) -> TestResult:
        """Test for API keys and secrets in log files"""
        self.print_test_header("TEST 5: Logs Containing API Keys/Secrets")

        issues = []
        score = 100.0
        details = []

        print(f"\n{BLUE}Scanning log files for secrets...{RESET}")

        # Find all log files
        log_patterns = ["*.log", "logs/*.log", "app.log", "*.log.*"]
        log_files = []

        for pattern in log_patterns:
            if '*' in pattern:
                log_files.extend(list(project_root.rglob(pattern.replace('*', ''))))
            else:
                log_path = project_root / pattern
                if log_path.exists():
                    log_files.append(log_path)

        # Remove duplicates
        log_files = list(set(log_files))

        # Secrets to look for in logs
        secret_patterns = {
            'Bearer ey': 'JWT token',
            'sk_test_': 'Stripe test key',
            'sk_live_': 'Stripe live key',
            r'AIza[A-Za-z0-9_-]{35}': 'Google API key',
            r'AKIA[0-9A-Z]{16}': 'AWS access key',
            r'postgresql://.*:.*@': 'PostgreSQL URL with password',
            r'mysql://.*:.*@': 'MySQL URL with password',
            r'mongodb://.*:.*@': 'MongoDB URL with password',
            r'password["\']?\\s*=\\s*["\'][^"\']+["\']': 'Password assignment',
            r'secret["\']?\\s*=\\s*["\'][^"\']+["\']': 'Secret assignment',
            r'api_key["\']?\\s*=\\s*["\'][^"\']+["\']': 'API key assignment',
            r'token["\']?\\s*=\\s*["\'][^"\']+["\']': 'Token assignment',
        }

        secrets_found = []

        for log_file in log_files:
            if not log_file.is_file():
                continue

            rel_path = log_file.relative_to(project_root)

            try:
                # Read first 10MB for scanning
                content = log_file.read_text()[:10_000_000]

                for pattern, desc in secret_patterns.items():
                    matches = list(re.finditer(pattern, content, re.IGNORECASE))

                    if matches:
                        # Count unique occurrences
                        unique_contexts = set()
                        for match in matches[:20]:  # Limit to first 20 matches
                            # Get context around the match
                            start = max(0, match.start() - 50)
                            end = min(len(content), match.end() + 50)
                            context = content[start:end].replace('\n', ' ')
                            unique_contexts.add(context[:100])

                        if unique_contexts:
                            secrets_found.append((rel_path, desc, len(matches)))
                            details.append(f"{RED}❌ {desc} found in {rel_path} ({len(matches)} occurrences){RESET}")

                            # Show a sample (redacted)
                            for ctx in list(unique_contexts)[:2]:
                                # Redact the actual secret
                                redacted = re.sub(r'ey[A-Za-z0-9+/=]{10,}', 'ey***REDACTED***', ctx)
                                redacted = re.sub(r'sk_[a-z]+_[A-Za-z0-9]{10,}', 'sk_***REDACTED***', redacted, flags=re.IGNORECASE)
                                details.append(f"   Sample: ...{redacted}...")

                            score -= 20
            except Exception as e:
                details.append(f"{YELLOW}⚠️  Could not read {log_file.name}: {e}{RESET}")

        # Check for PII in logs
        print(f"\n{BLUE}Checking for PII in logs...{RESET}")

        pii_patterns = {
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b': 'Email address',
            r'\b\d{3}-\d{2}-\d{4}\b': 'SSN (XXX-XX-XXXX)',
            r'\b\d{16}\b': 'Credit card number',
            r'\b\d{3}-\d{3}-\d{4}\b': 'Phone number (XXX-XXX-XXXX)',
        }

        for log_file in log_files[:20]:  # Check first 20 log files
            if not log_file.is_file():
                continue

            rel_path = log_file.relative_to(project_root)

            try:
                content = log_file.read_text()[:1_000_000]  # First 1MB

                for pattern, desc in pii_patterns.items():
                    matches = list(re.finditer(pattern, content))

                    if matches and len(matches) > 5:  # Only flag if more than 5 occurrences
                        details.append(f"{YELLOW}⚠️  Possible {desc} in {rel_path} ({len(matches)} occurrences){RESET}")
                        score -= 10
            except Exception:
                pass

        # Check for logging configuration
        print(f"\n{BLUE}Checking logging configuration...{RESET}")

        log_config_files = [
            "app/core/logging_config.py",
            "app/logging_config.py",
            "logging.conf",
            "logging.ini",
        ]

        for config_file in log_config_files:
            config_path = project_root / config_file
            if config_path.exists():
                content = config_path.read_text()

                # Check for sensitive data filtering
                if "sanitize" in content.lower() or "redact" in content.lower():
                    details.append(f"{GREEN}✅ Log sanitization configured in {config_file}{RESET}")
                else:
                    details.append(f"{YELLOW}⚠️  No log sanitization found in {config_file}{RESET}")
                    score -= 10

                # Check if logging to stdout (could be captured)
                if "StreamHandler" in content or "console" in content.lower():
                    details.append(f"{YELLOW}⚠️  Console logging in {config_file} (be careful with output){RESET}")

        # Calculate final score
        score = max(score, 0)

        if secrets_found:
            issues.append(SecurityIssue(
                category="log_secrets",
                severity="critical",
                title=f"Secrets in Log Files ({len(secrets_found)})",
                description=f"Found API keys/secrets in {len(secrets_found)} log files",
                location="logs/",
                remediation="Implement log sanitization:\n"
                          "- Create logging filter to redact secrets\n"
                          "- Filter patterns: password, token, api_key, secret\n"
                          "- Use structured logging with field-level filtering\n"
                          "- Never log request bodies with auth data\n"
                          "- Audit existing logs and rotate them out",
                cvss_score=8.5
            ))

        print(f"\n{BLUE}Test Results:{RESET}")
        for detail in details[:30]:
            print(f"   {detail}")

        if len(details) > 30:
            print(f"   ... and {len(details) - 30} more")

        print(f"\n{CYAN}Score: {score:.1f}/100{RESET}")

        return TestResult(
            test_name="Log Secrets Prevention",
            passed=score >= 70,
            score=score,
            issues=issues,
            details="\n".join(details)
        )

    # =========================================================================
    # Main Execution
    # =========================================================================

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all file system security tests"""
        self.print_header("📁 FILE SYSTEM & STORAGE SECURITY TESTING SUITE")

        print(f"{BLUE}Started: {self.start_time.isoformat()}{RESET}")
        print(f"{BLUE}Project: {project_root}{RESET}\n")

        print(f"{YELLOW}Tests to run:{RESET}")
        print(f"   1. Directory Traversal Vulnerabilities")
        print(f"   2. Publicly Accessible Temp Directories")
        print(f"   3. Leftover Deployment Artifacts")
        print(f"   4. .env File Exposure")
        print(f"   5. Logs Containing API Keys")

        # Run tests
        try:
            result1 = await self.test_directory_traversal()
            self.test_results.append(result1)

            result2 = await self.test_temp_directories()
            self.test_results.append(result2)

            result3 = await self.test_deployment_artifacts()
            self.test_results.append(result3)

            result4 = await self.test_env_file_exposure()
            self.test_results.append(result4)

            result5 = await self.test_log_secrets()
            self.test_results.append(result5)

        except Exception as e:
            print(f"{RED}Error running tests: {e}{RESET}")
            import traceback
            traceback.print_exc()

        # Generate summary
        self.print_summary()

        # Save detailed report
        self.save_report()

        return {
            "total_tests": len(self.test_results),
            "passed": sum(1 for r in self.test_results if r.passed),
            "failed": sum(1 for r in self.test_results if not r.passed),
            "average_score": sum(r.score for r in self.test_results) / len(self.test_results) if self.test_results else 0,
            "issues_found": sum(len(r.issues) for r in self.test_results),
            "critical_issues": sum(
                1 for r in self.test_results
                for i in r.issues
                if i.severity == "critical"
            )
        }

    def print_summary(self):
        """Print test summary"""
        self.print_header("📊 FILE SYSTEM SECURITY SUMMARY")

        if not self.test_results:
            print(f"{RED}No test results available{RESET}")
            return

        # Calculate overall score
        total_score = sum(r.score for r in self.test_results) / len(self.test_results)

        print(f"\n{CYAN}Overall Security Score: {total_score:.1f}/100{RESET}\n")

        # Print individual test results
        for result in self.test_results:
            status = f"{GREEN}✅ PASS{RESET}" if result.passed else f"{RED}❌ FAIL{RESET}"
            print(f"{status} {result.test_name}: {result.score:.1f}/100")

            if result.issues:
                for issue in result.issues:
                    severity_color = {
                        "critical": RED,
                        "high": YELLOW,
                        "medium": YELLOW,
                        "low": BLUE
                    }.get(issue.severity, RESET)

                    print(f"   {severity_color}● {issue.severity.upper()}: {issue.title}{RESET}")

        # Print issue count
        total_issues = sum(len(r.issues) for r in self.test_results)
        critical_issues = sum(
            1 for r in self.test_results
            for i in r.issues
            if i.severity == "critical"
        )

        print(f"\n{YELLOW}Total Issues Found: {total_issues}{RESET}")
        if critical_issues > 0:
            print(f"{RED}Critical Issues: {critical_issues}{RESET}")

        # Print status
        if total_score >= 90:
            print(f"\n{GREEN}✅ EXCELLENT: File system security is strong{RESET}")
        elif total_score >= 70:
            print(f"\n{YELLOW}⚠️  GOOD: Some improvements recommended{RESET}")
        else:
            print(f"\n{RED}❌ POOR: Critical file system security issues detected{RESET}")

        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"\n{BLUE}Completed: {datetime.now().isoformat()}{RESET}")
        print(f"{BLUE}Duration: {elapsed:.2f} seconds{RESET}")

    def save_report(self):
        """Save detailed report to JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(project_root),
            "overall_score": sum(r.score for r in self.test_results) / len(self.test_results) if self.test_results else 0,
            "tests": [
                {
                    "name": r.test_name,
                    "passed": r.passed,
                    "score": r.score,
                    "issues": [
                        {
                            "category": i.category,
                            "severity": i.severity,
                            "title": i.title,
                            "description": i.description,
                            "location": str(i.location),
                            "remediation": i.remediation,
                            "cvss_score": i.cvss_score
                        }
                        for i in r.issues
                    ],
                    "details": r.details
                }
                for r in self.test_results
            ]
        }

        report_file = project_root / "filesystem_security_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n{BLUE}Detailed report saved to: {report_file}{RESET}")


async def main():
    """Main entry point"""
    tester = FilesystemSecurityTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
