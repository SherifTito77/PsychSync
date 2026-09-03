#!/usr/bin/env python3
"""
Production Monitoring Setup Script

This script sets up comprehensive monitoring for PsychSync production deployment.
Includes Prometheus, Grafana, alerting, and health check endpoints.

Usage:
    python scripts/production_monitoring_setup.py [--setup-all] [--check-health] [--alerts-test]

Prerequisites:
    - Docker and Docker Compose installed
    - Redis and PostgreSQL running
    - Sufficient system resources
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMonitoringSetup:
    """Production monitoring setup and management"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.monitoring_dir = self.project_root / "monitoring"
        self.config_dir = self.monitoring_dir / "config"
        self.docker_compose_file = self.project_root / "docker-compose.monitoring.yml"

        # Create directories
        self.monitoring_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)

    async def setup_all(self):
        """Set up complete monitoring stack"""
        logger.info("Setting up production monitoring system...")

        await self.create_docker_compose()
        await self.setup_prometheus()
        await self.setup_grafana()
        await self.setup_alertmanager()
        await self.setup_health_checks()
        await self.setup_log_aggregation()

        logger.info("✅ Production monitoring setup completed")

    def create_docker_compose(self):
        """Create Docker Compose file for monitoring stack"""
        docker_compose_content = """
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.40.0
    container_name: psychsync_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/config/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/rules:/etc/prometheus/rules
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--storage.tsdb.retention.size=10GB'
    networks:
      - monitoring
    restart: unless-stopped

  grafana:
    image: grafana/grafana:9.3.0
    container_name: psychsync_grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin123!}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
      - GF_FEATURE_TOGGLES_ENABLE=publicDashboard
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/etc/grafana/dashboards
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - monitoring
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:v0.25.0
    container_name: psychsync_alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/config/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    networks:
      - monitoring
    restart: unless-stopped

  node_exporter:
    image: prom/node-exporter:v1.6.0
    container_name: psychsync_node_exporter
    ports:
      - "9100:9100"
    command:
      - '--path.rootfs=/host'
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host)etc/'
    volumes:
      - /:/host:ro
    networks:
      - monitoring
    restart: unless-stopped

  postgres_exporter:
    image: prom/prometheus-postgres-exporter:v0.11.1
    container_name: psychsync_postgres_exporter
    ports:
      - "9187:9187"
    environment:
      DATA_SOURCE_NAME: "postgresql://psychsync_user:password@postgres:5432/psychsync_prod?sslmode=require"
    depends_on:
      - postgres
    networks:
      - monitoring
      - default
    restart: unless-stopped

  redis_exporter:
    image: oliver006/redis_exporter:v1.43.0
    container_name: psychsync_redis_exporter
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://redis:6379
    depends_on:
      - redis
    networks:
      - monitoring
      - default
    restart: unless-stopped

  loki:
    image: grafana/loki:2.8.0
    container_name: psychsync_loki
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/config/loki.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring
    restart: unless-stopped

  promtail:
    image: grafana/promtail:2.8.0
    container_name: psychsync_promtail
    ports:
      - "9080:9080"
    volumes:
      - ./monitoring/config/promtail.yml:/etc/promtail/config.yml
      - /var/log:/var/log:ro
    command: -config.file=/etc/promtail/config.yml
    depends_on:
      - loki
    networks:
      - monitoring
      - default
    restart: unless-stopped

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: psychsync_elasticsearch
    environment:
      - node.name=psychsync-node
      - cluster.name=psychsync
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - monitoring
    restart: unless-stopped

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    container_name: psychsync_kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - monitoring
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
  elasticsearch_data:
  loki_data:

networks:
  monitoring:
    driver: bridge
  default:
    external: true

"""
        with open(self.docker_compose_file, 'w') as f:
            f.write(docker_compose_content)

        logger.info("✅ Docker Compose file created")

    async def setup_prometheus(self):
        """Setup Prometheus configuration"""
        prometheus_config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'psychsync'
    environment: 'production'

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'psychsync-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
    scrape_timeout: 10s
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance

  - job_name: 'psychsync-database'
    static_configs:
      - targets: ['postgres_exporter:9187']
    scrape_interval: 30s

  - job_name: 'psychsync-redis'
    static_configs:
      - targets: ['redis_exporter:9121']
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node_exporter:9100']
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']
    metrics_path: '/metrics'

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
    metrics_path: '/metrics'

alerting:
  alertmanagers:
    - static_configs:
      - - alertmanager:9093

