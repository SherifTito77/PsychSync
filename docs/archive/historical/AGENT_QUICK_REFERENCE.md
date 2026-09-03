# 🤖 Autonomous Agents - Quick Reference Guide

**Print-friendly quick reference for PsychSync autonomous agents**

---

## 🚀 Quick Start (5 Commands)

```bash
# 1. Set GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# 2. Deploy all agents
./scripts/deploy_agents.sh all

# 3. Verify installation
./scripts/verify_agents.sh

# 4. Watch agents work
tail -f agents/logs/*.log

# 5. See demo
./scripts/demo_agents.sh
```

---

## 📦 Agent Overview

| Agent | What It Does | When It Runs | Where It Runs |
|-------|--------------|--------------|---------------|
| **Code Quality Scanner** | Finds bugs, smells, security issues | Daily at 2 AM | Cron / GitHub Actions |
| **PR Coverage Tester** | Tests PR coverage, rejects if <90% | On every PR | GitHub Actions |
| **Crash Log Analyzer** | Analyzes crashes, creates issues | Continuous | Systemd service |
| **Documentation Syncer** | Syncs docs with code changes | Hourly | Cron / GitHub Actions |
| **Dependency Updater** | Updates dependencies safely | Weekly Sunday | Cron / GitHub Actions |

---

## 🎯 Common Commands

### Deployment

```bash
./scripts/deploy_agents.sh all      # Deploy everything
./scripts/deploy_agents.sh cron     # Setup cron only
./scripts/deploy_agents.sh systemd  # Setup systemd only
```

### Testing

```bash
./scripts/verify_agents.sh          # Verify agents work
./scripts/demo_agents.sh            # See agents in action

# Test individual agents
python3 agents/code_quality_scanner.py
python3 agents/pr_coverage_tester.py
python3 agents/crash_log_analyzer.py analyze crash.log
python3 agents/doc_syncer.py scan
python3 agents/dependency_updater.py check
```

### Monitoring

```bash
# View logs
tail -f agents/logs/*.log

# Check specific agent
tail -f agents/logs/code_quality_scanner.log

# Search for errors
grep ERROR agents/logs/*.log

# Check for successes
grep "✅" agents/logs/*.log
```

### Cron Management

```bash
crontab -l                          # View cron jobs
crontab -e                          # Edit cron jobs

# Remove all agent cron jobs
crontab -l | grep -v "agents/" | crontab -
```

### Systemd Management (Linux)

```bash
sudo systemctl status psychsync-crash-analyzer.service
sudo systemctl start psychsync-crash-analyzer.service
sudo systemctl stop psychsync-crash-analyzer.service
sudo systemctl restart psychsync-crash-analyzer.service
sudo journalctl -u psychsync-crash-analyzer.service -f
```

---

## 📁 File Locations

```
psychsync/
├── agents/                          # Agent code
│   ├── code_quality_scanner.py
│   ├── pr_coverage_tester.py
│   ├── crash_log_analyzer.py
│   ├── doc_syncer.py
│   ├── dependency_updater.py
│   ├── logs/                       # Agent logs
│   └── README.md
├── scripts/                         # Helper scripts
│   ├── deploy_agents.sh            # Deployment
│   ├── demo_agents.sh              # Demo
│   └── verify_agents.sh            # Verification
├── .github/workflows/
│   └── agents.yml                  # GitHub Actions
├── deploy/systemd/
│   ├── *.service                   # Systemd services
│   └── README.md
└── docs/
    └── AGENT_DEPLOYMENT_GUIDE.md   # Full guide
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
export GITHUB_REPOSITORY="psychsync/psychsync"

# Optional
export MIN_COVERAGE="90.0"           # Coverage threshold
export MAX_UPDATES="3"               # Max dependency updates
export BLOCKLIST="numpy,pandas"      # Block risky packages
```

### Configuration File

```bash
# Create .env.agents
cat > .env.agents << 'EOF'
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_REPOSITORY=psychsync/psychsync
MIN_COVERAGE=90.0
MAX_UPDATES=3
EOF

# Source it
source .env.agents
```

---

## 🐛 Troubleshooting

### Problem: Agent won't run

