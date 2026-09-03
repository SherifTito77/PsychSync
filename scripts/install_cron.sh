#!/bin/bash
# Install PsychSync Credential Rotation Cron Job
# This script installs the automated credential rotation cron job

echo "🔧 Installing PsychSync Credential Rotation Cron Job"
echo "=" 60
echo ""

# Check if crontab exists
if ! crontab -l >/dev/null 2>&1; then
    echo "No existing crontab found. Creating new one..."
    NEW_CRON="true"
else
    echo "Existing crontab found. Will append to it."
    NEW_CRON="false"
fi

echo ""
echo "📋 Cron job to be installed:"
echo "----------------------------"
cat psychsync_cron.conf
echo "----------------------------"
echo ""

# Ask for confirmation
read -p "Install this cron job? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Installation cancelled."
    exit 1
fi

# Install cron job
if [ "$NEW_CRON" = "true" ]; then
    cat psychsync_cron.conf | crontab -
else
    (crontab -l; cat psychsync_cron.conf) | crontab -
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Cron job installed successfully!"
    echo ""
    echo "Current crontab:"
    crontab -l
    echo ""
    echo "💡 To uninstall: crontab -e (remove PsychSync lines)"
else
    echo ""
    echo "❌ Failed to install cron job."
    echo "You can manually install by running: crontab -e"
    echo "Then add the contents of psychsync_cron.conf"
    exit 1
fi
