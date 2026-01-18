#!/usr/bin/env python3
"""
Simple CVE Vulnerability Scanner
Checks for common security vulnerabilities in detected software
"""

import subprocess
import re
import json
from datetime import datetime
from pathlib import Path

class SimpleCVEScanner:
    def __init__(self):
        self.results = {
            'scan_time': datetime.now().isoformat(),
            'target': 'localhost',
            'software_detected': [],
            'vulnerabilities_found': [],
            'security_recommendations': []
        }

    def scan_software_versions(self):
        """Scan for installed software versions"""
        print("🔍 SCANNING SOFTWARE VERSIONS")
        print("=" * 50)

        software_detected = []

        # Operating System
        print("🖥️  OPERATING SYSTEM:")
        try:
            if Path('/etc/os-release').exists():
                with open('/etc/os-release', 'r') as f:
                    os_info = f.read()

                print(f"   OS Info detected")
                software_detected.append({
                    'name': 'Linux',
                    'version': 'unknown',
                    'type': 'os',
                    'source': 'os-release'
                })
        except Exception as e:
            print(f"   ❌ Could not read OS info: {e}")

        # Database systems
        print("\n🗄️  DATABASE SYSTEMS:")

        # PostgreSQL
        try:
            result = subprocess.run(['psql', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_match = re.search(r'PostgreSQL (\d+\.\d+)', result.stdout)
                if version_match:
                    version = version_match.group(1)
                    print(f"   PostgreSQL {version}")
                    software_detected.append({
                        'name': 'PostgreSQL',
                        'version': version,
                        'type': 'database',
                        'source': 'command'
                    })
        except Exception as e:
            print("   PostgreSQL not found")

        # Redis
        try:
            result = subprocess.run(['redis-server', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_match = re.search(r'Redis server v=([\d\.]+)', result.stdout)
                if version_match:
                    version = version_match.group(1)
                    print(f"   Redis {version}")
                    software_detected.append({
                        'name': 'Redis',
                        'version': version,
                        'type': 'cache',
                        'source': 'command'
                    })
        except Exception as e:
            print("   Redis not found")

        # Web servers
        print("\n🌐 WEB SERVERS:")

        # Nginx
        try:
            result = subprocess.run(['nginx', '-v'], capture_output=True, text=True, timeout=5)
            version_match = re.search(r'nginx/([\d\.]+)', result.stderr)
            if version_match:
                version = version_match.group(1)
                print(f"   Nginx {version}")
                software_detected.append({
                    'name': 'Nginx',
                    'version': version,
                    'type': 'webserver',
                    'source': 'command'
                })
        except Exception as e:
            print("   Nginx not found")

        # Python
        print("\n🐍 PROGRAMMING RUNTIMES:")
        try:
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_match = re.search(r'Python ([\d\.]+)', result.stdout)
                if version_match:
                    version = version_match.group(1)
                    print(f"   Python {version}")
                    software_detected.append({
                        'name': 'Python',
                        'version': version,
                        'type': 'runtime',
                        'source': 'command'
                    })
        except Exception as e:
            print("   Python not found")

        self.results['software_detected'] = software_detected
        return software_detected

    def check_vulnerabilities(self):
        """Check detected software against known vulnerabilities"""
        print("\n🚨 VULNERABILITY ASSESSMENT")
        print("=" * 50)

        # Simplified vulnerability database
        vulnerable_software = {
            'PostgreSQL': {
                '9.6': 'CVE-2018-1058 - Memory disclosure vulnerability',
                '9.5': 'CVE-2017-8464 - Memory leak vulnerability',
                '9.4': 'CVE-2017-7598 - Session handling issues'
            },
            'Redis': {
                '3.2': 'CVE-2015-4335 - Integer overflow vulnerability',
                '2.8': 'CVE-2015-4335 - Integer overflow vulnerability'
            },
            'Nginx': {
                '1.14': 'CVE-2018-16845 - Integer overflow vulnerability',
                '1.13': 'CVE-2017-7529 - Range filter vulnerability'
            },
            'Python': {
                '3.6': 'Multiple security issues - Upgrade to 3.7+',
                '2.7': 'END OF LIFE - No security updates'
            }
        }

        vulnerabilities_found = []

        for software in self.results['software_detected']:
            name = software['name']
            version = software['version']

            if name in vulnerable_software:
                for vuln_version, description in vulnerable_software[name].items():
                    if version.startswith(vuln_version):
                        vulnerabilities_found.append({
                            'software': name,
                            'version': version,
                            'vulnerability': description,
                            'severity': 'HIGH'
                        })
                        print(f"   ❌ {name} {version}: {description}")

        # Additional security checks
        print("\n🔍 ADDITIONAL SECURITY CHECKS:")

        # Check for common security issues
        security_issues = []

        # Check if running as root
        try:
            result = subprocess.run(['id', '-u'], capture_output=True, text=True)
            if result.stdout.strip() == '0':
                security_issues.append("Running as root - security risk")
                print("   ⚠️  Running as root user")
        except Exception as e:
            pass

        # Check for common vulnerable packages
        vulnerable_packages = ['openssl 1.0.2', 'openssh 7.4', 'apache 2.4.29']
        for package in vulnerable_packages:
            try:
                pkg_name, pkg_version = package.split()
                result = subprocess.run(['dpkg', '-l', pkg_name], capture_output=True, text=True)
                if pkg_version in result.stdout:
                    security_issues.append(f"Vulnerable package: {package}")
                    print(f"   ❌ Vulnerable package found: {package}")
            except Exception as e:
                pass

        self.results['vulnerabilities_found'] = vulnerabilities_found + security_issues
        return len(vulnerabilities_found) + len(security_issues)

    def generate_recommendations(self):
        """Generate security recommendations"""
        print("\n🛡️  SECURITY RECOMMENDATIONS")
        print("=" * 50)

        recommendations = [
            "🔄 SOFTWARE UPDATES:",
            "   • Keep all software packages updated",
            "   • Use package managers with security updates (apt, yum)",
            "   • Subscribe to security mailing lists for installed software",
            "",
            "🔐 CONFIGURATION SECURITY:",
            "   • Disable unnecessary services and ports",
            "   • Use firewalls to restrict access",
            "   • Implement proper access controls",
            "   • Regular security audits and penetration testing",
            "",
            "📊 MONITORING:",
            "   • Monitor for suspicious activities",
            "   • Use intrusion detection systems",
            "   • Regular backup and recovery testing",
            "   • Log analysis and alerting"
        ]

        for rec in recommendations:
            print(rec)

        # Add specific recommendations based on findings
        if self.results['vulnerabilities_found']:
            print(f"\n⚠️  URGENT - {len(self.results['vulnerabilities_found'])} VULNERABILITIES FOUND:")
            for vuln in self.results['vulnerabilities_found']:
                if isinstance(vuln, dict):
                    print(f"   • Update {vuln['software']} to address: {vuln['vulnerability']}")
                else:
                    print(f"   • {vuln}")
        else:
            print(f"\n✅ No critical vulnerabilities detected")

        self.results['security_recommendations'] = recommendations

    def generate_report(self):
        """Generate comprehensive security report"""
        print(f"\n" + "="*70)
        print(f"🏁 CVE VULNERABILITY SCAN REPORT")
        print(f"="*70)
        print(f"🎯 Target: {self.results['target']}")
        print(f"📅 Scan Date: {self.results['scan_time']}")

        # Summary
        print(f"\n📊 EXECUTIVE SUMMARY:")
        print(f"   • Software Packages Detected: {len(self.results['software_detected'])}")
        print(f"   • Vulnerabilities Found: {len(self.results['vulnerabilities_found'])}")
        print(f"   • Security Recommendations: {len(self.results['security_recommendations'])}")

        # Risk assessment
        if self.results['vulnerabilities_found']:
            print(f"   🚨 RISK LEVEL: HIGH - Immediate action required")
        else:
            print(f"   ✅ RISK LEVEL: LOW - Basic security posture good")

        # Save detailed report
        report_file = f"cve_vulnerability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main execution function"""
    print("🔒 CVE VULNERABILITY SCANNER")
    print("="*50)

    scanner = SimpleCVEScanner()

    try:
        # Run comprehensive vulnerability scan
        scanner.scan_software_versions()
        vuln_count = scanner.check_vulnerabilities()
        scanner.generate_recommendations()
        scanner.generate_report()

    except KeyboardInterrupt:
        print(f"\n⚠️  Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Scan error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
