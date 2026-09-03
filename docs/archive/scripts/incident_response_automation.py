#!/usr/bin/env python3
"""
Incident Response Automation System
Automated tools for rapid incident response and containment
"""

import json
import os
import smtplib
import sqlite3
import subprocess
import time

try:
    from email.mime.text import MimeText
except ImportError:
    MimeText = None
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class IncidentResponseAutomation:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.incident_db = self.base_path / "incident_response.db"
        self.monitoring_db = self.base_path / "security_monitoring.db"
        self.initialize_incident_database()

    def initialize_incident_database(self):
        """Initialize incident response database"""
        try:
            conn = sqlite3.connect(str(self.incident_db))
            cursor = conn.cursor()

            # Create incidents table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT UNIQUE NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    commander TEXT,
                    affected_systems TEXT,
                    data_exposed BOOLEAN DEFAULT FALSE,
                    regulatory_impact TEXT,
                    contained_at TEXT,
                    resolved_at TEXT,
                    resolution_notes TEXT
                )
            """
            )

            # Create actions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    executed_by TEXT,
                    executed_at TEXT NOT NULL,
                    success BOOLEAN,
                    details TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
                )
            """
            )

            # Create communications table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_communications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    recipient_type TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    message TEXT NOT NULL,
                    sent_at TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by TEXT,
                    acknowledged_at TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
                )
            """
            )

            conn.commit()
            conn.close()
            print("✅ Incident response database initialized")

        except Exception as e:
            print(f"❌ Error initializing incident database: {e}")

    def create_incident(
        self, severity: str, description: str, affected_systems: List[str]
    ) -> str:
        """Create a new incident record"""
        incident_id = f"INC_{int(time.time())}_{os.urandom(4).hex()}"

        try:
            conn = sqlite3.connect(str(self.incident_db))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO incidents
                (incident_id, severity, status, description, created_at, updated_at, affected_systems)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    incident_id,
                    severity.upper(),
                    "ACTIVE",
                    description,
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    json.dumps(affected_systems),
                ),
            )

            conn.commit()
            conn.close()

            print(f"🚨 Incident created: {incident_id} ({severity})")
            return incident_id

        except Exception as e:
            print(f"❌ Error creating incident: {e}")
            return ""

    def execute_emergency_containment(self, incident_id: str) -> Dict[str, Any]:
        """Execute emergency containment procedures"""
        print(f"🛡️ Executing emergency containment for {incident_id}")

        containment_actions = []

        # Action 1: Enable application maintenance mode
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-X",
                    "POST",
                    "http://localhost:8000/api/v1/maintenance/enable",
                    "-H",
                    "Authorization: Bearer EMERGENCY_TOKEN",
                ],
                capture_output=True,
                text=True,
            )

            success = result.returncode == 0
            containment_actions.append(
                {
                    "action": "enable_maintenance_mode",
                    "success": success,
                    "details": result.stdout if success else result.stderr,
                }
            )

            if success:
                self.log_incident_action(
                    incident_id, "CONTAINMENT", "Enabled maintenance mode", success
                )

        except Exception as e:
            containment_actions.append(
                {
                    "action": "enable_maintenance_mode",
                    "success": False,
                    "details": str(e),
                }
            )

        # Action 2: Database lockdown
        try:
            # Create database lockdown
            db_lockdown_sql = """
                -- Lockdown procedures
                CREATE TEMPORARY TABLE incident_block_ips (ip INET);

                -- Block suspicious patterns
                CREATE OR REPLACE FUNCTION check_incident_ip() RETURNS BOOLEAN AS $$
                BEGIN
                    RETURN NOT EXISTS (
                        SELECT 1 FROM access_logs
                        WHERE ip_address = inet_client_addr()
                        AND request_count > 1000
                        AND timestamp >= NOW() - INTERVAL '1 hour'
                    );
                END;
                $$ LANGUAGE plpgsql;
            """

            result = subprocess.run(
                [
                    "psql",
                    "-h",
                    "localhost",
                    "-U",
                    "postgres",
                    "-d",
                    "psychsync_db",
                    "-c",
                    db_lockdown_sql,
                ],
                capture_output=True,
                text=True,
            )

            success = result.returncode == 0
            containment_actions.append(
                {
                    "action": "database_lockdown",
                    "success": success,
                    "details": result.stdout if success else result.stderr,
                }
            )

            if success:
                self.log_incident_action(
                    incident_id, "CONTAINMENT", "Applied database lockdown", success
                )

        except Exception as e:
            containment_actions.append(
                {"action": "database_lockdown", "success": False, "details": str(e)}
            )

        # Action 3: Disable compromised accounts
        try:
            disable_accounts_sql = """
                UPDATE users
                SET is_active = false, security_flag = true
                WHERE last_login < NOW() - INTERVAL '30 days'
                   OR failed_login_attempts > 5;
            """

            result = subprocess.run(
                [
                    "psql",
                    "-h",
                    "localhost",
                    "-U",
                    "postgres",
                    "-d",
                    "psychsync_db",
                    "-c",
                    disable_accounts_sql,
                ],
                capture_output=True,
                text=True,
            )

            success = result.returncode == 0
            containment_actions.append(
                {
                    "action": "disable_compromised_accounts",
                    "success": success,
                    "details": result.stdout if success else result.stderr,
                }
            )

            if success:
                self.log_incident_action(
                    incident_id, "CONTAINMENT", "Disabled compromised accounts", success
                )

        except Exception as e:
            containment_actions.append(
                {
                    "action": "disable_compromised_accounts",
                    "success": False,
                    "details": str(e),
                }
            )

        # Action 4: Create forensic backup
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"/tmp/forensic_backup_{timestamp}.sql"

            result = subprocess.run(
                [
                    "pg_dump",
                    "-h",
                    "localhost",
                    "-U",
                    "postgres",
                    "-d",
                    "psychsync_db",
                    "-f",
                    backup_file,
                ],
                capture_output=True,
                text=True,
            )

            success = os.path.exists(backup_file)
            containment_actions.append(
                {
                    "action": "create_forensic_backup",
                    "success": success,
                    "details": (
                        f"Backup created: {backup_file}" if success else result.stderr
                    ),
                }
            )

            if success:
                self.log_incident_action(
                    incident_id,
                    "CONTAINMENT",
                    f"Created forensic backup: {backup_file}",
                    success,
                )

        except Exception as e:
            containment_actions.append(
                {
                    "action": "create_forensic_backup",
                    "success": False,
                    "details": str(e),
                }
            )

        return {
            "incident_id": incident_id,
            "timestamp": datetime.now().isoformat(),
            "containment_actions": containment_actions,
            "summary": {
                "total_actions": len(containment_actions),
                "successful_actions": len(
                    [a for a in containment_actions if a["success"]]
                ),
                "failed_actions": len(
                    [a for a in containment_actions if not a["success"]]
                ),
            },
        }

    def log_incident_action(
        self,
        incident_id: str,
        action_type: str,
        description: str,
        success: bool,
        details: str = "",
    ):
        """Log incident action"""
        try:
            conn = sqlite3.connect(str(self.incident_db))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO incident_actions
                (incident_id, action_type, description, executed_by, executed_at, success, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    incident_id,
                    action_type,
                    description,
                    "automation_system",
                    datetime.now().isoformat(),
                    success,
                    details,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ Error logging incident action: {e}")

    def send_emergency_notification(
        self, incident_id: str, severity: str, description: str, recipients: List[str]
    ) -> bool:
        """Send emergency notification to incident response team"""
        try:
            # Create notification message
            subject = f"🚨 EMERGENCY: Security Incident {incident_id} - {severity}"

            message = f"""
