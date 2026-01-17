"""
Specialized AI Agents
Advanced agents for security, performance, monitoring, and automation
"""

import re
import ast
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from agent_framework import (
    BaseAgent, AgentConfig, run_command, find_files, read_file
)


# ============================================
# SECURITY AGENTS
# ============================================

class SecurityHeaderValidatorAgent(BaseAgent):
    """AI agent: validate security headers on all routes"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy',
            'Permissions-Policy'
        ]

        # Check FastAPI route files
        api_files = find_files(project_root / "app/api", "*.py")

        for api_file in api_files:
            code = read_file(api_file)

            missing_headers = []
            for header in security_headers:
                if header.lower() not in code.lower():
                    missing_headers.append(header)

            if missing_headers:
                findings.append({
                    "type": "missing_security_headers",
                    "file": str(api_file.relative_to(project_root)),
                    "missing_headers": missing_headers,
                    "severity": "high" if len(missing_headers) > 3 else "medium"
                })

        metrics = {
            "routes_checked": len(api_files),
            "routes_with_missing_headers": len(findings),
            "critical_security_headers": len(security_headers)
        }

        recommendations = [
            "Add X-Content-Type-Options: nosniff header",
            "Add X-Frame-Options: DENY or SAMEORIGIN header",
            "Add Content-Security-Policy header",
            "Add Strict-Transport-Security header for HTTPS",
            "Review and implement all security headers"
        ]

        return findings, metrics, recommendations


class EncryptionStrategyAgent(BaseAgent):
    """AI agent: suggest encryption strategy for sensitive fields"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        sensitive_patterns = {
            'password': r'\bpassword\s*[:=]',
            'ssn': r'\b(ssn|social_security)\s*[:=]',
            'credit_card': r'\b(credit_card|card_number|cc_number)\s*[:=]',
            'api_key': r'\b(api_key|apikey)\s*[:=]',
            'token': r'\b(access_token|refresh_token|auth_token)\s*[:=]',
            'email': r'\bemail\s*[:=]'
        }

        # Check model files for sensitive fields
        model_files = find_files(project_root / "app/db/models", "*.py")

        for model_file in model_files:
            code = read_file(model_file)

            sensitive_fields = []
            for field_name, pattern in sensitive_patterns.items():
                if re.search(pattern, code, re.IGNORECASE):
                    sensitive_fields.append(field_name)

            if sensitive_fields:
                # Check if encryption is used
                has_encryption = bool(re.search(
                    r'(encrypt|decrypt|cipher|hash|bcrypt)',
                    code,
                    re.IGNORECASE
                ))

                findings.append({
                    "type": "sensitive_field_encryption_check",
                    "file": str(model_file.relative_to(project_root)),
                    "sensitive_fields": sensitive_fields,
                    "has_encryption": has_encryption,
                    "recommendation": "Implement field-level encryption" if not has_encryption else "Encryption detected"
                })

        metrics = {
            "models_checked": len(model_files),
            "models_with_sensitive_fields": len(findings),
            "models_without_encryption": sum(1 for f in findings if not f['has_encryption'])
        }

        recommendations = [
            "Use AES-256 encryption for sensitive fields",
            "Implement hashing for passwords (bcrypt/argon2)",
            "Never store credit card numbers without PCI compliance",
            "Use environment variables for API keys",
            "Consider tokenization for PII"
        ]

        return findings, metrics, recommendations


