#!/usr/bin/env python3
"""
Simple JWT Testing Demo
Demonstrates JWT token validation testing framework capabilities
"""

import asyncio
import json
import time
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SimpleJWTTester:
    """Simple JWT testing demonstration"""

    def __init__(self):
        self.test_results = []

    def generate_mock_jwt(self, user_email: str, expires_in_minutes: int = 30) -> str:
        """Generate a mock JWT token for testing"""
        payload = {
            "sub": user_email,
            "exp": int(time.time()) + (expires_in_minutes * 60),
            "iat": int(time.time()),
            "type": "access",
            "jti": hashlib.sha256(f"{user_email}{time.time()}".encode()).hexdigest()[:16],
            "version": "1.0"
        }

        # Using a simple secret for demo
        secret = "demo_secret_key_for_testing_purposes_only"
        return jwt.encode(payload, secret, algorithm="HS256")

    def validate_jwt_structure(self, token: str) -> Dict[str, Any]:
        """Validate JWT token structure"""
        result = {
            "test_name": "JWT Structure Validation",
            "status": "pass",
            "issues": []
        }

        try:
            parts = token.split('.')
            if len(parts) != 3:
                result["status"] = "fail"
                result["issues"].append(f"Invalid JWT structure: expected 3 parts, got {len(parts)}")
                return result

            # Try to decode payload
            payload = json.loads(jwt.base64url_decode(parts[1] + '=='))

            required_claims = ["sub", "exp", "iat", "type"]
            for claim in required_claims:
                if claim not in payload:
                    result["issues"].append(f"Missing required claim: {claim}")

            if result["issues"]:
                result["status"] = "fail"
            else:
                result["details"] = payload

        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"JWT parsing error: {str(e)}")

        return result

    def test_jwt_expiration(self, token: str) -> Dict[str, Any]:
        """Test JWT expiration behavior"""
        result = {
            "test_name": "JWT Expiration Testing",
            "status": "pass",
            "issues": []
        }

        try:
            payload = jwt.decode(token, options={"verify_signature": False})

            exp_time = payload.get("exp")
            iat_time = payload.get("iat")
            now = int(time.time())

            if exp_time and iat_time:
                duration = exp_time - iat_time
                time_remaining = exp_time - now

                result["details"] = {
                    "issued_at": iat_time,
                    "expires_at": exp_time,
                    "duration_seconds": duration,
                    "time_remaining": time_remaining,
                    "is_expired": time_remaining <= 0
                }

                if time_remaining <= 0:
                    result["status"] = "fail"
                    result["issues"].append("Token has expired")
                elif duration < 1500:  # Less than 25 minutes
                    result["issues"].append(f"Token duration too short: {duration} seconds")
                elif duration > 2100:  # More than 35 minutes
                    result["issues"].append(f"Token duration too long: {duration} seconds")
            else:
                result["status"] = "fail"
                result["issues"].append("Token missing expiration claims")

        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Expiration testing error: {str(e)}")

        return result

    def test_jwt_security(self, token: str) -> Dict[str, Any]:
        """Test JWT security features"""
        result = {
            "test_name": "JWT Security Testing",
            "status": "pass",
            "security_score": 100,
            "issues": []
        }

        security_issues = []

        # Test 1: Check for obvious weak points
        if "admin" in token.lower():
            security_issues.append("Token contains admin-related keywords")
            result["security_score"] -= 20

        # Test 2: Check token length
        if len(token) < 100:
            security_issues.append("Token appears too short (possible weak secret)")
            result["security_score"] -= 15
        elif len(token) > 2000:
            security_issues.append("Token appears unusually long")
            result["security_score"] -= 10

        # Test 3: Try to decode and check claims
        try:
            payload = jwt.decode(token, options={"verify_signature": False})

            # Check for sensitive data in payload
            payload_str = json.dumps(payload).lower()
            sensitive_keywords = ["password", "secret", "key", "admin", "root"]
            found_keywords = [kw for kw in sensitive_keywords if kw in payload_str]

            if found_keywords:
                security_issues.append(f"Sensitive data in payload: {', '.join(found_keywords)}")
                result["security_score"] -= 25

            # Check algorithm in header
            header = json.loads(jwt.base64url_decode(token.split('.')[0] + '=='))
            alg = header.get("alg")

            if alg == "none":
                security_issues.append("Token uses 'none' algorithm (insecure)")
                result["security_score"] -= 50
            elif alg not in ["HS256", "RS256", "ES256"]:
                security_issues.append(f"Unusual algorithm: {alg}")
                result["security_score"] -= 10

        except Exception as e:
            security_issues.append(f"Security analysis error: {str(e)}")
            result["security_score"] -= 30

        result["issues"] = security_issues
        if security_issues:
            result["status"] = "fail"

        return result

    def test_invalid_tokens(self) -> Dict[str, Any]:
        """Test rejection of invalid tokens"""
        result = {
            "test_name": "Invalid Token Rejection",
            "status": "pass",
            "issues": []
        }

        invalid_tokens = [
            "",
            "invalid",
            "not.a.jwt",
            "headeronly.payload",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid",
            "tampered.token.signature"
        ]

        for i, invalid_token in enumerate(invalid_tokens):
            try:
                # This should fail
                jwt.decode(invalid_token, options={"verify_signature": False})
                result["issues"].append(f"Token {i+1} was accepted (should be rejected)")
            except Exception:
                # This is expected - invalid tokens should fail
                pass

        if result["issues"]:
            result["status"] = "fail"

        result["details"] = {
            "invalid_tokens_tested": len(invalid_tokens),
            "expected_failures": len(invalid_tokens)
        }

        return result

    def run_demo_tests(self) -> List[Dict[str, Any]]:
        """Run all demo tests"""
        print("🚀 Simple JWT Testing Demo")
        print("=" * 40)

        print("\n🔧 Generating Mock JWT Tokens...")

        # Generate test tokens
        tokens = {
            "valid_30min": self.generate_mock_jwt("user@example.com", 30),
            "valid_7day": self.generate_mock_jwt("user@example.com", 7 * 24 * 60),  # 7 days
            "expired": self.generate_mock_jwt("user@example.com", -1),  # Expired
        }

        print(f"✅ Generated {len(tokens)} test tokens")

        # Run tests on valid token
        print(f"\n📋 Testing JWT Implementation...")

        test_results = []

        # Test 1: JWT Structure
        print("   🧪 JWT Structure Validation...")
        result1 = self.validate_jwt_structure(tokens["valid_30min"])
        test_results.append(result1)

        # Test 2: JWT Expiration
        print("   ⏰ JWT Expiration Testing...")
        result2 = self.test_jwt_expiration(tokens["valid_30min"])
        test_results.append(result2)

        # Test 3: JWT Security
        print("   🔒 JWT Security Testing...")
        result3 = self.test_jwt_security(tokens["valid_30min"])
        test_results.append(result3)

        # Test 4: Invalid Tokens
        print("   🚫 Invalid Token Testing...")
        result4 = self.test_invalid_tokens()
        test_results.append(result4)

        # Test 5: Expired Token
        print("   ⏱️  Expired Token Testing...")
        result5 = self.test_jwt_expiration(tokens["expired"])
        test_results.append(result5)

        return test_results

    def generate_demo_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate demo test report"""

        total_tests = len(results)
        passed_tests = len([r for r in results if r["status"] == "pass"])
        failed_tests = len([r for r in results if r["status"] == "fail"])
        error_tests = len([r for r in results if r["status"] == "error"])

        # Collect all security issues
        all_issues = []
        security_scores = []

        for result in results:
            if "issues" in result:
                all_issues.extend(result["issues"])
            if "security_score" in result:
                security_scores.append(result["security_score"])

        avg_security_score = sum(security_scores) / len(security_scores) if security_scores else 0

        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "error_tests": error_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "avg_security_score": avg_security_score
            },
            "issues": all_issues,
            "recommendations": self.generate_recommendations(results, avg_security_score)
        }

    def generate_recommendations(self, results: List[Dict[str, Any]], security_score: float) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        if security_score < 80:
            recommendations.append("Review JWT security implementation")

        if any("duration" in issue.lower() for issue in sum([r.get("issues", []) for r in results], [])):
            recommendations.append("Adjust JWT token lifetimes to appropriate durations")

        if any("sensitive data" in issue.lower() for issue in sum([r.get("issues", []) for r in results], [])):
            recommendations.append("Remove sensitive data from JWT payload")

        if security_score < 50:
            recommendations.append("Implement stronger JWT security measures")

        if security_score >= 90:
            recommendations.append("JWT implementation appears secure")

        return recommendations

    def print_demo_report(self, report: Dict[str, Any]) -> None:
        """Print comprehensive demo report"""
        print(f"\n📊 JWT Testing Demo Report")
        print("=" * 30)

        summary = report["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']} ({summary['success_rate']:.1f}%)")
        print(f"❌ Failed: {summary['failed_tests']}")
        print(f"⚠️  Errors: {summary['error_tests']}")
        print(f"🔒 Security Score: {summary['avg_security_score']:.1f}/100")

        if report["issues"]:
            print(f"\n🔍 Issues Found:")
            for i, issue in enumerate(report["issues"][:5], 1):
                print(f"   {i}. {issue}")
            if len(report["issues"]) > 5:
                print(f"   ... and {len(report['issues']) - 5} more issues")

        if report["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")

        print(f"\n🎯 Assessment:")
        if summary['success_rate'] == 100:
            print("   ✅ All JWT tests passed - implementation appears secure!")
        elif summary['success_rate'] >= 80:
            print("   ✅ Good JWT implementation with minor issues")
        elif summary['success_rate'] >= 60:
            print("   ⚠️  Acceptable JWT implementation - improvements needed")
        else:
            print("   ❌ JWT implementation requires significant improvements")

def main():
    """Main demo function"""
    print("🔐 JWT Token Testing Framework Demo")
    print("This demonstrates the JWT testing capabilities we've built for PsychSync")
    print("=" * 70)

    tester = SimpleJWTTester()

    try:
        # Run the demo tests
        results = tester.run_demo_tests()

        # Generate and print report
        report = tester.generate_demo_report(results)
        tester.print_demo_report(report)

        print(f"\n🚀 JWT Testing Framework Ready!")
        print(f"The comprehensive test suite includes:")
        print(f"  - Token structure validation")
        print(f"  - Expiration time testing")
        print(f"  - Security vulnerability detection")
        print(f"  - Performance analysis")
        print(f"  - Concurrent usage testing")
        print(f"  - Token blacklisting validation")
        print(f"  - Integration with Postman collections")
        print(f"\nTo use with your API:")
        print(f"  python comprehensive_jwt_tests.py --quick")
        print(f"  python jwt_token_test_suite.py --security")
        print(f"  python postman_test_runner.py --collection postman_jwt_token_collection.json")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
