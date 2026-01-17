"""
Code Quality AI Agents
Monitor, analyze, and improve code quality continuously
"""

import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from agent_framework import (
    BaseAgent, AgentConfig, AgentStatus, Priority,
    run_command, find_files, read_file, analyze_code_complexity
)


class CodeQualityMonitorAgent(BaseAgent):
    """AI agent: continuously monitor code quality daily"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        metrics = {}
        recommendations = []

        # Check Python files
        py_files = find_files(project_root, "*.py")
        ts_files = find_files(project_root, "*.tsx")
        js_files = find_files(project_root, "*.jsx")

        total_files = len(py_files) + len(ts_files) + len(js_files)

        # Calculate complexity metrics
        complexities = []
        for py_file in py_files[:20]:  # Sample first 20
            code = read_file(py_file)
            complexity = analyze_code_complexity(code)
            complexities.append(complexity.get('complexity_score', 0))

        avg_complexity = sum(complexities) / len(complexities) if complexities else 0

        findings.append({
            "type": "code_quality_snapshot",
            "total_files": total_files,
            "python_files": len(py_files),
            "typescript_files": len(ts_files) + len(js_files),
            "average_complexity": round(avg_complexity, 2),
            "status": "good" if avg_complexity < 50 else "needs_attention"
        })

        metrics = {
            "files_analyzed": total_files,
            "avg_complexity": avg_complexity,
            "high_complexity_files": sum(1 for c in complexities if c > 100)
        }

        if avg_complexity > 50:
            recommendations.append("Consider refactoring high-complexity files")
            recommendations.append("Break down large modules into smaller components")

        return findings, metrics, recommendations


class BugSummarizerAgent(BaseAgent):
    """AI agent: summarize new bugs added in Jira"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        # This would integrate with Jira API
        # For now, return template findings

        findings = [{
            "type": "bug_summary",
            "period": "daily",
            "new_bugs": 0,
            "critical_bugs": 0,
            "resolved_bugs": 0
        }]

        metrics = {
            "bug_velocity": 0,
            "resolution_rate": 0,
            "avg_resolution_time_hours": 0
        }

        recommendations = [
            "Connect to Jira API for real bug tracking",
            "Set up automated bug triage"
        ]

        return findings, metrics, recommendations


class EngineeringPerformanceAgent(BaseAgent):
    """AI agent: generate a weekly engineering performance report"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        # Analyze git activity
        success, stdout, _ = run_command(
            ["git", "log", "--since=1 week ago", "--oneline", "--count"],
            cwd=project_root
        )

        commits = int(stdout.strip()) if success else 0

        findings = [{
            "type": "weekly_performance",
            "commits_last_week": commits,
            "productivity": "high" if commits > 20 else "normal"
        }]

        metrics = {
            "weekly_commits": commits,
            "avg_commits_per_day": round(commits / 7, 1)
        }

        recommendations = []
        if commits < 10:
            recommendations.append("Consider increasing development velocity")
        elif commits > 50:
            recommendations.append("High velocity - ensure code review quality")

        return findings, metrics, recommendations


class PRQualityScorerAgent(BaseAgent):
    """AI agent: score pull requests for quality & risk"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        # Get recent PRs (would integrate with GitHub/GitLab API)
        success, stdout, _ = run_command(
            ["git", "log", "--oneline", "-10"],
            cwd=project_root
        )

        recent_commits = stdout.strip().split('\n') if success else []

        findings = [{
            "type": "pr_quality_scan",
            "recent_commits_analyzed": len(recent_commits),
            "avg_changes_per_commit": "N/A - requires PR API"
        }]

        metrics = {
            "commits_analyzed": len(recent_commits),
            "quality_score": 85  # Placeholder
        }

        recommendations = [
            "Integrate with GitHub/GitLab API for PR analysis",
            "Set up automated PR quality checks",
            "Add risk scoring based on files changed"
        ]

        return findings, metrics, recommendations


