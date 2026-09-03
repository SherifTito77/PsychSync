#!/bin/bash
# Install Email Monitor as macOS LaunchAgent

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$SCRIPT_DIR/com.psychsync.emailmonitor.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
SERVICE_PLIST="$LAUNCH_AGENTS_DIR/com.psychsync.emailmonitor.plist"

echo "╔════════════════════════════════════════════════════════╗"
echo "║   PSYCHSYNC EMAIL MONITOR - SERVICE INSTALLER          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if plist file exists
if [ ! -f "$PLIST_FILE" ]; then
    echo "❌ Error: Plist file not found at $PLIST_FILE"
    exit 1
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist file
echo "📋 Copying service file..."
cp "$PLIST_FILE" "$SERVICE_PLIST"

# Make monitor script executable
echo "🔧 Making monitor script executable..."
chmod +x "$SCRIPT_DIR/start_email_monitor.sh"

# Unload existing service if it's already loaded
if launchctl list | grep -q "com.psychsync.emailmonitor"; then
    echo "🔄 Unloading existing service..."
    launchctl unload "$SERVICE_PLIST" 2>/dev/null || true
fi

# Load the service
echo "🚀 Loading email monitor service..."
launchctl load "$SERVICE_PLIST"

# Start the service
echo "▶️  Starting email monitor service..."
launchctl start com.psychsync.emailmonitor 2>/dev/null

echo ""
echo "✅ Email Monitor Service Installed Successfully!"
echo ""
echo "📊 Service Details:"
echo "   Name: com.psychsync.emailmonitor"
echo "   Status: Running"
echo "   Logs: /tmp/psychsync_email_monitor.log"
echo ""
echo "🔧 Management Commands:"
echo "   Start:   launchctl start com.psychsync.emailmonitor"
echo "   Stop:    launchctl stop com.psychsync.emailmonitor"
echo "   Restart: launchctl kickstart -k gui/$UID/com.psychsync.emailmonitor"
echo "   Unload:  launchctl unload $SERVICE_PLIST"
echo ""
echo "💡 The service will automatically start on macOS login!"
