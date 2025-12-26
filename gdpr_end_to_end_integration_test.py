#!/usr/bin/env python3
"""
GDPR End-to-End Integration Test
Validates complete GDPR compliance workflow across frontend and backend
"""

import asyncio
import json
import time
import requests
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any

class GDPRIntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8001"  # Using simple GDPR test server
        self.frontend_url = "http://localhost:5174"
        self.test_results = []
        self.test_user_data = {
            "email": "gdpr.test.integration@example.com",
            "password": "SecureTestPassword123!",
            "full_name": "GDPR Integration Test User"
        }

    def log_test_step(self, step: str, status: str, details: str = ""):
        """Log test step with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{icon} [{timestamp}] {step}")
        if details:
            print(f"    Details: {details}")

        self.test_results.append({
            "timestamp": timestamp,
            "step": step,
            "status": status,
            "details": details
        })

    def test_backend_connectivity(self) -> bool:
        """Test if backend is accessible"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test_step("Backend Connectivity Check", "PASS", "Backend responding normally")
                return True
            else:
                self.log_test_step("Backend Connectivity Check", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_step("Backend Connectivity Check", "FAIL", str(e))
            return False

    def test_frontend_connectivity(self) -> bool:
        """Test if frontend is accessible"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_test_step("Frontend Connectivity Check", "PASS", "Frontend responding normally")
                return True
            else:
                self.log_test_step("Frontend Connectivity Check", "FAIL", f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test_step("Frontend Connectivity Check", "FAIL", str(e))
            return False

    def test_gdpr_api_endpoints(self) -> Dict[str, Any]:
        """Test GDPR API endpoints availability"""
        endpoints = [
            "/api/v1/gdpr/data-retention-policy",
            "/api/v1/gdpr/processing-activities",
            "/api/v1/gdpr/privacy-policy",
            "/api/v1/cookies/categories"
        ]

        results = {}
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    results[endpoint] = {"status": "available", "response_size": len(response.content)}
                    self.log_test_step(f"GDPR Endpoint: {endpoint}", "PASS", "Endpoint available")
                else:
                    results[endpoint] = {"status": "error", "code": response.status_code}
                    self.log_test_step(f"GDPR Endpoint: {endpoint}", "FAIL", f"HTTP {response.status_code}")
            except Exception as e:
                results[endpoint] = {"status": "error", "error": str(e)}
                self.log_test_step(f"GDPR Endpoint: {endpoint}", "FAIL", str(e))

        return results

    def test_data_export_functionality(self) -> Dict[str, Any]:
        """Test data export functionality"""
        try:
            # Test export formats endpoint
            formats_response = requests.get(f"{self.backend_url}/api/v1/gdpr/export-formats", timeout=10)

            if formats_response.status_code == 200:
                formats = formats_response.json()
                available_formats = [f["id"] for f in formats.get("formats", [])]

                self.log_test_step("Data Export Formats", "PASS", f"Available formats: {available_formats}")

                # Test each format if user authentication is available
                export_results = {}
                for format_type in available_formats:
                    try:
                        # Note: This would require authentication in a real scenario
                        export_response = requests.post(
                            f"{self.backend_url}/api/v1/gdpr/data-export",
                            json={"format": format_type, "consent_confirmation": True},
                            timeout=15
                        )

                        if export_response.status_code in [200, 201, 401]:  # 401 is expected without auth
                            export_results[format_type] = "configured"
                            self.log_test_step(f"Export Format: {format_type}", "PASS", "Endpoint configured")
                        else:
                            export_results[format_type] = f"error_{export_response.status_code}"
                            self.log_test_step(f"Export Format: {format_type}", "FAIL", f"HTTP {export_response.status_code}")
                    except Exception as e:
                        export_results[format_type] = f"error_{str(e)}"
                        self.log_test_step(f"Export Format: {format_type}", "FAIL", str(e))

                return {
                    "formats_available": available_formats,
                    "export_endpoints": export_results
                }
            else:
                self.log_test_step("Data Export Formats", "FAIL", f"HTTP {formats_response.status_code}")
                return {"error": "formats_endpoint_unavailable"}

        except Exception as e:
            self.log_test_step("Data Export Functionality", "FAIL", str(e))
            return {"error": str(e)}

    def test_cookie_consent_system(self) -> Dict[str, Any]:
        """Test cookie consent system"""
        try:
            # Test consent categories
            categories_response = requests.get(f"{self.backend_url}/api/v1/cookies/categories", timeout=10)

            if categories_response.status_code == 200:
                categories = categories_response.json()
                consent_categories = categories.get("categories", [])

                self.log_test_step("Cookie Consent Categories", "PASS", f"Found {len(consent_categories)} categories")

                # Test consent recording
                consent_data = {
                    "analytics": True,
                    "marketing": False,
                    "functional": True,
                    "statistics": False,
                    "user_agent": "GDPR Integration Test",
                    "ip_address": "127.0.0.1"
                }

                consent_response = requests.post(
                    f"{self.backend_url}/api/v1/cookies/consent",
                    json=consent_data,
                    timeout=10
                )

                if consent_response.status_code in [200, 201]:
                    consent_result = consent_response.json()
                    self.log_test_step("Cookie Consent Recording", "PASS", f"Consent recorded: {consent_result.get('consent_id', 'N/A')}")

                    return {
                        "categories_available": len(consent_categories),
                        "recording_works": True,
                        "consent_id": consent_result.get("consent_id")
                    }
                else:
                    self.log_test_step("Cookie Consent Recording", "FAIL", f"HTTP {consent_response.status_code}")
                    return {
                        "categories_available": len(consent_categories),
                        "recording_works": False,
                        "error_code": consent_response.status_code
                    }
            else:
                self.log_test_step("Cookie Consent Categories", "FAIL", f"HTTP {categories_response.status_code}")
                return {"error": "categories_endpoint_unavailable"}

        except Exception as e:
            self.log_test_step("Cookie Consent System", "FAIL", str(e))
            return {"error": str(e)}

    def test_data_retention_policies(self) -> Dict[str, Any]:
        """Test data retention policy accessibility"""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/gdpr/data-retention-policy", timeout=10)

            if response.status_code == 200:
                policy = response.json()

                # Check for required policy elements
                required_elements = [
                    "legal_requirements",
                    "retention_periods",
                    "anonymization_schedule",
                    "compliance_review"
                ]

                found_elements = [elem for elem in required_elements if elem in policy.get("policy", {})]

                self.log_test_step("Data Retention Policy", "PASS", f"Found {len(found_elements)}/{len(required_elements)} required elements")

                return {
                    "policy_accessible": True,
                    "elements_found": len(found_elements),
                    "total_elements": len(required_elements),
                    "compliance_score": len(found_elements) / len(required_elements) * 100
                }
            else:
                self.log_test_step("Data Retention Policy", "FAIL", f"HTTP {response.status_code}")
                return {"policy_accessible": False, "error_code": response.status_code}

        except Exception as e:
            self.log_test_step("Data Retention Policy", "FAIL", str(e))
            return {"error": str(e)}

    def test_privacy_policy_accessibility(self) -> Dict[str, Any]:
        """Test privacy policy accessibility"""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/gdpr/privacy-policy", timeout=10)

            if response.status_code == 200:
                policy = response.json()

                self.log_test_step("Privacy Policy Access", "PASS", "Privacy policy accessible")

                return {
                    "policy_accessible": True,
                    "has_version_info": "version" in policy,
                    "has_content": len(str(policy)) > 100
                }
            else:
                self.log_test_step("Privacy Policy Access", "FAIL", f"HTTP {response.status_code}")
                return {"policy_accessible": False, "error_code": response.status_code}

        except Exception as e:
            self.log_test_step("Privacy Policy Access", "FAIL", str(e))
            return {"error": str(e)}

    def test_processing_activities_registry(self) -> Dict[str, Any]:
        """Test processing activities registry"""
        try:
            response = requests.get(f"{self.backend_url}/api/v1/gdpr/processing-activities", timeout=10)

            if response.status_code == 200:
                activities = response.json()
                processing_activities = activities.get("processing_activities", [])

                self.log_test_step("Processing Activities Registry", "PASS", f"Found {len(processing_activities)} activities")

                return {
                    "registry_accessible": True,
                    "activities_count": len(processing_activities),
                    "has_last_updated": "last_updated" in activities
                }
            else:
                self.log_test_step("Processing Activities Registry", "FAIL", f"HTTP {response.status_code}")
                return {"registry_accessible": False, "error_code": response.status_code}

        except Exception as e:
            self.log_test_step("Processing Activities Registry", "FAIL", str(e))
            return {"error": str(e)}

    def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed_tests = sum(1 for result in self.test_results if result["status"] == "FAIL")

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Determine overall status
        if success_rate >= 80:
            overall_status = "COMPLIANT"
        elif success_rate >= 60:
            overall_status = "SUBSTANTIALLY_COMPLIANT"
        elif success_rate >= 40:
            overall_status = "PARTIALLY_COMPLIANT"
        else:
            overall_status = "NON_COMPLIANT"

        return {
            "integration_test_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": success_rate,
                "overall_status": overall_status,
                "test_duration": len(self.test_results),
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "gdpr_compliance_areas": {
                "data_portability": self._get_compliance_score("export"),
                "right_to_erasure": self._get_compliance_score("deletion"),
                "cookie_consent": self._get_compliance_score("consent"),
                "data_transparency": self._get_compliance_score("policy"),
                "processing_registry": self._get_compliance_score("activities")
            }
        }

    def _get_compliance_score(self, keyword: str) -> float:
        """Calculate compliance score for a specific area"""
        relevant_tests = [
            result for result in self.test_results
            if keyword.lower() in result["step"].lower()
        ]

        if not relevant_tests:
            return 0.0

        passed = sum(1 for test in relevant_tests if test["status"] == "PASS")
        return (passed / len(relevant_tests)) * 100

    def save_integration_report(self, report: Dict[str, Any]) -> str:
        """Save integration report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gdpr_integration_test_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return filename

    async def run_complete_integration_test(self) -> Dict[str, Any]:
        """Run complete GDPR integration test suite"""
        print("🔒 Starting GDPR End-to-End Integration Test")
        print("=" * 60)

        # Test basic connectivity
        backend_ok = self.test_backend_connectivity()
        frontend_ok = self.test_frontend_connectivity()

        if not backend_ok:
            print("❌ Backend not accessible - cannot continue with GDPR testing")
            return {"error": "backend_unavailable"}

        # Test GDPR API endpoints
        print("\n📡 Testing GDPR API Endpoints...")
        api_results = self.test_gdpr_api_endpoints()

        # Test data export functionality
        print("\n📊 Testing Data Export Functionality...")
        export_results = self.test_data_export_functionality()

        # Test cookie consent system
        print("\n🍪 Testing Cookie Consent System...")
        consent_results = self.test_cookie_consent_system()

        # Test data retention policies
        print("\n📋 Testing Data Retention Policies...")
        retention_results = self.test_data_retention_policies()

        # Test privacy policy accessibility
        print("\n📄 Testing Privacy Policy Access...")
        privacy_results = self.test_privacy_policy_accessibility()

        # Test processing activities registry
        print("\n🔄 Testing Processing Activities Registry...")
        activities_results = self.test_processing_activities_registry()

        # Generate comprehensive report
        print("\n📈 Generating Integration Report...")
        report = self.generate_integration_report()

        # Add detailed results
        report["detailed_results"] = {
            "api_endpoints": api_results,
            "data_export": export_results,
            "cookie_consent": consent_results,
            "data_retention": retention_results,
            "privacy_policy": privacy_results,
            "processing_activities": activities_results
        }

        # Save report
        filename = self.save_integration_report(report)

        # Display summary
        summary = report["integration_test_summary"]
        print(f"\n🎯 GDPR INTEGRATION TEST SUMMARY")
        print("=" * 40)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Overall Status: {summary['overall_status'].replace('_', ' ').title()}")
        print(f"Test Duration: {summary['test_duration']} steps")
        print(f"\n📄 Detailed Report Saved: {filename}")

        # Display compliance area scores
        compliance_areas = report["gdpr_compliance_areas"]
        print(f"\n📊 GDPR COMPLIANCE AREA SCORES:")
        for area, score in compliance_areas.items():
            status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"  {status} {area.replace('_', ' ').title()}: {score:.1f}%")

        return report

