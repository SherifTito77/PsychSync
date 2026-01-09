# Systemd Service Files for Autonomous Agents

This directory contains systemd service templates for running autonomous agents as system services.

## Available Services

### 1. Crash Log Analyzer (psychsync-crash-analyzer.service)
Continuously monitors application logs and analyzes crashes in real-time.

**Purpose:** Watch log files for crashes and automatically create issues

**Status:** Continuous (always running)

**Restart:** Automatically restarts on failure

---

### 2. PR Coverage Watcher (psychsync-pr-coverage-watcher.service)
Continuously watches for new PRs and tests their coverage.

**Purpose:** Automatically test PR coverage as they are created

**Status:** Continuous (polling every 2 minutes)

**Restart:** Automatically restarts on failure

---

## Installation

### Prerequisites

1. **Root/sudo access** - Required to install systemd services
2. **Python 3.11+** - Must be available at `/usr/bin/python3`
3. **Environment variables** - Set in `.env.agents` file

### Installation Steps

```bash
# 1. Copy service files to systemd directory
sudo cp deploy/systemd/*.service /etc/systemd/system/

# 2. Update paths in service files (edit with your actual paths)
sudo nano /etc/systemd/system/psychsync-crash-analyzer.service
# Update: User, Group, WorkingDirectory, ExecStart paths

# 3. Reload systemd daemon
sudo systemctl daemon-reload

# 4. Enable services to start on boot
sudo systemctl enable psychsync-crash-analyzer.service
sudo systemctl enable psychsync-pr-coverage-watcher.service

# 5. Start services
sudo systemctl start psychsync-crash-analyzer.service
sudo systemctl start psychsync-pr-coverage-watcher.service

# 6. Check service status
sudo systemctl status psychsync-crash-analyzer.service
sudo systemctl status psychsync-pr-coverage-watcher.service
```

---

## Configuration

### Environment Variables

Edit the service file to set environment variables:

```ini
[Service]
Environment="GITHUB_TOKEN=ghp_xxxxxxxxxxxx"
Environment="GITHUB_REPOSITORY=psychsync/psychsync"
Environment="MIN_COVERAGE=90.0"
EnvironmentFile=-/path/to/.env.agents
```

### Path Updates

Update these paths in the service file:

- `User=` - Your Linux username
- `Group=` - Your user group
- `WorkingDirectory=` - Path to PsychSync project
- `ExecStart=` - Full path to Python and agent script
- `StandardOutput=` - Path to log file
- `StandardError=` - Path to error log file

---

## Management Commands

### Start/Stop Services

```bash
# Start services
sudo systemctl start psychsync-crash-analyzer.service
sudo systemctl start psychsync-pr-coverage-watcher.service

# Stop services
sudo systemctl stop psychsync-crash-analyzer.service
sudo systemctl stop psychsync-pr-coverage-watcher.service

# Restart services
sudo systemctl restart psychsync-crash-analyzer.service
sudo systemctl restart psychsync-pr-coverage-watcher.service

# Reload configuration (without restart)
sudo systemctl reload psychsync-crash-analyzer.service
```

### Check Status

```bash
# Check service status
sudo systemctl status psychsync-crash-analyzer.service

# Check if service is running
sudo systemctl is-active psychsync-crash-analyzer.service

# Check if service is enabled
sudo systemctl is-enabled psychsync-crash-analyzer.service

# View service logs
sudo journalctl -u psychsync-crash-analyzer.service -f
```

### View Logs

```bash
# View real-time logs from journalctl
sudo journalctl -u psychsync-crash-analyzer.service -f

# View last 100 lines
sudo journalctl -u psychsync-crash-analyzer.service -n 100

# View logs since today
sudo journalctl -u psychsync-crash-analyzer.service --since today

# View agent logs directly
tail -f agents/logs/crash_analyzer.log
tail -f agents/logs/pr_coverage_tester.log
```

---

## Troubleshooting

### Service Won't Start

**Problem:** Service fails to start

**Solution:**
```bash
# Check service status for error message
sudo systemctl status psychsync-crash-analyzer.service

# View detailed logs
sudo journalctl -u psychsync-crash-analyzer.service -n 50 --no-pager

# Common issues:
# 1. Wrong paths in ExecStart
# 2. Python not found at /usr/bin/python3
# 3. Missing GITHUB_TOKEN
# 4. Missing dependencies
```

