#!/usr/bin/env python3
"""
Automated Email Monitoring Script
Periodically checks for new emails and generates reports
"""

import email
import imaplib
import json
import os
import sys
import time
from datetime import datetime, timedelta
from email.header import decode_header

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config.settings import settings

# Email credentials
EMAIL_ADDR = "sherif.tito.77@gmail.com"
PASSWORD = "vuyq hopy idqp zhaa"

# Monitoring settings
CHECK_INTERVAL_MINUTES = 60  # Check every hour
ALERT_THRESHOLDS = {
    "security_alerts": 5,  # Alert if > 5 security emails in an hour
    "new_senders": 10,  # Alert if > 10 new unique senders
}


def decode_header_value(header_value):
    """Decode email header value"""
    if not header_value:
        return ""
    decoded = decode_header(header_value)[0][0]
    if isinstance(decoded, bytes):
        decoded = decoded.decode("utf-8", errors="ignore")
    return decoded


def fetch_recent_emails(mail, minutes_back=60):
    """Fetch emails from the last N minutes"""
    since_date = (datetime.now() - timedelta(minutes=minutes_back)).strftime(
        "%d-%b-%Y %H:%M"
    )
    status, messages = mail.search(None, f'(SINCE "{since_date}")')

    emails = []
    if status == "OK" and messages[0]:
        email_ids = messages[0].split()

        for email_id in email_ids:
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    email_data = {
                        "id": email_id.decode(),
                        "from": msg.get("From", ""),
                        "subject": decode_header_value(msg.get("Subject")),
                        "date": msg.get("Date", ""),
                        "to": msg.get("To", ""),
                    }
                    emails.append(email_data)

    return emails


def analyze_email_patterns(emails):
    """Analyze email patterns and detect anomalies"""
    analysis = {
        "total_emails": len(emails),
        "categories": {
            "security": 0,
            "financial": 0,
            "professional": 0,
            "social": 0,
            "promotional": 0,
            "other": 0,
        },
        "unique_senders": set(),
        "alerts": [],
    }

    for email_data in emails:
        from_addr = email_data["from"].lower()
        subject = email_data["subject"].lower()

        # Track unique senders
        if "<" in from_addr:
            sender = from_addr.split("<")[1].split(">")[0]
        else:
            sender = from_addr.split("@")[0] if "@" in from_addr else from_addr
        analysis["unique_senders"].add(sender)

        # Categorize emails
        if any(
            term in from_addr + subject
            for term in ["security", "alert", "sign-in", "login"]
        ):
            analysis["categories"]["security"] += 1
        elif any(
            term in from_addr for term in ["bank", "financial", "payment", "transfer"]
        ):
            analysis["categories"]["financial"] += 1
        elif any(term in from_addr for term in ["linkedin", "indeed", "recruit"]):
            analysis["categories"]["professional"] += 1
        elif any(
            term in from_addr for term in ["facebook", "twitter", "reddit", "instagram"]
        ):
            analysis["categories"]["social"] += 1
        elif any(term in from_addr for term in ["newsletter", "promo", "deal"]):
            analysis["categories"]["promotional"] += 1
        else:
            analysis["categories"]["other"] += 1

    # Generate alerts
    analysis["unique_senders_count"] = len(analysis["unique_senders"])

    if analysis["categories"]["security"] > ALERT_THRESHOLDS["security_alerts"]:
        analysis["alerts"].append(
            f"⚠️  HIGH security activity: {analysis['categories']['security']} security emails"
        )

    if analysis["unique_senders_count"] > ALERT_THRESHOLDS["new_senders"]:
        analysis["alerts"].append(
            f"📈 Many new contacts: {analysis['unique_senders_count']} unique senders"
        )

    return analysis


def save_monitoring_log(analysis):
    """Save monitoring results to database"""
    try:
        db_url = str(settings.DATABASE_URL).replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        engine = create_async_engine(db_url, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async def save_log():
            async with async_session() as session:
                # Get user ID
                user_query = text("SELECT id FROM users WHERE email = :email")
                result = await session.execute(user_query, {"email": EMAIL_ADDR})
                user_row = result.fetchone()

                if user_row:
                    user_id = str(user_row[0])

                    # Insert monitoring log
                    insert_query = text(
                        """
                        INSERT INTO email_monitoring_logs
                        (user_id, timestamp, emails_processed, categories, alerts, metadata)
                        VALUES (:user_id, :timestamp, :emails_processed, :categories, :alerts, :metadata)
                    """
                    )

                    await session.execute(
                        insert_query,
                        {
                            "user_id": user_id,
                            "timestamp": datetime.utcnow(),
                            "emails_processed": analysis["total_emails"],
                            "categories": json.dumps(analysis["categories"]),
                            "alerts": json.dumps(analysis["alerts"]),
                            "metadata": json.dumps(
                                {
                                    "unique_senders": analysis["unique_senders_count"],
                                    "check_interval_minutes": CHECK_INTERVAL_MINUTES,
                                }
                            ),
                        },
                    )

                    await session.commit()

        import asyncio

        asyncio.run(save_log())

    except Exception as e:
        print(f"⚠️  Could not save monitoring log: {e}")


def print_monitoring_report(analysis):
    """Print monitoring report"""
    print("\n" + "=" * 60)
    print(
        f"📧 EMAIL MONITORING REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print("=" * 60)

    print(f"\n📊 Emails Processed: {analysis['total_emails']}")

    print(f"\n📂 Categories:")
    for category, count in analysis["categories"].items():
        if count > 0:
            print(f"   {category.title()}: {count}")

    print(f"\n👥 Unique Senders: {analysis['unique_senders_count']}")

    if analysis["alerts"]:
        print(f"\n⚠️  ALERTS:")
        for alert in analysis["alerts"]:
            print(f"   {alert}")
    else:
        print(f"\n✅ No alerts - Email activity is normal")

    print("=" * 60)


def main():
    """Main monitoring loop"""
    print("🚀 Email Monitor Started")
    print(f"⏱️  Checking every {CHECK_INTERVAL_MINUTES} minutes")
    print(f"📧 Monitoring: {EMAIL_ADDR}")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        try:
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            mail.login(EMAIL_ADDR, PASSWORD)
            mail.select("INBOX")

            # Fetch recent emails
            recent_emails = fetch_recent_emails(
                mail, minutes_back=CHECK_INTERVAL_MINUTES
            )

            # Analyze patterns
            analysis = analyze_email_patterns(recent_emails)

            # Print report
            print_monitoring_report(analysis)

            # Save to database
            save_monitoring_log(analysis)

            # Logout
            mail.logout()

            # Wait for next check
            print(f"⏳ Next check in {CHECK_INTERVAL_MINUTES} minutes...\n")
            time.sleep(CHECK_INTERVAL_MINUTES * 60)

        except KeyboardInterrupt:
            print("\n\n👋 Email Monitor Stopped")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("🔄 Retrying in 60 seconds...\n")
            time.sleep(60)


if __name__ == "__main__":
    main()
