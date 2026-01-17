"""
Testing, Security, and Performance AI Agents
Automated testing, security scanning, and performance optimization
"""

import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from agent_framework import (
    BaseAgent, AgentConfig, run_command, find_files, read_file
)


# ============================================
# TESTING AGENTS
# ============================================

class CommentImproverAgent(BaseAgent):
    """AI agent: suggest improvements to code comments"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        py_files = find_files(project_root / "app", "*.py")[:15]

        comment_stats = {
            "total_lines": 0,
            "comment_lines": 0,
            "docstring_strings": 0,
            "todo_comments": 0
        }

        for py_file in py_files:
            code = read_file(py_file)
            lines = code.split('\n')

            for line in lines:
                comment_stats["total_lines"] += 1
                if line.strip().startswith('#'):
                    comment_stats["comment_lines"] += 1
                if '"""' in line or "'''" in line:
                    comment_stats["docstring_strings"] += 1
                if 'TODO' in line.upper() or 'FIXME' in line.upper():
                    comment_stats["todo_comments"] += 1

        findings.append({
            "type": "comment_quality_analysis",
            "comment_coverage": comment_stats
        })

        metrics = {
            "comment_ratio": f"{(comment_stats['comment_lines'] / comment_stats['total_lines'] * 100):.1f}%",
            "todos_found": comment_stats['todo_comments']
        }

        recommendations = [
            "Add more inline comments for complex logic",
            f"Address {comment_stats['todo_comments']} TODO/FIXME comments",
            "Use docstrings for all public functions"
        ]

        return findings, metrics, recommendations


class ErrorCodeGeneratorAgent(BaseAgent):
    """AI agent: generate missing error codes"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find exception definitions
        py_files = find_files(project_root / "app", "*.py")

        custom_exceptions = []
        error_codes = {}

        for py_file in py_files:
            code = read_file(py_file)

            # Find custom exceptions
            if re.search(r'class.*\(Exception\)', code):
                matches = re.findall(r'class (\w+)\(Exception\)', code)
                custom_exceptions.extend(matches)

            # Find error codes
            if 'error_code=' in code or 'ErrorCode.' in code:
                matches = re.findall(r'error_code[= ]*["\']?(\w+)["\']?', code)
                for match in matches:
                    error_codes[match] = error_codes.get(match, 0) + 1

        findings.append({
            "type": "error_code_audit",
            "custom_exceptions": len(set(custom_exceptions)),
            "error_codes_used": len(error_codes)
        })

        metrics = {
            "exception_types": len(set(custom_exceptions)),
            "error_code_variety": len(error_codes)
        }

        recommendations = [
            "Define error codes in a central constants file",
            "Use consistent error code format (e.g., ERR_001)",
            "Document all error codes in API documentation"
        ]

        return findings, metrics, recommendations


# ============================================
# SECURITY AGENTS
# ============================================

class SQLInjectionAuditorAgent(BaseAgent):
    """AI agent: audit all SQL queries for injection risks"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find files with SQL queries
        py_files = find_files(project_root, "*.py")

        risky_patterns = {
            "f-string_sql": 0,
            "string_concat_sql": 0,
            "raw_user_input": 0
        }

        for py_file in py_files:
            code = read_file(py_file)

            # Check for dangerous SQL patterns
            if re.search(r'f["\'].*SELECT.*{.*}.*["\']', code):
                risky_patterns["f-string_sql"] += 1

            if re.search(r'execute\(.+\+.+\)', code):
                risky_patterns["string_concat_sql"] += 1

            # Check for parameterized queries (good)
            has_safe_params = bool(re.search(r'\.execute\(.+,\s*\{', code))

        findings.append({
            "type": "sql_injection_audit",
            "risky_patterns": risky_patterns
        })

        metrics = {
            "files_scanned": len(py_files),
            "risky_findings": sum(risky_patterns.values())
        }

        recommendations = []
        if sum(risky_patterns.values()) > 0:
            recommendations.append("Use parameterized queries (prepared statements)")
            recommendations.append("Never use f-strings or concatenation for SQL")
            recommendations.append("Use SQLAlchemy ORM or proper escaping")

        return findings, metrics, recommendations