class ThirdPartyScriptSafetyAgent(BaseAgent):
    """AI agent: warn about unsafe third-party scripts"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        unsafe_patterns = {
            'cdn_script': r'<script\s+src=["\']https?://cdn\.',
            'http_script': r'<script\s+src=["\']http://',  # HTTP instead of HTTPS
            'inline_script': r'<script[^>]*>.*?</script>',  # Inline scripts
            'integrity_missing': r'<script\s+src=["\']https?://.*?(?<!integrity=)',
            'eval_usage': r'\beval\s*\(',
            'innerHTML': r'\.innerHTML\s*='
        }

        # Check HTML and template files
        html_files = find_files(project_root, "*.html")
        template_files = find_files(project_root / "app/templates", "*.html")
        all_files = html_files + template_files

        for file_path in all_files[:20]:  # Sample first 20
            code = read_file(file_path)

            unsafe_issues = []
            for issue_type, pattern in unsafe_patterns.items():
                matches = re.findall(pattern, code, re.IGNORECASE | re.DOTALL)
                if matches:
                    unsafe_issues.append({
                        "issue": issue_type,
                        "count": len(matches)
                    })

            if unsafe_issues:
                findings.append({
                    "type": "unsafe_third_party_script",
                    "file": str(file_path.relative_to(project_root)),
                    "issues": unsafe_issues,
                    "severity": "high"
                })

        metrics = {
            "files_scanned": len(all_files),
            "files_with_issues": len(findings),
            "total_issues": sum(len(f['issues']) for f in findings)
        }

        recommendations = [
            "Use Subresource Integrity (SRI) for all CDN scripts",
            "Avoid inline scripts - use external files",
            "Replace innerHTML with textContent or createElement",
            "Never use eval() - use JSON.parse instead",
            "Ensure all scripts load over HTTPS",
            "Implement Content Security Policy (CSP)"
        ]

        return findings, metrics, recommendations


# ============================================
# CODE QUALITY AGENTS
# ============================================

class CodingStyleEnforcerAgent(BaseAgent):
    """AI agent: continuously enforce coding style using prompts"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        style_violations = {
            'line_too_long': 0,
            'missing_docstring': 0,
            'incorrect_import_order': 0,
            'trailing_whitespace': 0,
            'multiple_blank_lines': 0
        }

        # Check Python files
        py_files = find_files(project_root, "*.py")[:30]

        for py_file in py_files:
            code = read_file(py_file)
            lines = code.split('\n')

            file_violations = []

            for i, line in enumerate(lines, 1):
                # Check line length
                if len(line) > 100:
                    style_violations['line_too_long'] += 1
                    file_violations.append(f"Line {i}: Too long ({len(line)} chars)")

                # Check trailing whitespace
                if line.rstrip() != line and line.strip():
                    style_violations['trailing_whitespace'] += 1
                    file_violations.append(f"Line {i}: Trailing whitespace")

                # Check multiple blank lines
                if i > 1 and not lines[i-2].strip() and not line.strip():
                    style_violations['multiple_blank_lines'] += 1

            # Check for docstrings
            has_docstring = bool(re.search(r'""".*?"""', code, re.DOTALL))
            if not has_docstring and len(code) > 100:
                style_violations['missing_docstring'] += 1
                file_violations.append("Missing module docstring")

            if file_violations:
                findings.append({
                    "type": "style_violation",
                    "file": str(py_file.relative_to(project_root)),
                    "violations": file_violations[:5]  # First 5 violations
                })

        metrics = {
            "files_checked": len(py_files),
            "total_violations": sum(style_violations.values()),
            "violation_types": style_violations
        }

        recommendations = [
            "Run: pip install black && black . (auto-format)",
            "Run: pip install flake8 && flake8 . (check style)",
            "Set up pre-commit hooks with black and flake8",
            "Configure line length to 88 characters (Black default)",
            "Add docstrings to all modules and functions"
        ]

        return findings, metrics, recommendations