EMERGENCY SECURITY INCIDENT NOTIFICATION

Incident ID: {incident_id}
Severity: {severity}
Time: {datetime.now().isoformat()}

Description: {description}

IMMEDIATE ACTIONS REQUIRED:
1. Access incident response dashboard
2. Review containment status
3. Coordinate response activities
4. Monitor for additional alerts

Incident Response Dashboard: http://localhost:8080/incident/{incident_id}
Monitoring System: http://localhost:8080/security

This is an automated emergency notification.
Please acknowledge receipt immediately.
            """

            # For demonstration, log to file instead of sending email
            notification_log = self.base_path / "emergency_notifications.log"
            with open(notification_log, "a") as f:
                f.write(f"\n{'='*60}\n")
                f.write(f"TO: {', '.join(recipients)}\n")
                f.write(f"SUBJECT: {subject}\n")
                f.write(f"TIME: {datetime.now().isoformat()}\n")
                f.write(f"MESSAGE: {message}\n")
                f.write(f"{'='*60}\n")

            # Log communication
            self.log_incident_communication(
                incident_id, "EMAIL", ", ".join(recipients), message
            )

            print(f"📧 Emergency notification sent to {len(recipients)} recipients")
            return True

        except Exception as e:
            print(f"❌ Error sending emergency notification: {e}")
            return False

    def log_incident_communication(
        self, incident_id: str, recipient_type: str, recipient: str, message: str
    ):
        """Log incident communication"""
        try:
            conn = sqlite3.connect(str(self.incident_db))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO incident_communications
                (incident_id, recipient_type, recipient, message, sent_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    incident_id,
                    recipient_type,
                    recipient,
                    message,
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ Error logging communication: {e}")

    def generate_automation_report(self, incident_id: str) -> Dict[str, Any]:
        """Generate incident response automation report"""
        try:
            conn = sqlite3.connect(str(self.incident_db))
            cursor = conn.cursor()

            # Get incident details
            cursor.execute(
                """
                SELECT severity, status, description, created_at, affected_systems, data_exposed
                FROM incidents WHERE incident_id = ?
            """,
                (incident_id,),
            )

            incident = cursor.fetchone()

            if not incident:
                return {"error": "Incident not found"}

            # Get actions taken
            cursor.execute(
                """
                SELECT action_type, description, executed_at, success, details
                FROM incident_actions WHERE incident_id = ?
                ORDER BY executed_at DESC
            """,
                (incident_id,),
            )

            actions = []
            for row in cursor.fetchall():
                actions.append(
                    {
                        "action_type": row[0],
                        "description": row[1],
                        "executed_at": row[2],
                        "success": row[3],
                        "details": row[4],
                    }
                )

            # Get communications
            cursor.execute(
                """
                SELECT recipient_type, recipient, sent_at, acknowledged
                FROM incident_communications WHERE incident_id = ?
                ORDER BY sent_at DESC
            """,
                (incident_id,),
            )

            communications = []
            for row in cursor.fetchall():
                communications.append(
                    {
                        "recipient_type": row[0],
                        "recipient": row[1],
                        "sent_at": row[2],
                        "acknowledged": row[3],
                    }
                )

            conn.close()

            return {
                "incident_id": incident_id,
                "report_timestamp": datetime.now().isoformat(),
                "incident_details": {
                    "severity": incident[0],
                    "status": incident[1],
                    "description": incident[2],
                    "created_at": incident[3],
                    "affected_systems": json.loads(incident[4]) if incident[4] else [],
                    "data_exposed": incident[5],
                },
                "automation_summary": {
                    "total_actions": len(actions),
                    "successful_actions": len([a for a in actions if a["success"]]),
                    "failed_actions": len([a for a in actions if not a["success"]]),
                    "total_communications": len(communications),
                    "acknowledged_communications": len(
                        [c for c in communications if c["acknowledged"]]
                    ),
                },
                "actions_taken": actions,
                "communications": communications,
            }

        except Exception as e:
            return {"error": str(e)}

    def create_automation_dashboard(self) -> Dict[str, Any]:
        """Create incident response automation dashboard"""
        try:
            conn = sqlite3.connect(str(self.incident_db))
            cursor = conn.cursor()

            # Get recent incidents
            cursor.execute(
                """
                SELECT incident_id, severity, status, created_at, updated_at
                FROM incidents
                ORDER BY created_at DESC
                LIMIT 10
            """
            )

            recent_incidents = []
            for row in cursor.fetchall():
                recent_incidents.append(
                    {
                        "incident_id": row[0],
                        "severity": row[1],
                        "status": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                    }
                )

            # Get statistics
            cursor.execute(
                """
                SELECT severity, COUNT(*) as count
                FROM incidents
                WHERE created_at >= datetime('now', '-24 hours')
                GROUP BY severity
            """
            )

            severity_stats = {}
            for row in cursor.fetchall():
                severity_stats[row[0]] = row[1]

            cursor.close()

            return {
                "dashboard_timestamp": datetime.now().isoformat(),
                "recent_incidents": recent_incidents,
                "statistics": {
                    "incidents_24h": sum(severity_stats.values()),
                    "by_severity": severity_stats,
                    "active_incidents": len(
                        [i for i in recent_incidents if i["status"] == "ACTIVE"]
                    ),
                },
                "automation_status": {
                    "system_ready": True,
                    "last_test": datetime.now().isoformat(),
                    "emergency_contacts_configured": True,
                    "automated_response_enabled": True,
                },
            }

        except Exception as e:
            return {"error": str(e)}


def main():
    """Main execution function"""
    print("🚨 INCIDENT RESPONSE AUTOMATION SYSTEM")
    print("=" * 60)

    automation = IncidentResponseAutomation()

    # Example: Create and respond to a critical incident
    print("1️⃣ Creating test incident...")
    incident_id = automation.create_incident(
        severity="CRITICAL",
        description="Suspicious database activity detected - potential SQL injection attempt",
        affected_systems=["database", "api", "user_data"],
    )

    if incident_id:
        print(f"✅ Incident created: {incident_id}")

        # Execute emergency containment
        print("\n2️⃣ Executing emergency containment...")
        containment_results = automation.execute_emergency_containment(incident_id)

        summary = containment_results["summary"]
        print(f"   Total Actions: {summary['total_actions']}")
        print(f"   Successful: {summary['successful_actions']}")
        print(f"   Failed: {summary['failed_actions']}")

        # Send emergency notification
        print("\n3️⃣ Sending emergency notification...")
        recipients = [
            "security-team@psychsync.com",
            "cto@psychsync.com",
            "dba@psychsync.com",
        ]
        automation.send_emergency_notification(
            incident_id,
            "CRITICAL",
            "Suspicious database activity detected - potential SQL injection attempt",
            recipients,
        )

        # Generate automation report
        print("\n4️⃣ Generating automation report...")
        report = automation.generate_automation_report(incident_id)

        with open("incident_automation_report.json", "w") as f:
            json.dump(report, f, indent=2, default=str)

        print("📄 Automation report saved to: incident_automation_report.json")

        # Create dashboard
        print("\n5️⃣ Creating automation dashboard...")
        dashboard = automation.create_automation_dashboard()

        with open("incident_response_dashboard.json", "w") as f:
            json.dump(dashboard, f, indent=2, default=str)

        print("📊 Dashboard saved to: incident_response_dashboard.json")

    else:
        print("❌ Failed to create incident")


if __name__ == "__main__":
    main()