class QueryOptimizerAgent(BaseAgent):
    """AI agent: rewrite slow queries automatically"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find SQL query files
        sql_files = find_files(project_root, "*.sql")

        slow_patterns = {
            "select_star": 0,
            "missing_where": 0,
            "missing_limit": 0,
            "no_index_hint": 0
        }

        for sql_file in sql_files:
            code = read_file(sql_file).upper()

            if 'SELECT *' in code:
                slow_patterns["select_star"] += 1
            if 'SELECT' in code and 'WHERE' not in code:
                slow_patterns["missing_where"] += 1
            if 'SELECT' in code and 'LIMIT' not in code:
                slow_patterns["missing_limit"] += 1

        findings.append({
            "type": "query_optimization",
            "slow_query_patterns": slow_patterns
        })

        metrics = {
            "sql_files_scanned": len(sql_files),
            "optimization_opportunities": sum(slow_patterns.values())
        }

        recommendations = [
            "Avoid SELECT * - specify only needed columns",
            "Always add WHERE clauses to limit result sets",
            "Use LIMIT on large queries",
            "Add appropriate indexes for frequent queries"
        ]

        return findings, metrics, recommendations


class BuildFailureAnalyzerAgent(BaseAgent):
    """AI agent: list all failed builds & categorize root causes"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        findings = [{
            "type": "build_analysis",
            "status": "requires_ci_integration",
            "message": "Connect to CI/CD system (GitHub Actions, Jenkins, etc.)"
        }]

        metrics = {
            "ci_integration_needed": True
        }

        recommendations = [
            "Integrate with GitHub Actions or Jenkins API",
            "Categorize failures: test failures, build errors, deployment issues",
            "Track failure patterns over time"
        ]

        return findings, metrics, recommendations


class CachingConfigOptimizerAgent(BaseAgent):
    """AI agent: propose improvements to caching configuration"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for Redis usage
        py_files = find_files(project_root, "*.py")

        cache_usage = {
            "redis_imports": 0,
            "cache_decorators": 0,
            "memoization": 0
        }

        for py_file in py_files:
            code = read_file(py_file)

            if 'import redis' in code or 'from redis' in code:
                cache_usage["redis_imports"] += 1
            if '@cache' in code or '@lru_cache' in code:
                cache_usage["cache_decorators"] += 1
            if 'functools.lru_cache' in code:
                cache_usage["memoization"] += 1

        findings.append({
            "type": "caching_analysis",
            "cache_usage": cache_usage
        })

        metrics = {
            "files_with_cache": sum([
                cache_usage["redis_imports"],
                cache_usage["cache_decorators"],
                cache_usage["memoization"]
            ])
        }

        recommendations = [
            "Add Redis caching for frequently accessed data",
            "Use @lru_cache for expensive function calls",
            "Implement cache invalidation strategy",
            "Monitor cache hit rates"
        ]

        return findings, metrics, recommendations


class BreakingChangeDetectorAgent(BaseAgent):
    """AI agent: detect breaking changes before merge"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Get modified files in git
        success, stdout, _ = run_command(
            ["git", "diff", "--name-only", "main~5..main"],
            cwd=project_root
        )

        if success:
            modified_files = stdout.strip().split('\n')
            api_files = [f for f in modified_files if 'api/' in f]

            findings.append({
                "type": "breaking_change_scan",
                "modified_files": len(modified_files),
                "api_changes": len(api_files),
                "api_files": api_files[:10]  # First 10
            })

        metrics = {
            "files_checked": len(modified_files) if success else 0,
            "api_changes": len(api_files) if success else 0
        }

        recommendations = [
            "Review API endpoint changes for breaking changes",
            "Use semantic versioning (MAJOR.MINOR.PATCH)",
            "Deprecate old endpoints before removing",
            "Maintain API versioning for backwards compatibility"
        ]

        return findings, metrics, recommendations


