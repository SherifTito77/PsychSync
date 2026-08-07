# 🤖 Autonomous Agents - PsychSync DevOps Automation

**Suite of autonomous AI agents for automated development operations**

---

## 🎯 Overview

This directory contains 5 autonomous agents that automate various aspects of the development workflow, from code quality to dependency management. Each agent operates independently and can be scheduled or triggered by events.

---

## 📦 Available Agents

### 1. 🧹 Code Quality Scanner
**File:** `code_quality_scanner.py`

**Purpose:** Scans code daily for bugs, code smells, unused imports, and dependency risks. Automatically creates PRs with fixes.

**Features:**
- Runs pylint, flake8, isort, bandit, safety
- Detects unused imports automatically
- Auto-fixes style issues with autopep8 and isort
- Creates PRs with automated fixes
- Generates detailed quality reports

**Usage:**
```bash
# Manual scan
python agents/code_quality_scanner.py

# Schedule with cron (daily at 2 AM)
0 2 * * * cd /path/to/psychsync && python agents/code_quality_scanner.py >> agents/logs/scanner.log 2>&1
```

**Environment Variables:**
- `GITHUB_TOKEN`: GitHub API token
- `GITHUB_REPOSITORY`: Repository name (default: psychsync/psychsync)

---

### 2. 🧪 PR Coverage Gatekeeper
**File:** `pr_coverage_tester.py`

**Purpose:** Tests each incoming PR and rejects if test coverage < 90%. Provides detailed coverage reports.

**Features:**
- Analyzes PR changes
- Runs pytest with coverage reporting
- Checks file-level coverage thresholds
- Posts detailed coverage reports as PR comments
- Fails status checks if coverage too low
- Identifies files needing tests

**Usage:**
```bash
# Test a specific PR
python agents/pr_coverage_tester.py 123

# Watch mode (continuous)
python agents/pr_coverage_tester.py
```

**Environment Variables:**
- `GITHUB_TOKEN`: GitHub API token
- `MIN_COVERAGE`: Minimum overall coverage (default: 90.0)
- `MIN_FILE_COVERAGE`: Minimum file coverage (default: 80.0)
- `TEST_COMMAND`: Test command to run

**Integration with GitHub:**
```yaml
# .github/workflows/coverage-check.yml
name: Coverage Check
on: [pull_request]
jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test coverage
        run: python agents/pr_coverage_tester.py ${{ github.event.number }}
```

---

### 3. 🔍 Crash Log Analyzer
**File:** `crash_log_analyzer.py`

**Purpose:** Reads crash logs and automatically locates code responsible. Uses stack trace analysis and AI-powered code mapping.

**Features:**
- Parses stack traces from various sources
- Maps stack frames to source code
- Identifies problematic lines
- Determines crash severity
- Suggests fixes based on error type
- Creates GitHub issues with detailed analysis
- Finds related historical issues

**Usage:**
```bash
# Analyze a crash log file
python agents/crash_log_analyzer.py analyze /path/to/crash.log

# Watch log files continuously
python agents/crash_log_analyzer.py watch /var/log/app/errors.log

# Watch for Sentry errors (if configured)
python agents/crash_log_analyzer.py watch
```

**Integration Points:**
- Sentry webhooks
- Application error logs
- CloudWatch logs
- K8s pod crash logs

---

### 4. 📚 Documentation Synchronizer
**File:** `doc_syncer.py`

**Purpose:** Automatically syncs documentation with code changes. Keeps API docs, README, and other docs up-to-date.

**Features:**
- Scans for code changes
- Extracts API endpoints, models, functions
- Detects outdated documentation
- Updates API specifications
- Syncs database schema docs
- Creates PRs for documentation updates
- Supports multiple doc formats

**Usage:**
```bash
# Single sync
python agents/doc_syncer.py scan

# Continuous sync (runs every 60 minutes)
python agents/doc_syncer.py continuous 60
```

**What It Updates:**
- OpenAPI specification (`docs/api/OPENAPI_SPECIFICATION.yaml`)
- Database schema docs (`docs/DATABASE_SCHEMA.md`)
- README.md
- CHANGELOG.md
- Architecture docs

---

### 5. 📦 Dependency Updater
**File:** `dependency_updater.py`

**Purpose:** Safely updates dependencies with full regression testing. Creates PRs only after all tests pass.

