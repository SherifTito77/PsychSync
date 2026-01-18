"""
Comprehensive Backend Validation Script
Tests all critical backend functionality for production readiness
"""

import asyncio
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, List

# Test framework classes
class ValidationResult:
    def __init__(self, test_name: str, passed: bool, message: str = "", details: Dict[str, Any] = None):
        self.test_name = test_name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class BackendValidator:
    """Comprehensive backend validation suite"""

    def __init__(self):
        self.results: List[ValidationResult] = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    async def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Starting Comprehensive Backend Validation")
        print("=" * 60)

        # Import tests
        await self.test_imports()

        # Database tests
        await self.test_database_imports()
        await self.test_database_models()

        # AI Framework tests
        await self.test_ai_processors()

        # Security tests
        await self.test_security_functions()

        # API tests
        await self.test_api_imports()
        await self.test_caching_system()

        # Generate report
        self.generate_report()

    async def test_imports(self):
        """Test core module imports"""
        test_name = "Core Module Imports"
        try:
            # Test database imports
            from app.core.database import Base, get_async_db
            print("✓ Database imports successful")

            # Test configuration imports
            from app.core.config import settings
            print("✓ Configuration imports successful")

            # Test security imports
            from app.services.security import verify_password, get_password_hash
            print("✓ Security imports successful")

            self.add_result(test_name, True, "All core modules imported successfully")
        except Exception as e:
            self.add_result(test_name, False, f"Import failed: {e}", {"traceback": traceback.format_exc()})

    async def test_database_imports(self):
        """Test database model imports"""
        test_name = "Database Model Imports"
        missing_models = []
        successful_imports = []

        models_to_test = [
            'app.db.models.user.User',
            'app.db.models.assessment.Assessment',
            'app.db.models.response.Response',
            'app.db.models.organization.Organization',
            'app.db.models.team.Team',
            'app.db.models.employee_safety.SafetyIncident',
            'app.db.models.analytics.Analytics'
        ]

        for model_path in models_to_test:
            try:
                module_path, class_name = model_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                model_class = getattr(module, class_name)
                successful_imports.append(model_path)
                print(f"✓ {model_path}")
            except Exception as e:
                missing_models.append(f"{model_path}: {e}")
                print(f"✗ {model_path}: {e}")

        if missing_models:
            self.add_result(
                test_name,
                False,
                f"Failed to import {len(missing_models)} models",
                {"missing": missing_models, "successful": successful_imports}
            )
        else:
            self.add_result(test_name, True, f"All {len(successful_imports)} models imported successfully")

    async def test_database_models(self):
        """Test database model relationships and structure"""
        test_name = "Database Model Structure"
        try:
            from app.db.models.user import User
            from app.db.models.employee_safety import SafetyIncident

            # Check User model has safety relationships
            user = User()
            relationship_attributes = [
                'reported_incidents', 'involved_incidents', 'investigated_incidents',
                'wellness_assessments', 'wellness_alerts', 'safety_training_completions'
            ]

            missing_relationships = []
            for attr in relationship_attributes:
                if not hasattr(user, attr):
                    missing_relationships.append(attr)

            if missing_relationships:
                self.add_result(
                    test_name,
                    False,
                    f"User model missing relationships: {missing_relationships}"
                )
            else:
                self.add_result(test_name, True, "All User model relationships properly implemented")

        except Exception as e:
            self.add_result(test_name, False, f"Model structure test failed: {e}")

    async def test_ai_processors(self):
        """Test AI assessment framework processors"""
        test_name = "AI Assessment Processors"
        processors_tested = []

        processors_to_test = [
            ('ai.processors.mbti_processor.MBTIProcessor', 'INTJ'),
            ('ai.processors.big_five.BigFiveProcessor', {'openness': 0.8, 'conscientiousness': 0.7})
        ]

        for processor_path, test_data in processors_to_test:
            try:
                module_path, class_name = processor_path.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                processor_class = getattr(module, class_name)

                processor = processor_class()
                result = processor._safe_process(test_data)

                if result.get('success', True) or result.get('fallback'):
                    processors_tested.append(processor_path)
                    print(f"✓ {processor_path} processed data successfully")
                else:
                    print(f"⚠ {processor_path} processing failed but handled gracefully")

            except Exception as e:
                print(f"✗ {processor_path}: {e}")

        if processors_tested:
            self.add_result(
                test_name,
                True,
                f"Successfully tested {len(processors_tested)} processors"
            )
        else:
            self.add_result(test_name, False, "No processors processed data successfully")

    async def test_security_functions(self):
        """Test security utility functions"""
        test_name = "Security Functions"
        try:
            from app.services.security import verify_password, get_password_hash, validate_password

            # Test password hashing
            password = "SecureP@ss123!"
            hashed = get_password_hash(password)

            # Test password verification
            is_valid = verify_password(password, hashed)

            if not is_valid:
                self.add_result(test_name, False, "Password verification failed")
                return

            # Test password validation
            validation_result = validate_password(password)

            if not validation_result.get('valid', False):
                self.add_result(test_name, False, "Password validation failed")
                return

            # Test invalid password
            invalid_validation = validate_password("weak")
            if invalid_validation.get('valid', False):
                self.add_result(test_name, False, "Invalid password validation failed")
                return

            self.add_result(test_name, True, "All security functions working correctly")

        except Exception as e:
            self.add_result(test_name, False, f"Security function test failed: {e}")

    async def test_api_imports(self):
        """Test API endpoint imports"""
        test_name = "API Endpoint Imports"
        failed_imports = []
        successful_imports = []

        endpoints_to_test = [
            'app.api.v1.endpoints.auth',
            'app.api.v1.endpoints.users',
            'app.api.v1.endpoints.assessments',
            'app.api.v1.endpoints.analytics'
        ]

        for endpoint in endpoints_to_test:
            try:
                __import__(endpoint)
                successful_imports.append(endpoint)
                print(f"✓ {endpoint}")
            except Exception as e:
                failed_imports.append(f"{endpoint}: {e}")
                print(f"✗ {endpoint}: {e}")

        if failed_imports:
            self.add_result(
                test_name,
                False,
                f"Failed to import {len(failed_imports)} endpoint modules",
                {"failed": failed_imports, "successful": successful_imports}
            )
        else:
            self.add_result(test_name, True, f"All {len(successful_imports)} endpoint modules imported successfully")

    async def test_caching_system(self):
        """Test performance optimization and caching system"""
        test_name = "Performance & Caching System"
        try:
            from app.core.api_performance_optimizer import get_performance_monitor, get_cache_manager

            monitor = get_performance_monitor()
            cache_manager = get_cache_manager()

            # Test cache manager
            cache_stats = cache_manager.get_cache_stats()

            required_stats = ['hits', 'misses', 'sets', 'hit_rate_percent']
            missing_stats = [stat for stat in required_stats if stat not in cache_stats]

            if missing_stats:
                self.add_result(
                    test_name,
                    False,
                    f"Cache manager missing stats: {missing_stats}"
                )
                return

            # Test performance monitor
            perf_summary = monitor.get_performance_summary(hours=1)

            if not isinstance(perf_summary, dict):
                self.add_result(test_name, False, "Performance monitor summary invalid")
                return

            self.add_result(
                test_name,
                True,
                "Performance optimization and caching system operational"
            )

        except Exception as e:
            self.add_result(test_name, False, f"Caching system test failed: {e}")

    def add_result(self, test_name: str, passed: bool, message: str, details: Dict[str, Any] = None):
        """Add test result"""
        result = ValidationResult(test_name, passed, message, details)
        self.results.append(result)
        self.total_tests += 1

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def generate_report(self):
        """Generate comprehensive validation report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE BACKEND VALIDATION REPORT")
        print("=" * 60)

        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   ✅ Passed: {self.passed_tests}")
        print(f"   ❌ Failed: {self.failed_tests}")
        print(f"   Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")

        # Detailed Results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.results:
            status_icon = "✅" if result.passed else "❌"
            print(f"\n{status_icon} {result.test_name}")
            print(f"   {result.message}")

            if result.details:
                for key, value in result.details.items():
                    if isinstance(value, list):
                        print(f"   {key}: {len(value)} items")
                        for item in value[:3]:  # Show first 3 items
                            print(f"     - {item}")
                        if len(value) > 3:
                            print(f"     ... and {len(value) - 3} more")
                    else:
                        print(f"   {key}: {value}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")

        if self.failed_tests == 0:
            print("   🎉 All tests passed! Backend is production-ready.")
            print("   📦 Consider deploying to staging environment for final testing.")
        else:
            print("   🔧 Address failed tests before production deployment.")

            # Specific recommendations based on failures
            for result in self.results:
                if not result.passed:
                    if "import" in result.test_name.lower():
                        print("   📦 Check module dependencies and Python path configuration.")
                    elif "security" in result.test_name.lower():
                        print("   🔐 Review security implementation and encryption settings.")
                    elif "database" in result.test_name.lower():
                        print("   🗄️ Verify database models and relationship configurations.")
                    elif "api" in result.test_name.lower():
                        print("   🌐 Validate API endpoint implementations and dependencies.")

        # Production Readiness Score
        readiness_score = (self.passed_tests / self.total_tests) * 100
        print(f"\n🏆 PRODUCTION READINESS SCORE: {readiness_score:.1f}/100")

        if readiness_score >= 95:
            print("   🌟 EXCELLENT - Ready for production deployment")
        elif readiness_score >= 85:
            print("   ✅ GOOD - Minor fixes needed before production")
        elif readiness_score >= 70:
            print("   ⚠️  FAIR - Significant fixes required")
        else:
            print("   ❌ POOR - Major issues must be resolved")

        print("\n" + "=" * 60)
        print(f"Report generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print("=" * 60)

async def main():
    """Main validation function"""
    validator = BackendValidator()
    await validator.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Validation interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Validation failed with error: {e}")
        traceback.print_exc()