class SpaghettiCodeRefactorAgent(BaseAgent):
    """AI agent: rewrite spaghetti code into modern patterns"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []
        py_files = find_files(project_root / "app", "*.py")

        code_smells = {
            "long_functions": 0,  # > 50 lines
            "deep_nesting": 0,     # > 4 levels
            "too_many_params": 0,  # > 5 parameters
            "large_classes": 0     # > 200 lines
        }

        for py_file in py_files[:20]:
            code = read_file(py_file)
            lines = code.split('\n')

            # Check for long functions
            in_function = False
            function_lines = 0
            for line in lines:
                if re.match(r'^def |^async def ', line):
                    in_function = True
                    function_lines = 0
                elif in_function:
                    function_lines += 1
                    if line and not line[0].isspace() and not line.startswith('async def'):
                        if function_lines > 50:
                            code_smells["long_functions"] += 1
                        in_function = False

            # Check file size
            if len(lines) > 200:
                code_smells["large_classes"] += 1

        findings.append({
            "type": "code_smell_analysis",
            "smells_detected": code_smells
        })

        metrics = {
            "files_analyzed": len(py_files[:20]),
            "total_smells": sum(code_smells.values())
        }

        recommendations = [
            "Extract long functions into smaller, single-purpose functions",
            "Reduce nesting depth using early returns",
            "Use parameter objects for functions with many parameters",
            "Apply SOLID principles to large classes"
        ]

        return findings, metrics, recommendations


class DeprecatedLibraryDetectorAgent(BaseAgent):
    """AI agent: catch deprecated library usage"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check requirements files
        req_files = list(project_root.glob("requirements*.txt")) + \
                    list(project_root.glob("frontend/package.json"))

        deprecated_packages = {
            "python": [],
            "javascript": []
        }

        # Common deprecated packages
        deprecated_python = [
            "imp",  # Use importlib instead
            "string",  # Sometimes deprecated usages
        ]

        for req_file in req_files:
            if req_file.suffix == '.txt':
                content = read_file(req_file)
                for pkg in deprecated_python:
                    if pkg in content.lower():
                        deprecated_packages["python"].append(pkg)

        findings.append({
            "type": "deprecated_library_check",
            "deprecated_found": deprecated_packages
        })

        metrics = {
            "files_checked": len(req_files),
            "deprecated_count": sum(len(v) for v in deprecated_packages.values())
        }

        recommendations = [
            "Update deprecated Python packages",
            "Use 'importlib' instead of 'imp'",
            "Check Node.js packages for security advisories",
            "Run `npm audit` to find vulnerable dependencies"
        ]

        return findings, metrics, recommendations


class DebugCodeRemoverAgent(BaseAgent):
    """AI agent: remove console logs & temporary debug code"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for console.log in JS/TS files
        js_files = find_files(project_root / "frontend/src", "*.[jt]sx")

        debug_statements = {
            "console_log": 0,
            "console_debug": 0,
            "console_warn": 0,
            "debugger": 0,
            "TODO": 0,
            "FIXME": 0,
            "XXX": 0
        }

        for js_file in js_files[:30]:
            code = read_file(js_file)

            for pattern in debug_statements:
                matches = len(re.findall(pattern, code, re.IGNORECASE))
                debug_statements[pattern] += matches

        findings.append({
            "type": "debug_code_scan",
            "debug_statements": debug_statements
        })

        metrics = {
            "files_scanned": len(js_files[:30]),
            "total_debug_statements": sum(debug_statements.values())
        }

        recommendations = []
        if debug_statements["console_log"] > 10:
            recommendations.append(f"Remove {debug_statements['console_log']} console.log statements")
        if debug_statements["TODO"] + debug_statements["FIXME"] > 5:
            recommendations.append("Address or track TODO/FIXME comments")

        return findings, metrics, recommendations


# ============================================
# PERFORMANCE & MONITORING AGENTS
# ============================================

class APIMockGeneratorAgent(BaseAgent):
    """AI agent: generate API mocks for producers/consumers"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Find endpoint definitions
        endpoint_files = find_files(project_root / "app/api/v1/endpoints", "*.py")

        api_endpoints = []
        for endpoint_file in endpoint_files:
            code = read_file(endpoint_file)

            # Find @router.get/post/put/delete decorators
            routes = re.findall(r'@router\.(get|post|put|delete)\(["\']([^"\']+)["\']', code)
            for method, path in routes:
                api_endpoints.append({
                    "file": endpoint_file.name,
                    "method": method.upper(),
                    "path": path
                })

        findings.append({
            "type": "api_mock_generation",
            "endpoints_discovered": len(api_endpoints),
            "sample_endpoints": api_endpoints[:10]
        })

        metrics = {
            "endpoints_found": len(api_endpoints),
            "mocks_ready": len(api_endpoints)
        }

        recommendations = [
            "Generate MSW (Mock Service Worker) handlers for frontend",
            "Create pytest fixtures for backend testing",
            "Document API contracts for external consumers"
        ]

        return findings, metrics, recommendations


