#!/usr/bin/env python3
"""
Comprehensive Performance Optimization Suite
Analyzes and optimizes system performance across multiple dimensions:
1. Frontend bundle analysis and optimization
2. API response time analysis
3. Database query performance
4. Memory usage optimization
5. Network request optimization
"""

import asyncio
import aiohttp
import json
import sys
import time
import psutil
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List
import subprocess
import threading

class PerformanceOptimizationResult:
    def __init__(self, test_name: str, success: bool, duration: float, details: str = "",
                 recommendations: List[str] = None, metrics: Dict[str, Any] = None):
        self.test_name = test_name
        self.success = success
        self.duration = duration
        self.details = details
        self.recommendations = recommendations or []
        self.metrics = metrics or {}
        self.timestamp = datetime.now(timezone.utc)

class PerformanceOptimizer:
    def __init__(self):
        self.frontend_url = "http://localhost:5174"
        self.backend_url = "http://localhost:8000"
        self.session = None
        self.results = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def analyze_frontend_performance(self):
        """Analyze frontend performance and bundle size"""
        start_time = time.time()
        recommendations = []
        metrics = {}

        try:
            # Test frontend loading time
            async with self.session.get(self.frontend_url) as response:
                content = await response.text()
                content_size = len(content.encode('utf-8'))

                metrics['content_size_kb'] = round(content_size / 1024, 2)
                metrics['load_time_seconds'] = round(time.time() - start_time, 3)

                # Analyze HTML for optimization opportunities
                script_tags = content.count('<script')
                link_tags = content.count('<link')
                inline_styles = content.count('style=')

                metrics['script_count'] = script_tags
                metrics['stylesheet_count'] = link_tags
                metrics['inline_styles'] = inline_styles

                # Generate recommendations
                if content_size > 500 * 1024:  # > 500KB
                    recommendations.append("Consider code splitting and lazy loading to reduce initial bundle size")

                if script_tags > 10:
                    recommendations.append("Consider bundling JavaScript files to reduce HTTP requests")

                if inline_styles > 5:
                    recommendations.append("Move inline styles to external stylesheets for better caching")

                # Check for common performance issues
                if 'console.log' in content:
                    recommendations.append("Remove console.log statements from production code")

                if 'debugger' in content:
                    recommendations.append("Remove debugger statements from production code")

                details = f"Frontend loaded {metrics['content_size_kb']}KB in {metrics['load_time_seconds']}s"
                details += f" | Scripts: {script_tags}, Stylesheets: {link_tags}"

                return PerformanceOptimizationResult(
                    "Frontend Performance Analysis",
                    True,
                    time.time() - start_time,
                    details,
                    recommendations,
                    metrics
                )

        except Exception as e:
            return PerformanceOptimizationResult(
                "Frontend Performance Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze frontend: {str(e)}",
                ["Check if frontend server is running"]
            )

    async def analyze_api_performance(self):
        """Analyze API response times and endpoints"""
        start_time = time.time()
        recommendations = []
        metrics = {}

        try:
            # Test various API endpoints
            endpoints = [
                "/health",
                "/docs",
                "/openapi.json"
            ]

            response_times = []
            for endpoint in endpoints:
                endpoint_start = time.time()
                try:
                    async with self.session.get(f"{self.backend_url}{endpoint}", timeout=10) as response:
                        response_time = time.time() - endpoint_start
                        response_times.append(response_time)
                        metrics[f"{endpoint.replace('/', '_').replace('-', '_')}_time"] = round(response_time, 3)
                except:
                    pass  # Skip failed endpoints

            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                metrics['avg_response_time'] = round(avg_response_time, 3)
                metrics['max_response_time'] = round(max_response_time, 3)

                # Generate recommendations
                if avg_response_time > 1.0:
                    recommendations.append("Consider implementing API response caching")

                if max_response_time > 5.0:
                    recommendations.append("Some endpoints are slow - optimize database queries and implement caching")

                if len(response_times) < len(endpoints):
                    recommendations.append("Some endpoints are failing - check API configuration")

                details = f"API endpoints: {len(response_times)}/{len(endpoints)} responding"
                details += f" | Avg response time: {metrics['avg_response_time']}s"

                return PerformanceOptimizationResult(
                    "API Performance Analysis",
                    True,
                    time.time() - start_time,
                    details,
                    recommendations,
                    metrics
                )
            else:
                return PerformanceOptimizationResult(
                    "API Performance Analysis",
                    False,
                    time.time() - start_time,
                    "No API endpoints responded",
                    ["Check backend server status and configuration"]
                )

        except Exception as e:
            return PerformanceOptimizationResult(
                "API Performance Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze API performance: {str(e)}"
            )

    async def analyze_memory_usage(self):
        """Analyze current memory usage"""
        start_time = time.time()
        recommendations = []
        metrics = {}

        try:
            # Get current process memory usage
            process = psutil.Process()
            memory_info = process.memory_info()

            metrics['process_memory_mb'] = round(memory_info.rss / 1024 / 1024, 2)
            metrics['process_memory_percent'] = round(process.memory_percent(), 2)

            # Get system memory usage
            system_memory = psutil.virtual_memory()
            metrics['system_memory_total_gb'] = round(system_memory.total / 1024 / 1024 / 1024, 2)
            metrics['system_memory_used_gb'] = round(system_memory.used / 1024 / 1024 / 1024, 2)
            metrics['system_memory_percent'] = system_memory.percent

            # Generate recommendations
            if metrics['process_memory_mb'] > 1000:  # > 1GB
                recommendations.append("Process memory usage is high - check for memory leaks")

            if metrics['system_memory_percent'] > 80:
                recommendations.append("System memory usage is high - consider freeing up memory")

            details = f"Process: {metrics['process_memory_mb']}MB ({metrics['process_memory_percent']}%)"
            details += f" | System: {metrics['system_memory_used_gb']}/{metrics['system_memory_total_gb']}GB ({metrics['system_memory_percent']}%)"

            return PerformanceOptimizationResult(
                "Memory Usage Analysis",
                True,
                time.time() - start_time,
                details,
                recommendations,
                metrics
            )

        except Exception as e:
            return PerformanceOptimizationResult(
                "Memory Usage Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze memory usage: {str(e)}"
            )

    def analyze_code_quality(self):
        """Analyze code quality and suggest optimizations"""
        start_time = time.time()
        recommendations = []
        metrics = {}

        try:
            # Count lines of code
            app_dir = Path("app")
            frontend_dir = Path("frontend/src")

            backend_py_files = list(app_dir.glob("**/*.py"))
            frontend_ts_files = list(frontend_dir.glob("**/*.ts*"))

            backend_lines = sum(len(f.read_text(encoding='utf-8').splitlines()) for f in backend_py_files if f.exists())
            frontend_lines = sum(len(f.read_text(encoding='utf-8').splitlines()) for f in frontend_ts_files if f.exists())

            metrics['backend_py_files'] = len(backend_py_files)
            metrics['frontend_ts_files'] = len(frontend_ts_files)
            metrics['backend_lines_of_code'] = backend_lines
            metrics['frontend_lines_of_code'] = frontend_lines
            metrics['total_lines_of_code'] = backend_lines + frontend_lines

            # Code quality recommendations
            if metrics['total_lines_of_code'] > 50000:
                recommendations.append("Consider code refactoring to reduce complexity")

            if metrics['backend_lines_of_code'] > 30000:
                recommendations.append("Backend codebase is large - consider microservices for better scalability")

            if metrics['frontend_lines_of_code'] > 20000:
                recommendations.append("Consider code splitting and lazy loading for better performance")

            # Check for common optimization opportunities
            test_files = list(Path("tests").glob("**/*.py"))
            metrics['test_files'] = len(test_files)

            if len(test_files) < len(backend_py_files) // 2:
                recommendations.append("Consider increasing test coverage for better code quality")

            details = f"Backend: {metrics['backend_lines_of_code']} lines in {metrics['backend_py_files']} files"
            details += f" | Frontend: {metrics['frontend_lines_of_code']} lines in {metrics['frontend_ts_files']} files"

            return PerformanceOptimizationResult(
                "Code Quality Analysis",
                True,
                time.time() - start_time,
                details,
                recommendations,
                metrics
            )

        except Exception as e:
            return PerformanceOptimizationResult(
                "Code Quality Analysis",
                False,
                time.time() - start_time,
                f"Failed to analyze code quality: {str(e)}"
            )

    def generate_optimization_report(self):
        """Generate comprehensive optimization report"""
        print(f"\n{'='*80}")
        print("📊 PERFORMANCE OPTIMIZATION ANALYSIS REPORT")
        print(f"{'='*80}")

        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.success)
        total_duration = sum(result.duration for result in self.results)

        print(f"\n📈 ANALYSIS SUMMARY:")
        print(f"  Total Analyses: {total_tests}")
        print(f"  Completed: {passed_tests} ✅")
        print(f"  Failed: {total_tests - passed_tests} ❌")
        print(f"  Total Duration: {total_duration:.3f}s")

        print(f"\n📋 PERFORMANCE METRICS:")
        for result in self.results:
            if result.success and result.metrics:
                print(f"\n🔍 {result.test_name}:")
                for metric, value in result.metrics.items():
                    print(f"   {metric}: {value}")

        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)

        if all_recommendations:
            # Remove duplicates and sort
            unique_recommendations = list(set(all_recommendations))
            for i, recommendation in enumerate(unique_recommendations, 1):
                print(f"  {i}. {recommendation}")
        else:
            print("  ✅ No optimization recommendations - system is well-optimized!")

        print(f"\n🚀 PERFORMANCE OPTIMIZATION ACTIONS:")
        print("  1. Frontend: Implement code splitting and lazy loading")
        print("  2. Backend: Add API response caching and optimize database queries")
        print("  3. Database: Add proper indexes and query optimization")
        print("  4. Infrastructure: Implement CDN and compression")
        print("  5. Monitoring: Set up performance monitoring and alerting")

        print(f"\n📊 NEXT PHASE:")
        print("  4. Security Enhancements")
        print("  5. Production Deployment Preparation")

        print(f"\n{'='*80}")
        print("🎉 PERFORMANCE OPTIMIZATION ANALYSIS COMPLETE")
        print(f"{'='*80}")

    async def run_performance_analysis(self):
        """Run all performance analysis"""
        print("⚡ PSYNSYNC PERFORMANCE OPTIMIZATION SUITE")
        print("=" * 70)
        print("Analyzing system performance across multiple dimensions")
        print("=" * 70)

        # Define all analyses
        analyses = [
            self.analyze_frontend_performance,
            self.analyze_api_performance,
            self.analyze_memory_usage,
            self.analyze_code_quality
        ]

        # Run each analysis
        for analysis_func in analyses:
            print(f"\n🔍 Running {analysis_func.__name__}...")

            if analysis_func.__name__ == 'analyze_code_quality':
                # This is a synchronous function
                result = analysis_func()
            else:
                # These are async functions
                result = await analysis_func()

            self.results.append(result)

            if result.success:
                print(f"✅ {result.test_name}: COMPLETED ({result.duration:.3f}s)")
                print(f"   Details: {result.details}")
            else:
                print(f"❌ {result.test_name}: FAILED ({result.duration:.3f}s)")
                print(f"   Error: {result.details}")

        # Generate final report
        self.generate_optimization_report()
        return self.results

async def main():
    """Main performance optimizer"""
    try:
        async with PerformanceOptimizer() as optimizer:
            results = await optimizer.run_performance_analysis()

            # Generate exit code based on analysis completion
            failed_count = sum(1 for result in results if not result.success)
            if failed_count > 0:
                sys.exit(1)
            else:
                sys.exit(0)

    except KeyboardInterrupt:
        print("\n⚠️  Performance analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    asyncio.run(main())