recording_rules:
  - name: 'psychsync-recording'
    rules:
      - record: 'api_requests:rate5m'
        expr: rate(http_requests_total[5m])
        labels:
          app: 'psychsync'
          environment: 'production'
"""

        with open(self.config_dir / "prometheus.yml", 'w') as f:
            f.write(prometheus_config)

        logger.info("✅ Prometheus configuration created")

    async def setup_grafana(self):
        """Setup Grafana configuration"""
        # Create directories
        grafana_provisioning = self.monitoring_dir / "grafana" / "provisioning"
        grafana_dashboards = self.monitoring_dir / "grafana" / "dashboards"

        grafana_provisioning.mkdir(parents=True, exist_ok=True)
        grafana_dashboards.mkdir(parents=True, exist_ok=True)

        # Grafana provisioning configuration
        provisioning_config = """
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

dashboardProviders:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/dashboards
"""

        with open(grafana_provisioning / "datasources.yml", 'w') as f:
            f.write(provisioning_config)

        # Create sample dashboard
        sample_dashboard = """
{
  "dashboard": {
    "id": null,
    "title": "PsychSync API Performance",
    "tags": ["psychsync", "api", "performance"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket[5m])",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, http_request_duration_seconds_bucket[5m])",
            "legendFormat": "50th percentile"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 8
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
"""

        dashboard_file = grafana_dashboards / "psychsync-api-performance.json"
        with open(dashboard_file, 'w') as f:
            f.write(sample_dashboard)

        logger.info("✅ Grafana configuration created")

    async def setup_alertmanager(self):
        """Setup AlertManager configuration"""
        alertmanager_config = """
global:
  smtp_smarthost: localhost
  smtp_from: alerts@psychsync.com
  smtp_auth_username: ${SMTP_USER}
  smtp_auth_password: ${SMTP_PASSWORD}

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'psychsync-alerts'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'psychsync-alerts'
    email_configs:
      - to: 'devops@psychsync.com'
        subject: '[PsychSync Alert] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@psychsync.com'
        subject: '[CRITICAL] PsychSync Alert: {{ .GroupLabels.alertname }}'
        body: |
          CRITICAL ALERT DETECTED

          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}

  - name: 'warning-alerts'
    email_configs:
      - to: 'devops@psychsync.com'
        subject: '[WARNING] PsychSync Alert: {{ .GroupLabels.alertname }}'
        body: |
          Warning alert detected

          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ .Labels }}
          {{ end }}

inhibit_rules:
  - name: 'SilenceWarningAlerts'
    equal: ['severity']
    source_match:
      - match:
        severity: warning
    target_match:
      - match:
        alertname: 'PsychSyncWarning'
"""

        with open(self.config_dir / "alertmanager.yml", 'w') as f:
            f.write(alertmanager_config)

        # Create alert rules
        alert_rules = """
groups:
  - name: psychsync_alerts
    rules:
      - alert: HighAPIResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket[5m]) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time detected"
          description: "95th percentile response time is above 1 second for 5 minutes"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"

      - alert: DatabaseConnectionFailure
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "Database is down for 1 minute"

      - alert: RedisConnectionFailure
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis connection failure"
          description: "Redis is down for 1 minute"

      - alert: HighMemoryUsage
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Available memory is below 10% for 5 minutes"

      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (rate(node_cpu_seconds_total[5m]) / rate(node_cpu_seconds_total[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is above 80% for 5 minutes"
"""

        rules_dir = self.config_dir / "rules"
        rules_dir.mkdir(exist_ok=True)

        with open(rules_dir / "psychsync_alerts.yml", 'w') as f:
            f.write(alert_rules)

        logger.info("✅ AlertManager configuration created")

    async def setup_health_checks(self):
        """Create comprehensive health check script"""
        health_check_script = """#!/bin/bash

# PsychSync Production Health Check Script

set -e

COLOR_GREEN='\\033[0;32m'
COLOR_YELLOW='\\033[1;33m'
COLOR_RED='\\033[0;31m'
COLOR_NC='\\033[0m'

echo -e "${COLOR_BLUE}PsychSync Production Health Check${COLOR_NC}"
echo "====================================="

# Check Docker services
echo -e "\\n${COLOR_BLUE}Checking Docker Services...${COLOR_NC}"

services=("prometheus" "grafana" "alertmanager" "node_exporter" "postgres_exporter" "redis_exporter")
all_running=true

for service in "${services[@]}"; do
    if docker ps --format "table" | grep -q "$service"; then
        echo -e "  ${COLOR_GREEN}✓ $service is running${COLOR_NC}"
    else
        echo -e "  ${COLOR_RED}✗ $service is not running${COLOR_NC}"
        all_running=false
    fi
done

# Check database connections
echo -e "\\n${COLOR_BLUE}Checking Database Connections...${COLOR_NC}"

if python3 -c "
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv('.env.production')

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'psychsync_prod'),
        user=os.getenv('DB_USER', 'psychsync_user'),
        password=os.getenv('DB_PASSWORD'),
        sslmode='require'
    )
    conn.close()
    print('  ${COLOR_GREEN}✓ Database connection successful${COLOR_NC}')
except Exception as e:
    print('  ${COLOR_RED}✗ Database connection failed: $e${COLOR_NC}')
    all_running=false
"

# Check Redis connection
if python3 -c "
import redis
import os
from dotenv import load_dotenv
load_dotenv('.env.production')

try:
    r = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True
    )
    r.ping()
    print('  ${COLOR_GREEN}✓ Redis connection successful${COLOR_NC}')
