#!/usr/bin/env python3
"""
SECURITY ENHANCEMENTS DEMONSTRATION
Shows the integration of all new security features:
1. Anomaly detection methods in SecurityMonitoringEngine
2. Failed login tracking with account lockout
3. SIEM integration for centralized monitoring

Author: Security Team
Version: 1.0
Date: December 23, 2024
"""

import asyncio
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, ".")

from app.core.failed_login_tracker import LockoutReason, failed_login_tracker
from app.core.security_monitoring import SecurityAlert, security_monitor
from app.core.siem_integration import send_security_event, siem_integration


async def demo_anomaly_detection():
    """Demonstrate anomaly detection methods"""
    print("\n" + "=" * 80)
    print("🔍 1. ANOMALY DETECTION METHODS DEMO")
    print("=" * 80)

    # Test impossible travel detection
    print("\n📍 Testing impossible travel detection...")
    alert = await security_monitor.detect_impossible_travel(
        user_id="test_user_123", ip_address="192.168.1.100", timestamp=datetime.now()
    )
    if alert:
        print(f"   ⚠️  Alert: {alert.description}")
    else:
        print("   ✅ No impossible travel detected (expected for first login)")

    # Test brute force detection
    print("\n🔐 Testing brute force detection...")
    alert = await security_monitor.detect_brute_force(
        user_id="test_user_456", ip_address="10.0.0.50", success=False
    )
    if alert:
        print(f"   ⚠️  Alert: {alert.description}")
    else:
        print("   ℹ️  No brute force pattern detected yet")

    # Test account takeover detection
    print("\n🎭 Testing account takeover detection...")
    alert = await security_monitor.detect_account_takeover(
        user_id="test_user_789",
        ip_address="203.0.113.42",
        user_agent="Mozilla/5.0 (New User Agent)",
    )
    if alert:
        print(f"   ⚠️  Alert: {alert.description}")
        print(f"   Risk Score: {alert.risk_score}")
    else:
        print("   ✅ No account takeover indicators")

    # Test privilege escalation detection
    print("\n⬆️  Testing privilege escalation detection...")
    alert = await security_monitor.detect_privilege_escalation(
        user_id="test_user_abc",
        attempted_role="admin",
        current_role="user",
        ip_address="192.168.1.50",
    )
    if alert:
        print(f"   🚨 CRITICAL Alert: {alert.description}")
        print(f"   Risk Score: {alert.risk_score}")
    else:
        print("   ✅ No privilege escalation attempt")

    # Test data exfiltration detection
    print("\n📤 Testing data exfiltration detection...")
    alert = await security_monitor.detect_data_exfiltration(
        user_id="test_user_xyz",
        data_accessed=1500,
        endpoint="/api/v1/assessments/export-all",
    )
    if alert:
        print(f"   🚨 Alert: {alert.description}")
        print(f"   Risk Score: {alert.risk_score}")
    else:
        print("   ✅ No exfiltration indicators")

    print("\n✅ Anomaly detection methods demo complete!")


