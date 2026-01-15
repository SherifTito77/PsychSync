#!/usr/bin/env python3
"""
Test script for crisis email delivery
Verifies SMTP configuration and email templates
"""

import asyncio
import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_smtp_connection():
    """Test SMTP connection and credentials"""
    print("\n" + "=" * 60)
    print("Crisis Email Delivery Test")
    print("=" * 60)

    try:
        from app.core.config import settings
        from app.services.email_service import EmailService

        print("\n1. Checking SMTP Configuration...")

        # Check configuration
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_tls = settings.SMTP_TLS

        if not smtp_host:
            print("  ❌ SMTP_HOST not configured")
            print("  → Please add SMTP_HOST to .env file")
            return False

        print(f"  ✅ SMTP Host: {smtp_host}")
        print(f"  ✅ SMTP Port: {smtp_port}")
        print(f"  ✅ SMTP User: {smtp_user}")
        print(f"  ✅ SMTP TLS: {smtp_tls}")

        # Test connection
        print("\n2. Testing SMTP Connection...")
        email_service = EmailService()

        # Try to send a test email
        test_email = "test@example.com"  # Replace with real email for testing
        print(f"\n3. Sending Test Email to: {test_email}")
        print("   (Replace with your email in the script to receive it)")

        success = await email_service.send_email(
            email_to=test_email,
            subject="🧪 PsychSync Crisis Email Test",
            body="""
This is a TEST email from PsychSync Crisis Intervention System.

If you receive this, email delivery is working correctly!

Test Details:
- System: PsychSync Clinical Screening
- Purpose: Crisis Intervention Email Test
- Time: {timestamp}

✅ Email delivery is operational.

This is only a test. No action required.
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

        if success:
            print("  ✅ Test email sent successfully!")
            print(f"  → Check {test_email} inbox (and spam folder)")
        else:
            print("  ❌ Failed to send test email")
            return False

        # Test crisis email template
        print("\n4. Testing Crisis Email Template...")

        crisis_success = await email_service.send_email(
            email_to=test_email,
            subject="🚨 TEST: Crisis Intervention Alert",
            body="""
═══════════════════════════════════════════════════════════
 🚨 URGENT: Crisis Intervention Required - TEST
═══════════════════════════════════════════════════════════

THIS IS A TEST ALERT - No action required

User: Test User
Email: test@example.com
Organization: Test Organization
Time: {timestamp}
Risk Level: CRITICAL

TEST DETAILS:
Recent suicide attempt reported on screening
PHQ-9 Score: 26/27 (Severe)
C-SSRS: Recent attempt (Q11 = Yes)

IMMEDIATE ACTIONS (Test):
1. ✓ Attempt to contact user by phone
2. ✓ Check if user is in immediate danger
3. ✓ Call 911 if imminent danger
4. ✓ Contact emergency services

CRISIS RESOURCES:
• 988 Suicide & Crisis Lifeline
• Crisis Text Line: Text HOME to 741741
• Emergency: 911

═══════════════════════════════════════════════════════════
This is a TEST. Real alerts will come from crisis-alerts@psychsync.ai
═══════════════════════════════════════════════════════════
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )

        if crisis_success:
            print("  ✅ Crisis email template sent successfully!")
        else:
            print("  ❌ Failed to send crisis template")
            return False

        return True

    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("  → Make sure you're in the project root directory")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test that all required configuration is present"""
    print("\n" + "=" * 60)
    print("SMTP Configuration Check")
    print("=" * 60)

    from app.core.config import settings

    required_vars = {
        "SMTP_HOST": settings.SMTP_HOST,
        "SMTP_PORT": settings.SMTP_PORT,
        "SMTP_USER": settings.SMTP_USER,
        "SMTP_PASSWORD": settings.SMTP_PASSWORD,
        "EMAILS_FROM_EMAIL": settings.EMAILS_FROM_EMAIL,
    }

    all_present = True
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"  ✅ {var_name}: {'*' * (len(str(var_value))-2) + str(var_value)[-2:] if 'PASSWORD' in var_name else var_value}")
        else:
            print(f"  ❌ {var_name}: NOT SET")
            all_present = False

    return all_present


async def main():
    """Run all email tests"""
    print("\n" + "🔧" * 30)
    print("Crisis Email System Test Suite")
    print("🔧" * 30)

    # Check configuration first
    config_ok = test_configuration()

    if not config_ok:
        print("\n" + "=" * 60)
        print("⚠️  SMTP Configuration Incomplete")
        print("=" * 60)
        print("\nTo configure SMTP, update your .env file:")
        print("""
# SMTP Configuration (using Gmail as example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password_here
EMAILS_FROM_EMAIL=your@gmail.com
EMAILS_FROM_NAME=PsychSync Crisis Team
ENABLE_EMAIL_VERIFICATION=true

# For production, use SendGrid, AWS SES, or Mailgun
# See CRISIS_EMAIL_SETUP_GUIDE.md for full instructions
        """)
        return 1

    # Test email delivery
    email_ok = await test_smtp_connection()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Configuration: {'✅' if config_ok else '❌'}")
    print(f"Email Delivery: {'✅' if email_ok else '❌'}")

    if config_ok and email_ok:
        print("\n✅ Email system is operational!")
        print("\nNext steps:")
        print("1. Update CRISIS_EMAIL_SETUP_GUIDE.md with your provider")
        print("2. Test with real crisis screening workflow")
        print("3. Setup monitoring for email delivery failures")
        return 0
    else:
        print("\n⚠️  Email system needs configuration")
        print("→ Follow CRISIS_EMAIL_SETUP_GUIDE.md for setup")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
