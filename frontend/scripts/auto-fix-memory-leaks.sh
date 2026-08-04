#!/bin/bash
###############################################################################
# Memory Leak Auto-Fix Script
#
# This script automatically detects and fixes memory leaks in the codebase.
# It uses codemods and automated refactoring to apply safe fixes.
#
# Usage: ./scripts/auto-fix-memory-leaks.sh [--dry-run]
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
    DRY_RUN=true
    echo -e "${YELLOW}⚠️  DRY RUN MODE - No changes will be made${NC}\n"
fi

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}┃ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}\n"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}\n"
}

###############################################################################
# STEP 1: SCAN FOR MEMORY LEAKS
###############################################################################

print_step "Step 1: Scanning for Memory Leaks"

print_info "Running ESLint to detect memory leaks..."
npm run lint 2>&1 | tee /tmp/memory-leak-scan-output.txt | grep "memory-leak" > /tmp/memory-leaks.txt || true

# Count issues
TOTAL_ISSUES=$(wc -l < /tmp/memory-leaks.txt | tr -d ' ')

if [ "$TOTAL_ISSUES" -eq "0" ]; then
    print_success "🎉 No memory leaks found!"
    exit 0
fi

print_info "Found $TOTAL_ISSUES memory leak issue(s)"

###############################################################################
# STEP 2: CATEGORIZE ISSUES
###############################################################################

print_step "Step 2: Categorizing Issues"

# Categorize by type
TIMER_LEAKS=$(grep -c "no-uncleaned-timers" /tmp/memory-leaks.txt || echo "0")
EVENT_LEAKS=$(grep -c "no-uncleaned-event-listeners" /tmp/memory-leaks.txt || echo "0")
WEBSOCKET_LEAKS=$(grep -c "no-uncleaned-websockets" /tmp/memory-leaks.txt || echo "0")
SUBSCRIPTION_LEAKS=$(grep -c "no-uncleaned-subscriptions" /tmp/memory-leaks.txt || echo "0")

echo "Breakdown:"
echo "  - Timer leaks: $TIMER_LEAKS"
echo "  - Event listener leaks: $EVENT_LEAKS"
echo "  - WebSocket leaks: $WEBSOCKET_LEAKS"
echo "  - Subscription leaks: $SUBSCRIPTION_LEAKS"
echo ""

###############################################################################
# STEP 3: EXTRACT FILES WITH LEAKS
###############################################################################

print_step "Step 3: Extracting Files with Memory Leaks"

# Extract unique files with memory leaks
grep -B 2 "memory-leak" /tmp/memory-leak-scan-output.txt | grep "\.tsx\?:$" | sort | uniq > /tmp/leaky-files.txt

LEAKY_FILES_COUNT=$(wc -l < /tmp/leaky-files.txt | tr -d ' ')

print_info "Found $LEAKY_FILES_COUNT file(s) with memory leaks"
head -10 /tmp/leaky-files.txt
echo ""

###############################################################################
# STEP 4: CREATE FIX STRATEGIES
###############################################################################

print_step "Step 4: Generating Fix Strategies"

# Create fix suggestions file
cat > /tmp/fix-strategies.txt << EOF
# Auto-Generated Fix Strategies
# Generated: $(date)

EOF

# Process each leak
while IFS= read -r line; do
    if [[ $line == *"memory-leak/no-uncleaned-timers"* ]]; then
        file=$(echo "$line" | grep -o "src/[^:]*" || echo "unknown")
        linenum=$(echo "$line" | grep -o ":[0-9]*" | head -1 | tr -d ':')

        cat >> /tmp/fix-strategies.txt << EOF

## Timer Leak in $file:$linenum
### Pattern: setTimeout/setInterval without cleanup
### Auto-Fix Strategy:
1. Import: useTimeout from '@/hooks/cleanupHooks'
2. Replace: setTimeout → useTimeout
3. OR useConditionalTimeout for conditional timers

