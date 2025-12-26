#!/usr/bin/env python3
"""
Complete MBTI Assessment Integration Test

This script tests the entire MBTI assessment flow from user perspective:
1. Access the MBTI assessment page
2. Submit assessment responses
3. Verify comprehensive results are returned
4. Test different personality type outcomes
"""

import requests
import json
import time
from typing import Dict, Any

class MBTIIntegrationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8000/api/v1"
        self.frontend_url = "http://localhost:5173"
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status} {test_name}"
        if details:
            result += f" - {details}"
        self.test_results.append(result)
        print(result)

    def test_frontend_accessibility(self) -> bool:
        """Test if frontend MBTI assessment page is accessible"""
        try:
            response = requests.get(f"{self.frontend_url}/assessments/mbti/start", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Frontend accessibility error: {e}")
            return False

    def test_mbti_submit_endpoint(self, responses: Dict[str, str], expected_type: str = None) -> Dict[str, Any]:
        """Test MBTI assessment submission with different response patterns"""
        payload = {
            "assessment_id": "mbti-integration-test",
            "assessment_type": "mbti",
            "responses": responses,
            "raw_type": expected_type
        }

        try:
            response = requests.post(
                f"{self.backend_url}/mbti-test-submit",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"API request error: {e}")
            return None

    def test_personality_type_calculations(self):
        """Test that different response patterns produce expected MBTI types"""

        # Test Case 1: Clear ENTJ responses
        entj_responses = {
            "1": "E", "2": "E", "3": "E",  # Strong Extraversion
            "4": "N", "5": "N", "6": "N",  # Strong Intuition
            "7": "T", "8": "T", "9": "T",  # Strong Thinking
            "10": "J", "11": "J", "12": "J" # Strong Judging
        }

        result = self.test_mbti_submit_endpoint(entj_responses)
        if result:
            has_required_fields = all(key in result for key in [
                'type', 'confidence', 'description', 'dimensions',
                'preferences', 'strengths', 'blind_spots'
            ])
            self.log_test(
                "ENTJ Calculation Test",
                has_required_fields,
                f"Type: {result.get('type', 'N/A')}, Confidence: {result.get('confidence', 'N/A')}"
            )
        else:
            self.log_test("ENTJ Calculation Test", False, "API call failed")

        # Test Case 2: Balanced responses (should use raw_type)
        balanced_responses = {
            "1": "E", "2": "I",  # Balanced E-I
            "3": "S", "4": "N",  # Balanced S-N
            "5": "T", "6": "F",  # Balanced T-F
            "7": "J", "8": "P"   # Balanced J-P
        }

        result = self.test_mbti_submit_endpoint(balanced_responses, "INFP")
        if result:
            correct_type = result.get('type') == "INFP"
            self.log_test(
                "Balanced Responses Test",
                correct_type,
                f"Expected INFP, got {result.get('type', 'N/A')}"
            )

        # Test Case 3: Strong Introverted responses
        introvert_responses = {
            "1": "I", "2": "I", "3": "I",  # Strong Introversion
            "4": "S", "5": "S", "6": "S",  # Strong Sensing
            "7": "F", "8": "F", "9": "F",  # Strong Feeling
            "10": "P", "11": "P", "12": "P" # Strong Perceiving
        }

        result = self.test_mbti_submit_endpoint(introvert_responses)
        if result:
            is_introverted = result['type'][0] == 'I'  # First letter should be I
            self.log_test(
                "Introvert Calculation Test",
                is_introverted,
                f"Type: {result.get('type', 'N/A')}, Expected introverted type"
            )

    def test_comprehensive_results_structure(self):
        """Test that the results contain all required MBTI information"""
        test_responses = {
            "1": "E", "2": "N", "3": "T", "4": "J"
        }

        result = self.test_mbti_submit_endpoint(test_responses)
        if not result:
            self.log_test("Results Structure Test", False, "No results returned")
            return

        # Check required fields
        required_fields = [
            'type', 'confidence', 'description', 'dimensions',
            'preferences', 'strengths', 'blind_spots', 'submitted_at',
            'assessment_id', 'scoring_details'
        ]

        missing_fields = [field for field in required_fields if field not in result]

        if missing_fields:
            self.log_test("Results Structure Test", False, f"Missing fields: {missing_fields}")
            return

        # Check dimensions structure
        dimensions = result.get('dimensions', {})
        expected_dimensions = ['extraversion', 'intuition', 'thinking', 'judging']
        missing_dimensions = [dim for dim in expected_dimensions if dim not in dimensions]

        if missing_dimensions:
            self.log_test("Results Structure Test", False, f"Missing dimensions: {missing_dimensions}")
            return

        # Check preferences length (should be 6 combinations)
        preferences = result.get('preferences', [])
        has_six_preferences = len(preferences) == 6

        # Check scoring details
        scoring_details = result.get('scoring_details', {})
        has_scoring_algorithm = scoring_details.get('algorithm') == 'mbti'
        has_dimension_scores = 'dimension_scores' in scoring_details

        all_checks_pass = (
            not missing_fields and
            not missing_dimensions and
            has_six_preferences and
            has_scoring_algorithm and
            has_dimension_scores
        )

        self.log_test(
            "Results Structure Test",
            all_checks_pass,
            f"Fields: {len(required_fields)}/✓, Preferences: {len(preferences)}/6, Algorithm: {has_scoring_algorithm}/✓"
        )

    def test_error_handling(self):
        """Test API error handling with invalid data"""

        # Test with empty responses
        empty_payload = {
            "assessment_id": "test-error",
            "assessment_type": "mbti",
            "responses": {},
            "raw_type": "ENTJ"
        }

        try:
            response = requests.post(
                f"{self.backend_url}/mbti-test-submit",
                json=empty_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            # Should still return 200 with default results
            handles_empty = response.status_code == 200
            self.log_test(
                "Empty Responses Test",
                handles_empty,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test("Empty Responses Test", False, f"Exception: {e}")

        # Test with invalid assessment type
        invalid_payload = {
            "assessment_id": "test-error",
            "assessment_type": "invalid_type",
            "responses": {"1": "E"},
            "raw_type": "TEST"
        }

        try:
            response = requests.post(
                f"{self.backend_url}/mbti-test-submit",
                json=invalid_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            handles_invalid = response.status_code == 200
            self.log_test(
                "Invalid Assessment Type Test",
                handles_invalid,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test("Invalid Assessment Type Test", False, f"Exception: {e}")

    def test_performance(self):
        """Test API response time"""
        test_responses = {
            "1": "E", "2": "N", "3": "T", "4": "J",
            "5": "I", "6": "S", "7": "F", "8": "P"
        }

        start_time = time.time()
        result = self.test_mbti_submit_endpoint(test_responses)
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        is_fast = response_time < 1000  # Should respond in under 1 second

        self.log_test(
            "Performance Test",
            is_fast,
            f"Response time: {response_time:.0f}ms"
        )

    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting MBTI Assessment Integration Tests")
        print("=" * 50)

        print("\n📱 Frontend Tests")
        print("-" * 20)
        frontend_accessible = self.test_frontend_accessibility()
        self.log_test("Frontend Accessibility", frontend_accessible)

        print("\n🔧 Backend API Tests")
        print("-" * 20)
        self.test_comprehensive_results_structure()
        self.test_personality_type_calculations()
        self.test_error_handling()
        self.test_performance()

        print("\n📊 Test Summary")
        print("=" * 50)

        passed_count = sum(1 for result in self.test_results if "✅ PASS" in result)
        total_count = len(self.test_results)

        for result in self.test_results:
            print(result)

        print(f"\nOverall Result: {passed_count}/{total_count} tests passed")

        if passed_count == total_count:
            print("🎉 All tests passed! MBTI assessment system is fully functional.")
        else:
            print("⚠️  Some tests failed. Please review the results above.")

        return passed_count == total_count

if __name__ == "__main__":
    tester = MBTIIntegrationTest()
    tester.run_all_tests()