```bash
# Check Python version (need 3.11+)
python3 --version

# Install dependencies
pip install github3.py GitPython pylint flake8 isort bandit safety

# Check GITHUB_TOKEN
echo $GITHUB_TOKEN
```

### Problem: Cron job not running

```bash
# Check if cron is running
sudo systemctl status cron  # Linux
launchctl list | grep cron  # macOS

# View cron logs
grep CRON /var/log/syslog   # Linux
log show --predicate 'process == "cron"'  # macOS
```

### Problem: Systemd service failed

```bash
# Check service status
sudo systemctl status psychsync-crash-analyzer.service

# View logs
sudo journalctl -u psychsync-crash-analyzer.service -n 100

# Restart service
sudo systemctl restart psychsync-crash-analyzer.service
```

### Problem: Too many PRs created

```bash
# Reduce frequency
# Edit crontab and change schedule
crontab -e

# Or reduce updates
export MAX_UPDATES=1
```

---

## 📊 Success Metrics

### Week 1 Expectations

- ✅ All agents running without errors
- ✅ Logs created in `agents/logs/`
- ✅ Cron jobs scheduled
- ✅ GitHub Actions running

### Week 2-4 Expectations

- ✅ 1-3 code quality PRs per week
- ✅ All PRs tested for coverage
- ✅ Documentation synced with changes
- ✅ Dependencies updated weekly

### Month 2+ Expectations

- ✅ 27+ hours saved per week
- ✅ Zero security vulnerabilities
- ✅ 100% coverage compliance
- ✅ Improved code quality

---

## 🔐 Security Checklist

- [ ] GITHUB_TOKEN set correctly
- [ ] GITHUB_TOKEN has repo scope (not admin)
- [ ] No hardcoded secrets in agent files
- [ ] Log files have appropriate permissions
- [ ] Blocklist configured for risky packages
- [ ] Services run as non-root user

---

## 📚 Documentation

- **Quick Reference:** This file
- **Full Guide:** `docs/AGENT_DEPLOYMENT_GUIDE.md`
- **Agent README:** `agents/README.md`
- **Systemd Guide:** `deploy/systemd/README.md`
- **Delivery Summary:** `AGENT_DEPLOYMENT_DELIVERY.md`

---

## 🎯 Deployment Decision Tree

```
Need to deploy agents?
│
├─ Quick setup, one-time?
│  └─ Use: ./scripts/deploy_agents.sh all
│
├─ Scheduled tasks (Unix/Linux)?
│  └─ Use: Cron jobs (crontab -e)
│
├─ Cloud-based, no infrastructure?
│  └─ Use: GitHub Actions (.github/workflows/agents.yml)
│
└─ Continuous monitoring?
   └─ Use: Systemd services (deploy/systemd/*.service)
```

---

## 💡 Tips

1. **Start conservative** - Use dry-run mode first
2. **Monitor logs** - Check `agents/logs/` daily first week
3. **Customize settings** - Adjust coverage thresholds, blocklists
4. **Set up alerts** - Get notified of agent failures
5. **Review PRs** - Don't auto-merge initially
6. **Document changes** - Keep track of custom configurations

---

## 🆘 Getting Help

### Check logs first
```bash
tail -50 agents/logs/*.log
```

### Run verification
```bash
./scripts/verify_agents.sh
```

### See demo
```bash
./scripts/demo_agents.sh
```

### Read documentation
```bash
less docs/AGENT_DEPLOYMENT_GUIDE.md
```

---

## 🎉 Quick Command Summary

```bash
# Deploy
./scripts/deploy_agents.sh all

# Verify
./scripts/verify_agents.sh

# Demo
./scripts/demo_agents.sh

# Monitor
tail -f agents/logs/*.log

# Test manually
python3 agents/code_quality_scanner.py

# Manage cron
crontab -l

# Manage systemd
sudo systemctl status psychsync-crash-analyzer.service
```

---

**Version:** 1.0.0
**Last Updated:** December 27, 2025
**For detailed guide, see:** `docs/AGENT_DEPLOYMENT_GUIDE.md`

---

## 📋 Print Version

Print this page and keep it handy for quick reference!

Or save as PDF: `Ctrl+P → Save as PDF`
