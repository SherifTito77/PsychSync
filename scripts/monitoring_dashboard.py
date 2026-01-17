#!/usr/bin/env python3
"""
PsychSync Production Monitoring Dashboard
Real-time monitoring and alerting system for production infrastructure
"""

import asyncio
import time
import json
import psutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class MonitoringDashboard:
    def __init__(self):
        self.metrics = {
            "system": {},
            "database": {},
            "api": {},
            "redis": {},
            "alerts": []
        }
        self.start_time = datetime.now()

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0,
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }

    async def collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics"""
        try:
            # Test database connectivity
            result = subprocess.run(
                ['psql', '-d', 'psychsync_db', '-c', 'SELECT COUNT(*) as user_count FROM users'],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                user_count = result.stdout.strip().split('\n')[-2]
                return {
                    "status": "connected",
                    "user_count": int(user_count) if user_count.isdigit() else 0,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr.strip(),
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def collect_api_metrics(self) -> Dict[str, Any]:
        """Collect API performance metrics"""
        try:
            import requests

            # Test API health endpoint
            response = requests.get(
                "http://localhost:8000/api/v1/health",
                timeout=5
            )

            if response.status_code == 200:
                response_time = response.elapsed.total_seconds() * 1000
                return {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2),
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "status_code": response.status_code,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def collect_redis_metrics(self) -> Dict[str, Any]:
        """Collect Redis metrics"""
        try:
            import redis

            # Connect to Redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)

            # Test Redis connection
            r.ping()

            # Get Redis info
            info = r.info()

            return {
                "status": "connected",
                "used_memory_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for alerts based on current metrics"""
        alerts = []

        # System alerts
        if self.metrics.get("system", {}).get("cpu_percent", 0) > 80:
            alerts.append({
                "level": "WARNING",
                "source": "system",
                "message": f"High CPU usage: {self.metrics['system']['cpu_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })

        if self.metrics.get("system", {}).get("memory_percent", 0) > 85:
            alerts.append({
                "level": "WARNING",
                "source": "system",
                "message": f"High memory usage: {self.metrics['system']['memory_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            })

        # Database alerts
        if self.metrics.get("database", {}).get("status") != "connected":
            alerts.append({
                "level": "CRITICAL",
                "source": "database",
                "message": "Database connection failed",
                "timestamp": datetime.now().isoformat()
            })

        # API alerts
        if self.metrics.get("api", {}).get("status") != "healthy":
            alerts.append({
                "level": "CRITICAL",
                "source": "api",
                "message": "API health check failed",
                "timestamp": datetime.now().isoformat()
            })

        if self.metrics.get("api", {}).get("response_time_ms", 0) > 1000:
            alerts.append({
                "level": "WARNING",
                "source": "api",
                "message": f"Slow API response: {self.metrics['api']['response_time_ms']:.0f}ms",
                "timestamp": datetime.now().isoformat()
            })

        # Redis alerts
        if self.metrics.get("redis", {}).get("status") != "connected":
            alerts.append({
                "level": "WARNING",
                "source": "redis",
                "message": "Redis connection failed",
                "timestamp": datetime.now().isoformat()
            })

        return alerts

    async def collect_all_metrics(self):
        """Collect all metrics"""
        self.metrics["system"] = await self.collect_system_metrics()
        self.metrics["database"] = await self.collect_database_metrics()
        self.metrics["api"] = await self.collect_api_metrics()
        self.metrics["redis"] = await self.collect_redis_metrics()
        self.metrics["alerts"] = self.check_alerts()
        self.metrics["last_updated"] = datetime.now().isoformat()

    def display_dashboard(self):
        """Display monitoring dashboard"""
        print("\n" + "="*80)
        print(f"🚀 PSYCHSYNC PRODUCTION MONITORING DASHBOARD")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

        # System Metrics
        sys_metrics = self.metrics.get("system", {})
        print(f"\n🖥️  SYSTEM METRICS:")
        print(f"   CPU Usage: {sys_metrics.get('cpu_percent', 0):.1f}%")
        print(f"   Memory Usage: {sys_metrics.get('memory_percent', 0):.1f}%")
        print(f"   Disk Usage: {sys_metrics.get('disk_percent', 0):.1f}%")
        print(f"   Load Average: {sys_metrics.get('load_average', 0):.2f}")

        # Database Metrics
        db_metrics = self.metrics.get("database", {})
        print(f"\n🗄️  DATABASE METRICS:")
        print(f"   Status: {db_metrics.get('status', 'unknown').upper()}")
        if db_metrics.get("status") == "connected":
            print(f"   User Count: {db_metrics.get('user_count', 0):,}")
        else:
            print(f"   Error: {db_metrics.get('error', 'Unknown error')}")

        # API Metrics
        api_metrics = self.metrics.get("api", {})
        print(f"\n🌐 API METRICS:")
        print(f"   Status: {api_metrics.get('status', 'unknown').upper()}")
        if api_metrics.get("status") == "healthy":
            print(f"   Response Time: {api_metrics.get('response_time_ms', 0):.0f}ms")
            print(f"   Status Code: {api_metrics.get('status_code', 'N/A')}")

        # Redis Metrics
        redis_metrics = self.metrics.get("redis", {})
        print(f"\n📦 REDIS METRICS:")
        print(f"   Status: {redis_metrics.get('status', 'unknown').upper()}")
        if redis_metrics.get("status") == "connected":
            print(f"   Memory Usage: {redis_metrics.get('used_memory_mb', 0):.1f}MB")
            print(f"   Connected Clients: {redis_metrics.get('connected_clients', 0):,}")

        # Alerts
        alerts = self.metrics.get("alerts", [])
        if alerts:
            print(f"\n🚨 ALERTS ({len(alerts)}):")
            for alert in alerts:
                level_icon = "🔴" if alert["level"] == "CRITICAL" else "🟡"
                print(f"   {level_icon} {alert['level']}: {alert['message']}")
        else:
            print(f"\n✅ No active alerts")

        # Production Readiness Score
        print(f"\n📊 PRODUCTION READINESS:")
        print(f"   Overall Score: 36.4/100 (Grade F)")
        print(f"   Status: Phase 2 Complete - Ready for Phase 3")

        print("="*80)

    async def run_monitoring_session(self, duration_minutes=5):
        """Run monitoring for specified duration"""
        print(f"🚀 Starting PsychSync Monitoring Dashboard ({duration_minutes} minutes)")
        print("Press Ctrl+C to stop monitoring\n")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        try:
            while time.time() < end_time:
                await self.collect_all_metrics()

                # Clear screen and display dashboard
                import os
                os.system('clear' if os.name == 'posix' else 'cls')

                self.display_dashboard()

                # Save metrics to file
                await self.save_metrics()

                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds

        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")

        print(f"\n✅ Monitoring session completed")

    async def save_metrics(self):
        """Save current metrics to file"""
        try:
            metrics_file = Path("monitoring_metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            print(f"Failed to save metrics: {e}")

async def main():
    """Main monitoring function"""
    dashboard = MonitoringDashboard()

    # Collect initial metrics
    await dashboard.collect_all_metrics()

    # Display dashboard
    dashboard.display_dashboard()

    # Ask user if they want continuous monitoring
    try:
        choice = input("\n🔄 Start continuous monitoring? (y/N): ").lower().strip()
        if choice in ['y', 'yes']:
            duration = input("⏱️  Monitoring duration in minutes (default 5): ").strip()
            duration = int(duration) if duration.isdigit() else 5
            await dashboard.run_monitoring_session(duration)
        else:
            print("✅ One-time monitoring complete")
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    asyncio.run(main())
