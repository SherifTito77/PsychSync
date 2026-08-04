#!/usr/bin/env python3
"""
Scheduled Email Report Generator
Generates and emails PDF reports weekly/monthly
"""

import base64
import json
import os
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config.settings import settings


class ScheduledReportGenerator:
    """Generate and email scheduled reports"""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.report_from = os.getenv("REPORT_FROM", "noreply@psychsync.com")
        self.report_to = os.getenv("REPORT_TO", "sherif.tito.77@gmail.com")

    async def generate_report_data(self):
        """Fetch data for report"""
        db_url = str(settings.DATABASE_URL).replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        engine = create_async_engine(db_url, echo=False)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with async_session() as session:
            # Get user info
            user_query = text("SELECT id, email, full_name FROM users LIMIT 1")
            result = await session.execute(user_query)
            user = result.fetchone()

            # Get email connections
            conn_query = text(
                """
                SELECT email_address, provider, created_at
                FROM email_connections
                WHERE provider = 'IMAP'
                ORDER BY created_at DESC
            """
            )
            connections = await session.execute(conn_query)
            conn_list = connections.fetchall()

            # Get total email count (sample)
            stats = {
                "user_email": user[1] if user else "N/A",
                "user_name": user[2] if user else "User",
                "total_connections": len(conn_list),
                "accounts": [conn[0] for conn in conn_list],
                "generated_at": datetime.utcnow().isoformat(),
            }

        await engine.dispose()
        return stats

    def generate_html_report(self, stats, period="weekly"):
        """Generate HTML report content"""

        # Sample analytics data (in real implementation, this would come from actual monitoring logs)
        sample_analytics = {
            "total_emails": 62377,
            "emails_this_period": 987 if period == "weekly" else 4234,
            "daily_average": 141,
            "categories": {
                "security": 81,
                "financial": 29,
                "professional": 15,
                "social": 17,
                "promotional": 4,
                "other": 54,
            },
            "alerts": [
                "High security activity detected",
                "Financial activity above normal",
            ],
        }

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Email Monitoring Report - {period.title()}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .category-bar {{
            margin: 10px 0;
        }}
        .category-bar-fill {{
            height: 30px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .alert {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            color: #6c757d;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📧 Email Monitoring Report</h1>
        <p>Period: {period.title()} | Generated: {stats['generated_at']}</p>
        <p>Account: {stats['user_email']}</p>
    </div>

    <div class="section">
        <h2>📊 Overview</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-value">{sample_analytics['total_emails']:,}</div>
                <div class="metric-label">Total Emails</div>
            </div>
            <div class="metric">
                <div class="metric-value">{sample_analytics['emails_this_period']:,}</div>
                <div class="metric-label">This {period}</div>
            </div>
            <div class="metric">
                <div class="metric-value">{sample_analytics['daily_average']}</div>
                <div class="metric-label">Daily Average</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats['total_connections']}</div>
                <div class="metric-label">Accounts Connected</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📂 Email Categories</h2>
        {self._generate_category_html(sample_analytics['categories'])}
    </div>

    <div class="section">
        <h2>⚠️ Alerts & Insights</h2>
        {self._generate_alerts_html(sample_analytics['alerts'])}
    </div>

    <div class="section">
        <h2>💡 Recommendations</h2>
        <ul>
            <li>✅ Your security awareness is HIGH - continue monitoring alerts</li>
            <li>✅ Consider unsubscribing from promotional emails to reduce volume</li>
            <li>✅ Your financial activity is well-organized and tracked</li>
            <li>✅ Professional networking is moderate - consider increasing engagement</li>
        </ul>
    </div>

    <div class="footer">
        <p><strong>PsychSync Email Monitor</strong></p>
        <p>Report ID: {datetime.now().strftime('%Y%m%d%H%M%S')}</p>
        <p>Generated automatically • <a href="http://localhost:5173/email-monitoring">View Live Dashboard</a></p>
    </div>
</body>
</html>
        """

    def _generate_category_html(self, categories):
        """Generate category bars HTML"""
        total = sum(categories.values())
        html = ""

        for category, count in sorted(
            categories.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total) * 100
            html += f"""
            <div class="category-bar">
                <div class="category-bar-fill" style="width: {percentage}%">
                    {category.title()}: {count} ({percentage:.1f}%)
                </div>
            </div>
            """

        return html

    def _generate_alerts_html(self, alerts):
        """Generate alerts HTML"""
        if not alerts:
            return "<p>✅ No alerts - everything is normal!</p>"

        html = ""
        for alert in alerts:
            html += f'<div class="alert">⚠️ {alert}</div>'

        return html

    def send_email_report(self, html_content, period="weekly"):
        """Send report via email"""
        if not self.smtp_username or not self.smtp_password:
            print("⚠️ SMTP credentials not configured - skipping email send")
            print("Set SMTP_USERNAME and SMTP_PASSWORD environment variables")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📧 Your {period.title()} Email Report - PsychSync"
            msg["From"] = self.report_from
            msg["To"] = self.report_to

            # Attach HTML version
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Connect and send
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()

            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            print(f"✅ {period.title()} report sent to {self.report_to}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    async def generate_weekly_report(self):
        """Generate and send weekly report"""
        print("📊 Generating weekly report...")

        stats = await self.generate_report_data()
        html_content = self.generate_html_report(stats, "weekly")

        # Save to file
        filename = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.html"
        filepath = f"/tmp/{filename}"

        with open(filepath, "w") as f:
            f.write(html_content)

        print(f"📄 Report saved to {filepath}")

        # Send email
        self.send_email_report(html_content, "weekly")

        return filepath

    async def generate_monthly_report(self):
        """Generate and send monthly report"""
        print("📊 Generating monthly report...")

        stats = await self.generate_report_data()
        html_content = self.generate_html_report(stats, "monthly")

        # Save to file
        filename = f"monthly_report_{datetime.now().strftime('%Y%m')}.html"
        filepath = f"/tmp/{filename}"

        with open(filepath, "w") as f:
            f.write(html_content)

        print(f"📄 Report saved to {filepath}")

        # Send email
        self.send_email_report(html_content, "monthly")

        return filepath


# CLI interface
if __name__ == "__main__":
    import asyncio

    generator = ScheduledReportGenerator()

    if len(sys.argv) > 1:
        report_type = sys.argv[1]
    else:
        report_type = "weekly"

    if report_type == "weekly":
        asyncio.run(generator.generate_weekly_report())
    elif report_type == "monthly":
        asyncio.run(generator.generate_monthly_report())
    else:
        print("Usage: python3 scheduled_reports.py [weekly|monthly]")
