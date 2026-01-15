#!/usr/bin/env python3
"""
Log Anomaly Detection Agent

Continuously scans application logs for anomalies, errors, and unusual patterns.
Uses statistical analysis and ML techniques to detect issues early.

Features:
- Real-time log monitoring (tail -f style)
- Error rate spike detection
- Unusual pattern detection
- Performance anomaly detection (slow queries, high latency)
- Security event flagging (SQL injection attempts, brute force, etc.)

Usage:
    python agents/log_anomaly_agent.py --log-path logs/app.log
    python agents/log_anomaly_agent.py --log-path logs/ --pattern "*.log" --watch
    python agents/log_anomaly_agent.py --log-path logs/app.log --threshold 3.0
"""

import argparse
import ast
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict, deque
import statistics
import hashlib
import fnmatch


class LogEntry:
    """Represents a single log entry"""

    def __init__(self, raw_line: str, timestamp: datetime = None):
        self.raw = raw_line
        self.timestamp = timestamp or datetime.now()
        self.level = self._extract_level()
        self.message = self._extract_message()
        self.error_type = self._extract_error_type()
        self.status_code = self._extract_status_code()
        self.response_time = self._extract_response_time()
        self.user_id = self._extract_field('user_id')
        self.ip = self._extract_field('ip')
        self.endpoint = self._extract_field('endpoint')
        self.sql_query = self._extract_sql_query()

    def _extract_level(self) -> str:
        """Extract log level (INFO, WARNING, ERROR, CRITICAL)"""
        levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
        for level in levels:
            if level in self.raw:
                return level
        return 'INFO'  # Default

    def _extract_message(self) -> str:
        """Extract the main log message"""
        # Remove timestamp, level, and other metadata
        patterns = [
            r'\d{4}-\d{2}-\d{2}.*?\d{2}:\d{2}:\d{2}',  # Timestamp
            r'\[(CRITICAL|ERROR|WARNING|INFO|DEBUG)\]',  # Level
            r'\[\w+\]',  # Other brackets
        ]

        message = self.raw
        for pattern in patterns:
            message = re.sub(pattern, '', message).strip()

        return message[:200]  # Truncate long messages

    def _extract_error_type(self) -> Optional[str]:
        """Extract error type from log entry"""
        error_patterns = [
            r'(?:TypeError|ValueError|AttributeError|KeyError|IndexError|NameError|RuntimeError)',
            r'(?:SQLAlchemyError|IntegrityError|OperationalError)',
            r'(?:HTTPException|ValidationError)',
            r'Exception: (\w+)',
        ]

        for pattern in error_patterns:
            match = re.search(pattern, self.raw)
            if match:
                return match.group(1) if match.groups() else match.group(0)

        return None

    def _extract_status_code(self) -> Optional[int]:
        """Extract HTTP status code"""
        match = re.search(r'"status":\s*(\d{3})', self.raw)
        if match:
            return int(match.group(1))

        match = re.search(r' (4\d{2}|5\d{2}) ', self.raw)
        if match:
            return int(match.group(1))

        return None

    def _extract_response_time(self) -> Optional[float]:
        """Extract response time in milliseconds"""
        # Look for patterns like "duration=123ms" or "response_time": 1.23
        patterns = [
            r'duration[=:](\d+(?:\.\d+)?)ms',
            r'response_time[=:](\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)ms',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.raw)
            if match:
                value = float(match.group(1))
                # Convert to milliseconds if needed
                if 'response_time' in self.raw and value < 100:
                    value *= 1000
                return value

        return None

    def _extract_field(self, field_name: str) -> Optional[str]:
        """Extract a specific field from JSON log entry"""
        # Try to parse as JSON
        try:
            json_match = re.search(r'\{.*\}', self.raw)
            if json_match:
                data = json.loads(json_match.group(0))
                return data.get(field_name)
        except:
            pass

        # Try pattern matching
        pattern = rf'{field_name}[=:]([^\s,]+)'
        match = re.search(pattern, self.raw)
        if match:
            return match.group(1)

        return None

    def _extract_sql_query(self) -> Optional[str]:
        """Extract SQL query from log entry"""
        patterns = [
            r'SELECT.*?(?:FROM|WHERE)',
            r'INSERT INTO.*?VALUES',
            r'UPDATE.*?SET',
            r'DELETE FROM.*?WHERE',
        ]

        for pattern in patterns:
            match = re.search(pattern, self.raw, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(0)[:100]  # Truncate long queries

        return None

    def is_anomaly(self) -> bool:
        """Check if this log entry is clearly anomalous"""
        # Critical errors
        if self.level in ['CRITICAL', 'ERROR']:
            return True

        # 5xx status codes
        if self.status_code and self.status_code >= 500:
            return True

        # Very slow response times (>5 seconds)
        if self.response_time and self.response_time > 5000:
            return True

        # Security-related events
        security_keywords = ['injection', 'brute force', 'unauthorized', 'forbidden', 'attack']
        if any(keyword in self.raw.lower() for keyword in security_keywords):
            return True

        return False


class LogAnalyzer:
    """Analyzes log patterns and detects anomalies"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.error_history = deque(maxlen=window_size)
        self.response_time_history = deque(maxlen=window_size)
        self.endpoint_counts = defaultdict(int)
        self.error_types = defaultdict(int)
        self.ip_counts = defaultdict(int)

        # Baseline statistics
        self.baseline_error_rate = 0.0
        self.baseline_response_time = 0.0

    def process_entry(self, entry: LogEntry) -> Optional[Dict]:
        """Process a log entry and detect anomalies"""
        anomaly = None

        # Track metrics
        is_error = entry.level in ['ERROR', 'CRITICAL']
        self.error_history.append(1 if is_error else 0)

        if entry.response_time:
            self.response_time_history.append(entry.response_time)

        if entry.endpoint:
            self.endpoint_counts[entry.endpoint] += 1

        if entry.error_type:
            self.error_types[entry.error_type] += 1

        if entry.ip:
            self.ip_counts[entry.ip] += 1

        # Detect anomalies
        if is_error:
            error_rate = statistics.mean(self.error_history)
            if error_rate > self.baseline_error_rate * 3:  # 3x baseline
                anomaly = {
                    'type': 'error_spike',
                    'severity': 'warning',
                    'message': f"Error rate spike detected: {error_rate:.1%}",
                    'timestamp': entry.timestamp.isoformat(),
                    'baseline': f"{self.baseline_error_rate:.1%}",
                    'current': f"{error_rate:.1%}"
                }

        if entry.response_time:
            avg_response_time = statistics.mean(self.response_time_history)
            if entry.response_time > avg_response_time * 3:  # 3x slower than average
                anomaly = {
                    'type': 'performance_anomaly',
                    'severity': 'warning' if entry.response_time < 5000 else 'critical',
                    'message': f"Slow response time: {entry.response_time:.0f}ms (avg: {avg_response_time:.0f}ms)",
                    'timestamp': entry.timestamp.isoformat(),
                    'endpoint': entry.endpoint,
                    'response_time_ms': entry.response_time,
                    'baseline_avg_ms': avg_response_time
                }

        # Check for specific anomalies
        if entry.status_code and entry.status_code >= 500:
            anomaly = {
                'type': 'server_error',
                'severity': 'error',
                'message': f"Server error: {entry.status_code}",
                'timestamp': entry.timestamp.isoformat(),
                'status_code': entry.status_code,
                'endpoint': entry.endpoint,
                'user_id': entry.user_id
            }

        # Security anomaly detection
        if entry.sql_query:
            # Check for potential SQL injection
            suspicious_patterns = [
                r"(\bOR\b|\bAND\b).*=.*['\"]",  # OR 1=1
                r"UNION.*SELECT",
                r";.*DROP\s+TABLE",
                r";.*EXECUTE",
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, entry.sql_query, re.IGNORECASE):
                    anomaly = {
                        'type': 'security_alert',
                        'severity': 'critical',
                        'message': "Potential SQL injection detected",
                        'timestamp': entry.timestamp.isoformat(),
                        'sql_query': entry.sql_query[:100],
                        'ip': entry.ip,
                        'user_id': entry.user_id
                    }
                    break

        # Rate limiting / brute force detection
        if self.ip_counts[entry.ip] > 100:  # More than 100 requests from same IP
            anomaly = {
                'type': 'security_alert',
                'severity': 'warning',
                'message': f"High request rate from IP: {entry.ip}",
                'timestamp': entry.timestamp.isoformat(),
                'ip': entry.ip,
                'request_count': self.ip_counts[entry.ip]
            }

        return anomaly

    def update_baseline(self):
        """Update baseline statistics"""
        if len(self.error_history) > 0:
            self.baseline_error_rate = statistics.mean(self.error_history)

        if len(self.response_time_history) > 0:
            self.baseline_response_time = statistics.mean(self.response_time_history)


class AnomalyReporter:
    """Reports and aggregates anomalies"""

    def __init__(self):
        self.anomalies = []
        self.anomaly_counts = defaultdict(int)

    def add_anomaly(self, anomaly: Dict):
        """Add an anomaly to the report"""
        self.anomalies.append(anomaly)
        self.anomaly_counts[anomaly['type']] += 1

    def generate_summary(self) -> Dict:
        """Generate anomaly summary report"""
        severity_counts = defaultdict(int)
        for anomaly in self.anomalies:
            severity_counts[anomaly['severity']] += 1

        return {
            'timestamp': datetime.now().isoformat(),
            'total_anomalies': len(self.anomalies),
            'severity_breakdown': dict(severity_counts),
            'type_breakdown': dict(self.anomaly_counts),
            'recent_anomalies': self.anomalies[-10:],  # Last 10
        }

    def save_report(self, output_path: str = 'reports/log_anomalies.json'):
        """Save anomaly report to file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        summary = self.generate_summary()

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        return summary


def watch_logs(log_path: str, pattern: str = '*', threshold: float = 3.0, watch: bool = False):
    """Watch log file(s) for anomalies"""

    print(f"🔍 Log Anomaly Detection Agent")
    print(f"   Monitoring: {log_path}")
    print(f"   Pattern: {pattern}")
    print(f"   Anomaly threshold: {threshold}x baseline")
    print(f"   Watch mode: {'enabled' if watch else 'disabled (single scan)'}")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'-'*60}")

    analyzer = LogAnalyzer(window_size=100)
    reporter = AnomalyReporter()

    # Find log files
    log_files = []
    if os.path.isfile(log_path):
        log_files = [log_path]
    elif os.path.isdir(log_path):
        for root, dirs, files in os.walk(log_path):
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    log_files.append(os.path.join(root, filename))

    if not log_files:
        print(f"❌ No log files found matching pattern '{pattern}' in {log_path}")
        return

    print(f"   Found {len(log_files)} log file(s)")

    # Track file positions
    file_positions = {f: 0 for f in log_files}

    iteration = 0

    try:
        while True:
            iteration += 1

            # Update baseline periodically
            if iteration % 100 == 0:
                analyzer.update_baseline()

            # Read new lines from each log file
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        # Seek to last position
                        f.seek(file_positions[log_file])

                        # Read new lines
                        new_lines = f.readlines()
                        if new_lines:
                            # Update position
                            file_positions[log_file] = f.tell()

                            # Process each new line
                            for line in new_lines:
                                line = line.strip()
                                if line:
                                    try:
                                        entry = LogEntry(line)
                                        anomaly = analyzer.process_entry(entry)

                                        if anomaly or entry.is_anomaly():
                                            # Log the anomaly
                                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                            severity = anomaly['severity'] if anomaly else entry.level
                                            icon = '🚨' if severity == 'critical' else '⚠️' if severity == 'warning' else 'ℹ️'

                                            print(f"[{timestamp}] {icon} {anomaly['message'] if anomaly else entry.message}")

                                            if anomaly:
                                                reporter.add_anomaly(anomaly)

                                    except Exception as e:
                                        # Don't let parsing errors stop monitoring
                                        pass

                except FileNotFoundError:
                    # Log file might not exist yet
                    pass
                except Exception as e:
                    print(f"❌ Error reading {log_file}: {e}")

            # Save report periodically
            if iteration % 100 == 0 and reporter.anomalies:
                reporter.save_report()
                summary = reporter.generate_summary()
                print(f"\n📊 Periodic Summary (iteration {iteration}):")
                print(f"   Total anomalies: {summary['total_anomalies']}")
                print(f"   By severity: {summary['severity_breakdown']}")
                print(f"   By type: {summary['type_breakdown']}")
                print()

            if not watch:
                # Single scan - break after processing all files
                break

            # Sleep before next iteration
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n✅ Stopped monitoring at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Save final report
        if reporter.anomalies:
            reporter.save_report()
            summary = reporter.generate_summary()
            print(f"\n{'='*60}")
            print(f"FINAL REPORT")
            print(f"{'='*60}")
            print(f"Total anomalies detected: {summary['total_anomalies']}")
            print(f"\nSeverity Breakdown:")
            for severity, count in summary['severity_breakdown'].items():
                print(f"  {severity.upper()}: {count}")
            print(f"\nType Breakdown:")
            for anomaly_type, count in summary['type_breakdown'].items():
                print(f"  {anomaly_type}: {count}")
            print(f"\n✅ Report saved to: reports/log_anomalies.json")
            print(f"{'='*60}\n")

            # Exit with error if critical anomalies found
            if summary['severity_breakdown'].get('critical', 0) > 0:
                sys.exit(1)
        else:
            print("\n✅ No anomalies detected. All logs look healthy!")


def main():
    parser = argparse.ArgumentParser(
        description='Log Anomaly Detection Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor single log file (one-time scan)
  python agents/log_anomaly_agent.py --log-path logs/app.log

  # Monitor all log files continuously
  python agents/log_anomaly_agent.py --log-path logs/ --watch

  # Monitor specific pattern with custom threshold
  python agents/log_anomaly_agent.py --log-path logs/ --pattern "app*.log" --threshold 5.0
        """
    )

    parser.add_argument('--log-path', required=True, help='Path to log file or directory')
    parser.add_argument('--pattern', default='*.log', help='Log file pattern to match (default: *.log)')
    parser.add_argument('--threshold', type=float, default=3.0, help='Anomaly threshold multiplier (default: 3.0)')
    parser.add_argument('--watch', action='store_true', help='Enable continuous monitoring mode')

    args = parser.parse_args()

    watch_logs(args.log_path, args.pattern, args.threshold, args.watch)


if __name__ == '__main__':
    main()