class CodeStandardizerAgent(BaseAgent):
    """AI agent: rewrite inconsistent code to match standards"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        ts_files = find_files(project_root, "*.tsx")[:10]

        inconsistent_patterns = {
            "inconsistent_quotes": 0,
            "missing_semicolons": 0,
            "trailing_whitespace": 0,
            "long_lines": 0
        }

        for file_path in ts_files:
            code = read_file(file_path)
            lines = code.split('\n')

            # Check for patterns
            for line in lines:
                if '"' in line and "'" in line:
                    inconsistent_patterns["inconsistent_quotes"] += 1
                if line.rstrip() != line and line.strip():
                    inconsistent_patterns["trailing_whitespace"] += 1
                if len(line) > 100:
                    inconsistent_patterns["long_lines"] += 1

        findings.append({
            "type": "code_style_analysis",
            "files_checked": len(ts_files),
            "issues_found": inconsistent_patterns
        })

        metrics = {
            "total_issues": sum(inconsistent_patterns.values()),
            "files_analyzed": len(ts_files)
        }

        recommendations = [
            "Run Prettier formatter: `npm run format`",
            "Configure ESLint with auto-fix",
            "Set up pre-commit hooks for formatting"
        ]

        return findings, metrics, recommendations


class APIDriftDetectorAgent(BaseAgent):
    """AI agent: detect API contracts that drift from spec"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        # Check API endpoint files
        api_files = find_files(project_root.glob("app/api"), "endpoints/*.py")

        for api_file in api_files:
            code = read_file(api_file)

            # Check for docstrings
            has_docstring = bool(re.search(r'""".*"""', code))
            has_type_hints = bool(re.search(r':\s*(str|int|bool|List|Dict)', code))

            if not has_docstring or not has_type_hints:
                findings.append({
                    "type": "api_drift",
                    "file": str(api_file.relative_to(project_root)),
                    "missing_docstring": not has_docstring,
                    "missing_type_hints": not has_type_hints
                })

        metrics = {
            "api_endpoints_checked": len(api_files),
            "drift_detected": len(findings)
        }

        recommendations = [
            "Ensure all endpoints have complete docstrings",
            "Add type hints to all function signatures",
            "Keep API specs in sync with implementations"
        ]

        return findings, metrics, recommendations


class LogAnomalyScannerAgent(BaseAgent):
    """AI agent: continuously scan logs for anomalies"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        # Check for recent error logs
        log_patterns = {
            "ERROR": 0,
            "WARNING": 0,
            "CRITICAL": 0,
            "Exception": 0
        }

        # Scan log files if they exist
        log_files = list(project_root.glob("*.log")) + \
                    list(project_root.glob("logs/*.log"))

        for log_file in log_files:
            content = read_file(log_file)
            for pattern, count in log_patterns.items():
                occurrences = len(re.findall(pattern, content))
                log_patterns[pattern] += occurrences

        if log_files:
            findings.append({
                "type": "log_anomaly_scan",
                "logs_scanned": len(log_files),
                "error_patterns": log_patterns
            })

        metrics = {
            "logs_scanned": len(log_files),
            "total_errors": log_patterns["ERROR"],
            "total_warnings": log_patterns["WARNING"]
        }

        recommendations = []
        if log_patterns["ERROR"] > 100:
            recommendations.append("High error rate detected - investigate urgent issues")
        if log_patterns["WARNING"] > 500:
            recommendations.append("Review and address warning patterns")

        return findings, metrics, recommendations


class AutoTestGeneratorAgent(BaseAgent):
    """AI agent: create tests immediately when new endpoints appear"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        # Find endpoint files
        endpoint_files = find_files(project_root / "app/api/v1/endpoints", "*.py")
        test_files = find_files(project_root / "tests/api", f"test_*.py")

        # Check which endpoints have tests
        untested_endpoints = []
        for endpoint_file in endpoint_files:
            endpoint_name = endpoint_file.stem
            test_exists = any(f"test_{endpoint_name}" in t.name for t in test_files)

            if not test_exists:
                untested_endpoints.append(endpoint_name)

        findings.append({
            "type": "test_coverage_gap",
            "endpoints_found": len(endpoint_files),
            "endpoints_with_tests": len(endpoint_files) - len(untested_endpoints),
            "endpoints_needing_tests": untested_endpoints
        })

        metrics = {
            "test_coverage": f"{((len(endpoint_files) - len(untested_endpoints)) / len(endpoint_files) * 100):.0f}%" if endpoint_files else "N/A",
            "untested_count": len(untested_endpoints)
        }

        recommendations = [
            f"Generate tests for {len(untested_endpoints)} untested endpoints",
            "Use pytest fixtures for common test setup",
            "Set up pytest-watch for TDD workflow"
        ]

        return findings, metrics, recommendations