### Service Keeps Restarting

**Problem:** Service enters restart loop

**Solution:**
```bash
# Check why it's crashing
sudo journalctl -u psychsync-crash-analyzer.service -n 100

# Increase restart delay in service file:
RestartSec=300  # 5 minutes instead of 60 seconds

# Then reload and restart
sudo systemctl daemon-reload
sudo systemctl restart psychsync-crash-analyzer.service
```

### Permission Errors

**Problem:** Service can't write to logs

**Solution:**
```bash
# Create logs directory with correct permissions
mkdir -p agents/logs
chmod 755 agents/logs

# Or change service user to your user:
User=yourusername
Group=yourgroup
```

### Missing Dependencies

**Problem:** Service can't import Python modules

**Solution:**
```bash
# Install dependencies globally (for systemd)
sudo pip3 install github3.py GitPython pylint flake8 isort bandit safety

# Or use virtualenv in service file:
ExecStart=/path/to/venv/bin/python /path/to/agents/crash_log_analyzer.py watch
```

---

## Service File Structure

### Main Sections

**[Unit]**
- Description: Service description
- After: When to start (after network, database, etc.)
- Documentation: Link to documentation

**[Service]**
- Type: forking, simple, oneshot
- User/Group: Run as this user
- WorkingDirectory: Where to run from
- ExecStart: Command to start service
- ExecReload: Command to reload config
- Restart: When to restart (always, on-failure, no)
- RestartSec: Seconds before restart
- StandardOutput/Error: Where to log

**[Install]**
- WantedBy: Which target installs this service (multi-user.target = normal boot)

---

## Uninstallation

```bash
# 1. Stop and disable services
sudo systemctl stop psychsync-crash-analyzer.service
sudo systemctl stop psychsync-pr-coverage-watcher.service
sudo systemctl disable psychsync-crash-analyzer.service
sudo systemctl disable psychsync-pr-coverage-watcher.service

# 2. Remove service files
sudo rm /etc/systemd/system/psychsync-crash-analyzer.service
sudo rm /etc/systemd/system/psychsync-pr-coverage-watcher.service

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Remove systemd state files (optional)
sudo rm -rf /var/lib/systemd/deb-systemd-helper-multiarch/wants/*
```

---

## Security Considerations

### Service Security Features

The service files include these security measures:

```ini
NoNewPrivileges=true          # Don't gain extra privileges
PrivateTmp=true              # Use private /tmp directory
ProtectSystem=strict         # Read-only system directories
ProtectHome=true             # Can't access home directories
ReadWritePaths=/path/to/logs # Only write to these paths
```

### Best Practices

1. **Run as non-root user** - Don't run as root if possible
2. **Limit write access** - Only write to specific directories
3. **Use environment files** - Don't hardcode secrets in service files
4. **Log rotation** - Configure logrotate for agent logs
5. **Resource limits** - Add MemoryLimit/CPULimit if needed

---

## Monitoring

### Health Checks

```bash
# Create a simple health check script
cat > /usr/local/bin/check-agents-health.sh << 'EOF'
#!/bin/bash
services=("psychsync-crash-analyzer" "psychsync-pr-coverage-watcher")

for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service.service"; then
        echo "✅ $service is running"
    else
        echo "❌ $service is NOT running"
        # Send alert, log, or restart
    fi
done
EOF

chmod +x /usr/local/bin/check-agents-health.sh

# Add to cron for periodic checks
*/5 * * * * /usr/local/bin/check-agents-health.sh
```

### Metrics and Alerts

Monitor these metrics:

- Service uptime (`systemctl show --property=ActiveEnterTimestamp`)
- Restart count (`systemctl show --property=NRestarts`)
- Log file sizes
- Error rates in logs

---

## Alternative: Supervisord

If systemd is not available, use supervisord:

```ini
[program:crash-analyzer]
command=/usr/bin/python3 /path/to/agents/crash_log_analyzer.py watch /var/log/app/errors.log
directory=/path/to/psychsync
user=youruser
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/path/to/agents/logs/crash_analyzer.log
```

---

**Version:** 1.0.0
**Last Updated:** December 27, 2025
**Maintained By:** DevOps Team
