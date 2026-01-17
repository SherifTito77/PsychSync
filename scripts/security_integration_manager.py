#!/usr/bin/env python3
"""
PsychSync Security Integration Manager
Comprehensive security system integration and management
"""

import asyncio
import json
import logging
import sys
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
import argparse

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.enterprise_security import EnterpriseSecurityManager
from scripts.infrastructure_security_scanner import InfrastructureSecurityScanner
from scripts.ssh_brute_force_tester import SSHBruteForceTester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_integration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityStatus(Enum):
    SECURE = "SECURE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    id: str
    timestamp: datetime
    level: AlertLevel
    source: str
    title: str
    description: str
    details: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class SecurityMetrics:
    """Security metrics data structure"""
    timestamp: datetime
    enterprise_security_score: float
    infrastructure_risk_score: float
    ssh_security_score: float
    open_ports: int
    critical_cves: int
    active_alerts: int
    compliance_scores: Dict[str, float]
    threat_indicators: Dict[str, int]

class SecurityIntegrationManager:
    """Comprehensive security integration and management system"""

    def __init__(self, config_file: str = "security_config.json"):
        self.config_file = config_file
        self.config = self._load_config()

        # Initialize security components
        self.enterprise_security = EnterpriseSecurityManager()
        self.infrastructure_scanner = InfrastructureSecurityScanner()
        self.ssh_tester = SSHBruteForceTester()

        # State management
        self.alerts: List[SecurityAlert] = []
        self.metrics_history: List[SecurityMetrics] = []
        self.current_status = SecurityStatus.UNKNOWN
        self.last_scan_time: Optional[datetime] = None
        self.scan_in_progress = False

        # Background tasks
        self.background_tasks: List[threading.Thread] = []
        self.running = False

        # Callbacks for real-time updates
        self.alert_callbacks: List[Callable[[SecurityAlert], None]] = []
        self.metrics_callbacks: List[Callable[[SecurityMetrics], None]] = []

        # Create data directory
        self.data_dir = Path("security_data")
        self.data_dir.mkdir(exist_ok=True)

        logger.info("Security Integration Manager initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")

        # Default configuration
        return {
            "scan_interval_minutes": 60,
            "alert_thresholds": {
                "critical_cves": 5,
                "high_risk_ports": 3,
                "ssh_security_score": 70,
                "enterprise_security_score": 80
            },
            "infrastructure": {
                "target_host": "localhost",
                "ssh_host": "localhost",
                "ssh_port": 22
            },
            "background_scanning": True,
            "auto_resolve_alerts": False
        }

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _save_state(self):
        """Save current state to file"""
        try:
            state = {
                "alerts": [asdict(alert) for alert in self.alerts],
                "metrics_history": [asdict(metrics) for metrics in self.metrics_history],
                "current_status": self.current_status.value,
                "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None
            }

            # Convert datetime objects for JSON serialization
            for alert in state["alerts"]:
                alert["timestamp"] = alert["timestamp"].isoformat()
                if alert["resolved_at"]:
                    alert["resolved_at"] = alert["resolved_at"].isoformat()

            for metrics in state["metrics_history"]:
                metrics["timestamp"] = metrics["timestamp"].isoformat()

            with open(self.data_dir / "security_state.json", 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _load_state(self):
        """Load state from file"""
        try:
            state_file = self.data_dir / "security_state.json"
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)

                # Restore alerts
                self.alerts = []
                for alert_data in state.get("alerts", []):
                    alert_data["timestamp"] = datetime.fromisoformat(alert_data["timestamp"])
                    if alert_data["resolved_at"]:
                        alert_data["resolved_at"] = datetime.fromisoformat(alert_data["resolved_at"])
                    self.alerts.append(SecurityAlert(**alert_data))

                # Restore metrics history
                self.metrics_history = []
                for metrics_data in state.get("metrics_history", []):
                    metrics_data["timestamp"] = datetime.fromisoformat(metrics_data["timestamp"])
                    self.metrics_history.append(SecurityMetrics(**metrics_data))

                # Restore status
                self.current_status = SecurityStatus(state.get("current_status", "UNKNOWN"))

                # Restore last scan time
                if state.get("last_scan_time"):
                    self.last_scan_time = datetime.fromisoformat(state["last_scan_time"])

                logger.info(f"Loaded {len(self.alerts)} alerts and {len(self.metrics_history)} metrics records")

        except Exception as e:
            logger.error(f"Failed to load state: {e}")

    def add_alert_callback(self, callback: Callable[[SecurityAlert], None]):
        """Add callback for real-time alert updates"""
        self.alert_callbacks.append(callback)

    def add_metrics_callback(self, callback: Callable[[SecurityMetrics], None]):
        """Add callback for real-time metrics updates"""
        self.metrics_callbacks.append(callback)

    def create_alert(self, level: AlertLevel, source: str, title: str, description: str, details: Dict[str, Any] = None) -> SecurityAlert:
        """Create and handle a new security alert"""
        alert = SecurityAlert(
            id=f"{int(time.time())}-{source}",
            timestamp=datetime.now(),
            level=level,
            source=source,
            title=title,
            description=description,
            details=details or {}
        )

        self.alerts.append(alert)
        logger.warning(f"New {level.value} alert: {title}")

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

        # Update overall status
        self._update_overall_status()

        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert by ID"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Resolved alert: {alert.title}")
                self._update_overall_status()
                return True
        return False

    def _update_overall_status(self):
        """Update overall security status based on alerts"""
        unresolved_alerts = [alert for alert in self.alerts if not alert.resolved]

        if not unresolved_alerts:
            self.current_status = SecurityStatus.SECURE
        else:
            critical_alerts = [alert for alert in unresolved_alerts if alert.level == AlertLevel.CRITICAL]
            error_alerts = [alert for alert in unresolved_alerts if alert.level == AlertLevel.ERROR]
            warning_alerts = [alert for alert in unresolved_alerts if alert.level == AlertLevel.WARNING]

            if critical_alerts:
                self.current_status = SecurityStatus.CRITICAL
            elif error_alerts:
                self.current_status = SecurityStatus.WARNING
            elif warning_alerts:
                self.current_status = SecurityStatus.WARNING
            else:
                self.current_status = SecurityStatus.SECURE

    async def run_comprehensive_scan(self) -> Dict[str, Any]:
        """Run comprehensive security scan across all components"""
        if self.scan_in_progress:
            logger.warning("Scan already in progress")
            return {"error": "Scan already in progress"}

        self.scan_in_progress = True
        scan_start = datetime.now()

        try:
            logger.info("Starting comprehensive security scan")

            # Run infrastructure scan
            logger.info("Running infrastructure security scan")
            infra_results = self.infrastructure_scanner.run_comprehensive_scan()

            # Run SSH security test
            logger.info("Running SSH security test")
            ssh_results = self.ssh_tester.run_comprehensive_ssh_security_test()

            # Run enterprise security assessment
            logger.info("Running enterprise security assessment")
            enterprise_results = await self.enterprise_security.generate_comprehensive_security_report()

            # Process results and create alerts
            await self._process_scan_results(infra_results, ssh_results, enterprise_results)

            # Generate metrics
            metrics = self._generate_metrics(infra_results, ssh_results, enterprise_results)
            self.metrics_history.append(metrics)

            # Trigger metrics callbacks
            for callback in self.metrics_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    logger.error(f"Metrics callback failed: {e}")

            self.last_scan_time = datetime.now()

            # Save state
            self._save_state()

            scan_duration = (datetime.now() - scan_start).total_seconds()
            logger.info(f"Comprehensive scan completed in {scan_duration:.2f} seconds")

            return {
                "status": "success",
                "scan_duration": scan_duration,
                "metrics": asdict(metrics),
                "alerts_created": len([a for a in self.alerts if a.timestamp > scan_start])
            }

        except Exception as e:
            logger.error(f"Comprehensive scan failed: {e}")
            self.create_alert(
                AlertLevel.ERROR,
                "scan_manager",
                "Comprehensive Scan Failed",
                f"Security scan failed: {str(e)}",
                {"error": str(e), "scan_start": scan_start.isoformat()}
            )
            return {"error": str(e)}

        finally:
            self.scan_in_progress = False

    async def _process_scan_results(self, infra_results: Dict, ssh_results: Dict, enterprise_results: Dict):
        """Process scan results and generate alerts"""
        thresholds = self.config["alert_thresholds"]

        # Process infrastructure results
        if infra_results.get("risk_summary", {}).get("critical_cves", 0) > thresholds["critical_cves"]:
            self.create_alert(
                AlertLevel.CRITICAL,
                "infrastructure",
                "Critical CVEs Detected",
                f"Found {infra_results['risk_summary']['critical_cves']} critical CVEs",
                infra_results
            )

        if infra_results.get("risk_summary", {}).get("high_risk_ports", 0) > thresholds["high_risk_ports"]:
            self.create_alert(
                AlertLevel.WARNING,
                "infrastructure",
                "High Risk Ports Detected",
                f"Found {infra_results['risk_summary']['high_risk_ports']} high-risk open ports",
                infra_results
            )

        # Process SSH results
        ssh_score = ssh_results.get("overall_security_score", 100)
        if ssh_score < thresholds["ssh_security_score"]:
            self.create_alert(
                AlertLevel.WARNING,
                "ssh_security",
                "SSH Security Score Low",
                f"SSH security score: {ssh_score}/100",
                ssh_results
            )

        # Process enterprise results
        enterprise_score = enterprise_results.get("overall_security_score", 100)
        if enterprise_score < thresholds["enterprise_security_score"]:
            self.create_alert(
                AlertLevel.WARNING,
                "enterprise_security",
                "Enterprise Security Score Low",
                f"Enterprise security score: {enterprise_score}/100",
                enterprise_results
            )

    def _generate_metrics(self, infra_results: Dict, ssh_results: Dict, enterprise_results: Dict) -> SecurityMetrics:
        """Generate security metrics from scan results"""
        return SecurityMetrics(
            timestamp=datetime.now(),
            enterprise_security_score=enterprise_results.get("overall_security_score", 0),
            infrastructure_risk_score=infra_results.get("risk_summary", {}).get("risk_score", 0),
            ssh_security_score=ssh_results.get("overall_security_score", 0),
            open_ports=infra_results.get("risk_summary", {}).get("open_ports_count", 0),
            critical_cves=infra_results.get("risk_summary", {}).get("critical_cves", 0),
            active_alerts=len([a for a in self.alerts if not a.resolved]),
            compliance_scores={
                "soc2_type2": enterprise_results.get("compliance_status", {}).get("soc2_type2", 0),
                "iso_27001": enterprise_results.get("compliance_status", {}).get("iso_27001", 0),
                "gdpr": enterprise_results.get("compliance_status", {}).get("gdpr", 0),
                "hipaa": enterprise_results.get("compliance_status", {}).get("hipaa", 0),
                "fedramp": enterprise_results.get("compliance_status", {}).get("fedramp", 0)
            },
            threat_indicators={
                "suspicious_activities": 0,  # Would be populated by real-time monitoring
                "data_access_anomalies": 0,
                "encryption_failures": 0,
                "authentication_failures": ssh_results.get("failed_attempts", 0)
            }
        )

    def start_background_scanning(self):
        """Start background security scanning"""
        if not self.config["background_scanning"]:
            logger.info("Background scanning disabled in configuration")
            return

        def background_scan_loop():
            while self.running:
                try:
                    # Calculate next scan time
                    scan_interval = timedelta(minutes=self.config["scan_interval_minutes"])
                    next_scan = self.last_scan_time + scan_interval if self.last_scan_time else datetime.now()

                    if datetime.now() >= next_scan:
                        # Run scan in background
                        asyncio.run(self.run_comprehensive_scan())

                    # Sleep for a short interval to check frequently
                    time.sleep(60)

                except Exception as e:
                    logger.error(f"Background scan error: {e}")
                    time.sleep(300)  # Wait 5 minutes on error

        self.running = True
        background_thread = threading.Thread(target=background_scan_loop, daemon=True)
        background_thread.start()
        self.background_tasks.append(background_thread)

        logger.info("Background security scanning started")

    def stop_background_scanning(self):
        """Stop background security scanning"""
        self.running = False
        logger.info("Background security scanning stopped")

    def get_current_status(self) -> Dict[str, Any]:
        """Get current security status"""
        return {
            "overall_status": self.current_status.value,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None,
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "total_alerts": len(self.alerts),
            "scan_in_progress": self.scan_in_progress,
            "latest_metrics": asdict(self.metrics_history[-1]) if self.metrics_history else None
        }

    def get_alerts(self, level: Optional[AlertLevel] = None, resolved: Optional[bool] = None, limit: int = 50) -> List[SecurityAlert]:
        """Get alerts with optional filtering"""
        filtered_alerts = self.alerts

        if level:
            filtered_alerts = [a for a in filtered_alerts if a.level == level]

        if resolved is not None:
            filtered_alerts = [a for a in filtered_alerts if a.resolved == resolved]

        # Sort by timestamp (newest first) and limit
        filtered_alerts.sort(key=lambda a: a.timestamp, reverse=True)
        return filtered_alerts[:limit]

    def get_metrics_history(self, hours: int = 24) -> List[SecurityMetrics]:
        """Get metrics history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        if not self.metrics_history:
            return {"error": "No metrics data available"}

        latest_metrics = self.metrics_history[-1]

        # Calculate trends
        if len(self.metrics_history) >= 2:
            previous_metrics = self.metrics_history[-2]
            trends = {
                "enterprise_security_trend": latest_metrics.enterprise_security_score - previous_metrics.enterprise_security_score,
                "infrastructure_risk_trend": latest_metrics.infrastructure_risk_score - previous_metrics.infrastructure_risk_score,
                "ssh_security_trend": latest_metrics.ssh_security_score - previous_metrics.ssh_security_score,
                "alerts_trend": latest_metrics.active_alerts - previous_metrics.active_alerts
            }
        else:
            trends = {}

        return {
            "report_timestamp": datetime.now().isoformat(),
            "overall_status": self.current_status.value,
            "latest_metrics": asdict(latest_metrics),
            "trends": trends,
            "alert_summary": {
                "total": len(self.alerts),
                "active": len([a for a in self.alerts if not a.resolved]),
                "critical": len([a for a in self.alerts if a.level == AlertLevel.CRITICAL and not a.resolved]),
                "warning": len([a for a in self.alerts if a.level == AlertLevel.WARNING and not a.resolved])
            },
            "recent_alerts": [asdict(a) for a in self.get_alerts(limit=10)],
            "compliance_scores": latest_metrics.compliance_scores,
            "recommendations": self._generate_recommendations(latest_metrics)
        }

    def _generate_recommendations(self, metrics: SecurityMetrics) -> List[str]:
        """Generate security recommendations based on metrics"""
        recommendations = []

        if metrics.enterprise_security_score < 80:
            recommendations.append("Review and strengthen enterprise security controls")

        if metrics.ssh_security_score < 70:
            recommendations.append("Implement stronger SSH security configurations")

        if metrics.critical_cves > 0:
            recommendations.append("Patch critical CVEs immediately")

        if metrics.open_ports > 20:
            recommendations.append("Review open ports and close unnecessary services")

        if metrics.active_alerts > 10:
            recommendations.append("Address active security alerts promptly")

        # Compliance recommendations
        for standard, score in metrics.compliance_scores.items():
            if score < 90:
                recommendations.append(f"Improve {standard.upper()} compliance controls")

        return recommendations

def main():
    """Main CLI interface for Security Integration Manager"""
    parser = argparse.ArgumentParser(description="PsychSync Security Integration Manager")
    parser.add_argument("--config", default="security_config.json", help="Configuration file path")
    parser.add_argument("--scan", action="store_true", help="Run comprehensive security scan")
    parser.add_argument("--status", action="store_true", help="Show current security status")
    parser.add_argument("--alerts", action="store_true", help="Show recent alerts")
    parser.add_argument("--report", action="store_true", help="Generate security report")
    parser.add_argument("--monitor", action="store_true", help="Start continuous monitoring")
    parser.add_argument("--resolve", type=str, help="Resolve alert by ID")

    args = parser.parse_args()

    # Initialize security manager
    security_manager = SecurityIntegrationManager(args.config)
    security_manager._load_state()

    if args.scan:
        print("🔍 Running comprehensive security scan...")
        result = asyncio.run(security_manager.run_comprehensive_scan())
        if result.get("status") == "success":
            print(f"✅ Scan completed in {result['scan_duration']:.2f} seconds")
            print(f"📊 Alerts created: {result['alerts_created']}")
        else:
            print(f"❌ Scan failed: {result.get('error')}")

    elif args.status:
        status = security_manager.get_current_status()
        print(f"\n📊 Security Status: {status['overall_status']}")
        print(f"🕐 Last scan: {status['last_scan_time'] or 'Never'}")
        print(f"🚨 Active alerts: {status['active_alerts']}")
        print(f"📈 Total alerts: {status['total_alerts']}")

        if status['latest_metrics']:
            metrics = status['latest_metrics']
            print(f"\n📊 Latest Metrics:")
            print(f"  Enterprise Security: {metrics['enterprise_security_score']:.1f}%")
            print(f"  Infrastructure Risk: {metrics['infrastructure_risk_score']:.1f}")
            print(f"  SSH Security: {metrics['ssh_security_score']:.1f}")
            print(f"  Open Ports: {metrics['open_ports']}")
            print(f"  Critical CVEs: {metrics['critical_cves']}")

    elif args.alerts:
        alerts = security_manager.get_alerts(limit=20)
        print(f"\n🚨 Recent Alerts ({len(alerts)} shown)")

        for alert in alerts:
            status_icon = "✅" if alert.resolved else "🚨"
            print(f"\n{status_icon} {alert.level.value} - {alert.title}")
            print(f"   📅 {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   📝 {alert.description}")
            print(f"   🔗 Source: {alert.source}")
            if alert.resolved:
                print(f"   ✅ Resolved: {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S')}")

    elif args.report:
        report = security_manager.generate_report()
        print(f"\n📊 PsychSync Security Report")
        print(f"🕐 Generated: {report['report_timestamp']}")
        print(f"🔒 Overall Status: {report['overall_status']}")

        metrics = report['latest_metrics']
        print(f"\n📈 Security Metrics:")
        print(f"  Enterprise Security: {metrics['enterprise_security_score']:.1f}%")
        print(f"  Infrastructure Risk Score: {metrics['infrastructure_risk_score']:.1f}")
        print(f"  SSH Security Score: {metrics['ssh_security_score']:.1f}")

        print(f"\n🚨 Alert Summary:")
        alert_summary = report['alert_summary']
        print(f"  Total: {alert_summary['total']}")
        print(f"  Active: {alert_summary['active']}")
        print(f"  Critical: {alert_summary['critical']}")
        print(f"  Warning: {alert_summary['warning']}")

        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")

    elif args.resolve:
        if security_manager.resolve_alert(args.resolve):
            print(f"✅ Alert {args.resolve} resolved")
            security_manager._save_state()
        else:
            print(f"❌ Alert {args.resolve} not found or already resolved")

    elif args.monitor:
        print("🔍 Starting continuous security monitoring...")
        print("Press Ctrl+C to stop")

        def alert_callback(alert: SecurityAlert):
            print(f"\n🚨 NEW ALERT: {alert.level.value} - {alert.title}")
            print(f"   {alert.description}")

        def metrics_callback(metrics: SecurityMetrics):
            print(f"\n📊 Updated Metrics - Security Score: {metrics.enterprise_security_score:.1f}%")

        security_manager.add_alert_callback(alert_callback)
        security_manager.add_metrics_callback(metrics_callback)

        try:
            security_manager.start_background_scanning()
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            security_manager.stop_background_scanning()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