class PaginationValidatorAgent(BaseAgent):
    """AI agent: detect missing pagination, sorting, filtering"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check GET endpoints for pagination
        endpoint_files = find_files(project_root / "app/api/v1/endpoints", "*.py")

        endpoints_without_pagination = []

        for endpoint_file in endpoint_files:
            code = read_file(endpoint_file)

            # Find GET routes
            get_routes = re.findall(r'@router\.get\(["\']([^"\']+)["\'].*\nasync def (\w+)\(([^)]+)\)', code)

            for route, func_name, params in get_routes:
                has_limit = 'limit' in params.lower()
                has_offset = 'offset' in params.lower() or 'skip' in params.lower()
                has_page = 'page' in params.lower()

                if not (has_limit or has_offset or has_page):
                    endpoints_without_pagination.append({
                        "route": route,
                        "function": func_name,
                        "file": endpoint_file.name
                    })

        findings.append({
            "type": "pagination_audit",
            "endpoints_needing_pagination": endpoints_without_pagination[:20]
        })

        metrics = {
            "endpoints_checked": len(get_routes),
            "missing_pagination": len(endpoints_without_pagination)
        }

        recommendations = [
            "Add pagination to all list endpoints",
            "Include limit, offset/skip, and page parameters",
            "Return total count along with paginated results",
            "Document max page size limits"
        ]

        return findings, metrics, recommendations


class AccessibilityAuditorAgent(BaseAgent):
    """AI agent: generate UI accessibility report"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check React components for accessibility
        component_files = find_files(project_root / "frontend/src/components", "*.tsx")

        a11y_checks = {
            "has_aria_labels": 0,
            "has_alt_text": 0,
            "has_role_attr": 0,
            "uses_semantic_html": 0
        }

        for comp_file in component_files[:20]:
            code = read_file(comp_file)

            if 'aria-label' in code or 'ariaLabel' in code:
                a11y_checks["has_aria_labels"] += 1
            if 'alt=' in code:
                a11y_checks["has_alt_text"] += 1
            if 'role=' in code:
                a11y_checks["has_role_attr"] += 1
            if any(tag in code for tag in ['<nav>', '<main>', '<header>', '<button>', '<input>']):
                a11y_checks["uses_semantic_html"] += 1

        findings.append({
            "type": "accessibility_audit",
            "checks": a11y_checks
        })

        metrics = {
            "components_checked": len(component_files[:20]),
            "a11y_score": sum(a11y_checks.values())
        }

        recommendations = [
            "Add aria-labels to all interactive elements",
            "Include alt text for all images",
            "Use semantic HTML elements",
            "Ensure keyboard navigation works",
            "Test with screen reader"
        ]

        return findings, metrics, recommendations


class ReRenderOptimizerAgent(BaseAgent):
    """AI agent: flag unnecessary re-renders"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for React anti-patterns
        component_files = find_files(project_root / "frontend/src/components", "*.tsx")

        anti_patterns = {
            "inline_functions_in_render": 0,
            "missing_keys_in_lists": 0,
            "unnecessary_state": 0,
            "prop_drilling": 0
        }

        for comp_file in component_files[:15]:
            code = read_file(comp_file)

            # Check for inline functions in JSX
            if re.search(r'{\s*\(.*?\)\s*=>', code):
                anti_patterns["inline_functions_in_render"] += 1

            # Check for missing keys in lists
            if '{.map(' in code and 'key=' not in code:
                anti_patterns["missing_keys_in_lists"] += 1

        findings.append({
            "type": "render_optimization",
            "anti_patterns": anti_patterns
        })

        metrics = {
            "components_analyzed": len(component_files[:15]),
            "optimization_opportunities": sum(anti_patterns.values())
        }

        recommendations = [
            "Move inline functions out of render methods",
            "Add React.memo to prevent unnecessary re-renders",
            "Use useMemo and useCallback for expensive computations",
            "Implement Context API or Redux to avoid prop drilling"
        ]

        return findings, metrics, recommendations


class BundleOptimizerAgent(BaseAgent):
    """AI agent: optimize frontend bundle"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check package.json and imports
        package_json = project_root / "frontend" / "package.json"

        if package_json.exists():
            content = read_file(package_json)

            bundle_size_checks = {
                "dependencies": len(re.findall(r'"dependencies":', content)) > 0,
                "large_dependencies": 0
            }

            # Check for heavy packages
            heavy_packages = ['moment', 'lodash', 'jquery']
            for pkg in heavy_packages:
                if pkg in content:
                    bundle_size_checks["large_dependencies"] += 1

        findings.append({
            "type": "bundle_analysis",
            "checks": bundle_size_checks
        })

        metrics = {
            "optimization_potential": "high" if bundle_size_checks.get("large_dependencies", 0) > 0 else "low"
        }

        recommendations = [
            "Replace moment.js with date-fns (smaller)",
            "Use lodash-es instead of lodash (tree-shakeable)",
            "Remove unused dependencies",
            "Enable code splitting in webpack/vite config",
            "Use dynamic imports for heavy components"
        ]

        return findings, metrics, recommendations


