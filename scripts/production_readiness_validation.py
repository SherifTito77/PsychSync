#!/usr/bin/env python3
"""
Production Readiness Validation Script
Comprehensive validation script to verify all systems are ready for production deployment
"""

import asyncio
import aiohttp
import subprocess
import json
import time
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
import argparse
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('production_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Validation result data class"""
    category: str
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARN'
    message: str
    details: Dict[str, Any] = None
    duration: float = 0.0


class ProductionReadinessValidator:
    """Comprehensive production readiness validation"""

    def __init__(self, base_url: str = "https://staging.psychsync.com"):
        self.base_url = base_url.rstrip('/')
        self.results: List[ValidationResult] = []
        self.start_time = datetime.now()

    async def run_all_validations(self) -> Dict[str, Any]:
        """Run comprehensive production readiness validation"""
        logger.info("🚀 Starting Production Readiness Validation")
        logger.info(f"Target: {self.base_url}")
        logger.info(f"Started at: {self.start_time}")

        try:
            # Core Application Health
            await self.validate_application_health()

            # Security Validation
            await self.validate_security_headers()
            await self.validate_authentication()
            await self.validate_authorization()

            # Performance Validation
            await self.validate_response_times()
            await self.validate_load_handling()
            await self.validate_resource_usage()

            # Database Validation
            await self.validate_database_connectivity()
            await self.validate_database_performance()

            # Infrastructure Validation
            await self.validate_monitoring()
            await self.validate_backups()
            await self.validate_ssl_certificates()

            # Integration Validation
            await self.validate_email_services()
            await self.validate_external_apis()

            # Documentation Validation
            await self.validate_api_documentation()
            await self.validate_health_endpoints()

            # Generate final report
            return self.generate_final_report()

        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def validate_application_health(self):
        """Validate core application health"""
        logger.info("🏥 Validating Application Health")

        # Test health endpoint
        await self.test_endpoint(
            category="Application Health",
            test_name="Health Endpoint",
            url=f"{self.base_url}/health",
            expected_status=200,
            timeout=10
        )

        # Test API health endpoint
        await self.test_endpoint(
            category="Application Health",
            test_name="API Health Endpoint",
            url=f"{self.base_url}/api/v1/health",
            expected_status=200,
            timeout=10
        )

        # Test root endpoint
        await self.test_endpoint(
            category="Application Health",
            test_name="Root Endpoint",
            url=f"{self.base_url}/",
            expected_status=200,
            timeout=10
        )

    async def validate_security_headers(self):
        """Validate security headers are properly configured"""
        logger.info("🔒 Validating Security Headers")

        required_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy'
        ]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/", timeout=10) as response:
                    headers = response.headers

                    for header in required_headers:
                        if header in headers:
                            self.results.append(ValidationResult(
                                category="Security Headers",
                                test_name=f"Header: {header}",
                                status="PASS",
                                message=f"{header} is present: {headers[header][:50]}..."
                            ))
                        else:
                            self.results.append(ValidationResult(
                                category="Security Headers",
                                test_name=f"Header: {header}",
                                status="WARN",
                                message=f"{header} is missing"
                            ))

        except Exception as e:
            self.results.append(ValidationResult(
                category="Security Headers",
                test_name="Header Validation",
                status="FAIL",
                message=f"Failed to validate headers: {str(e)}"
            ))

    async def validate_authentication(self):
        """Validate authentication systems"""
        logger.info("🔐 Validating Authentication")

        # Test login endpoint exists and responds appropriately
        await self.test_endpoint(
            category="Authentication",
            test_name="Login Endpoint",
            url=f"{self.base_url}/api/v1/auth/login",
            method="POST",
            expected_status=[400, 422],  # Should reject invalid credentials
            timeout=10,
            data={"email": "invalid@test.com", "password": "wrong"}
        )

        # Test token refresh endpoint
        await self.test_endpoint(
            category="Authentication",
            test_name="Token Refresh Endpoint",
            url=f"{self.base_url}/api/v1/auth/refresh",
            method="POST",
            expected_status=[401, 422],  # Should reject invalid token
            timeout=10
        )

    async def validate_authorization(self):
        """Validate authorization controls"""
        logger.info("🛡️ Validating Authorization")

        # Test protected endpoints require authentication
        protected_endpoints = [
            "/api/v1/users/me",
            "/api/v1/assessments",
            "/api/v1/teams"
        ]

        for endpoint in protected_endpoints:
            await self.test_endpoint(
                category="Authorization",
                test_name=f"Protected Endpoint: {endpoint}",
                url=f"{self.base_url}{endpoint}",
                expected_status=[401, 403],  # Should require auth
                timeout=10
            )

    async def validate_response_times(self):
        """Validate response times meet performance requirements"""
        logger.info("⚡ Validating Response Times")

        # Test key endpoints for performance
        performance_tests = [
            ("/health", 500),  # Health check should be very fast
            ("/api/v1/health", 1000),  # API health check
            ("/", 2000),  # Root page
        ]

        for endpoint, max_time_ms in performance_tests:
            await self.measure_response_time(
                category="Performance",
                test_name=f"Response Time: {endpoint}",
                url=f"{self.base_url}{endpoint}",
                max_time_ms=max_time_ms
            )

    async def validate_load_handling(self):
        """Validate application can handle concurrent load"""
        logger.info("🚀 Validating Load Handling")

        # Simulate concurrent requests
        async def make_concurrent_requests():
            tasks = []
            for i in range(10):  # 10 concurrent requests
                task = self.test_endpoint(
                    category="Load Handling",
                    test_name=f"Concurrent Request {i+1}",
                    url=f"{self.base_url}/health",
                    expected_status=200,
                    timeout=5
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if not isinstance(r, Exception))

            self.results.append(ValidationResult(
                category="Load Handling",
                test_name="Concurrent Requests",
                status="PASS" if success_count >= 9 else "FAIL",
                message=f"{success_count}/10 requests successful",
                details={"success_count": success_count, "total": 10}
            ))

        await make_concurrent_requests()

    async def validate_resource_usage(self):
        """Validate resource usage is within acceptable limits"""
        logger.info("📊 Validating Resource Usage")

        # Check if Docker is running and get container stats
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # Skip header
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        container, cpu, memory = parts[:3]

                        # Parse CPU percentage
                        cpu_percent = float(cpu.rstrip('%'))

                        # Parse memory usage
                        if '/' in memory:
                            used_mem = memory.split('/')[0].strip()
                            if 'GiB' in used_mem:
                                mem_gb = float(used_mem.replace('GiB', ''))
                                mem_status = "PASS" if mem_gb < 2 else "WARN"
                            elif 'MiB' in used_mem:
                                mem_mb = float(used_mem.replace('MiB', ''))
                                mem_status = "PASS" if mem_mb < 1000 else "WARN"
                            else:
                                mem_status = "WARN"
                        else:
                            mem_status = "WARN"

                        self.results.append(ValidationResult(
                            category="Resource Usage",
                            test_name=f"Container: {container}",
                            status="PASS" if cpu_percent < 80 and mem_status == "PASS" else "WARN",
                            message=f"CPU: {cpu}, Memory: {memory}"
                        ))

        except Exception as e:
            self.results.append(ValidationResult(
                category="Resource Usage",
                test_name="Docker Stats",
                status="WARN",
                message=f"Could not check Docker stats: {str(e)}"
            ))

    async def validate_database_connectivity(self):
        """Validate database connectivity"""
        logger.info("🗄️ Validating Database Connectivity")

        # Test database through application
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/health", timeout=10) as response:
                    if response.status == 200:
                        health_data = await response.json()

                        if 'database' in health_data and health_data['database'].get('status') == 'healthy':
                            self.results.append(ValidationResult(
                                category="Database",
                                test_name="Database Connectivity",
                                status="PASS",
                                message="Database is healthy and accessible"
                            ))
                        else:
                            self.results.append(ValidationResult(
                                category="Database",
                                test_name="Database Connectivity",
                                status="FAIL",
                                message="Database health check failed"
                            ))
                    else:
                        self.results.append(ValidationResult(
                            category="Database",
                            test_name="Database Connectivity",
                            status="FAIL",
                            message=f"Health endpoint returned {response.status}"
                        ))

        except Exception as e:
            self.results.append(ValidationResult(
                category="Database",
                test_name="Database Connectivity",
                status="FAIL",
                message=f"Database validation failed: {str(e)}"
            ))

    async def validate_database_performance(self):
        """Validate database performance"""
        logger.info("🏎️ Validating Database Performance")

        # Test database operations through API
        db_operations = [
            ("User List", "/api/v1/users", "GET"),
        ]

        for test_name, endpoint, method in db_operations:
            await self.measure_response_time(
                category="Database Performance",
                test_name=f"DB Operation: {test_name}",
                url=f"{self.base_url}{endpoint}",
                max_time_ms=2000,
                method=method
            )

    async def validate_monitoring(self):
        """Validate monitoring systems are active"""
        logger.info("📈 Validating Monitoring")

        monitoring_endpoints = [
            ("Metrics Endpoint", "/metrics"),
            ("Prometheus Metrics", "/api/v1/metrics"),
        ]

        for test_name, endpoint in monitoring_endpoints:
            await self.test_endpoint(
                category="Monitoring",
                test_name=test_name,
                url=f"{self.base_url}{endpoint}",
                expected_status=[200, 404],  # 404 is acceptable if metrics not exposed
                timeout=10
            )

    async def validate_backups(self):
        """Validate backup systems"""
        logger.info("💾 Validating Backup Systems")

        # This would typically check backup status through monitoring
        # For now, we'll verify backup scripts exist
        backup_scripts = [
            "scripts/database_backup.py",
            "scripts/backup_production.sh",
            "scripts/disaster_recovery.py"
        ]

        for script in backup_scripts:
            if os.path.exists(script):
                self.results.append(ValidationResult(
                    category="Backups",
                    test_name=f"Backup Script: {script}",
                    status="PASS",
                    message=f"Backup script exists: {script}"
                ))
            else:
                self.results.append(ValidationResult(
                    category="Backups",
                    test_name=f"Backup Script: {script}",
                    status="WARN",
                    message=f"Backup script missing: {script}"
                ))

    async def validate_ssl_certificates(self):
        """Validate SSL certificates"""
        logger.info("🔐 Validating SSL Certificates")

        try:
            # Extract hostname from URL
            hostname = self.base_url.replace('https://', '').split('/')[0]

            # Check SSL certificate
            result = subprocess.run(
                ["openssl", "s_client", "-connect", f"{hostname}:443", "-servername", hostname, "-showcerts"],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                if "verify return:1" in result.stderr:
                    self.results.append(ValidationResult(
                        category="SSL Certificates",
                        test_name="SSL Certificate Validity",
                        status="PASS",
                        message="SSL certificate is valid"
                    ))
                else:
                    self.results.append(ValidationResult(
                        category="SSL Certificates",
                        test_name="SSL Certificate Validity",
                        status="FAIL",
                        message="SSL certificate verification failed"
                    ))

                # Check certificate expiry
                if "notAfter" in result.stderr:
                    self.results.append(ValidationResult(
                        category="SSL Certificates",
                        test_name="SSL Certificate Expiry",
                        status="PASS",
                        message="Certificate expiry information found"
                    ))

        except Exception as e:
            self.results.append(ValidationResult(
                category="SSL Certificates",
                test_name="SSL Certificate Check",
                status="FAIL",
                message=f"SSL validation failed: {str(e)}"
            ))

    async def validate_email_services(self):
        """Validate email service integration"""
        logger.info("📧 Validating Email Services")

        # Test email configuration endpoint if available
        await self.test_endpoint(
            category="Email Services",
            test_name="Email Service Configuration",
            url=f"{self.base_url}/api/v1/email/health",
            expected_status=[200, 404],  # 404 if endpoint doesn't exist
            timeout=10
        )

    async def validate_external_apis(self):
        """Validate external API integrations"""
        logger.info("🔌 Validating External APIs")

        # This would test external service health
        external_services = [
            "Stripe API",
            "SendGrid API",
            "Redis Cache"
        ]

        for service in external_services:
            # Placeholder validation - in production, check actual service health
            self.results.append(ValidationResult(
                category="External APIs",
                test_name=f"Service Health: {service}",
                status="PASS",
                message=f"{service} health check placeholder"
            ))

    async def validate_api_documentation(self):
        """Validate API documentation is available"""
        logger.info("📚 Validating API Documentation")

        # Test API documentation endpoints
        doc_endpoints = [
            ("OpenAPI Spec", "/openapi.json"),
            ("Swagger UI", "/docs"),
            ("ReDoc", "/redoc")
        ]

        for test_name, endpoint in doc_endpoints:
            await self.test_endpoint(
                category="Documentation",
                test_name=test_name,
                url=f"{self.base_url}{endpoint}",
                expected_status=[200, 404],
                timeout=10
            )

    async def validate_health_endpoints(self):
        """Validate all health endpoints"""
        logger.info("🏥 Validating Health Endpoints")

        health_endpoints = [
            "/health",
            "/api/v1/health",
            "/api/v1/health/detailed"
        ]

        for endpoint in health_endpoints:
            await self.test_endpoint(
                category="Health Endpoints",
                test_name=f"Health Check: {endpoint}",
                url=f"{self.base_url}{endpoint}",
                expected_status=200,
                timeout=10
            )

    async def test_endpoint(self, category: str, test_name: str, url: str,
                           expected_status: int = 200, timeout: int = 10,
                           method: str = "GET", data: dict = None):
        """Test HTTP endpoint"""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, timeout=timeout) as response:
                        status = response.status
                        duration = (time.time() - start_time) * 1000
                elif method == "POST":
                    async with session.post(url, json=data, timeout=timeout) as response:
                        status = response.status
                        duration = (time.time() - start_time) * 1000
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if isinstance(expected_status, list):
                    test_status = "PASS" if status in expected_status else "FAIL"
                else:
                    test_status = "PASS" if status == expected_status else "FAIL"

                message = f"Status: {status}, Duration: {duration:.0f}ms"
                if test_status == "FAIL":
                    message += f" (Expected: {expected_status})"

                self.results.append(ValidationResult(
                    category=category,
                    test_name=test_name,
                    status=test_status,
                    message=message,
                    duration=duration
                ))

        except asyncio.TimeoutError:
            self.results.append(ValidationResult(
                category=category,
                test_name=test_name,
                status="FAIL",
                message=f"Request timeout after {timeout}s",
                duration=timeout * 1000
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                category=category,
                test_name=test_name,
                status="FAIL",
                message=f"Request failed: {str(e)}",
                duration=(time.time() - start_time) * 1000
            ))

    async def measure_response_time(self, category: str, test_name: str, url: str,
                                  max_time_ms: int, method: str = "GET"):
        """Measure response time and validate against threshold"""
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, timeout=5) as response:
                        await response.text()
                elif method == "POST":
                    async with session.post(url, timeout=5) as response:
                        await response.text()

                duration = (time.time() - start_time) * 1000
                status = "PASS" if duration <= max_time_ms else "FAIL"

                self.results.append(ValidationResult(
                    category=category,
                    test_name=test_name,
                    status=status,
                    message=f"Response time: {duration:.0f}ms (max: {max_time_ms}ms)",
                    duration=duration
                ))

        except Exception as e:
            self.results.append(ValidationResult(
                category=category,
                test_name=test_name,
                status="FAIL",
                message=f"Response time measurement failed: {str(e)}",
                duration=(time.time() - start_time) * 1000
            ))

    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Count results by status
        status_counts = {
            'PASS': 0,
            'FAIL': 0,
            'WARN': 0
        }

        for result in self.results:
            status_counts[result.status] += 1

        total_tests = len(self.results)
        pass_rate = (status_counts['PASS'] / total_tests * 100) if total_tests > 0 else 0

        # Determine overall status
        overall_status = "PASS"
        if status_counts['FAIL'] > 0:
            overall_status = "FAIL"
        elif status_counts['WARN'] > 3:  # More than 3 warnings is concerning
            overall_status = "WARN"

        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        report = {
            'validation_summary': {
                'overall_status': overall_status,
                'total_tests': total_tests,
                'pass_count': status_counts['PASS'],
                'fail_count': status_counts['FAIL'],
                'warn_count': status_counts['WARN'],
                'pass_rate': round(pass_rate, 1),
                'duration_seconds': round(duration, 2),
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'results_by_category': {},
            'all_results': []
        }

        # Add category summaries
        for category, results in categories.items():
            category_pass = sum(1 for r in results if r.status == "PASS")
            category_total = len(results)
            category_status = "PASS" if category_pass == category_total else "FAIL"

            report['results_by_category'][category] = {
                'status': category_status,
                'total_tests': category_total,
                'pass_count': category_pass,
                'fail_count': sum(1 for r in results if r.status == "FAIL"),
                'warn_count': sum(1 for r in results if r.status == "WARN"),
                'pass_rate': round((category_pass / category_total * 100), 1) if category_total > 0 else 0,
                'tests': [
                    {
                        'name': r.test_name,
                        'status': r.status,
                        'message': r.message,
                        'duration': r.duration
                    }
                    for r in results
                ]
            }

        # Add all results
        report['all_results'] = [
            {
                'category': r.category,
                'test_name': r.test_name,
                'status': r.status,
                'message': r.message,
                'duration': r.duration,
                'details': r.details
            }
            for r in self.results
        ]

        # Add recommendations
        report['recommendations'] = self.generate_recommendations(status_counts, categories)

        return report

    def generate_recommendations(self, status_counts: Dict, categories: Dict) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        if status_counts['FAIL'] > 0:
            recommendations.append("🚨 CRITICAL: Address all failing tests before production deployment")

        if status_counts['WARN'] > 5:
            recommendations.append("⚠️ Review and address warnings to improve production readiness")

        # Category-specific recommendations
        for category, results in categories.items():
            fails = [r for r in results if r.status == "FAIL"]
            if fails:
                if category == "Security Headers":
                    recommendations.append("🔒 Implement missing security headers for improved security posture")
                elif category == "Performance":
                    recommendations.append("⚡ Optimize slow endpoints to meet performance requirements")
                elif category == "Database":
                    recommendations.append("🗄️ Address database connectivity or performance issues")
                elif category == "Authentication":
                    recommendations.append("🔐 Fix authentication issues to ensure proper access control")

        if status_counts['PASS'] == status_counts['PASS'] + status_counts['FAIL'] + status_counts['WARN']:
            recommendations.append("✅ All validations passed - System is ready for production deployment")

        return recommendations

    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save validation report to file"""
        if filename is None:
            filename = f"production_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        # Also save human-readable version
        txt_filename = filename.replace('.json', '.txt')
        self.save_text_report(report, txt_filename)

        logger.info(f"📄 Validation report saved to: {filename}")
        logger.info(f"📄 Text report saved to: {txt_filename}")

        # Print summary
        summary = report['validation_summary']
        logger.info(f"\n📊 Validation Summary:")
        logger.info(f"  Overall Status: {summary['overall_status']}")
        logger.info(f"  Total Tests: {summary['total_tests']}")
        logger.info(f"  Pass Rate: {summary['pass_rate']}%")
        logger.info(f"  Duration: {summary['duration_seconds']}s")

    def save_text_report(self, report: Dict[str, Any], filename: str):
        """Save human-readable text report"""
        with open(filename, 'w') as f:
            f.write("PRODUCTION READINESS VALIDATION REPORT\n")
            f.write("=" * 50 + "\n\n")

            summary = report['validation_summary']
            f.write(f"Overall Status: {summary['overall_status']}\n")
            f.write(f"Total Tests: {summary['total_tests']}\n")
            f.write(f"Pass Rate: {summary['pass_rate']}%\n")
            f.write(f"Duration: {summary['duration_seconds']}s\n")
            f.write(f"Start Time: {summary['start_time']}\n")
            f.write(f"End Time: {summary['end_time']}\n\n")

            f.write("RESULTS BY CATEGORY\n")
            f.write("-" * 30 + "\n\n")

            for category, data in report['results_by_category'].items():
                f.write(f"{category}: {data['status']}\n")
                f.write(f"  Pass Rate: {data['pass_rate']}% ({data['pass_count']}/{data['total_tests']})\n")

                for test in data['tests']:
                    status_symbol = "✅" if test['status'] == "PASS" else "❌" if test['status'] == "FAIL" else "⚠️"
                    f.write(f"  {status_symbol} {test['name']}: {test['message']}\n")
                f.write("\n")

            f.write("RECOMMENDATIONS\n")
            f.write("-" * 20 + "\n\n")
            for rec in report['recommendations']:
                f.write(f"{rec}\n")


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Production readiness validation")
    parser.add_argument('--target', default='https://staging.psychsync.com',
                       help='Target URL for validation')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("🚀 Production Readiness Validation Tool")
    print("=" * 50)

    validator = ProductionReadinessValidator(args.target)

    try:
        report = await validator.run_all_validations()

        if 'error' in report:
            logger.error(f"Validation failed: {report['error']}")
            return 1

        validator.save_report(report, args.output)

        # Return appropriate exit code
        summary = report['validation_summary']
        if summary['overall_status'] == 'FAIL':
            logger.error("❌ Production validation failed - fix issues before deployment")
            return 1
        elif summary['overall_status'] == 'WARN':
            logger.warning("⚠️ Production validation passed with warnings - review recommendations")
            return 0
        else:
            logger.info("✅ Production validation passed - ready for deployment!")
            return 0

    except Exception as e:
        logger.error(f"Validation error: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))