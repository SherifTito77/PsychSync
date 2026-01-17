#!/usr/bin/env python3
"""
Simple SSH Security Testing Tool
Tests SSH configuration and brute force resistance without external dependencies
"""

import socket
import threading
import time
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class SimpleSSHSecurityTester:
    def __init__(self, target_host, target_port=22):
        self.target_host = target_host
        self.target_port = target_port
        self.results = {
            'scan_time': datetime.now().isoformat(),
            'target': f"{target_host}:{target_port}",
            'connectivity_test': False,
            'configuration_analysis': {},
            'brute_force_test': {},
            'security_recommendations': []
        }

    def test_connectivity(self):
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
                    self.results['ssh_banner'] = banner

                    # Extract SSH version information
                    if 'SSH-2.0-OpenSSH' in banner:
                        version_match = re.search(r'SSH-2\.0-OpenSSH_(\d+\.\d+)', banner)
                        if version_match:
                            version = version_match.group(1)
                            print(f"🔍 OpenSSH Version: {version}")
                            self.results['openssh_version'] = version

                            # Check for known vulnerable versions
                            vulnerable_versions = ['7.4', '7.3', '7.2', '7.1', '7.0', '6.6', '6.5']
                            if version.startswith(tuple(vulnerable_versions)):
                                self.results['security_recommendations'].append(
                                    f"🚨 OUTDATED OPENSSH: Version {version} has known vulnerabilities - Upgrade to latest version"
                                )
                                print(f"  ⚠️  OUTDATED: OpenSSH {version} should be upgraded")
                            else:
                                print(f"  ✅ OpenSSH {version} appears to be recent")

                    sock.close()
                    self.results['connectivity_test'] = True
                    return True

                except Exception as e:
                    print(f"  ❌ Could not read banner: {e}")
                    sock.close()
                    self.results['connectivity_test'] = True
                    return True
            else:
                print("❌ SSH port is not accessible")
                self.results['security_recommendations'].append(
                    "SSH port not accessible - No services exposed on port 22"
                )
                return False

        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def analyze_local_ssh_config(self):
        """Analyze local SSH configuration files"""
        print(f"\n🔧 ANALYZING SSH CONFIGURATION")
        print("=" * 60)

        config_analysis = {
            'config_file_found': False,
            'security_settings': {},
            'vulnerabilities': [],
            'hardening_score': 0
        }

        # Check SSH daemon config
        sshd_config_path = '/etc/ssh/sshd_config'
        if Path(sshd_config_path).exists():
            config_analysis['config_file_found'] = True
            print("📋 Analyzing SSHD Configuration:")

            try:
                with open(sshd_config_path, 'r') as f:
                    config_content = f.read()

                # Analyze critical security settings
                security_settings = {
                    'PermitRootLogin': {
                        'pattern': r'PermitRootLogin\s+(yes|no)',
                        'value': None,
                        'secure': 'no',
                        'description': 'Root login access'
                    },
                    'PasswordAuthentication': {
                        'pattern': r'PasswordAuthentication\s+(yes|no)',
                        'value': None,
                        'secure': 'no',
                        'description': 'Password authentication'
                    },
                    'PubkeyAuthentication': {
                        'pattern': r'PubkeyAuthentication\s+(yes|no)',
                        'value': None,
                        'secure': 'yes',
                        'description': 'Public key authentication'
                    },
                    'PermitEmptyPasswords': {
                        'pattern': r'PermitEmptyPasswords\s+(yes|no)',
                        'value': None,
                        'secure': 'no',
                        'description': 'Empty passwords'
                    },
                    'X11Forwarding': {
                        'pattern': r'X11Forwarding\s+(yes|no)',
                        'value': None,
                        'secure': 'no',
                        'description': 'X11 forwarding'
                    },
                    'MaxAuthTries': {
                        'pattern': r'MaxAuthTries\s+(\d+)',
                        'value': None,
                        'secure_range': '3-6',
                        'description': 'Maximum authentication attempts'
                    },
                    'LoginGraceTime': {
                        'pattern': r'LoginGraceTime\s+(\d+)',
                        'value': None,
                        'secure_range': '30-60',
                        'description': 'Login grace time'
                    },
                    'ClientAliveInterval': {
                        'pattern': r'ClientAliveInterval\s+(\d+)',
                        'value': None,
                        'secure_range': '300-900',
                        'description': 'Client keep-alive interval'
                    },
                    'Port': {
                        'pattern': r'Port\s+(\d+)',
                        'value': None,
                        'secure': 'not_default',
                        'description': 'SSH port number'
                    }
                }

                for setting, config in security_settings.items():
                    match = re.search(config['pattern'], config_content)
                    if match:
                        value = match.group(1)
                        config['value'] = value
                        config_analysis['security_settings'][setting] = value

                        # Analyze the setting
                        if setting == 'Port' and value == '22':
                            config_analysis['vulnerabilities'].append(
                                "DEFAULT SSH PORT: Using port 22 - Consider changing to non-standard port"
                            )
                            print(f"  ⚠️  {config['description']}: Port {value} (Security Risk)")
                        elif setting in ['MaxAuthTries', 'LoginGraceTime', 'ClientAliveInterval']:
                            try:
                                num_value = int(value)
                                if 'secure_range' in config:
                                    if config['secure_range'] == '3-6':
                                        if not (3 <= num_value <= 6):
                                            config_analysis['vulnerabilities'].append(
                                                f"INSECURE {setting}: {num_value} (should be 3-6)"
                                            )
                                            print(f"  ⚠️  {config['description']}: {num_value} (Insecure Range)")
                                        else:
                                            print(f"  ✅ {config['description']}: {num_value} (Secure)")
                                            config_analysis['hardening_score'] += 10
                                    elif config['secure_range'] == '30-60':
                                        if not (30 <= num_value <= 60):
                                            config_analysis['vulnerabilities'].append(
                                                f"INSECURE {setting}: {num_value}s (should be 30-60s)"
                                            )
                                            print(f"  ⚠️  {config['description']}: {num_value}s (Insecure Range)")
                                        else:
                                            print(f"  ✅ {config['description']}: {num_value}s (Secure)")
                                            config_analysis['hardening_score'] += 10
                                    elif config['secure_range'] == '300-900':
                                        if not (300 <= num_value <= 900):
                                            config_analysis['vulnerabilities'].append(
                                                f"INSECURE {setting}: {num_value}s (should be 300-900s)"
                                            )
                                            print(f"  ⚠️  {config['description']}: {num_value}s (Insecure Range)")
                                        else:
                                            print(f"  ✅ {config['description']}: {num_value}s (Secure)")
                                            config_analysis['hardening_score'] += 5
                            except ValueError:
                                config_analysis['vulnerabilities'].append(
                                    f"INVALID {setting} VALUE: {value} (should be numeric)"
                                )
                        else:
                            # Check if value matches secure setting
                            if value == config.get('secure'):
                                print(f"  ✅ {config['description']}: {value} (Secure)")
                                config_analysis['hardening_score'] += 15
                            elif value == config.get('secure') + 's' and config['description'].endswith('interval'):
                                # Handle time-based settings
                                continue
                            elif value != config.get('secure') and config['secure'] != 'not_default':
                                print(f"  ⚠️  {config['description']}: {value} (Security Risk)")
                                config_analysis['vulnerabilities'].append(
                                    f"INSECURE {config['description']}: {value} - Should be {config['secure']}"
                                )

                    else:
                        print(f"  ❓ {config['description']}: Not explicitly set")

            except Exception as e:
                print(f"  ❌ Error reading SSH config: {e}")
        else:
            print("  ❌ SSHD config file not found")
            config_analysis['vulnerabilities'].append("SSH config file not accessible for analysis")

        self.results['configuration_analysis'] = config_analysis
        return config_analysis

    def test_brute_force_resistance(self, duration=30):
        """Test SSH resistance to rapid connections"""
        print(f"\n🚨 TESTING SSH BRUTE FORCE RESISTANCE")
        print("=" * 60)
        print(f"Testing with {duration} seconds of rapid connection attempts...")

        if not self.results['connectivity_test']:
            print("❌ SSH not accessible - cannot test brute force resistance")
            return

        connection_stats = {
            'total_attempts': 0,
            'successful_connections': 0,
            'failed_connections': 0,
            'timeouts': 0,
            'blocked_connections': 0,
            'start_time': time.time(),
            'connection_times': []
        }

        def test_connection(test_id):
            """Test individual SSH connection"""
            try:
                conn_start = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((self.target_host, self.target_port))
                conn_time = time.time() - conn_start

                # Quick read of banner
                try:
                    banner = sock.recv(256)
                    connection_stats['connection_times'].append(conn_time)
                    sock.close()
                except:
                    pass

                connection_stats['total_attempts'] += 1

                if result == 0:
                    connection_stats['successful_connections'] += 1
                    if test_id < 5:  # Only print first few
                        print(f"  ✅ Connection {test_id}: SUCCESS ({conn_time:.3f}s)")
                else:
                    connection_stats['failed_connections'] += 1
                    if result == 11:  # Connection refused
                        connection_stats['blocked_connections'] += 1
                        if test_id < 5:
                            print(f"  🚫 Connection {test_id}: BLOCKED (Connection refused)")
                    elif test_id < 5:
                        print(f"  ❌ Connection {test_id}: FAILED (Error {result})")

            except socket.timeout:
                connection_stats['timeouts'] += 1
                connection_stats['total_attempts'] += 1
                if test_id < 5:
                    print(f"  ⏱️  Connection {test_id}: TIMEOUT")
            except Exception as e:
                connection_stats['failed_connections'] += 1
                connection_stats['total_attempts'] += 1
                if test_id < 5:
                    print(f"  ❌ Connection {test_id}: ERROR - {e}")

        start_time = time.time()
        test_counter = 0

        # Run connection tests for specified duration
        while time.time() - start_time < duration:
            # Launch burst of connections
            threads = []
            for i in range(3):  # 3 concurrent connections
                thread = threading.Thread(target=test_connection, args=(test_counter,))
                threads.append(thread)
                thread.start()
                test_counter += 1

            # Wait for connections to complete
            for thread in threads:
                thread.join()

            # Brief pause between bursts
            time.sleep(0.5)

        connection_stats['end_time'] = time.time()
        total_test_time = connection_stats['end_time'] - connection_stats['start_time']

        # Calculate statistics
        if connection_stats['connection_times']:
            avg_time = sum(connection_stats['connection_times']) / len(connection_stats['connection_times'])
        else:
            avg_time = 0

        results = {
            'duration': round(total_test_time, 2),
            'total_attempts': connection_stats['total_attempts'],
            'successful_connections': connection_stats['successful_connections'],
            'failed_connections': connection_stats['failed_connections'],
            'blocked_connections': connection_stats['blocked_connections'],
            'timeouts': connection_stats['timeouts'],
            'attempts_per_second': round(connection_stats['total_attempts'] / total_test_time, 2),
            'avg_connection_time': round(avg_time, 3),
            'success_rate': round((connection_stats['successful_connections'] / connection_stats['total_attempts']) * 100, 1) if connection_stats['total_attempts'] > 0 else 0
        }

        print(f"\n📊 BRUTE FORCE TEST RESULTS:")
        print(f"   Test Duration: {results['duration']}s")
        print(f"   Total Attempts: {results['total_attempts']}")
        print(f"   Successful: {results['successful_connections']}")
        print(f"   Failed: {results['failed_connections']}")
        print(f"   Blocked: {results['blocked_connections']}")
        print(f"   Timeouts: {results['timeouts']}")
        print(f"   Attempts/Second: {results['attempts_per_second']}")
        print(f"   Success Rate: {results['success_rate']}%")
        print(f"   Avg Connection Time: {results['avg_connection_time']}s")

        # Analyze results
        if results['blocked_connections'] > 0:
            print(f"\n  ✅ GOOD: {results['blocked_connections']} connections were blocked")
            if results['blocked_connections'] > results['successful_connections']:
                print("  ✅ EXCELLENT: More connections blocked than successful")
                results['protection_level'] = 'HIGH'
            else:
                print("  ✅ GOOD: Some connection blocking detected")
                results['protection_level'] = 'MEDIUM'
        else:
            print(f"\n  ⚠️  NO CONNECTION BLOCKING DETECTED")
            print("  ❌ POOR: Server may be vulnerable to brute force attacks")
            results['protection_level'] = 'LOW'
            self.results['security_recommendations'].append(
                "IMPLEMENT RATE LIMITING: Install fail2ban to block brute force attempts"
            )

        if results['attempts_per_second'] > 20:
            self.results['security_recommendations'].append(
                f"HIGH CONNECTION RATE: {results['attempts_per_second']}/s - Consider additional rate limiting"
            )

        self.results['brute_force_test'] = results
        return results

    def generate_recommendations(self):
        """Generate comprehensive security recommendations"""
        print(f"\n🛡️  SSH SECURITY RECOMMENDATIONS")
        print("=" * 60)

        config_vulns = self.results.get('configuration_analysis', {}).get('vulnerabilities', [])
        test_results = self.results.get('brute_force_test', {})

        recommendations = []

        # Configuration hardening
        print("🔧 SSH CONFIGURATION HARDENING:")
        hardening_recs = [
            "• Change default SSH port from 22 to a non-standard port (e.g., 2222, 2022)",
            "• Disable root login: PermitRootLogin no",
            "• Disable password authentication: PasswordAuthentication no",
            "• Require public key authentication only: PubkeyAuthentication yes",
            "• Disable empty passwords: PermitEmptyPasswords no",
            "• Set maximum authentication attempts: MaxAuthTries 3-6",
            "• Set reasonable login timeout: LoginGraceTime 30-60",
            "• Enable client keep-alive: ClientAliveInterval 600",
            "• Disable X11 forwarding if not needed: X11Forwarding no",
            "• Limit SSH users to specific groups if possible"
        ]

        for rec in hardening_recs:
            print(f"   {rec}")

        # Brute force protection
        print(f"\n🚨 BRUTE FORCE PROTECTION:")
        protection_recs = [
            "• Install and configure fail2ban for SSH protection",
            "• Configure automatic IP blocking for failed attempts",
            "• Implement connection rate limiting at firewall level",
            "• Use IP whitelisting for SSH access",
            "• Consider VPN access for administrative SSH",
            "• Monitor authentication logs regularly",
            "• Set up alerts for suspicious login patterns",
            "• Use SSH keys with strong passphrases",
            "• Implement account lockout policies"
        ]

        for rec in protection_recs:
            print(f"   {rec}")

        # Specific recommendations based on findings
        if config_vulns:
            print(f"\n⚠️  CONFIGURATION VULNERABILITIES FOUND:")
            for i, vuln in enumerate(config_vulns, 1):
                print(f"   {i}. {vuln}")

        if test_results.get('protection_level') == 'LOW':
            print(f"\n🚨 HIGH PRIORITY RECOMMENDATIONS:")
            priority_recs = [
                "IMMEDIATE: Install fail2ban to prevent brute force attacks",
                "IMMEDIATE: Configure firewall to rate limit SSH connections",
                "IMMEDIATE: Consider using non-standard SSH port",
                "URGENT: Review SSH access logs for suspicious activity"
            ]
            for rec in priority_recs:
                print(f"   {rec}")

        self.results['security_recommendations'].extend(hardening_recs + protection_recs)

    def generate_report(self):
        """Generate comprehensive security report"""
        print(f"\n" + "="*80)
        print(f"🏁 SSH SECURITY TEST REPORT")
        print(f"="*80)
        print(f"🎯 Target: {self.results['target']}")
        print(f"📅 Test Date: {self.results['scan_time']}")

        # Executive summary
        print(f"\n📊 EXECUTIVE SUMMARY:")

        connectivity = self.results['connectivity_test']
        config_score = self.results.get('configuration_analysis', {}).get('hardening_score', 0)
        protection_level = self.results.get('brute_force_test', {}).get('protection_level', 'UNKNOWN')

        print(f"   • SSH Connectivity: {'✅ ACCESSIBLE' if connectivity else '❌ NOT ACCESSIBLE'}")
        print(f"   • Configuration Security: {config_score}/80 points")
        print(f"   • Brute Force Protection: {protection_level}")
        print(f"   • Total Recommendations: {len(self.results.get('security_recommendations', []))}")

        # Save report to file
        import json
        report_file = f"ssh_security_report_{self.target_host}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Security Score
        total_score = 100
        if not connectivity:
            total_score -= 50  # SSH not exposed
        else:
            total_score -= (80 - config_score)  # Config issues
            if protection_level == 'LOW':
                total_score -= 30  # Poor brute force protection
            elif protection_level == 'MEDIUM':
                total_score -= 15  # Some protection

        print(f"\n🎯 OVERALL SSH SECURITY SCORE: {max(0, total_score)}/100")

        if total_score >= 80:
            print("✅ EXCELLENT SSH SECURITY POSTURE")
        elif total_score >= 60:
            print("⚠️  GOOD SSH SECURITY WITH ROOM FOR IMPROVEMENT")
        else:
            print("❌ SSH SECURITY NEEDS IMMEDIATE ATTENTION")

        return self.results

def main():
    """Main execution function"""
    print("🔒 SIMPLE SSH SECURITY TESTING TOOL")
    print("="*60)

    target_host = "localhost"
    if len(sys.argv) > 1:
        target_host = sys.argv[1]

    print(f"🎯 Target SSH Server: {target_host}")
    print(f"⚠️  Only test systems you own or have explicit permission to test")

    tester = SimpleSSHSecurityTester(target_host)

    try:
        # Run comprehensive SSH security tests
        tester.test_connectivity()
        tester.analyze_local_ssh_config()

        if tester.results['connectivity_test']:
            tester.test_brute_force_resistance(duration=30)

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