except Exception as e:
    print('  ${COLOR_RED}✗ Redis connection failed: $e${COLOR_NC}')
    all_running=false
"

# Check API health
echo -e "\\n${COLOR_BLUE}Checking API Health...${COLOR_NC}"

if curl -s -f http://localhost:8000/api/v1/health > /dev/null; then
    echo -e "  ${COLOR_GREEN}✓ API health check passed${COLOR_NC}"
else
    echo -e "  ${COLOR_RED}✗ API health check failed${COLOR_NC}"
    all_running=false
fi

# Check available disk space
echo -e "\\n${COLOR_BLUE}Checking System Resources...${COLOR_NC}"
disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$disk_usage" -gt "85" ]; then
    echo -e "  ${COLOR_YELLOW}⚠ Disk usage: ${disk_usage}% (getting high)${COLOR_NC}"
elif [ "$disk_usage" -gt "95" ]; then
    echo -e "  ${COLOR_RED}✗ Disk usage: ${disk_usage}% (critical)${COLOR_NC}"
    all_running=false
else
    echo -e "  ${COLOR_GREEN}✓ Disk usage: ${disk_usage}% (OK)${COLOR_NC}"
fi

# Final status
echo -e "\\n${COLOR_BLUE}Health Check Summary${COLOR_NC}"
echo "===================================="

if [ "$all_running" = true ]; then
    echo -e "${COLOR_GREEN}✅ All systems healthy!${COLOR_NC}"
    exit 0
else
    echo -e "${COLOR_RED}❌ Some systems need attention!${COLOR_NC}"
    exit 1
fi
"""

        health_check_file = self.project_root / "scripts" / "health_check.sh"
        health_check_file.parent.mkdir(exist_ok=True)

        with open(health_check_file, 'w') as f:
            f.write(health_check_script)

        # Make script executable
        os.chmod(health_check_file, 0o755)

        logger.info("✅ Health check script created")

    async def setup_log_aggregation(self):
        """Setup log aggregation with Loki and Promtail"""

        # Loki configuration
        loki_config = """
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  loki_server_url: http://localhost:3100/loki/api/v1/push

positions:
  filename:
    target: tmp
    labels:
      job: "varlogs"
      __path__: "/var/log/*/*"
"""

        with open(self.config_dir / "loki.yml", 'w') as f:
            f.write(loki_config)

        # Promtail configuration
        promtail_config = """
server:
  http_listen_port: 9080
  grpc_listen_port: 0

clients:
  - url: http://loki:3100/loki/api/v1/push

positions:
  - filename:
      target: /var/log/*/*
      labels:
        job: "varlogs"
        host: "${HOSTNAME}"
        __path__: "/var/log/*/*"

scrape_configs:
  - job_name: psychsync-logs
    static_configs:
      - targets:
        - localhost
      labels:
        job: "psychsync"
        __path__: "/var/log/*/*"

    pipeline_stages:
      - json_parser:
          expressions:
            - output:
              timestamp: time
              record: level
              message: output
          timestamp_format: RFC3339
          json_configs:
            - source: output