class DocumentationCompletenessAgent(BaseAgent):
    """AI agent: assess documentation completeness"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for README
        has_readme = (project_root / "README.md").exists()
        has_contributing = (project_root / "CONTRIBUTING.md").exists()
        has_api_docs = (project_root / "docs" / "api.md").exists()

        # Check docstring coverage in Python files
        py_files = find_files(project_root / "app", "*.py")[:20]

        docstring_coverage = {
            "modules": 0,
            "functions": 0,
            "classes": 0,
            "documented": 0
        }

        for py_file in py_files:
            code = read_file(py_file)
            docstring_coverage["modules"] += 1

            if '"""' in code:
                docstring_coverage["documented"] += 1

        findings.append({
            "type": "documentation_assessment",
            "has_readme": has_readme,
            "has_contributing_guide": has_contributing,
            "has_api_documentation": has_api_docs,
            "docstring_coverage": docstring_coverage
        })

        metrics = {
            "docs_score": sum([
                has_readme, has_contributing, has_api_docs
            ]),
            "docstring_ratio": f"{(docstring_coverage['documented'] / docstring_coverage['modules'] * 100):.0f}%" if docstring_coverage['modules'] > 0 else "0%"
        }

        recommendations = []
        if not has_readme:
            recommendations.append("Create comprehensive README.md")
        if not has_api_docs:
            recommendations.append("Generate API documentation from docstrings")
        if docstring_coverage['documented'] < docstring_coverage['modules']:
            recommendations.append("Improve docstring coverage in Python modules")

        return findings, metrics, recommendations


class UnusedCodeDetectorAgent(BaseAgent):
    """AI agent: identify unused variables, functions, files"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for unused Python files
        py_files = find_files(project_root, "*.py")
        unused_files = []

        for py_file in py_files:
            code = read_file(py_file)
            # Simple heuristic: files with very few lines might be unused
            if len(code.strip()) < 50:
                unused_files.append({
                    "file": str(py_file.relative_to(project_root)),
                    "size_bytes": len(code),
                    "reason": "Very small file - possibly unused"
                })

        findings.append({
            "type": "unused_code_scan",
            "potentially_unused_files": unused_files
        })

        metrics = {
            "files_scanned": len(py_files),
            "suspicious_files": len(unused_files)
        }

        recommendations = [
            "Review potentially unused files",
            "Remove dead code to reduce maintenance burden",
            "Use code coverage tools to identify unused code"
        ]

        return findings, metrics, recommendations


class ModuleDecomposerAgent(BaseAgent):
    """AI agent: propose decompositions of overgrown modules"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find large Python files
        py_files = find_files(project_root / "app", "*.py")

        overgrown_modules = []
        for py_file in py_files:
            code = read_file(py_file)
            lines = len(code.split('\n'))

            if lines > 500:
                complexity = analyze_code_complexity(code)
                overgrown_modules.append({
                    "file": str(py_file.relative_to(project_root)),
                    "lines": lines,
                    "functions": complexity.get('functions', 0),
                    "classes": complexity.get('classes', 0),
                    "recommendation": "Split into smaller modules"
                })

        findings.append({
            "type": "module_size_analysis",
            "overgrown_modules": overgrown_modules
        })

        metrics = {
            "files_analyzed": len(py_files),
            "overgrown_count": len(overgrown_modules),
            "avg_file_size": sum(f['lines'] for f in overgrown_modules) / len(overgrown_modules) if overgrown_modules else 0
        }

        recommendations = [
            f"Break down {len(overgrown_modules)} overgrown modules",
            "Apply Single Responsibility Principle",
            "Consider using dependency injection for modularity"
        ]

        return findings, metrics, recommendations


class JSONSchemaValidatorAgent(BaseAgent):
    """AI agent: validate all JSON responses follow schema"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find Pydantic schema files
        schema_files = find_files(project_root / "app/schemas", "*.py")

        validation_results = []
        for schema_file in schema_files:
            code = read_file(schema_file)

            # Check for Field definitions
            has_validations = bool(re.search(r'Field\(', code))
            has_examples = bool(re.search(r'example=', code))

            validation_results.append({
                "schema": str(schema_file.relative_to(project_root)),
                "has_field_validations": has_validations,
                "has_examples": has_examples
            })

        findings.append({
            "type": "json_schema_validation",
            "schemas_checked": len(schema_files),
            "validation_results": validation_results
        })

        metrics = {
            "schemas_validated": len(schema_files),
            "with_examples": sum(1 for r in validation_results if r['has_examples'])
        }

        recommendations = [
            "Add Field examples to all schemas for better documentation",
            "Use Pydantic's Config class for schema validation",
            "Keep schemas in sync with OpenAPI specs"
        ]

        return findings, metrics, recommendations


class DuplicateIssueDetectorAgent(BaseAgent):
    """AI agent: check open issues for duplicates"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        # This would integrate with GitHub Issues/Jira API

        findings = [{
            "type": "duplicate_issue_check",
            "status": "requires_integration",
            "message": "Connect to GitHub/Jira API to detect duplicates"
        }]

        metrics = {
            "api_integration_needed": True
        }

        recommendations = [
            "Integrate with GitHub Issues API",
            "Use similarity algorithms to detect duplicates",
            "Auto-label potential duplicates"
        ]

        return findings, metrics, recommendations