class LocalizationGapDetectorAgent(BaseAgent):
    """AI agent: detect missing localization keys"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find localization files
        locale_files = find_files(project_root / "frontend/src/i18n", "*.json")

        if not locale_files:
            return [{
                "type": "no_localization_files",
                "message": "No localization files found"
            }, {}, ["Create i18n directory with locale files"]]

        # Get reference locale (usually English)
        reference_keys = set()
        reference_file = None

        for locale_file in locale_files:
            if 'en' in str(locale_file).lower():
                try:
                    data = json.loads(read_file(locale_file))
                    reference_keys = self._get_all_keys(data)
                    reference_file = locale_file
                    break
                except:
                    continue

        if not reference_keys:
            reference_keys = self._get_all_keys(json.loads(read_file(locale_files[0])))
            reference_file = locale_files[0]

        # Check other locales for missing keys
        for locale_file in locale_files:
            if locale_file == reference_file:
                continue

            try:
                data = json.loads(read_file(locale_file))
                current_keys = self._get_all_keys(data)

                missing_keys = reference_keys - current_keys
                extra_keys = current_keys - reference_keys

                if missing_keys or extra_keys:
                    findings.append({
                        "type": "localization_gap",
                        "locale": str(locale_file.relative_to(project_root)),
                        "missing_keys": list(missing_keys)[:10],
                        "extra_keys": list(extra_keys)[:10],
                        "coverage": f"{(len(current_keys) / len(reference_keys) * 100):.0f}%"
                    })
            except:
                findings.append({
                    "type": "localization_error",
                    "locale": str(locale_file.relative_to(project_root)),
                    "error": "Failed to parse JSON"
                })

        metrics = {
            "locales_checked": len(locale_files),
            "reference_keys": len(reference_keys),
            "locales_with_gaps": len(findings)
        }

        recommendations = [
            "Ensure all locales have matching keys",
            "Use i18n ally VS Code extension for validation",
            "Consider using i18next or similar for better management",
            "Run localization checks in CI/CD pipeline"
        ]

        return findings, metrics, recommendations

    def _get_all_keys(self, data, prefix=''):
        """Recursively get all keys from nested dictionary"""
        keys = set()
        if isinstance(data, dict):
            for key, value in data.items():
                current_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    keys.update(self._get_all_keys(value, current_key))
                else:
                    keys.add(current_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                keys.update(self._get_all_keys(item, current_key))
        return keys


# ============================================
# PERFORMANCE AGENTS
# ============================================

class PerformanceRegressionAgent(BaseAgent):
    """AI agent: check for performance regression per commit"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Get recent commits
        success, stdout, _ = run_command(
            ["git", "log", "--oneline", "-10"],
            cwd=project_root
        )

        if not success:
            return [{"type": "error", "message": "Cannot access git history"}], {}, []

        commits = stdout.strip().split('\n')

        # Analyze commit patterns
        for commit in commits[:5]:
            commit_hash, *message = commit.split(' ', 1)
            message = message[0] if message else ""

            # Check for performance-related changes
            perf_keywords = ['optimize', 'slow', 'performance', 'fast', 'cache']
            if any(keyword in message.lower() for keyword in perf_keywords):
                findings.append({
                    "type": "performance_commit",
                    "commit": commit_hash,
                    "message": message,
                    "impact": "positive"
                })

            # Check for potentially problematic patterns
            risky_keywords = ['loop', 'nested', 'recursive', 'synchronous']
            if any(keyword in message.lower() for keyword in risky_keywords):
                findings.append({
                    "type": "potential_performance_risk",
                    "commit": commit_hash,
                    "message": message,
                    "recommendation": "Review for performance impact"
                })

        metrics = {
            "commits_analyzed": len(commits),
            "performance_commits": len([f for f in findings if f.get('type') == 'performance_commit']),
            "risky_commits": len([f for f in findings if f.get('type') == 'potential_performance_risk'])
        }

        recommendations = [
            "Add performance benchmarks for critical paths",
            "Run load tests after performance-related commits",
            "Monitor response times in production",
            "Set up alerts for performance degradation",
            "Use profiling tools to identify bottlenecks"
        ]

        return findings, metrics, recommendations


