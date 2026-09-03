#!/bin/bash
# Setup scheduled memory leak monitoring
# Runs daily via cron

# Add to crontab
(crontab -l 2>/dev/null; echo "0 9 * * * cd $(pwd) && ./scripts/monitor-memory-leaks.sh >> /var/log/memory-leak-cron.log 2>&1") | crontab -

echo "✓ Scheduled monitoring configured (runs daily at 9 AM)"
echo "To view: crontab -l"
echo "To edit: crontab -e"
echo "To remove: crontab -r (then delete the line)"
