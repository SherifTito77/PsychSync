# 🚀 Autonomous Agents Deployment Guide

**Complete guide for deploying autonomous agents in production**

---

## Table of Contents

1. [Deployment Options Overview](#deployment-options-overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Deployment Methods](#deployment-methods)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Deployment Options Overview

You have **4 deployment options** for the autonomous agents:

| Option | Best For | Difficulty | Maintenance |
|--------|----------|------------|-------------|
| **Automated Script** | Quick setup, one-time deployment | ⭐ Easy | Low |
| **Cron Jobs** | Unix/Linux servers, simple scheduling | ⭐⭐ Medium | Low |
| **GitHub Actions** | Cloud-based, no infrastructure | ⭐ Easy | Very Low |
| **Systemd Services** | Continuous monitoring, Linux servers | ⭐⭐⭐ Advanced | Medium |

### Recommended Deployments by Agent

**Code Quality Scanner:**
- ✅ GitHub Actions (recommended)
- ✅ Cron job
- ❌ Systemd (not continuous)

**PR Coverage Tester:**
- ✅ GitHub Actions (recommended - triggers on PR)
- ✅ Systemd service (continuous polling)
- ❌ Cron (not recommended)

**Crash Log Analyzer:**
- ✅ Systemd service (recommended - continuous)
- ✅ Manual on-demand
- ❌ Cron (not continuous enough)

**Documentation Syncer:**
- ✅ GitHub Actions (recommended)
- ✅ Cron job (hourly)
- ❌ Systemd (overkill)

**Dependency Updater:**
- ✅ GitHub Actions (recommended)
- ✅ Cron job (weekly)
- ❌ Systemd (not needed)

---

## Prerequisites

### Required Software

**For All Deployments:**
```bash
# Python 3.11+
python3 --version

# Git
git --version

# GitHub CLI (optional, for testing)
gh --version
```

**For Cron Deployment:**
```bash
# cron (usually installed by default)
crontab -l
```

**For Systemd Deployment:**
```bash
# systemd
systemctl --version
```

### Required Python Packages

```bash
# Core agent dependencies
pip install github3.py GitPython

# Code quality scanner
pip install pylint flake8 isort bandit safety autopep8

# PR coverage tester
pip install pytest pytest-cov

# Dependency updater
pip install pip-outdated
```

### Required Environment Variables

All agents require:

```bash
# GitHub authentication
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GITHUB_REPOSITORY="psychsync/psychsync"

# Optional: Coverage thresholds
export MIN_COVERAGE="90.0"
export MIN_FILE_COVERAGE="80.0"

# Optional: Dependency update limits
export MAX_UPDATES="3"
export BLOCKLIST=""
```

**Create `.env.agents` file:**
```bash
cat > .env.agents << 'EOF'
# GitHub Settings
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPOSITORY=psychsync/psychsync

# Coverage Settings
MIN_COVERAGE=90.0
MIN_FILE_COVERAGE=80.0

# Dependency Settings
MAX_UPDATES=3
BLOCKLIST=
EOF
```

---

## Quick Start

### Fastest Path to Production (5 minutes)

```bash
# 1. Set GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# 2. Run deployment script
./scripts/deploy_agents.sh all

# 3. Verify deployment
crontab -l  # Check cron jobs
ls agents/logs/  # Check logs directory

# 4. Test manually
python3 agents/code_quality_scanner.py
```

**That's it!** Your agents are now deployed.

---

## Deployment Methods

### Method 1: Automated Deployment Script

**File:** `scripts/deploy_agents.sh`

**What it does:**
- ✅ Runs pre-flight checks
- ✅ Installs dependencies
- ✅ Sets up cron jobs
- ✅ Configures systemd services
- ✅ Tests deployment

**Usage:**
```bash
# Deploy everything
./scripts/deploy_agents.sh all

# Deploy cron jobs only
./scripts/deploy_agents.sh cron

# Deploy systemd services only
./scripts/deploy_agents.sh systemd

# Test deployment
./scripts/deploy_agents.sh test
```

**Output:**
```
╔════════════════════════════════════════════════════════════════╗
║          PsychSync Autonomous Agents Deployment               ║
╚════════════════════════════════════════════════════════════════╝

[INFO] Running pre-flight checks...
[INFO] Checking environment variables...
[SUCCESS] Pre-flight checks passed!

[INFO] Installing dependencies...
[SUCCESS] Dependencies installed!

[INFO] Setting up cron jobs...
[SUCCESS] Cron jobs installed!

[INFO] Testing agent deployment...
[SUCCESS] Code quality scanner: OK
[SUCCESS] PR coverage tester: OK
[SUCCESS] Crash log analyzer: OK
[SUCCESS] Documentation syncer: OK
[SUCCESS] Dependency updater: OK

[SUCCESS] Deployment complete!
```

---

### Method 2: Cron Jobs

**Best for:** Scheduled tasks (daily, weekly, hourly)

**Setup:**
```bash
# Edit crontab
crontab -e

# Add these lines:
# PsychSync Autonomous Agents

# Daily code quality scan at 2 AM
0 2 * * * cd /path/to/psychsync && python3 agents/code_quality_scanner.py >> agents/logs/scanner.log 2>&1

# Weekly dependency update on Sunday at 3 AM
0 3 * * 0 cd /path/to/psychsync && python3 agents/dependency_updater.py schedule >> agents/logs/updater.log 2>&1

# Hourly documentation sync
0 * * * * cd /path/to/psychsync && python3 agents/doc_syncer.py scan >> agents/logs/docsyncer.log 2>&1
```

**Verify:**
```bash
# List cron jobs
crontab -l

# Check last run
tail -20 agents/logs/scanner.log
```

**Cron Schedule Reference:**
```
* * * * * command to be executed
│ │ │ │ │
│ │ │ │ └───── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └─────── Month (1-12)
│ │ └───────── Day of month (1-31)
│ └─────────── Hour (0-23)
└───────────── Minute (0-59)

Examples:
0 2 * * *      # Daily at 2 AM
0 3 * * 0      # Weekly on Sunday at 3 AM
0 * * * *      # Every hour
*/15 * * * *   # Every 15 minutes
0 0 * * 1      # Weekly on Monday at midnight
```

---

### Method 3: GitHub Actions

**Best for:** Cloud-based deployment, no infrastructure management

**File:** `.github/workflows/agents.yml`

**Features:**
- ✅ Automatic scheduling (daily, weekly, hourly)
- ✅ Manual trigger via GitHub UI
- ✅ PR-based coverage testing
- ✅ Agent health checks
- ✅ Log artifact storage

**Setup:**
1. Add `GITHUB_TOKEN` to repository secrets (already available)
2. Push workflow file to repository
3. Enable Actions in repository settings
4. Agents run automatically on schedule

**Manual Trigger:**
1. Go to repository on GitHub
2. Click "Actions" tab
3. Select "Autonomous Agents" workflow
4. Click "Run workflow"
5. Choose agent to run
6. Click "Run workflow"

**View Results:**
- Actions tab → Select workflow run → View logs
- PR comments for coverage reports
- Created PRs and issues

**Advantages:**
- ✅ No server required
- ✅ Free for public repositories
- ✅ Automatic scaling
- ✅ Integrated with GitHub
- ✅ Artifact storage for logs

**Disadvantages:**
- ❌ Limited to GitHub repositories
- ❌ 6-hour job timeout
- ❌ No continuous monitoring (can't watch log files)

---

### Method 4: Systemd Services

**Best for:** Continuous monitoring, long-running processes

**Files:** `deploy/systemd/*.service`

**Setup:**
```bash
# 1. Copy service files
sudo cp deploy/systemd/*.service /etc/systemd/system/

# 2. Edit service files with your paths
sudo nano /etc/systemd/system/psychsync-crash-analyzer.service

# Update these fields:
# - User=yourusername
# - Group=yourgroup
# - WorkingDirectory=/path/to/psychsync
# - ExecStart=/usr/bin/python3 /path/to/agents/crash_log_analyzer.py watch /var/log/app/errors.log

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Enable services (start on boot)
sudo systemctl enable psychsync-crash-analyzer.service
sudo systemctl enable psychsync-pr-coverage-watcher.service

# 5. Start services
sudo systemctl start psychsync-crash-analyzer.service
sudo systemctl start psychsync-pr-coverage-watcher.service

# 6. Check status
sudo systemctl status psychsync-crash-analyzer.service
```

**Management Commands:**
```bash
# Start/Stop/Restart
sudo systemctl start psychsync-crash-analyzer.service
sudo systemctl stop psychsync-crash-analyzer.service
sudo systemctl restart psychsync-crash-analyzer.service

# View logs
sudo journalctl -u psychsync-crash-analyzer.service -f

# Enable/disable autostart
sudo systemctl enable psychsync-crash-analyzer.service
sudo systemctl disable psychsync-crash-analyzer.service

# Check if active
sudo systemctl is-active psychsync-crash-analyzer.service
```

**Advantages:**
- ✅ Automatic restart on failure
- ✅ Starts on system boot
- ✅ Integrated logging with journalctl
- ✅ Resource limits
- ✅ Security features

**Disadvantages:**
- ❌ Linux only
- ❌ Requires root/sudo
- ❌ More complex setup

---

## Configuration

### Environment Variables

All agents can be configured via environment variables:

```bash
# GitHub Settings (required)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPOSITORY="psychsync/psychsync"

# Code Quality Scanner
export ENABLE_PYLINT="true"
export ENABLE_FLAKE8="true"
export ENABLE_ISORT="true"
export ENABLE_BANDIT="true"
export ENABLE_SAFETY="true"

# PR Coverage Tester
export MIN_COVERAGE="90.0"           # Overall coverage threshold
export MIN_FILE_COVERAGE="80.0"      # Per-file coverage threshold
export TEST_COMMAND="pytest"         # Test command to run

# Dependency Updater
export MAX_UPDATES="3"               # Max updates per run
export BLOCKLIST="numpy,pandas"      # Packages to skip
export REQUIRE_TESTS="true"          # Require tests before PR

# Crash Log Analyzer
export CRASH_LOG_PATH="/var/log/app/errors.log"
export SENTRY_DSN=""                 # Optional: Sentry integration

# Documentation Syncer
export SYNC_INTERVAL_MINUTES="60"    # How often to sync
```

**Configuration Files:**
```bash
# Create .env.agents
cat > .env.agents << 'EOF'
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPOSITORY=psychsync/psychsync
MIN_COVERAGE=90.0
EOF

# Source it
source .env.agents
```

**Cron Job with Environment:**
```bash
# Source environment in cron job
0 2 * * * cd /path/to/psychsync && . .env.agents && python3 agents/code_quality_scanner.py
```

---

## Monitoring

### Log Files

All agents write logs to `agents/logs/`:

```bash
agents/logs/
├── code_quality_scanner.log       # Code quality scans
├── pr_coverage_tester.log         # PR coverage tests
├── crash_analyzer.log             # Crash analyses
├── doc_syncer.log                 # Documentation syncs
└── dependency_updater.log         # Dependency updates
```

**View logs:**
```bash
# Real-time monitoring
tail -f agents/logs/code_quality_scanner.log

# Last 50 lines
tail -50 agents/logs/pr_coverage_tester.log

# Search for errors
grep ERROR agents/logs/*.log

# Search for successes
grep "✅" agents/logs/*.log

# Log statistics
wc -l agents/logs/*.log
```

### Metrics and Alerts

**Key Metrics to Track:**

**Code Quality Scanner:**
```bash
# Scans completed
grep "Scan complete" agents/logs/code_quality_scanner.log | wc -l

# Issues found
grep "issues found" agents/logs/code_quality_scanner.log

# PRs created
grep "PR created" agents/logs/code_quality_scanner.log
```

**PR Coverage Tester:**
```bash
# PRs tested
grep "Testing PR #" agents/logs/pr_coverage_tester.log

# Coverage failures
grep "FAILED" agents/logs/pr_coverage_tester.log

# Average coverage
grep "Coverage:" agents/logs/pr_coverage_tester.log | awk '{sum+=$2; count++} END {print sum/count}'
```

**Crash Log Analyzer:**
```bash
# Crashes analyzed
grep "Analyzing crash" agents/logs/crash_analyzer.log | wc -l

# Issues created
grep "Issue created" agents/logs/crash_analyzer.log

# Critical crashes
grep "CRITICAL" agents/logs/crash_analyzer.log
```

**Set up alerts:**
```bash
# Create alert script
cat > /usr/local/bin/agent-alerts.sh << 'EOF'
#!/bin/bash
# Check for critical errors in agent logs

if grep -r "CRITICAL" agents/logs/*.log | tail -1; then
    echo "CRITICAL: Agent errors detected!"
    # Send email, Slack notification, etc.
fi
EOF

chmod +x /usr/local/bin/agent-alerts.sh

# Add to cron (check every hour)
0 * * * * /usr/local/bin/agent-alerts.sh
```

### Health Checks

**GitHub Actions Health Check:**
The workflow includes an automatic health check job that:
- Checks for errors in agent logs
- Creates GitHub issue if errors found

**Manual Health Check:**
```bash
# Create health check script
cat > agents/health_check.sh << 'EOF'
#!/bin/bash

echo "Checking agent health..."

services=("code_quality_scanner" "pr_coverage_tester" "crash_analyzer" "doc_syncer" "dependency_updater")

for service in "${services[@]}"; do
    log_file="agents/logs/${service}.log"

    if [ -f "$log_file" ]; then
        last_run=$(tail -1 "$log_file" | grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

        if [ -n "$last_run" ]; then
            echo "✅ $service: Last run $last_run"
        else
            echo "⚠️  $service: No recent runs"
        fi

        # Check for errors
        if grep -q "ERROR" "$log_file"; then
            echo "❌ $service: Errors found in log"
        fi
    else
        echo "❌ $service: Log file not found"
    fi
done
EOF

chmod +x agents/health_check.sh

# Run it
./agents/health_check.sh
```

---

## Troubleshooting

### Common Issues

**Issue: Agent won't run**

```
Error: GITHUB_TOKEN not set
```

**Solution:**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
# Or add to .env.agents and source it
```

---

**Issue: Permission denied when running agent**

```
bash: ./agents/code_quality_scanner.py: Permission denied
```

**Solution:**
```bash
chmod +x agents/*.py
```

---

**Issue: Module not found**

```
ModuleNotFoundError: No module named 'github3'
```

**Solution:**
```bash
pip install github3.py GitPython pylint flake8 isort bandit safety autopep8
```

---

**Issue: Cron job not running**

**Solution:**
```bash
# Check cron is running
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Verify cron job syntax
crontab -l | grep -v "^#" | cat -  # View jobs without comments
```

---

**Issue: Systemd service fails**

**Solution:**
```bash
# Check service status
sudo systemctl status psychsync-crash-analyzer.service

# View service logs
sudo journalctl -u psychsync-crash-analyzer.service -n 100

# Check service file syntax
sudo systemd-analyze verify psychsync-crash-analyzer.service
```

---

**Issue: Agent creates too many PRs**

**Solution:**
```bash
# Reduce frequency
# Cron: Run weekly instead of daily
0 3 * * 0 python agents/code_quality_scanner.py  # Only Sunday

# Or limit updates
export MAX_UPDATES=1  # Only 1 dependency update per run
```

---

### Debug Mode

Run agents in debug mode:

```bash
# Enable debug logging
export DEBUG="true"
export LOG_LEVEL="DEBUG"

# Run agent manually
python3 agents/code_quality_scanner.py

# Check logs
cat agents/logs/code_quality_scanner.log
```

---

### Rollback

If agents cause issues:

```bash
# Remove cron jobs
crontab -l > /tmp/crontab_backup
crontab -l | grep -v "agents/" | crontab -

# Stop systemd services
sudo systemctl stop psychsync-crash-analyzer.service
sudo systemctl disable psychsync-crash-analyzer.service

# Disable GitHub Actions workflow
# Go to: .github/workflows/agents.yml
# Add: if: false  # at the top of each job
git commit -am "Disable agents temporarily"
git push
```

---

## Best Practices

### 1. Start Conservative

**Week 1:** Dry run only
```bash
export DRY_RUN="true"
python agents/code_quality_scanner.py
```

**Week 2:** Manual approval
- Let agents create PRs
- Review each PR manually
- Don't auto-merge

**Week 3+:** Full automation
- Merge PRs automatically if tests pass
- Set up alerts for failures

### 2. Monitor Initial Performance

First 2 weeks, check daily:
- Review agent logs
- Check PR quality
- Verify coverage compliance
- Monitor dependency updates

### 3. Customize for Your Team

Adjust configurations:
```bash
# Stricter coverage requirements
export MIN_COVERAGE=95.0

# Fewer dependency updates
export MAX_UPDATES=1

# Block risky packages
export BLOCKLIST="tensorflow,scikit-learn"
```

### 4. Set Up Alerts

Configure notifications for:
- Agent failures
- Coverage drops
- Security vulnerabilities
- Created PRs/issues

### 5. Document Customizations

Keep track of changes:
```bash
# Create team-specific config
cat > .env.agents.team << 'EOF'
# Team XYZ Custom Settings
MIN_COVERAGE=95.0
MAX_UPDATES=1
BLOCKLIST=numpy,pandas
EOF
```

### 6. Regular Maintenance

**Monthly:**
- Review agent logs
- Update agent code
- Adjust configurations
- Check false positive rates

**Quarterly:**
- Evaluate agent effectiveness
- Add new agents as needed
- Retire unused agents
- Update documentation

---

## Additional Resources

### Documentation

- **Agent README:** `agents/README.md`
- **Agent Summary:** `agents/AUTONOMOUS_AGENTS_SUMMARY.md`
- **Systemd Services:** `deploy/systemd/README.md`

### Scripts

- **Deployment Script:** `scripts/deploy_agents.sh`
- **Health Check:** `agents/health_check.sh`

### Configuration Files

- **Environment Variables:** `.env.agents`
- **Cron Jobs:** `crontab -l`
- **Systemd Services:** `/etc/systemd/system/psychsync-*.service`

### Support

- **GitHub Issues:** https://github.com/psychsync/psychsync/issues
- **Documentation:** See agent README files
- **Logs:** `agents/logs/`

---

**Version:** 1.0.0
**Last Updated:** December 27, 2025
**Maintained By:** DevOps Team

---

## Summary

**Choose your deployment method:**

1. **Automated Script** - Fastest, easiest (`./scripts/deploy_agents.sh all`)
2. **Cron Jobs** - Simple, reliable for scheduled tasks
3. **GitHub Actions** - Cloud-based, no infrastructure
4. **Systemd Services** - Continuous monitoring, Linux servers

**Key steps:**
1. Set `GITHUB_TOKEN`
2. Run deployment script or set up manually
3. Monitor logs in `agents/logs/`
4. Customize configurations as needed

**You're ready to deploy!** 🚀