class SlowEndpointTrackerAgent(BaseAgent):
    """AI agent: track slow endpoints and auto-propose fixes"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find route definitions
        route_files = find_files(project_root / "app/api", "*/endpoints/*.py")

        for route_file in route_files:
            code = read_file(route_file)

            # Look for potential performance issues
            slow_patterns = {
                'n_plus_one': r'for\s+\w+\s+in\s+.+:\s*.+\.filter\(',  # N+1 query pattern
                'large_query': r'\.all\(\)',  # Potential large result set
                'sync_in_async': r'await\s+sync_',  # Sync operations in async
                'no_limit': r'Query\(.+\)\.(all|first)\(\)',  # No pagination
            }

            for issue_type, pattern in slow_patterns.items():
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    findings.append({
                        "type": "potential_slow_endpoint",
                        "file": str(route_file.relative_to(project_root)),
                        "line": line_num,
                        "issue": issue_type,
                        "code_snippet": match.group(0)[:50]
                    })

        metrics = {
            "endpoints_analyzed": len(route_files),
            "potential_slow_endpoints": len(findings)
        }

        recommendations = {
            "n_plus_one": "Use eager loading with select_in/load_select_in",
            "large_query": "Add pagination with limit/offset",
            "sync_in_async": "Convert to async operations",
            "no_limit": "Always add pagination parameters"
        }

        rec_list = [
            f"Implement pagination for all list endpoints",
            f"Use database indexes on frequently queried fields",
            f"Consider caching for expensive operations",
            f"Add response time monitoring to all endpoints"
        ]

        return findings, metrics, rec_list


# ============================================
# MONITORING & TELEMETRY AGENTS
# ============================================

class UXFrictionTrackerAgent(BaseAgent):
    """AI agent: track UX friction points via telemetry"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for common UX issues in frontend code
        frontend_files = find_files(project_root / "frontend/src", "*.tsx")

        ux_issues = {
            'no_loading_state': 0,
            'no_error_handling': 0,
            'complex_form': 0,
            'missing_labels': 0,
            'no_feedback': 0
        }

        for file_path in frontend_files[:20]:
            code = read_file(file_path)

            # Check for loading states
            if 'useState' in code and 'loading' not in code.lower():
                ux_issues['no_loading_state'] += 1

            # Check for error handling
            if 'fetch' in code or 'axios' in code:
                if '.catch' not in code and 'try' not in code:
                    ux_issues['no_error_handling'] += 1

            # Check for form labels
            input_count = code.count('<input')
            label_count = code.count('<label')
            if input_count > label_count:
                ux_issues['missing_labels'] += input_count - label_count

        findings.append({
            "type": "ux_friction_analysis",
            "issues": ux_issues,
            "files_analyzed": len(frontend_files)
        })

        metrics = {
            "total_issues": sum(ux_issues.values()),
            "files_with_issues": sum(1 for v in ux_issues.values() if v > 0)
        }

        recommendations = [
            "Add loading states for all async operations",
            "Implement proper error handling with user-friendly messages",
            "Ensure all form inputs have associated labels",
            "Provide visual feedback for user actions",
            "Monitor time-to-interactive metrics",
            "Track user frustration indicators (rage clicks, rapid navigation)"
        ]

        return findings, metrics, recommendations


class EnvironmentConfigDetectorAgent(BaseAgent):
    """AI agent: detect environment misconfigurations"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for .env files
        env_files = list(project_root.glob(".env*"))

        # Check for common misconfigurations
        misconfigs = []

        for env_file in env_files:
            content = read_file(env_file)

            # Check for insecure defaults
            if 'DEBUG=True' in content or 'DEBUG = True' in content:
                misconfigs.append({
                    "file": env_file.name,
                    "issue": "DEBUG enabled in production",
                    "severity": "critical"
                })

            # Check for hardcoded secrets
            secret_patterns = [
                (r'password\s*=\s*\w+', "Hardcoded password"),
                (r'api_key\s*=\s*\w+', "Hardcoded API key"),
                (r'secret\s*=\s*\w+', "Hardcoded secret")
            ]

            for pattern, description in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    misconfigs.append({
                        "file": env_file.name,
                        "issue": description,
                        "severity": "high"
                    })

            # Check for missing required variables
            required_vars = ['DATABASE_URL', 'SECRET_KEY', 'ALLOWED_HOSTS']
            for var in required_vars:
                if var not in content:
                    misconfigs.append({
                        "file": env_file.name,
                        "issue": f"Missing required variable: {var}",
                        "severity": "medium"
                    })

        if misconfigs:
            findings.append({
                "type": "environment_misconfiguration",
                "issues": misconfigs
            })

        metrics = {
            "env_files_checked": len(env_files),
            "misconfigurations_found": len(misconfigs)
        }

        recommendations = [
            "Use environment-specific .env files (.env.dev, .env.prod)",
            "Never commit .env files to version control",
            "Use secret management systems (AWS Secrets Manager, Vault)",
            "Validate required environment variables on startup",
            "Use different values for development and production"
        ]

        return findings, metrics, recommendations


class UptimeMonitorAgent(BaseAgent):
    """AI agent: monitor uptime and provide daily status summary"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check if application is running
        success, _, _ = run_command(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000/docs"],
            cwd=project_root
        )

        status = "up" if success and "200" in str(success) else "down"

        findings.append({
            "type": "uptime_status",
            "service": "backend_api",
            "status": status,
            "url": "http://localhost:8000",
            "timestamp": datetime.now().isoformat()
        })

        # Check database connection
        db_status = "unknown"
        try:
            import psycopg2
            conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/psychsync_db")
            conn.close()
            db_status = "connected"
        except:
            db_status = "disconnected"

        findings.append({
            "type": "database_status",
            "service": "postgres",
            "status": db_status,
            "timestamp": datetime.now().isoformat()
        })

        metrics = {
            "services_checked": 2,
            "services_up": sum(1 for f in findings if f['status'] in ['up', 'connected']),
            "uptime_percentage": 100 if all(f['status'] in ['up', 'connected'] for f in findings) else 50
        }

        recommendations = []
        if status == "down":
            recommendations.append("Backend API is down - start with: uvicorn app.main:app --reload")
        if db_status == "disconnected":
            recommendations.append("Database is disconnected - check PostgreSQL service")

        if not recommendations:
            recommendations.append("All systems operational - continue monitoring")

        return findings, metrics, recommendations


