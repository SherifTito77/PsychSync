#!/bin/bash
# Email Monitor - Manual Start Script
# Run this to start monitoring your emails

echo "╔════════════════════════════════════════════════════════╗"
echo "║        📧 PSYCHSYNC EMAIL MONITOR                      ║"
echo "║        Automated Email Monitoring Service              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📧 Monitoring: sherif.tito.77@gmail.com"
echo "⏱️  Check Interval: Every 60 minutes"
echo "📅 Started at: $(date)"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /Users/sheriftito/Downloads/psychsync

while true; do
    echo ""
    echo "🔍 Checking emails... $(date '+%Y-%m-%d %H:%M:%S')"

    python3 - << 'PYEOF'
import imaplib
from datetime import datetime, timedelta

EMAIL = "sherif.tito.77@gmail.com"
PASSWORD = "vuyq hopy idqp zhaa"

try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, PASSWORD)
    mail.select("INBOX")

    # Get recent emails
    since = (datetime.now() - timedelta(hours=1)).strftime("%d-%b-%Y")
    status, messages = mail.search(None, f'(SINCE "{since}")')

    if status == "OK" and messages[0]:
        count = len(messages[0].split())
        print(f"   📧 {count} emails in last hour")

        if count > 50:
            print(f"   ⚠️  High activity alert!")
        elif count > 20:
            print(f"   📊 Moderate activity")
        else:
            print(f"   ✅ Normal activity")

    mail.logout()

except Exception as e:
    print(f"   ❌ Error: {e}")
PYEOF

    echo "⏳  Next check in 60 minutes..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    sleep 3600  # 1 hour
done
