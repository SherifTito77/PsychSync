#!/usr/bin/env python3
"""
Database Security Monitoring and Alerting System
Real-time monitoring for security threats and compliance violations
"""

import os
import json
import time
import sqlite3
import hashlib
import subprocess
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SecurityEventType(Enum):
    INJECTION_ATTEMPT = "injection_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    CREDENTIAL_COMPROMISE = "credential_compromise"
    DATA_EXFILTRATION = "data_exfiltration"
    COMPLIANCE_VIOLATION = "compliance_violation"
    ACCESS_VIOLATION = "access_violation"
    CONFIGURATION_CHANGE = "configuration_change"

class SecuritySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    timestamp: datetime
    event_type: SecurityEventType
    severity: SecuritySeverity
    description: str
    source_ip: Optional[str]
    user_id: Optional[str]
    affected_resource: str
    details: Dict[str, Any]
    event_id: str

class SecurityMonitoringSystem:
    def __init__(self):
        self.base_path = Path("/Users/sheriftito/Downloads/psychsync")
        self.db_path = self.base_path / "security_monitoring.db"
        self.alert_log = []
        self.alert_rules = self.load_alert_rules()
        self.initialize_database()

    def initialize_database(self):
        """Initialize security monitoring database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Create security events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    source_ip TEXT,
                    user_id TEXT,
                    affected_resource TEXT NOT NULL,
                    details TEXT,
                    alert_generated BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_notes TEXT
                )
            ''')

            # Create alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_by TEXT,
                    resolved_at TEXT,
                    FOREIGN KEY (event_id) REFERENCES security_events(event_id)
                )
            ''')

            # Create metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT
                )
            ''')

            conn.commit()
            conn.close()
            print("✅ Security monitoring database initialized")

        except Exception as e:
            print(f"❌ Error initializing security database: {e}")

    def load_alert_rules(self) -> List[Dict]:
        """Load security alert rules"""
        return [
            {
                "rule_name": "sql_injection_detection",
                "event_types": [SecurityEventType.INJECTION_ATTEMPT],
                "conditions": [
                    {"field": "description", "pattern": r"((?i)union.*select|select.*from|insert.*values|update.*set|delete.*from)"},
                    {"field": "severity", "value": SecuritySeverity.HIGH.value}
                ],
                "actions": ["immediate_alert", "block_ip", "require_investigation"]
            },
            {
                "rule_name": "privilege_escalation_detection",
                "event_types": [SecurityEventType.PRIVILEGE_ESCALATION],
                "conditions": [
                    {"field": "details", "pattern": r"((?i)admin|root|superuser)"},
                    {"field": "severity", "value": SecuritySeverity.CRITICAL.value}
                ],
                "actions": ["immediate_alert", "disable_account", "require_investigation"]
            },
            {
                "rule_name": "data_exfiltration_detection",
                "event_types": [SecurityEventType.DATA_EXFILTRATION],
                "conditions": [
                    {"field": "details", "pattern": r"((?i)large.*download|bulk.*export|mass.*data)"},
                    {"field": "description", "pattern": r"((?i)download.*large|export.*bulk)"}
                ],
                "actions": ["immediate_alert", "data_access_review", "compliance_report"]
            },
            {
                "rule_name": "access_pattern_anomaly",
                "event_types": [SecurityEventType.ACCESS_VIOLATION],
                "conditions": [
                    {"field": "source_ip", "pattern": r"((?i)unusual|suspicious)"},
                    {"field": "details", "key": "request_count", "operator": ">", "value": 100}
                ],
                "actions": ["monitoring_alert", "behavior_analysis", "potential_block"]
            }
        ]

    def detect_sql_injection(self, log_data: Dict) -> Optional[SecurityEvent]:
        """Detect SQL injection attempts"""
        injection_patterns = [
            r"union\s+.*\s+select",
            r"select\s+.*\s+from\s+.*",
            r"insert\s+into\s+.*",
            r"update\s+.*\s+set\s+.*",
            r"delete\s+from\s+.*",
            r"drop\s+table\s+.*",
            r";\s*--",
            r"'\s*or\s*'1'\s*=\s*'1",
            r"waitfor\s+delay\s+",
            r"xp_cmdshell",
            r"load_file"
        ]

        # Check request parameters and query strings
        for key, value in log_data.get("params", {}).items():
            if isinstance(value, str):
                for pattern in injection_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return SecurityEvent(
                            timestamp=datetime.now(),
                            event_type=SecurityEventType.INJECTION_ATTEMPT,
                            severity=SecuritySeverity.HIGH,
                            description=f"SQL injection pattern detected in parameter '{key}'",
                            source_ip=log_data.get("client_ip"),
                            user_id=log_data.get("user_id"),
                            affected_resource=log_data.get("endpoint"),
                            details={
                                "pattern": pattern,
                                "parameter": key,
                                "value": value[:100],  # Truncate long values
                                "user_agent": log_data.get("user_agent"),
                                "method": log_data.get("method")
                            },
                            event_id=self.generate_event_id()
                        )

        return None

    def detect_privilege_escalation(self, log_data: Dict) -> Optional[SecurityEvent]:
        """Detect privilege escalation attempts"""
        escalation_indicators = [
            ("admin", "User accessing admin resources"),
            ("root", "Root access attempt"),
            ("sudo", "Sudo command execution"),
            ("privilege", "Privilege modification attempt"),
            ("permission", "Permission escalation attempt"),
            ("grant", "Grant permission attempt"),
            ("revoke", "Revoke permission attempt")
        ]

        for indicator, description in escalation_indicators:
            if indicator in str(log_data.get("path", "")).lower():
                return SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=SecurityEventType.PRIVILEGE_ESCALATION,
                    severity=SecuritySeverity.CRITICAL,
                    description=f"Privilege escalation attempt: {description}",
                    source_ip=log_data.get("client_ip"),
                    user_id=log_data.get("user_id"),
                    affected_resource=log_data.get("endpoint"),
                    details={
                        "indicator": indicator,
                        "path": log_data.get("path"),
                        "method": log_data.get("method"),
                        "user_agent": log_data.get("user_agent")
                    },
                    event_id=self.generate_event_id()
                )

        return None

    def detect_data_exfiltration(self, log_data: Dict) -> Optional[SecurityEvent]:
        """Detect data exfiltration attempts"""
        exfiltration_patterns = [
            (r"download.*large", "Large file download"),
            (r"export.*bulk", "Bulk data export"),
            (r"backup.*download", "Backup download"),
            (r"select.*all", "Select all records"),
            (r"fetch.*large", "Large data fetch"),
            (r"query.*large", "Large query execution")
        ]

        request_details = f"{log_data.get('method', '')} {log_data.get('path', '')} {json.dumps(log_data.get('params', {}))}".lower()

        for pattern, description in exfiltration_patterns:
            if re.search(pattern, request_details, re.IGNORECASE):
                return SecurityEvent(
                    timestamp=datetime.now(),
                    event_type=SecurityEventType.DATA_EXFILTRATION,
                    severity=SecuritySeverity.HIGH,
                    description=f"Data exfiltration attempt: {description}",
                    source_ip=log_data.get("client_ip"),
                    user_id=log_data.get("user_id"),
                    affected_resource=log_data.get("endpoint"),
                    details={
                        "pattern": pattern,
                        "request_size": len(request_details),
                        "endpoint": log_data.get("endpoint"),
                        "params": list(log_data.get("params", {}).keys())
                    },
                    event_id=self.generate_event_id()
                )

        return None

    def monitor_database_activity(self) -> List[SecurityEvent]:
        """Monitor database activity for security threats"""
        security_events = []

        try:
            # Monitor PostgreSQL logs
            pg_log_path = "/var/log/postgresql/postgresql.log"
            if Path(pg_log_path).exists():
                security_events.extend(self.analyze_postgres_logs(pg_log_path))

            # Monitor application logs for database activity
            app_logs = [
                self.base_path / "logs" / "app.log",
                self.base_path / "logs" / "database.log",
                self.base_path / ".backend.log"
            ]

            for log_file in app_logs:
                if log_file.exists():
                    security_events.extend(self.analyze_application_logs(log_file))

        except Exception as e:
            print(f"⚠️ Error monitoring database activity: {e}")

        return security_events

    def analyze_postgres_logs(self, log_path: Path) -> List[SecurityEvent]:
        """Analyze PostgreSQL logs for security events"""
        security_events = []

        try:
            with open(log_path, 'r') as f:
                for line in f:
                    # Look for security-relevant log entries
                    security_patterns = [
                        (r"authentication failed", "Failed authentication attempt"),
                        (r"permission denied", "Permission denied"),
                        (r"connection unauthorized", "Unauthorized connection"),
                        (r"password authentication failed", "Password authentication failed"),
                        (r"invalid connection attempt", "Invalid connection attempt")
                    ]

                    for pattern, description in security_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Extract IP and other details
                            ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
                            source_ip = ip_match.group(0) if ip_match else None

                            event = SecurityEvent(
                                timestamp=datetime.now(),
                                event_type=SecurityEventType.ACCESS_VIOLATION,
                                severity=SecuritySeverity.MEDIUM,
                                description=f"Database security event: {description}",
                                source_ip=source_ip,
                                affected_resource="database",
                                details={
                                    "log_entry": line.strip()[:200],
                                    "log_file": str(log_path)
                                },
                                event_id=self.generate_event_id()
                            )
                            security_events.append(event)

        except Exception as e:
            print(f"⚠️ Error analyzing PostgreSQL logs: {e}")

        return security_events

    def analyze_application_logs(self, log_path: Path) -> List[SecurityEvent]:
        """Analyze application logs for security events"""
        security_events = []

        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # Parse JSON log entries if possible
                    try:
                        log_entry = json.loads(line)
                    except:
                        log_entry = {"raw_log": line}

                    # Check for security events
                    security_event = (
                        self.detect_sql_injection(log_entry) or
                        self.detect_privilege_escalation(log_entry) or
                        self.detect_data_exfiltration(log_entry)
                    )

                    if security_event:
                        security_events.append(security_event)

        except Exception as e:
            print(f"⚠️ Error analyzing application logs: {e}")

        return security_events

    def monitor_file_changes(self) -> List[SecurityEvent]:
        """Monitor critical files for unauthorized changes"""
        security_events = []

        # Define critical files to monitor
        critical_files = [
            self.base_path / ".env.dev",
            self.base_path / ".env.prod",
            self.base_path / "app" / "core" / "config.py",
            self.base_path / "alembic.ini"
        ]

        for file_path in critical_files:
            if file_path.exists():
                try:
                    stat_info = file_path.stat()
                    # Check file modifications (simple implementation)
                    # In production, use file monitoring tools like inotify
                    if stat_info.st_size > 0:  # Basic check
                        # Hash file for change detection
                        file_hash = self.calculate_file_hash(file_path)
                        # Store and compare with previous hash
                        # For now, just log the file being monitored

                except Exception as e:
                    print(f"⚠️ Error monitoring file {file_path}: {e}")

        return security_events

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read and update hash string value in blocks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return ""

    def generate_event_id(self) -> str:
        """Generate unique event ID"""
        return f"evt_{int(time.time() * 1000000)}_{os.urandom(4).hex()}"

    def process_alert_rules(self, event: SecurityEvent) -> bool:
        """Process event against alert rules"""
        alert_generated = False

        for rule in self.alert_rules:
            if event.event_type in rule["event_types"]:
                rule_match = True

                # Check all conditions
                for condition in rule["conditions"]:
                    field_value = getattr(event, condition["field"], "")
                    if "pattern" in condition:
                        if not re.search(condition["pattern"], str(field_value), re.IGNORECASE):
                            rule_match = False
                            break
                    elif "value" in condition:
                        if str(field_value) != str(condition["value"]):
                            rule_match = False
                            break
                    elif "operator" in condition and "value" in condition:
                        field_value_numeric = float(str(field_value)) if str(field_value).isdigit() else 0
                        condition_value = float(condition["value"])

                        if condition["operator"] == ">" and field_value_numeric <= condition_value:
                            rule_match = False
                            break
                        elif condition["operator"] == "<" and field_value_numeric >= condition_value:
                            rule_match = False
                            break

                if rule_match:
                    self.generate_alert(event, rule)
                    alert_generated = True

        return alert_generated

    def generate_alert(self, event: SecurityEvent, rule: Dict):
        """Generate security alert"""
        alert = {
            "event_id": event.event_id,
            "alert_type": rule["rule_name"],
            "severity": event.severity.value,
            "timestamp": event.timestamp.isoformat(),
            "message": f"SECURITY ALERT: {event.description}",
            "actions": rule["actions"],
            "event_details": {
                "event_type": event.event_type.value,
                "source_ip": event.source_ip,
                "user_id": event.user_id,
                "affected_resource": event.affected_resource,
                "details": event.details
            }
        }

        self.alert_log.append(alert)

        # Store alert in database
        self.store_alert_in_database(alert)

        # Log the alert
        print(f"🚨 SECURITY ALERT: {event.description}")
        print(f"   Severity: {event.severity.value.upper()}")
        print(f"   Rule: {rule['rule_name']}")
        print(f"   Actions: {', '.join(rule['actions'])}")

        # Send immediate notifications (in production, integrate with notification system)
        self.send_immediate_notification(alert)

    def store_alert_in_database(self, alert: Dict):
        """Store alert in monitoring database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO security_alerts
                (event_id, alert_type, severity, timestamp, message, acknowledged, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert["event_id"],
                alert["alert_type"],
                alert["severity"],
                alert["timestamp"],
                alert["message"],
                False,
                False
            ))

            # Also store the event
            cursor.execute('''
                INSERT INTO security_events
                (event_id, timestamp, event_type, severity, description, source_ip, user_id, affected_resource, details, alert_generated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert["event_id"],
                alert["timestamp"],
                alert["event_type"],
                alert["severity"],
                alert["message"].replace("SECURITY ALERT: ", ""),
                alert["event_details"]["source_ip"],
                alert["event_details"]["user_id"],
                alert["event_details"]["affected_resource"],
                json.dumps(alert["event_details"]["details"]),
                True
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ Error storing alert in database: {e}")

    def send_immediate_notification(self, alert: Dict):
        """Send immediate security notification"""
        # In production, integrate with:
        # - Email notifications
        # - Slack/Teams webhook
        # - SMS alerts
        # - PagerDuty
        # - Security operations center

        notification_message = f"""
SECURITY ALERT - {alert['severity'].upper()}

Rule: {alert['alert_type']}
Description: {alert['message']}
Timestamp: {alert['timestamp']}

Event Details:
- Type: {alert['event_details']['event_type']}
- Source IP: {alert['event_details']['source_ip']}
- User ID: {alert['event_details']['user_id']}
- Resource: {alert['event_details']['affected_resource']}

Required Actions: {', '.join(alert['actions'])}
        """

        # For now, log to file
        alert_log_file = self.base_path / "security_alerts.log"
        with open(alert_log_file, 'a') as f:
            f.write(f"\n{'='*60}\n{notification_message}\n{'='*60}\n")

        print(f"📧 Security notification logged to {alert_log_file}")

    def run_security_scan(self) -> Dict[str, Any]:
        """Run comprehensive security scan"""
        print("🔍 Running security monitoring scan...")

        scan_results = {
            "timestamp": datetime.now().isoformat(),
            "events_detected": [],
            "alerts_generated": len(self.alert_log),
            "scan_summary": {}
        }

        # Monitor different sources
        print("  📊 Monitoring database activity...")
        db_events = self.monitor_database_activity()
        scan_results["events_detected"].extend(db_events)

        print("  📁 Monitoring file changes...")
        file_events = self.monitor_file_changes()
        scan_results["events_detected"].extend(file_events)

        # Process events against alert rules
        total_events = len(scan_results["events_detected"])
        alerts_generated = 0

        for event in scan_results["events_detected"]:
            if self.process_alert_rules(event):
                alerts_generated += 1

        # Store metrics
        self.store_security_metrics(scan_results)

        # Generate summary
        scan_results["scan_summary"] = {
            "total_events": total_events,
            "alerts_generated_this_scan": alerts_generated,
            "total_alerts": len(self.alert_log),
            "critical_events": len([e for e in scan_results["events_detected"] if e.severity == SecuritySeverity.CRITICAL]),
            "high_severity_events": len([e for e in scan_results["events_detected"] if e.severity == SecuritySeverity.HIGH])
        }

        return scan_results

    def store_security_metrics(self, scan_results: Dict):
        """Store security metrics in database"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            metrics = [
                ("events_detected", scan_results["scan_summary"]["total_events"]),
                ("alerts_generated", scan_results["scan_summary"]["alerts_generated_this_scan"]),
                ("critical_events", scan_results["scan_summary"]["critical_events"]),
                ("high_severity_events", scan_results["scan_summary"]["high_severity_events"]),
                ("total_alerts", len(self.alert_log))
            ]

            for metric_type, metric_value in metrics:
                cursor.execute('''
                    INSERT INTO security_metrics (timestamp, metric_type, metric_value, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    metric_type,
                    float(metric_value),
                    json.dumps({"scan_id": scan_results.get("timestamp", "")})
                ))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"❌ Error storing security metrics: {e}")

    def generate_security_dashboard(self) -> Dict[str, Any]:
        """Generate security dashboard data"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get recent security events
            cursor.execute('''
                SELECT event_id, timestamp, event_type, severity, description
                FROM security_events
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
                LIMIT 50
            ''')

            recent_events = []
            for row in cursor.fetchall():
                recent_events.append({
                    "event_id": row[0],
                    "timestamp": row[1],
                    "event_type": row[2],
                    "severity": row[3],
                    "description": row[4]
                })

            # Get unresolved alerts
            cursor.execute('''
                SELECT id, event_id, alert_type, severity, timestamp, message
                FROM security_alerts
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
                LIMIT 20
            ''')

            unresolved_alerts = []
            for row in cursor.fetchall():
                unresolved_alerts.append({
                    "id": row[0],
                    "event_id": row[1],
                    "alert_type": row[2],
                    "severity": row[3],
                    "timestamp": row[4],
                    "message": row[5]
                })

            # Get security metrics
            cursor.execute('''
                SELECT metric_type, metric_value, timestamp
                FROM security_metrics
                WHERE timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
            ''')

            metrics_24h = {}
            for row in cursor.fetchall():
                metric_type, metric_value, timestamp = row
                if metric_type not in metrics_24h:
                    metrics_24h[metric_type] = []
                metrics_24h[metric_type].append({
                    "value": metric_value,
                    "timestamp": timestamp
                })

            conn.close()

            return {
                "timestamp": datetime.now().isoformat(),
                "recent_events": recent_events,
                "unresolved_alerts": unresolved_alerts,
                "metrics_24h": metrics_24h,
                "dashboard_summary": {
                    "total_events_last_24h": len(recent_events),
                    "unresolved_alerts": len(unresolved_alerts),
                    "critical_events_count": len([e for e in recent_events if e["severity"] == "critical"])
                }
            }

        except Exception as e:
            return {"error": str(e)}

    def start_continuous_monitoring(self, interval_seconds: int = 60):
        """Start continuous security monitoring"""
        print(f"🔄 Starting continuous security monitoring (interval: {interval_seconds}s)")

        try:
            while True:
                print(f"\n🔍 Security scan at {datetime.now()}")
                scan_results = self.run_security_scan()

                summary = scan_results["scan_summary"]
                print(f"📊 Scan Results:")
                print(f"   Total Events: {summary['total_events']}")
                print(f"   Alerts Generated: {summary['alerts_generated_this_scan']}")
                print(f"   Critical Events: {summary['critical_events']}")
                print(f"   High Severity: {summary['high_severity_events']}")

                if summary["alerts_generated_this_scan"] > 0:
                    print("🚨 New security alerts generated!")

                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n🛑 Security monitoring stopped by user")

        except Exception as e:
            print(f"❌ Security monitoring error: {e}")

def main():
    """Main execution function"""
    print("🛡️ DATABASE SECURITY MONITORING SYSTEM")
    print("=" * 60)

    monitoring_system = SecurityMonitoringSystem()

    # Run initial scan
    print("🔍 Running initial security scan...")
    scan_results = monitoring_system.run_security_scan()

    # Generate dashboard
    print("\n📊 Generating security dashboard...")
    dashboard = monitoring_system.generate_security_dashboard()

    if "error" not in dashboard:
        summary = dashboard["dashboard_summary"]
        print(f"   Total Events (24h): {summary['total_events_last_24h']}")
        print(f"   Unresolved Alerts: {summary['unresolved_alerts']}")
        print(f"   Critical Events: {summary['critical_events_count']}")

        # Save dashboard
        with open("/Users/sheriftito/Downloads/psychsync/security_dashboard.json", "w") as f:
            json.dump(dashboard, f, indent=2, default=str)

        print("📄 Security dashboard saved to: security_dashboard.json")

    # Ask user if they want to start continuous monitoring
    print("\n🔄 Options:")
    print("1. Run single scan (default)")
    print("2. Start continuous monitoring")
    print("3. Generate security dashboard")

    try:
        choice = input("Select option (1-3): ").strip()

        if choice == "2":
            interval = input("Enter monitoring interval in seconds (default: 60): ").strip()
            interval_seconds = int(interval) if interval.isdigit() else 60
            monitoring_system.start_continuous_monitoring(interval_seconds)
        elif choice == "3":
            dashboard = monitoring_system.generate_security_dashboard()
            with open("/Users/sheriftito/Downloads/psychsync/security_dashboard.json", "w") as f:
                json.dump(dashboard, f, indent=2, default=str)
            print("📄 Security dashboard updated")
        else:
            print("🔍 Running single scan...")
            scan_results = monitoring_system.run_security_scan()
            print(f"✅ Scan complete. {scan_results['scan_summary']['total_events']} events detected.")

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    main()