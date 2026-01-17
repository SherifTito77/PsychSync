"""
AI Agents Package

Automation agents for security, performance, and development workflows.

Active Agents (20 total):
1. Security Headers Validator - Validates OWASP security headers
2. Encryption Strategy Advisor - Recommends field encryption
3. Unsafe Script Detector - Scans for vulnerable dependencies
4. Coding Style Enforcer - Enforces code style standards
5. Performance Regression Detector - Detects performance issues
6. Localization Key Detector - Finds missing i18n keys
7. Slow Endpoint Tracker - Tracks slow API endpoints
8. Release Notes Generator - Auto-generates release notes
9. UX Telemetry Tracker - Tracks user experience metrics
10. Environment Config Detector - Validates environment configs
11. Incident Mitigation Planner - Creates incident response plans
12. Dependency Updater - Auto-updates dependencies
13. PR-Jira Mapper - Maps PRs to Jira tickets
14. Test Coverage Reporter - Generates test coverage reports
15. Permission Gap Detector - Detects missing permission checks
16. Uptime Monitor - Monitors system uptime
17. Stability Score Calculator - Calculates stability metrics
18. Architecture Drift Detector - Detects architectural drift
19. Bug Environment Creator - Creates reproducible bug environments
20. Refactoring Target Proposer - Suggests refactoring opportunities
"""

# Security agents
from app.services.ai_agents.security_headers_agent import security_headers_agent
from app.services.ai_agents.encryption_strategy_agent import encryption_strategy_agent
from app.services.ai_agents.unsafe_script_agent import unsafe_script_agent

# Development workflow agents
from app.services.ai_agents.development_agents import (
    coding_style_agent,
    performance_regression_agent,
    localization_agent,
    slow_endpoint_agent,
    release_notes_agent,
    permission_gap_agent,
    uptime_monitor_agent,
    stability_score_agent,
)

# Operations agents
from app.services.ai_agents.operations_agents import (
    ux_telemetry_agent,
    environment_config_agent,
    incident_mitigation_agent,
    dependency_updater_agent,
    pr_jira_mapper_agent,
    test_coverage_agent,
    architecture_drift_agent,
    bug_environment_agent,
    refactoring_target_agent,
)

__all__ = [
    # Security
    "security_headers_agent",
    "encryption_strategy_agent",
    "unsafe_script_agent",
    # Development
    "coding_style_agent",
    "performance_regression_agent",
    "localization_agent",
    "slow_endpoint_agent",
    "release_notes_agent",
    "permission_gap_agent",
    "uptime_monitor_agent",
    "stability_score_agent",
    # Operations
    "ux_telemetry_agent",
    "environment_config_agent",
    "incident_mitigation_agent",
    "dependency_updater_agent",
    "pr_jira_mapper_agent",
    "test_coverage_agent",
    "architecture_drift_agent",
    "bug_environment_agent",
    "refactoring_target_agent",
]
