#!/usr/bin/env python3
"""
PsychSync Metrics Logger
Records metrics to CSV for unlimited local storage and analysis
Usage: python metrics_logger.py
"""

import csv
import time
from datetime import datetime
from pathlib import Path

import requests

# Configuration
METRICS_URL = "http://localhost:8000/metrics"
OUTPUT_DIR = Path("metrics_history")
OUTPUT_FILE = OUTPUT_DIR / f"metrics_{datetime.now().strftime('%Y%m%d')}.csv"
INTERVAL_SECONDS = 60  # Record metrics every minute

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)


def get_metric_value(metrics_text, metric_name):
    """Extract value from Prometheus metrics text"""
    for line in metrics_text.split("\n"):
        if line.startswith(metric_name + "{") or line.startswith(metric_name + " "):
            # Extract the value (last number on the line)
            parts = line.split()
            if parts:
                try:
                    return float(parts[-1])
                except (ValueError, IndexError):
                    continue
    return 0.0


def record_metrics():
    """Record current metrics to CSV"""
    try:
        # Fetch metrics
        response = requests.get(METRICS_URL, timeout=5)
        response.raise_for_status()
        metrics_text = response.text

        # Extract key metrics
        timestamp = datetime.now().isoformat()
        data = {
            "timestamp": timestamp,
            "http_requests_total": get_metric_value(
                metrics_text, "psychsync_http_requests_total"
            ),
            "http_requests_active": get_metric_value(
                metrics_text, "psychsync_http_requests_active"
            ),
            "auth_failures": get_metric_value(
                metrics_text, "psychsync_auth_failures_total"
            ),
            "auth_success": get_metric_value(
                metrics_text, "psychsync_auth_success_total"
            ),
            "db_connections_active": get_metric_value(
                metrics_text, "psychsync_db_connections_active"
            ),
            "db_connections_idle": get_metric_value(
                metrics_text, "psychsync_db_connections_idle"
            ),
            "cache_hits": get_metric_value(metrics_text, "psychsync_cache_hits_total"),
            "cache_misses": get_metric_value(
                metrics_text, "psychsync_cache_misses_total"
            ),
            "user_registrations": get_metric_value(
                metrics_text, "psychsync_user_registrations_total"
            ),
            "assessments_completed": get_metric_value(
                metrics_text, "psychsync_assessments_completed_total"
            ),
        }

        # Write to CSV
        file_exists = OUTPUT_FILE.exists()
        with open(OUTPUT_FILE, "a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)

        print(f"✅ [{timestamp}] Metrics recorded to {OUTPUT_FILE}")
        print(
            f"   Requests: {data['http_requests_total']}, "
            f"Auth Failures: {data['auth_failures']}, "
            f"DB Active: {data['db_connections_active']}"
        )

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching metrics: {e}")
    except Exception as e:
        print(f"❌ Error recording metrics: {e}")


def main():
    """Main logging loop"""
    print("🔍 PsychSync Metrics Logger")
    print("=" * 50)
    print(f"Recording metrics every {INTERVAL_SECONDS} seconds...")
    print(f"Output directory: {OUTPUT_DIR.absolute()}")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()

    try:
        while True:
            record_metrics()
            time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n\n✅ Metrics logging stopped")
        print(f"📊 Data saved to: {OUTPUT_DIR.absolute()}")


if __name__ == "__main__":
    main()