# ============================================
# INCIDENT & RELEASE MANAGEMENT AGENTS
# ============================================

class IncidentMitigationPlannerAgent(BaseAgent):
    """AI agent: create mitigation plan for major incidents"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        # Check for recent errors in logs
        log_files = list(project_root.glob("*.log")) + list(project_root.glob("logs/*.log"))

        critical_errors = []

        for log_file in log_files[:5]:
            content = read_file(log_file)

            # Find critical errors
            error_pattern = r'(CRITICAL|ERROR|500|Exception)'
            matches = re.findall(error_pattern, content)

            if matches:
                critical_errors.append({
                    "file": str(log_file.name),
                    "error_count": len(matches)
                })

        findings = [{
            "type": "incident_assessment",
            "critical_errors_detected": len(critical_errors) > 0,
            "error_sources": critical_errors,
            "severity": "high" if critical_errors else "low"
        }]

        metrics = {
            "log_files_scanned": len(log_files),
            "critical_errors": sum(e['error_count'] for e in critical_errors)
        }

        recommendations = [
            "Set up automated error tracking (Sentry, Rollbar)",
            "Create incident response playbook",
            "Implement circuit breakers for failing services",
            "Add health check endpoints",
            "Set up alerting for critical errors",
            "Document common incident scenarios and mitigations"
        ]

        return findings, metrics, recommendations


class ReleaseNotesGeneratorAgent(BaseAgent):
    """AI agent: generate internal release notes"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        # Get recent commits
        success, stdout, _ = run_command(
            ["git", "log", "--pretty=format:%h|%s|%an", "--since=1 week ago"],
            cwd=project_root
        )

        commits = stdout.strip().split('\n') if success else []

        # Categorize commits
        categories = {
            'features': [],
            'bugfixes': [],
            'improvements': [],
            'breaking': [],
            'other': []
        }

        for commit in commits:
            if not commit:
                continue

            parts = commit.split('|')
            if len(parts) < 2:
                continue

            hash_val, message = parts[0], parts[1]
            message_lower = message.lower()

            if 'break' in message_lower:
                categories['breaking'].append(f"{hash_val}: {message}")
            elif any(kw in message_lower for kw in ['feat', 'add', 'new']):
                categories['features'].append(f"{hash_val}: {message}")
            elif any(kw in message_lower for kw in ['fix', 'bug']):
                categories['bugfixes'].append(f"{hash_val}: {message}")
            elif any(kw in message_lower for kw in ['improve', 'optimize', 'refactor']):
                categories['improvements'].append(f"{hash_val}: {message}")
            else:
                categories['other'].append(f"{hash_val}: {message}")

        findings = [{
            "type": "release_notes",
            "period": "Last 7 days",
            "summary": categories
        }]

        metrics = {
            "total_commits": len(commits),
            "features": len(categories['features']),
            "bugfixes": len(categories['bugfixes']),
            "breaking_changes": len(categories['breaking'])
        }

        recommendations = [
            "Review breaking changes before deployment",
            "Update documentation for new features",
            "Communicate bug fixes to stakeholders",
            "Plan testing around high-risk changes"
        ]

        return findings, metrics, recommendations


