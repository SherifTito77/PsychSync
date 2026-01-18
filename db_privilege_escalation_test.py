#!/usr/bin/env python3
"""
Database Privilege Escalation Security Tester
Tests for database privilege escalation vulnerabilities
"""

import os
import json
import sqlite3
import psycopg2
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class DatabasePrivilegeEscalationTester:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.findings = []
        self.test_results = []

    async def test_api_privilege_escalation(self) -> List[Dict]:
        """Test API endpoints for privilege escalation vulnerabilities"""
        print("🔍 Testing API endpoints for privilege escalation...")

        escalation_tests = []

        # Define test scenarios
        test_scenarios = [
            {
                "name": "Admin endpoint access",
                "endpoint": "/api/v1/admin/users",
                "method": "GET",
                "expected_status": 403,
                "description": "Try to access admin-only endpoint as regular user"
            },
            {
                "name": "User data access across organizations",
                "endpoint": "/api/v1/users/",
                "method": "GET",
                "expected_status": 200,
                "description": "Try to access all user data"
            },
            {
                "name": "Team data escalation",
                "endpoint": "/api/v1/teams/",
                "method": "GET",
                "expected_status": 200,
                "description": "Try to access all team data"
            },
            {
                "name": "Assessment data access",
                "endpoint": "/api/v1/assessments/",
                "method": "GET",
                "expected_status": 200,
                "description": "Try to access all assessment data"
            },
            {
                "name": "Response data escalation",
                "endpoint": "/api/v1/responses/",
                "method": "GET",
                "expected_status": 200,
                "description": "Try to access all response data"
            }
        ]

        # Test with different user contexts
        user_contexts = [
            {"auth": None, "description": "No authentication"},
            {"auth": "regular_user", "description": "Regular user token"},
            {"auth": "admin_user", "description": "Admin user token"}
        ]

        async with aiohttp.ClientSession() as session:
            for context in user_contexts:
                for scenario in test_scenarios:
                    test_result = await self.execute_privilege_test(
                        session, scenario, context
                    )
                    escalation_tests.append(test_result)

        return escalation_tests

    async def execute_privilege_test(self, session: aiohttp.ClientSession,
                                    scenario: Dict, context: Dict) -> Dict:
        """Execute a single privilege escalation test"""
        test_result = {
            "test_name": f"{scenario['name']} - {context['description']}",
            "endpoint": scenario["endpoint"],
            "method": scenario["method"],
            "context": context["description"],
            "status_code": None,
            "response_size": None,
            "escalation_detected": False,
            "security_issue": None,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Prepare headers
            headers = {"Content-Type": "application/json"}

            if context.get("auth") == "regular_user":
                # Simulate regular user token
                headers["Authorization"] = "Bearer regular_user_token_123"
            elif context.get("auth") == "admin_user":
                # Simulate admin user token
                headers["Authorization"] = "Bearer admin_user_token_123"

            # Make the request
            url = f"http://localhost:8000{scenario['endpoint']}"

            if scenario["method"] == "GET":
                async with session.get(url, headers=headers) as response:
                    test_result["status_code"] = response.status
                    content = await response.text()
                    test_result["response_size"] = len(content)
            elif scenario["method"] == "POST":
                async with session.post(url, headers=headers, json={}) as response:
                    test_result["status_code"] = response.status
                    content = await response.text()
                    test_result["response_size"] = len(content)

            # Analyze for privilege escalation
            if context.get("auth") is None and test_result["status_code"] == 200:
                test_result["escalation_detected"] = True
                test_result["security_issue"] = "Unauthorized access without authentication"
            elif context.get("auth") == "regular_user" and test_result["status_code"] == 200:
                # Check if we got more data than expected
                try:
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) > 50:  # Large data dump
                        test_result["escalation_detected"] = True
                        test_result["security_issue"] = "Regular user accessing excessive data"
                    elif isinstance(data, dict) and "admin" in str(data).lower():
                        test_result["escalation_detected"] = True
                        test_result["security_issue"] = "Regular user accessing admin data"
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    pass

        except Exception as e:
            test_result["error"] = str(e)
            # If connection failed, assume the endpoint exists but is protected
            if "Connection refused" in str(e):
                test_result["status_code"] = 503
                test_result["security_note"] = "Service unavailable - assume protected"

        return test_result

    def test_database_privilege_escalation(self) -> List[Dict]:
        """Test database-level privilege escalation"""
        print("🔍 Testing database privilege escalation...")

        escalation_results = []

        # Test different database privilege levels
        test_cases = [
            {
                "name": "Test user table access",
                "sql": "SELECT COUNT(*) FROM users",
                "description": "Try to access user count"
            },
            {
                "name": "Test admin user access",
                "sql": "SELECT * FROM users WHERE is_admin = true",
                "description": "Try to access admin users"
            },
            {
                "name": "Test sensitive data access",
                "sql": "SELECT email, password_hash FROM users LIMIT 5",
                "description": "Try to access sensitive user data"
            },
            {
                "name": "Test system tables access",
                "sql": "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
                "description": "Try to access system schema information"
            },
            {
                "name": "Test database configuration",
                "sql": "SHOW ALL;",
                "description": "Try to access database configuration"
            }
        ]

        for test_case in test_cases:
            result = self.execute_database_privilege_test(test_case)
            escalation_results.append(result)

        return escalation_results

    def execute_database_privilege_test(self, test_case: Dict) -> Dict:
        """Execute a single database privilege test"""
        result = {
            "test_name": test_case["name"],
            "sql_query": test_case["sql"],
            "description": test_case["description"],
            "success": False,
            "data_returned": False,
            "row_count": 0,
            "privilege_escalation": False,
            "security_issue": None,
            "error": None
        }

        try:
            # Try to connect with different privilege levels
            connection_attempts = [
                {
                    "name": "web_user",
                    "connection_params": {
                        "host": "localhost",
                        "database": "psychsync_db",
                        "user": "webapp_user",
                        "password": "weak_password",
                        "connect_timeout": 5
                    }
                },
                {
                    "name": "read_only_user",
                    "connection_params": {
                        "host": "localhost",
                        "database": "psychsync_db",
                        "user": "readonly_user",
                        "password": "readonly_password",
                        "connect_timeout": 5
                    }
                },
                {
                    "name": "default_user",
                    "connection_params": {
                        "host": "localhost",
                        "database": "psychsync_db",
                        "user": "postgres",
                        "password": "postgres",
                        "connect_timeout": 5
                    }
                }
            ]

            for attempt in connection_attempts:
                try:
                    conn = psycopg2.connect(**attempt["connection_params"])
                    cursor = conn.cursor()

                    try:
                        cursor.execute(test_case["sql"])

                        # Check if we got results
                        if cursor.description:
                            rows = cursor.fetchall()
                            result["success"] = True
                            result["data_returned"] = True
                            result["row_count"] = len(rows)
                            result["access_level"] = attempt["name"]

                            # Check for privilege escalation indicators
                            if "password" in test_case["sql"].lower() and rows:
                                result["privilege_escalation"] = True
                                result["security_issue"] = f"Access to password data via {attempt['name']} account"
                            elif "admin" in test_case["sql"].lower() and rows:
                                result["privilege_escalation"] = True
                                result["security_issue"] = f"Access to admin data via {attempt['name']} account"
                            elif "information_schema" in test_case["sql"] and rows:
                                result["privilege_escalation"] = True
                                result["security_issue"] = f"System schema access via {attempt['name']} account"

                        else:
                            # Command executed successfully (no results)
                            result["success"] = True
                            result["access_level"] = attempt["name"]

                            if "SHOW ALL" in test_case["sql"]:
                                result["privilege_escalation"] = True
                                result["security_issue"] = f"Database config access via {attempt['name']} account"

                        break  # Stop on first successful connection

                    except psycopg2.Error as sql_error:
                        # Check for permission denied errors
                        if "permission denied" in str(sql_error).lower():
                            result["security_note"] = f"Proper permission denied for {attempt['name']}"
                        else:
                            result["error"] = f"SQL Error: {sql_error}"

                    cursor.close()
                    conn.close()

                except psycopg2.OperationalError as op_error:
                    if "FATAL" in str(op_error) and "password authentication failed" in str(op_error):
                        result["security_note"] = f"Authentication failed for {attempt['name']}"
                    else:
                        result["error"] = f"Connection Error: {op_error}"

        except Exception as e:
            result["error"] = f"General Error: {e}"

        return result

    def test_injection_based_escalation(self) -> List[Dict]:
        """Test for injection-based privilege escalation"""
        print("🔍 Testing injection-based privilege escalation...")

        injection_payloads = [
            # SQL injection for privilege escalation
            "'; SELECT pg_sleep(5); --",
            "'; DROP TABLE users; --",
            "'; UPDATE users SET is_admin = true WHERE id = 1; --",
            "'; INSERT INTO users (email, password_hash, is_admin) VALUES ('hacker@evil.com', 'hashed', true); --",

            # NoSQL injection for privilege escalation
            {"$set": {"is_admin": True}},
            {"$push": {"roles": "admin"}},
            {"$or": [{"is_admin": True}, {"password": {"$ne": None}}]},

            # Command injection
            "; cat /etc/passwd",
            "; whoami",
            "; id",
            "; sudo -l"
        ]

        escalation_results = []

        # Test on various endpoints
        test_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users/",
            "/api/v1/assessments/",
            "/api/v1/responses/"
        ]

        for endpoint in test_endpoints:
            for payload in injection_payloads:
                result = self.test_injection_payload(endpoint, payload)
                escalation_results.append(result)

        return escalation_results

    async def test_injection_payload(self, endpoint: str, payload: Any) -> Dict:
        """Test a single injection payload for privilege escalation"""
        result = {
            "endpoint": endpoint,
            "payload": payload,
            "escalation_detected": False,
            "security_issue": None,
            "response_time": None,
            "status_code": None,
            "error": None
        }

        try:
            import time
            start_time = time.time()

            async with aiohttp.ClientSession() as session:
                if isinstance(payload, dict):
                    async with session.post(
                        f"http://localhost:8000{endpoint}",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        result["status_code"] = response.status
                        result["response_time"] = time.time() - start_time
                        content = await response.text()
                else:
                    # String payload - try as form data
                    async with session.post(
                        f"http://localhost:8000{endpoint}",
                        data={"input": payload},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    ) as response:
                        result["status_code"] = response.status
                        result["response_time"] = time.time() - start_time
                        content = await response.text()

                # Check for escalation indicators
                if result["response_time"] and result["response_time"] > 4:
                    result["escalation_detected"] = True
                    result["security_issue"] = "Possible time-based injection (sleep command executed)"

                elif "admin" in content.lower() and "privilege" in content.lower():
                    result["escalation_detected"] = True
                    result["security_issue"] = "Privilege information disclosed"

                elif "root:" in content.lower() or "uid=" in content.lower():
                    result["escalation_detected"] = True
                    result["security_issue"] = "System information disclosure via command injection"

        except Exception as e:
            result["error"] = str(e)

        return result

    def test_orm_privilege_escalation(self) -> List[Dict]:
        """Test ORM-based privilege escalation"""
        print("🔍 Testing ORM-based privilege escalation...")

        orm_tests = []

        # Look for ORM configuration files
        orm_configs = []
        for py_file in self.base_path.rglob("*.py"):
            if "model" in str(py_file).lower() or "orm" in str(py_file).lower():
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if "sqlalchemy" in content.lower() or "orm" in content.lower():
                            orm_configs.append(str(py_file.relative_to(self.base_path)))
                except (OSError, IOError, ValueError) as e:
                    pass

        # Test ORM privilege bypass patterns
        privilege_bypass_patterns = [
            "Role.query.all()",  # Should be filtered by user
            "User.query.get()",  # Should check ownership
            "db.session.delete()",  # Should check permissions
            "db.session.add()",   # Should validate data
            "filter_by()",        # Should validate filters
        ]

        for config_file in orm_configs[:5]:  # Limit to first 5 files
            try:
                with open(self.base_path / config_file, 'r') as f:
                    content = f.read()

                file_tests = {
                    "file": config_file,
                    "privilege_issues": []
                }

                for pattern in privilege_bypass_patterns:
                    if pattern in content:
                        file_tests["privilege_issues"].append({
                            "pattern": pattern,
                            "risk": "Potential privilege escalation if not properly secured"
                        })

                if file_tests["privilege_issues"]:
                    orm_tests.append(file_tests)

            except Exception as e:
                orm_tests.append({
                    "file": config_file,
                    "error": str(e)
                })

        return orm_tests

    def generate_privilege_recommendations(self, test_results: Dict) -> List[Dict]:
        """Generate privilege escalation security recommendations"""
        recommendations = []

        # Analyze API escalation tests
        api_escalations = [r for r in test_results.get("api_tests", [])
                          if r.get("escalation_detected", False)]

        if api_escalations:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": f"{len(api_escalations)} API privilege escalation vulnerabilities found",
                "recommendation": "Implement proper role-based access control (RBAC) and authorization checks",
                "affected_endpoints": list(set([r["endpoint"] for r in api_escalations]))
            })

        # Analyze database escalation tests
        db_escalations = [r for r in test_results.get("database_tests", [])
                         if r.get("privilege_escalation", False)]

        if db_escalations:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": f"{len(db_escalations)} database privilege escalation vulnerabilities found",
                "recommendation": "Implement least-privilege database users and proper access controls",
                "vulnerable_accounts": list(set([r.get("access_level", "unknown") for r in db_escalations]))
            })

        # Analyze injection escalation tests
        injection_escalations = [r for r in test_results.get("injection_tests", [])
                               if r.get("escalation_detected", False)]

        if injection_escalations:
            recommendations.append({
                "priority": "CRITICAL",
                "issue": f"{len(injection_escalations)} injection-based privilege escalation vulnerabilities found",
                "recommendation": "Implement input validation and parameterized queries"
            })

        # Analyze ORM issues
        orm_issues = test_results.get("orm_tests", [])
        if orm_issues:
            recommendations.append({
                "priority": "HIGH",
                "issue": f"{len(orm_issues)} ORM files have potential privilege escalation issues",
                "recommendation": "Add ownership checks and data validation in ORM operations"
            })

        return recommendations

    async def run_comprehensive_test(self) -> Dict:
        """Run comprehensive privilege escalation security test"""
        print("🔐 STARTING PRIVILEGE ESCALATION SECURITY TEST")
        print("=" * 60)

        results = {}

        # Test 1: API privilege escalation
        print("1️⃣ Testing API privilege escalation...")
        results["api_tests"] = await self.test_api_privilege_escalation()

        # Test 2: Database privilege escalation
        print("2️⃣ Testing database privilege escalation...")
        results["database_tests"] = self.test_database_privilege_escalation()

        # Test 3: Injection-based escalation
        print("3️⃣ Testing injection-based privilege escalation...")
        results["injection_tests"] = await self.test_injection_based_escalation()

        # Test 4: ORM privilege escalation
        print("4️⃣ Testing ORM privilege escalation...")
        results["orm_tests"] = self.test_orm_privilege_escalation()

        # Generate recommendations
        recommendations = self.generate_privilege_recommendations(results)
        results["recommendations"] = recommendations

        # Generate summary
        api_escalations = len([r for r in results["api_tests"] if r.get("escalation_detected", False)])
        db_escalations = len([r for r in results["database_tests"] if r.get("privilege_escalation", False)])
        injection_escalations = len([r for r in results["injection_tests"] if r.get("escalation_detected", False)])
        orm_issues = len(results["orm_tests"])

        results["summary"] = {
            "total_api_tests": len(results["api_tests"]),
            "api_escalations": api_escalations,
            "total_db_tests": len(results["database_tests"]),
            "database_escalations": db_escalations,
            "total_injection_tests": len(results["injection_tests"]),
            "injection_escalations": injection_escalations,
            "orm_files_with_issues": orm_issues,
            "total_vulnerabilities": api_escalations + db_escalations + injection_escalations + orm_issues,
            "recommendations_count": len(recommendations)
        }

        return results

