#!/usr/bin/env python3
"""
API Authentication Security Fix Script
Ensures all API endpoints have proper authentication implemented
"""

import re
import ast
from pathlib import Path
from typing import List, Dict, Any, Set
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class APIAuthenticationFixer:
    def __init__(self):
        self.endpoints_path = Path("app/api/v1/endpoints")
        self.security_issues = []
        self.fixed_files = []

    def analyze_endpoint_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single endpoint file for authentication issues"""
        issues = []
        endpoints = []

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Parse the Python file
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                issues.append(f"Syntax error in file: {e}")
                return {"file": str(file_path), "issues": issues, "endpoints": endpoints}

            # Find all route decorators and check authentication
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function has route decorator
                    route_decorators = []
                    auth_dependencies = []

                    for decorator in node.decorator_list:
                        # Check for @router.get, @router.post, etc.
                        if (isinstance(decorator, ast.Attribute) and
                            isinstance(decorator.value, ast.Name) and
                            decorator.value.id == 'router'):
                            route_decorators.append(ast.unparse(decorator))

                    # Check function arguments for authentication
                    for arg in node.args.args:
                        if (arg.annotation and
                            isinstance(arg.annotation, ast.Attribute) and
                            'get_current' in ast.unparse(arg.annotation)):
                            auth_dependencies.append(ast.unparse(arg.annotation))

                    # If it has route decorators but no auth dependencies, it's a security issue
                    if route_decorators and not auth_dependencies:
                        # Skip if function name suggests it's for authentication itself
                        if not any(skip_word in node.name.lower()
                                 for skip_word in ['login', 'token', 'auth', 'register']):
                            endpoint_info = {
                                "function": node.name,
                                "routes": route_decorators,
                                "file": str(file_path.relative_to(Path.cwd())),
                                "line": node.lineno
                            }
                            endpoints.append(endpoint_info)
                            issues.append(f"Endpoint '{node.name}' has routes but no authentication")

            return {
                "file": str(file_path.relative_to(Path.cwd())),
                "issues": issues,
                "endpoints": endpoints
            }

        except Exception as e:
            issues.append(f"Error analyzing file: {e}")
            return {"file": str(file_path), "issues": issues, "endpoints": endpoints}

    def scan_all_endpoints(self) -> List[Dict[str, Any]]:
        """Scan all endpoint files for authentication issues"""
        logger.info("🔍 Scanning all API endpoint files for authentication issues...")

        all_issues = []
        endpoint_files = list(self.endpoints_path.glob("*.py"))

        for file_path in endpoint_files:
            # Skip certain files that are meant to be public or for testing
            skip_files = [
                'auth.py', 'auth_fixed.py', 'auth_original_backup.py',
                'standalone_auth.py', 'simple_auth.py'
            ]

            if file_path.name in skip_files:
                logger.info(f"⏭️  Skipping {file_path.name} (authentication file)")
                continue

            logger.info(f"📋 Analyzing {file_path.name}...")
            result = self.analyze_endpoint_file(file_path)

            if result["issues"]:
                all_issues.append(result)
                self.security_issues.extend(result["issues"])

        return all_issues

    def generate_security_report(self, issues: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive security report"""
        report = []
        report.append("🔐 API AUTHENTICATION SECURITY AUDIT REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        total_files = len(issues)
        total_endpoints_without_auth = sum(len(issue.get("endpoints", [])) for issue in issues)

        report.append(f"📊 SUMMARY:")
        report.append(f"   Files with issues: {total_files}")
        report.append(f"   Endpoints without authentication: {total_endpoints_without_auth}")
        report.append(f"   Risk Level: {'HIGH' if total_endpoints_without_auth > 0 else 'LOW'}")
        report.append("")

        if issues:
            report.append("🚨 SECURITY ISSUES FOUND:")
            report.append("")

            for file_issue in issues:
                if file_issue["endpoints"]:
                    report.append(f"📁 FILE: {file_issue['file']}")

                    for endpoint in file_issue["endpoints"]:
                        report.append(f"   ❌ Endpoint: {endpoint['function']} (line {endpoint['line']})")
                        for route in endpoint["routes"]:
                            report.append(f"      Route: {route}")
                        report.append(f"      Fix: Add 'current_user: User = Depends(get_current_active_user)' parameter")

                    report.append("")
        else:
            report.append("✅ No authentication issues found!")
            report.append("   All endpoints have proper authentication implemented.")

        report.append("")
        report.append("🔧 RECOMMENDED ACTIONS:")
        report.append("1. Add authentication dependencies to all identified endpoints")
        report.append("2. Use get_current_active_user for standard user authentication")
        report.append("3. Use get_current_admin_user for admin-only endpoints")
        report.append("4. Consider implementing role-based access control (RBAC)")
        report.append("5. Add rate limiting to prevent brute force attacks")

        return "\n".join(report)

    def create_authentication_fix_template(self, issues: List[Dict[str, Any]]) -> str:
        """Create a template file with authentication fixes"""
        template = []
        template.append("#!/usr/bin/env python3")
        template.append('"""')
        template.append("API Authentication Fixes")
        template.append("Generated automatically - review before applying")
        template.append('"""')
        template.append("")
        template.append("# Add these imports to files that need authentication:")
        template.append("from app.api.v1.deps import get_current_active_user, get_current_admin_user")
        template.append("from app.db.models.user import User")
        template.append("")
        template.append("# Example fixes for endpoints missing authentication:")
        template.append("")

        for file_issue in issues:
            if file_issue["endpoints"]:
                template.append(f"# FILE: {file_issue['file']}")

                for endpoint in file_issue["endpoints"]:
                    template.append(f"# ENDPOINT: {endpoint['function']}")
                    template.append("# BEFORE:")
                    template.append(f"# async def {endpoint['function']}(")
                    template.append("#     request: Request")
                    template.append("#     db: AsyncSession = Depends(get_db)")
                    template.append("")
                    template.append("# AFTER:")
                    template.append(f"# async def {endpoint['function']}(")
                    template.append("#     request: Request")
                    template.append("#     db: AsyncSession = Depends(get_db)")
                    template.append("#     current_user: User = Depends(get_current_active_user)")
                    template.append("")

        template.append("# Apply these changes manually or use automated refactoring tools")
        template.append("# Test all endpoints after applying authentication fixes")

        return "\n".join(template)

    def run_security_audit(self):
        """Run the complete security audit"""
        logger.info("🚀 Starting API Authentication Security Audit...")

        # Scan all endpoints
        issues = self.scan_all_endpoints()

        # Generate reports
        security_report = self.generate_security_report(issues)
        fix_template = self.create_authentication_fix_template(issues)

        # Save reports
        with open("api_authentication_audit_report.txt", "w") as f:
            f.write(security_report)

        with open("api_authentication_fix_template.py", "w") as f:
            f.write(fix_template)

        # Display summary
        total_endpoints_without_auth = sum(len(issue.get("endpoints", [])) for issue in issues)

        print("\n" + "=" * 60)
        print("🔐 API AUTHENTICATION SECURITY AUDIT RESULTS")
        print("=" * 60)
        print(f"📁 Files analyzed: {len(list(self.endpoints_path.glob('*.py')))}")
        print(f"🚨 Files with issues: {len(issues)}")
        print(f"❌ Endpoints without authentication: {total_endpoints_without_auth}")
        print(f"📊 Risk Level: {'HIGH' if total_endpoints_without_auth > 0 else 'LOW'}")

        if total_endpoints_without_auth > 0:
            print(f"\n🚨 CRITICAL: Found {total_endpoints_without_auth} endpoints without authentication!")
            print(f"📄 Detailed report saved to: api_authentication_audit_report.txt")
            print(f"🔧 Fix template saved to: api_authentication_fix_template.py")
        else:
            print("\n✅ EXCELLENT: All endpoints have proper authentication!")

        print("\n" + "=" * 60)

        return issues

def main():
    """Main execution function"""
    fixer = APIAuthenticationFixer()
    issues = fixer.run_security_audit()

    if issues:
        logger.warning("⚠️  Authentication issues found - please review the generated reports")
        return 1
    else:
        logger.info("✅ No authentication issues found")
        return 0

if __name__ == "__main__":
    from datetime import datetime
    exit(main())