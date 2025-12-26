#!/usr/bin/env python3
"""
Master CI/CD Integration Pipeline
=================================

Comprehensive CI/CD pipeline that integrates all testing frameworks for the PsychSync platform.
Provides automated testing, validation, reporting, and deployment readiness assessment.
"""

import asyncio
import time
import json
import sys
import os
import subprocess
import importlib.util
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import traceback

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@dataclass
class PipelineStageResult:
    """Results from a pipeline stage execution"""
    stage_name: str
    success: bool
    duration_seconds: float
    test_count: int
    passed_tests: int
    failed_tests: int
    error_rate_percent: float
    metrics: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    report_file: Optional[str]

@dataclass
class PipelineExecutionSummary:
    """Summary of entire pipeline execution"""
    pipeline_name: str
    execution_id: str
    start_time: datetime
    end_time: datetime
    total_duration_seconds: float
    overall_success: bool
    stages_completed: int
    stages_total: int
    production_ready: bool
    critical_issues: List[str]
    deployment_recommendation: str

class MasterCICDPipeline:
    """Master CI/CD pipeline integrating all testing frameworks"""

    def __init__(self):
        self.execution_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.stage_results: List[PipelineStageResult] = []
        self.base_url = "http://localhost:8000"

        # Pipeline stages configuration
        self.pipeline_stages = [
            {
                "name": "Regression Testing",
                "file": "test_psychsync_regression_suite.py",
                "priority": 1,
                "critical": True,
                "description": "Platform-wide regression testing"
            },
            {
                "name": "User Permission Testing",
                "file": "test_user_permissions_profile_settings.py",
                "priority": 2,
                "critical": True,
                "description": "User access control validation"
            },
            {
                "name": "Team Member Addition Testing",
                "file": "test_manual_team_member_addition.py",
                "priority": 2,
                "critical": True,
                "description": "Team management workflow testing"
            },
            {
                "name": "Load Testing and Performance",
                "file": "advanced_load_testing_suite.py",
                "priority": 3,
                "critical": True,
                "description": "Performance and load testing"
            },
            {
                "name": "Monitoring and Alerting",
                "file": "monitoring_alerting_system_tests.py",
                "priority": 3,
                "critical": True,
                "description": "System observability testing"
            },
            {
                "name": "Cross-Platform Compatibility",
                "file": "cross_platform_compatibility_tests.py",
                "priority": 4,
                "critical": False,
                "description": "Platform compatibility validation"
            }
        ]

    async def execute_full_pipeline(self) -> PipelineExecutionSummary:
        """Execute the complete CI/CD pipeline"""
        print("🚀 STARTING PSYCHSYNC MASTER CI/CD PIPELINE")
        print("=" * 80)
        print(f"Execution ID: {self.execution_id}")
        print(f"Pipeline Version: 1.0.0")
        print(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        try:
            # Pipeline initialization
            await self.initialize_pipeline()

            # Execute pipeline stages in priority order
            for stage in sorted(self.pipeline_stages, key=lambda x: x["priority"]):
                print(f"\n{'='*60}")
                print(f"🔄 EXECUTING STAGE: {stage['name']}")
                print(f"Priority: {stage['priority']} | Critical: {stage['critical']}")
                print(f"Description: {stage['description']}")
                print(f"{'='*60}")

                stage_result = await self.execute_pipeline_stage(stage)
                self.stage_results.append(stage_result)

                # Check if critical stage failed
                if stage["critical"] and not stage_result.success:
                    print(f"\n❌ CRITICAL STAGE FAILED: {stage['name']}")
                    print("⏹️  Pipeline execution stopped due to critical failure")
                    break

                # Add delay between stages for system recovery
                await asyncio.sleep(2)

            # Generate final pipeline summary
            return await self.generate_pipeline_summary()

        except Exception as e:
            print(f"\n❌ PIPELINE EXECUTION FAILED: {str(e)}")
            traceback.print_exc()
            return await self.generate_pipeline_summary(error=str(e))

    async def initialize_pipeline(self) -> None:
        """Initialize pipeline environment"""
        print("\n🔧 INITIALIZING PIPELINE ENVIRONMENT")

        # Check if required test files exist
        missing_files = []
        for stage in self.pipeline_stages:
            if not os.path.exists(stage["file"]):
                missing_files.append(stage["file"])

        if missing_files:
            print(f"⚠️  Missing test files: {missing_files}")
            print("Pipeline will continue with available test files")
        else:
            print("✅ All test files found")

        # Check server availability
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/v1/health")
                if response.status_code == 200:
                    print("✅ Backend server is running and healthy")
                else:
                    print(f"⚠️  Backend server responded with status {response.status_code}")
        except Exception:
            print("⚠️  Backend server is not accessible - some tests may fail")

        print("✅ Pipeline initialization completed")

    async def execute_pipeline_stage(self, stage: Dict[str, Any]) -> PipelineStageResult:
        """Execute a specific pipeline stage"""
        stage_start_time = time.time()

        print(f"\n📋 Starting stage: {stage['name']}")
        print(f"📄 Test file: {stage['file']}")

        try:
            # Check if test file exists
            if not os.path.exists(stage["file"]):
                return PipelineStageResult(
                    stage_name=stage["name"],
                    success=False,
                    duration_seconds=0,
                    test_count=0,
                    passed_tests=0,
                    failed_tests=0,
                    error_rate_percent=100.0,
                    metrics={},
                    issues=[f"Test file not found: {stage['file']}"],
                    recommendations=["Create missing test file"],
                    report_file=None
                )

            # Execute the test suite
            result = await self.execute_test_suite(stage["file"], stage["name"])

            duration = time.time() - stage_start_time

            # Extract metrics from the test result
            if result and isinstance(result, dict):
                metrics = self.extract_metrics_from_result(result)
                issues = result.get("readiness_issues", [])
                recommendations = result.get("optimization_recommendations", [])
                report_file = self.save_stage_report(stage["name"], result)

                # Determine success based on the result
                success = result.get("production_ready", True) or result.get("success", True)

                # Extract test counts if available
                test_count = result.get("test_count", 0)
                passed_tests = result.get("successful_tests", result.get("passed_tests", 0))
                failed_tests = result.get("failed_tests", test_count - passed_tests)

            else:
                # Fallback metrics if execution failed
                metrics = {}
                issues = ["Test execution failed"]
                recommendations = ["Check test configuration and environment"]
                report_file = None
                success = False
                test_count = 0
                passed_tests = 0
                failed_tests = 0

            error_rate = (failed_tests / test_count * 100) if test_count > 0 else 0

            print(f"\n📊 Stage Results: {stage['name']}")
            print(f"├─ Duration: {duration:.2f} seconds")
            print(f"├─ Tests: {passed_tests}/{test_count} passed")
            print(f"├─ Error Rate: {error_rate:.1f}%")
            print(f"├─ Status: {'✅ PASSED' if success else '❌ FAILED'}")
            if issues:
                print(f"├─ Issues: {len(issues)} identified")
            if report_file:
                print(f"└─ Report: {report_file}")

            return PipelineStageResult(
                stage_name=stage["name"],
                success=success,
                duration_seconds=duration,
                test_count=test_count,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                error_rate_percent=error_rate,
                metrics=metrics,
                issues=issues,
                recommendations=recommendations,
                report_file=report_file
            )

        except Exception as e:
            duration = time.time() - stage_start_time
            error_msg = f"Stage execution failed: {str(e)}"

            print(f"\n❌ Stage failed: {stage['name']}")
            print(f"└─ Error: {error_msg}")

            return PipelineStageResult(
                stage_name=stage["name"],
                success=False,
                duration_seconds=duration,
                test_count=0,
                passed_tests=0,
                failed_tests=0,
                error_rate_percent=100.0,
                metrics={},
                issues=[error_msg],
                recommendations=["Check test file syntax and dependencies"],
                report_file=None
            )

    async def execute_test_suite(self, test_file: str, stage_name: str) -> Optional[Dict[str, Any]]:
        """Execute a test suite and return results"""
        try:
            print(f"🔄 Executing test suite: {test_file}")

            # Import the test module
            spec = importlib.util.spec_from_file_location("test_module", test_file)
            test_module = importlib.util.module_from_spec(spec)

            # Execute the test module
            if hasattr(test_module, 'main'):
                # Run async main function
                if asyncio.iscoroutinefunction(test_module.main):
                    result = await test_module.main()
                else:
                    result = test_module.main()

                return result
            else:
                # Look for other entry points
                for attr_name in dir(test_module):
                    attr = getattr(test_module, attr_name)
                    if (attr_name.startswith('test_') and
                        callable(attr) and
                        asyncio.iscoroutinefunction(attr)):

                        print(f"🧪 Running test: {attr_name}")
                        result = await attr()
                        return result

                print(f"⚠️  No main function found in {test_file}")
                return None

        except Exception as e:
            print(f"❌ Error executing test suite {test_file}: {str(e)}")
            traceback.print_exc()
            return None

    def extract_metrics_from_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant metrics from test result"""
        metrics = {}

        # Common metrics to extract
        metric_keys = [
            "total_requests",
            "successful_requests",
            "failed_requests",
            "success_rate_percent",
            "average_response_time_ms",
            "peak_throughput_rps",
            "min_error_rate_percent",
            "total_tests",
            "successful_tests",
            "failed_tests",
            "test_count",
            "execution_time_seconds"
        ]

        for key in metric_keys:
            if key in result:
                metrics[key] = result[key]

        # Extract summary if available
        if "summary" in result:
            summary = result["summary"]
            for key, value in summary.items():
                if isinstance(value, (int, float)):
                    metrics[f"summary_{key}"] = value

        # Extract performance metrics
        if "performance_metrics" in result:
            perf = result["performance_metrics"]
            for key, value in perf.items():
                if isinstance(value, (int, float)):
                    metrics[f"performance_{key}"] = value

        return metrics

    def save_stage_report(self, stage_name: str, result: Dict[str, Any]) -> str:
        """Save stage report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_stage_name = stage_name.lower().replace(" ", "_").replace("-", "_")
        report_filename = f"pipeline_stage_{safe_stage_name}_report_{timestamp}.json"

        try:
            with open(report_filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)

            return report_filename
        except Exception as e:
            print(f"⚠️  Failed to save stage report: {str(e)}")
            return None

    async def generate_pipeline_summary(self, error: Optional[str] = None) -> PipelineExecutionSummary:
        """Generate comprehensive pipeline execution summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()

        print("\n" + "="*80)
        print("📊 PSYCHSYNC CI/CD PIPELINE EXECUTION SUMMARY")
        print("="*80)

        # Calculate overall statistics
        stages_completed = len(self.stage_results)
        stages_total = len(self.pipeline_stages)

        if error:
            overall_success = False
            production_ready = False
        else:
            critical_stages_passed = all(
                r.success for r, s in zip(self.stage_results, self.pipeline_stages[:stages_completed])
                if s["critical"]
            )
            overall_success = len([r for r in self.stage_results if r.success]) == stages_completed
            production_ready = critical_stages_passed and overall_success

        # Calculate aggregate metrics
        total_tests = sum(r.test_count for r in self.stage_results)
        total_passed = sum(r.passed_tests for r in self.stage_results)
        total_failed = sum(r.failed_tests for r in self.stage_results)
        overall_error_rate = (total_failed / total_tests * 100) if total_tests > 0 else 0

        # Collect all issues
        all_issues = []
        for result in self.stage_results:
            all_issues.extend(result.issues)

        # Collect critical issues
        critical_issues = []
        for result in self.stage_results:
            if not result.success:
                critical_issues.extend(result.issues[:3])  # Top 3 issues per failed stage

        # Display summary
        print(f"\n🎯 PIPELINE EXECUTION OVERVIEW")
        print(f"├─ Execution ID: {self.execution_id}")
        print(f"├─ Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"├─ End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"├─ Total Duration: {total_duration:.2f} seconds")
        print(f"├─ Stages Completed: {stages_completed}/{stages_total}")
        print(f"├─ Overall Status: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
        print(f"└─ Production Ready: {'✅ YES' if production_ready else '❌ NO'}")

        # Test statistics
        print(f"\n📊 TEST EXECUTION STATISTICS")
        print(f"├─ Total Tests: {total_tests:,}")
        print(f"├─ Passed Tests: {total_passed:,}")
        print(f"├─ Failed Tests: {total_failed:,}")
        print(f"├─ Overall Error Rate: {overall_error_rate:.2f}%")
        if total_tests > 0:
            print(f"└─ Success Rate: {(total_passed/total_tests*100):.2f}%")
        else:
            print(f"└─ Success Rate: N/A (no tests executed)")

        # Stage-by-stage breakdown
        print(f"\n🔄 STAGE EXECUTION BREAKDOWN")
        for result in self.stage_results:
            status_icon = "✅" if result.success else "❌"
            print(f"{status_icon} {result.stage_name}")
            print(f"   ├─ Duration: {result.duration_seconds:.2f}s")
            print(f"   ├─ Tests: {result.passed_tests}/{result.test_count}")
            print(f"   ├─ Error Rate: {result.error_rate_percent:.1f}%")
            if result.issues:
                print(f"   └─ Issues: {len(result.issues)} identified")

        # Performance metrics
        print(f"\n⚡ PERFORMANCE METRICS SUMMARY")

        # Aggregate performance metrics
        all_metrics = {}
        for result in self.stage_results:
            for key, value in result.metrics.items():
                if isinstance(value, (int, float)):
                    if key not in all_metrics:
                        all_metrics[key] = []
                    all_metrics[key].append(value)

        # Show key performance indicators
        key_metrics = [
            "average_response_time_ms",
            "peak_throughput_rps",
            "success_rate_percent",
            "total_requests"
        ]

        for metric in key_metrics:
            if metric in all_metrics:
                values = all_metrics[metric]
                avg_val = sum(values) / len(values)
                max_val = max(values)
                min_val = min(values)
                print(f"├─ {metric.replace('_', ' ').title()}:")
                print(f"   │  ├─ Average: {avg_val:.2f}")
                print(f"   │  ├─ Maximum: {max_val:.2f}")
                print(f"   │  └─ Minimum: {min_val:.2f}")

        # Issues and recommendations
        if critical_issues:
            print(f"\n⚠️  CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION")
            for i, issue in enumerate(critical_issues[:5], 1):
                print(f"{i}. {issue}")

        if all_issues:
            print(f"\n📋 ALL ISSUES IDENTIFIED ({len(all_issues)} total)")
            issue_frequency = {}
            for issue in all_issues:
                normalized_issue = issue.lower().strip()
                issue_frequency[normalized_issue] = issue_frequency.get(normalized_issue, 0) + 1

            # Show most common issues
            common_issues = sorted(issue_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
            for issue, count in common_issues:
                print(f"├─ {issue}: {count} occurrences")

        # Recommendations
        all_recommendations = []
        for result in self.stage_results:
            all_recommendations.extend(result.recommendations)

        if all_recommendations:
            # Remove duplicates and show top recommendations
            unique_recommendations = list(set(all_recommendations))
            print(f"\n🚀 OPTIMIZATION RECOMMENDATIONS")
            for i, rec in enumerate(unique_recommendations[:10], 1):
                print(f"{i}. {rec}")

        # Deployment recommendation
        if production_ready:
            deployment_recommendation = "✅ APPROVED FOR PRODUCTION DEPLOYMENT"
            print(f"\n🎯 DEPLOYMENT DECISION")
            print(f"└─ {deployment_recommendation}")
        elif error:
            deployment_recommendation = "❌ PIPELINE EXECUTION FAILED - INVESTIGATE ERRORS"
            print(f"\n🎯 DEPLOYMENT DECISION")
            print(f"└─ {deployment_recommendation}")
        else:
            deployment_recommendation = "⚠️  NOT READY FOR PRODUCTION - ADDRESS CRITICAL ISSUES"
            print(f"\n🎯 DEPLOYMENT DECISION")
            print(f"└─ {deployment_recommendation}")

        # Generate comprehensive pipeline report
        pipeline_report = {
            "execution_id": self.execution_id,
            "pipeline_version": "1.0.0",
            "execution_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration_seconds": total_duration,
                "stages_completed": stages_completed,
                "stages_total": stages_total,
                "overall_success": overall_success,
                "production_ready": production_ready
            },
            "test_statistics": {
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "overall_error_rate_percent": overall_error_rate,
                "success_rate_percent": (total_passed/total_tests*100) if total_tests > 0 else 0
            },
            "stage_results": [asdict(result) for result in self.stage_results],
            "performance_metrics": all_metrics,
            "issues_identified": all_issues,
            "critical_issues": critical_issues,
            "optimization_recommendations": all_recommendations,
            "deployment_recommendation": deployment_recommendation,
            "pipeline_configuration": self.pipeline_stages
        }

        # Save pipeline report
        report_filename = f"pipeline_execution_report_{self.execution_id}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(pipeline_report, f, indent=2, default=str)
            print(f"\n📄 Comprehensive pipeline report saved to: {report_filename}")
        except Exception as e:
            print(f"\n⚠️  Failed to save pipeline report: {str(e)}")

        return PipelineExecutionSummary(
            pipeline_name="PsychSync Master CI/CD Pipeline",
            execution_id=self.execution_id,
            start_time=self.start_time,
            end_time=end_time,
            total_duration_seconds=total_duration,
            overall_success=overall_success,
            stages_completed=stages_completed,
            stages_total=stages_total,
            production_ready=production_ready,
            critical_issues=critical_issues,
            deployment_recommendation=deployment_recommendation
        )

async def main():
    """Main function to execute the master CI/CD pipeline"""
    print("🚀 PSYCHSYNC MASTER CI/CD INTEGRATION PIPELINE")
    print("=" * 80)
    print("This pipeline integrates all testing frameworks for comprehensive validation")
    print("and provides production readiness assessment for the PsychSync platform.")
    print("=" * 80)

    pipeline = MasterCICDPipeline()

    try:
        summary = await pipeline.execute_full_pipeline()

        # Return appropriate exit code
        if summary.production_ready:
            print(f"\n🎉 PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
            print(f"✅ PsychSync platform is PRODUCTION READY")
            print(f"🚀 Safe to proceed with deployment")
            return 0
        else:
            print(f"\n⚠️  PIPELINE EXECUTION COMPLETED WITH ISSUES")
            print(f"❌ Address critical issues before production deployment")
            return 1

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Pipeline execution interrupted by user")
        return 2
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {str(e)}")
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)