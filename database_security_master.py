#!/usr/bin/env python3
"""
Comprehensive Database Security Testing Master Suite
Runs all database security tests and generates consolidated reports
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import logging

# Import all security testing modules
from database_security_tester import DatabaseSecurityTester
from nosql_injection_tester import NoSQLInjectionTester
from backup_security_tester import BackupSecurityTester
from privilege_escalation_tester import PrivilegeEscalationTester
from log_security_tester import LogSecurityTester

class DatabaseSecurityMaster:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self.setup_logging()
        self.results = {}

    def setup_logging(self):
        """Setup master logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database_security_master.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('DatabaseSecurityMaster')

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all database security tests"""
        self.logger.info("🚀 Starting comprehensive database security testing...")

        start_time = datetime.utcnow()

        # Run individual test suites
        await self.run_database_security_tests()
        await self.run_nosql_injection_tests()
        await self.run_backup_security_tests()
        await self.run_privilege_escalation_tests()
        await self.run_log_security_tests()

        # Generate consolidated report
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        master_report = await self.generate_consolidated_report(duration)

        # Save master report
        self.save_master_report(master_report)

        return master_report

    async def run_database_security_tests(self):
        """Run general database security tests"""
        self.logger.info("🔍 Running database security tests...")
        try:
            tester = DatabaseSecurityTester(self.config)
            report = await tester.generate_report()
            self.results['database_security'] = report
            self.logger.info(f"✅ Database security tests completed: {report['summary']['total_findings']} findings")
        except Exception as e:
            self.logger.error(f"❌ Database security tests failed: {str(e)}")
            self.results['database_security'] = {"error": str(e), "findings": []}

    async def run_nosql_injection_tests(self):
        """Run NoSQL injection tests"""
        self.logger.info("🔍 Running NoSQL injection tests...")
        try:
            tester = NoSQLInjectionTester(
                target_url=self.config.get('api_base_url', 'http://localhost:8000'),
                auth_headers=self.config.get('auth_headers', {})
            )
            report = await tester.run_all_tests()
            self.results['nosql_injection'] = report
            self.logger.info(f"✅ NoSQL injection tests completed: {report['total_vulnerabilities']} vulnerabilities")
        except Exception as e:
            self.logger.error(f"❌ NoSQL injection tests failed: {str(e)}")
            self.results['nosql_injection'] = {"error": str(e), "vulnerabilities": []}

    async def run_backup_security_tests(self):
        """Run backup security tests"""
        self.logger.info("🔍 Running backup security tests...")
        try:
            tester = BackupSecurityTester(self.config)
            report = await tester.run_all_tests()
            self.results['backup_security'] = report
            self.logger.info(f"✅ Backup security tests completed: {report['total_findings']} findings")
        except Exception as e:
            self.logger.error(f"❌ Backup security tests failed: {str(e)}")
            self.results['backup_security'] = {"error": str(e), "findings": []}

    async def run_privilege_escalation_tests(self):
        """Run privilege escalation tests"""
        self.logger.info("🔍 Running privilege escalation tests...")
        try:
            tester = PrivilegeEscalationTester(self.config)
            report = await tester.run_all_tests()
            self.results['privilege_escalation'] = report
            self.logger.info(f"✅ Privilege escalation tests completed: {report['total_findings']} findings")
        except Exception as e:
            self.logger.error(f"❌ Privilege escalation tests failed: {str(e)}")
            self.results['privilege_escalation'] = {"error": str(e), "findings": []}

    async def run_log_security_tests(self):
        """Run log security tests"""
        self.logger.info("🔍 Running log security tests...")
        try:
            tester = LogSecurityTester(self.config)
            report = await tester.run_all_tests()
            self.results['log_security'] = report
            self.logger.info(f"✅ Log security tests completed: {report['total_findings']} findings")
        except Exception as e:
            self.logger.error(f"❌ Log security tests failed: {str(e)}")
            self.results['log_security'] = {"error": str(e), "findings": []}

    async def generate_consolidated_report(self, duration: float) -> Dict[str, Any]:
        """Generate consolidated security report"""
        self.logger.info("📋 Generating consolidated security report...")

        master_report = {
            "scan_metadata": {
                "scan_date": datetime.utcnow().isoformat(),
                "duration_seconds": round(duration, 2),
                "scanner_version": "1.0.0",
                "target_environment": self.config.get('environment', 'development'),
                "tested_components": list(self.results.keys())
            },
            "executive_summary": self.generate_executive_summary(),
            "detailed_results": self.results,
            "risk_assessment": self.generate_risk_assessment(),
            "remediation_roadmap": self.generate_remediation_roadmap(),
            "compliance_status": self.generate_compliance_status()
        }

        return master_report

    def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate executive summary"""
        total_findings = 0
        critical_findings = 0
        high_findings = 0
        findings_by_category = {}

        # Aggregate findings from all test suites
        for test_name, result in self.results.items():
            if 'error' not in result:
                if test_name == 'nosql_injection':
                    findings = result.get('vulnerabilities', [])
                    total_findings += len(findings)
                    critical_findings += len([f for f in findings if f.get('severity') == 'CRITICAL'])
                    high_findings += len([f for f in findings if f.get('severity') == 'HIGH'])
                    findings_by_category[test_name] = len(findings)
                else:
                    findings = result.get('findings', [])
                    total_findings += len(findings)
                    if 'summary' in result:
                        summary = result['summary']
                        critical_findings += summary.get('by_severity', {}).get('CRITICAL', 0)
                        high_findings += summary.get('by_severity', {}).get('HIGH', 0)
                    findings_by_category[test_name] = len(findings)

        # Calculate overall risk score
        critical_weight = 10
        high_weight = 5
        medium_weight = 2
        low_weight = 1

        risk_score = (
            critical_findings * critical_weight +
            high_findings * high_weight +
            (total_findings - critical_findings - high_findings) * medium_weight
        )

        max_risk_score = 100  # Normalize to 100
        normalized_risk_score = min(risk_score, max_risk_score)

        # Determine risk level
        if normalized_risk_score >= 80:
            risk_level = "CRITICAL"
        elif normalized_risk_score >= 60:
            risk_level = "HIGH"
        elif normalized_risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "total_findings": total_findings,
            "critical_findings": critical_findings,
            "high_findings": high_findings,
            "findings_by_category": findings_by_category,
            "risk_score": normalized_risk_score,
            "risk_level": risk_level,
            "overall_status": "SECURE" if critical_findings == 0 and high_findings == 0 else "VULNERABLE"
        }

    def generate_risk_assessment(self) -> Dict[str, Any]:
        """Generate detailed risk assessment"""
        executive_summary = self.generate_executive_summary()

        # Identify top risks
        top_risks = []
        for test_name, result in self.results.items():
            if 'error' not in result:
                if test_name == 'nosql_injection':
                    critical_vulns = [f for f in result.get('vulnerabilities', [])
                                    if f.get('severity') == 'CRITICAL']
                    for vuln in critical_vulns[:3]:  # Top 3 per category
                        top_risks.append({
                            "category": test_name,
                            "description": vuln.get('description', 'Unknown'),
                            "impact": "CRITICAL",
                            "likelihood": "HIGH"
                        })
                else:
                    findings = result.get('findings', [])
                    critical_findings = [f for f in findings if f.get('severity') == 'CRITICAL']
                    for finding in critical_findings[:3]:
                        top_risks.append({
                            "category": test_name,
                            "description": finding.get('description', 'Unknown'),
                            "impact": "CRITICAL",
                            "likelihood": "HIGH"
                        })

        # Asset impact assessment
        asset_impacts = {
            "data_confidentiality": executive_summary['critical_findings'] > 0,
            "data_integrity": executive_summary['high_findings'] > 0,
            "system_availability": any('denial' in str(r).lower() for r in top_risks),
            "compliance": executive_summary['total_findings'] > 0
        }

        return {
            "overall_risk_score": executive_summary['risk_score'],
            "risk_level": executive_summary['risk_level'],
            "top_risks": top_risks[:10],  # Top 10 overall risks
            "asset_impacts": asset_impacts,
            "threat_vectors": self.identify_threat_vectors(),
            "affected_systems": self.identify_affected_systems()
        }

    def identify_threat_vectors(self) -> List[str]:
        """Identify threat vectors based on findings"""
        threat_vectors = []

        for test_name, result in self.results.items():
            if 'error' not in result:
                if test_name == 'nosql_injection':
                    if result.get('vulnerabilities'):
                        threat_vectors.append("NoSQL Injection")
                elif test_name == 'database_security':
                    findings = result.get('findings', [])
                    if any('credential' in str(f).lower() for f in findings):
                        threat_vectors.append("Credential Theft")
                    if any('injection' in str(f).lower() for f in findings):
                        threat_vectors.append("SQL Injection")
                elif test_name == 'backup_security':
                    if result.get('findings'):
                        threat_vectors.append("Data Exposure via Backups")
                elif test_name == 'privilege_escalation':
                    if result.get('findings'):
                        threat_vectors.append("Privilege Escalation")
                elif test_name == 'log_security':
                    findings = result.get('findings', [])
                    if any(f.get('sensitive_type') == 'CREDENTIALS' for f in findings):
                        threat_vectors.append("Credential Exposure via Logs")

        return list(set(threat_vectors))

    def identify_affected_systems(self) -> List[str]:
        """Identify affected systems"""
        systems = []

        if 'postgresql' in self.config:
            systems.append("PostgreSQL Database")
        if 'mongodb' in self.config:
            systems.append("MongoDB Database")
        if 'redis' in self.config:
            systems.append("Redis Cache")
        if self.config.get('api_base_url'):
            systems.append("Web Application")
        if self.config.get('backup_directories'):
            systems.append("Backup Systems")

        return systems

    def generate_remediation_roadmap(self) -> Dict[str, Any]:
        """Generate prioritized remediation roadmap"""
        executive_summary = self.generate_executive_summary()

        # Immediate actions (Critical findings)
        immediate_actions = []
        urgent_actions = []
        planned_actions = []

        for test_name, result in self.results.items():
            if 'error' not in result:
                if test_name == 'nosql_injection':
                    critical_vulns = [f for f in result.get('vulnerabilities', [])
                                    if f.get('severity') == 'CRITICAL']
                    high_vulns = [f for f in result.get('vulnerabilities', [])
                                 if f.get('severity') == 'HIGH']

                    for vuln in critical_vulns:
                        immediate_actions.append({
                            "title": f"Fix {vuln.get('type', 'Unknown')} in {vuln.get('endpoint', 'Unknown')}",
                            "description": vuln.get('description', 'No description'),
                            "priority": "IMMEDIATE",
                            "estimated_effort": "4-8 hours",
                            "risk_reduction": "High"
                        })

                    for vuln in high_vulns:
                        urgent_actions.append({
                            "title": f"Address {vuln.get('type', 'Unknown')} vulnerability",
                            "description": vuln.get('description', 'No description'),
                            "priority": "URGENT",
                            "estimated_effort": "2-4 hours",
                            "risk_reduction": "Medium"
                        })
                else:
                    findings = result.get('findings', [])
                    critical_findings = [f for f in findings if f.get('severity') == 'CRITICAL']
                    high_findings = [f for f in findings if f.get('severity') == 'HIGH']
                    medium_findings = [f for f in findings if f.get('severity') == 'MEDIUM']

                    for finding in critical_findings:
                        immediate_actions.append({
                            "title": f"Fix {finding.get('issue_type', 'Critical Issue')}",
                            "description": finding.get('description', 'No description'),
                            "priority": "IMMEDIATE",
                            "estimated_effort": "2-6 hours",
                            "risk_reduction": "High"
                        })

                    for finding in high_findings:
                        urgent_actions.append({
                            "title": f"Address {finding.get('issue_type', 'High Issue')}",
                            "description": finding.get('description', 'No description'),
                            "priority": "URGENT",
                            "estimated_effort": "1-3 hours",
                            "risk_reduction": "Medium"
                        })

                    for finding in medium_findings:
                        planned_actions.append({
                            "title": f"Resolve {finding.get('issue_type', 'Medium Issue')}",
                            "description": finding.get('description', 'No description'),
                            "priority": "PLANNED",
                            "estimated_effort": "1-2 hours",
                            "risk_reduction": "Low"
                        })

        return {
            "immediate_actions": immediate_actions[:5],  # Top 5 immediate
            "urgent_actions": urgent_actions[:10],  # Top 10 urgent
            "planned_actions": planned_actions[:15],  # Top 15 planned
            "total_remediation_time": self.calculate_total_remediation_time(immediate_actions, urgent_actions, planned_actions),
            "success_metrics": self.define_success_metrics()
        }

    def calculate_total_remediation_time(self, immediate, urgent, planned):
        """Calculate total remedation time in days"""
        def extract_hours(actions):
            total = 0
            for action in actions:
                effort = action.get('estimated_effort', '1 hour')
                if isinstance(effort, str):
                    # Extract hours from string like "2-4 hours"
                    import re
                    match = re.search(r'(\d+)', effort)
                    if match:
                        total += int(match.group(1))
            return total

        immediate_hours = extract_hours(immediate)
        urgent_hours = extract_hours(urgent)
        planned_hours = extract_hours(planned)

        # Assume 8 hours per day, parallel work possible
        immediate_days = (immediate_hours + 7) // 8  # Round up
        urgent_days = (urgent_hours + 7) // 8
        planned_days = (planned_hours + 7) // 8

        return {
            "immediate_days": immediate_days,
            "urgent_days": urgent_days,
            "planned_days": planned_days,
            "total_calendar_days": immediate_days + urgent_days + planned_days
        }

    def define_success_metrics(self):
        """Define success metrics for remediation"""
        return {
            "zero_critical_findings": "All critical vulnerabilities resolved",
            "zero_high_findings": "All high-risk vulnerabilities resolved",
            "automated_monitoring": "Continuous security monitoring implemented",
            "regular_scanning": "Monthly security scans scheduled",
            "compliance_achievement": "Industry compliance standards met"
        }

    def generate_compliance_status(self) -> Dict[str, Any]:
        """Generate compliance status"""
        executive_summary = self.generate_executive_summary()

        compliance_standards = {
            "SOC2": {
                "status": "COMPLIANT" if executive_summary['critical_findings'] == 0 else "NON_COMPLIANT",
                "findings": executive_summary['critical_findings'],
                "requirements": ["Access Control", "Security Monitoring", "Data Protection"]
            },
            "PCI_DSS": {
                "status": "COMPLIANT" if executive_summary['critical_findings'] == 0 else "NON_COMPLIANT",
                "findings": executive_summary['critical_findings'],
                "requirements": ["Data Encryption", "Access Control", "Network Security"]
            },
            "HIPAA": {
                "status": "COMPLIANT" if executive_summary['critical_findings'] == 0 else "NON_COMPLIANT",
                "findings": executive_summary['critical_findings'],
                "requirements": ["Data Protection", "Access Controls", "Audit Logging"]
            },
            "GDPR": {
                "status": "COMPLIANT" if executive_summary['critical_findings'] == 0 else "NON_COMPLIANT",
                "findings": executive_summary['critical_findings'],
                "requirements": ["Data Protection", "Access Control", "Breach Notification"]
            }
        }

        # Check specific compliance requirements
        log_security_result = self.results.get('log_security', {})
        backup_security_result = self.results.get('backup_security', {})
        privilege_result = self.results.get('privilege_escalation', {})

        # Update compliance based on specific findings
        if 'error' not in log_security_result:
            if log_security_result.get('findings'):
                compliance_standards["HIPAA"]["status"] = "NON_COMPLIANT"
                compliance_standards["GDPR"]["status"] = "NON_COMPLIANT"

        if 'error' not in backup_security_result:
            if backup_security_result.get('findings'):
                compliance_standards["PCI_DSS"]["status"] = "NON_COMPLIANT"
                compliance_standards["HIPAA"]["status"] = "NON_COMPLIANT"

        if 'error' not in privilege_result:
            if privilege_result.get('findings'):
                for standard in compliance_standards.values():
                    standard["status"] = "NON_COMPLIANT"

        return compliance_standards

    def save_master_report(self, report: Dict[str, Any]):
        """Save master security report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"database_security_master_report_{timestamp}.json"

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"✅ Master security report saved to: {report_file}")

        # Also save a summary report
        summary_file = f"security_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            self.write_summary_report(report, f)

        self.logger.info(f"✅ Security summary saved to: {summary_file}")

    def write_summary_report(self, report: Dict[str, Any], file):
        """Write human-readable summary report"""
        exec_summary = report['executive_summary']
        risk_assessment = report['risk_assessment']
        remediation = report['remediation_roadmap']

        file.write("="*80 + "\n")
        file.write("DATABASE SECURITY ASSESSMENT REPORT\n")
        file.write("="*80 + "\n\n")

        file.write(f"Scan Date: {report['scan_metadata']['scan_date']}\n")
        file.write(f"Duration: {report['scan_metadata']['duration_seconds']} seconds\n")
        file.write(f"Environment: {report['scan_metadata']['target_environment']}\n\n")

        file.write("EXECUTIVE SUMMARY\n")
        file.write("-" * 40 + "\n")
        file.write(f"Total Findings: {exec_summary['total_findings']}\n")
        file.write(f"Critical Findings: {exec_summary['critical_findings']}\n")
        file.write(f"High Findings: {exec_summary['high_findings']}\n")
        file.write(f"Risk Score: {exec_summary['risk_score']}/100\n")
        file.write(f"Risk Level: {exec_summary['risk_level']}\n")
        file.write(f"Overall Status: {exec_summary['overall_status']}\n\n")

        file.write("FINDINGS BY CATEGORY\n")
        file.write("-" * 40 + "\n")
        for category, count in exec_summary['findings_by_category'].items():
            file.write(f"{category}: {count} findings\n")
        file.write("\n")

        file.write("TOP RISKS\n")
        file.write("-" * 40 + "\n")
        for i, risk in enumerate(risk_assessment['top_risks'][:5], 1):
            file.write(f"{i}. {risk['description']}\n")
            file.write(f"   Category: {risk['category']}\n")
            file.write(f"   Impact: {risk['impact']}\n\n")

        file.write("IMMEDIATE ACTIONS REQUIRED\n")
        file.write("-" * 40 + "\n")
        for i, action in enumerate(remediation['immediate_actions'], 1):
            file.write(f"{i}. {action['title']}\n")
            file.write(f"   Effort: {action['estimated_effort']}\n")
            file.write(f"   Risk Reduction: {action['risk_reduction']}\n\n")

        file.write("COMPLIANCE STATUS\n")
        file.write("-" * 40 + "\n")
        for standard, info in report['compliance_status'].items():
            file.write(f"{standard}: {info['status']}\n")
        file.write("\n")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Comprehensive Database Security Testing Suite')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000',
                       help='API base URL for testing')
    parser.add_argument('--env', type=str, default='development',
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--output-dir', type=str, default='.',
                       help='Output directory for reports')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--tests', nargs='+',
                       choices=['all', 'database', 'injection', 'backup', 'privilege', 'logs'],
                       default=['all'],
                       help='Specific tests to run (default: all)')
    return parser.parse_args()

def load_config(args) -> Dict[str, Any]:
    """Load configuration from file and arguments"""
    config = {
        "api_base_url": args.api_url,
        "environment": args.env,
        "backup_directories": [
            "./backups", "/var/backups", "/tmp/backups",
            "./db_backups", "./sql_dumps", "./mongodumps"
        ],
        "log_directories": [
            "./logs", "/var/log", "./app/logs", "./log",
            ".", "/tmp", "/var/tmp"
        ],
        "max_file_size": 50 * 1024 * 1024,
        "auth_headers": {
            "Content-Type": "application/json",
        }
    }

    # Load database configuration from environment variables
    if os.getenv('MONGO_USERNAME'):
        config['mongodb'] = {
            "host": os.getenv('MONGO_HOST', 'localhost'),
            "port": int(os.getenv('MONGO_PORT', 27017)),
            "username": os.getenv('MONGO_USERNAME'),
            "password": os.getenv('MONGO_PASSWORD'),
            "authDatabase": os.getenv('MONGO_AUTH_DB', 'admin')
        }

    if os.getenv('DB_USER'):
        config['postgresql'] = {
            "host": os.getenv('DB_HOST', 'localhost'),
            "port": int(os.getenv('DB_PORT', 5432)),
            "database": os.getenv('DB_NAME', 'psychsync'),
            "username": os.getenv('DB_USER'),
            "password": os.getenv('DB_PASSWORD')
        }

    if os.getenv('REDIS_HOST'):
        config['redis'] = {
            "host": os.getenv('REDIS_HOST', 'localhost'),
            "port": int(os.getenv('REDIS_PORT', 6379)),
            "password": os.getenv('REDIS_PASSWORD')
        }

    # Load config file if provided
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)

    return config

async def main():
    """Main execution function"""
    args = parse_arguments()
    config = load_config(args)

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print("🚀 Starting Comprehensive Database Security Testing Suite")
    print(f"🎯 Target: {config['api_base_url']}")
    print(f"🌍 Environment: {config['environment']}")
    print("-" * 60)

    master = DatabaseSecurityMaster(config)

    try:
        # Run selected tests
        if 'all' in args.tests:
            report = await master.run_all_tests()
        else:
            # Run specific tests
            if 'database' in args.tests:
                await master.run_database_security_tests()
            if 'injection' in args.tests:
                await master.run_nosql_injection_tests()
            if 'backup' in args.tests:
                await master.run_backup_security_tests()
            if 'privilege' in args.tests:
                await master.run_privilege_escalation_tests()
            if 'logs' in args.tests:
                await master.run_log_security_tests()

            report = await master.generate_consolidated_report(0)

        # Print summary
        exec_summary = report['executive_summary']
        print("\n📊 SECURITY ASSESSMENT COMPLETE")
        print("="*50)
        print(f"🔍 Total Findings: {exec_summary['total_findings']}")
        print(f"🚨 Critical: {exec_summary['critical_findings']}")
        print(f"⚠️  High: {exec_summary['high_findings']}")
        print(f"⚡ Medium: {exec_summary.get('medium_findings', 0)}")
        print(f"ℹ️  Low: {exec_summary.get('low_findings', 0)}")
        print(f"📈 Risk Score: {exec_summary['risk_score']}/100")
        print(f"🎯 Risk Level: {exec_summary['risk_level']}")
        print(f"✅ Overall Status: {exec_summary['overall_status']}")

        # Immediate actions needed
        if exec_summary['critical_findings'] > 0 or exec_summary['high_findings'] > 0:
            print(f"\n🚨 IMMEDIATE ACTION REQUIRED!")
            if exec_summary['critical_findings'] > 0:
                print(f"• {exec_summary['critical_findings']} critical vulnerabilities need immediate attention")
            if exec_summary['high_findings'] > 0:
                print(f"• {exec_summary['high_findings']} high-risk vulnerabilities need urgent attention")
            print(f"• Review detailed reports for specific remediation steps")

    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))