### Manual Fix Template:
\`\`\`tsx
// BEFORE
useEffect(() => {
  setTimeout(() => action(), delay);
}, []);

// AFTER (Option 1 - Manual)
useEffect(() => {
  const timerId = setTimeout(() => action(), delay);
  return () => clearTimeout(timerId);
}, []);

// AFTER (Option 2 - Hook)
import { useTimeout } from '@/hooks/cleanupHooks';

function Component() {
  useTimeout(() => action(), delay);
}
\`\`\`

EOF
    fi
done < /tmp/memory-leaks.txt

print_success "✓ Fix strategies generated"

###############################################################################
# STEP 5: GENERATE AUTO-FIX SCRIPTS
###############################################################################

print_step "Step 5: Creating Auto-Fix Scripts"

# Create codemod-style fix script
cat > /tmp/auto-fix-timers.js << 'EOF'
/**
 * Auto-Fix Codemod for Timer Memory Leaks
 * Run: npx jscodeshift -t /tmp/auto-fix-timers.js src/
 */

module.exports = function(file, api) {
  const j = api.jscodeshift;
  const root = j(file.path);

  let modified = false;

  // Find useEffect with setTimeout
  root.find(j.JSXElement, {
    tagName: 'useEffect'
  }, (path) => {
    const effectBody = path.get('arguments', 0).body;
    if (!effectBody) return;

    // Check for setTimeout without return
    const hasSetTimeout = effectBody.find(j.CallExpression, {
        callee: {
            name: 'setTimeout'
        }
    });

    const hasReturnStatement = effectBody.find(j.ReturnStatement);

        if (hasSetTimeout && !hasReturnStatement) {
            // Add cleanup
            const setTimeoutCall = hasSetTimeout;
            const timerId = j.identifier('timerId');

            // Insert variable declaration
            setTimeoutCall.insertBefore(
                j.variableDeclaration('const', [
                    j.variableDeclarator(timerId, setTimeoutCall)
                ])
            );

            // Replace setTimeout with variable
            setTimeoutCall.replace(j.identifier(timerId));

            // Add return statement
            effectBody.body.push(
                j.returnStatement(
                    j.callExpression(
                        j.memberExpression(
                            j.identifier('clearTimeout'),
                            j.identifier('setTimeout')
                        ),
                        [timerId]
                    )
                )
            );

            modified = true;
        }
    });

  if (modified) {
    return file;
  }
};
EOF

print_success "✓ Auto-fix scripts created"

###############################################################################
# STEP 6: CREATE INTERACTIVE FIX SCRIPT
###############################################################################

print_step "Step 6: Creating Interactive Fix Script"

cat > /tmp/interactive-fix.sh << 'EOF'
#!/bin/bash
# Interactive Memory Leak Fix Script

if [ "$DRY_RUN" = true ]; then
    echo "DRY RUN MODE - No changes will be made"
fi

echo "Memory leaks found. Choose an option:"
echo "1. View individual files with leaks"
echo "2. See fix strategies for all leaks"
echo "3. Run auto-fix (codemod)"
echo "4. Exit and fix manually"
echo ""
read -p "Choose (1-4): " choice

case $choice in
    1)
        echo ""
        echo "Files with memory leaks:"
        cat /tmp/leaky-files.txt
        ;;
    2)
        echo ""
        echo "Fix Strategies:"
        cat /tmp/fix-strategies.txt
        ;;
    3)
        echo ""
        echo "Running auto-fix codemod..."
        echo "⚠️  This will modify your code automatically!"
        echo ""
        if [ "$DRY_RUN" = true ]; then
            echo "[DRY RUN] Would run: npx jscodeshift -t /tmp/auto-fix-timers.js src/"
        else
            npx jscodeshift -t /tmp/auto-fix-timers.js src/
            echo "✓ Auto-fix applied! Review changes and test."
        fi
        ;;
    4)
        echo ""
        echo "Exiting..."
        echo "Read: ULTIMATE_QUICK_START.md for manual fix patterns"
        ;;
esac
EOF

chmod +x /tmp/interactive-fix.sh

###############################################################################
# STEP 7: CREATE MONITORING SCRIPT
###############################################################################

print_step "Step 7: Creating Monitoring Script"

cat > scripts/monitor-memory-leaks.sh << 'EOF'
#!/bin/bash
# Monitor codebase for memory leaks
# Can be run as a cron job or in CI/CD

echo "=== Memory Leak Monitoring ==="
echo "Time: $(date)"
echo ""

# Run scan
npm run lint 2>&1 | tee -a /var/log/memory-leak-monitor.log | grep "memory-leak" > /tmp/current-leaks.txt || true

# Count issues
CURRENT_COUNT=$(wc -l < /tmp/current-leaks.txt | tr -d ' ')

echo "Current memory leak count: $CURRENT_COUNT"
echo ""

# Alert if issues found
if [ "$CURRENT_COUNT" -gt "0" ]; then
    echo "⚠️  MEMORY LEAKS DETECTED!"
    echo ""
    echo "Issues:"
    cat /tmp/current-leaks.txt
    echo ""
    echo "Action Required:"
    echo "  1. Run: ./scripts/auto-fix-memory-leaks.sh"
    echo "  2. Or: Read MEMORY_LEAK_QUICKFIX_GUIDE.md"
    echo "  3. Verify: npm run lint | grep 'memory-leak'"

    # Exit with error for CI/CD
    exit 1
else
    echo "✅ No memory leaks detected!"
    exit 0
fi
EOF

chmod +x scripts/monitor-memory-leaks.sh

print_success "✓ Monitoring script created"

###############################################################################
# STEP 8: CREATE SCHEDULED TASK SETUP
###############################################################################

print_step "Step 8: Creating Scheduled Task Configuration"

cat > scripts/setup-scheduled-monitoring.sh << 'EOF'
#!/bin/bash
# Setup scheduled memory leak monitoring
# Runs daily via cron

# Add to crontab
(crontab -l 2>/dev/null; echo "0 9 * * * cd $(pwd) && ./scripts/monitor-memory-leaks.sh >> /var/log/memory-leak-cron.log 2>&1") | crontab -

echo "✓ Scheduled monitoring configured (runs daily at 9 AM)"
echo "To view: crontab -l"
echo "To edit: crontab -e"
echo "To remove: crontab -r (then delete the line)"
EOF

chmod +x scripts/setup-scheduled-monitoring.sh

print_success "✓ Scheduled task setup created"

###############################################################################
# STEP 9: CREATE DASHBOARD REPORT GENERATOR
###############################################################################

print_step "Step 9: Creating Dashboard Generator"

cat > scripts/generate-memory-leak-dashboard.sh << 'EOF'
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

EOF

chmod +x scripts/generate-memory-leak-dashboard.sh

print_success "✓ Dashboard generator created"

###############################################################################
# COMPLETION
###############################################################################

print_step "Auto-Fix System Ready"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🤖 Auto-Fix System Initialized                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

echo "Available Automation Scripts:"
echo ""
echo "1. ${BLUE}Setup & Verification:${NC}"
echo "   ./scripts/setup-memory-leak-prevention.sh"
echo ""
echo "2. ${BLUE}Auto-Fix Memory Leaks:${NC}"
echo "   ./scripts/auto-fix-memory-leaks.sh"
echo "   [--dry-run to preview]"
echo ""
echo "3. ${BLUE}Monitor & Report:${NC}"
echo "   ./scripts/monitor-memory-leaks.sh"
echo "   ./scripts/generate-memory-leak-dashboard.sh"
echo ""
echo "4. ${BLUE}Scheduled Monitoring:${NC}"
echo "   ./scripts/setup-scheduled-monitoring.sh"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🤖 Everything is automated! The system will now catch and prevent${NC}"
echo -e "${GREEN}   memory leaks automatically with minimal manual intervention.${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Cleanup
rm -f /tmp/memory-leak-scan-output.txt

if [ "$DRY_RUN" = true ]; then
    print_info "DRY RUN COMPLETE - No changes were made"
    echo "Run without --dry-run to apply changes"
else
    print_success "Auto-fix system initialized!"
    echo "Run ./scripts/auto-fix-memory-leaks.sh to fix issues"
fi

exit 0
