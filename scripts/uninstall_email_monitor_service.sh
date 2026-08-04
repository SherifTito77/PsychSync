#!/bin/bash
# Uninstall Email Monitor macOS LaunchAgent

SERVICE_PLIST="$HOME/Library/LaunchAgents/com.psychsync.emailmonitor.plist"

echo "╔════════════════════════════════════════════════════════╗"
echo "║   PSYCHSYNC EMAIL MONITOR - SERVICE UNINSTALLER        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if service is loaded
if launchctl list | grep -q "com.psychsync.emailmonitor"; then
    echo "🛑 Stopping email monitor service..."
    launchctl stop com.psychsync.emailmonitor 2>/dev/null || true

    echo "📋 Unloading service..."
    launchctl unload "$SERVICE_PLIST" 2>/dev/null || true
else
    echo "ℹ️  Service not currently loaded"
fi

# Remove plist file
if [ -f "$SERVICE_PLIST" ]; then
    echo "🗑️  Removing service file..."
    rm "$SERVICE_PLIST"
    echo "✅ Service file removed"
else
    echo "ℹ️  Service file not found"
fi

echo ""
echo "✅ Email Monitor Service Uninstalled Successfully!"
echo ""
echo "💡 The monitor will no longer start automatically."
echo "   You can still run it manually with ./scripts/start_email_monitor.sh"