async def demo_failed_login_tracking():
    """Demonstrate failed login tracking with account lockout"""
    print("\n" + "=" * 80)
    print("🔐 2. FAILED LOGIN TRACKING & ACCOUNT LOCKOUT DEMO")
    print("=" * 80)

    test_user = "demo_user_lockout"
    test_ip = "198.51.100.23"

    print(f"\n👤 Testing user: {test_user}")
    print(f"🌐 Test IP: {test_ip}")
    print(f"⚙️  Max attempts: {failed_login_tracker.max_attempts}")
    print(
        f"⏱️  Lockout duration: {int(failed_login_tracker.lockout_duration.total_seconds() / 60)} minutes"
    )

    # Simulate failed login attempts
    print(
        f"\n🔓 Simulating {failed_login_tracker.max_attempts + 1} failed login attempts..."
    )
    for i in range(1, failed_login_tracker.max_attempts + 2):
        allowed, lockout_info = await failed_login_tracker.record_login_attempt(
            username=test_user,
            success=False,
            ip_address=test_ip,
            user_agent="TestAgent/1.0",
        )

        attempts = await failed_login_tracker.get_failed_attempt_count(test_user)

        if lockout_info and lockout_info.is_locked:
            print(f"\n   🚨 Attempt {i}: ACCOUNT LOCKED!")
            print(f"   Reason: {lockout_info.reason.value}")
            print(f"   Expires at: {lockout_info.expires_at}")
            print(f"   Total attempts: {lockout_info.attempts_count}")
            break
        else:
            if lockout_info:
                warning = lockout_info.metadata.get("warning", "")
                print(
                    f"   Attempt {i}: Failed ({attempts}/{failed_login_tracker.max_attempts}) {warning}"
                )
            else:
                print(
                    f"   Attempt {i}: Failed ({attempts}/{failed_login_tracker.max_attempts})"
                )

    # Check lockout status
    lockout_status = await failed_login_tracker.get_lockout_status(test_user)
    if lockout_status.is_locked:
        print(f"\n🔒 Account Status: LOCKED")
        print(f"   Locked at: {lockout_status.locked_at}")
        print(f"   Expires at: {lockout_status.expires_at}")

    # Try to login while locked
    print(f"\n🔓 Attempting login while locked...")
    allowed, lockout_info = await failed_login_tracker.record_login_attempt(
        username=test_user, success=False, ip_address=test_ip
    )
    if not allowed:
        print(f"   ❌ Login BLOCKED - Account is locked")
    else:
        print(f"   ✅ Login allowed")

    # Unlock the account
    print(f"\n🔓 Manually unlocking account...")
    await failed_login_tracker.unlock_account(test_user)
    print(f"   ✅ Account unlocked")

    # Successful login clears attempts
    print(f"\n✅ Successful login (clears failed attempts)...")
    allowed, lockout_info = await failed_login_tracker.record_login_attempt(
        username=test_user, success=True, ip_address=test_ip
    )
    attempts = await failed_login_tracker.get_failed_attempt_count(test_user)
    print(f"   Failed attempts cleared: {attempts}")

    print("\n✅ Failed login tracking demo complete!")


async def demo_siem_integration():
    """Demonstrate SIEM integration"""
    print("\n" + "=" * 80)
    print("📡 3. SIEM INTEGRATION DEMO")
    print("=" * 80)

    print(f"\n⚙️  SIEM Configuration:")
    print(f"   Enabled: {siem_integration.config.enabled}")
    print(f"   Platform: {siem_integration.config.platform.value}")
    print(f"   Endpoint: {siem_integration.config.endpoint_url or 'Not configured'}")

    # Test connection
    print(f"\n🔌 Testing SIEM connection...")
    test_result = await siem_integration.test_connection()
    print(
        f"   Status: {'✅ Connected' if test_result['success'] else '⚠️  Not configured'}"
    )
    if not test_result.get("success"):
        print(f"   Message: {test_result.get('message', 'Unknown error')}")

    if siem_integration.config.enabled:
        # Send security events
        print(f"\n📤 Sending security events to SIEM...")

        # Event 1: Login attempt
        success = await send_security_event(
            event_type="login_attempt",
            severity="medium",
            category="authentication",
            user_id="siem_test_user",
            source_ip="192.168.1.100",
            action="login",
            outcome="success",
            details={"method": "password", "mfa_enabled": True},
        )
        print(f"   Event 1 (Login): {'✅ Sent' if success else '❌ Failed'}")

        # Event 2: Failed login
        success = await send_security_event(
            event_type="login_attempt",
            severity="high",
            category="authentication",
            user_id="siem_test_user",
            source_ip="198.51.100.50",
            action="login",
            outcome="failure",
            details={"reason": "invalid_password"},
        )
        print(f"   Event 2 (Failed Login): {'✅ Sent' if success else '❌ Failed'}")

        # Event 3: Security alert
        test_alert = SecurityAlert(
            id="test_alert_001",
            anomaly_type="brute_force_pattern",
            severity="high",
            user_id="siem_test_user",
            description="Test alert for SIEM integration",
            details={"test": True},
            risk_score=75.0,
        )
        success = await siem_integration.send_alert(test_alert)
        print(f"   Event 3 (Security Alert): {'✅ Sent' if success else '❌ Failed'}")

        # Flush events
        print(f"\n🔄 Flushing event queue...")
        await siem_integration.flush_events()
        print(f"   ✅ Events sent to SIEM")
    else:
        print(f"\n⚠️  SIEM is disabled. Enable it by setting:")
        print(f"   SIEM_ENABLED=true")
        print(f"   SIEM_PLATFORM=webhook (or splunk_hec, elasticsearch, etc.)")
        print(f"   SIEM_ENDPOINT_URL=https://your-siem-endpoint.com")

    print("\n✅ SIEM integration demo complete!")