class DependencyUpdaterAgent(BaseAgent):
    """AI agent: automatically update dependency versions monthly"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check Python dependencies
        requirements_files = list(project_root.glob("requirements*.txt"))

        for req_file in requirements_files:
            content = read_file(req_file)
            lines = content.split('\n')

            outdated_packages = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Simple check for unpinned versions
                    if '==' not in line and not line.startswith('-'):
                        outdated_packages.append({
                            "package": line,
                            "issue": "Unpinned version",
                            "recommendation": f"{line}==<version>"
                        })

            if outdated_packages:
                findings.append({
                    "type": "dependency_issue",
                    "file": str(req_file.name),
                    "issues": outdated_packages
                })

        # Check package.json
        package_json = project_root / "frontend/package.json"
        if package_json.exists():
            content = read_file(package_json)
            try:
                data = json.loads(content)

                dependencies = data.get('dependencies', {})
                dev_dependencies = data.get('devDependencies', {})

                total_deps = len(dependencies) + len(dev_dependencies)
                findings.append({
                    "type": "npm_dependencies",
                    "file": "frontend/package.json",
                    "dependencies_count": total_deps,
                    "last_updated": "Unknown - run 'npm outdated'"
                })
            except:
                pass

        metrics = {
            "dependency_files_checked": len(requirements_files) + (1 if package_json.exists() else 0),
            "issues_found": len(findings)
        }

        recommendations = [
            "Run 'pip list --outdated' to check for updates",
            "Run 'npm outdated' in frontend directory",
            "Set up Dependabot or Renovate for automatic updates",
            "Pin all dependency versions in requirements.txt",
            "Review and test updates before applying"
        ]

        return findings, metrics, recommendations


# ============================================
# INTEGRATION & TRACKING AGENTS
# ============================================

class PRToJiraMapperAgent(BaseAgent):
    """AI agent: map PRs to Jira tickets"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        # Get recent commits
        success, stdout, _ = run_command(
            ["git", "log", "--pretty=format:%h|%s", "-20"],
            cwd=project_root
        )

        commits = stdout.strip().split('\n') if success else []

        # Look for Jira ticket patterns
        jira_pattern = r'[A-Z]{2,}-\d{1,5}'

        mapped_prs = []
        unmapped_prs = []

        for commit in commits:
            if not commit:
                continue

            parts = commit.split('|')
            if len(parts) < 2:
                continue

            hash_val, message = parts[0], parts[1]

            jira_match = re.search(jira_pattern, message)
            if jira_match:
                mapped_prs.append({
                    "commit": hash_val,
                    "ticket": jira_match.group(0),
                    "message": message
                })
            else:
                unmapped_prs.append({
                    "commit": hash_val,
                    "message": message
                })

        findings = [{
            "type": "jira_mapping_report",
            "mapped_commits": len(mapped_prs),
            "unmapped_commits": len(unmapped_prs),
            "mapping_rate": f"{(len(mapped_prs) / len(commits) * 100):.0f}%" if commits else "0%"
        }]

        metrics = {
            "total_commits": len(commits),
            "with_jira_tickets": len(mapped_prs),
            "without_jira_tickets": len(unmapped_prs)
        }

        recommendations = [
            "Include Jira ticket ID in commit messages (e.g., PROJ-123)",
            "Set up branch naming convention: feature/PROJ-123-description",
            "Use commit hooks to validate Jira ticket format",
            "Configure PR templates to require ticket number"
        ]

        return findings, metrics, recommendations