"""
        - file_metadata: []
"""

        with open(self.config_dir / "promtail.yml", 'w') as f:
            f.write(promtail_config)

        logger.info("✅ Log aggregation configuration created")

    async def check_health(self):
        """Check health of all monitoring components"""
        logger.info("Checking monitoring system health...")

        health_status = {
            "prometheus": False,
            "grafana": False,
            "alertmanager": False,
            "loki": False,
            "elasticsearch": False,
            "node_exporter": False
        }

        # Check Prometheus
        try:
            response = requests.get("http://localhost:9090/-/healthy", timeout=5)
            if response.status_code == 200:
                health_status["prometheus"] = True
                logger.info("✅ Prometheus is healthy")
        except Exception as e:
            logger.error(f"Prometheus health check failed: {e}")

        # Check Grafana
        try:
            response = requests.get("http://localhost:3001/api/health", timeout=5)
            if response.status_code == 200:
                health_status["grafana"] = True
                logger.info("✅ Grafana is healthy")
        except Exception as e:
            logger.error(f"Grafana health check failed: {e}")

        # Check AlertManager
        try:
            response = requests.get("http://localhost:9093/-/healthy", timeout=5)
            if response.status_code == 200:
                health_status["alertmanager"] = True
                logger.info("✅ AlertManager is healthy")
        except Exception as e:
            logger.error(f"AlertManager health check failed: {e}")

        # Check Loki
        try:
            response = requests.get("http://localhost:3100/ready", timeout=5)
            if response.status_code == 200:
                health_status["loki"] = True
                logger.info("✅ Loki is healthy")
        except Exception as e:
            logger.error(f"Loki health check failed: {e}")

        return health_status

    async def test_alerts(self):
        """Test alerting system"""
        logger.info("Testing alerting system...")

        try:
            # Send test alert to AlertManager
            test_alert = {
                "receiver": "psychsync-alerts",
                "status": "firing",
                "alerts": [
                    {
                        "status": "firing",
                        "labels": {
                            "alertname": "TestAlert",
                            "severity": "warning"
                        },
                        "annotations": {
                            "summary": "Test alert from monitoring setup",
                            "description": "This is a test alert to verify the alerting system is working"
                        },
                        "startsAt": datetime.utcnow().isoformat() + "Z"
                    }
                ]
            }

            response = requests.post(
                "http://localhost:9093/api/v1/alerts",
                json=test_alert,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✅ Alerting system test passed")
                return True
            else:
                logger.error(f"Alerting system test failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Alerting system test failed: {e}")
            return False

    async def start_services(self):
        """Start monitoring services"""
        logger.info("Starting monitoring services...")

        try:
            # Check if Docker is running
            result = subprocess.run(
                ["docker", "ps"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error("Docker is not running")
                return False

            # Start monitoring stack
            result = subprocess.run(
                ["docker-compose", "-f", str(self.docker_compose_file), "up", "-d"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("✅ Monitoring services started")

                # Wait for services to be ready
                await asyncio.sleep(30)

                # Health check
                health_status = await self.check_health()
                healthy_services = sum(health_status.values())
                total_services = len(health_status)

                logger.info(f"Monitoring health: {healthy_services}/{total_services} services healthy")

                return healthy_services == total_services
            else:
                logger.error(f"Failed to start monitoring services: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to start monitoring services: {e}")
            return False

    async def stop_services(self):
        """Stop monitoring services"""
        logger.info("Stopping monitoring services...")

        try:
            result = subprocess.run(
                ["docker-compose", "-f", str(self.docker_compose_file), "down"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("✅ Monitoring services stopped")
            else:
                logger.error(f"Failed to stop monitoring services: {result.stderr}")

        except Exception as e:
            logger.error(f"Failed to stop monitoring services: {e}")


async def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(
        description="PsychSync Production Monitoring Setup"
    )
    parser.add_argument("--setup-all", action="store_true", help="Set up complete monitoring stack")
    parser.add_argument("--check-health", action="store_true", help="Check monitoring system health")
    parser.add_argument("--alerts-test", action="store_true", help="Test alerting system")
    parser.add_argument("--start", action="store_true", help="Start monitoring services")
    parser.add_argument("--stop", action="store_true", help="Stop monitoring services")

    args = parser.parse_args()

    setup = ProductionMonitoringSetup()

    try:
        if args.setup_all:
            await setup.setup_all()
        elif args.check_health:
            health_status = await setup.check_health()
            print(f"Health Status: {health_status}")
        elif args.alerts_test:
            test_result = await setup.test_alerts()
            print(f"Alert Test Result: {'PASSED' if test_result else 'FAILED'}")
        elif args.start:
            start_result = await setup.start_services()
            print(f"Services Started: {'SUCCESS' if start_result else 'FAILED'}")
        elif args.stop:
            await setup.stop_services()
            print("Services stopped")
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    asyncio.run(main())
