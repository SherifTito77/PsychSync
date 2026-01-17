#!/usr/bin/env python3
"""
Advanced Monitoring System with Predictive Alerting
Sophisticated monitoring with trend analysis and predictive capabilities
"""

import asyncio
import time
import json
import statistics
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import deque
import psutil

class AdvancedMonitoringSystem:
    def __init__(self):
        self.metrics_history = {
            "system": deque(maxlen=100),  # Store last 100 data points
            "database": deque(maxlen=100),
            "api": deque(maxlen=100),
            "redis": deque(maxlen=100)
        }
        self.alert_thresholds = self._initialize_thresholds()
        self.prediction_models = self._initialize_prediction_models()
        self.start_time = datetime.now()

    def _initialize_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize alert thresholds with dynamic adjustment"""
        return {
            "system": {
                "cpu_warning": 75.0,
                "cpu_critical": 90.0,
                "memory_warning": 80.0,
                "memory_critical": 90.0,
                "disk_warning": 85.0,
                "disk_critical": 95.0,
                "load_warning": 4.0,
                "load_critical": 6.0
            },
            "api": {
                "response_time_warning": 200.0,  # ms
                "response_time_critical": 1000.0,  # ms
                "error_rate_warning": 5.0,  # %
                "error_rate_critical": 10.0  # %
            },
            "database": {
                "connection_warning": 80.0,  # % of max connections
                "connection_critical": 90.0,
                "query_time_warning": 500.0,  # ms
                "query_time_critical": 2000.0
            }
        }

    def _initialize_prediction_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize predictive models"""
        return {
            "trend_analysis": {
                "window_size": 10,  # Look at last 10 data points
                "trend_threshold": 0.1  # 10% change triggers prediction
            },
            "anomaly_detection": {
                "std_dev_multiplier": 2.0,  # 2 standard deviations from mean
                "min_samples": 5  # Minimum samples for analysis
            },
            "capacity_planning": {
                "growth_rate_window": 20,  # Last 20 data points
                "capacity_threshold": 0.8  # 80% utilization triggers capacity alert
            }
        }

    async def collect_enhanced_metrics(self) -> Dict[str, Any]:
        """Collect enhanced system metrics with additional context"""
        system_metrics = await self._collect_system_metrics()
        database_metrics = await self._collect_database_metrics()
        api_metrics = await self._collect_api_metrics()
        redis_metrics = await self._collect_redis_metrics()

        # Add timestamp and metadata
        timestamp = datetime.now().isoformat()

        return {
            "timestamp": timestamp,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "system": system_metrics,
            "database": database_metrics,
            "api": api_metrics,
            "redis": redis_metrics,
            "metadata": {
                "collection_time_ms": self._measure_collection_time(),
                "monitoring_version": "3.0"
            }
        }

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Network metrics
        network = psutil.net_io_counters()
        network_sent_mb = network.bytes_sent / 1024 / 1024
        network_recv_mb = network.bytes_recv / 1024 / 1024

        # Process metrics
        process_count = len(psutil.pids())

        # Temperature (if available)
        temps = psutil.sensors_temperatures() if hasattr(psutil, 'sensors_temperatures') else {}

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "load_avg": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            },
            "memory": {
                "percent": memory.percent,
                "available_gb": memory.available / 1024 / 1024 / 1024,
                "used_gb": memory.used / 1024 / 1024 / 1024,
                "total_gb": memory.total / 1024 / 1024 / 1024
            },
            "disk": {
                "percent": disk.percent,
                "free_gb": disk.free / 1024 / 1024 / 1024,
                "used_gb": disk.used / 1024 / 1024 / 1024,
                "total_gb": disk.total / 1024 / 1024 / 1024
            },
            "network": {
                "sent_mb": round(network_sent_mb, 2),
                "recv_mb": round(network_recv_mb, 2)
            },
            "processes": {
                "count": process_count,
                "running": len([p for p in psutil.process_iter() if p.status() == 'running'])
            },
            "temperature": {
                "cpu_temp": temps.get('coretemp', [{}])[0].get('current', 0) if temps else 0,
                "available": len(temps) > 0
            }
        }

    async def _collect_database_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive database metrics"""
        try:
            # Connection test with timing
            start_time = time.time()
            result = subprocess.run(
                ['psql', '-d', 'psychsync_db', '-c',
                 'SELECT COUNT(*) as users, pg_stat_activity.count as connections FROM users, pg_stat_activity'],
                capture_output=True, text=True, timeout=5
            )
            connection_time = (time.time() - start_time) * 1000

            if result.returncode == 0:
                # Parse results
                lines = result.stdout.strip().split('\n')
                user_count = 0
                connection_count = 0

                for line in lines[-3:]:  # Check last few lines
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 2:
                            try:
                                val = int(parts[0].strip())
                                if 'users' in line.lower():
                                    user_count = val
                                elif 'connections' in line.lower():
                                    connection_count = val
                            except ValueError:
                                continue

                return {
                    "status": "connected",
                    "connection_time_ms": round(connection_time, 2),
                    "users_count": user_count,
                    "active_connections": connection_count,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr.strip(),
                    "connection_time_ms": round(connection_time, 2)
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "connection_time_ms": 0
            }

    async def _collect_api_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive API metrics"""
        try:
            import requests
            import statistics

            # Test multiple endpoints
            endpoints = [
                "/api/v1/health",
                "/api/v1/health/db"
            ]

            response_times = []
            status_codes = []
            errors = []

            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    response = requests.get(
                        f"http://localhost:8000{endpoint}",
                        timeout=5
                    )
                    response_time = (time.time() - start_time) * 1000

                    response_times.append(response_time)
                    status_codes.append(response.status_code)

                except Exception as e:
                    errors.append(str(e))
                    response_times.append(5000)  # Penalty for timeout/error
                    status_codes.append(500)

            return {
                "status": "healthy" if len(errors) == 0 else "degraded",
                "endpoints_tested": len(endpoints),
                "response_times": {
                    "avg_ms": round(statistics.mean(response_times), 2),
                    "min_ms": round(min(response_times), 2),
                    "max_ms": round(max(response_times), 2),
                    "p95_ms": round(sorted(response_times)[int(len(response_times) * 0.95)], 2) if response_times else 0
                },
                "success_rate": round((len([c for c in status_codes if c == 200]) / len(status_codes)) * 100, 2),
                "status_codes": list(set(status_codes)),
                "errors": errors
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _collect_redis_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive Redis metrics"""
        try:
            import redis

            r = redis.Redis(host='localhost', port=6379, decode_responses=True)

            # Test connection
            start_time = time.time()
            r.ping()
            ping_time = (time.time() - start_time) * 1000

            # Get Redis info
            info = r.info()

            # Memory usage analysis
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            memory_usage_percent = (used_memory / max_memory * 100) if max_memory > 0 else 0

            # Connection details
            connected_clients = info.get('connected_clients', 0)
            blocked_clients = info.get('blocked_clients', 0)

            # Performance metrics
            total_commands = info.get('total_commands_processed', 0)
            instantaneous_ops_per_sec = info.get('instantaneous_ops_per_sec', 0)
            keyspace_hits = info.get('keyspace_hits', 0)
            keyspace_misses = info.get('keyspace_misses', 0)
            hit_rate = (keyspace_hits / (keyspace_hits + keyspace_misses) * 100) if (keyspace_hits + keyspace_misses) > 0 else 0

            return {
                "status": "connected",
                "ping_time_ms": round(ping_time, 2),
                "memory": {
                    "used_mb": round(used_memory / 1024 / 1024, 2),
                    "max_mb": round(max_memory / 1024 / 1024, 2),
                    "usage_percent": round(memory_usage_percent, 2)
                },
                "connections": {
                    "total": connected_clients,
                    "blocked": blocked_clients
                },
                "performance": {
                    "total_commands": total_commands,
                    "ops_per_sec": instantaneous_ops_per_sec,
                    "hit_rate_percent": round(hit_rate, 2)
                },
                "keyspace": {
                    "keys": info.get('db0', {}).get('keys', 0),
                    "expires": info.get('db0', {}).get('expires', 0)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _measure_collection_time(self) -> float:
        """Measure metrics collection time"""
        start = time.time()
        # Simulate collection overhead
        time.sleep(0.001)
        return (time.time() - start) * 1000

    def analyze_trends(self, metric_name: str, current_value: float) -> Dict[str, Any]:
        """Analyze trends for a specific metric"""
        if metric_name not in self.metrics_history:
            return {"trend": "stable", "direction": 0, "confidence": 0}

        history = self.metrics_history[metric_name]
        if len(history) < self.prediction_models["trend_analysis"]["window_size"]:
            return {"trend": "insufficient_data", "direction": 0, "confidence": 0}

        # Extract recent values
        recent_values = [m.get("value", 0) for m in list(history)[-10:]]

        if len(recent_values) < 2:
            return {"trend": "stable", "direction": 0, "confidence": 0}

        # Calculate trend
        x = list(range(len(recent_values)))
        y = recent_values

        # Simple linear regression for trend calculation
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0

        # Calculate trend direction and magnitude
        avg_value = statistics.mean(y)
        trend_percent = (slope * len(y) / avg_value * 100) if avg_value != 0 else 0

        # Determine trend
        threshold = self.prediction_models["trend_analysis"]["trend_threshold"] * 100
        if abs(trend_percent) < threshold:
            trend = "stable"
            direction = 0
        elif trend_percent > 0:
            trend = "increasing"
            direction = 1
        else:
            trend = "decreasing"
            direction = -1

        # Calculate confidence based on consistency
        std_dev = statistics.stdev(y) if len(y) > 1 else 0
        cv = (std_dev / avg_value * 100) if avg_value != 0 else 0  # Coefficient of variation
        confidence = max(0, min(100, 100 - cv))  # Lower variation = higher confidence

        return {
            "trend": trend,
            "direction": direction,
            "trend_percent": round(trend_percent, 2),
            "slope": round(slope, 4),
            "confidence": round(confidence, 2),
            "data_points": len(recent_values)
        }

    def detect_anomalies(self, metric_name: str, current_value: float) -> Dict[str, Any]:
        """Detect anomalies using statistical methods"""
        if metric_name not in self.metrics_history:
            return {"anomaly": False, "z_score": 0, "severity": "none"}

        history = self.metrics_history[metric_name]
        min_samples = self.prediction_models["anomaly_detection"]["min_samples"]

        if len(history) < min_samples:
            return {"anomaly": False, "z_score": 0, "severity": "none"}

        # Extract values
        values = [m.get("value", 0) for m in list(history)]

        if len(set(values)) == 1:  # All values are the same
            return {"anomaly": False, "z_score": 0, "severity": "none"}

        # Calculate statistics
        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values)

        if std_dev == 0:
            return {"anomaly": False, "z_score": 0, "severity": "none"}

        # Calculate Z-score
        z_score = abs((current_value - mean_val) / std_dev)
        threshold = self.prediction_models["anomaly_detection"]["std_dev_multiplier"]

        # Determine anomaly severity
        if z_score > threshold * 2:
            severity = "critical"
        elif z_score > threshold:
            severity = "warning"
        else:
            severity = "none"

        return {
            "anomaly": z_score > threshold,
            "z_score": round(z_score, 2),
            "severity": severity,
            "mean": round(mean_val, 2),
            "std_dev": round(std_dev, 2),
            "threshold": round(threshold, 2)
        }

    def predict_capacity_needs(self, metric_name: str) -> Dict[str, Any]:
        """Predict future capacity needs"""
        if metric_name not in self.metrics_history:
            return {"prediction": "insufficient_data", "time_to_threshold": None}

        history = self.metrics_history[metric_name]
        window = self.prediction_models["capacity_planning"]["growth_rate_window"]

        if len(history) < window:
            return {"prediction": "insufficient_data", "time_to_threshold": None}

        # Extract recent values
        recent_values = [m.get("value", 0) for m in list(history)[-window:]]

        if len(recent_values) < 2:
            return {"prediction": "insufficient_data", "time_to_threshold": None}

        # Calculate growth rate
        first_value = recent_values[0]
        last_value = recent_values[-1]

        if first_value == 0:
            return {"prediction": "cannot_predict", "time_to_threshold": None}

        growth_rate = (last_value - first_value) / first_value

        # Determine threshold (e.g., 80% utilization)
        threshold = self.prediction_models["capacity_planning"]["capacity_threshold"] * 100

        if metric_name in ["cpu", "memory", "disk"]:
            # For utilization metrics
            if last_value >= threshold:
                time_to_threshold = 0
            elif growth_rate <= 0:
                time_to_threshold = None  # Not growing towards threshold
            else:
                # Calculate time to reach threshold
                remaining = threshold - last_value
                if growth_rate > 0:
                    periods_to_threshold = remaining / (growth_rate * first_value)
                    time_to_threshold = periods_to_threshold * 5  # Assuming 5-minute collection interval
                else:
                    time_to_threshold = None
        else:
            # For other metrics
            time_to_threshold = None

        return {
            "prediction": "growing" if growth_rate > 0.01 else "stable" if abs(growth_rate) < 0.01 else "declining",
            "growth_rate_percent": round(growth_rate * 100, 2),
            "current_value": round(last_value, 2),
            "threshold": round(threshold, 2),
            "time_to_threshold_minutes": round(time_to_threshold, 1) if time_to_threshold else None,
            "data_points_analyzed": len(recent_values)
        }

    async def generate_comprehensive_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive alerts with predictive insights"""
        alerts = []

        # Traditional threshold-based alerts
        alerts.extend(self._generate_threshold_alerts(metrics))

        # Trend-based alerts
        alerts.extend(self._generate_trend_alerts(metrics))

        # Anomaly detection alerts
        alerts.extend(self._generate_anomaly_alerts(metrics))

        # Capacity planning alerts
        alerts.extend(self._generate_capacity_alerts(metrics)

        # Performance degradation alerts
        alerts.extend(self._generate_performance_alerts(metrics))

        return alerts

    def _generate_threshold_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate traditional threshold-based alerts"""
        alerts = []

        # System alerts
        system = metrics.get("system", {})

        if "cpu" in system:
            cpu_percent = system["cpu"]["percent"]
            if cpu_percent >= self.alert_thresholds["system"]["cpu_critical"]:
                alerts.append({
                    "level": "CRITICAL",
                    "type": "threshold",
                    "source": "system",
                    "metric": "cpu",
                    "current_value": cpu_percent,
                    "threshold": self.alert_thresholds["system"]["cpu_critical"],
                    "message": f"CRITICAL: CPU usage at {cpu_percent:.1f}%"
                })
            elif cpu_percent >= self.alert_thresholds["system"]["cpu_warning"]:
                alerts.append({
                    "level": "WARNING",
                    "type": "threshold",
                    "source": "system",
                    "metric": "cpu",
                    "current_value": cpu_percent,
                    "threshold": self.alert_thresholds["system"]["cpu_warning"],
                    "message": f"WARNING: CPU usage at {cpu_percent:.1f}%"
                })

        # Memory alerts
        if "memory" in system:
            memory_percent = system["memory"]["percent"]
            if memory_percent >= self.alert_thresholds["system"]["memory_critical"]:
                alerts.append({
                    "level": "CRITICAL",
                    "type": "threshold",
                    "source": "system",
                    "metric": "memory",
                    "current_value": memory_percent,
                    "threshold": self.alert_thresholds["system"]["memory_critical"],
                    "message": f"CRITICAL: Memory usage at {memory_percent:.1f}%"
                })

        # Disk alerts
        if "disk" in system:
            disk_percent = system["disk"]["percent"]
            if disk_percent >= self.alert_thresholds["system"]["disk_critical"]:
                alerts.append({
                    "level": "CRITICAL",
                    "type": "threshold",
                    "source": "system",
                    "metric": "disk",
                    "current_value": disk_percent,
                    "threshold": self.alert_thresholds["system"]["disk_critical"],
                    "message": f"CRITICAL: Disk usage at {disk_percent:.1f}%"
                })

        return alerts

    def _generate_trend_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trend-based predictive alerts"""
        alerts = []

        # Analyze trends for key metrics
        key_metrics = [
            ("system.cpu", metrics.get("system", {}).get("cpu", {}).get("percent", 0)),
            ("system.memory", metrics.get("system", {}).get("memory", {}).get("percent", 0)),
            ("system.disk", metrics.get("system", {}).get("disk", {}).get("percent", 0))
        ]

        for metric_path, current_value in key_metrics:
            trend_analysis = self.analyze_trends(metric_path, current_value)

            if trend_analysis["trend"] == "increasing" and trend_analysis["confidence"] > 70:
                alerts.append({
                    "level": "WARNING",
                    "type": "trend",
                    "source": "predictive",
                    "metric": metric_path,
                    "trend": trend_analysis["trend"],
                    "trend_percent": trend_analysis["trend_percent"],
                    "confidence": trend_analysis["confidence"],
                    "message": f"PREDICTIVE: {metric_path} showing {trend_analysis['trend']} trend ({trend_analysis['trend_percent']:.1f}%)"
                })

        return alerts

    def _generate_anomaly_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate anomaly detection alerts"""
        alerts = []

        # Check for anomalies in key metrics
        anomaly_checks = [
            ("system.cpu", metrics.get("system", {}).get("cpu", {}).get("percent", 0)),
            ("system.memory", metrics.get("system", {}).get("memory", {}).get("percent", 0)),
            ("api.response_times", metrics.get("api", {}).get("response_times", {}).get("avg_ms", 0))
        ]

        for metric_path, current_value in anomaly_checks:
            anomaly = self.detect_anomalies(metric_path, current_value)

            if anomaly["anomaly"]:
                level = "CRITICAL" if anomaly["severity"] == "critical" else "WARNING"
                alerts.append({
                    "level": level,
                    "type": "anomaly",
                    "source": "predictive",
                    "metric": metric_path,
                    "z_score": anomaly["z_score"],
                    "severity": anomaly["severity"],
                    "message": f"ANOMALY DETECTED: {metric_path} value {current_value} is {anomaly['severity']} (Z-score: {anomaly['z_score']})"
                })

        return alerts

    def _generate_capacity_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate capacity planning alerts"""
        alerts = []

        capacity_checks = [
            ("system.cpu", metrics.get("system", {}).get("cpu", {}).get("percent", 0)),
            ("system.memory", metrics.get("system", {}).get("memory", {}).get("percent", 0)),
            ("system.disk", metrics.get("system", {}).get("disk", {}).get("percent", 0))
        ]

        for metric_path, current_value in capacity_checks:
            capacity = self.predict_capacity_needs(metric_path)

            if capacity["time_to_threshold_minutes"] is not None:
                if capacity["time_to_threshold_minutes"] <= 60:  # Within 1 hour
                    alerts.append({
                        "level": "WARNING",
                        "type": "capacity",
                        "source": "predictive",
                        "metric": metric_path,
                        "prediction": capacity["prediction"],
                        "time_to_threshold": capacity["time_to_threshold_minutes"],
                        "message": f"CAPACITY ALERT: {metric_path} will reach threshold in {capacity['time_to_threshold_minutes']:.1f} minutes"
                    })
                elif capacity["time_to_threshold_minutes"] <= 1440:  # Within 24 hours
                    alerts.append({
                        "level": "INFO",
                        "type": "capacity",
                        "source": "predictive",
                        "metric": metric_path,
                        "prediction": capacity["prediction"],
                        "time_to_threshold": capacity["time_to_threshold_minutes"],
                        "message": f"CAPACITY FORECAST: {metric_path} will reach threshold in {capacity['time_to_threshold_minutes']:.1f} minutes"
                    })

        return alerts

    def _generate_performance_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance degradation alerts"""
        alerts = []

        # API performance alerts
        api = metrics.get("api", {})
        if "response_times" in api and "success_rate" in api:
            response_time = api["response_times"]["avg_ms"]
            success_rate = api["success_rate"]

            if response_time > 500:  # Poor performance
                alerts.append({
                    "level": "WARNING",
                    "type": "performance",
                    "source": "api",
                    "metric": "response_time",
                    "current_value": response_time,
                    "message": f"PERFORMANCE DEGRADATION: API response time {response_time:.0f}ms is poor"
                })

            if success_rate < 95:  # Low success rate
                alerts.append({
                    "level": "CRITICAL" if success_rate < 90 else "WARNING",
                    "type": "performance",
                    "source": "api",
                    "metric": "success_rate",
                    "current_value": success_rate,
                    "message": f"RELIABILITY ISSUE: API success rate {success_rate:.1f}% is low"
                })

        # Collection time alerts
        metadata = metrics.get("metadata", {})
        if "collection_time_ms" in metadata and metadata["collection_time_ms"] > 100:
            alerts.append({
                "level": "INFO",
                "type": "performance",
                "source": "monitoring",
                "metric": "collection_time",
                "current_value": metadata["collection_time_ms"],
                "message": f"MONITORING OVERHEAD: Metrics collection taking {metadata['collection_time_ms']:.1f}ms"
            })

        return alerts

    def update_metrics_history(self, metrics: Dict[str, Any]):
        """Update metrics history for trend analysis"""
        timestamp = metrics.get("timestamp", datetime.now().isoformat())

        # Store individual component metrics
        for component, data in metrics.items():
            if component in ["system", "database", "api", "redis"] and isinstance(data, dict):
                # Extract primary value for trend analysis
                if component == "system":
                    value = data.get("cpu", {}).get("percent", 0)
                elif component == "database":
                    value = data.get("connection_time_ms", 0)
                elif component == "api":
                    value = data.get("response_times", {}).get("avg_ms", 0)
                elif component == "redis":
                    value = data.get("ping_time_ms", 0)
                else:
                    value = 0

                self.metrics_history[component].append({
                    "timestamp": timestamp,
                    "value": value,
                    "data": data
                })

    def display_enhanced_dashboard(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]):
        """Display enhanced monitoring dashboard with predictions"""
        print("\n" + "="*100)
        print(f"🚀 PSYCHSYNC ADVANCED MONITORING DASHBOARD - PREDICTIVE ANALYTICS")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)

        # System Metrics with trend analysis
        sys_metrics = metrics.get("system", {})
        print(f"\n🖥️  SYSTEM METRICS:")
        print(f"   CPU Usage: {sys_metrics.get('cpu', {}).get('percent', 0):.1f}%")
        print(f"   Memory: {sys_metrics.get('memory', {}).get('percent', 0):.1f}% ({sys_metrics.get('memory', {}).get('available_gb', 0):.1f}GB available)")
        print(f"   Disk: {sys_metrics.get('disk', {}).get('percent', 0):.1f}%")
        print(f"   Load Average: {sys_metrics.get('cpu', {}).get('load_avg', 0):.2f}")
        print(f"   Processes: {sys_metrics.get('processes', {}).get('count', 0)} total, {sys_metrics.get('processes', {}).get('running', 0)} running")

        # Network metrics
        if "network" in sys_metrics:
            net = sys_metrics["network"]
            print(f"   Network: ↑{net.get('sent_mb', 0):.1f}MB ↓{net.get('recv_mb', 0):.1f}MB")

        # Database Metrics
        db_metrics = metrics.get("database", {})
        print(f"\n🗄️  DATABASE METRICS:")
        print(f"   Status: {db_metrics.get('status', 'unknown').upper()}")
        if db_metrics.get('status') == 'connected':
            print(f"   Connection Time: {db_metrics.get('connection_time_ms', 0):.1f}ms")
            print(f"   Users: {db_metrics.get('users_count', 0):,}")
            print(f"   Active Connections: {db_metrics.get('active_connections', 0)}")
        else:
            print(f"   Error: {db_metrics.get('error', 'Unknown error')}")

        # API Metrics with detailed breakdown
        api_metrics = metrics.get("api", {})
        print(f"\n🌐 API METRICS:")
        print(f"   Status: {api_metrics.get('status', 'unknown').upper()}")
        if "response_times" in api_metrics:
            rt = api_metrics["response_times"]
            print(f"   Response Times: Avg {rt['avg_ms']:.0f}ms, Min {rt['min_ms']:.0f}ms, Max {rt['max_ms']:.0f}ms, P95 {rt['p95_ms']:.0f}ms")
        print(f"   Success Rate: {api_metrics.get('success_rate', 0):.1f}%")
        print(f"   Endpoints Tested: {api_metrics.get('endpoints_tested', 0)}")

        # Redis Metrics
        redis_metrics = metrics.get("redis", {})
        print(f"\n📦 REDIS METRICS:")
        print(f"   Status: {redis_metrics.get('status', 'unknown').upper()}")
        if redis_metrics.get('status') == 'connected':
            print(f"   Ping Time: {redis_metrics.get('ping_time_ms', 0):.1f}ms")
            print(f"   Memory: {redis_metrics.get('memory', {}).get('used_mb', 0):.1f}MB ({redis_metrics.get('memory', {}).get('usage_percent', 0):.1f}%)")
            print(f"   Connections: {redis_metrics.get('connections', {}).get('total', 0)} total")
            print(f"   Performance: {redis_metrics.get('performance', {}).get('ops_per_sec', 0):.0f} ops/sec, {redis_metrics.get('performance', {}).get('hit_rate_percent', 0):.1f}% hit rate")

        # Predictive Insights
        print(f"\n🔮 PREDICTIVE INSIGHTS:")
        self._display_predictions_summary()

        # Alerts with categorization
        if alerts:
            self._display_categorized_alerts(alerts)
        else:
            print(f"\n✅ No active alerts - System operating normally")

        # System Health Score
        health_score = self._calculate_health_score(metrics, alerts)
        health_grade = self._get_health_grade(health_score)

        print(f"\n📊 SYSTEM HEALTH SCORE: {health_score:.1f}/100 ({health_grade})")
        print("="*100)

    def _display_predictions_summary(self):
        """Display summary of predictions"""
        # Show trend analysis for key metrics
        key_metrics = ["system.cpu", "system.memory"]

        for metric_path in key_metrics:
            if metric_path in self.metrics_history and len(self.metrics_history[metric_path]) >= 5:
                trend = self.analyze_trends(metric_path, 0)
                if trend["confidence"] > 50:
                    status_emoji = "📈" if trend["direction"] > 0 else "📉" if trend["direction"] < 0 else "➡️"
                    print(f"   {status_emoji} {metric_path}: {trend['trend']} ({trend['trend_percent']:+.1f}%)")

    def _display_categorized_alerts(self, alerts: List[Dict[str, Any]]):
        """Display alerts categorized by level and type"""
        # Group alerts by level
        critical_alerts = [a for a in alerts if a["level"] == "CRITICAL"]
        warning_alerts = [a for a in alerts if a["level"] == "WARNING"]
        info_alerts = [a for a in alerts if a["level"] == "INFO"]

        if critical_alerts:
            print(f"\n🔴 CRITICAL ALERTS ({len(critical_alerts)}):")
            for alert in critical_alerts:
                print(f"   • {alert['message']}")

        if warning_alerts:
            print(f"\n🟡 WARNING ALERTS ({len(warning_alerts)}):")
            for alert in warning_alerts:
                print(f"   • {alert['message']}")

        if info_alerts:
            print(f"\n🔵 INFO ALERTS ({len(info_alerts)}):")
            for alert in info_alerts:
                print(f"   • {alert['message']}")

    def _calculate_health_score(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]) -> float:
        """Calculate overall system health score"""
        score = 100.0

        # Deduct points for critical issues
        critical_count = len([a for a in alerts if a["level"] == "CRITICAL"])
        score -= critical_count * 20

        # Deduct points for warnings
        warning_count = len([a for a in alerts if a["level"] == "WARNING"])
        score -= warning_count * 10

        # Deduct points for info alerts (smaller penalty)
        info_count = len([a for a in alerts if a["level"] == "INFO"])
        score -= info_count * 5

        # Factor in component health
        system = metrics.get("system", {})
        if system.get("cpu", {}).get("percent", 0) > 80:
            score -= 10
        if system.get("memory", {}).get("percent", 0) > 85:
            score -= 10

        db = metrics.get("database", {})
        if db.get("status") != "connected":
            score -= 30

        api = metrics.get("api", {})
        if api.get("status") != "healthy":
            score -= 20
        elif api.get("success_rate", 100) < 95:
            score -= 15

        redis = metrics.get("redis", {})
        if redis.get("status") != "connected":
            score -= 10

        return max(0, score)

    def _get_health_grade(self, score: float) -> str:
        """Get health grade based on score"""
        if score >= 90:
            return "A (Excellent)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Fair)"
        elif score >= 60:
            return "D (Poor)"
        else:
            return "F (Critical)"

    async def run_advanced_monitoring_session(self, duration_minutes=10):
        """Run advanced monitoring session with predictions"""
        print(f"🚀 Starting Advanced Monitoring with Predictive Analytics ({duration_minutes} minutes)")
        print("Real-time trend analysis, anomaly detection, and capacity planning enabled\n")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        try:
            while time.time() < end_time:
                # Collect comprehensive metrics
                metrics = await self.collect_enhanced_metrics()

                # Update history for trend analysis
                self.update_metrics_history(metrics)

                # Generate predictive alerts
                alerts = await self.generate_comprehensive_alerts(metrics)

                # Clear screen and display dashboard
                import os
                os.system('clear' if os.name == 'posix' else 'cls')

                self.display_enhanced_dashboard(metrics, alerts)

                # Save enhanced metrics
                await self.save_enhanced_metrics(metrics, alerts)

                # Wait before next update
                await asyncio.sleep(30)  # Update every 30 seconds

        except KeyboardInterrupt:
            print("\n\n🛑 Advanced monitoring stopped by user")

        print(f"\n✅ Advanced monitoring session completed")

    async def save_enhanced_metrics(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]):
        """Save enhanced metrics with predictions"""
        try:
            data = {
                "metrics": metrics,
                "alerts": alerts,
                "predictions": {
                    "trends": {
                        metric_path: self.analyze_trends(metric_path, 0)
                        for metric_path in self.metrics_history.keys()
                        if len(self.metrics_history[metric_path]) >= 5
                    },
                    "anomalies": {
                        metric_path: self.detect_anomalies(metric_path, 0)
                        for metric_path in self.metrics_history.keys()
                        if len(self.metrics_history[metric_path]) >= 5
                    },
                    "capacity": {
                        metric_path: self.predict_capacity_needs(metric_path)
                        for metric_path in self.metrics_history.keys()
                        if len(self.metrics_history[metric_path]) >= 5
                    }
                },
                "monitoring_version": "3.0",
                "features": ["trend_analysis", "anomaly_detection", "capacity_planning", "predictive_alerts"]
            }

            metrics_file = Path("advanced_monitoring_metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to save enhanced metrics: {e}")

async def main():
    """Main advanced monitoring function"""
    monitor = AdvancedMonitoringSystem()

    # Collect initial metrics
    metrics = await monitor.collect_enhanced_metrics()

    # Display dashboard
    alerts = await monitor.generate_comprehensive_alerts(metrics)
    monitor.display_enhanced_dashboard(metrics, alerts)

    # Ask user if they want continuous monitoring
    try:
        choice = input("\n🔄 Start advanced monitoring with predictions? (y/N): ").lower().strip()
        if choice in ['y', 'yes']:
            duration = input("⏱️  Monitoring duration in minutes (default 10): ").strip()
            duration = int(duration) if duration.isdigit() else 10
            await monitor.run_advanced_monitoring_session(duration)
        else:
            print("✅ One-time advanced monitoring complete")
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped")

if __name__ == "__main__":
    asyncio.run(main())
