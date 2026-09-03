#!/usr/bin/env python3
"""
Simple Cache Monitoring Script
Shows async cache performance in terminal - no Grafana needed!
"""

import subprocess
import sys
import time
from datetime import datetime


def get_redis_stats():
    """Get Redis cache statistics"""
    try:
        result = subprocess.run(
            ["redis-cli", "INFO", "stats"], capture_output=True, text=True, timeout=5
        )

        stats = {}
        for line in result.stdout.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                stats[key] = value

        return stats
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None


def display_stats():
    """Display cache statistics in a nice format"""
    stats = get_redis_stats()

    if not stats:
        print("❌ Cannot connect to Redis")
        return

    # Extract relevant stats
    hits = int(stats.get("keyspace_hits", 0))
    misses = int(stats.get("keyspace_misses", 0))
    expired = int(stats.get("expired_keys", 0))
    commands = int(stats.get("total_commands_processed", 0))

    # Calculate hit rate
    total = hits + misses
    hit_rate = (hits / total * 100) if total > 0 else 0

    # Clear screen and show header
    print("\033[2J\033[H")  # Clear screen
    print(
        "╔══════════════════════════════════════════════════════════════════════════════╗"
    )
    print(
        "║                    📊 ASYNC CACHE MONITOR                                  ║"
    )
    print(
        f"║           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                  ║"
    )
    print(
        "╚══════════════════════════════════════════════════════════════════════════════╝"
    )
    print()

    # Display metrics
    print("📈 Cache Performance:")
    print(f"   Hit Rate: {hit_rate:.1f}% ", end="")

    if hit_rate >= 80:
        print("✅ EXCELLENT")
    elif hit_rate >= 70:
        print("✅ GOOD")
    elif hit_rate >= 50:
        print("⚠️  FAIR")
    else:
        print("❌ POOR")

    print()
    print("📊 Statistics:")
    print(f"   Cache Hits:        {hits:,}")
    print(f"   Cache Misses:      {misses:,}")
    print(f"   Expired Keys:      {expired:,}")
    print(f"   Total Commands:    {commands:,}")

    print()
    print("🎯 Performance Targets:")
    print(
        f"   Hit Rate >70%:     {'✅ ACHIEVED' if hit_rate >= 70 else '❌ NOT ACHIEVED'}"
    )

    # Show visual bar
    print()
    print("📊 Hit Rate Visualization:")
    bar_length = 40
    filled = int(bar_length * hit_rate / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"   [{bar}] {hit_rate:.1f}%")

    print()
    print("Press Ctrl+C to exit. Updates every 5 seconds.")
    print("─" * 80)


def main():
    """Main monitoring loop"""
    try:
        print("Starting Async Cache Monitor...")
        print("Press Ctrl+C to stop")
        time.sleep(2)

        while True:
            display_stats()
            time.sleep(5)  # Update every 5 seconds

    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped. Your async cache is working great!")
        print("\n💡 Quick check anytime:")
        print("   redis-cli INFO stats | grep keyspace")


if __name__ == "__main__":
    main()
