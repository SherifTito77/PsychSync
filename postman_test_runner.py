#!/usr/bin/env python3
"""
Postman Authentication Test Runner
Automated test runner for PsychSync authentication endpoints

Usage:
    python postman_test_runner.py [--env=development] [--suite=auth] [--report=json]
"""

import json
import requests
import time
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class TestResult:
    """Represents a single test result"""
    name: str
    status: str  # 'pass', 'fail', 'error'
    response_code: int
    response_time: float
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None

@dataclass
class TestSuiteResult:
    """Represents results for a test suite"""
    name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    total_time: float
    results: List[TestResult]

class PostmanTestRunner:
    """Runs Postman collections programmatically"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'PostmanTestRunner/1.0'
        })
        self.tokens = {}  # Store tokens for authenticated requests

    def load_collection(self, collection_path: str) -> Dict:
        """Load Postman collection from JSON file"""
        try:
            with open(collection_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading collection {collection_path}: {e}")
            return {}

    def substitute_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Replace {{variable}} placeholders with actual values"""
        for key, value in variables.items():
            text = text.replace(f"{{{{{key}}}}}", value)
        return text

    def execute_request(self, request_data: Dict, variables: Dict[str, str]) -> TestResult:
        """Execute a single request and return test result"""
        try:
            # Prepare URL
            raw_url = request_data.get('url', {}).get('raw', '')
            url = self.substitute_variables(raw_url, variables)
            if not url.startswith('http'):
                url = f"{self.base_url}{url}"

            # Prepare method
            method = request_data.get('method', 'GET').upper()

            # Prepare headers
            headers = {}
            for header in request_data.get('header', []):
                if header.get('enabled', True):
                    key = self.substitute_variables(header['key'], variables)
                    value = self.substitute_variables(header['value'], variables)
                    headers[key] = value

            # Prepare body
            body = None
            body_mode = request_data.get('body', {}).get('mode', '')
            if body_mode == 'raw':
                raw_body = request_data.get('body', {}).get('raw', '')
                body = self.substitute_variables(raw_body, variables)
            elif body_mode == 'urlencoded':
                body = {}
                for item in request_data.get('body', {}).get('urlencoded', []):
                    key = self.substitute_variables(item['key'], variables)
                    value = self.substitute_variables(item['value'], variables)
                    body[key] = value

            # Handle form data for login
            if 'username' in body and 'password' in body:
                # Use form-encoded content type
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                body = f"username={body['username']}&password={body['password']}"

            # Execute request
            start_time = time.time()
            if method == 'GET':
                response = self.session.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if headers.get('Content-Type') == 'application/x-www-form-urlencoded':
                    response = self.session.post(url, data=body, headers=headers, timeout=30)
                else:
                    response = self.session.post(url, json=json.loads(body) if body else None, headers=headers, timeout=30)
            elif method == 'PUT':
                response = self.session.put(url, json=json.loads(body) if body else None, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response_time = time.time() - start_time

            # Parse response
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {'raw_response': response.text}

            return TestResult(
                name=request_data.get('description', 'Unknown Request'),
                status='pass' if 200 <= response.status_code < 300 else 'fail',
                response_code=response.status_code,
                response_time=response_time * 1000,  # Convert to ms
                response_data=response_data
            )

        except requests.exceptions.Timeout:
            return TestResult(
                name=request_data.get('description', 'Unknown Request'),
                status='error',
                response_code=0,
                response_time=30000,
                error_message='Request timeout'
            )
        except requests.exceptions.ConnectionError:
            return TestResult(
                name=request_data.get('description', 'Unknown Request'),
                status='error',
                response_code=0,
                response_time=0,
                error_message='Connection error'
            )
        except Exception as e:
            return TestResult(
                name=request_data.get('description', 'Unknown Request'),
                status='error',
                response_code=0,
                response_time=0,
                error_message=str(e)
            )

    def run_test_suite(self, collection: Dict, suite_name: str = "Authentication") -> TestSuiteResult:
        """Run a test suite from Postman collection"""
        print(f"\n🚀 Running {suite_name} Test Suite")
        print("=" * 50)

        results = []
        total_time = 0

        # Find all items in the collection
        items = collection.get('item', [])

        # Handle nested folder structures
        def process_items(items_list, path=""):
            nonlocal results, total_time

            for item in items_list:
                if 'item' in item:  # Folder
                    folder_name = item.get('name', 'Unknown Folder')
                    new_path = f"{path}/{folder_name}" if path else folder_name
                    process_items(item['item'], new_path)
                elif 'request' in item:  # Request
                    try:
                        # Prepare variables
                        variables = {
                            'baseUrl': self.base_url,
                            **self.tokens
                        }

                        # Execute request
                        result = self.execute_request(item['request'], variables)
                        result.name = f"{path}/{result.name}" if path else result.name
                        results.append(result)
                        total_time += result.response_time

                        # Print test result
                        status_icon = "✅" if result.status == 'pass' else "❌" if result.status == 'fail' else "⚠️"
                        print(f"{status_icon} {result.name}: {result.response_code} ({result.response_time:.0f}ms)")

                        # Store tokens from successful authentication
                        if result.status == 'pass' and result.response_data:
                            if 'access_token' in str(result.response_data):
                                try:
                                    data = result.response_data
                                    if isinstance(data, dict):
                                        if 'data' in data and 'access_token' in data['data']:
                                            self.tokens['accessToken'] = data['data']['access_token']
                                        elif 'access_token' in data:
                                            self.tokens['accessToken'] = data['access_token']
                                except:
                                    pass

                        # Small delay between requests
                        time.sleep(0.1)

                    except Exception as e:
                        print(f"⚠️  Error executing {item.get('name', 'Unknown')}: {e}")
                        results.append(TestResult(
                            name=f"{path}/{item.get('name', 'Unknown')}" if path else item.get('name', 'Unknown'),
                            status='error',
                            response_code=0,
                            response_time=0,
                            error_message=str(e)
                        ))

        process_items(items)

        # Calculate statistics
        total_tests = len(results)
        passed_tests = len([r for r in results if r.status == 'pass'])
        failed_tests = len([r for r in results if r.status == 'fail'])
        error_tests = len([r for r in results if r.status == 'error'])

        return TestSuiteResult(
            name=suite_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            total_time=total_time,
            results=results
        )

    def generate_report(self, results: TestSuiteResult, output_format: str = "console") -> None:
        """Generate test report"""
        if output_format == "console":
            self._print_console_report(results)
        elif output_format == "json":
            self._print_json_report(results)

    def _print_console_report(self, results: TestSuiteResult) -> None:
        """Print console-friendly report"""
        print(f"\n📊 {results.name} Test Results")
        print("=" * 40)
        print(f"Total Tests: {results.total_tests}")
        print(f"✅ Passed: {results.passed_tests}")
        print(f"❌ Failed: {results.failed_tests}")
        print(f"⚠️  Errors: {results.error_tests}")
        print(f"⏱️  Total Time: {results.total_time:.0f}ms")
        print(f"📈 Success Rate: {(results.passed_tests / results.total_tests * 100):.1f}%" if results.total_tests > 0 else "N/A")

        # Show failed tests
        failed_results = [r for r in results.results if r.status in ['fail', 'error']]
        if failed_results:
            print(f"\n❌ Failed Tests:")
            for result in failed_results[:10]:  # Show first 10 failures
                print(f"   • {result.name}: {result.response_code}")
                if result.error_message:
                    print(f"     Error: {result.error_message}")
            if len(failed_results) > 10:
                print(f"   ... and {len(failed_results) - 10} more failures")

        # Performance analysis
        if results.results:
            avg_time = sum(r.response_time for r in results.results) / len(results.results)
            slowest = max(results.results, key=lambda x: x.response_time)
            print(f"\n⚡ Performance:")
            print(f"   Average Response Time: {avg_time:.0f}ms")
            print(f"   Slowest Request: {slowest.name} ({slowest.response_time:.0f}ms)")

    def _print_json_report(self, results: TestSuiteResult) -> None:
        """Print JSON report"""
        report = {
            "test_suite": results.name,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": results.total_tests,
                "passed_tests": results.passed_tests,
                "failed_tests": results.failed_tests,
                "error_tests": results.error_tests,
                "success_rate": (results.passed_tests / results.total_tests * 100) if results.total_tests > 0 else 0,
                "total_time_ms": results.total_time
            },
            "results": [
                {
                    "name": result.name,
                    "status": result.status,
                    "response_code": result.response_code,
                    "response_time_ms": result.response_time,
                    "error_message": result.error_message
                }
                for result in results.results
            ]
        }

        print(json.dumps(report, indent=2))

    def save_report(self, results: TestSuiteResult, filename: str) -> None:
        """Save detailed test report to file"""
        report_data = {
            "test_suite": results.name,
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "summary": {
                "total_tests": results.total_tests,
                "passed_tests": results.passed_tests,
                "failed_tests": results.failed_tests,
                "error_tests": results.error_tests,
                "success_rate": (results.passed_tests / results.total_tests * 100) if results.total_tests > 0 else 0,
                "total_time_ms": results.total_time
            },
            "detailed_results": [
                {
                    "name": result.name,
                    "status": result.status,
                    "response_code": result.response_code,
                    "response_time_ms": result.response_time,
                    "error_message": result.error_message,
                    "response_data": result.response_data
                }
                for result in results.results
            ]
        }

        report_path = Path(filename)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_path}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run PsychSync authentication tests")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for the API")
    parser.add_argument("--collection", default="postman_auth_collection.json", help="Postman collection file")
    parser.add_argument("--report", choices=["console", "json"], default="console", help="Report format")
    parser.add_argument("--output", help="Save detailed report to file")
    parser.add_argument("--suite", default="Authentication", help="Test suite name")

    args = parser.parse_args()

    print("🔧 Postman Authentication Test Runner")
    print("=" * 40)
    print(f"Base URL: {args.url}")
    print(f"Collection: {args.collection}")
    print(f"Report Format: {args.report}")

    # Initialize test runner
    runner = PostmanTestRunner(args.url)

    # Load collection
    collection = runner.load_collection(args.collection)
    if not collection:
        print("❌ Failed to load Postman collection")
        return 1

    # Run tests
    try:
        results = runner.run_test_suite(collection, args.suite)
        runner.generate_report(results, args.report)

        if args.output:
            runner.save_report(results, args.output)

        # Return exit code based on results
        return 0 if results.failed_tests == 0 and results.error_tests == 0 else 1

    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Test run failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())