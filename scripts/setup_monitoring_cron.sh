#!/bin/bash
# Setup Automated Monitoring Schedule for Query Optimization
# This script configures cron jobs for daily and weekly monitoring

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║       Query Optimization - Monitoring Schedule Setup           ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

PROJECT_DIR="$(pwd)"
LOG_DIR="$PROJECT_DIR/monitoring_logs"

# Create log directory
mkdir -p "$LOG_DIR"

echo "Project Directory: $PROJECT_DIR"
echo "Log Directory: $LOG_DIR"
echo ""

# Function to install cron job
install_cron_job() {
    local schedule="$1"
    local command="$2"
    local description="$3"

    echo "Installing cron job: $description"
    echo "Schedule: $schedule"
    echo "Command: $command"
    echo ""

    # Export EDITOR to use cat for non-interactive crontab editing
    (crontab -l 2>/dev/null || true; echo "$schedule $command") | crontab -

    echo "✅ Cron job installed"
    echo ""
}

# Daily monitoring check (8:00 AM every day)
install_cron_job \
    "0 8 * * *" \
    "cd $PROJECT_DIR && bash scripts/daily_monitoring_check.sh >> $LOG_DIR/daily_\$(date +\%Y\%m\%d).log 2>&1" \
    "Daily Monitoring Check (8:00 AM)"

# Weekly performance report (5:00 PM every Friday)
install_cron_job \
    "0 17 * * 5" \
    "cd $PROJECT_DIR && python scripts/generate_weekly_report.py --week \$(( (\$(date +\%s) - \$(date -j -f '\%Y-\%m-\%d' '2025-01-18' +\%s)) / 86400 / 7 + 1 )) >> $LOG_DIR/weekly_\$(date +\%Y\%m\%d).log 2>&1" \
    "Weekly Performance Report (5:00 PM Friday)"

# Hourly health check (optional - commented out by default)
# Uncomment if you want hourly health checks
# install_cron_job \
#     "0 * * * *" \
#     "cd $PROJECT_DIR && python scripts/validate_query_optimization.py >> $LOG_DIR/hourly_\$(date +\%Y\%m\%d_\%H).log 2>&1" \
#     "Hourly Health Check"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CRON JOBS INSTALLED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Display current crontab
echo "Current crontab:"
echo "─────────────────────────────────────────────────────────────────"
crontab -l | grep -E "daily_monitoring_check|generate_weekly_report" || echo "No monitoring jobs found"
echo "─────────────────────────────────────────────────────────────────"
echo ""

echo "✅ Monitoring schedule setup complete!"
echo ""
echo "Scheduled Jobs:"
echo "  • Daily Check: 8:00 AM every day"
echo "  • Weekly Report: 5:00 PM every Friday"
echo "  • Logs: $LOG_DIR/"
echo ""
echo "To view scheduled jobs: crontab -l"
echo "To edit: crontab -e"
echo "To remove: crontab -r (CAUTION: removes all cron jobs)"
echo ""

# Test daily monitoring script
echo "Testing daily monitoring script..."
if bash "$PROJECT_DIR/scripts/daily_monitoring_check.sh" > /tmp/test_monitoring.log 2>&1; then
    echo "✅ Daily monitoring script test successful"
    echo "Preview:"
    head -30 /tmp/test_monitoring.log
else
    echo "⚠️  Daily monitoring script test had issues"
    echo "Check: /tmp/test_monitoring.log"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SETUP COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next automated check: Tomorrow at 8:00 AM"
echo "Next weekly report: Friday at 5:00 PM"
echo ""