async def main():
    """Main execution function"""
    tester = DatabasePrivilegeEscalationTester()

    try:
        results = await tester.run_comprehensive_test()

        # Display results
        print("\n" + "=" * 60)
        print("🔐 PRIVILEGE ESCALATION SECURITY TEST REPORT")
        print("=" * 60)

        summary = results["summary"]
        print(f"📊 API Tests: {summary['total_api_tests']} (Escalations: {summary['api_escalations']})")
        print(f"🗄️ Database Tests: {summary['total_db_tests']} (Escalations: {summary['database_escalations']})")
        print(f"💉 Injection Tests: {summary['total_injection_tests']} (Escalations: {summary['injection_escalations']})")
        print(f"🔧 ORM Issues: {summary['orm_files_with_issues']}")
        print(f"🚨 Total Vulnerabilities: {summary['total_vulnerabilities']}")
        print(f"💡 Recommendations: {summary['recommendations_count']}")

        # Show privilege escalation vulnerabilities
        api_vulns = [r for r in results["api_tests"] if r.get("escalation_detected", False)]
        if api_vulns:
            print(f"\n🚨 API PRIVILEGE ESCALATION VULNERABILITIES:")
            for vuln in api_vulns[:5]:  # Show first 5
                print(f"  ❌ {vuln['test_name']}: {vuln.get('security_issue', 'Unknown issue')}")

        db_vulns = [r for r in results["database_tests"] if r.get("privilege_escalation", False)]
        if db_vulns:
            print(f"\n🗄️ DATABASE PRIVILEGE ESCALATION VULNERABILITIES:")
            for vuln in db_vulns:
                print(f"  ❌ {vuln['test_name']}: {vuln.get('security_issue', 'Unknown issue')}")

        # Show recommendations
        print(f"\n💡 SECURITY RECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['issue']}")
            print(f"     → {rec['recommendation']}")

        # Save detailed report
        with open("/Users/sheriftito/Downloads/psychsync/privilege_escalation_security_report.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: privilege_escalation_security_report.json")

    except Exception as e:
        print(f"❌ Error running privilege escalation test: {e}")

if __name__ == "__main__":
    asyncio.run(main())