**Features:**
- Checks for outdated dependencies (Python & Node)
- Reviews changelogs for breaking changes
- Updates one dependency at a time
- Runs full test suite before creating PR
- Runs smoke tests for basic validation
- Automatically rolls back if issues detected
- Blocklist support for risky packages

**Usage:**
```bash
# Check for updates
python agents/dependency_updater.py check

# Apply safe updates
python agents/dependency_updater.py update

# Run on schedule (cron)
python agents/dependency_updater.py schedule
```

**Safety Features:**
- ✅ Max 3 updates per run (configurable)
- ✅ Blocklist support
- ✅ Major version bump detection
- ✅ Full test suite required
- ✅ Smoke test validation
- ✅ Auto-rollback on failure

**Environment Variables:**
- `MAX_UPDATES`: Maximum updates per run (default: 3)
- `BLOCKLIST`: Comma-separated list of packages to skip
- `REQUIRE_TESTS`: Require tests to pass (default: true)

---

## 🚀 Quick Start

### Installation

```bash
# Install required packages
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install additional agent dependencies
pip install pylint flake8 isort bandit safety autopep8 pip-outdated
pip install github3.py GitPython

# Install frontend dependencies (for doc_syncer)
cd frontend && npm install && cd ..
```

### Configuration

All agents require GitHub access:

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPOSITORY="psychsync/psychsync"
```

### Running Agents

```bash
# Make scripts executable
chmod +x agents/*.py

# Run any agent
python agents/code_quality_scanner.py
```

---

## 📅 Scheduling with Cron

### Daily Quality Scan
```bash
# Run every day at 2 AM
0 2 * * * cd /path/to/psychsync && python agents/code_quality_scanner.py >> agents/logs/scanner.log 2>&1
```

### Weekly Dependency Update
```bash
# Run every Sunday at 3 AM
0 3 * * 0 cd /path/to/psychsync && python agents/dependency_updater.py schedule >> agents/logs/updater.log 2>&1
```

### Hourly Documentation Sync
```bash
# Run every hour
0 * * * * cd /path/to/psychsync && python agents/doc_syncer.py scan >> agents/logs/docsyncer.log 2>&1
```

### Continuous Crash Log Monitoring
```bash
# Run continuously
nohup python agents/crash_log_analyzer.py watch /var/log/app/errors.log >> agents/logs/crash_analyzer.log 2>&1 &
```

---

## 🔧 Integration with CI/CD

### GitHub Actions Workflow

```yaml
name: Agent Workflows

on:
  schedule:
    # Code quality scan daily
    - cron: '0 2 * * *'
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  # Daily quality scan
  quality-scan:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run quality scanner
        run: python agents/code_quality_scanner.py

  # PR coverage check
  coverage-check:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test coverage
        run: python agents/pr_coverage_tester.py ${{ github.event.number }}

  # Dependency updates (weekly)
  dependency-update:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Update dependencies
        run: python agents/dependency_updater.py update
```

---

## 📊 Monitoring and Logs

All agents write logs to `agents/logs/`:

```
agents/logs/
├── code_quality_scanner.log
├── pr_coverage_tester.log
├── crash_analyzer.log
├── doc_syncer.log
└── dependency_updater.log
```

### Viewing Logs

```bash
# View latest logs
tail -f agents/logs/code_quality_scanner.log

# Search for errors
grep ERROR agents/logs/*.log

# Get statistics
grep "✅" agents/logs/*.log | wc -l
```

---

## 🎯 Agent Capabilities Summary

| Agent | Frequency | Automation | PR Creation | Safety |
|-------|-----------|------------|-------------|--------|
| Code Quality Scanner | Daily | ✅ | ✅ | ⭐⭐⭐⭐ |
| PR Coverage Tester | Per PR | ✅ | ❌ (only rejects) | ⭐⭐⭐⭐ |
| Crash Log Analyzer | Continuous | ✅ | ✅ | ⭐⭐⭐⭐ |
| Documentation Syncer | Hourly | ✅ | ✅ | ⭐⭐⭐⭐ |
| Dependency Updater | Weekly | ✅ | ✅ | ⭐⭐⭐⭐⭐ |

**Safety Ratings:**
- ⭐⭐⭐⭐⭐ = Very Safe (extensive testing, rollback mechanisms)
- ⭐⭐⭐⭐ = Safe (tested, reviewed)
- ⭐⭐⭐ = Moderate (some manual review recommended)

---

## 🛠️ Advanced Configuration

### Customizing Tools

**Code Quality Scanner:**
Edit `code_quality_scanner.py` to adjust tools:
```python
self.tools = {
    'pylint': {'enabled': True, 'config': '.pylintrc'},
    'flake8': {'enabled': True},
    'isort': {'enabled': True},
    'bandit': {'enabled': True},
    'safety': {'enabled': True}
}
```

**PR Coverage Tester:**
Adjust coverage thresholds:
```bash
export MIN_COVERAGE=95.0  # Require 95% coverage
export MIN_FILE_COVERAGE=85.0  # Require 85% per file
```

**Dependency Updater:**
Set blocklist:
```bash
export BLOCKLIST="numpy,pandas,scipy"
export MAX_UPDATES=5  # Allow up to 5 updates per run
```

---

## 🔐 Security Considerations

All agents are designed with security in mind:

### GitHub Permissions
- Read-only access to repository
- Create pull requests (no direct push to main)
- Cannot modify secrets or protected branches

### Code Execution
- All code runs in sandboxed environment
- No direct database access
- No production infrastructure changes

### Dependency Updates
- Major version bumps require manual review
- Blocklist for critical packages
- Full regression testing required
- Automatic rollback on test failure

---

## 🚀 Quick Deployment

### Option 1: Automated Deployment Script

The fastest way to deploy all agents:

```bash
# Run the deployment script
./scripts/deploy_agents.sh all

# This will:
# - Install dependencies
# - Set up cron jobs
# - Configure systemd services (Linux)
# - Test deployment
```

**Deployment Options:**
```bash
./scripts/deploy_agents.sh all      # Deploy everything
./scripts/deploy_agents.sh cron     # Setup cron jobs only
./scripts/deploy_agents.sh systemd  # Setup systemd services only
./scripts/deploy_agents.sh test     # Test deployment
```

### Option 2: Manual Cron Setup

```bash
# Edit crontab
crontab -e

# Add these lines:
# Daily code quality scan at 2 AM
0 2 * * * cd /path/to/psychsync && python3 agents/code_quality_scanner.py >> agents/logs/scanner.log 2>&1

# Weekly dependency update on Sunday at 3 AM
0 3 * * 0 cd /path/to/psychsync && python3 agents/dependency_updater.py schedule >> agents/logs/updater.log 2>&1

# Hourly documentation sync
0 * * * * cd /path/to/psychsync && python3 agents/doc_syncer.py scan >> agents/logs/docsyncer.log 2>&1
```

### Option 3: GitHub Actions (Cloud)

The `.github/workflows/agents.yml` workflow automatically runs:

```yaml
schedule:
  # Daily code quality scan at 2 AM UTC
  - cron: '0 2 * * *'
  # Weekly dependency update on Sunday at 3 AM UTC
  - cron: '0 3 * * 0'
  # Hourly documentation sync
  - cron: '0 * * * *'
```

**Manual trigger via GitHub UI:**
- Go to Actions tab
- Select "Autonomous Agents" workflow
- Click "Run workflow"
- Choose which agent to run

### Option 4: Systemd Services (Linux)

For continuous monitoring agents:

```bash
# Install systemd services
sudo cp deploy/systemd/*.service /etc/systemd/system/

# Edit service files with your paths
sudo nano /etc/systemd/system/psychsync-crash-analyzer.service

# Reload and start
sudo systemctl daemon-reload
sudo systemctl enable psychsync-crash-analyzer.service
sudo systemctl start psychsync-crash-analyzer.service

# Check status
sudo systemctl status psychsync-crash-analyzer.service
```

See `deploy/systemd/README.md` for detailed instructions.

---

## 📈 Metrics and Reporting

### Agent Performance Metrics

Track agent effectiveness with these metrics:

```bash
# Code Quality Scanner
grep "✅ Scan complete" agents/logs/code_quality_scanner.log | wc -l

# PR Coverage Tester
grep "PR #" agents/logs/pr_coverage_tester.log | wc -l

# Crash Log Analyzer
grep "🔍 Analyzing crash" agents/logs/crash_analyzer.log | wc -l

# Documentation Syncer
grep "files updated" agents/logs/doc_syncer.log | wc -l

# Dependency Updater
grep "Successfully updated" agents/logs/dependency_updater.log | wc -l
```

### Success Criteria

**Code Quality Scanner:**
- ✅ Finds at least 5 issues per scan
- ✅ Creates PR within 5 minutes
- ✅ Auto-fixes applied successfully

**PR Coverage Tester:**
- ✅ 100% PR coverage checks pass
- ✅ Coverage reports posted within 2 minutes
- ✅ False positive rate < 5%

**Crash Log Analyzer:**
- ✅ Analyzes crashes within 5 minutes
- ✅ Correct root cause identified >80% of time
- ✅ Issues created with actionable fixes

**Documentation Syncer:**
- ✅ Detects all code changes
- ✅ Updates documentation within 10 minutes
- ✅ PRs merged successfully

**Dependency Updater:**
- ✅ Checks for updates weekly
- ✅ Safe updates applied
- ✅ Zero regressions from updates

---

## 🤝 Contributing to Agents

All agents are modular and extensible. To add new features:

1. **Clone the agent file**
2. **Add your enhancement**
3. **Test locally**
4. **Create PR with `[agents]` label**
5. **Include tests for new functionality**

### Testing Agents Locally

```bash
# Test code quality scanner
python agents/code_quality_scanner.py

# Test PR coverage tester
python agents/pr_coverage_tester.py

# Test crash log analyzer (with sample log)
python agents/crash_log_analyzer.py analyze agents/test_data/sample_crash.log

# Test documentation syncer
python agents/doc_syncer.py scan

# Test dependency updater
python agents/dependency_updater.py check
```

---

## 🐛 Troubleshooting

### Agent Won't Run

**Problem:** `GITHUB_TOKEN not set`
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
```

**Problem:** Permission denied
```bash
chmod +x agents/*.py
```

**Problem:** Module not found
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Agent Created PR but Tests Failed

This is expected safety behavior:
1. Review the failed PR
2. Fix the underlying issue
3. The agent will try again next run

### Too Many PRs Created

Adjust agent frequency:
- Code Quality Scanner: Run weekly instead of daily
- Dependency Updater: Set `MAX_UPDATES=1`
- Documentation Syncer: Run daily instead of hourly

---

## 📚 Related Documentation

- **CI/CD Pipeline:** `.github/workflows/cicd-pipeline.yaml`
- **Testing Guide:** `docs/sops/DEVELOPER_ONBOARDING_SOP.md`
- **Incident Response:** `docs/sops/INCIDENT_RESPONSE_ESCALATION_SOP.md`
- **Production Deployment:** `docs/sops/PRODUCTION_DEPLOYMENT_SOP.md`

---

## 🎓 Best Practices

### 1. Start Slowly
- Run agents manually first
- Verify they work as expected
- Then automate with cron/GitHub Actions

### 2. Monitor Initial Runs
- Check logs after first few runs
- Verify PRs are appropriate
- Adjust thresholds as needed

### 3. Customize for Your Team
- Adjust coverage thresholds
- Set up package blocklists
- Configure notification channels

### 4. Maintain Agents
- Keep agent dependencies updated
- Review and improve agent code
- Add new features as needed

### 5. Document Changes
- Update this README when adding features
- Document configuration changes
- Share knowledge with team

---

## 🚀 Future Enhancements

Planned improvements:

**Short Term:**
- [ ] Add Slack/Teams notifications
- [ ] Create dashboard for agent metrics
- [ ] Add agent health monitoring
- [ ] Implement rate limiting for PR creation

**Long Term:**
- [ ] Machine learning for smarter PR creation
- [ ] Predictive crash detection
- [ ] Automatic test generation for low coverage
- [ ] Dependency vulnerability scanning
- [ ] Multi-repository support

---

## 📞 Support

**Questions?**
- **Docs Team:** docs@psychsync.com
- **DevOps Team:** devops@psychsync.com
- **GitHub Issues:** https://github.com/psychsync/psychsync/issues

**Report Issues:**
Create an issue with label `agent:` and the specific agent name.

---

**Version:** 1.0.0
**Last Updated:** December 27, 2025
**Maintained By:** DevOps Team

---

## 🎉 Summary

These 5 autonomous agents work together to:

✅ **Maintain code quality** - Automatically fix bugs and smells
✅ **Enforce standards** - Require 90% test coverage
✅ **Improve reliability** - Analyze crashes and suggest fixes
✅ **Keep docs current** - Sync documentation with code
✅ **Stay secure** - Update dependencies safely

**Result:** Less manual work, higher code quality, faster development! 🚀
