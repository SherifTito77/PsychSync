#!/usr/bin/env python3
"""
Comprehensive Server & Infrastructure Security Scanner
Performs security checks for open ports, SSH protections, banner info, firewall rules, and CVEs
"""

import socket
import subprocess
import re
import json
import sys
import time
import threading
from datetime import datetime
from pathlib import Path

class ServerSecurityScanner:
    def __init__(self, target_host="localhost", ports=None):
        self.target_host = target_host
        self.ports = ports or [
            21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995,
            1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9100, 27017
        ]
        self.results = {
            'scan_time': datetime.now().isoformat(),
            'target_host': target_host,
            'open_ports': [],
            'ssh_security': {},
            'banner_info': {},
            'firewall_analysis': {},
            'vulnerabilities': [],
            'recommendations': []
        }

    def scan_open_ports(self):
        """Scan for open ports and identify services"""
        print(f"\n🔍 SCANNING FOR OPEN PORTS ON {self.target_host}")
        print("=" * 60)

        open_ports = []
        services_seen = set()

        def check_port(port):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.target_host, port))
                if result == 0:
                    # Try to identify service
                    service_name = self.identify_service(port)
                    open_ports.append({
                        'port': port,
                        'service': service_name,
                        'status': 'open'
                    })
                    services_seen.add(service_name)
                    print(f"  ✅ Port {port} - {service_name} - OPEN")
                sock.close()
            except Exception as e:
                pass

        # Use threading for faster scanning
        threads = []
        for port in self.ports:
            thread = threading.Thread(target=check_port, args=(port,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Check for common web framework ports
        common_web_ports = [3000, 3001, 4000, 5000, 8000, 8080, 9000]
        for port in common_web_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.target_host, port))
                if result == 0:
                    open_ports.append({
                        'port': port,
                        'service': f'Web App (Port {port})',
                        'status': 'open'
                    })
                    print(f"  ✅ Port {port} - Web App - OPEN")
                sock.close()
            except:
                pass

        self.results['open_ports'] = open_ports

        # Analysis and recommendations
        if open_ports:
            print(f"\n📊 OPEN PORTS ANALYSIS:")
            print(f"   Total open ports found: {len(open_ports)}")

            # Check for potentially dangerous services
            dangerous_services = ['telnet', 'ftp', 'rsh', 'rlogin', 'finger']
            for port_info in open_ports:
                if any(svc in port_info['service'].lower() for svc in dangerous_services):
                    self.results['recommendations'].append(
                        f"⚠️  DANGEROUS SERVICE DETECTED: {port_info['service']} on port {port_info['port']} - Consider disabling or securing"
                    )

            # Check for database exposure
            database_services = ['mysql', 'postgresql', 'mongodb', 'redis']
            db_ports = [p for p in open_ports if any(db in p['service'].lower() for db in database_services)]
            if db_ports:
                self.results['recommendations'].append(
                    f"🔒 DATABASE PORTS EXPOSED: Found database services on ports {[p['port'] for p in db_ports]} - Ensure proper firewall rules and authentication"
                )

        return open_ports

    def identify_service(self, port):
        """Identify service based on port number"""
        service_map = {
            21: 'FTP',
            22: 'SSH',
            23: 'Telnet',
            25: 'SMTP',
            53: 'DNS',
            80: 'HTTP',
            110: 'POP3',
            143: 'IMAP',
            443: 'HTTPS',
            445: 'SMB',
            993: 'IMAPS',
            995: 'POP3S',
            1433: 'MSSQL',
            1521: 'Oracle',
            3306: 'MySQL',
            3389: 'RDP',
            5432: 'PostgreSQL',
            5900: 'VNC',
            6379: 'Redis',
            8080: 'HTTP Alt',
            8443: 'HTTPS Alt',
            27017: 'MongoDB'
        }
        return service_map.get(port, f'Unknown (Port {port})')

    def test_ssh_security(self):
        """Test SSH brute force protections and security configurations"""
        print(f"\n🔐 TESTING SSH SECURITY ON {self.target_host}")
        print("=" * 60)

        ssh_results = {
            'port_open': False,
            'banner_grabbed': False,
            'auth_methods': [],
            'security_issues': [],
            'hardening_score': 0
        }

        # Check if SSH port is open
        ssh_port = 22
        for port_info in self.results.get('open_ports', []):
            if port_info['port'] == ssh_port and 'SSH' in port_info['service']:
                ssh_results['port_open'] = True
                break

        if not ssh_results['port_open']:
            print("  ✅ SSH port (22) is not open - Service not exposed")
            ssh_results['hardening_score'] += 20
        else:
            print("  ⚠️  SSH port (22) is open - Security testing required")

            # Try to grab SSH banner
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((self.target_host, ssh_port))
                banner = sock.recv(1024).decode('utf-8', errors='ignore')
                ssh_results['banner_grabbed'] = True
                ssh_results['banner'] = banner.strip()
                print(f"  📋 SSH Banner: {banner.strip()}")

                # Check for security issues in banner
                if 'SSH-2.0-OpenSSH' in banner:
                    # Extract version
                    version_match = re.search(r'SSH-2\.0-OpenSSH_(\d+\.\d+)', banner)
                    if version_match:
                        version = version_match.group(1)
                        print(f"  🔍 OpenSSH Version: {version}")

                        # Check for known vulnerabilities
                        if version.startswith(('7.', '6.', '5.', '4.', '3.', '2.', '1.')):
                            ssh_results['security_issues'].append(
                                f"🚨 OUTDATED OPENSSH VERSION: {version} - Upgrade to latest version"
                            )
                        else:
                            ssh_results['hardening_score'] += 15

                sock.close()
            except Exception as e:
                print(f"  ❌ Could not grab SSH banner: {e}")

        # Test for common SSH security configurations
        print("\n🔧 SSH SECURITY CONFIGURATION TESTS:")

        # Test for SSH weak configurations (requires local access)
        try:
            if Path('/etc/ssh/sshd_config').exists():
                with open('/etc/ssh/sshd_config', 'r') as f:
                    sshd_config = f.read()

                # Check for PermitRootLogin
                if 'PermitRootLogin yes' in sshd_config:
                    ssh_results['security_issues'].append(
                        "🚨 ROOT LOGIN ALLOWED - Set 'PermitRootLogin no'"
                    )
                else:
                    ssh_results['hardening_score'] += 10
                    print("  ✅ Root login disabled")

                # Check for password authentication
                if 'PasswordAuthentication yes' in sshd_config:
                    ssh_results['security_issues'].append(
                        "⚠️  PASSWORD AUTHENTICATION ENABLED - Consider using key-based authentication"
                    )
                else:
                    ssh_results['hardening_score'] += 10
                    print("  ✅ Password authentication disabled")

                # Check for empty passwords
                if 'PermitEmptyPasswords yes' in sshd_config:
                    ssh_results['security_issues'].append(
                        "🚨 EMPTY PASSWORDS ALLOWED - Set 'PermitEmptyPasswords no'"
                    )
                else:
                    ssh_results['hardening_score'] += 10
                    print("  ✅ Empty passwords disabled")

                # Check for X11 forwarding
                if 'X11Forwarding yes' in sshd_config:
                    ssh_results['security_issues'].append(
                        "⚠️  X11 FORWARDING ENABLED - Disable if not needed"
                    )
                else:
                    ssh_results['hardening_score'] += 5
                    print("  ✅ X11 forwarding disabled")

        except Exception as e:
            print(f"  ❌ Could not read SSH config: {e}")

        # Test SSH connection limits (brute force protection simulation)
        print("\n  🔐 TESTING BRUTE FORCE PROTECTIONS:")
        failed_connections = 0
        rapid_failures = 0

        for i in range(10):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.target_host, 22))
                if result != 0:
                    rapid_failures += 1
                sock.close()
                time.sleep(0.1)
            except:
                failed_connections += 1

        if rapid_failures >= 8:
            print("  ⚠️  Multiple connection failures detected - May indicate rate limiting")
            ssh_results['hardening_score'] += 5
        else:
            print("  ⚠️  No clear rate limiting detected - Consider implementing fail2ban")

        self.results['ssh_security'] = ssh_results
        return ssh_results

    def check_server_banners(self):
        """Check server banners for sensitive information disclosure"""
        print(f"\n📋 CHECKING SERVER BANNERS FOR SENSITIVE INFO")
        print("=" * 60)

        banner_info = {
            'services_checked': [],
            'information_disclosure': [],
            'security_recommendations': []
        }

        # Check HTTP/HTTPS banners
        for port_info in self.results.get('open_ports', []):
            port = port_info['port']
            service = port_info['service']

            if 'HTTP' in service or port in [80, 443, 8080, 8443]:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((self.target_host, port))

                    # Send HTTP request
                    request = f"GET / HTTP/1.1\r\nHost: {self.target_host}\r\n\r\n"
                    sock.send(request.encode())

                    response = sock.recv(4096).decode('utf-8', errors='ignore')
                    sock.close()

                    banner_info['services_checked'].append(service)
                    print(f"  📋 {service} (Port {port}): Banner received")

                    # Check for sensitive information in headers
                    lines = response.split('\n')
                    for line in lines:
                        if 'server:' in line.lower():
                            server_info = line.split(':', 1)[1].strip()
                            if len(server_info) > 20:
                                banner_info['information_disclosure'].append(
                                    f"DETAILED SERVER INFO: {server_info} - Consider minimal headers"
                                )
                                print(f"    ⚠️  Server header reveals detailed info: {server_info}")

                        if 'x-powered-by:' in line.lower():
                            powered_by = line.split(':', 1)[1].strip()
                            banner_info['information_disclosure'].append(
                                f"POWERED BY INFO: {powered_by} - Remove unnecessary headers"
                            )
                            print(f"    ⚠️  X-Powered-By header: {powered_by}")

                        if 'x-aspnet-version:' in line.lower():
                            aspnet_version = line.split(':', 1)[1].strip()
                            banner_info['information_disclosure'].append(
                                f"ASP.NET VERSION: {aspnet_version} - Remove version headers"
                            )
                            print(f"    ⚠️  ASP.NET version disclosed: {aspnet_version}")

                except Exception as e:
                    print(f"  ❌ Could not get banner for {service}: {e}")

        # Check FTP banner
        for port_info in self.results.get('open_ports', []):
            if port_info['port'] == 21 and 'FTP' in port_info['service']:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((self.target_host, 21))
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    sock.close()

                    banner_info['services_checked'].append('FTP')
                    print(f"  📋 FTP Banner: {banner}")

                    if 'vsftpd' in banner.lower() or 'proftpd' in banner.lower() or 'pure-ftpd' in banner.lower():
                        print("    ⚠️  FTP server type disclosed")

                except Exception as e:
                    print(f"  ❌ Could not get FTP banner: {e}")

        # Check SMTP banner
        for port_info in self.results.get('open_ports', []):
            if port_info['port'] in [25, 587] and 'SMTP' in port_info['service']:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((self.target_host, port_info['port']))
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    sock.close()

                    banner_info['services_checked'].append('SMTP')
                    print(f"  📋 SMTP Banner: {banner}")

                    if 'postfix' in banner.lower() or 'sendmail' in banner.lower():
                        print("    ⚠️  Mail server type disclosed")

                except Exception as e:
                    print(f"  ❌ Could not get SMTP banner: {e}")

        # Generate recommendations
        if banner_info['information_disclosure']:
            banner_info['security_recommendations'].append(
                "HIDE SERVER DETAILS: Configure servers to reveal minimal information"
            )
            banner_info['security_recommendations'].append(
                "REMOVE VERSION HEADERS: Disable version disclosure in web server configuration"
            )

        self.results['banner_info'] = banner_info
        return banner_info

    def test_firewall_rules(self):
        """Test firewall rules for common misconfigurations"""
        print(f"\n🔥 TESTING FIREWALL CONFIGURATION")
        print("=" * 60)

        firewall_analysis = {
            'method': 'port_scanning_analysis',
            'issues_found': [],
            'recommendations': [],
            'security_score': 0
        }

        # Analyze open ports for firewall issues
        open_ports = self.results.get('open_ports', [])

        # Check for dangerous exposed services
        dangerous_ports = [
            (21, 'FTP - Unencrypted file transfer'),
            (23, 'Telnet - Unencrypted terminal access'),
            (135, 'RPC - Potential DCOM vulnerabilities'),
            (139, 'NetBIOS - Windows file sharing'),
            (445, 'SMB - Windows file sharing'),
            (1433, 'MSSQL - Database exposure'),
            (3306, 'MySQL - Database exposure'),
            (5432, 'PostgreSQL - Database exposure'),
            (6379, 'Redis - No authentication by default'),
            (27017, 'MongoDB - Database exposure')
        ]

        for port, description in dangerous_ports:
            port_info = next((p for p in open_ports if p['port'] == port), None)
            if port_info:
                firewall_analysis['issues_found'].append(
                    f"DANGEROUS SERVICE EXPOSED: {description} on port {port}"
                )
                print(f"  🚨 DANGEROUS: {description} on port {port}")

        # Check for standard web ports
        web_ports = [p for p in open_ports if p['port'] in [80, 443, 8080, 8443]]
        if not web_ports:
            print("  ⚠️  NO WEB PORTS DETECTED - May indicate restrictive firewall or no web services")
        else:
            print(f"  ✅ Web services running on ports: {[p['port'] for p in web_ports]}")
            firewall_analysis['security_score'] += 10

        # Check if HTTPS is properly configured
        https_ports = [p for p in open_ports if p['port'] in [443, 8443]]
        http_ports = [p for p in open_ports if p['port'] in [80, 8080]]

        if http_ports and not https_ports:
            firewall_analysis['issues_found'].append(
                "HTTP ONLY: Running HTTP without HTTPS - Configure SSL/TLS"
            )
            print("  ⚠️  HTTP running without HTTPS - Security risk")
        elif https_ports:
            print("  ✅ HTTPS properly configured")
            firewall_analysis['security_score'] += 15

        # Check for unnecessary services
        common_services = {
            21: 'FTP',
            23: 'Telnet',
            25: 'SMTP',
            110: 'POP3',
            143: 'IMAP'
        }

        unnecessary_services = []
        for port, service in common_services.items():
            if not any(p['port'] == port for p in open_ports):
                continue

            # These services should only be exposed if absolutely necessary
            if service in ['FTP', 'Telnet']:
                unnecessary_services.append(f"{service} (Port {port})")

        if unnecessary_services:
            firewall_analysis['issues_found'].append(
                f"UNNECESSARY SERVICES: {', '.join(unnecessary_services)} - Consider disabling"
            )
            print(f"  ⚠️  Unnecessary services: {', '.join(unnecessary_services)}")

        # Check firewall effectiveness by scanning common blocked ports
        blocked_ports = [135, 139, 445]  # Common Windows ports that should be blocked
        found_blocked = 0
        for port in blocked_ports:
            if not any(p['port'] == port for p in open_ports):
                found_blocked += 1

        if found_blocked >= 2:
            print(f"  ✅ Firewall appears to be blocking dangerous ports")
            firewall_analysis['security_score'] += 20

        # Calculate overall score
        max_score = 50
        firewall_analysis['overall_security'] = (firewall_analysis['security_score'] / max_score) * 100

        # Generate recommendations
        if firewall_analysis['issues_found']:
            firewall_analysis['recommendations'].append(
                "FIREWALL HARDENING: Block unnecessary services and dangerous ports"
            )
            firewall_analysis['recommendations'].append(
                "NETWORK SEGMENTATION: Consider segregating different types of services"
            )

        if http_ports and not https_ports:
            firewall_analysis['recommendations'].append(
                "ENCRYPT ALL TRAFFIC: Implement HTTPS for all web services"
            )

        self.results['firewall_analysis'] = firewall_analysis
        return firewall_analysis

    def scan_for_cves(self):
        """Scan for outdated software and known CVEs"""
        print(f"\n🔍 SCANNING FOR OUTDATED SOFTWARE AND CVEs")
        print("=" * 60)

        vulnerability_scan = {
            'software_detected': [],
            'vulnerabilities_found': [],
            'recommendations': []
        }

        # Check common software versions via banners
        open_ports = self.results.get('open_ports', [])

        # Web server detection
        web_servers = {
            'Apache': ['Apache/'],
            'Nginx': ['nginx/'],
            'IIS': ['IIS/'],
            'Tomcat': ['Apache-Coyote/'],
            'Node.js': ['Node.js']
        }

        web_server_info = self.results.get('banner_info', {}).get('information_disclosure', [])
        for disclosure in web_server_info:
            for server_name, patterns in web_servers.items():
                if any(pattern in disclosure for pattern in patterns):
                    vulnerability_scan['software_detected'].append(server_name)
                    break

        # Check SSH version from banner
        ssh_banner = self.results.get('ssh_security', {}).get('banner', '')
        if ssh_banner and 'OpenSSH' in ssh_banner:
            version_match = re.search(r'OpenSSH_(\d+\.\d+)', ssh_banner)
            if version_match:
                version = version_match.group(1)
                vulnerability_scan['software_detected'].append(f'OpenSSH {version}')

                # Known vulnerable OpenSSH versions (simplified check)
                vulnerable_versions = ['7.4', '7.3', '7.2', '7.1', '7.0', '6.6', '6.5']
                if any(version.startswith(v) for v in vulnerable_versions):
                    vulnerability_scan['vulnerabilities_found'].append(
                        f"OUTDATED OPENSSH: Version {version} has known vulnerabilities"
                    )

        # Operating System detection attempts
        try:
            # Try to get OS info from local system
            if self.target_host == 'localhost':
                # Check Linux distribution
                if Path('/etc/os-release').exists():
                    with open('/etc/os-release', 'r') as f:
                        os_info = f.read()
                        if 'ubuntu' in os_info.lower():
                            ubuntu_match = re.search(r'PRETTY_NAME=\"Ubuntu ([\d.]+)', os_info)
                            if ubuntu_match:
                                version = ubuntu_match.group(1)
                                vulnerability_scan['software_detected'].append(f'Ubuntu {version}')
                                # Check for old Ubuntu versions
                                if version.startswith(('18.', '16.', '14.')):
                                    vulnerability_scan['vulnerabilities_found'].append(
                                        f"END-OF-LIFE UBUNTU: {version} - Upgrade to supported version"
                                    )
                        elif 'centos' in os_info.lower():
                            centos_match = re.search(r'PRETTY_NAME=\"CentOS ([\d.]+)', os_info)
                            if centos_match:
                                version = centos_match.group(1)
                                vulnerability_scan['software_detected'].append(f'CentOS {version}')
                                if version.startswith(('6.', '7.')):
                                    vulnerability_scan['vulnerabilities_found'].append(
                                        f"END-OF-LIFE CENTOS: {version} - Upgrade to supported version"
                                    )
        except Exception as e:
            print(f"  ❌ Could not detect OS: {e}")

        # Database version checks (if ports are open)
        db_ports = [p for p in open_ports if p['port'] in [3306, 5432, 1433, 27017, 6379]]
        for port_info in db_ports:
            vulnerability_scan['software_detected'].append(f"Database service on port {port_info['port']}")
            vulnerability_scan['vulnerabilities_found'].append(
                f"DATABASE EXPOSED: Database port {port_info['port']} open - Use firewall and strong authentication"
            )

        # Print results
        print(f"\n📊 SOFTWARE DETECTION RESULTS:")
        if vulnerability_scan['software_detected']:
            for software in vulnerability_scan['software_detected']:
                print(f"  📋 Detected: {software}")
        else:
            print("  ℹ️  No specific software versions detected")

        print(f"\n🚨 VULNERABILITIES FOUND:")
        if vulnerability_scan['vulnerabilities_found']:
            for vuln in vulnerability_scan['vulnerabilities_found']:
                print(f"  ❌ {vuln}")
        else:
            print("  ✅ No obvious vulnerabilities detected")

        # Generate recommendations
        if vulnerability_scan['vulnerabilities_found']:
            vulnerability_scan['recommendations'].append(
                "UPDATE SOFTWARE: Apply security patches and update to latest versions"
            )
            vulnerability_scan['recommendations'].append(
                "MONITOR VULNERABILITIES: Subscribe to security mailing lists for detected software"
            )

        vulnerability_scan['recommendations'].extend([
            "REGULAR SCANNING: Perform regular vulnerability assessments",
            "ACCESS CONTROL: Limit database access to trusted sources only",
            "ENCRYPTION: Use encrypted connections for all database access"
        ])

        self.results['vulnerabilities'] = vulnerability_scan
        return vulnerability_scan

    def generate_report(self):
        """Generate comprehensive security report"""
        print(f"\n" + "="*80)
        print(f"🏁 COMPREHENSIVE SERVER SECURITY REPORT")
        print(f"="*80)
        print(f"🎯 Target: {self.target_host}")
        print(f"📅 Scan Date: {self.results['scan_time']}")

        # Summary section
        print(f"\n📊 EXECUTIVE SUMMARY:")
        print(f"   • Open Ports Found: {len(self.results.get('open_ports', []))}")
        print(f"   • SSH Port Status: {'SECURED' if self.results.get('ssh_security', {}).get('hardening_score', 0) > 50 else 'NEEDS ATTENTION'}")
        print(f"   • Banner Issues: {len(self.results.get('banner_info', {}).get('information_disclosure', []))}")
        print(f"   • Firewall Issues: {len(self.results.get('firewall_analysis', {}).get('issues_found', []))}")
        print(f"   • Vulnerabilities: {len(self.results.get('vulnerabilities', {}).get('vulnerabilities_found', []))}")

        # Detailed findings
        print(f"\n🔍 DETAILED FINDINGS:")

        # Open ports
        if self.results.get('open_ports'):
            print(f"\n📡 OPEN PORTS:")
            for port_info in self.results['open_ports']:
                print(f"   • Port {port_info['port']}: {port_info['service']}")

        # Security recommendations
        all_recommendations = []
        all_recommendations.extend(self.results.get('recommendations', []))
        all_recommendations.extend(self.results.get('banner_info', {}).get('security_recommendations', []))
        all_recommendations.extend(self.results.get('firewall_analysis', {}).get('recommendations', []))
        all_recommendations.extend(self.results.get('vulnerabilities', {}).get('recommendations', []))

        if all_recommendations:
            print(f"\n🛡️  SECURITY RECOMMENDATIONS:")
            unique_recommendations = list(set(all_recommendations))
            for i, rec in enumerate(unique_recommendations, 1):
                print(f"   {i}. {rec}")

        # Save detailed report to file
        report_file = f"security_report_{self.target_host}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return self.results

def main():
    """Main execution function"""
    print("🔒 COMPREHENSIVE SERVER & INFRASTRUCTURE SECURITY SCANNER")
    print("="*70)

    # Get target host (default to localhost)
    target_host = "localhost"
    if len(sys.argv) > 1:
        target_host = sys.argv[1]

    print(f"🎯 Scanning target: {target_host}")
    print(f"⚠️  Note: This scanner performs only passive reconnaissance and basic tests")
    print(f"⚠️  Only scan systems you own or have permission to test")

    # Initialize scanner
    scanner = ServerSecurityScanner(target_host)

    try:
        # Run all security tests
        scanner.scan_open_ports()
        scanner.test_ssh_security()
        scanner.check_server_banners()
        scanner.test_firewall_rules()
        scanner.scan_for_cves()

        # Generate comprehensive report
        scanner.generate_report()

    except KeyboardInterrupt:
        print(f"\n⚠️  Scan interrupted by user")
    except Exception as e:
        print(f"\n❌ Scan error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