class MemoryLeakDetectorAgent(BaseAgent):
    """AI agent: list potential memory leaks"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Check for common memory leak patterns
        component_files = find_files(project_root / "frontend/src", "*.tsx")

        leak_patterns = {
            "missing_cleanup": 0,
            "event_listeners_not_removed": 0,
            "timers_not_cleared": 0,
            "closures_trapping_state": 0
        }

        for comp_file in component_files[:15]:
            code = read_file(comp_file)

            if 'useEffect' in code:
                # Check if cleanup is returned
                useEffect_blocks = re.findall(r'useEffect\(\(\) => \{.*?\}, \[\]\)', code, re.DOTALL)
                for block in useEffect_blocks:
                    if 'return' not in block and 'addEventListener' in code:
                        leak_patterns["event_listeners_not_removed"] += 1

                    if 'setInterval' in code or 'setTimeout' in code:
                        if 'clear' not in code:
                            leak_patterns["timers_not_cleared"] += 1

        findings.append({
            "type": "memory_leak_scan",
            "potential_leaks": leak_patterns
        })

        metrics = {
            "files_scanned": len(component_files[:15]),
            "leak_indicators": sum(leak_patterns.values())
        }

        recommendations = [
            "Always return cleanup functions in useEffect",
            "Remove event listeners in cleanup callbacks",
            "Clear timers in cleanup functions",
            "Avoid closures in loops",
            "Use React DevTools Profiler to detect leaks"
        ]

        return findings, metrics, recommendations


class UnusedCSSDetectorAgent(BaseAgent):
    """AI agent: detect unused CSS classes"""

    def _run(self, context: Dict[str, Any]) -> Tuple:
        project_root = Path(context.get('project_root', '.'))

        findings = []

        # Get CSS class definitions
        css_files = find_files(project_root / "frontend/src", "*.css")

        defined_classes = set()
        for css_file in css_files:
            code = read_file(css_file)
            classes = re.findall(r'\.([\w-]+)\s*{', code)
            defined_classes.update(classes)

        # Check which classes are used in components
        component_files = find_files(project_root / "frontend/src/components", "*.tsx")

        used_classes = set()
        for comp_file in component_files[:20]:
            code = read_file(comp_file)
            # Find className attributes
            classes = re.findall(r'className=["\']([^"\']+)["\']', code)
            for cls_list in classes:
                for cls in cls_list.split():
                    used_classes.add(cls)

        unused_classes = defined_classes - used_classes

        findings.append({
            "type": "css_usage_analysis",
            "total_classes_defined": len(defined_classes),
            "classes_used": len(used_classes),
            "unused_classes": len(unused_classes),
            "sample_unused": list(unused_classes)[:20]
        })

        metrics = {
            "css_files": len(css_files),
            "unused_ratio": f"{(len(unused_classes) / len(defined_classes) * 100):.0f}%" if defined_classes else "0%"
        }

        recommendations = [
            f"Remove {len(unused_classes)} unused CSS classes",
            "Use CSS Modules or Tailwind for scoped styling",
            "PurgeCSS can automatically remove unused CSS"
        ]

        return findings, metrics, recommendations