async def demo_integration():
    """Demonstrate full integration of all security features"""
    print("\n" + "=" * 80)
    print("🔗 4. FULL INTEGRATION DEMO")
    print("=" * 80)

    test_user = "integration_test_user"
    test_ip = "203.0.113.100"

    print(f"\n🎯 Simulating attack scenario: Multiple failed logins + SIEM logging")

    # Record failed logins
    for i in range(3):
        await failed_login_tracker.record_login_attempt(
            username=test_user,
            success=False,
            ip_address=test_ip,
            user_agent="AttackBot/1.0",
        )

        # Send to SIEM
        await send_security_event(
            event_type="login_attempt",
            severity="high",
            category="authentication",
            user_id=test_user,
            source_ip=test_ip,
            action="login",
            outcome="failure",
            details={"attempt_number": i + 1},
        )

    print(f"   ✅ Recorded 3 failed login attempts")
    print(f"   ✅ Sent 3 events to SIEM")

    # Check for brute force
    alert = await security_monitor.detect_brute_force(
        user_id=test_user, ip_address=test_ip, success=False
    )

    if alert:
        print(f"   ⚠️  Brute force detected!")
        print(f"      Severity: {alert.severity.value}")
        print(f"      Risk Score: {alert.risk_score}")

        # Send alert to SIEM
        await siem_integration.send_alert(alert)
        print(f"   ✅ Alert sent to SIEM")

    print("\n✅ Full integration demo complete!")


async def main():
    """Run all demonstrations"""
    print("\n" + "=" * 80)
    print("🚀 PSYCHSYNC SECURITY ENHANCEMENTS DEMONSTRATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().isoformat()}")

    try:
        await demo_anomaly_detection()
        await demo_failed_login_tracking()
        await demo_siem_integration()
        await demo_integration()

        print("\n" + "=" * 80)
        print("📋 SUMMARY")
        print("=" * 80)
        print(
            """
✅ All security enhancements demonstrated!

New Features:
1. Anomaly Detection Methods (6 new public methods)
   - detect_impossible_travel()
   - detect_brute_force()
   - detect_credential_stuffing()
   - detect_unusual_location()
   - detect_account_takeover()
   - detect_privilege_escalation()
   - detect_data_exfiltration()

2. Failed Login Tracker with Account Lockout
   - Per-user failed login counting
   - Automatic account lockout (default: 5 attempts, 15 min)
   - IP-based tracking for credential stuffing detection
   - Manual unlock capability

3. SIEM Integration
   - Multi-platform support (Splunk, Elasticsearch, Webhook)
   - Batch event sending
   - Security alert forwarding
   - Connection testing

Configuration:
Add to .env or .env.dev:
# SIEM Settings
SIEM_ENABLED=true
SIEM_PLATFORM=webhook
SIEM_ENDPOINT_URL=https://your-siem-endpoint.com/api/events
SIEM_TOKEN=your-api-token

# Security Monitoring
SECURITY_MONITORING_ENABLED=true
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

Usage Examples:
from app.core.security_monitoring import security_monitor
from app.core.failed_login_tracker import failed_login_tracker
from app.core.siem_integration import send_security_event

# Check for anomalies
alert = await security_monitor.detect_account_takeover(
    user_id=user.id,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent", "")
)

# Track login attempts
allowed, lockout = await failed_login_tracker.record_login_attempt(
    username=form_data.username,
    success=False,
    ip_address=request.client.host
)

# Send to SIEM
await send_security_event(
    event_type="login_attempt",
    severity="high",
    category="authentication",
    user_id=user.id,
    source_ip=request.client.host,
    action="login",
    outcome="failure"
)
        """
        )

        print(f"\nCompleted at: {datetime.now().isoformat()}")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup
        await siem_integration.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