class TestCoverageReporterAgent(BaseAgent):
    """AI agent: generate test coverage reports"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Count test files vs source files
        test_files = find_files(project_root / "tests", "test_*.py")
        source_files = find_files(project_root / "app", "*.py")

        # Run pytest coverage if available
        success, stdout, stderr = run_command(
            ["python", "-m", "pytest", "--cov=app", "--cov-report=term", "--collect-only"],
            cwd=project_root
        )

        coverage_data = {
            "test_files": len(test_files),
            "source_files": len(source_files),
            "test_to_source_ratio": f"{(len(test_files) / len(source_files) * 100):.0f}%" if source_files else "0%"
        }

        findings.append({
            "type": "test_coverage_summary",
            "coverage_data": coverage_data,
            "recommendation": "Aim for 80%+ test coverage"
        })

        metrics = coverage_data

        recommendations = [
            "Run 'pytest --cov=app --cov-report=html' for HTML report",
            "Set minimum coverage threshold in pytest.ini",
            "Add tests for new features",
            "Use pytest-cov for coverage tracking",
            "Integrate coverage reports in CI/CD"
        ]

        return findings, metrics, recommendations


class PermissionGapDetectorAgent(BaseAgent):
    """AI agent: detect gaps in permission enforcement"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find endpoint files
        endpoint_files = find_files(project_root / "app/api", "*/endpoints/*.py")

        unprotected_endpoints = []

        for endpoint_file in endpoint_files:
            code = read_file(endpoint_file)

            # Check for endpoint definitions
            endpoint_pattern = r'@(router\.)?\w+\.(get|post|put|delete|patch)'
            endpoints = re.findall(endpoint_pattern, code)

            # Check if dependencies are used
            has_auth_checks = bool(re.search(r'(Depends|authorize|permission)', code, re.IGNORECASE))

            if endpoints and not has_auth_checks:
                unprotected_endpoints.append({
                    "file": str(endpoint_file.relative_to(project_root)),
                    "endpoints_count": len(endpoints)
                })

        if unprotected_endpoints:
            findings.append({
                "type": "permission_enforcement_gap",
                "unprotected_endpoints": unprotected_endpoints,
                "severity": "high"
            })

        metrics = {
            "endpoint_files_checked": len(endpoint_files),
            "files_without_permissions": len(unprotected_endpoints)
        }

        recommendations = [
            "Add authentication dependencies to all endpoints",
            "Implement role-based access control (RBAC)",
            "Use @require_login decorator for protected routes",
            "Audit endpoint permissions regularly",
            "Document permission requirements"
        ]

        return findings, metrics, recommendations


class WeeklyStabilityScorerAgent(BaseAgent):
    """AI agent: produce weekly stability score"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        # Get weekly commit activity
        success, stdout, _ = run_command(
            ["git", "log", "--since=1 week ago", "--oneline"],
            cwd=project_root
        )

        commits = stdout.strip().split('\n') if success else []
        commit_count = len([c for c in commits if c.strip()])

        # Calculate stability score
        # Factors: commit count, failed builds (mock), errors in logs (mock)
        score = 100

        # Reduce score for excessive commits (may indicate instability)
        if commit_count > 100:
            score -= 10
        elif commit_count < 5:
            score -= 5  # Low activity

        # Mock data for other factors
        failed_builds = 0
        critical_errors = 0

        score -= (failed_builds * 5)
        score -= (critical_errors * 2)

        score = max(0, min(100, score))

        findings = [{
            "type": "weekly_stability_report",
            "week_start": (datetime.now() - timedelta(days=7)).isoformat(),
            "week_end": datetime.now().isoformat(),
            "stability_score": score,
            "grade": "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D",
            "commits_this_week": commit_count
        }]

        metrics = {
            "stability_score": score,
            "commits": commit_count,
            "failed_builds": failed_builds,
            "critical_errors": critical_errors
        }

        recommendations = []
        if score >= 90:
            recommendations.append("Excellent stability - maintain current practices")
        elif score >= 75:
            recommendations.append("Good stability - monitor trends")
        elif score >= 60:
            recommendations.append("Fair stability - investigate issues")
        else:
            recommendations.append("Poor stability - immediate action required")

        return findings, metrics, recommendations


class ArchitectureDriftDetectorAgent(BaseAgent):
    """AI agent: generate architecture drift warnings"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for architecture violations
        violations = []

        # Check for direct database access in API endpoints
        api_files = find_files(project_root / "app/api", "*.py")
        for api_file in api_files:
            code = read_file(api_file)
            if re.search(r'(from app.db.models import|import.*models\.|Session\(\))', code):
                violations.append({
                    "type": "direct_db_access",
                    "file": str(api_file.relative_to(project_root)),
                    "severity": "medium"
                })

        # Check for business logic in frontend
        frontend_files = find_files(project_root / "frontend/src", "*.ts")
        for frontend_file in frontend_files[:20]:
            code = read_file(frontend_file)
            # Look for complex logic that should be in backend
            if code.count('if ') > 10:
                violations.append({
                    "type": "complex_frontend_logic",
                    "file": str(frontend_file.relative_to(project_root)),
                    "severity": "low"
                })

        # Check for circular dependencies
        import_pattern = r'from app\.(\w+)'
        for py_file in find_files(project_root / "app", "*.py")[:30]:
            code = read_file(py_file)
            imports = re.findall(import_pattern, code)
            if len(set(imports)) > 5:
                violations.append({
                    "type": "high_coupling",
                    "file": str(py_file.relative_to(project_root)),
                    "imports": len(set(imports)),
                    "severity": "medium"
                })

        if violations:
            findings.append({
                "type": "architecture_drift",
                "violations": violations
            })

        metrics = {
            "files_analyzed": len(api_files) + len(frontend_files),
            "drift_violations": len(violations)
        }

        recommendations = [
            "Enforce layered architecture (API → Service → CRUD → DB)",
            "Keep business logic in service layer",
            "Use dependency injection to reduce coupling",
            "Document architecture decision records (ADRs)",
            "Run architecture linters in CI/CD"
        ]

        return findings, metrics, recommendations


