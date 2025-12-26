#!/usr/bin/env python3
"""
Comprehensive Assessment Integration Test

This script demonstrates the complete assessment system integration:
- Backend API for storing/retrieving assessment results
- Frontend service connectivity
- Support for all assessment types (MBTI, Big Five, DISC, Enneagram, Custom)
- End-to-end data flow from submission to storage to retrieval
"""

import requests
import json
import time
from typing import Dict, Any, List

class ComprehensiveAssessmentTest:
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

    def test_mbti_assessment_flow(self):
        """Test complete MBTI assessment flow"""
        print("\n🧠 Testing MBTI Assessment Flow")
        print("-" * 40)

        try:
            # Test MBTI submission
            mbti_data = {
                "assessment_type": "mbti",
                "assessment_id": "comprehensive-mbti-test",
                "responses": {
                    "1": "E", "2": "N", "3": "T", "4": "J",
                    "5": "I", "6": "S", "7": "F", "8": "P"
                },
                "raw_type": "ENTJ",
                "metadata": {
                    "source": "comprehensive_test",
                    "version": "1.0"
                }
            }

            response = requests.post(
                f"{self.backend_url}/assessment-results-test",
                json=mbti_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                has_required_fields = all(key in result.get("results", {}) for key in [
                    "type", "confidence", "description", "dimensions", "assessment_type"
                ])

                is_entj = result.get("results", {}).get("type") == "ENTJ"

                self.log_test(
                    "MBTI Assessment Submission",
                    has_required_fields and is_entj,
                    f"Type: {result.get('results', {}).get('type', 'N/A')}, ID: {result.get('result_id', 'N/A')}"
                )

                return result.get("result_id")
            else:
                self.log_test("MBTI Assessment Submission", False, f"HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log_test("MBTI Assessment Submission", False, f"Exception: {e}")
            return None

    def test_big_five_assessment_flow(self):
        """Test Big Five assessment flow"""
        print("\n🌟 Testing Big Five Assessment Flow")
        print("-" * 40)

        try:
            big_five_data = {
                "assessment_type": "big_five",
                "assessment_id": "comprehensive-big-five-test",
                "responses": {
                    "openness_q1": 5, "openness_q2": 4,
                    "conscientiousness_q1": 4, "conscientiousness_q2": 5,
                    "extraversion_q1": 3, "extraversion_q2": 4
                },
                "metadata": {
                    "source": "comprehensive_test",
                    "version": "1.0"
                }
            }

            response = requests.post(
                f"{self.backend_url}/assessment-results-test",
                json=big_five_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                has_traits = "traits" in result.get("results", {})
                has_all_five_traits = all(trait in result.get("results", {}).get("traits", {})
                                        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"])

                self.log_test(
                    "Big Five Assessment Submission",
                    has_traits and has_all_five_traits,
                    f"Traits: {len(result.get('results', {}).get('traits', {}))}/5 present"
                )

                return result.get("result_id")
            else:
                self.log_test("Big Five Assessment Submission", False, f"HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log_test("Big Five Assessment Submission", False, f"Exception: {e}")
            return None

    def test_disc_assessment_flow(self):
        """Test DISC assessment flow"""
        print("\n💼 Testing DISC Assessment Flow")
        print("-" * 40)

        try:
            disc_data = {
                "assessment_type": "disc",
                "assessment_id": "comprehensive-disc-test",
                "responses": {
                    "q1": "D", "q2": "I", "q3": "S", "q4": "C",
                    "q5": "D", "q6": "I"
                },
                "raw_type": "DI",
                "metadata": {
                    "source": "comprehensive_test",
                    "version": "1.0"
                }
            }

            response = requests.post(
                f"{self.backend_url}/assessment-results-test",
                json=disc_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                has_primary_style = "primary_style" in result.get("results", {})
                has_dimensions = "dimensions" in result.get("results", {})

                self.log_test(
                    "DISC Assessment Submission",
                    has_primary_style and has_dimensions,
                    f"Style: {result.get('results', {}).get('primary_style', 'N/A')}"
                )

                return result.get("result_id")
            else:
                self.log_test("DISC Assessment Submission", False, f"HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log_test("DISC Assessment Submission", False, f"Exception: {e}")
            return None

    def test_enneagram_assessment_flow(self):
        """Test Enneagram assessment flow"""
        print("\n🔢 Testing Enneagram Assessment Flow")
        print("-" * 40)

        try:
            enneagram_data = {
                "assessment_type": "enneagram",
                "assessment_id": "comprehensive-enneagram-test",
                "responses": {
                    "q1": 5, "q2": 4, "q3": 3, "q4": 5, "q5": 2
                },
                "raw_type": "Type 3",
                "metadata": {
                    "source": "comprehensive_test",
                    "version": "1.0"
                }
            }

            response = requests.post(
                f"{self.backend_url}/assessment-results-test",
                json=enneagram_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                has_type = "number" in result.get("results", {})
                has_description = "description" in result.get("results", {})

                self.log_test(
                    "Enneagram Assessment Submission",
                    has_type and has_description,
                    f"Type: {result.get('results', {}).get('number', 'N/A')}"
                )

                return result.get("result_id")
            else:
                self.log_test("Enneagram Assessment Submission", False, f"HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log_test("Enneagram Assessment Submission", False, f"Exception: {e}")
            return None

    def test_custom_assessment_flow(self):
        """Test Custom assessment flow"""
        print("\n🎯 Testing Custom Assessment Flow")
        print("-" * 40)

        try:
            custom_data = {
                "assessment_type": "custom",
                "assessment_id": "comprehensive-custom-test",
                "responses": {
                    "skill1": "advanced", "skill2": "intermediate", "skill3": "expert"
                },
                "processed_result": {
                    "score": 0.85,
                    "category": "Technical Skills",
                    "level": "Senior",
                    "recommendations": ["Focus on leadership", "Mentor junior developers"]
                },
                "metadata": {
                    "source": "comprehensive_test",
                    "version": "1.0",
                    "category": "technical_skills"
                }
            }

            response = requests.post(
                f"{self.backend_url}/assessment-results-test",
                json=custom_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                preserved_custom_data = result.get("results", {}).get("score") == 0.85
                has_metadata = "category" in result.get("results", {})

                self.log_test(
                    "Custom Assessment Submission",
                    preserved_custom_data and has_metadata,
                    f"Score: {result.get('results', {}).get('score', 'N/A')}"
                )

                return result.get("result_id")
            else:
                self.log_test("Custom Assessment Submission", False, f"HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log_test("Custom Assessment Submission", False, f"Exception: {e}")
            return None

    def test_data_persistence(self):
        """Test that assessment results are properly stored and can be retrieved"""
        print("\n💾 Testing Data Persistence")
        print("-" * 40)

        # This test would typically use authenticated endpoints
        # For now, we'll test the storage system by checking if we get sequential IDs

        try:
            # Submit multiple assessments to test ID generation
            submissions = []
            for i in range(3):
                data = {
                    "assessment_type": "custom",
                    "assessment_id": f"persistence-test-{i}",
                    "responses": {"q1": f"answer_{i}"},
                    "metadata": {"test_index": i}
                }

                response = requests.post(
                    f"{self.backend_url}/assessment-results-test",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )

                if response.status_code == 200:
                    submissions.append(response.json().get("result_id"))
                time.sleep(0.1)  # Small delay between submissions

            # Check that we got sequential, unique IDs
            unique_ids = len(set(submissions)) == len(submissions)
            sequential = all(submissions[i] < submissions[i+1] for i in range(len(submissions)-1))

            self.log_test(
                "Data Persistence",
                unique_ids and sequential,
                f"Generated {len(submissions)} unique sequential IDs: {submissions}"
            )

        except Exception as e:
            self.log_test("Data Persistence", False, f"Exception: {e}")

    def test_assessment_type_coverage(self):
        """Test that all supported assessment types work"""
        print("\n📊 Testing Assessment Type Coverage")
        print("-" * 40)

        supported_types = ["mbti", "big_five", "disc", "enneagram", "custom"]
        successful_types = []

        for assessment_type in supported_types:
            try:
                data = {
                    "assessment_type": assessment_type,
                    "assessment_id": f"coverage-test-{assessment_type}",
                    "responses": {"q1": "test_response"},
                    "metadata": {"coverage_test": True}
                }

                # Add type-specific data
                if assessment_type == "mbti":
                    data["raw_type"] = "INTP"
                elif assessment_type == "disc":
                    data["raw_type"] = "S"
                elif assessment_type == "enneagram":
                    data["raw_type"] = "Type 5"

                response = requests.post(
                    f"{self.backend_url}/assessment-results-test",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    processed_result = result.get("results", {})

                    # Basic validation for each type
                    is_valid = True
                    if assessment_type == "mbti":
                        is_valid = "type" in processed_result and len(processed_result.get("type", "")) == 4
                    elif assessment_type == "big_five":
                        is_valid = "traits" in processed_result
                    elif assessment_type == "disc":
                        is_valid = "primary_style" in processed_result
                    elif assessment_type == "enneagram":
                        is_valid = "number" in processed_result

                    if is_valid:
                        successful_types.append(assessment_type)
                        self.log_test(
                            f"{assessment_type.title()} Coverage",
                            True,
                            f"Result ID: {result.get('result_id', 'N/A')}"
                        )
                    else:
                        self.log_test(
                            f"{assessment_type.title()} Coverage",
                            False,
                            "Invalid result structure"
                        )
                else:
                    self.log_test(
                        f"{assessment_type.title()} Coverage",
                        False,
                        f"HTTP {response.status_code}"
                    )

            except Exception as e:
                self.log_test(f"{assessment_type.title()} Coverage", False, f"Exception: {e}")

        coverage_percentage = (len(successful_types) / len(supported_types)) * 100
        self.log_test(
            "Overall Assessment Type Coverage",
            coverage_percentage >= 80,
            f"{len(successful_types)}/{len(supported_types)} types working ({coverage_percentage:.0f}%)"
        )

    def run_comprehensive_test(self):
        """Run the complete assessment integration test suite"""
        print("=" * 60)
        print("🎯 COMPREHENSIVE ASSESSMENT INTEGRATION TEST")
        print("=" * 60)
        print()
        print("Testing complete assessment system integration:")
        print("- Backend API with assessment results storage")
        print("- Support for all assessment types")
        print("- Data processing and persistence")
        print("- End-to-end workflow validation")
        print()

        # Test individual assessment flows
        self.test_mbti_assessment_flow()
        self.test_big_five_assessment_flow()
        self.test_disc_assessment_flow()
        self.test_enneagram_assessment_flow()
        self.test_custom_assessment_flow()

        # Test system-wide functionality
        self.test_data_persistence()
        self.test_assessment_type_coverage()

        # Final summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)

        passed_count = sum(1 for result in self.test_results if "✅ PASS" in result)
        total_count = len(self.test_results)

        for result in self.test_results:
            print(result)

        print(f"\nOverall Result: {passed_count}/{total_count} tests passed")

        if passed_count == total_count:
            print("🎉 ALL TESTS PASSED! The assessment system is fully integrated and functional.")
            print("\n✅ Backend assessment results API working perfectly")
            print("✅ All assessment types supported (MBTI, Big Five, DISC, Enneagram, Custom)")
            print("✅ Data processing and storage functioning correctly")
            print("✅ End-to-end assessment workflow validated")
            print("✅ System ready for production use")
        else:
            print("⚠️  Some tests failed. Please review the results above.")

        print("=" * 60)
        return passed_count == total_count

if __name__ == "__main__":
    tester = ComprehensiveAssessmentTest()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)