#!/usr/bin/env python3
"""
PsychSync Master Production Optimizer
Complete production readiness and optimization automation

This script orchestrates all production optimization tools:
1. Security Audit (pre_production_security_audit.py)
2. Database Excellence (database_excellence_optimizer.py)
3. API Enhancement (api_excellence_optimizer.py)
4. Testing Excellence (testing_excellence_suite.py)
5. Frontend Optimization (frontend_excellence_optimizer.py)
6. Deployment Readiness (deployment_readiness_automation.py)
7. Monitoring & Observability (monitoring_observability_system.py)
8. Documentation Package (documentation_package_generator.py)
"""

import asyncio
import importlib.util
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent))

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result from an optimization tool"""

    tool_name: str
    success: bool
    execution_time: float
    score: Optional[float]
    grade: Optional[str]
    critical_issues: List[str]
    recommendations: List[str]
    report_file: str


@dataclass
class MasterOptimizationReport:
    """Master optimization report"""

    timestamp: datetime
    total_execution_time: float
    overall_score: float
    overall_grade: str
    tool_results: List[OptimizationResult]
    combined_recommendations: List[str]
    combined_critical_issues: List[str]
    production_ready: bool
    next_steps: List[str]


class MasterProductionOptimizer:
    """
    Master optimizer that orchestrates all production optimization tools
    """

    def __init__(self, project_root: str = None):
        self.project_root = project_root or str(Path(__file__).parent.parent)
        self.scripts_dir = os.path.join(self.project_root, "scripts")
        self.tools = [
            {
                "name": "Security Audit",
                "script": "pre_production_security_audit.py",
                "description": "Comprehensive security vulnerability assessment",
                "critical": True,
                "priority": 1,
            },
            {
                "name": "Database Excellence",
                "script": "database_excellence_optimizer.py",
                "description": "Database performance optimization and analysis",
                "critical": True,
                "priority": 2,
            },
            {
                "name": "API Enhancement",
                "script": "api_excellence_optimizer.py",
                "description": "API performance and security optimization",
                "critical": True,
                "priority": 3,
            },
            {
                "name": "Testing Excellence",
                "script": "testing_excellence_suite.py",
                "description": "Comprehensive testing framework analysis",
                "critical": True,
                "priority": 4,
            },
            {
                "name": "Frontend Optimization",
                "script": "frontend_excellence_optimizer.py",
                "description": "Frontend performance and bundle optimization",
                "critical": False,
                "priority": 5,
            },
            {
                "name": "Deployment Readiness",
                "script": "deployment_readiness_automation.py",
                "description": "Deployment validation and automation",
                "critical": True,
                "priority": 6,
            },
            {
                "name": "Monitoring & Observability",
                "script": "monitoring_observability_system.py",
                "description": "Monitoring setup and configuration",
                "critical": False,
                "priority": 7,
            },
            {
                "name": "Documentation Package",
                "script": "documentation_package_generator.py",
                "description": "Complete documentation generation",
                "critical": False,
                "priority": 8,
            },
        ]

    async def run_complete_optimization(
        self, run_all: bool = True, selected_tools: List[str] = None
    ) -> MasterOptimizationReport:
        """Run complete production optimization"""
        print("🚀 PsychSync Master Production Optimizer")
        print("=" * 60)
        print("Complete Production Readiness & Optimization System")
        print()

        start_time = time.time()
        tool_results = []

        # Determine which tools to run
        tools_to_run = (
            self.tools
            if run_all
            else [tool for tool in self.tools if tool["name"] in selected_tools]
        )

        print(f"Running {len(tools_to_run)} optimization tools...")
        print()

        # Run each optimization tool
        for tool in tools_to_run:
            print(f"🔧 Running {tool['name']}...")
            print(f"   {tool['description']}")

            result = await self._run_optimization_tool(tool)
            tool_results.append(result)

            # Display immediate results
            status = "✅ PASSED" if result.success else "❌ FAILED"
            score_display = f"({result.score:.1f}/100)" if result.score else ""
            grade_display = f" [{result.grade}]" if result.grade else ""
            print(f"   {status} {score_display}{grade_display}")

            if result.critical_issues:
                for issue in result.critical_issues[:2]:  # Show first 2 issues
                    print(f"   ⚠️  {issue}")

            print()

        # Calculate overall metrics
        total_execution_time = time.time() - start_time
        overall_score = self._calculate_overall_score(tool_results)
        overall_grade = self._get_grade_from_score(overall_score)
        combined_critical_issues = self._combine_critical_issues(tool_results)
        combined_recommendations = self._combine_recommendations(tool_results)
        production_ready = overall_score >= 80 and len(combined_critical_issues) == 0

        # Generate next steps
        next_steps = self._generate_next_steps(tool_results, production_ready)

        # Create master report
        report = MasterOptimizationReport(
            timestamp=datetime.now(),
            total_execution_time=total_execution_time,
            overall_score=overall_score,
            overall_grade=overall_grade,
            tool_results=tool_results,
            combined_recommendations=combined_recommendations,
            combined_critical_issues=combined_critical_issues,
            production_ready=production_ready,
            next_steps=next_steps,
        )

        # Display summary
        self._display_summary(report)

        # Save master report
        await self._save_master_report(report)

        return report

    async def _run_optimization_tool(self, tool: Dict) -> OptimizationResult:
        """Run a single optimization tool"""
        script_path = os.path.join(self.scripts_dir, tool["script"])

        if not os.path.exists(script_path):
            return OptimizationResult(
                tool_name=tool["name"],
                success=False,
                execution_time=0.0,
                score=None,
                grade=None,
                critical_issues=[f"Script not found: {tool['script']}"],
                recommendations=[
                    f"Ensure {tool['script']} exists in scripts directory"
                ],
                report_file="",
            )

        start_time = time.time()

        try:
            # Run the script as a subprocess
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout per tool
            )

            execution_time = time.time() - start_time
            success = result.returncode == 0

            # Try to parse the report file if it exists
            report_file = f"{tool['script'].replace('.py', '_report.json')}"
            report_path = os.path.join(self.project_root, report_file)

            score = None
            grade = None
            critical_issues = []
            recommendations = []

            if os.path.exists(report_path):
                try:
                    with open(report_path, "r") as f:
                        report_data = json.load(f)

                    # Extract common fields from different report formats
                    if "overall_score" in report_data:
                        score = report_data["overall_score"]
                    elif "performance_score" in report_data:
                        score = report_data["performance_score"]
                    elif "quality_score" in report_data:
                        score = report_data["quality_score"]

                    if "overall_grade" in report_data:
                        grade = report_data["overall_grade"]
                    elif "grade" in report_data:
                        grade = report_data["grade"]

                    # Extract critical issues
                    if "critical_recommendations" in report_data:
                        critical_issues = report_data["critical_recommendations"]
                    elif "critical_issues" in report_data:
                        critical_issues = report_data["critical_issues"]
                    elif "blocking_issues" in report_data:
                        critical_issues = report_data["blocking_issues"]

                    # Extract recommendations
                    if "recommendations" in report_data:
                        recommendations = report_data["recommendations"]
                    elif "medium_priority_recommendations" in report_data:
                        recommendations = report_data["medium_priority_recommendations"]
                    elif "high_priority_recommendations" in report_data:
                        recommendations.extend(
                            report_data["high_priority_recommendations"]
                        )

                except Exception as e:
                    logger.error(f"Error parsing report file {report_file}: {e}")

            # If no score from report file, try to extract from stdout
            if score is None and result.stdout:
                score = self._extract_score_from_output(result.stdout)

            return OptimizationResult(
                tool_name=tool["name"],
                success=success,
                execution_time=execution_time,
                score=score,
                grade=grade,
                critical_issues=critical_issues,
                recommendations=recommendations,
                report_file=report_file,
            )

        except subprocess.TimeoutExpired:
            return OptimizationResult(
                tool_name=tool["name"],
                success=False,
                execution_time=600.0,
                score=None,
                grade=None,
                critical_issues=[f"Tool execution timed out after 10 minutes"],
                recommendations=["Check for infinite loops or long-running operations"],
                report_file="",
            )

        except Exception as e:
            return OptimizationResult(
                tool_name=tool["name"],
                success=False,
                execution_time=time.time() - start_time,
                score=None,
                grade=None,
                critical_issues=[f"Tool execution failed: {str(e)}"],
                recommendations=["Check tool dependencies and configuration"],
                report_file="",
            )

    def _extract_score_from_output(self, output: str) -> Optional[float]:
        """Extract score from tool output"""
        import re

        # Look for patterns like "Score: 85.3/100" or "Overall Score: 92.1"
        patterns = [
            r"(?i)(?:overall\s*)?score:\s*(\d+(?:\.\d+)?)",
            r"(?i)grade:\s*([A-F])",
            r"(?i)(\d+(?:\.\d+)?)\/100",
        ]

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                try:
                    value = float(match.group(1))
                    return min(100, value)  # Cap at 100
                except ValueError:
                    continue

        return None

    def _calculate_overall_score(self, tool_results: List[OptimizationResult]) -> float:
        """Calculate overall optimization score"""
        if not tool_results:
            return 0.0

        # Weight critical tools more heavily
        critical_tools = [
            r for r in tool_results if self._is_critical_tool(r.tool_name)
        ]
        non_critical_tools = [
            r for r in tool_results if not self._is_critical_tool(r.tool_name)
        ]

        scores = []
        weights = []

        for result in critical_tools:
            if result.score is not None:
                scores.append(result.score)
                weights.append(2)  # Double weight for critical tools

        for result in non_critical_tools:
            if result.score is not None:
                scores.append(result.score)
                weights.append(1)  # Normal weight for non-critical tools

        if not scores:
            return 0.0

        # Calculate weighted average
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)

        return weighted_sum / total_weight

    def _is_critical_tool(self, tool_name: str) -> bool:
        """Check if a tool is critical for production readiness"""
        critical_tools = [
            "Security Audit",
            "Database Excellence",
            "API Enhancement",
            "Testing Excellence",
            "Deployment Readiness",
        ]
        return tool_name in critical_tools

    def _get_grade_from_score(self, score: float) -> str:
        """Get grade from score"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 65:
            return "D+"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _combine_critical_issues(
        self, tool_results: List[OptimizationResult]
    ) -> List[str]:
        """Combine all critical issues from tool results"""
        all_issues = []

        for result in tool_results:
            all_issues.extend(result.critical_issues)

        # Remove duplicates while preserving order
        seen = set()
        unique_issues = []
        for issue in all_issues:
            if issue not in seen:
                unique_issues.append(issue)
                seen.add(issue)

        return unique_issues

    def _combine_recommendations(
        self, tool_results: List[OptimizationResult]
    ) -> List[str]:
        """Combine all recommendations from tool results"""
        all_recommendations = []

        for result in tool_results:
            all_recommendations.extend(result.recommendations)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in all_recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)

        return unique_recommendations

    def _generate_next_steps(
        self, tool_results: List[OptimizationResult], production_ready: bool
    ) -> List[str]:
        """Generate next steps based on results"""
        next_steps = []

        if production_ready:
            next_steps.extend(
                [
                    "🚀 System is PRODUCTION READY!",
                    "📋 Create deployment plan and schedule",
                    "🔄 Set up CI/CD pipeline automation",
                    "📊 Configure production monitoring alerts",
                    "📚 Share documentation with team",
                ]
            )
        else:
            failed_tools = [r for r in tool_results if not r.success]
            critical_issues_tools = [r for r in tool_results if r.critical_issues]

            if failed_tools:
                next_steps.append(
                    f"🔧 Fix {len(failed_tools)} failed tool(s): {', '.join([t.tool_name for t in failed_tools])}"
                )

            if critical_issues_tools:
                next_steps.append(
                    f"⚠️  Address {len(critical_issues_tools)} tools with critical issues"
                )

            low_score_tools = [r for r in tool_results if r.score and r.score < 70]
            if low_score_tools:
                next_steps.append(
                    f"📈 Improve {len(low_score_tools)} tools with low scores: {', '.join([t.tool_name for t in low_score_tools])}"
                )

            next_steps.extend(
                [
                    "🔄 Re-run optimization tools after fixes",
                    "📋 Review individual tool reports for detailed guidance",
                    "👥 Schedule team meeting to discuss remediation plan",
                ]
            )

        return next_steps

    def _display_summary(self, report: MasterOptimizationReport):
        """Display optimization summary"""
        print("=" * 60)
        print("🎯 OPTIMIZATION SUMMARY")
        print("=" * 60)

        print(f"📊 Overall Production Readiness Score: {report.overall_score:.1f}/100")
        print(f"📈 Overall Grade: {report.overall_grade}")
        print(f"⏱️  Total Execution Time: {report.total_execution_time:.1f} seconds")
        print(
            f"🚀 Production Ready: {'✅ YES' if report.production_ready else '❌ NO'}"
        )

        print(f"\n📊 Tool Results:")
        for result in report.tool_results:
            status = "✅ PASSED" if result.success else "❌ FAILED"
            score_display = f" ({result.score:.1f}/100)" if result.score else ""
            grade_display = f" [{result.grade}]" if result.grade else ""
            time_display = (
                f" ({result.execution_time:.1f}s)" if result.execution_time > 0 else ""
            )

            print(
                f"   {status} {result.tool_name}{score_display}{grade_display}{time_display}"
            )

            # Show critical issues count
            if result.critical_issues:
                print(f"      ⚠️  {len(result.critical_issues)} critical issues")

        if report.combined_critical_issues:
            print(
                f"\n🚨 Combined Critical Issues ({len(report.combined_critical_issues)}):"
            )
            for issue in report.combined_critical_issues[:5]:  # Show first 5
                print(f"   • {issue}")
            if len(report.combined_critical_issues) > 5:
                print(f"   ... and {len(report.combined_critical_issues) - 5} more")

        if report.combined_recommendations:
            print(f"\n💡 Top Recommendations:")
            for rec in report.combined_recommendations[:5]:  # Show first 5
                print(f"   • {rec}")
            if len(report.combined_recommendations) > 5:
                print(f"   ... and {len(report.combined_recommendations) - 5} more")

        print(f"\n🎯 Next Steps:")
        for step in report.next_steps:
            print(f"   {step}")

        print()

    async def _save_master_report(self, report: MasterOptimizationReport):
        """Save master optimization report"""
        report_file = os.path.join(
            self.project_root, "master_production_optimization_report.json"
        )

        try:
            with open(report_file, "w") as f:
                json.dump(asdict(report), f, indent=2, default=str)

            print(f"📄 Master optimization report saved to: {report_file}")

            # Also save a human-readable summary
            summary_file = os.path.join(
                self.project_root, "PRODUCTION_READINESS_SUMMARY.md"
            )
            await self._save_summary_markdown(report, summary_file)

        except Exception as e:
            logger.error(f"Error saving master report: {e}")

    async def _save_summary_markdown(
        self, report: MasterOptimizationReport, summary_file: str
    ):
        """Save human-readable summary in markdown format"""
        summary_content = f"""# PsychSync Production Readiness Summary

**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Overall Score:** {report.overall_score:.1f}/100 ({report.overall_grade})
**Production Ready:** {'✅ YES' if report.production_ready else '❌ NO'}
**Execution Time:** {report.total_execution_time:.1f} seconds

## Tool Results

| Tool | Status | Score | Grade | Time |
|------|--------|-------|-------|------|
"""

        for result in report.tool_results:
            status = "✅ PASSED" if result.success else "❌ FAILED"
            score = f"{result.score:.1f}/100" if result.score else "N/A"
            grade = result.grade or "N/A"
            time = (
                f"{result.execution_time:.1f}s" if result.execution_time > 0 else "N/A"
            )
            summary_content += (
                f"| {result.tool_name} | {status} | {score} | {grade} | {time} |\n"
            )

        if report.combined_critical_issues:
            summary_content += f"""
## Critical Issues ({len(report.combined_critical_issues)})

"""
            for issue in report.combined_critical_issues:
                summary_content += f"- ⚠️ {issue}\n"

        if report.combined_recommendations:
            summary_content += f"""
## Recommendations

"""
            for rec in report.combined_recommendations:
                summary_content += f"- 💡 {rec}\n"

        summary_content += f"""
## Next Steps

"""
        for step in report.next_steps:
            summary_content += f"- {step}\n"

        summary_content += f"""
---

*This report was generated by the PsychSync Master Production Optimizer*
*For detailed reports, see the individual tool reports in the project directory*
"""

        with open(summary_file, "w") as f:
            f.write(summary_content)

        print(f"📄 Human-readable summary saved to: {summary_file}")


async def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="PsychSync Master Production Optimizer"
    )
    parser.add_argument(
        "--tools",
        nargs="+",
        help="Specific tools to run",
        choices=[tool["name"] for tool in MasterProductionOptimizer().tools],
    )
    parser.add_argument("--quick", action="store_true", help="Run only critical tools")

    args = parser.parse_args()

    optimizer = MasterProductionOptimizer()

    try:
        # Determine which tools to run
        if args.tools:
            # Run specific tools
            report = await optimizer.run_complete_optimization(
                run_all=False, selected_tools=args.tools
            )
        elif args.quick:
            # Run only critical tools
            critical_tools = [
                tool["name"] for tool in optimizer.tools if tool["critical"]
            ]
            report = await optimizer.run_complete_optimization(
                run_all=False, selected_tools=critical_tools
            )
        else:
            # Run all tools
            report = await optimizer.run_complete_optimization(run_all=True)

        # Return appropriate exit code
        return 0 if report.production_ready else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Optimization interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error during optimization: {e}")
        print(f"\n❌ Optimization failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
