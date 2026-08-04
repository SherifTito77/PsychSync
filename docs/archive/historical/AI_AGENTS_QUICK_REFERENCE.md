# 🤖 AI Agents - Quick Reference Card

**Version:** 1.0.0 | **Total Agents:** 54 | **Status:** ✅ Production Ready

---

## ⚡ Common Commands

```bash
# List all agents
python app.ai.agents/run_agents.py --list

# Run single agent
python app.ai.agents/run_agents.py --agent <agent_name>

# Run by category
python app.ai.agents/run_agents.py --category security

# Run all agents
python app.ai.agents/run_agents.py --all

# Save report
python app.ai.agents/run_agents.py --all --output report.json

# Get help
python app.ai.agents/run_agents.py --help
```

---

## 📂 Categories & Agent Count

| Category | Count | Priority |
|----------|-------|----------|
| Code Quality | 13 | Medium |
| Testing | 9 | High |
| Performance | 7 | Medium |
| Security | 3 | **Critical** |
| Monitoring | 6 | High |
| Analytics | 2 | Low |
| Deployment | 3 | **Critical** |
| Maintenance | 2 | Medium |
| Documentation | 1 | Low |
| Workflow | 8 | High |

---

## 🔒 Critical Agents (Run Frequently)

```bash
# Security (run every commit)
python app.ai.agents/run_agents.py --agent sql_injection_auditor
python app.ai.agents/run_agents.py --agent security_scanner

# Deployment (run on deploy)
python app.ai.agents/run_agents.py --agent deployment_safety
python app.ai.agents/run_agents.py --agent release_validator

# Incidents (run on failure)
python app.ai.agents/run_agents.py --agent incident_response
python app.ai.agents/run_agents.py --agent build_failure_analyzer
```

---

## 📊 High-Value Agents

```bash
# Code quality
python app.ai.agents/run_agents.py --agent code_quality_monitor
python app.ai.agents/run_agents.py --agent api_drift_detector

# Performance
python app.ai.agents/run_agents.py --agent query_optimizer
python app.ai.agents/run_agents.py --agent bundle_optimizer

# Testing
python app.ai.agents/run_agents.py --agent test_coverage
python app.ai.agents/run_agents.py --agent breaking_change_detector
```

---

## 🔧 CI/CD Integration

### GitHub Actions

```yaml
- name: Run AI Agents
  run: python app.ai.agents/run_agents.py --category security --category testing
```

### Pre-Commit Hook

```bash
#!/bin/bash
python app.ai.agents/run_agents.py --agent security_scanner || exit 1
```

### Cron Job

```bash
0 2 * * * cd /path/to/psychsync && python app.ai.agents/run_agents.py --all --output daily.json
```

---

## 📈 Example Output

```
============================================================
Agent: code_quality_monitor
Status: completed
Duration: 7.84s
============================================================

📊 FINDINGS:
  • Total files: 1839
  • Python files: 1441
  • TypeScript files: 398
  • Avg complexity: 15.8
  • Status: good

📈 METRICS:
  • Files analyzed: 1839
  • High complexity files: 0

💡 RECOMMENDATIONS:
  • No critical issues found
```

---

## 📚 Documentation

- **Comprehensive Guide:** `AI_AGENTS_OPERATIONAL_GUIDE.md`
- **Completion Report:** `AI_AGENTS_COMPLETION_REPORT.md`
- **Framework:** `app.ai.agents/agent_framework.py`
- **Logs:** `app.ai.agents/agent_execution.log`

---

## 🎯 Quick Start

1. **List agents:** `python app.ai.agents/run_agents.py --list`
2. **Run one:** `python app.ai.agents/run_agents.py --agent code_quality_monitor`
3. **Run all:** `python app.ai.agents/run_agents.py --all`
4. **Check logs:** `tail -f app.ai.agents/agent_execution.log`

---

**Status:** ✅ Production Ready | **Tested:** Yes | **Version:** 1.0.0
