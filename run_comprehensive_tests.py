#!/usr/bin/env python3
"""
Comprehensive Test Runner for All Implemented Features
"""

import sys
import os
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path

def run_command(command, description, timeout=60):
    """Run a command with timeout and error handling"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")

    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )

        execution_time = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ PASSED ({execution_time:.2f}s)")
            if result.stdout:
                print("Output:")
                print(result.stdout)
            return True, result.stdout, execution_time
        else:
            print(f"❌ FAILED ({execution_time:.2f}s)")
            print("Error output:")
            print(result.stderr)
            if result.stdout:
                print("Standard output:")
                print(result.stdout)
            return False, result.stderr, execution_time

    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT (>{timeout}s)")
        return False, "Command timed out", timeout
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return False, str(e), 0

def check_prerequisites():
    """Check if required dependencies are available"""
    print("🔍 Checking prerequisites...")

    prerequisites = [
        ("python --version", "Python version"),
        ("pip --version", "Pip availability"),
        ("node --version", "Node.js availability"),
        ("npm --version", "NPM availability")
    ]

    all_good = True
    for command, description in prerequisites:
        success, _, _ = run_command(command, f"Checking {description}", timeout=10)
        if not success:
            all_good = False
            print(f"❌ {description} not available")

    return all_good

def install_python_dependencies():
    """Install required Python dependencies for testing"""
    print("\n📦 Installing Python testing dependencies...")

    dependencies = [
        "pytest",
        "pytest-asyncio",
        "pytest-mock",
        "httpx",
        "fastapi",
        "sqlalchemy",
        "alembic"
    ]

    for dep in dependencies:
        success, _, _ = run_command(f"pip install {dep}", f"Installing {dep}", timeout=120)
        if not success:
            print(f"⚠️  Failed to install {dep}, continuing...")

def run_backend_tests():
    """Run all backend tests"""
    print("\n🚀 Running Backend Tests")

    backend_tests = [
        ("python -m pytest tests/test_enhanced_ai_service.py -v", "Enhanced AI Service Tests", 120),
        ("python -m pytest tests/test_assessment_integration.py -v", "Assessment Integration Tests", 120),
        ("python -m pytest tests/test_enhanced_backend.py -v", "Enhanced Backend Tests", 180),
        ("python -m pytest tests/ -k 'test_' --tb=short --maxfail=3", "All Backend Tests", 300)
    ]

    results = []
    for command, description, timeout in backend_tests:
        success, output, exec_time = run_command(command, description, timeout)
        results.append({
            'test': description,
            'success': success,
            'execution_time': exec_time,
            'output': output[:500] if output else ""  # Truncate output
        })

    return results

def run_frontend_tests():
    """Run frontend tests"""
    print("\n⚛️ Running Frontend Tests")

    frontend_tests = [
        ("cd frontend && npm install", "Install Frontend Dependencies", 180),
        ("cd frontend && npm run type-check", "TypeScript Type Checking", 120),
        ("cd frontend && npm run test", "Frontend Unit Tests", 120),
        ("cd frontend && npm run lint", "ESLint Code Quality", 60),
        ("cd frontend && npm run build", "Frontend Build Test", 120)
    ]

    results = []
    for command, description, timeout in frontend_tests:
        success, output, exec_time = run_command(command, description, timeout)
        results.append({
            'test': description,
            'success': success,
            'execution_time': exec_time,
            'output': output[:500] if output else ""
        })

    return results

def run_integration_tests():
    """Run integration tests"""
    print("\n🔗 Running Integration Tests")

    # Test enhanced backend startup
    backend_tests = [
        ("python -c 'import app.services.enhanced_ai_service; print(\"✅ Enhanced AI Service imports successfully\")'",
         "Enhanced AI Service Import Test", 30),
        ("python -c 'from app.services.enhanced_ai_service import enhanced_ai_processor; result = enhanced_ai_processor.process_enhanced_assessment(\"mbti\", {\"type\": \"INTJ\", \"confidence\": 0.9}); print(\"✅ AI Processing test passed\")'",
         "Enhanced AI Processing Test", 60),
        ("python -c 'import json; print(json.dumps({\"test\": \"JSON serialization works\"}, indent=2))'",
         "JSON Processing Test", 30)
    ]

    results = []
    for command, description, timeout in backend_tests:
        success, output, exec_time = run_command(command, description, timeout)
        results.append({
            'test': description,
            'success': success,
            'execution_time': exec_time,
            'output': output[:500] if output else ""
        })

    return results

def run_performance_tests():
    """Run performance tests"""
    print("\n⚡ Running Performance Tests")

    performance_tests = [
        ("python -c 'import time; start = time.time(); [i**2 for i in range(10000)]; print(f\"✅ List comprehension performance: {(time.time()-start)*1000:.2f}ms\")'",
         "Basic Python Performance", 30),
        ("python -c 'import time; start = time.time(); import json; data = {\"test\": \"value\"} * 1000; json.dumps(data); print(f\"✅ JSON serialization performance: {(time.time()-start)*1000:.2f}ms\")'",
         "JSON Serialization Performance", 30)
    ]

    results = []
    for command, description, timeout in performance_tests:
        success, output, exec_time = run_command(command, description, timeout)
        results.append({
            'test': description,
            'success': success,
            'execution_time': exec_time,
            'output': output[:500] if output else ""
        })

    return results

def generate_test_report(all_results):
    """Generate comprehensive test report"""
    print("\n📊 Generating Test Report")

    # Calculate statistics
    total_tests = sum(len(results) for results in all_results.values())
    total_passed = sum(len([r for r in results if r['success']]) for results in all_results.values())
    total_time = sum(r['execution_time'] for results in all_results.values() for r in results)

    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    report = {
        'test_summary': {
            'total_tests': total_tests,
            'passed_tests': total_passed,
            'failed_tests': total_tests - total_passed,
            'success_rate_percent': round(success_rate, 2),
            'total_execution_time_seconds': round(total_time, 2),
            'timestamp': datetime.now().isoformat()
        },
        'test_categories': {}
    }

    for category, results in all_results.items():
        category_passed = len([r for r in results if r['success']])
        category_total = len(results)
        category_time = sum(r['execution_time'] for r in results)

        report['test_categories'][category] = {
            'total_tests': category_total,
            'passed_tests': category_passed,
            'failed_tests': category_total - category_passed,
            'success_rate_percent': round((category_passed / category_total * 100) if category_total > 0 else 0, 2),
            'execution_time_seconds': round(category_time, 2),
            'tests': results
        }

    # Save report to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    # Print summary
    print(f"\n{'='*80}")
    print("🎯 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed: {total_passed}")
    print(f"Tests Failed: {total_tests - total_passed}")
    print(f"Overall Success Rate: {success_rate:.1f}%")
    print(f"Total Execution Time: {total_time:.2f}s")
    print(f"Report Saved: {report_file}")

    # Category breakdown
    print(f"\n📋 Category Breakdown:")
    for category, results in all_results.items():
        category_passed = len([r for r in results if r['success']])
        category_total = len(results)
        category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
        print(f"  {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")

    # Failed tests details
    failed_tests = []
    for category, results in all_results.items():
        for test in results:
            if not test['success']:
                failed_tests.append(f"{category} - {test['test']}")

    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    else:
        print(f"\n🎉 All tests passed!")

    print(f"{'='*80}")

    return report

def main():
    """Main test runner"""
    print("🚀 COMPREHENSIVE PSYCHSYNC TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed. Please install required dependencies.")
        sys.exit(1)

    # Install dependencies
    install_python_dependencies()

    # Run all test categories
    all_results = {}

    try:
        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE TESTING")
        print("="*80)

        # Backend Tests
        all_results['backend_tests'] = run_backend_tests()

        # Frontend Tests
        all_results['frontend_tests'] = run_frontend_tests()

        # Integration Tests
        all_results['integration_tests'] = run_integration_tests()

        # Performance Tests
        all_results['performance_tests'] = run_performance_tests()

    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {str(e)}")
        sys.exit(1)

    # Generate final report
    report = generate_test_report(all_results)

    # Exit with appropriate code
    total_failed = sum(len([r for r in results if not r['success']]) for results in all_results.values())
    if total_failed > 0:
        print(f"\n⚠️ {total_failed} tests failed. Check the report for details.")
        sys.exit(1)
    else:
        print(f"\n🎉 All tests passed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()