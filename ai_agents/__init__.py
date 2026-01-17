"""
AI Agents for PsychSync
Autonomous agents for code quality, testing, security, and monitoring
"""

from .agent_framework import (
    BaseAgent,
    AgentConfig,
    AgentResult,
    AgentOrchestrator,
    AgentStatus,
    Priority,
    run_command,
    find_files,
    read_file,
    analyze_code_complexity
)

# Code Quality Agents
from .code_quality_agents import (
    CodeQualityMonitorAgent,
    BugSummarizerAgent,
    EngineeringPerformanceAgent,
    PRQualityScorerAgent,
    CodeStandardizerAgent,
    APIDriftDetectorAgent,
    LogAnomalyScannerAgent,
    AutoTestGeneratorAgent,
    DocumentationCompletenessAgent,
    UnusedCodeDetectorAgent,
    ModuleDecomposerAgent,
    JSONSchemaValidatorAgent,
    DuplicateIssueDetectorAgent
)

# Testing & Performance Agents
from .testing_performance_agents import (
    CommentImproverAgent,
    ErrorCodeGeneratorAgent,
    SQLInjectionAuditorAgent,
    QueryOptimizerAgent,
    BuildFailureAnalyzerAgent,
    CachingConfigOptimizerAgent,
    BreakingChangeDetectorAgent,
    SpaghettiCodeRefactorAgent,
    DeprecatedLibraryDetectorAgent,
    DebugCodeRemoverAgent,
    APIMockGeneratorAgent,
    PaginationValidatorAgent,
    AccessibilityAuditorAgent,
    ReRenderOptimizerAgent,
    BundleOptimizerAgent,
    MemoryLeakDetectorAgent,
    UnusedCSSDetectorAgent
)

# Analytics & Workflow Agents
from .analytics_workflow_agents import (
    HealthMonitorAgent,
    ErrorRateMonitorAgent,
    PerformanceMetricsAgent,
    UserBehaviorAnalyticsAgent,
    UsageStatisticsAgent,
    CIPipelineMonitorAgent,
    TestCoverageAgent,
    DeploymentSafetyAgent,
    DependencyUpdaterAgent,
    LintEnforcerAgent,
    TypeCheckValidatorAgent,
    SecurityScannerAgent,
    DocumentationAuditorAgent,
    CodeReviewAgent,
    MergeSafetyAgent,
    ReleaseValidatorAgent,
    BackupAgent,
    ScalabilityAnalyzerAgent,
    IncidentResponseAgent,
    SLAMonitorAgent,
    TestDataGeneratorAgent,
    APITestingAgent,
    UITestingAgent,
    LoadTestingAgent
)

# Specialized Agents
from .specialized_agents import (
    SecurityHeaderValidatorAgent,
    EncryptionStrategyAgent,
    ThirdPartyScriptSafetyAgent,
    CodingStyleEnforcerAgent,
    LocalizationGapDetectorAgent,
    PerformanceRegressionAgent,
    SlowEndpointTrackerAgent,
    UXFrictionTrackerAgent,
    EnvironmentConfigDetectorAgent,
    UptimeMonitorAgent,
    IncidentMitigationPlannerAgent,
    ReleaseNotesGeneratorAgent,
    DependencyUpdaterAgent as DependencyUpdaterAgentV2,
    PRToJiraMapperAgent,
    TestCoverageReporterAgent,
    PermissionGapDetectorAgent,
    WeeklyStabilityScorerAgent,
    ArchitectureDriftDetectorAgent,
    BugEnvironmentCreatorAgent,
    RefactoringTargetProposerAgent
)

__all__ = [
    # Framework
    'BaseAgent',
    'AgentConfig',
    'AgentResult',
    'AgentOrchestrator',
    'AgentStatus',
    'Priority',
    'run_command',
    'find_files',
    'read_file',
    'analyze_code_complexity',

    # Code Quality Agents (13)
    'CodeQualityMonitorAgent',
    'BugSummarizerAgent',
    'EngineeringPerformanceAgent',
    'PRQualityScorerAgent',
    'CodeStandardizerAgent',
    'APIDriftDetectorAgent',
    'LogAnomalyScannerAgent',
    'AutoTestGeneratorAgent',
    'DocumentationCompletenessAgent',
    'UnusedCodeDetectorAgent',
    'ModuleDecomposerAgent',
    'JSONSchemaValidatorAgent',
    'DuplicateIssueDetectorAgent',

    # Testing & Performance Agents (17)
    'CommentImproverAgent',
    'ErrorCodeGeneratorAgent',
    'SQLInjectionAuditorAgent',
    'QueryOptimizerAgent',
    'BuildFailureAnalyzerAgent',
    'CachingConfigOptimizerAgent',
    'BreakingChangeDetectorAgent',
    'SpaghettiCodeRefactorAgent',
    'DeprecatedLibraryDetectorAgent',
    'DebugCodeRemoverAgent',
    'APIMockGeneratorAgent',
    'PaginationValidatorAgent',
    'AccessibilityAuditorAgent',
    'ReRenderOptimizerAgent',
    'BundleOptimizerAgent',
    'MemoryLeakDetectorAgent',
    'UnusedCSSDetectorAgent',

    # Analytics & Workflow Agents (24)
    'HealthMonitorAgent',
    'ErrorRateMonitorAgent',
    'PerformanceMetricsAgent',
    'UserBehaviorAnalyticsAgent',
    'UsageStatisticsAgent',
    'CIPipelineMonitorAgent',
    'TestCoverageAgent',
    'DeploymentSafetyAgent',
    'DependencyUpdaterAgent',
    'LintEnforcerAgent',
    'TypeCheckValidatorAgent',
    'SecurityScannerAgent',
    'DocumentationAuditorAgent',
    'CodeReviewAgent',
    'MergeSafetyAgent',
    'ReleaseValidatorAgent',
    'BackupAgent',
    'ScalabilityAnalyzerAgent',
    'IncidentResponseAgent',
    'SLAMonitorAgent',
    'TestDataGeneratorAgent',
    'APITestingAgent',
    'UITestingAgent',
    'LoadTestingAgent',

    # Specialized Agents (20)
    'SecurityHeaderValidatorAgent',
    'EncryptionStrategyAgent',
    'ThirdPartyScriptSafetyAgent',
    'CodingStyleEnforcerAgent',
    'LocalizationGapDetectorAgent',
    'PerformanceRegressionAgent',
    'SlowEndpointTrackerAgent',
    'UXFrictionTrackerAgent',
    'EnvironmentConfigDetectorAgent',
    'UptimeMonitorAgent',
    'IncidentMitigationPlannerAgent',
    'ReleaseNotesGeneratorAgent',
    'DependencyUpdaterAgentV2',
    'PRToJiraMapperAgent',
    'TestCoverageReporterAgent',
    'PermissionGapDetectorAgent',
    'WeeklyStabilityScorerAgent',
    'ArchitectureDriftDetectorAgent',
    'BugEnvironmentCreatorAgent',
    'RefactoringTargetProposerAgent'
]

# Version info
__version__ = "2.0.0"
__author__ = "PsychSync AI Team"
TOTAL_AGENTS = 74