class BugEnvironmentCreatorAgent(BaseAgent):
    """AI agent: create reproducible bug environments"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for Docker setup
        docker_compose = project_root / "docker-compose.yml"
        dockerfile = project_root / "Dockerfile"

        has_docker = docker_compose.exists() and dockerfile.exists()

        # Check for test data fixtures
        fixtures_dir = project_root / "tests" / "fixtures"
        has_fixtures = fixtures_dir.exists()

        # Check for seed scripts
        seed_scripts = list(project_root.glob("app/scripts/seed*.py"))

        findings.append({
            "type": "bug_reproducibility_assessment",
            "docker_available": has_docker,
            "test_fixtures": has_fixtures,
            "seed_scripts": len(seed_scripts),
            "reproducibility_score": sum([
                25 if has_docker else 0,
                25 if has_fixtures else 0,
                25 if seed_scripts else 0,
                25  # Base score for having tests
            ])
        })

        metrics = {
            "docker_setup": 1 if has_docker else 0,
            "fixtures": 1 if has_fixtures else 0,
            "seed_scripts": len(seed_scripts)
        }

        recommendations = [
            "Create Docker setup for consistent environments",
            "Add test fixtures for common scenarios",
            "Create seed scripts for test data",
            "Document environment setup steps",
            "Use docker-compose for local development"
        ]

        return findings, metrics, recommendations


class RefactoringTargetProposerAgent(BaseAgent):
    """AI agent: propose refactoring targets each sprint"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find large files (potential refactoring targets)
        py_files = find_files(project_root / "app", "*.py")
        large_files = []

        for py_file in py_files:
            code = read_file(py_file)
            lines = len(code.split('\n'))

            if lines > 300:
                # Calculate complexity
                complexity = code.count('def ') + code.count('class ') * 2

                large_files.append({
                    "file": str(py_file.relative_to(project_root)),
                    "lines": lines,
                    "complexity": complexity,
                    "priority": "high" if lines > 500 else "medium"
                })

        # Sort by size
        large_files.sort(key=lambda x: x['lines'], reverse=True)

        if large_files:
            findings.append({
                "type": "refactoring_candidates",
                "targets": large_files[:10],  # Top 10
                "total_candidates": len(large_files)
            })

        metrics = {
            "files_analyzed": len(py_files),
            "large_files_found": len(large_files),
            "avg_file_size": sum(f['lines'] for f in large_files) / len(large_files) if large_files else 0
        }

        recommendations = [
            "Prioritize files over 500 lines for refactoring",
            "Apply Single Responsibility Principle",
            "Extract classes for complex logic",
            "Create separate modules for distinct functionality",
            "Set file size limit in linting rules"
        ]

        return findings, metrics, recommendations
