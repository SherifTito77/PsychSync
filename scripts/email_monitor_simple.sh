#!/bin/bash
# Simple Email Monitor - Runs once every 60 minutes
# Can be run as a cron job or background service

cd /Users/sheriftito/Downloads/psychsync

while true; do
    echo "📧 Email Monitor Check - $(date)"
    python3 - << 'PYEOF'
import imaplib
import email
from datetime import datetime, timedelta
from email.header import decode_header

EMAIL = "sherif.tito.77@gmail.com"
PASSWORD = "vuyq hopy idqp zhaa"

try:
    mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    mail.login(EMAIL, PASSWORD)
    mail.select("INBOX")

    # Get emails from last 60 minutes
    since = (datetime.now() - timedelta(minutes=60)).strftime("%d-%b-%Y %H:%M")
    status, messages = mail.search(None, f'(SINCE "{since}")')

    if status == "OK" and messages[0]:
        count = len(messages[0].split())
        print(f"✅ {count} new emails in last hour")

        if count > 50:
            print("⚠️  High email activity detected!")
    else:
        print("✅ No new emails in last hour")

    mail.logout()

except Exception as e:
    print(f"❌ Error: {e}")
PYEOF

    echo "⏳ Next check in 60 minutes..."
    sleep 3600  # Sleep for 1 hour
done
