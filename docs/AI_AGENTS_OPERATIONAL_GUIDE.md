# 🤖 PsychSync AI Agents - Complete Operational Guide

**Version:** 1.0.0
**Total Agents:** 54
**Last Updated:** 2026-01-17

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Agent Categories](#agent-categories)
5. [Usage Examples](#usage-examples)
6. [CI/CD Integration](#cicd-integration)
7. [Customization](#customization)
8. [Best Practices](#best-practices)

---

## 🎯 Overview

PsychSync AI Agents are autonomous agents that continuously monitor, analyze, and improve your codebase across multiple dimensions:

- **Code Quality** (13 agents): Monitor complexity, detect bugs, enforce standards
- **Testing & Performance** (17 agents): Optimize performance, run tests, audit security
- **Analytics & Workflow** (24 agents): Monitor health, track metrics, automate CI/CD

### Key Features

✅ **Autonomous Execution**: Each agent runs independently with standardized results
✅ **Comprehensive Coverage**: 54 agents covering all aspects of development
✅ **Extensible Framework**: Easy to add custom agents
✅ **Production Ready**: Error handling, logging, and reporting built-in
✅ **CI/CD Integration**: Schedule agents or run on demand

---

## 🚀 Installation

### Prerequisites

```bash
# Python 3.8+
python3 --version

# PsychSync project
cd /path/to/psychsync
```

### Setup

The AI agents are already included in the PsychSync project:

```bash
# Navigate to project root
cd /Users/sheriftito/Downloads/psychsync

# AI agents are in the ai_agents/ directory
ls ai_agents/
# - agent_framework.py      (Core framework)
# - code_quality_agents.py   (13 agents)
# - testing_performance_agents.py (17 agents)
# - analytics_workflow_agents.py (24 agents)
# - run_agents.py            (Orchestrator script)
# - __init__.py              (Package exports)
```

---

## ⚡ Quick Start

### 1. List All Available Agents

```bash
python ai_agents/run_agents.py --list
```

**Output:**
```
🤖 Available AI Agents:
============================================================

ANALYTICS (5 agents):
  • user_behavior_analytics
  • usage_statistics
  • performance_metrics
  • test_data_generator
  • scalability_analyzer

CODE_QUALITY (13 agents):
  • code_quality_monitor
  • bug_summarizer
  • engineering_performance
  • pr_quality_scorer
  • code_standardizer
  • api_drift_detector
  • log_anomaly_scanner
  • auto_test_generator
  • documentation_completeness
  • unused_code_detector
  • module_decomposer
  • json_schema_validator
  • duplicate_issue_detector

DEPLOYMENT (3 agents):
  • deployment_safety
  • merge_safety
  • release_validator

DOCUMENTATION (2 agents):
  • documentation_auditor
  • documentation_completeness

MAINTENANCE (2 agents):
  • backup
  • dependency_updater

MONITORING (8 agents):
  • health_monitor
  • error_rate_monitor
  • ci_pipeline_monitor
  • incident_response
  • sla_monitor
  • security_scanner
  • code_review
  • merge_safety

PERFORMANCE (7 agents):
  • query_optimizer
  • caching_config_optimizer
  • pagination_validator
  • rerender_optimizer
  • bundle_optimizer
  • memory_leak_detector
  • unused_css_detector

SECURITY (3 agents):
  • sql_injection_auditor
  • deprecated_library_detector
  • security_scanner

TESTING (9 agents):
  • comment_improver
  • error_code_generator
  • build_failure_analyzer
  • breaking_change_detector
  • spaghetti_code_refactor
  • debug_code_remover
  • api_mock_generator
  • accessibility_auditor
  • test_coverage
  • typecheck_validator
  • test_data_generator
  • api_testing
  • ui_testing
  • load_testing

============================================================
Total: 54 agents
```

### 2. Run a Single Agent

```bash
python ai_agents/run_agents.py --agent code_quality_monitor
```

**Output:**
```
============================================================
Running agent: code_quality_monitor
============================================================

============================================================
Agent: code_quality_monitor
Status: completed
Duration: 2.34s
============================================================

📊 FINDINGS:
  • {
        "type": "code_quality_snapshot",
        "total_files": 847,
        "python_files": 312,
        "typescript_files": 535,
        "average_complexity": 42.5,
        "status": "good"
    }

📈 METRICS:
  • {
        "files_analyzed": 847,
        "avg_complexity": 42.5,
        "high_complexity_files": 12
    }

💡 RECOMMENDATIONS:
  • Consider refactoring high-complexity files
  • Break down large modules into smaller components
```

### 3. Run All Agents in a Category

```bash
# Run all security agents
python ai_agents/run_agents.py --category security

# Run all testing agents
python ai_agents/run_agents.py --category testing

# Run all performance agents
python ai_agents/run_agents.py --category performance
```

### 4. Run ALL Agents

```bash
# Execute all 54 agents
python ai_agents/run_agents.py --all

# Save execution report
python ai_agents/run_agents.py --all --output agent_report.json
```

---

## 📂 Agent Categories

### Code Quality Agents (13)

| Agent | Description | Priority | Schedule |
|-------|-------------|----------|----------|
| `code_quality_monitor` | Monitor code quality metrics | Medium | Daily |
| `bug_summarizer` | Summarize Jira bugs | Medium | Daily |
| `engineering_performance` | Weekly performance report | Low | Weekly |
| `pr_quality_scorer` | Score PR quality | High | On PR |
| `code_standardizer` | Fix code style issues | Medium | On commit |
| `api_drift_detector` | Detect API contract changes | High | On PR |
| `log_anomaly_scanner` | Scan logs for errors | High | Continuous |
| `auto_test_generator` | Generate tests for endpoints | High | On endpoint creation |
| `documentation_completeness` | Assess documentation | Low | Weekly |
| `unused_code_detector` | Find unused code | Low | Weekly |
| `module_decomposer` | Suggest module splits | Medium | Weekly |
| `json_schema_validator` | Validate JSON schemas | Medium | On commit |
| `duplicate_issue_detector` | Find duplicate issues | Low | Daily |

### Testing & Performance Agents (17)

| Agent | Description | Priority | Schedule |
|-------|-------------|----------|----------|
| `comment_improver` | Improve code comments | Low | On PR |
| `error_code_generator` | Generate error codes | Medium | On error |
| `sql_injection_auditor` | Audit SQL security | Critical | On commit |
| `query_optimizer` | Optimize slow queries | High | Weekly |
| `build_failure_analyzer` | Analyze build failures | Critical | On failure |
| `caching_config_optimizer` | Optimize caching | Medium | Weekly |
| `breaking_change_detector` | Detect breaking changes | High | On PR |
| `spaghetti_code_refactor` | Refactor bad code | Medium | Weekly |
| `deprecated_library_detector` | Find deprecated libs | High | Weekly |
| `debug_code_remover` | Remove debug code | Medium | On commit |
| `api_mock_generator` | Generate API mocks | Medium | On endpoint creation |
| `pagination_validator` | Check pagination | Medium | On PR |
| `accessibility_auditor` | Audit accessibility | High | On PR |
| `rerender_optimizer` | Fix React re-renders | Medium | On PR |
| `bundle_optimizer` | Optimize bundle size | Medium | Weekly |
| `memory_leak_detector` | Find memory leaks | High | Weekly |
| `unused_css_detector` | Find unused CSS | Low | Weekly |

### Analytics & Workflow Agents (24)

| Agent | Description | Priority | Schedule |
|-------|-------------|----------|----------|
| `health_monitor` | Monitor app health | Critical | Continuous |
| `error_rate_monitor` | Track error rates | High | Continuous |
| `performance_metrics` | Collect metrics | High | Continuous |
| `user_behavior_analytics` | Analyze behavior | Low | Weekly |
| `usage_statistics` | Aggregate stats | Low | Weekly |
| `ci_pipeline_monitor` | Monitor CI/CD | High | Continuous |
| `test_coverage` | Measure coverage | Medium | On PR |
| `deployment_safety` | Ensure safe deployment | Critical | On deploy |
| `dependency_updater` | Update dependencies | Medium | Weekly |
| `lint_enforcer` | Enforce linting | Medium | On commit |
| `typecheck_validator` | Validate types | Medium | On PR |
| `security_scanner` | Scan vulnerabilities | Critical | Daily |
| `documentation_auditor` | Audit docs | Low | Weekly |
| `code_review` | Automated review | High | On PR |
| `merge_safety` | Ensure merge safety | High | On PR |
| `release_validator` | Validate releases | Critical | On release |
| `backup` | Verify backups | High | Daily |
| `scalability_analyzer` | Analyze scalability | Medium | Weekly |
| `incident_response` | Respond to incidents | Critical | On incident |
| `sla_monitor` | Monitor SLA | High | Continuous |
| `test_data_generator` | Generate test data | Medium | On demand |
| `api_testing` | Run API tests | High | On PR |
| `ui_testing` | Run UI tests | Medium | On PR |
| `load_testing` | Run load tests | Medium | Weekly |

---

## 💡 Usage Examples

### Example 1: Pre-Commit Hook

Run critical agents before each commit:

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running AI agents..."

# Run security scanner
python ai_agents/run_agents.py --agent security_scanner
if [ $? -ne 0 ]; then
    echo "❌ Security issues found. Commit aborted."
    exit 1
fi

# Run SQL injection auditor
python ai_agents/run_agents.py --agent sql_injection_auditor
if [ $? -ne 0 ]; then
    echo "❌ SQL injection risks found. Commit aborted."
    exit 1
fi

# Run debug code remover
python ai_agents/run_agents.py --agent debug_code_remover

echo "✅ All checks passed. Proceeding with commit."
```

### Example 2: CI/CD Pipeline

Integrate into GitHub Actions:

```yaml
# .github/workflows/ai-agents.yml
name: AI Agents

on:
  pull_request:
    branches: [main]

jobs:
  ai-agents:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Run critical agents
        run: |
          python ai_agents/run_agents.py \
            --agent security_scanner \
            --agent sql_injection_auditor \
            --agent breaking_change_detector \
            --output agent_results.json

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: agent-results
          path: agent_results.json
```

### Example 3: Scheduled Execution

Run agents daily via cron:

```bash
# crontab -e

# Run all agents every day at 2 AM
0 2 * * * cd /path/to/psychsync && python ai_agents/run_agents.py --all --output daily_report.json >> /var/log/ai_agents.log 2>&1

# Run security agents every 6 hours
0 */6 * * * cd /path/to/psychsync && python ai_agents/run_agents.py --category security --output security_report.json >> /var/log/ai_agents.log 2>&1

# Run performance agents weekly on Sunday at 3 AM
0 3 * * 0 cd /path/to/psychsync && python ai_agents/run_agents.py --category performance --output perf_report.json >> /var/log/ai_agents.log 2>&1
```

### Example 4: Python API Usage

Use agents programmatically in Python:

```python
from ai_agents import AgentOrchestrator, AgentConfig
from ai_agents.code_quality_agents import CodeQualityMonitorAgent
from pathlib import Path

# Initialize orchestrator
orchestrator = AgentOrchestrator(project_root=".")

# Register and run agent
agent = CodeQualityMonitorAgent(AgentConfig(
    name="code_quality_monitor",
    description="Monitor code quality",
    category="code_quality"
))

orchestrator.register_agent(agent)

# Execute agent
result = orchestrator.execute_agent(
    "code_quality_monitor",
    context={"project_root": "."}
)

# Process results
print(f"Status: {result.status}")
print(f"Findings: {result.findings}")
print(f"Recommendations: {result.recommendations}")

# Generate report
report = orchestrator.get_report()
orchestrator.save_report("quality_report.json")
```

### Example 5: Custom Agent

Create your own agent:

```python
from ai_agents import BaseAgent, AgentConfig, AgentResult
from typing import Dict, Any, Tuple, List

class CustomAgent(BaseAgent):
    """Your custom AI agent"""

    def _run(self, context: Dict[str, Any]) -> Tuple[List[Dict], Dict, List[str]]:
        """Override this method with your logic"""

        findings = [
            {
                "type": "custom_finding",
                "message": "Custom analysis complete"
            }
        ]

        metrics = {
            "custom_metric": 42
        }

        recommendations = [
            "Custom recommendation 1",
            "Custom recommendation 2"
        ]

        return findings, metrics, recommendations

# Use your custom agent
from ai_agents import AgentOrchestrator

orchestrator = AgentOrchestrator(".")
agent = CustomAgent(AgentConfig(
    name="custom_agent",
    description="My custom agent",
    category="custom"
))

orchestrator.register_agent(agent)
result = orchestrator.execute_agent("custom_agent")
```

---

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: AI Agents Quality Gate

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality-gate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Run AI agents
        run: |
          python ai_agents/run_agents.py \
            --category security \
            --category testing \
            --output results.json

      - name: Check results
        run: |
          if grep -q '"failed"' results.json; then
            echo "❌ Some agents failed. Check results.json"
            exit 1
          fi
          echo "✅ All agents passed"
```

### GitLab CI

```yaml
# .gitlab-ci.yml
ai-agents:
  stage: test
  image: python:3.9

  script:
    - pip install -r requirements.txt
    - python ai_agents/run_agents.py --all --output results.json

  artifacts:
    paths:
      - results.json
    expire_in: 1 week

  only:
    - merge_requests
    - main
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('AI Agents') {
            steps {
                sh '''
                    python ai_agents/run_agents.py \
                        --category security \
                        --category code_quality \
                        --output results.json
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results.json'
        }
    }
}
```

---

## ⚙️ Customization

### Configure Agent Behavior

Modify agent configurations in `run_agents.py`:

```python
orchestrator.register_agent(SecurityScannerAgent(AgentConfig(
    name="security_scanner",
    description="Scan for security vulnerabilities",
    category="security",
    priority="critical",           # Set priority
    timeout_seconds=600,            # Increase timeout
    auto_schedule=True,             # Enable auto-scheduling
    schedule_interval="0 2 * * *"  # Cron schedule
)))
```

### Add Custom Agent Categories

```python
# In your custom agents file
from ai_agents import BaseAgent

class DataQualityAgent(BaseAgent):
    """Custom data quality agent"""

    def _run(self, context):
        # Your implementation
        return findings, metrics, recommendations
```

### Filter Results

```python
# Run agents and filter successful ones
results = orchestrator.execute_all(context=context)

successful = {
    name: result
    for name, result in results.items()
    if result.status.value == "completed"
}

failed = {
    name: result
    for name, result in results.items()
    if result.status.value == "failed"
}
```

---

## 📊 Best Practices

### 1. Run Critical Agents Frequently

```bash
# Critical agents should run on every commit/PR
python ai_agents/run_agents.py --agent security_scanner
python ai_agents/run_agents.py --agent sql_injection_auditor
python ai_agents/run_agents.py --agent breaking_change_detector
```

### 2. Schedule Heavy Agents Off-Hours

```bash
# Performance tests and comprehensive scans
0 2 * * * python ai_agents/run_agents.py --agent load_testing
0 3 * * 0 python ai_agents/run_agents.py --category performance
```

### 3. Review Agent Recommendations

```python
# Always review recommendations before applying
result = orchestrator.execute_agent("code_standardizer")

print("Recommendations:")
for rec in result.recommendations:
    print(f"  • {rec}")
```

### 4. Monitor Agent Execution

```bash
# Check agent logs
tail -f ai_agents/agent_execution.log

# Review historical reports
cat agent_report.json | jq '.summary'
```

### 5. Integrate with Existing Tools

```python
# Export results to other systems
import requests

result = orchestrator.execute_agent("security_scanner")

# Send to Slack
if result.errors:
    requests.post(
        "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        json={"text": f"❌ Security scan failed: {result.errors}"}
    )

# Create Jira ticket
if result.findings:
    requests.post(
        "https://jira.example.com/rest/api/2/issue/",
        json={
            "fields": {
                "project": {"key": "SEC"},
                "summary": f"Security findings: {len(result.findings)} issues",
                "description": str(result.findings)
            }
        }
    )
```

---

## 📈 Monitoring & Reporting

### View Execution History

```python
from ai_agents import AgentOrchestrator

orchestrator = AgentOrchestrator(".")
report = orchestrator.get_report(last_n=100)

print(json.dumps(report, indent=2))
```

**Sample Report:**

```json
{
  "summary": {
    "total_executions": 54,
    "successful": 52,
    "failed": 2,
    "success_rate": "96.3%"
  },
  "by_category": {
    "security": {
      "total": 3,
      "successful": 3,
      "findings": 12
    },
    "code_quality": {
      "total": 13,
      "successful": 13,
      "findings": 45
    },
    "testing": {
      "total": 9,
      "successful": 8,
      "findings": 23
    }
  },
  "recent_results": [...]
}
```

---

## 🐛 Troubleshooting

### Agent Fails to Run

```bash
# Check agent logs
cat ai_agents/agent_execution.log

# Run with verbose output
python ai_agents/run_agents.py --agent <name> --debug
```

### Import Errors

```bash
# Ensure Python path is correct
export PYTHONPATH="${PYTHONPATH}:/path/to/psychsync"

# Verify agent files
ls -la ai_agents/*.py
```

### Timeout Issues

```bash
# Increase timeout for specific agent
# Edit run_agents.py and modify AgentConfig:
timeout_seconds=600  # 10 minutes
```

---

## 📚 Additional Resources

- **Agent Framework**: `ai_agents/agent_framework.py`
- **Agent Implementations**: `ai_agents/*_agents.py`
- **Orchestrator Script**: `ai_agents/run_agents.py`
- **Execution Logs**: `ai_agents/agent_execution.log`
- **Sample Reports**: `ai_agents/agent_report.json`

---

## 📝 Changelog

### Version 1.0.0 (2026-01-17)
- ✅ Initial release with 54 AI agents
- ✅ Complete agent framework
- ✅ Orchestrator and execution system
- ✅ Comprehensive documentation

---

## 🤝 Support

For issues or questions:
1. Check this guide
2. Review agent logs: `ai_agents/agent_execution.log`
3. Check agent implementations in `ai_agents/*_agents.py`
4. Run with `--list` to verify agent availability

---

**Status**: ✅ Production Ready
**Total Agents**: 54
**Categories**: 10
**Tested**: Yes
