#!/usr/bin/env python3
"""
SSH Brute Force Protection Testing Tool
Tests SSH server resilience against brute force attacks and configuration security
"""

import socket
import threading
import time
import paramiko
import sys
import subprocess
import re
from datetime import datetime
from collections import defaultdict

class SSHBruteForceTester:
    def __init__(self, target_host, target_port=22):
        self.target_host = target_host
        self.target_port = target_port
        self.results = {
            'scan_time': datetime.now().isoformat(),
            'target': f"{target_host}:{target_port}",
            'connection_tests': [],
            'configuration_analysis': {},
            'brute_force_resistance': {},
            'security_recommendations': []
        }

    def test_basic_connectivity(self):
        """Test basic SSH connectivity"""
        print(f"🔍 TESTING SSH CONNECTIVITY TO {self.target_host}:{self.target_port}")
        print("=" * 60)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.target_host, self.target_port))

            if result == 0:
                print("✅ SSH port is open and accepting connections")

                # Get SSH banner
                try:
                    banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                    print(f"📋 SSH Banner: {banner}")
                    self.results['banner'] = banner
                    sock.close()
                    return True
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    sock.close()
                    return True
            else:
                print("❌ SSH port is not accessible")
                return False

        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def analyze_ssh_configuration(self):
        """Analyze SSH server configuration for security issues"""
        print(f"\n🔧 ANALYZING SSH CONFIGURATION")
        print("=" * 60)

        config_analysis = {
            'config_file_found': False,
            'security_settings': {},
            'vulnerabilities': [],
            'hardening_score': 0
        }

        # Check SSH config file
        ssh_config_paths = ['/etc/ssh/sshd_config', '/etc/ssh/ssh_config']
        for config_path in ssh_config_paths:
            if config_path.endswith('sshd_config') and Path(config_path).exists():
                config_analysis['config_file_found'] = True
                try:
                    with open(config_path, 'r') as f:
                        config_content = f.read()

                    print("📋 SSHD Configuration Analysis:")

                    # Analyze critical security settings
                    security_checks = {
                        'PermitRootLogin': {
                            'pattern': r'PermitRootLogin\s+(yes|no)',
                            'secure': 'no',
                            'description': 'Root login access'
                        },
                        'PasswordAuthentication': {
                            'pattern': r'PasswordAuthentication\s+(yes|no)',
                            'secure': 'no',
                            'description': 'Password authentication'
                        },
                        'PubkeyAuthentication': {
                            'pattern': r'PubkeyAuthentication\s+(yes|no)',
                            'secure': 'yes',
                            'description': 'Public key authentication'
                        },
                        'PermitEmptyPasswords': {
                            'pattern': r'PermitEmptyPasswords\s+(yes|no)',
                            'secure': 'no',
                            'description': 'Empty passwords'
                        },
                        'X11Forwarding': {
                            'pattern': r'X11Forwarding\s+(yes|no)',
                            'secure': 'no',
                            'description': 'X11 forwarding'
                        },
                        'MaxAuthTries': {
                            'pattern': r'MaxAuthTries\s+(\d+)',
                            'secure': '3-6',
                            'description': 'Maximum authentication attempts'
                        },
                        'LoginGraceTime': {
                            'pattern': r'LoginGraceTime\s+(\d+)',
                            'secure': '30-60',
                            'description': 'Login grace time'
                        },
                        'Port': {
                            'pattern': r'Port\s+(\d+)',
                            'secure': 'not_default',
                            'description': 'SSH port'
                        }
                    }

                    for setting, config in security_checks.items():
                        match = re.search(config['pattern'], config_content)
                        if match:
                            value = match.group(1)
                            config_analysis['security_settings'][setting] = value

                            if setting == 'Port' and value == '22':
                                config_analysis['vulnerabilities'].append(
                                    f"DEFAULT SSH PORT: Using port 22 - Consider changing to non-standard port"
                                )
                            elif setting == 'MaxAuthTries':
                                try:
                                    tries = int(value)
                                    if tries > 6:
                                        config_analysis['vulnerabilities'].append(
                                            f"HIGH MAX AUTH TRIES: {tries} - Recommend 3-6"
                                        )
                                    else:
                                        print(f"  ✅ {config['description']}: {value} (Secure)")
                                        config_analysis['hardening_score'] += 5
                                except Exception as e:
                                    pass
                            elif setting == 'LoginGraceTime':
                                try:
                                    grace_time = int(value)
                                    if grace_time > 120:
                                        config_analysis['vulnerabilities'].append(
                                            f"HIGH LOGIN GRACE TIME: {grace_time}s - Recommend 30-60s"
                                        )
                                    else:
                                        print(f"  ✅ {config['description']}: {value}s (Secure)")
                                        config_analysis['hardening_score'] += 5
                                except Exception as e:
                                    pass
                            else:
                                if value == config.get('secure') or (setting == 'Port' and value != '22'):
                                    print(f"  ✅ {config['description']}: {value} (Secure)")
                                    config_analysis['hardening_score'] += 10
                                elif value != config.get('secure') and config.get('secure') != 'not_default':
                                    print(f"  ⚠️  {config['description']}: {value} (Security Risk)")
                                    config_analysis['vulnerabilities'].append(
                                        f"{config['description']} set to {value} - Should be {config['secure']}"
                                    )
                        else:
                            print(f"  ❓ {config['description']}: Not explicitly set")

                except Exception as e:
                    print(f"  ❌ Error reading SSH config: {e}")
            break

        if not config_analysis['config_file_found']:
            print("  ❌ SSH config file not found")
            config_analysis['vulnerabilities'].append("SSH config file not accessible")

        self.results['configuration_analysis'] = config_analysis
        return config_analysis

    def test_connection_limiting(self, test_duration=30):
        """Test SSH server's resistance to rapid connections"""
        print(f"\n🚨 TESTING CONNECTION LIMITING AND BRUTE FORCE RESISTANCE")
        print("=" * 60)
        print(f"Testing with {test_duration} seconds of rapid connection attempts...")

        connection_stats = {
            'total_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'timeouts': 0,
            'blocked_connections': 0,
            'connection_times': []
        }

        start_time = time.time()

        def rapid_connection_test(test_id):
            """Individual connection test"""
            try:
                conn_start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((self.target_host, self.target_port))
                conn_time = time.time() - conn_start
                sock.close()

                connection_stats['connection_times'].append(conn_time)
                connection_stats['total_attempts'] += 1

                if result == 0:
                    connection_stats['successful_connections'] += 1
                    if test_id < 5:  # Only print first few to avoid spam
                        print(f"  ✅ Connection {test_id}: SUCCESS ({conn_time:.3f}s)")
                else:
                    connection_stats['failed_connections'] += 1
                    if result == 11:  # Connection refused
                        connection_stats['blocked_connections'] += 1
                        if test_id < 5:
                            print(f"  🚫 Connection {test_id}: BLOCKED")
                    elif test_id < 5:
                        print(f"  ❌ Connection {test_id}: FAILED")

            except socket.timeout:
                connection_stats['timeouts'] += 1
                if test_id < 5:
                    print(f"  ⏱️  Connection {test_id}: TIMEOUT")
            except Exception as e:
                if test_id < 5:
                    print(f"  ❌ Connection {test_id}: ERROR - {e}")

        # Launch multiple connection attempts
        threads = []
        test_counter = 0

        while time.time() - start_time < test_duration:
            # Launch burst of connections
            for i in range(5):  # 5 concurrent connections
                thread = threading.Thread(target=rapid_connection_test, args=(test_counter,))
                threads.append(thread)
                thread.start()
                test_counter += 1

            # Wait for this burst to complete
            for thread in threads:
                thread.join()

            threads = []
            time.sleep(0.5)  # Brief pause between bursts

        # Calculate statistics
        total_time = time.time() - start_time
        if connection_stats['connection_times']:
            avg_connection_time = sum(connection_stats['connection_times']) / len(connection_stats['connection_times'])
            min_connection_time = min(connection_stats['connection_times'])
            max_connection_time = max(connection_stats['connection_times'])
        else:
            avg_connection_time = min_connection_time = max_connection_time = 0

        resistance_score = {
            'total_attempts': connection_stats['total_attempts'],
            'duration_seconds': round(total_time, 2),
            'successful_connections': connection_stats['successful_connections'],
            'blocked_connections': connection_stats['blocked_connections'],
            'timeouts': connection_stats['timeouts'],
            'avg_connection_time': round(avg_connection_time, 3),
            'min_connection_time': round(min_connection_time, 3),
            'max_connection_time': round(max_connection_time, 3),
            'attempts_per_second': round(connection_stats['total_attempts'] / total_time, 2)
        }

        print(f"\n📊 CONNECTION LIMITING TEST RESULTS:")
        print(f"   Total connection attempts: {resistance_score['total_attempts']}")
        print(f"   Successful connections: {resistance_score['successful_connections']}")
        print(f"   Blocked connections: {resistance_score['blocked_connections']}")
        print(f"   Timeouts: {resistance_score['timeouts']}")
        print(f"   Average connection time: {resistance_score['avg_connection_time']}s")
        print(f"   Attempts per second: {resistance_score['attempts_per_second']}")

        # Analyze results
        if resistance_score['blocked_connections'] > resistance_score['successful_connections']:
            print(f"\n  ✅ GOOD: More connections blocked than successful (rate limiting working)")
            resistance_score['brute_force_resistance'] = 'HIGH'
        elif resistance_score['blocked_connections'] > 0:
            print(f"\n  ⚠️  PARTIAL: Some connections blocked (basic rate limiting)")
            resistance_score['brute_force_resistance'] = 'MEDIUM'
        else:
            print(f"\n  ❌ POOR: No connection blocking detected (vulnerable to brute force)")
            resistance_score['brute_force_resistance'] = 'LOW'
            self.results['security_recommendations'].append(
                "IMPLEMENT RATE LIMITING: Use fail2ban or similar tools to block brute force attempts"
            )

        self.results['brute_force_resistance'] = resistance_score
        return resistance_score

    def test_authentication_methods(self):
        """Test available SSH authentication methods"""
        print(f"\n🔍 TESTING SSH AUTHENTICATION METHODS")
        print("=" * 60)

        try:
            # Use paramiko to test authentication methods
            transport = paramiko.Transport((self.target_host, self.target_port))
            transport.connect()
            auth_methods = transport.get_remote_server_key()

            print("✅ SSH connection established")

            # Get available authentication methods
            session = transport.open_session()
            try:
                methods = transport.auth_none('')
                print(f"🔐 Available authentication methods: {methods}")

                # Check for weak authentication methods
                weak_methods = ['password', 'keyboard-interactive']
                found_weak = [method for method in methods if method in weak_methods]

                if found_weak:
                    print("⚠️  Weak authentication methods detected:")
                    for method in found_weak:
                        print(f"   • {method}")
                    self.results['security_recommendations'].append(
                        "DISABLE PASSWORD AUTH: Use only public key authentication for better security"
                    )
                else:
                    print("✅ No weak authentication methods detected")

            except paramiko.AuthenticationException:
                print("🔐 Server requires authentication (expected)")

            transport.close()

        except Exception as e:
            print(f"❌ Could not test authentication methods: {e}")

    def generate_recommendations(self):
        """Generate comprehensive security recommendations"""
        print(f"\n🛡️  SECURITY RECOMMENDATIONS")
        print("=" * 60)

        recommendations = []

        # SSH hardening recommendations
        recommendations.extend([
            "🔐 SSH HARDENING:",
            "   • Change default SSH port from 22 to a non-standard port",
            "   • Disable root login: PermitRootLogin no",
            "   • Disable password authentication: PasswordAuthentication no",
            "   • Use only public key authentication",
            "   • Set MaxAuthTries to 3-6 attempts",
            "   • Set LoginGraceTime to 30-60 seconds",
            "   • Disable X11Forwarding if not needed",
            "",
            "🚨 BRUTE FORCE PROTECTION:",
            "   • Install and configure fail2ban",
            "   • Implement IP whitelisting for SSH access",
            "   • Use VPN for remote SSH access",
            "   • Monitor authentication logs regularly",
            "   • Consider using SSH keys with passphrases",
            "",
            "🔍 MONITORING & LOGGING:",
            "   • Enable verbose SSH logging",
            "   • Monitor failed login attempts",
            "   • Set up alerting for suspicious activity",
            "   • Regular security audits of SSH configurations",
            "",
            "🌐 NETWORK SECURITY:",
            "   • Use firewall to restrict SSH access to specific IPs",
            "   • Implement network segmentation",
            "   • Use jump hosts for additional security",
        ])

        for rec in recommendations:
            print(rec)

        # Add specific recommendations based on scan results
        if self.results['configuration_analysis'].get('vulnerabilities'):
            print(f"\n📋 SPECIFIC VULNERABILITIES FOUND:")
            for vuln in self.results['configuration_analysis']['vulnerabilities']:
                print(f"   • {vuln}")

        self.results['security_recommendations'] = recommendations

    def generate_report(self):
        """Generate comprehensive security report"""
        print(f"\n" + "="*80)
        print(f"🏁 SSH BRUTE FORCE PROTECTION TEST REPORT")
        print(f"="*80)
        print(f"🎯 Target: {self.results['target']}")
        print(f"📅 Test Date: {self.results['scan_time']}")

        # Summary
        print(f"\n📊 EXECUTIVE SUMMARY:")

        config_score = self.results.get('configuration_analysis', {}).get('hardening_score', 0)
        resistance = self.results.get('brute_force_resistance', {}).get('brute_force_resistance', 'UNKNOWN')

        print(f"   • SSH Configuration Security Score: {config_score}/100")
        print(f"   • Brute Force Resistance: {resistance}")
        print(f"   • Total Security Recommendations: {len(self.results.get('security_recommendations', []))}")

        # Save detailed report
        report_file = f"ssh_security_report_{self.target_host}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main execution function"""
    print("🔒 SSH BRUTE FORCE PROTECTION TESTING TOOL")
    print("="*60)

    target_host = "localhost"
    if len(sys.argv) > 1:
        target_host = sys.argv[1]

    print(f"🎯 Target SSH Server: {target_host}")
    print(f"⚠️  Only test systems you own or have explicit permission to test")

    tester = SSHBruteForceTester(target_host)

    try:
        # Run comprehensive SSH security tests
        if tester.test_basic_connectivity():
            tester.analyze_ssh_configuration()
            tester.test_connection_limiting(test_duration=30)
            tester.test_authentication_methods()

        tester.generate_recommendations()
        tester.generate_report()

    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
