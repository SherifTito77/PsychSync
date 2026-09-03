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
