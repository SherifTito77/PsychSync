#!/usr/bin/env python3
"""
Cache Warmer Script
Populates your async cache with requests to build hit rate
"""

import subprocess
import time
import requests
from datetime import datetime

def make_request(url):
    """Make a request to the API"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code
    except Exception as e:
        return None

def warm_cache():
    """Warm up the cache by making requests"""
    base_url = "http://localhost:8000"

    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║                    🔥 CACHE WARMER                                            ║")
    print("║           Populating cache to build hit rate...                            ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝")
    print()

    # Check if server is running
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=2)
        print(f"✅ Server is running (HTTP {response.status_code})")
    except:
        print("❌ Server not running! Start it first:")
        print("   uvicorn app.main:app --reload")
        return

    print()
    print("🔄 Warming up cache with 50 requests...")
    print()

    endpoints = [
        "/api/v1/health",
        "/api/v1/health",
        "/api/v1/health",
    ]

    for i in range(50):
        for endpoint in endpoints:
            status = make_request(f"{base_url}{endpoint}")
            if status:
                print(f"  Request {i+1}/50: HTTP {status}", end="\r")

        time.sleep(0.1)  # Small delay between batches

    print()
    print()
    print("✅ Cache warming complete!")
    print()
    print("📊 Check your hit rate now:")
    print("   redis-cli INFO stats | grep keyspace")
    print()
    print("Or run the monitor:")
    print("   python3 scripts/cache-monitor.py")

if __name__ == "__main__":
    warm_cache()
