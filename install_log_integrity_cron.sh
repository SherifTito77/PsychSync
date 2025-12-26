#!/bin/bash
# Install log integrity cron job

# Read cron configuration
CRON_CONFIG=$(cat log_integrity_cron.conf)

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "log_integrity"; then
    echo "⚠️  Log integrity cron jobs already installed"
    echo "Run: crontab -l to view current jobs"
    exit 0
fi

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_CONFIG") | crontab -

echo "✅ Log integrity cron jobs installed"
echo "Run 'crontab -l' to verify"
