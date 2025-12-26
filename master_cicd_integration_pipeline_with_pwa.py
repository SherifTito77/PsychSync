#!/usr/bin/env python3
"""
🚀 PsychSync Master CI/CD Integration Pipeline with PWA Testing
====================================================================

Enhanced master pipeline that orchestrates all testing frameworks including
the new Progressive Web App (PWA) testing suite for complete platform validation.

Pipeline Architecture:
├─ Stage 1: Regression Testing (Priority 1, Critical)
├─ Stage 2: User Permission Testing (Priority 2, Critical)
├─ Stage 3: Team Member Testing (Priority 2, Critical)
├─ Stage 4: PWA Testing (Priority 3, Critical)
├─ Stage 5: Load Testing (Priority 3, Critical)
├─ Stage 6: Monitoring Testing (Priority 3, Critical)
└─ Stage 7: Compatibility Testing (Priority 4, Optional)

Total Frameworks: 8 comprehensive testing suites
Total Code Lines: 12,000+ lines of enterprise-grade testing
"""

import asyncio
import json
import time
import os
import sys
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CICDIntegrationPipeline:
    """Enhanced master CI/CD pipeline with PWA testing integration"""

    def __init__(self):
        self.execution_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.base_url = os.getenv('BASE_URL', 'http://localhost:8000')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.read_only_tests = os.getenv('READ_ONLY_TESTS', 'false').lower() == 'true'

        # Pipeline configuration
        self.pipeline_stages = [
            {
                "stage": "Regression Testing",
                "file": "test_psychsync_regression_suite.py",
                "priority": 1,
                "critical": True,
                "timeout": 300,
                "description": "Core platform functionality validation"
            },
            {
                "stage": "User Permission Testing",
                "file": "test_user_permissions_profile_settings.py",
                "priority": 2,
                "critical": True,
                "timeout": 180,
                "description": "Role-based access control validation"
            },
            {
                "stage": "Team Member Testing",
                "file": "test_manual_team_member_addition.py",
                "priority": 2,
                "critical": True,
                "timeout": 200,
                "description": "Team management workflow validation"
            },
            {
                "stage": "PWA Testing",
                "file": "pwa_comprehensive_test_suite.py",
                "priority": 3,
                "critical": True,
                "timeout": 180,
                "description": "Progressive Web App functionality validation"
            },
            {
                "stage": "Real Device PWA Testing",
                "file": "real_device_pwa_testing.py",
                "priority": 3,
                "critical": False,
                "timeout": 240,
                "description": "PWA cross-device compatibility testing"
            },
            {
                "stage": "Load Testing",
                "file": "advanced_load_testing_suite.py",
                "priority": 3,
                "critical": True,
                "timeout": 600,
                "description": "Performance under load validation"
            },
            {
                "stage": "Monitoring Testing",
                "file": "monitoring_alerting_system_tests.py",
                "priority": 3,
                "critical": True,
                "timeout": 200,
                "description": "System observability validation"
            },
            {
                "stage": "Compatibility Testing",
                "file": "cross_platform_compatibility_tests.py",
                "priority": 4,
                "critical": False,
                "timeout": 300,
                "description": "Cross-platform compatibility validation"
            }
        ]

        # Results tracking
        self.results = {
            "execution_id": self.execution_id,
            "start_time": datetime.now().isoformat(),
            "environment": self.environment,
            "base_url": self.base_url,
            "frontend_url": self.frontend_url,
            "stages_completed": 0,
            "stages_total": len(self.pipeline_stages),
            "stage_results": [],
            "overall_metrics": {},
            "issues": [],
            "recommendations": [],
            "production_ready": False
        }

    async def execute_pipeline(self) -> Dict[str, Any]:
        """Execute the complete CI/CD pipeline with PWA testing"""
        logger.info(f"🚀 Starting PsychSync CI/CD Pipeline with PWA Testing")
        logger.info(f"📋 Execution ID: {self.execution_id}")
        logger.info(f"🌍 Environment: {self.environment}")
        logger.info(f"🔗 Backend URL: {self.base_url}")
        logger.info(f"🌐 Frontend URL: {self.frontend_url}")

        start_time = time.time()

        try:
            # Pre-execution validation
            await self.validate_environment()

            # Execute pipeline stages
            for i, stage in enumerate(self.pipeline_stages):
                stage_result = await self.execute_stage(stage, i + 1)
                self.results["stage_results"].append(stage_result)
                self.results["stages_completed"] = i + 1

                # Check for critical failures
                if stage.get("critical", False) and not stage_result.get("passed", True):
                    logger.error(f"❌ Critical stage failed: {stage['stage']}")
                    self.results["issues"].append({
                        "stage": stage["stage"],
                        "severity": "CRITICAL",
                        "message": f"Critical stage {stage['stage']} failed"
                    })
                    if self.environment != "development":
                        break

            # Generate overall metrics and assessment
            await self.generate_overall_metrics()
            await self.assess_production_readiness()

            # Generate comprehensive report
            total_duration = time.time() - start_time
            await self.generate_pipeline_report(total_duration)

            return self.results

        except Exception as e:
            logger.error(f"❌ Pipeline execution failed: {e}")
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            self.results["issues"].append({
                "stage": "PIPELINE",
                "severity": "CRITICAL",
                "message": f"Pipeline execution failed: {str(e)}"
            })
            return self.results

    async def validate_environment(self):
        """Validate environment before executing pipeline"""
        logger.info("🔍 Validating environment...")

        # Check backend availability
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/v1/health", timeout=10.0)
                if response.status_code == 200:
                    logger.info("✅ Backend health check passed")
                else:
                    logger.warning(f"⚠️ Backend health check returned {response.status_code}")
        except Exception as e:
            if self.environment == "production":
                raise Exception(f"Backend not available: {e}")
            else:
                logger.warning(f"⚠️ Backend health check failed: {e}")

        # Check frontend availability (if needed for PWA testing)
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(self.frontend_url, timeout=10.0)
                if response.status_code == 200:
                    logger.info("✅ Frontend availability check passed")
                else:
                    logger.warning(f"⚠️ Frontend returned {response.status_code}")
        except Exception as e:
            if self.environment == "production":
                logger.warning(f"⚠️ Frontend health check failed: {e}")
            else:
                logger.warning(f"⚠️ Frontend health check failed: {e}")

        # Check required files exist
        required_files = [stage["file"] for stage in self.pipeline_stages]
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)

        if missing_files:
            logger.error(f"❌ Missing test files: {missing_files}")
            raise Exception(f"Required test files not found: {missing_files}")

        logger.info("✅ Environment validation completed")

    async def execute_stage(self, stage: Dict[str, Any], stage_number: int) -> Dict[str, Any]:
        """Execute a single pipeline stage"""
        stage_name = stage["stage"]
        stage_file = stage["file"]
        stage_timeout = stage.get("timeout", 300)
        stage_priority = stage.get("priority", 99)

        logger.info(f"📋 [{stage_number}/{len(self.pipeline_stages)}] Executing: {stage_name}")
        logger.info(f"📁 File: {stage_file}")
        logger.info(f"⏱️ Timeout: {stage_timeout}s")
        logger.info(f"🎯 Priority: {stage_priority}")

        start_time = time.time()

        try:
            # Execute the test suite
            process = await asyncio.create_subprocess_exec(
                sys.executable, stage_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=stage_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise Exception(f"Stage timed out after {stage_timeout} seconds")

            execution_time = time.time() - start_time
            return_code = process.returncode

            # Parse results
            stage_result = await self.parse_stage_results(
                stage_name, stage_file, return_code, stdout, stderr, execution_time
            )

            logger.info(f"{'✅' if stage_result['passed'] else '❌'} {stage_name}: {stage_result['score']:.1f}%")
            if stage_result.get('issues'):
                logger.warning(f"⚠️ Issues found: {len(stage_result['issues'])}")

            return stage_result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Stage execution failed: {e}")

            return {
                "stage": stage_name,
                "file": stage_file,
                "priority": stage_priority,
                "passed": False,
                "score": 0.0,
                "execution_time": execution_time,
                "issues": [
                    {
                        "severity": "CRITICAL",
                        "message": f"Stage execution failed: {str(e)}"
                    }
                ],
                "metrics": {},
                "recommendations": ["Fix stage execution errors before proceeding"]
            }

    async def parse_stage_results(
        self, stage_name: str, stage_file: str, return_code: int,
        stdout: bytes, stderr: bytes, execution_time: float
    ) -> Dict[str, Any]:
        """Parse and format stage execution results"""

        try:
            # Decode output
            stdout_text = stdout.decode('utf-8') if stdout else ""
            stderr_text = stderr.decode('utf-8') if stderr else ""

            # Try to find JSON report
            json_report = None
            try:
                # Look for JSON report file
                report_files = list(Path('.').glob(f'*{stage_file.replace(".py", "")}*report*.json'))
                if report_files:
                    latest_report = max(report_files, key=lambda p: p.stat().st_mtime)
                    with open(latest_report, 'r') as f:
                        json_report = json.load(f)
            except Exception:
                pass

            # Extract metrics from JSON report or parse manually
            if json_report:
                metrics = await self.extract_metrics_from_json_report(json_report)
                issues = json_report.get('issues', [])
                recommendations = json_report.get('recommendations', [])
                score = json_report.get('overall_score', 0.0)
                passed = return_code == 0 and score >= 70.0
            else:
                # Parse output manually
                metrics = await self.extract_metrics_from_output(stdout_text, stderr_text)
                issues = await self.extract_issues_from_output(stderr_text)
                recommendations = await self.extract_recommendations_from_output(stdout_text)
                score = 100.0 if return_code == 0 else 0.0
                passed = return_code == 0

            return {
                "stage": stage_name,
                "file": stage_file,
                "priority": self.get_stage_priority(stage_name),
                "passed": passed,
                "score": score,
                "execution_time": execution_time,
                "issues": issues,
                "metrics": metrics,
                "recommendations": recommendations,
                "output_length": len(stdout_text) + len(stderr_text)
            }

        except Exception as e:
            logger.error(f"❌ Failed to parse stage results: {e}")
            return {
                "stage": stage_name,
                "file": stage_file,
                "priority": self.get_stage_priority(stage_name),
                "passed": False,
                "score": 0.0,
                "execution_time": execution_time,
                "issues": [
                    {
                        "severity": "ERROR",
                        "message": f"Failed to parse results: {str(e)}"
                    }
                ],
                "metrics": {},
                "recommendations": ["Fix result parsing issues"]
            }

    def get_stage_priority(self, stage_name: str) -> int:
        """Get priority level for a stage"""
        for stage in self.pipeline_stages:
            if stage["stage"] == stage_name:
                return stage.get("priority", 99)
        return 99

    async def extract_metrics_from_json_report(self, json_report: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from JSON report"""
        metrics = {}

        # Common metrics
        if "test_execution" in json_report:
            metrics.update(json_report["test_execution"])

        if "overall_metrics" in json_report:
            metrics.update(json_report["overall_metrics"])

        # PWA-specific metrics
        if json_report.get("overall_score") is not None:
            metrics["pwa_score"] = json_report["overall_score"]

        # Performance metrics
        if "performance_metrics" in json_report:
            metrics.update(json_report["performance_metrics"])

        return metrics

    async def extract_metrics_from_output(self, stdout: str, stderr: str) -> Dict[str, Any]:
        """Extract metrics from text output"""
        metrics = {}

        # Look for performance metrics
        lines = (stdout + stderr).split('\n')
        for line in lines:
            if "Success Rate:" in line:
                try:
                    success_rate = float(line.split("Success Rate:")[1].strip().split("%")[0])
                    metrics["success_rate"] = success_rate
                except:
                    pass
            elif "Tests Passed:" in line:
                try:
                    passed = int(line.split("Tests Passed:")[1].split("/")[0])
                    total = int(line.split("Tests Passed:")[1].split("/")[1])
                    metrics["tests_passed"] = passed
                    metrics["tests_total"] = total
                    metrics["success_rate"] = (passed / total) * 100 if total > 0 else 0
                except:
                    pass
            elif "Overall Score:" in line:
                try:
                    score = float(line.split("Overall Score:")[1].strip().split("%")[0])
                    metrics["overall_score"] = score
                except:
                    pass

        return metrics

    async def extract_issues_from_output(self, stderr: str) -> List[Dict[str, Any]]:
        """Extract issues from error output"""
        issues = []
        lines = stderr.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith("ERROR:") or line.startswith("CRITICAL:") or line.startswith("❌"):
                issues.append({
                    "severity": "HIGH" if "CRITICAL" in line else "MEDIUM",
                    "message": line
                })

        return issues

    async def extract_recommendations_from_output(self, stdout: str) -> List[str]:
        """Extract recommendations from output"""
        recommendations = []
        lines = stdout.split('\n')

        for line in lines:
            if "⚠️" in line or "WARNING:" in line:
                recommendations.append(line.strip())

        return recommendations

    async def generate_overall_metrics(self):
        """Generate overall pipeline metrics"""
        total_stages = len(self.results["stage_results"])
        passed_stages = sum(1 for stage in self.results["stage_results"] if stage.get("passed", False))
        critical_stages = [s for s in self.results["stage_results"] if s.get("priority", 99) <= 3]
        passed_critical = sum(1 for stage in critical_stages if stage.get("passed", False))

        total_tests = 0
        total_score = 0.0
        total_execution_time = 0.0
        all_issues = []

        for stage in self.results["stage_results"]:
            metrics = stage.get("metrics", {})
            if "tests_total" in metrics:
                total_tests += metrics["tests_total"]
            if "overall_score" in metrics:
                total_score += stage["score"]
            total_execution_time += stage.get("execution_time", 0)
            all_issues.extend(stage.get("issues", []))

        self.results["overall_metrics"] = {
            "total_stages": total_stages,
            "passed_stages": passed_stages,
            "critical_stages": len(critical_stages),
            "passed_critical": passed_critical,
            "stage_success_rate": (passed_stages / total_stages * 100) if total_stages > 0 else 0,
            "critical_success_rate": (passed_critical / len(critical_stages) * 100) if critical_stages else 0,
            "overall_score": (total_score / total_stages) if total_stages > 0 else 0,
            "total_tests": total_tests,
            "total_execution_time": total_execution_time,
            "total_issues": len(all_issues),
            "critical_issues": len([i for i in all_issues if i.get("severity") == "CRITICAL"]),
            "high_issues": len([i for i in all_issues if i.get("severity") == "HIGH"]),
            "medium_issues": len([i for i in all_issues if i.get("severity") == "MEDIUM"])
        }

        # Consolidate issues
        self.results["issues"] = all_issues

    async def assess_production_readiness(self):
        """Assess if the system is ready for production deployment"""
        metrics = self.results["overall_metrics"]

        # Critical criteria
        critical_passed = (
            metrics["critical_success_rate"] >= 90 and
            metrics["critical_issues"] == 0 and
            metrics["overall_score"] >= 80
        )

        # Overall criteria
        overall_passed = (
            metrics["stage_success_rate"] >= 95 and
            metrics["high_issues"] == 0 and
            metrics["overall_score"] >= 85
        )

        # PWA-specific criteria (if PWA tests ran)
        pwa_results = [s for s in self.results["stage_results"] if "PWA" in s["stage"]]
        pwa_passed = True
        if pwa_results:
            pwa_scores = [s["score"] for s in pwa_results]
            avg_pwa_score = sum(pwa_scores) / len(pwa_scores)
            pwa_passed = avg_pwa_score >= 90 and all(s.get("passed", False) for s in pwa_results)

        # Environment-specific criteria
        if self.environment == "production":
            self.results["production_ready"] = critical_passed and overall_passed and pwa_passed
        elif self.environment == "staging":
            self.results["production_ready"] = critical_passed and pwa_passed
        else:
            self.results["production_ready"] = critical_passed

        # Generate recommendations
        if not self.results["production_ready"]:
            if metrics["critical_issues"] > 0:
                self.results["recommendations"].append("Resolve all critical issues before deployment")
            if metrics["critical_success_rate"] < 90:
                self.results["recommendations"].append("All critical stages must pass with 90%+ success rate")
            if metrics["overall_score"] < 80:
                self.results["recommendations"].append("Improve overall test scores to 80%+ before production")
            if pwa_results and not pwa_passed:
                self.results["recommendations"].append("PWA functionality must achieve 90%+ score for production")
        else:
            self.results["recommendations"].append("✅ System ready for production deployment")

    async def generate_pipeline_report(self, total_duration: float):
        """Generate comprehensive pipeline execution report"""
        self.results["end_time"] = datetime.now().isoformat()
        self.results["total_duration"] = total_duration
        self.results["status"] = "SUCCESS" if self.results["production_ready"] else "NEEDS_ATTENTION"

        # Generate summary
        summary = f"""
🚀 PSYCHSYNC CI/CD PIPELINE EXECUTION SUMMARY
=============================================
Execution ID: {self.execution_id}
Environment: {self.environment}
Duration: {total_duration:.2f} seconds
Status: {self.results['status']}

📊 OVERALL METRICS:
├─ Stages Completed: {self.results['overall_metrics']['passed_stages']}/{self.results['overall_metrics']['total_stages']}
├─ Critical Stages: {self.results['overall_metrics']['passed_critical']}/{self.results['overall_metrics']['critical_stages']}
├─ Overall Score: {self.results['overall_metrics']['overall_score']:.1f}%
├─ Success Rate: {self.results['overall_metrics']['stage_success_rate']:.1f}%
├─ Total Tests: {self.results['overall_metrics']['total_tests']}
└─ Total Issues: {self.results['overall_metrics']['total_issues']}

📋 STAGE RESULTS:
"""

        for stage in self.results["stage_results"]:
            status_icon = "✅" if stage.get("passed", False) else "❌"
            summary += f"├─ {status_icon} {stage['stage']}: {stage['score']:.1f}% ({stage.get('execution_time', 0):.1f}s)\n"

        summary += f"\n🎯 PRODUCTION READINESS: {'✅ READY' if self.results['production_ready'] else '❌ NOT READY'}\n"

        if self.results["recommendations"]:
            summary += "\n📝 RECOMMENDATIONS:\n"
            for rec in self.results["recommendations"]:
                summary += f"├─ {rec}\n"

        logger.info(summary)

        # Save detailed report
        report_filename = f"pipeline_execution_report_{self.execution_id}.json"
        try:
            with open(report_filename, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info(f"📊 Detailed report saved: {report_filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")

        # Save summary report
        summary_filename = f"pipeline_summary_{self.execution_id}.txt"
        try:
            with open(summary_filename, 'w') as f:
                f.write(summary)
            logger.info(f"📄 Summary report saved: {summary_filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save summary: {e}")

async def main():
    """Main pipeline execution"""
    pipeline = CICDIntegrationPipeline()

    try:
        results = await pipeline.execute_pipeline()

        # Exit with appropriate code
        if results["production_ready"]:
            logger.info("🎉 Pipeline completed successfully - PRODUCTION READY")
            sys.exit(0)
        else:
            logger.error("❌ Pipeline completed with issues - NOT PRODUCTION READY")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("⚠️ Pipeline interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())