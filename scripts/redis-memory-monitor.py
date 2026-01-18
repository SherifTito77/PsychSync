#!/usr/bin/env python3
"""
Redis Memory Monitoring Script

This script monitors Redis memory usage and cache growth over time
to verify that cache entries are properly expiring and not accumulating
indefinitely (which would indicate missing TTL configuration).

Usage:
    python scripts/redis-memory-monitor.py --duration 120 --interval 30

Arguments:
    --duration: Monitoring duration in minutes (default: 120)
    --interval: Check interval in seconds (default: 30)
    --host: Redis host (default: localhost)
    --port: Redis port (default: 6379)
    --db: Redis database number (default: 0)
    --output: Output file for results (default: redis-monitor-results.json)
"""

import argparse
import json
import time
import sys
from datetime import datetime
from pathlib import Path

try:
    import redis
except ImportError:
    print("❌ redis-py not installed. Install with: pip install redis")
    sys.exit(1)


class RedisMemoryMonitor:
    """Monitor Redis memory usage and cache statistics"""

    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.redis_client.ping()
            print(f"✅ Connected to Redis at {host}:{port}")
        except redis.ConnectionError as e:
            print(f"❌ Failed to connect to Redis: {e}")
            sys.exit(1)

        self.metrics = []
        self.start_time = None

    def get_memory_info(self):
        """Get Redis memory information"""
        info = self.redis_client.info('memory')
        return {
            'used_memory': info['used_memory'],
            'used_memory_human': info['used_memory_human'],
            'used_memory_peak': info['used_memory_peak'],
            'used_memory_peak_human': info['used_memory_peak_human'],
            'used_memory_percentage': info.get('used_memory_percentage', 0),
            'maxmemory': info.get('maxmemory', 0),
            'maxmemory_human': info.get('maxmemory-human', '0B'),
            'maxmemory_policy': info.get('maxmemory_policy', 'noeviction'),
        }

    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            # Get total number of keys
            db_size = self.redis_client.dbsize()

            # Get keys with expiration (cached data)
            # Note: This is an approximation - scanning all keys to check TTL is expensive
            cursor = 0
            sample_keys = []
            sampled_with_ttl = 0
            sample_size = min(1000, db_size)  # Sample up to 1000 keys

            while len(sample_keys) < sample_size:
                cursor, keys = self.redis_client.scan(cursor=cursor, count=100)
                sample_keys.extend(keys)
                if cursor == 0:
                    break

            # Check TTL for sampled keys
            for key in sample_keys[:sample_size]:
                ttl = self.redis_client.ttl(key)
                if ttl > 0:
                    sampled_with_ttl += 1

            ttl_percentage = (sampled_with_ttl / len(sample_keys) * 100) if sample_keys else 0

            return {
                'total_keys': db_size,
                'sampled_keys_with_ttl': sampled_with_ttl,
                'sample_size': len(sample_keys),
                'ttl_percentage': round(ttl_percentage, 2),
            }
        except Exception as e:
            print(f"⚠️  Error getting cache stats: {e}")
            return {
                'total_keys': 0,
                'sampled_keys_with_ttl': 0,
                'sample_size': 0,
                'ttl_percentage': 0,
            }

    def get_key_patterns(self):
        """Get statistics by key patterns"""
        patterns = {
            'cache:*': 0,
            'user:*': 0,
            'session:*': 0,
            'lock:*': 0,
            'other': 0,
        }

        try:
            for pattern in patterns.keys():
                if pattern == 'other':
                    continue
                count = len(list(self.redis_client.scan_iter(match=pattern, count=100)))
                patterns[pattern] = count

            # Count other keys
            total_keys = self.redis_client.dbsize()
            patterned_keys = sum(v for k, v in patterns.items() if k != 'other')
            patterns['other'] = max(0, total_keys - patterned_keys)

        except Exception as e:
            print(f"⚠️  Error getting key patterns: {e}")

        return patterns

    def collect_metrics(self):
        """Collect all metrics"""
        timestamp = datetime.now().isoformat()
        elapsed_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        metrics = {
            'timestamp': timestamp,
            'elapsed_time_seconds': round(elapsed_time, 2),
            'memory': self.get_memory_info(),
            'cache': self.get_cache_stats(),
            'key_patterns': self.get_key_patterns(),
        }

        self.metrics.append(metrics)
        return metrics

    def print_metrics(self, metrics, iteration):
        """Pretty print metrics"""
        elapsed = metrics['elapsed_time_seconds']
        memory = metrics['memory']
        cache = metrics['cache']
        patterns = metrics['key_patterns']

        print(f"\n{'='*70}")
        print(f"📊 Redis Metrics - Check #{iteration}")
        print(f"{'='*70}")
        print(f"⏱️  Elapsed Time: {elapsed/60:.1f} minutes")
        print(f"\n💾 Memory Usage:")
        print(f"   Used: {memory['used_memory_human']}")
        print(f"   Peak: {memory['used_memory_peak_human']}")
        print(f"   Max: {memory['maxmemory_human']}")
        print(f"   Policy: {memory['maxmemory_policy']}")

        if memory['used_memory_percentage'] > 0:
            pct = memory['used_memory_percentage']
            status = '🚨' if pct > 80 else '⚠️' if pct > 60 else '✅'
            print(f"   Usage: {pct:.1f}% {status}")

        print(f"\n📦 Cache Statistics:")
        print(f"   Total Keys: {cache['total_keys']}")
        print(f"   Keys with TTL: {cache['sampled_keys_with_ttl']}/{cache['sample_size']} sampled")
        print(f"   TTL Coverage: {cache['ttl_percentage']}%")

        if cache['ttl_percentage'] < 80:
            print(f"   ⚠️  Warning: Low TTL coverage! Keys may not be expiring.")

        print(f"\n🔑 Key Patterns:")
        for pattern, count in patterns.items():
            if count > 0:
                print(f"   {pattern}: {count}")

    def monitor(self, duration_minutes, interval_seconds, output_file):
        """Run monitoring loop"""
        duration_seconds = duration_minutes * 60
        self.start_time = datetime.now()
        end_time = time.time() + duration_seconds

        print(f"\n🔍 Starting Redis Memory Monitoring")
        print(f"   Duration: {duration_minutes} minutes")
        print(f"   Interval: {interval_seconds} seconds")
        print(f"   Output: {output_file}")
        print(f"   Expected checks: {int(duration_seconds / interval_seconds)}\n")

        iteration = 0
        next_check = time.time()

        # Initial metrics
        metrics = self.collect_metrics()
        self.print_metrics(metrics, iteration)
        iteration += 1
        next_check = time.time() + interval_seconds

        # Monitoring loop
        while time.time() < end_time:
            time.sleep(max(0, next_check - time.time()))

            if time.time() >= next_check:
                metrics = self.collect_metrics()
                self.print_metrics(metrics, iteration)

                # Save results incrementally
                self.save_results(output_file)

                iteration += 1
                next_check = time.time() + interval_seconds

        self.generate_report(output_file)

    def save_results(self, output_file):
        """Save metrics to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def generate_report(self, output_file):
        """Generate final report"""
        print(f"\n\n{'='*70}")
        print(f"📈 FINAL REPORT")
        print(f"{'='*70}")

        if len(self.metrics) < 2:
            print("⚠️  Insufficient data for analysis")
            return

        initial = self.metrics[0]
        final = self.metrics[-1]

        # Memory growth analysis
        initial_memory_mb = initial['memory']['used_memory'] / 1024 / 1024
        final_memory_mb = final['memory']['used_memory'] / 1024 / 1024
        memory_growth_mb = final_memory_mb - initial_memory_mb
        memory_growth_pct = (memory_growth_mb / initial_memory_mb * 100) if initial_memory_mb > 0 else 0

        print(f"\n💾 Memory Growth:")
        print(f"   Initial: {initial_memory_mb:.2f} MB")
        print(f"   Final: {final_memory_mb:.2f} MB")
        print(f"   Growth: {memory_growth_mb:+.2f} MB ({memory_growth_pct:+.1f}%)")

        if memory_growth_mb > 100:
            print(f"   🚨 CRITICAL: Memory grew by {memory_growth_mb:.0f} MB!")
            print(f"   → Cache keys may not be expiring properly")
        elif memory_growth_mb > 50:
            print(f"   ⚠️  WARNING: Significant memory growth detected")
            print(f"   → Review cache TTL settings")
        elif memory_growth_mb > 20:
            print(f"   ⚠️  CAUTION: Moderate memory growth")
            print(f"   → Monitor in production")
        else:
            print(f"   ✅ GOOD: Memory usage is stable")

        # Cache keys growth
        initial_keys = initial['cache']['total_keys']
        final_keys = final['cache']['total_keys']
        keys_growth = final_keys - initial_keys
        keys_growth_rate = keys_growth / (duration_minutes := (final['elapsed_time_seconds'] / 60))

        print(f"\n📦 Cache Keys Growth:")
        print(f"   Initial Keys: {initial_keys}")
        print(f"   Final Keys: {final_keys}")
        print(f"   Growth: {keys_growth:+d} keys")
        print(f"   Rate: {keys_growth_rate:+.1f} keys/minute")

        if keys_growth > 10000:
            print(f"   🚨 CRITICAL: {keys_growth} keys accumulated!")
            print(f"   → Missing TTL on cache.set() calls")
        elif keys_growth > 5000:
            print(f"   ⚠️  WARNING: High key accumulation rate")
            print(f"   → Review cache expiration policies")
        elif keys_growth > 1000:
            print(f"   ⚠️  CAUTION: Keys are accumulating")
            print(f"   → Check cache TTL configuration")

        # TTL coverage
        ttl_coverage = final['cache']['ttl_percentage']
        print(f"\n⏰ TTL Coverage:")
        print(f"   Keys with Expiration: {ttl_coverage}%")

        if ttl_coverage < 50:
            print(f"   🚨 CRITICAL: Most keys have no expiration!")
            print(f"   → This WILL cause Redis memory exhaustion")
        elif ttl_coverage < 80:
            print(f"   ⚠️  WARNING: Low TTL coverage")
            print(f"   → Some keys may not expire properly")
        else:
            print(f"   ✅ GOOD: Most keys have TTL set")

        # Key pattern analysis
        print(f"\n🔑 Key Pattern Distribution:")
        patterns = final['key_patterns']
        for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                print(f"   {pattern}: {count} keys")

        # Overall assessment
        print(f"\n{'='*70}")
        print(f"📊 OVERALL ASSESSMENT:")

        issues = []
        if memory_growth_mb > 100:
            issues.append("Critical memory growth")
        if keys_growth > 5000:
            issues.append("Excessive key accumulation")
        if ttl_coverage < 50:
            issues.append("Insufficient TTL coverage")

        if issues:
            print(f"   ❌ FAIL:")
            for issue in issues:
                print(f"      • {issue}")
            print(f"\n   📝 Action Required:")
            print(f"      1. Review cache.set() calls for missing TTL parameter")
            print(f"      2. Check EnhancedCacheService DEFAULT_TTL configuration")
            print(f"      3. Verify cache entries use expire parameter")
        elif memory_growth_mb > 50 or keys_growth > 1000 or ttl_coverage < 80:
            print(f"   ⚠️  WARN: Review cache configuration")
            print(f"      • Memory growth: {memory_growth_mb:+.0f} MB")
            print(f"      • Keys added: {keys_growth:+d}")
            print(f"      • TTL coverage: {ttl_coverage}%")
        else:
            print(f"   ✅ PASS: Cache management is healthy")
            print(f"      • Memory stable")
            print(f"      • Keys expiring properly")
            print(f"      • TTL coverage good")

        print(f"\n📁 Detailed results saved to: {output_file}")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor Redis memory usage and cache growth',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor for 2 hours, checking every 30 seconds
  python scripts/redis-memory-monitor.py --duration 120 --interval 30

  # Quick 10-minute check
  python scripts/redis-memory-monitor.py --duration 10 --interval 10

  # Monitor specific Redis instance
  python scripts/redis-memory-monitor.py --host redis.example.com --port 6380
        """
    )

    parser.add_argument(
        '--duration',
        type=int,
        default=120,
        help='Monitoring duration in minutes (default: 120)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Check interval in seconds (default: 30)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='Redis host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6379,
        help='Redis port (default: 6379)'
    )
    parser.add_argument(
        '--db',
        type=int,
        default=0,
        help='Redis database number (default: 0)'
    )
    parser.add_argument(
        '--password',
        type=str,
        default=None,
        help='Redis password (default: None)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='redis-monitor-results.json',
        help='Output file for results (default: redis-monitor-results.json)'
    )

    args = parser.parse_args()

    monitor = RedisMemoryMonitor(
        host=args.host,
        port=args.port,
        db=args.db,
        password=args.password
    )

    try:
        monitor.monitor(
            duration_minutes=args.duration,
            interval_seconds=args.interval,
            output_file=args.output
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Monitoring interrupted by user")
        if monitor.metrics:
            monitor.save_results(args.output)
            monitor.generate_report(args.output)
        sys.exit(0)


if __name__ == '__main__':
    main()
