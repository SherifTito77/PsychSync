#!/usr/bin/env python3
"""
AI Agent Orchestrator - Run and manage AI agents for PsychSync
This script executes various AI agents for code quality, testing, security, and monitoring.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_agents.agent_framework import AgentConfig, AgentOrchestrator
from ai_agents.analytics_workflow_agents import (
    APITestingAgent,
    BackupAgent,
    CIPipelineMonitorAgent,
    CodeReviewAgent,
    DependencyUpdaterAgent,
    DeploymentSafetyAgent,
    DocumentationAuditorAgent,
    ErrorRateMonitorAgent,
    HealthMonitorAgent,
    IncidentResponseAgent,
    LintEnforcerAgent,
    LoadTestingAgent,
    MergeSafetyAgent,
    PerformanceMetricsAgent,
    ReleaseValidatorAgent,
    ScalabilityAnalyzerAgent,
    SecurityScannerAgent,
    SLAMonitorAgent,
    TestCoverageAgent,
    TestDataGeneratorAgent,
    TypeCheckValidatorAgent,
    UITestingAgent,
    UsageStatisticsAgent,
    UserBehaviorAnalyticsAgent,
)
from ai_agents.code_quality_agents import (
    APIDriftDetectorAgent,
    AutoTestGeneratorAgent,
    BugSummarizerAgent,
    CodeQualityMonitorAgent,
    CodeStandardizerAgent,
    DocumentationCompletenessAgent,
    DuplicateIssueDetectorAgent,
    EngineeringPerformanceAgent,
    JSONSchemaValidatorAgent,
    LogAnomalyScannerAgent,
    ModuleDecomposerAgent,
    PRQualityScorerAgent,
    UnusedCodeDetectorAgent,
)
from ai_agents.specialized_agents import (
    ArchitectureDriftDetectorAgent,
    BugEnvironmentCreatorAgent,
    CodingStyleEnforcerAgent,
)
from ai_agents.specialized_agents import (
    DependencyUpdaterAgent as DependencyUpdaterAgentV2,
)
from ai_agents.specialized_agents import (
    EncryptionStrategyAgent,
    EnvironmentConfigDetectorAgent,
    IncidentMitigationPlannerAgent,
    LocalizationGapDetectorAgent,
    PerformanceRegressionAgent,
    PermissionGapDetectorAgent,
    PRToJiraMapperAgent,
    RefactoringTargetProposerAgent,
    ReleaseNotesGeneratorAgent,
    SecurityHeaderValidatorAgent,
    SlowEndpointTrackerAgent,
    TestCoverageReporterAgent,
    ThirdPartyScriptSafetyAgent,
    UptimeMonitorAgent,
    UXFrictionTrackerAgent,
    WeeklyStabilityScorerAgent,
)
from ai_agents.testing_performance_agents import (
    AccessibilityAuditorAgent,
    APIMockGeneratorAgent,
    BreakingChangeDetectorAgent,
    BuildFailureAnalyzerAgent,
    BundleOptimizerAgent,
    CachingConfigOptimizerAgent,
    CommentImproverAgent,
    DebugCodeRemoverAgent,
    DeprecatedLibraryDetectorAgent,
    ErrorCodeGeneratorAgent,
    MemoryLeakDetectorAgent,
    PaginationValidatorAgent,
    QueryOptimizerAgent,
    ReRenderOptimizerAgent,
    SpaghettiCodeRefactorAgent,
    SQLInjectionAuditorAgent,
    UnusedCSSDetectorAgent,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_agents/agent_execution.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def register_all_agents(orchestrator: AgentOrchestrator, project_root: str):
    """Register all 54 AI agents with the orchestrator"""

    # Code Quality Agents (13)
    orchestrator.register_agent(
        CodeQualityMonitorAgent(
            AgentConfig(
                name="code_quality_monitor",
                description="Monitor code quality metrics daily",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        BugSummarizerAgent(
            AgentConfig(
                name="bug_summarizer",
                description="Summarize new bugs from Jira",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        EngineeringPerformanceAgent(
            AgentConfig(
                name="engineering_performance",
                description="Generate weekly engineering performance report",
                category="code_quality",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        PRQualityScorerAgent(
            AgentConfig(
                name="pr_quality_scorer",
                description="Score pull requests for quality & risk",
                category="code_quality",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        CodeStandardizerAgent(
            AgentConfig(
                name="code_standardizer",
                description="Rewrite inconsistent code to match standards",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        APIDriftDetectorAgent(
            AgentConfig(
                name="api_drift_detector",
                description="Detect API contracts that drift from spec",
                category="code_quality",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        LogAnomalyScannerAgent(
            AgentConfig(
                name="log_anomaly_scanner",
                description="Continuously scan logs for anomalies",
                category="code_quality",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        AutoTestGeneratorAgent(
            AgentConfig(
                name="auto_test_generator",
                description="Create tests for new endpoints",
                category="code_quality",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        DocumentationCompletenessAgent(
            AgentConfig(
                name="documentation_completeness",
                description="Assess documentation completeness",
                category="code_quality",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        UnusedCodeDetectorAgent(
            AgentConfig(
                name="unused_code_detector",
                description="Identify unused code",
                category="code_quality",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        ModuleDecomposerAgent(
            AgentConfig(
                name="module_decomposer",
                description="Propose decompositions of overgrown modules",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        JSONSchemaValidatorAgent(
            AgentConfig(
                name="json_schema_validator",
                description="Validate JSON responses follow schema",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        DuplicateIssueDetectorAgent(
            AgentConfig(
                name="duplicate_issue_detector",
                description="Check open issues for duplicates",
                category="code_quality",
                priority="low",
            )
        )
    )

    # Testing & Performance Agents (17)
    orchestrator.register_agent(
        CommentImproverAgent(
            AgentConfig(
                name="comment_improver",
                description="Improve code comments",
                category="testing",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        ErrorCodeGeneratorAgent(
            AgentConfig(
                name="error_code_generator",
                description="Generate standardized error codes",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        SQLInjectionAuditorAgent(
            AgentConfig(
                name="sql_injection_auditor",
                description="Audit SQL for injection risks",
                category="security",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        QueryOptimizerAgent(
            AgentConfig(
                name="query_optimizer",
                description="Rewrite slow queries",
                category="performance",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        BuildFailureAnalyzerAgent(
            AgentConfig(
                name="build_failure_analyzer",
                description="Analyze build failures",
                category="testing",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        CachingConfigOptimizerAgent(
            AgentConfig(
                name="caching_config_optimizer",
                description="Optimize caching configuration",
                category="performance",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        BreakingChangeDetectorAgent(
            AgentConfig(
                name="breaking_change_detector",
                description="Detect breaking changes",
                category="testing",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        SpaghettiCodeRefactorAgent(
            AgentConfig(
                name="spaghetti_code_refactor",
                description="Refactor spaghetti code",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        DeprecatedLibraryDetectorAgent(
            AgentConfig(
                name="deprecated_library_detector",
                description="Find deprecated libraries",
                category="security",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        DebugCodeRemoverAgent(
            AgentConfig(
                name="debug_code_remover",
                description="Remove console logs & debug code",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        APIMockGeneratorAgent(
            AgentConfig(
                name="api_mock_generator",
                description="Generate API mocks",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        PaginationValidatorAgent(
            AgentConfig(
                name="pagination_validator",
                description="Detect missing pagination",
                category="performance",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        AccessibilityAuditorAgent(
            AgentConfig(
                name="accessibility_auditor",
                description="Generate UI accessibility report",
                category="testing",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        ReRenderOptimizerAgent(
            AgentConfig(
                name="rerender_optimizer",
                description="Flag unnecessary re-renders",
                category="performance",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        BundleOptimizerAgent(
            AgentConfig(
                name="bundle_optimizer",
                description="Optimize frontend bundle",
                category="performance",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        MemoryLeakDetectorAgent(
            AgentConfig(
                name="memory_leak_detector",
                description="Find potential memory leaks",
                category="performance",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        UnusedCSSDetectorAgent(
            AgentConfig(
                name="unused_css_detector",
                description="Detect unused CSS classes",
                category="performance",
                priority="low",
            )
        )
    )

    # Analytics & Workflow Agents (24)
    orchestrator.register_agent(
        HealthMonitorAgent(
            AgentConfig(
                name="health_monitor",
                description="Monitor application health",
                category="monitoring",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        ErrorRateMonitorAgent(
            AgentConfig(
                name="error_rate_monitor",
                description="Monitor error rates",
                category="monitoring",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        PerformanceMetricsAgent(
            AgentConfig(
                name="performance_metrics",
                description="Collect performance metrics",
                category="monitoring",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        UserBehaviorAnalyticsAgent(
            AgentConfig(
                name="user_behavior_analytics",
                description="Analyze user behavior",
                category="analytics",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        UsageStatisticsAgent(
            AgentConfig(
                name="usage_statistics",
                description="Aggregate usage statistics",
                category="analytics",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        CIPipelineMonitorAgent(
            AgentConfig(
                name="ci_pipeline_monitor",
                description="Monitor CI/CD pipelines",
                category="monitoring",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        TestCoverageAgent(
            AgentConfig(
                name="test_coverage",
                description="Measure test coverage",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        DeploymentSafetyAgent(
            AgentConfig(
                name="deployment_safety",
                description="Ensure safe deployments",
                category="deployment",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        DependencyUpdaterAgent(
            AgentConfig(
                name="dependency_updater",
                description="Update dependencies",
                category="maintenance",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        LintEnforcerAgent(
            AgentConfig(
                name="lint_enforcer",
                description="Enforce linting rules",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        TypeCheckValidatorAgent(
            AgentConfig(
                name="typecheck_validator",
                description="Validate type checking",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        SecurityScannerAgent(
            AgentConfig(
                name="security_scanner",
                description="Scan for security vulnerabilities",
                category="security",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        DocumentationAuditorAgent(
            AgentConfig(
                name="documentation_auditor",
                description="Audit documentation",
                category="documentation",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        CodeReviewAgent(
            AgentConfig(
                name="code_review",
                description="Automated code review",
                category="code_quality",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        MergeSafetyAgent(
            AgentConfig(
                name="merge_safety",
                description="Ensure merge safety",
                category="deployment",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        ReleaseValidatorAgent(
            AgentConfig(
                name="release_validator",
                description="Validate releases",
                category="deployment",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        BackupAgent(
            AgentConfig(
                name="backup",
                description="Verify backups",
                category="maintenance",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        ScalabilityAnalyzerAgent(
            AgentConfig(
                name="scalability_analyzer",
                description="Analyze scalability",
                category="performance",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        IncidentResponseAgent(
            AgentConfig(
                name="incident_response",
                description="Incident response",
                category="monitoring",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        SLAMonitorAgent(
            AgentConfig(
                name="sla_monitor",
                description="Monitor SLA compliance",
                category="monitoring",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        TestDataGeneratorAgent(
            AgentConfig(
                name="test_data_generator",
                description="Generate test data",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        APITestingAgent(
            AgentConfig(
                name="api_testing",
                description="Run API tests",
                category="testing",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        UITestingAgent(
            AgentConfig(
                name="ui_testing",
                description="Run UI tests",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        LoadTestingAgent(
            AgentConfig(
                name="load_testing",
                description="Run load tests",
                category="performance",
                priority="medium",
            )
        )
    )

    # Specialized Agents (20 new agents)
    orchestrator.register_agent(
        SecurityHeaderValidatorAgent(
            AgentConfig(
                name="security_header_validator",
                description="Validate security headers on all routes",
                category="security",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        EncryptionStrategyAgent(
            AgentConfig(
                name="encryption_strategy",
                description="Suggest encryption for sensitive fields",
                category="security",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        ThirdPartyScriptSafetyAgent(
            AgentConfig(
                name="third_party_script_safety",
                description="Warn about unsafe third-party scripts",
                category="security",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        CodingStyleEnforcerAgent(
            AgentConfig(
                name="coding_style_enforcer",
                description="Enforce coding style",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        LocalizationGapDetectorAgent(
            AgentConfig(
                name="localization_gap_detector",
                description="Detect missing localization keys",
                category="code_quality",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        PerformanceRegressionAgent(
            AgentConfig(
                name="performance_regression",
                description="Check performance regression per commit",
                category="performance",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        SlowEndpointTrackerAgent(
            AgentConfig(
                name="slow_endpoint_tracker",
                description="Track slow endpoints and propose fixes",
                category="performance",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        UXFrictionTrackerAgent(
            AgentConfig(
                name="ux_friction_tracker",
                description="Track UX friction points via telemetry",
                category="monitoring",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        EnvironmentConfigDetectorAgent(
            AgentConfig(
                name="environment_config_detector",
                description="Detect environment misconfigurations",
                category="security",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        UptimeMonitorAgent(
            AgentConfig(
                name="uptime_monitor",
                description="Monitor uptime and daily status",
                category="monitoring",
                priority="high",
            )
        )
    )

    orchestrator.register_agent(
        IncidentMitigationPlannerAgent(
            AgentConfig(
                name="incident_mitigation_planner",
                description="Create mitigation plan for incidents",
                category="monitoring",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        ReleaseNotesGeneratorAgent(
            AgentConfig(
                name="release_notes_generator",
                description="Generate internal release notes",
                category="documentation",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        DependencyUpdaterAgentV2(
            AgentConfig(
                name="dependency_updater_v2",
                description="Update dependencies monthly",
                category="maintenance",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        PRToJiraMapperAgent(
            AgentConfig(
                name="pr_to_jira_mapper",
                description="Map PRs to Jira tickets",
                category="documentation",
                priority="low",
            )
        )
    )

    orchestrator.register_agent(
        TestCoverageReporterAgent(
            AgentConfig(
                name="test_coverage_reporter",
                description="Generate test coverage reports",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        PermissionGapDetectorAgent(
            AgentConfig(
                name="permission_gap_detector",
                description="Detect gaps in permission enforcement",
                category="security",
                priority="critical",
            )
        )
    )

    orchestrator.register_agent(
        WeeklyStabilityScorerAgent(
            AgentConfig(
                name="weekly_stability_scorer",
                description="Produce weekly stability score",
                category="monitoring",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        ArchitectureDriftDetectorAgent(
            AgentConfig(
                name="architecture_drift_detector",
                description="Generate architecture drift warnings",
                category="code_quality",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        BugEnvironmentCreatorAgent(
            AgentConfig(
                name="bug_environment_creator",
                description="Create reproducible bug environments",
                category="testing",
                priority="medium",
            )
        )
    )

    orchestrator.register_agent(
        RefactoringTargetProposerAgent(
            AgentConfig(
                name="refactoring_target_proposer",
                description="Propose refactoring targets each sprint",
                category="code_quality",
                priority="medium",
            )
        )
    )

    logger.info(f"✅ Registered {len(orchestrator.agents)} AI agents")


def run_agent_by_name(
    orchestrator: AgentOrchestrator, agent_name: str, context: Dict[str, Any]
):
    """Run a specific agent by name"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running agent: {agent_name}")
    logger.info(f"{'='*60}\n")

    result = orchestrator.execute_agent(agent_name, context)

    print(f"\n{'='*60}")
    print(f"Agent: {result.agent_name}")
    print(f"Status: {result.status.value}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    print(f"{'='*60}\n")

    if result.findings:
        print("📊 FINDINGS:")
        for finding in result.findings:
            print(f"  • {json.dumps(finding, indent=4, default=str)}")

    if result.metrics:
        print("\n📈 METRICS:")
        print(f"  • {json.dumps(result.metrics, indent=4, default=str)}")

    if result.recommendations:
        print("\n💡 RECOMMENDATIONS:")
        for rec in result.recommendations:
            print(f"  • {rec}")

    if result.errors:
        print("\n❌ ERRORS:")
        for error in result.errors:
            print(f"  • {error}")

    print()


def run_all_agents_by_category(
    orchestrator: AgentOrchestrator, category: str, context: Dict[str, Any]
):
    """Run all agents in a specific category"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running all agents in category: {category}")
    logger.info(f"{'='*60}\n")

    results = orchestrator.execute_all(category=category, context=context)

    successful = sum(1 for r in results.values() if r.status.value == "completed")
    failed = sum(1 for r in results.values() if r.status.value == "failed")

    print(f"\n{'='*60}")
    print(f"Category: {category}")
    print(f"Total: {len(results)} | Successful: {successful} | Failed: {failed}")
    print(f"{'='*60}\n")

    for name, result in results.items():
        print(f"✓ {name}: {result.status.value} ({result.duration_seconds:.2f}s)")

    return results


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="PsychSync AI Agent Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all agents
  python run_agents.py --all

  # Run specific agent
  python run_agents.py --agent code_quality_monitor

  # Run all agents in category
  python run_agents.py --category security

  # Generate report only
  python run_agents.py --report

  # List all agents
  python run_agents.py --list
        """,
    )

    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--agent", help="Run specific agent by name")
    parser.add_argument("--category", help="Run all agents in category")
    parser.add_argument("--all", action="store_true", help="Run all agents")
    parser.add_argument("--report", action="store_true", help="Generate report only")
    parser.add_argument("--list", action="store_true", help="List all agents")
    parser.add_argument("--output", help="Save report to file")

    args = parser.parse_args()

    # Initialize orchestrator
    project_root = Path(args.project_root).resolve()
    orchestrator = AgentOrchestrator(str(project_root))

    # Register all agents
    register_all_agents(orchestrator, str(project_root))

    # List agents
    if args.list:
        print("\n🤖 Available AI Agents:")
        print("=" * 60)

        categories = {}
        for name, agent in orchestrator.agents.items():
            cat = agent.config.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(name)

        for category, agents in sorted(categories.items()):
            print(f"\n{category.upper()} ({len(agents)} agents):")
            for agent_name in sorted(agents):
                print(f"  • {agent_name}")

        print(f"\n{'='*60}")
        print(f"Total: {len(orchestrator.agents)} agents")
        return

    # Generate report
    if args.report:
        report = orchestrator.get_report()
        print(json.dumps(report, indent=2, default=str))

        if args.output:
            orchestrator.save_report(args.output)
            logger.info(f"✅ Report saved to: {args.output}")
        return

    # Execution context
    context = {
        "project_root": str(project_root),
        "timestamp": datetime.now().isoformat(),
    }

    # Run agents based on arguments
    if args.agent:
        run_agent_by_name(orchestrator, args.agent, context)
    elif args.category:
        run_all_agents_by_category(orchestrator, args.category, context)
    elif args.all:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running ALL {len(orchestrator.agents)} agents")
        logger.info(f"{'='*60}\n")

        results = orchestrator.execute_all(context=context)

        successful = sum(1 for r in results.values() if r.status.value == "completed")
        failed = sum(1 for r in results.values() if r.status.value == "failed")

        print(f"\n{'='*60}")
        print(f"EXECUTION COMPLETE")
        print(f"Total: {len(results)} | Successful: {successful} | Failed: {failed}")
        print(f"{'='*60}\n")

        # Save report
        if args.output:
            orchestrator.save_report(args.output)
            logger.info(f"✅ Report saved to: {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