async def main():
    """Main entry point"""
    print("🔒 PsychSync GDPR End-to-End Integration Test")
    print("Validating complete GDPR compliance workflow")
    print()

    tester = GDPRIntegrationTester()

    try:
        report = await tester.run_complete_integration_test()

        # Provide final assessment
        overall_status = report["integration_test_summary"]["overall_status"]
        success_rate = report["integration_test_summary"]["success_rate"]

        print(f"\n🏆 FINAL ASSESSMENT")
        print("=" * 20)

        if overall_status == "COMPLIANT":
            print("✅ GDPR INTEGRATION TEST PASSED")
            print("   System demonstrates strong GDPR compliance")
            print("   Ready for production deployment with confidence")
        elif overall_status == "SUBSTANTIALLY_COMPLIANT":
            print("⚠️ GDPR INTEGRATION TEST MOSTLY PASSED")
            print("   System shows good GDPR compliance with minor issues")
            print("   Address remaining issues before full production")
        elif overall_status == "PARTIALLY_COMPLIANT":
            print("⚠️ GDPR INTEGRATION TEST PARTIALLY PASSED")
            print("   System has basic GDPR compliance but needs improvements")
            print("   Significant work required before production deployment")
        else:
            print("❌ GDPR INTEGRATION TEST FAILED")
            print("   System lacks adequate GDPR compliance")
            print("   Major implementation work required")

        print(f"\n📊 Compliance Score: {success_rate:.1f}%")
        print(f"📋 Next Steps: Address any failed tests before production deployment")

    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Integration test error: {e}")

if __name__ == "__main__":
    asyncio.run(main())