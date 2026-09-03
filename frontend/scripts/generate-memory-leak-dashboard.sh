#!/bin/bash
# Generate memory leak dashboard report
# Output: HTML dashboard with metrics

REPORT_FILE="MEMORY_LEAK_DASHBOARD_$(date +%Y%m%d).html"

cat > "$REPORT_FILE" <<'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <title>Memory Leak Prevention Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .dashboard { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .metric { display: inline-block; margin: 20px; padding: 20px; background: #ecf0f1; border-radius: 8px; text-align: center; min-width: 200px; }
        .metric-label { font-size: 14px; color: #7f8c8d; }
        .metric-value { font-size: 32px; font-weight: bold; margin: 10px 0; }
        .good { color: #27ae60; }
        .warning { color: #f39c12; }
        .error { color: #e74c3c; }
        .section { margin: 30px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }
        .code-block { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 5px; overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>🔒 Memory Leak Prevention Dashboard</h1>
        <p><strong>Generated:</strong> $(date)</p>

        <div style="text-align: center; margin: 30px 0;">
HTMLEOF

# Run scan and get metrics
TOTAL_LEAKS=$(npm run lint 2>&1 | grep -c "memory-leak" || echo "0")
TIMER_LEAKS=$(npm run lint 2>&1 | grep -c "no-uncleaned-timers" || echo "0")
EVENT_LEAKS=$(npm run lint 2>&1 | grep -c "no-uncleaned-event-listeners" || echo "0")
WEBSOCKET_LEAKS=$(npm run lint 2>&1 | grep -c "no-uncleaned-websockets" || echo "0")

# Determine status
if [ "$TOTAL_LEAKS" -eq "0" ]; then
    STATUS="good"
    STATUS_TEXT="No Leaks"
    STATUS_EMOJI="✅"
else
    STATUS="warning"
    STATUS_TEXT="Leaks Found"
    STATUS_EMOJI="⚠️"
fi

cat >> "$REPORT_FILE" <<'HTMLEOF'
        <div class="metric">
            <div class="metric-label">Total Memory Leaks</div>
            <div class="metric-value $STATUS">$TOTAL_LEAKS</div>
            <div>$STATUS_EMOJI $STATUS_TEXT</div>
        </div>
        <div class="metric">
            <div class="metric-label">Timer Leaks</div>
            <div class="metric-value">$TIMER_LEAKS</div>
        </div>
        <div class="metric">
            <div class="metric-label">Event Listener Leaks</div>
            <div class="metric-value">$EVENT_LEAKS</div>
        </div>
        <div class="metric">
            <div class="metric-label">WebSocket Leaks</div>
            <div class="metric-value">$WEBSOCKET_LEAKS</div>
        </div>
    </div>

    <div class="section">
        <h2>📊 Breakdown by Type</h2>
        <table>
            <tr>
                <th>Type</th>
                <th>Count</th>
                <th>Severity</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Timer Leaks (setTimeout/setInterval)</td>
                <td>$TIMER_LEAKS</td>
                <td><span class="error">High</span></td>
                <td>$( [ $TIMER_LEAKS -eq 0 ] && echo '✅ Fixed' || echo '⚠️ Needs Fix' )</td>
            </tr>
            <tr>
                <td>Event Listener Leaks</td>
                <td>$EVENT_LEAKS</td>
                <td><span class="warning">Medium</span></td>
                <td>$( [ $EVENT_LEAKS -eq 0 ] && echo '✅ Fixed' || echo '⚠️ Needs Fix' )</td>
            </tr>
            <tr>
                <td>WebSocket Leaks</td>
                <td>$WEBSOCKET_LEAKS</td>
                <td><span class="error">High</span></td>
                <td>$( [ $WEBSOCKET_LEAKS -eq 0 ] && echo '✅ Fixed' || echo '⚠️ Needs Fix' )</td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>🛠️ Quick Actions</h2>
        <div class="code-block">
            <strong>Check for leaks:</strong><br>
            <code>npm run lint | grep "memory-leak"</code>
        </div>
        <br>
        <div class="code-block">
            <strong>Auto-fix:</strong><br>
            <code>./scripts/auto-fix-memory-leaks.sh</code>
        </div>
        <br>
        <div class="code-block">
            <strong>View guide:</strong><br>
            <code>cat ULTIMATE_QUICK_START.md</code>
        </div>
    </div>

    <div class="section">
        <h2>📚 Documentation</h2>
        <ul>
            <li><a href="ULTIMATE_QUICK_START.md">Quick Start Guide (10 min)</a></li>
            <li><a href="QUICK_REFERENCE_CARD.md">Reference Card (printable)</a></li>
            <li><a href="TEAM_TRAINING_MEMORY_LEAKS.md">Team Training (60 min)</a></li>
            <li><a href="MEMORY_LEAK_QUICKFIX_GUIDE.md">Fix Patterns</a></li>
            <li><a href="MIGRATION_CHECKLIST.md">Migration Checklist</a></li>
        </ul>
    </div>

    <div style="text-align: center; margin: 40px 0; color: #7f8c8d;">
        <p><em>Report generated by Memory Leak Prevention System</em></p>
        <p><strong>Next Scheduled Scan:</strong> $(date -v+1d)</p>
    </div>
</div>
</body>
</html>
HTMLEOF

echo "✓ Dashboard generated: $REPORT_FILE"
echo "  Open in browser to view: open $REPORT_FILE"
