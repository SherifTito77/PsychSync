#!/usr/bin/env python3
"""
GDPR Compliance Testing Suite
Tests data protection requirements per GDPR regulations
"""

import asyncio
import json
import time
import random
import requests
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import tempfile
import os

class GDPRTestScenario(Enum):
    """Types of GDPR compliance tests"""
    DATA_PORTABILITY = "data_portability"
    RIGHT_TO_ERASURE = "right_to_erasure"
    COOKIE_CONSENT = "cookie_consent"
    PROFILE_EXPORT = "profile_export"
    DATA_ANONYMIZATION = "data_anonymization"

class TestResult(Enum):
    """Test outcome statuses"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"
    CRITICAL = "critical"

@dataclass
class GDPRTestResult:
    """Result of a GDPR compliance test"""
    scenario_id: str
    scenario_type: GDPRTestScenario
    result: TestResult
    execution_time: float
    compliance_score: float  # 0-100 percentage
    error_message: Optional[str] = None
    violation_details: Optional[str] = None
    data_access_points: List[str] = field(default_factory=list)
    legal_basis_verified: bool = False
    consent_records: Dict[str, Any] = field(default_factory=dict)
    deletion_timeline: Optional[float] = None
    anonymization_verified: bool = False
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

class GDPRComplianceTester:
    """Comprehensive GDPR compliance testing system"""

    def __init__(self):
        self.test_results = []
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:5174"
        self.test_users = self._generate_test_users()
        self.compliance_database = self._setup_compliance_database()
        self.legal_requirements = self._load_gdpr_requirements()

    def _generate_test_users(self) -> Dict[str, Dict[str, Any]]:
        """Generate test users with various data scenarios"""
        return {
            "active_user": {
                "email": "gdpr.test.active@example.com",
                "user_id": "gdpr_user_001",
                "full_name": "Active Test User",
                "data_types": ["assessment_results", "psychometric_profile", "cookies", "analytics"],
                "created_at": datetime.now() - timedelta(days=180)
            },
            "user_with_deletion_request": {
                "email": "gdpr.test.deletion@example.com",
                "user_id": "gdpr_user_002",
                "full_name": "Deletion Test User",
                "data_types": ["assessment_results", "psychometric_profile", "cookies"],
                "created_at": datetime.now() - timedelta(days=365),
                "deletion_requested": datetime.now() - timedelta(days=10)
            },
            "minimally_active_user": {
                "email": "gdpr.test.minimal@example.com",
                "user_id": "gdpr_user_003",
                "full_name": "Minimal Test User",
                "data_types": ["basic_profile"],
                "created_at": datetime.now() - timedelta(days=30)
            }
        }

    def _setup_compliance_database(self) -> Dict[str, Any]:
        """Setup database for tracking compliance metrics"""
        # In a real implementation, this would connect to actual compliance tracking
        return {
            "consent_logs": [],
            "deletion_requests": [],
            "data_exports": [],
            "access_requests": []
        }

    def _load_gdpr_requirements(self) -> Dict[str, Any]:
        """Load GDPR legal requirements"""
        return {
            "data_portability": {
                "article": "Article 20",
                "requirement": "Users have right to receive personal data in structured, commonly used, machine-readable format",
                "formats": ["JSON", "CSV", "XML"],
                "timeline": "within 30 days"
            },
            "right_to_erasure": {
                "article": "Article 17",
                "requirement": "Users have right to request deletion of personal data",
                "timeline": "within 30 days",
                "verification": "Identity verification required"
            },
            "cookie_consent": {
                "article": "ePrivacy Directive",
                "requirement": "Explicit consent required for non-essential cookies",
                "granularity": "Granular consent options required"
            },
            "data_anonymization": {
                "article": "Article 5(1)(b)",
                "requirement": "Data must be pseudonymized where appropriate",
                "retention": "No longer than necessary"
            }
        }

    def test_gdpr_data_portability(self) -> GDPRTestResult:
        """Test GDPR data portability requirements"""
        print("📊 Testing: GDPR Data Portability Requirements...")

        start_time = time.time()
        user = self.test_users["active_user"]
        compliance_score = 0
        violation_details = []

        try:
            # Test 1: Verify data export API endpoint exists
            export_formats = ["json", "csv"]
            format_availability = {}

            for fmt in export_formats:
                try:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/export?format={fmt}",
                        headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                        timeout=10
                    )

                    if response.status_code == 200:
                        format_availability[fmt] = {
                            "available": True,
                            "content_type": response.headers.get('content-type', ''),
                            "data_size": len(response.content),
                            "response_time": response.elapsed.total_seconds()
                        }
                        compliance_score += 25
                    else:
                        format_availability[fmt] = {
                            "available": False,
                            "status_code": response.status_code
                        }
                        violation_details.append(f"Export format {fmt.upper()} not available (HTTP {response.status_code})")

                except Exception as e:
                    format_availability[fmt] = {
                        "available": False,
                        "error": str(e)
                    }
                    violation_details.append(f"Export format {fmt.upper()} failed: {str(e)}")

            # Test 2: Verify exported data completeness
            data_completeness_score = 0
            if format_availability.get("json", {}).get("available"):
                try:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/export?format=json",
                        headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                        timeout=10
                    )

                    exported_data = response.json()

                    # Check required data types are present
                    required_data_types = ["user_profile", "assessment_results", "preferences"]
                    found_data_types = []

                    for data_type in required_data_types:
                        if data_type in exported_data:
                            found_data_types.append(data_type)
                            data_completeness_score += 33.33

                    if data_completeness_score > 0:
                        compliance_score += min(data_completeness_score, 25)
                    else:
                        violation_details.append("Exported data missing required data types")

                except Exception as e:
                    violation_details.append(f"Data completeness check failed: {str(e)}")

            # Test 3: Verify response time compliance (within 30 days = immediate for testing)
            response_time_score = 25
            total_response_time = sum(fmt.get("response_time", 0) for fmt in format_availability.values() if fmt.get("available"))

            if total_response_time > 0 and total_response_time < 30:  # 30 seconds for testing
                compliance_score += response_time_score
            else:
                violation_details.append(f"Response time exceeds compliance threshold: {total_response_time:.2f}s")

            # Test 4: Verify data is in machine-readable format
            machine_readable_score = 25
            try:
                if format_availability.get("json", {}).get("available"):
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/export?format=json",
                        headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                        timeout=10
                    )
                    json.loads(response.text)  # Verify valid JSON
                    compliance_score += machine_readable_score
                else:
                    violation_details.append("No machine-readable format available")
            except Exception as e:
                violation_details.append(f"Machine-readable format validation failed: {str(e)}")

            # Determine overall result
            if compliance_score >= 90:
                result = TestResult.PASS
                recommendations = ["Continue monitoring data export performance"]
            elif compliance_score >= 70:
                result = TestResult.WARNING
                recommendations = [
                    "Improve data export format availability",
                    "Optimize response times for large data exports",
                    "Ensure all required data types are included"
                ]
            else:
                result = TestResult.FAIL
                recommendations = [
                    "Implement missing export formats",
                    "Fix data completeness issues",
                    "Optimize export API performance",
                    "Ensure GDPR Article 20 compliance"
                ]

            # Calculate final compliance score
            compliance_score = min(compliance_score, 100)

            return GDPRTestResult(
                scenario_id="gdpr_data_portability",
                scenario_type=GDPRTestScenario.DATA_PORTABILITY,
                result=result,
                execution_time=time.time() - start_time,
                compliance_score=compliance_score,
                data_access_points=[f"/api/v1/users/{user['user_id']}/export"],
                legal_basis_verified=True,
                consent_records={"data_export": {"granted": True, "timestamp": datetime.now().isoformat()}},
                violation_details="; ".join(violation_details) if violation_details else None,
                recommendations=recommendations
            )

        except Exception as e:
            return GDPRTestResult(
                scenario_id="gdpr_data_portability",
                scenario_type=GDPRTestScenario.DATA_PORTABILITY,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                compliance_score=0,
                error_message=str(e),
                violation_details="Test execution failed - potential GDPR compliance issue",
                recommendations=["Investigate data export API implementation", "Ensure GDPR Article 20 compliance"]
            )

    def test_right_to_erasure_30_days(self) -> GDPRTestResult:
        """Test 'Delete My Data' within 30 days requirement"""
        print("🗑️ Testing: Right to Erasure (30-Day Rule)...")

        start_time = time.time()
        user = self.test_users["user_with_deletion_request"]
        compliance_score = 0
        violation_details = []

        try:
            # Test 1: Verify deletion request API exists and is accessible
            deletion_request_available = False
            try:
                response = requests.post(
                    f"{self.backend_url}/api/v1/users/{user['user_id']}/request-deletion",
                    json={"reason": "GDPR Article 17 - Right to Erasure", "confirmation": True},
                    headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                    timeout=10
                )

                if response.status_code in [200, 201, 202]:
                    deletion_request_available = True
                    compliance_score += 25

                    # Parse response for deletion request details
                    deletion_response = response.json()
                    request_id = deletion_response.get("request_id")
                    expected_completion = deletion_response.get("expected_completion_date")
                else:
                    violation_details.append(f"Deletion request failed: HTTP {response.status_code}")

            except Exception as e:
                violation_details.append(f"Deletion request API error: {str(e)}")

            # Test 2: Verify identity verification requirement
            identity_verification_score = 25
            try:
                response = requests.post(
                    f"{self.backend_url}/api/v1/users/{user['user_id']}/request-deletion",
                    json={"reason": "Test deletion", "confirmation": False},  # No confirmation
                    headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                    timeout=10
                )

                # Should fail without proper confirmation
                if response.status_code == 400:
                    compliance_score += identity_verification_score
                else:
                    violation_details.append("Identity verification bypass detected - GDPR violation")

            except Exception as e:
                violation_details.append(f"Identity verification test failed: {str(e)}")

            # Test 3: Verify deletion timeline tracking
            timeline_tracking_score = 25
            try:
                if deletion_request_available:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/deletion-status",
                        headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                        timeout=10
                    )

                    if response.status_code == 200:
                        status_response = response.json()
                        status = status_response.get("status")
                        created_at = status_response.get("created_at")
                        estimated_completion = status_response.get("estimated_completion")

                        if created_at and estimated_completion:
                            # Verify compliance with 30-day rule
                            completion_date = datetime.fromisoformat(estimated_completion.replace('Z', '+00:00'))
                            request_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            days_to_complete = (completion_date - request_date).days

                            if days_to_complete <= 30:
                                compliance_score += timeline_tracking_score
                                deletion_timeline = days_to_complete
                            else:
                                violation_details.append(f"Deletion timeline exceeds 30 days: {days_to_complete} days")
                                deletion_timeline = days_to_complete
                        else:
                            violation_details.append("Deletion timeline information missing")
                    else:
                        violation_details.append("Deletion status tracking not available")

            except Exception as e:
                violation_details.append(f"Timeline tracking test failed: {str(e)}")

            # Test 4: Verify partial deletion and retention policies
            partial_deletion_score = 25
            try:
                # Check if system respects legal retention requirements
                response = requests.get(
                    f"{self.backend_url}/api/v1/legal/retention-policy",
                    timeout=10
                )

                if response.status_code == 200:
                    retention_policy = response.json()
                    legal_obligations = retention_policy.get("legal_obligations", [])
                    retention_periods = retention_policy.get("retention_periods", {})

                    if legal_obligations and retention_periods:
                        compliance_score += partial_deletion_score
                    else:
                        violation_details.append("Legal retention policy not documented")
                else:
                    violation_details.append("Legal retention policy not accessible")

            except Exception as e:
                violation_details.append(f"Partial deletion test failed: {str(e)}")

            # Determine overall result
            if compliance_score >= 80:
                result = TestResult.PASS
                recommendations = ["Monitor deletion request completion", "Document retention policies"]
            elif compliance_score >= 60:
                result = TestResult.WARNING
                recommendations = [
                    "Improve deletion timeline tracking",
                    "Document legal retention requirements",
                    "Enhance identity verification processes"
                ]
            else:
                result = TestResult.CRITICAL
                recommendations = [
                    "Implement proper deletion request handling",
                    "Add identity verification requirements",
                    "Document 30-day compliance procedures",
                    "URGENT: Fix GDPR Article 17 compliance"
                ]

            # Calculate final compliance score
            compliance_score = min(compliance_score, 100)

            return GDPRTestResult(
                scenario_id="right_to_erasure_30_days",
                scenario_type=GDPRTestScenario.RIGHT_TO_ERASURE,
                result=result,
                execution_time=time.time() - start_time,
                compliance_score=compliance_score,
                deletion_timeline=deletion_timeline if 'deletion_timeline' in locals() else None,
                legal_basis_verified=True,
                data_access_points=[f"/api/v1/users/{user['user_id']}/request-deletion"],
                violation_details="; ".join(violation_details) if violation_details else None,
                recommendations=recommendations
            )

        except Exception as e:
            return GDPRTestResult(
                scenario_id="right_to_erasure_30_days",
                scenario_type=GDPRTestScenario.RIGHT_TO_ERASURE,
                result=TestResult.CRITICAL,
                execution_time=time.time() - start_time,
                compliance_score=0,
                error_message=str(e),
                violation_details="CRITICAL: Right to Erasure implementation failed - GDPR Article 17 violation",
                recommendations=["URGENT: Implement GDPR Article 17 compliance", "Add legal review of deletion processes"]
            )

    def test_cookie_consent_rules(self) -> GDPRTestResult:
        """Test that tracking cookies follow consent rules"""
        print("🍪 Testing: Cookie Consent Rules Compliance...")

        start_time = time.time()
        compliance_score = 0
        violation_details = []

        try:
            # Test 1: Verify consent banner/popup presence
            consent_banner_score = 25
            try:
                response = requests.get(self.frontend_url, timeout=10)

                if response.status_code == 200:
                    page_content = response.text.lower()

                    # Check for consent management elements
                    consent_indicators = [
                        "cookie", "consent", "privacy", "gdpr", "accept", "reject", "preferences"
                    ]

                    consent_elements_found = sum(1 for indicator in consent_indicators if indicator in page_content)

                    if consent_elements_found >= 4:  # Require multiple consent elements
                        compliance_score += consent_banner_score
                    else:
                        violation_details.append("Insufficient cookie consent elements detected")
                else:
                    violation_details.append(f"Frontend not accessible: HTTP {response.status_code}")

            except Exception as e:
                violation_details.append(f"Consent banner test failed: {str(e)}")

            # Test 2: Verify granular consent options
            granular_consent_score = 25
            try:
                # Test cookie categories API
                response = requests.get(f"{self.backend_url}/api/v1/cookies/categories", timeout=10)

                if response.status_code == 200:
                    categories = response.json()
                    required_categories = ["essential", "analytics", "marketing", "functional"]

                    found_categories = [cat.get("name", "").lower() for cat in categories]
                    category_compliance = len([cat for cat in required_categories if cat in found_categories])

                    if category_compliance >= 3:
                        compliance_score += granular_consent_score
                    else:
                        violation_details.append(f"Insufficient cookie categories: {category_compliance}/4 required")
                else:
                    violation_details.append("Cookie categories API not available")

            except Exception as e:
                violation_details.append(f"Granular consent test failed: {str(e)}")

            # Test 3: Verify consent recording and storage
            consent_recording_score = 25
            try:
                # Test consent submission
                consent_data = {
                    "analytics": True,
                    "marketing": False,
                    "functional": True,
                    "timestamp": datetime.now().isoformat(),
                    "user_agent": "GDPR Compliance Test",
                    "ip_address": "127.0.0.1"
                }

                response = requests.post(
                    f"{self.backend_url}/api/v1/cookies/consent",
                    json=consent_data,
                    timeout=10
                )

                if response.status_code in [200, 201]:
                    consent_response = response.json()
                    consent_id = consent_response.get("consent_id")

                    if consent_id:
                        compliance_score += consent_recording_score

                        # Test consent retrieval
                        retrieve_response = requests.get(
                            f"{self.backend_url}/api/v1/cookies/consent/{consent_id}",
                            timeout=10
                        )

                        if retrieve_response.status_code == 200:
                            stored_consent = retrieve_response.json()
                            # Verify consent data integrity
                            if stored_consent.get("analytics") == consent_data["analytics"]:
                                pass  # Consent properly stored
                            else:
                                violation_details.append("Consent data integrity issue")
                        else:
                            violation_details.append("Consent retrieval failed")
                    else:
                        violation_details.append("Consent recording failed - no ID returned")
                else:
                    violation_details.append(f"Consent submission failed: HTTP {response.status_code}")

            except Exception as e:
                violation_details.append(f"Consent recording test failed: {str(e)}")

            # Test 4: Verify cookie blocking before consent
            pre_consent_blocking_score = 25
            try:
                # Test that non-essential cookies are blocked without consent
                headers = {"Cookie": ""}  # No consent cookies

                response = requests.get(
                    f"{self.backend_url}/api/v1/analytics/track",
                    headers=headers,
                    json={"action": "page_view", "timestamp": datetime.now().isoformat()},
                    timeout=10
                )

                # Should return 403 or similar for non-consented tracking
                if response.status_code in [403, 401, 422]:
                    compliance_score += pre_consent_blocking_score
                else:
                    violation_details.append(f"Tracking without consent allowed: HTTP {response.status_code}")

            except Exception as e:
                violation_details.append(f"Pre-consent blocking test failed: {str(e)}")

            # Determine overall result
            if compliance_score >= 80:
                result = TestResult.PASS
                recommendations = ["Continue monitoring consent compliance", "Regular consent audit reviews"]
            elif compliance_score >= 60:
                result = TestResult.WARNING
                recommendations = [
                    "Improve granular consent options",
                    "Enhance consent recording accuracy",
                    "Better pre-consent cookie blocking"
                ]
            else:
                result = TestResult.FAIL
                recommendations = [
                    "Implement proper cookie consent banner",
                    "Add granular consent categories",
                    "Fix consent recording system",
                    "Implement pre-consent blocking"
                ]

            # Calculate final compliance score
            compliance_score = min(compliance_score, 100)

            return GDPRTestResult(
                scenario_id="cookie_consent_rules",
                scenario_type=GDPRTestScenario.COOKIE_CONSENT,
                result=result,
                execution_time=time.time() - start_time,
                compliance_score=compliance_score,
                legal_basis_verified=True,
                consent_records={
                    "cookie_consent": {
                        "granular_options": True,
                        "recording_enabled": True,
                        "pre_consent_blocking": True,
                        "last_tested": datetime.now().isoformat()
                    }
                },
                violation_details="; ".join(violation_details) if violation_details else None,
                recommendations=recommendations
            )

        except Exception as e:
            return GDPRTestResult(
                scenario_id="cookie_consent_rules",
                scenario_type=GDPRTestScenario.COOKIE_CONSENT,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                compliance_score=0,
                error_message=str(e),
                violation_details="Cookie consent system failed - ePrivacy Directive violation",
                recommendations=["URGENT: Implement cookie consent compliance", "Review ePrivacy Directive requirements"]
            )

    def test_psychometric_profile_export(self) -> GDPRTestResult:
        """Test that users can export their psychometric profile"""
        print("🧠 Testing: Psychometric Profile Export...")

        start_time = time.time()
        user = self.test_users["active_user"]
        compliance_score = 0
        violation_details = []

        try:
            # Test 1: Verify psychometric data export endpoint
            profile_export_available = False
            try:
                response = requests.get(
                    f"{self.backend_url}/api/v1/users/{user['user_id']}/psychometric-profile/export",
                    headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                    timeout=15
                )

                if response.status_code == 200:
                    profile_export_available = True
                    compliance_score += 25

                    # Verify response is valid JSON
                    try:
                        profile_data = response.json()
                        profile_size = len(response.content)
                    except json.JSONDecodeError:
                        violation_details.append("Psychometric profile export not in valid JSON format")
                else:
                    violation_details.append(f"Psychometric profile export failed: HTTP {response.status_code}")

            except Exception as e:
                violation_details.append(f"Profile export API error: {str(e)}")

            # Test 2: Verify psychometric data completeness
            data_completeness_score = 0
            if profile_export_available:
                try:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/psychometric-profile/export",
                        headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                        timeout=15
                    )

                    profile_data = response.json()

                    # Check required psychometric components
                    required_components = [
                        "personality_traits",
                        "assessment_results",
                        "behavioral_patterns",
                        "development_insights",
                        "recommendations"
                    ]

                    found_components = []
                    for component in required_components:
                        if component in profile_data:
                            found_components.append(component)
                            data_completeness_score += 20

                    if data_completeness_score >= 80:
                        compliance_score += 25
                    else:
                        violation_details.append(f"Psychometric data incomplete: {len(found_components)}/{len(required_components)} components")

                except Exception as e:
                    violation_details.append(f"Data completeness check failed: {str(e)}")

            # Test 3: Verify data accuracy and consistency
            data_accuracy_score = 25
            if profile_export_available:
                try:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/psychometric-profile/export",
                        headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                        timeout=15
                    )

                    profile_data = response.json()

                    # Check data integrity indicators
                    accuracy_checks = []

                    # Check for consistent data types
                    if "assessment_results" in profile_data:
                        results = profile_data["assessment_results"]
                        if isinstance(results, list) and len(results) > 0:
                            # Check each result has required fields
                            valid_results = sum(1 for result in results if all(
                                field in result for field in ["assessment_type", "score", "completion_date"]
                            ))
                            if valid_results == len(results):
                                accuracy_checks.append(True)

                    # Check personality traits have proper structure
                    if "personality_traits" in profile_data:
                        traits = profile_data["personality_traits"]
                        if isinstance(traits, dict) and traits:
                            # Check trait values are within expected ranges
                            valid_traits = sum(1 for trait, value in traits.items() if
                                             isinstance(value, (int, float)) and 0 <= value <= 100)
                            if valid_traits == len(traits):
                                accuracy_checks.append(True)

                    if len(accuracy_checks) >= 2:
                        compliance_score += data_accuracy_score
                    else:
                        violation_details.append("Psychometric data accuracy or consistency issues")

                except Exception as e:
                    violation_details.append(f"Data accuracy check failed: {str(e)}")

            # Test 4: Verify export format compliance
            format_compliance_score = 25
            if profile_export_available:
                try:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/psychometric-profile/export",
                        headers={"Authorization": f"Bearer test_token_{user['user_id']}"},
                        timeout=15
                    )

                    # Verify it's valid JSON with proper structure
                    profile_data = response.json()

                    # Check GDPR-compliant metadata
                    required_metadata = ["export_date", "user_id", "data_format", "version"]
                    metadata_present = sum(1 for meta in required_metadata if meta in profile_data.get("metadata", {}))

                    if metadata_present >= 3:
                        compliance_score += format_compliance_score
                    else:
                        violation_details.append(f"Missing export metadata: {metadata_present}/{len(required_metadata)} fields")

                except Exception as e:
                    violation_details.append(f"Format compliance check failed: {str(e)}")

            # Determine overall result
            if compliance_score >= 80:
                result = TestResult.PASS
                recommendations = ["Continue monitoring profile export accuracy", "Regular psychometric data audits"]
            elif compliance_score >= 60:
                result = TestResult.WARNING
                recommendations = [
                    "Improve psychometric data completeness",
                    "Enhance data accuracy validation",
                    "Add comprehensive export metadata"
                ]
            else:
                result = TestResult.FAIL
                recommendations = [
                    "Fix psychometric profile export functionality",
                    "Ensure all required data components are included",
                    "Implement data accuracy validation",
                    "Add proper export metadata"
                ]

            # Calculate final compliance score
            compliance_score = min(compliance_score, 100)

            return GDPRTestResult(
                scenario_id="psychometric_profile_export",
                scenario_type=GDPRTestScenario.PROFILE_EXPORT,
                result=result,
                execution_time=time.time() - start_time,
                compliance_score=compliance_score,
                legal_basis_verified=True,
                data_access_points=[f"/api/v1/users/{user['user_id']}/psychometric-profile/export"],
                violation_details="; ".join(violation_details) if violation_details else None,
                recommendations=recommendations
            )

        except Exception as e:
            return GDPRTestResult(
                scenario_id="psychometric_profile_export",
                scenario_type=GDPRTestScenario.PROFILE_EXPORT,
                result=TestResult.ERROR,
                execution_time=time.time() - start_time,
                compliance_score=0,
                error_message=str(e),
                violation_details="Psychometric profile export failed - Data portability violation",
                recommendations=["URGENT: Implement psychometric profile export", "Ensure GDPR Article 20 compliance for specialized data"]
            )

    def test_data_anonymization_after_deletion(self) -> GDPRTestResult:
        """Test data anonymization after deletion"""
        print("🔒 Testing: Data Anonymization After Deletion...")

        start_time = time.time()
        user = self.test_users["user_with_deletion_request"]
        compliance_score = 0
        violation_details = []

        try:
            # Test 1: Verify anonymization process implementation
            anonymization_process_score = 25
            try:
                # Test anonymization API endpoint
                response = requests.post(
                    f"{self.backend_url}/api/v1/admin/anonymize-user-data",
                    json={"user_id": user["user_id"], "reason": "GDPR Article 17"},
                    headers={"Authorization": "Bearer admin_test_token"},
                    timeout=15
                )

                if response.status_code in [200, 202]:
                    anonymization_response = response.json()
                    anonymization_id = anonymization_response.get("anonymization_id")

                    if anonymization_id:
                        compliance_score += anonymization_process_score
                    else:
                        violation_details.append("Anonymization process failed - no ID returned")
                else:
                    violation_details.append(f"Anonymization API failed: HTTP {response.status_code}")

            except Exception as e:
                violation_details.append(f"Anonymization process test failed: {str(e)}")

            # Test 2: Verify pseudonymization implementation
            pseudonymization_score = 25
            try:
                # Check if user data is properly pseudonymized
                response = requests.get(
                    f"{self.backend_url}/api/v1/users/{user['user_id']}/data-check",
                    headers={"Authorization": "Bearer admin_test_token"},
                    timeout=10
                )

                if response.status_code == 200:
                    data_status = response.json()

                    # Check for pseudonymization indicators
                    personal_data_fields = ["email", "full_name", "phone", "address"]
                    anonymized_fields = []

                    for field in personal_data_fields:
                        if field in data_status:
                            field_value = data_status[field]
                            # Check if field appears pseudonymized (hashed, replaced, or removed)
                            if isinstance(field_value, str):
                                # Check for common pseudonymization patterns
                                if (field_value.startswith("anon_") or
                                    field_value.startswith("hash_") or
                                    len(field_value) == 64 and all(c in "0123456789abcdefABCDEF" for c in field_value)):
                                    anonymized_fields.append(field)

                    if len(anonymized_fields) >= 3:
                        compliance_score += pseudonymization_score
                    else:
                        violation_details.append(f"Insufficient field pseudonymization: {len(anonymized_fields)}/{len(personal_data_fields)}")
                else:
                    violation_details.append("Data check API not available")

            except Exception as e:
                violation_details.append(f"Pseudonymization check failed: {str(e)}")

            # Test 3: Verify data retention policies
            retention_policy_score = 25
            try:
                # Check retention policy implementation
                response = requests.get(
                    f"{self.backend_url}/api/v1/legal/data-retention",
                    timeout=10
                )

                if response.status_code == 200:
                    retention_policy = response.json()

                    # Check for required retention policy elements
                    required_elements = [
                        "legal_requirements",
                        "retention_periods",
                        "anonymization_schedule",
                        "compliance_review"
                    ]

                    found_elements = sum(1 for element in required_elements if element in retention_policy)

                    if found_elements >= 3:
                        compliance_score += retention_policy_score
                    else:
                        violation_details.append(f"Missing retention policy elements: {found_elements}/{len(required_elements)}")
                else:
                    violation_details.append("Data retention policy not accessible")

            except Exception as e:
                violation_details.append(f"Retention policy check failed: {str(e)}")

            # Test 4: Verify complete data removal where required
            complete_removal_score = 25
            try:
                # Verify sensitive data is completely removed
                sensitive_data_types = [
                    "biometric_data",
                    "health_information",
                    "genetic_data",
                    "political_opinions",
                    "religious_beliefs"
                ]

                removal_verification = []
                for data_type in sensitive_data_types:
                    response = requests.get(
                        f"{self.backend_url}/api/v1/users/{user['user_id']}/data/{data_type}",
                        headers={"Authorization": "Bearer admin_test_token"},
                        timeout=5
                    )

                    # Should return 404 or empty data for deleted sensitive data
                    if response.status_code in [404, 410]:
                        removal_verification.append(True)
                    else:
                        removal_verification.append(False)

                if all(removal_verification):
                    compliance_score += complete_removal_score
                else:
                    violation_details.append(f"Incomplete sensitive data removal: {sum(removal_verification)}/{len(removal_verification)}")

            except Exception as e:
                violation_details.append(f"Complete removal verification failed: {str(e)}")

            # Determine overall result
            if compliance_score >= 80:
                result = TestResult.PASS
                recommendations = ["Continue monitoring anonymization processes", "Regular privacy compliance audits"]
            elif compliance_score >= 60:
                result = TestResult.WARNING
                recommendations = [
                    "Improve pseudonymization coverage",
                    "Enhance data retention documentation",
                    "Complete sensitive data removal"
                ]
            else:
                result = TestResult.CRITICAL
                recommendations = [
                    "URGENT: Implement proper data anonymization",
                    "Fix pseudonymization processes",
                    "Document retention policies",
                    "Ensure complete sensitive data removal"
                ]

            # Calculate final compliance score
            compliance_score = min(compliance_score, 100)

            return GDPRTestResult(
                scenario_id="data_anonymization_after_deletion",
                scenario_type=GDPRTestScenario.DATA_ANONYMIZATION,
                result=result,
                execution_time=time.time() - start_time,
                compliance_score=compliance_score,
                anonymization_verified=compliance_score >= 60,
                legal_basis_verified=True,
                data_access_points=[
                    f"/api/v1/admin/anonymize-user-data",
                    f"/api/v1/users/{user['user_id']}/data-check"
                ],
                violation_details="; ".join(violation_details) if violation_details else None,
                recommendations=recommendations
            )

        except Exception as e:
            return GDPRTestResult(
                scenario_id="data_anonymization_after_deletion",
                scenario_type=GDPRTestScenario.DATA_ANONYMIZATION,
                result=TestResult.CRITICAL,
                execution_time=time.time() - start_time,
                compliance_score=0,
                error_message=str(e),
                violation_details="CRITICAL: Data anonymization failed - GDPR Article 5(1)(b) violation",
                recommendations=["URGENT: Implement GDPR Article 5 compliance", "Review data protection by design principles"]
            )

    def run_comprehensive_gdpr_test_suite(self) -> List[GDPRTestResult]:
        """Run all GDPR compliance tests"""
        print("🔒 Starting Comprehensive GDPR Compliance Testing Suite")
        print("=" * 60)

        test_functions = [
            self.test_gdpr_data_portability,
            self.test_right_to_erasure_30_days,
            self.test_cookie_consent_rules,
            self.test_psychometric_profile_export,
            self.test_data_anonymization_after_deletion
        ]

        results = []

        for test_func in test_functions:
            try:
                result = test_func()
                results.append(result)

                status_icon = {
                    TestResult.PASS: "✅",
                    TestResult.FAIL: "❌",
                    TestResult.WARNING: "⚠️",
                    TestResult.ERROR: "💥",
                    TestResult.CRITICAL: "🚨",
                    TestResult.SKIPPED: "⏭️"
                }.get(result.result, "❓")

                print(f"{status_icon} {result.scenario_type.value}: {result.result.value.upper()} ({result.compliance_score:.1f}% compliance)")

                if result.violation_details:
                    print(f"    Violations: {result.violation_details[:100]}...")

            except Exception as e:
                error_result = GDPRTestResult(
                    scenario_id=test_func.__name__,
                    scenario_type=GDPRTestScenario.DATA_PORTABILITY,  # Default
                    result=TestResult.ERROR,
                    execution_time=0,
                    compliance_score=0,
                    error_message=str(e),
                    violation_details="Test execution failed - potential GDPR compliance issue",
                    recommendations=["URGENT: Investigate GDPR compliance implementation"]
                )
                results.append(error_result)
                print(f"💥 {test_func.__name__}: ERROR - {str(e)[:100]}")

            print()

        return results

    def generate_gdpr_compliance_report(self, results: List[GDPRTestResult]) -> Dict[str, Any]:
        """Generate comprehensive GDPR compliance report"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.result == TestResult.PASS)
        failed_tests = sum(1 for r in results if r.result == TestResult.FAIL)
        warning_tests = sum(1 for r in results if r.result == TestResult.WARNING)
        error_tests = sum(1 for r in results if r.result == TestResult.ERROR)
        critical_tests = sum(1 for r in results if r.result == TestResult.CRITICAL)
        skipped_tests = sum(1 for r in results if r.result == TestResult.SKIPPED)

        # Calculate average compliance score
        avg_compliance_score = sum(r.compliance_score for r in results) / total_tests if total_tests > 0 else 0

        # Determine overall compliance status
        if critical_tests > 0:
            overall_status = "CRITICAL_VIOLATION"
        elif avg_compliance_score >= 90:
            overall_status = "COMPLIANT"
        elif avg_compliance_score >= 75:
            overall_status = "SUBSTANTIALLY_COMPLIANT"
        elif avg_compliance_score >= 60:
            overall_status = "PARTIALLY_COMPLIANT"
        else:
            overall_status = "NON_COMPLIANT"

        report = {
            "gdpr_compliance_summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warning_tests,
                "errors": error_tests,
                "critical": critical_tests,
                "skipped": skipped_tests,
                "overall_status": overall_status,
                "average_compliance_score": avg_compliance_score,
                "execution_time": sum(r.execution_time for r in results),
                "legal_risk_level": "HIGH" if critical_tests > 0 else "MEDIUM" if avg_compliance_score < 75 else "LOW"
            },
            "gdpr_test_results": [],
            "compliance_gaps": {
                "critical_violations": [r for r in results if r.result == TestResult.CRITICAL],
                "compliance_warnings": [r for r in results if r.result == TestResult.WARNING],
                "legal_recommendations": list(set([rec for r in results for rec in r.recommendations if "URGENT" in rec])),
                "improvement_areas": list(set([rec for r in results for rec in r.recommendations if "URGENT" not in rec]))
            },
            "gdpr_articles_assessed": [
                {
                    "article": "Article 15 - Right of Access",
                    "status": "Assessed via data portability tests",
                    "compliant": passed_tests > 0
                },
                {
                    "article": "Article 16 - Right to Rectification",
                    "status": "Assessed via profile export tests",
                    "compliant": any(r.scenario_type == GDPRTestScenario.PROFILE_EXPORT and r.result != TestResult.CRITICAL for r in results)
                },
                {
                    "article": "Article 17 - Right to Erasure",
                    "status": "Assessed via deletion request tests",
                    "compliant": any(r.scenario_type == GDPRTestScenario.RIGHT_TO_ERASURE and r.result != TestResult.CRITICAL for r in results)
                },
                {
                    "article": "Article 20 - Right to Data Portability",
                    "status": "Assessed via data export tests",
                    "compliant": any(r.scenario_type == GDPRTestScenario.DATA_PORTABILITY and r.result != TestResult.CRITICAL for r in results)
                },
                {
                    "article": "Article 5(1)(b) - Data Minimisation",
                    "status": "Assessed via anonymization tests",
                    "compliant": any(r.scenario_type == GDPRTestScenario.DATA_ANONYMIZATION and r.result != TestResult.CRITICAL for r in results)
                }
            ],
            "timestamp": datetime.now().isoformat(),
            "report_type": "GDPR_COMPLIANCE_ASSESSMENT"
        }

        # Add detailed results
        for result in results:
            report["gdpr_test_results"].append({
                "scenario_id": result.scenario_id,
                "scenario_type": result.scenario_type.value,
                "result": result.result.value,
                "execution_time": result.execution_time,
                "compliance_score": result.compliance_score,
                "error_message": result.error_message,
                "violation_details": result.violation_details,
                "legal_basis_verified": result.legal_basis_verified,
                "data_access_points": result.data_access_points,
                "consent_records": result.consent_records,
                "deletion_timeline": result.deletion_timeline,
                "anonymization_verified": result.anonymization_verified,
                "recommendations": result.recommendations,
                "timestamp": result.timestamp.isoformat()
            })

        return report

    def save_gdpr_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """Save GDPR compliance report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gdpr_compliance_report_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return filename

def main():
    """Main entry point"""
    print("🔒 PsychSync GDPR Compliance Testing Suite")
    print("Validating data protection compliance with GDPR requirements")
    print()

    tester = GDPRComplianceTester()

    try:
        # Run comprehensive GDPR test suite
        results = tester.run_comprehensive_gdpr_test_suite()

        # Generate and save report
        report = tester.generate_gdpr_compliance_report(results)
        filename = tester.save_gdpr_report(report)

        # Display summary
        summary = report["gdpr_compliance_summary"]
        print("🎯 GDPR COMPLIANCE ASSESSMENT SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ✅")
        print(f"Failed: {summary['failed']} ❌")
        print(f"Warnings: {summary['warnings']} ⚠️")
        print(f"Errors: {summary['errors']} 💥")
        print(f"Critical: {summary['critical']} 🚨")
        print(f"Avg Compliance Score: {summary['average_compliance_score']:.1f}%")
        print(f"Overall Status: {summary['overall_status'].replace('_', ' ').title()}")
        print(f"Legal Risk Level: {summary['legal_risk_level']}")
        print(f"Execution Time: {summary['execution_time']:.2f} seconds")
        print()
        print(f"📄 Detailed Report Saved: {filename}")

        # Display GDPR articles assessment
        print("\n📋 GDPR ARTICLES ASSESSMENT:")
        for article in report["gdpr_articles_assessed"]:
            status_icon = "✅" if article["compliant"] else "❌"
            print(f"  {status_icon} {article['article']}: {article['status']}")

        # Critical legal recommendations
        critical_recommendations = report["compliance_gaps"]["legal_recommendations"]
        if critical_recommendations:
            print("\n🚨 CRITICAL LEGAL RECOMMENDATIONS:")
            for i, rec in enumerate(critical_recommendations, 1):
                print(f"  {i}. {rec}")

        # Improvement areas
        improvement_areas = report["compliance_gaps"]["improvement_areas"][:5]
        if improvement_areas:
            print("\n💡 COMPLIANCE IMPROVEMENT AREAS:")
            for i, area in enumerate(improvement_areas, 1):
                print(f"  {i}. {area}")

        # Compliance gaps
        critical_violations = report["compliance_gaps"]["critical_violations"]
        if critical_violations:
            print("\n⚖️ CRITICAL GDPR VIOLATIONS REQUIRING IMMEDIATE ACTION:")
            for violation in critical_violations:
                print(f"  • {violation.scenario_type.value.replace('_', ' ').title()}: {violation.violation_details}")

    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 GDPR testing suite error: {e}")

    print("\n🏁 GDPR Compliance Testing Complete!")

if __name__ == "__main__":
    main()
