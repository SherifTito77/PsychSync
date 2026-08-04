#!/usr/bin/env python3
"""
PsychSync Monitoring Stack Setup Script
Automated installation and configuration of the complete monitoring stack
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MonitoringStackInstaller:
    """Complete monitoring stack installation and configuration"""

    def __init__(self, base_dir: str = "/Users/sheriftito/Downloads/psychsync"):
        self.base_dir = Path(base_dir)
        self.monitoring_dir = self.base_dir / "monitoring"
        self.docker_compose_file = self.base_dir / "docker-compose.monitoring.yml"
        self.env_file = self.base_dir / ".env.monitoring"

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        logger.info("Checking prerequisites...")

        # Check Docker
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            logger.info("✓ Docker is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Docker is not installed or not in PATH")
            return False

        # Check Docker Compose
        try:
            subprocess.run(
                ["docker-compose", "--version"], check=True, capture_output=True
            )
            logger.info("✓ Docker Compose is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ Docker Compose is not installed or not in PATH")
            return False

        # Check Python requirements for custom components
        required_packages = [
            "aiohttp",
            "prometheus_client",
            "psycopg2",
            "redis",
            "stripe",
        ]
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✓ Python package {package} is available")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"⚠️  Python package {package} is missing")

        if missing_packages:
            logger.info(
                f"Installing missing Python packages: {', '.join(missing_packages)}"
            )
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + missing_packages,
                    check=True,
                )
                logger.info("✓ Python packages installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install Python packages: {e}")
                return False

        return True

    def create_directories(self):
        """Create necessary directory structure"""
        logger.info("Creating directory structure...")

        directories = [
            "monitoring/prometheus",
            "monitoring/grafana/dashboards",
            "monitoring/grafana/provisioning/datasources",
            "monitoring/grafana/provisioning/dashboards",
            "monitoring/alertmanager",
            "monitoring/loki",
            "monitoring/promtail",
            "monitoring/exporters",
            "monitoring/synthetic",
            "monitoring/sla",
            "monitoring/datadog/conf.d",
            "logs/psychsync/api",
            "logs/psychsync/frontend",
            "logs/postgresql",
            "logs/nginx",
        ]

        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Created directory: {directory}")

    def create_environment_file(self, force: bool = False):
        """Create environment configuration file"""
        env_file_path = self.base_dir / ".env.monitoring"

        if env_file_path.exists() and not force:
            logger.info("✓ Environment file already exists (use --force to recreate)")
            return

        logger.info("Creating environment configuration file...")

        env_content = """# PsychSync Monitoring Environment Configuration
# Generated on: {timestamp}

# Datadog Configuration
DD_API_KEY=your_datadog_api_key_here
DD_SITE=datadoghq.com
DD_ENV=production
DD_SERVICE=psychsync-api
DD_VERSION=1.0.0
DD_LOGS_ENABLED=true
DD_PROFILING_ENABLED=true
DD_TRACE_SAMPLE_RATE=0.1
DD_LOGS_INJECTION=true

# Sentry Configuration
SENTRY_DSN=your_sentry_dsn_here
SENTRY_SECRET_KEY=your_sentry_secret_key_here
SENTRY_DB_PASSWORD=secure_sentry_db_password
SENTRY_EMAIL=alerts@psychsync.com

# Grafana Configuration
GRAFANA_PASSWORD=secure_grafana_password
GRAFANA_DOMAIN=monitoring.psychsync.com

# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=psychsync

# SMTP Configuration (for Sentry notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password

# Stripe Configuration (for business metrics)
STRIPE_API_KEY=sk_test_your_stripe_test_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Notification Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
PAGERDUTY_INTEGRATION_KEY=your_pagerduty_integration_key

# Performance and Scaling
METRICS_UPDATE_INTERVAL=60
SYNTHETIC_TEST_INTERVAL=300
SLA_MONITORING_INTERVAL=300

# Storage and Retention
PROMETHEUS_RETENTION=15d
PROMETHEUS_SIZE_LIMIT=20GB
LOG_RETENTION_DAYS=30
SENTRY_EVENT_RETENTION=90d

# Health Check URLs
API_HEALTH_URL=https://api.psychsync.com/api/v1/health
FRONTEND_URL=https://app.psychsync.com
""".format(
            timestamp=datetime.now().isoformat()
        )

        env_file_path.write_text(env_content)
        logger.info(f"✓ Created environment file: {env_file_path}")

        # Set file permissions
        env_file_path.chmod(0o600)
        logger.info("✓ Set secure permissions on environment file")

    def install_prometheus_configuration(self):
        """Install and configure Prometheus"""
        logger.info("Installing Prometheus configuration...")

        prometheus_config = self.monitoring_dir / "prometheus" / "prometheus.yml"
        alert_rules = self.monitoring_dir / "prometheus" / "alert_rules.yml"
        recording_rules = self.monitoring_dir / "prometheus" / "recording_rules.yml"

        # These files should already exist from previous steps
        config_files = [
            (prometheus_config, "prometheus.yml"),
            (alert_rules, "alert_rules.yml"),
            (recording_rules, "recording_rules.yml"),
        ]

        for config_file, name in config_files:
            if config_file.exists():
                logger.info(f"✓ {name} is already configured")
            else:
                logger.warning(f"⚠️  {name} is missing - please ensure it's created")

    def install_grafana_configuration(self):
        """Install and configure Grafana"""
        logger.info("Installing Grafana configuration...")

        # Grafana datasources configuration
        datasources_dir = (
            self.monitoring_dir / "grafana" / "provisioning" / "datasources"
        )
        datasources_file = datasources_dir / "datasources.yml"

        if not datasources_file.exists():
            datasources_config = """apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
    jsonData:
      maxLines: 1000
"""
            datasources_file.write_text(datasources_config)
            logger.info("✓ Created Grafana datasources configuration")

        # Grafana dashboard provisioning
        dashboards_dir = self.monitoring_dir / "grafana" / "provisioning" / "dashboards"
        dashboards_file = dashboards_dir / "dashboards.yml"

        if not dashboards_file.exists():
            dashboards_config = """apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
"""
            dashboards_file.write_text(dashboards_config)
            logger.info("✓ Created Grafana dashboard provisioning")

    def install_sentry_configuration(self):
        """Install and configure Sentry"""
        logger.info("Installing Sentry configuration...")

        sentry_config = {
            "integrations": {
                "datadog": {
                    "enabled": True,
                    "api_key": os.getenv("DD_API_KEY", ""),
                    "site": os.getenv("DD_SITE", "datadoghq.com"),
                }
            },
            "notifications": {
                "slack": {
                    "enabled": True,
                    "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
                }
            },
            "retention": {"days": 90, "performance": {"days": 30}},
        }

        sentry_config_file = self.monitoring_dir / "sentry" / "config.json"
        sentry_config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(sentry_config_file, "w") as f:
            json.dump(sentry_config, f, indent=2)

        logger.info("✓ Created Sentry configuration")

    def create_startup_scripts(self):
        """Create startup and management scripts"""
        logger.info("Creating startup scripts...")

        scripts_dir = self.base_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        # Monitoring stack startup script
        startup_script = scripts_dir / "start_monitoring.sh"
        startup_content = """#!/bin/bash
# PsychSync Monitoring Stack Startup Script

set -e

echo "🚀 Starting PsychSync Monitoring Stack..."

# Check if environment file exists
if [ ! -f ".env.monitoring" ]; then
    echo "❌ Environment file .env.monitoring not found!"
    echo "Please create it using: python scripts/setup_monitoring_stack.py --create-env"
    exit 1
fi

# Load environment variables
source .env.monitoring

echo "📋 Environment variables loaded"

# Create network if it doesn't exist
docker network create psychsync-network 2>/dev/null || true

# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
services=("prometheus:9090" "grafana:3001" "alertmanager:9093")

for service in "${services[@]}"; do
    service_name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)

    if curl -f http://localhost:$port > /dev/null 2>&1; then
        echo "✅ $service_name is healthy"
    else
        echo "❌ $service_name is not responding"
    fi
done

echo "🎉 Monitoring stack started successfully!"
echo ""
echo "📊 Access your monitoring dashboards:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3001 (admin/$GRAFANA_PASSWORD)"
echo "   Alertmanager: http://localhost:9093"
echo "   Sentry: http://localhost:9000"
echo ""
echo "📈 Custom Business Metrics: http://localhost:8081/metrics"
echo "🔍 Synthetic Monitoring: http://localhost:8082/metrics"
echo "📊 SLA Monitoring: http://localhost:8083/metrics"
"""
        startup_script.write_text(startup_content)
        startup_script.chmod(0o755)
        logger.info("✓ Created startup script")

        # Stop script
        stop_script = scripts_dir / "stop_monitoring.sh"
        stop_content = """#!/bin/bash
# PsychSync Monitoring Stack Stop Script

set -e

echo "🛑 Stopping PsychSync Monitoring Stack..."

docker-compose -f docker-compose.monitoring.yml down

echo "✅ Monitoring stack stopped successfully!"
"""
        stop_script.write_text(stop_content)
        stop_script.chmod(0o755)
        logger.info("✓ Created stop script")

        # Health check script
        health_script = scripts_dir / "health_check.sh"
        health_content = """#!/bin/bash
# PsychSync Monitoring Stack Health Check

set -e

echo "🔍 Checking PsychSync Monitoring Stack Health..."

services=(
    "prometheus:9090:/api/v1/targets"
    "grafana:3001:/api/health"
    "alertmanager:9093:/api/v1/status"
    "sentry:9000:/_health/"
)

all_healthy=true

for service in "${services[@]}"; do
    IFS=':' read -r name port path <<< "$service"

    if curl -f "http://localhost:$port$path" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "❌ $name is unhealthy"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo "🎉 All services are healthy!"
    exit 0
else
    echo "❌ Some services are unhealthy!"
    exit 1
fi
"""
        health_script.write_text(health_content)
        health_script.chmod(0o755)
        logger.info("✓ Created health check script")

    def create_systemd_service(self):
        """Create systemd service for automatic startup"""
        logger.info("Creating systemd service...")

        service_content = """[Unit]
Description=PsychSync Monitoring Stack
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory={base_dir}
ExecStart=/usr/bin/docker-compose -f docker-compose.monitoring.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.monitoring.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
""".format(
            base_dir=str(self.base_dir)
        )

        service_file = Path("/tmp/psychsync-monitoring.service")
        service_file.write_text(service_content)

        logger.info(f"✅ Created systemd service file: {service_file}")
        logger.info("To install the service, run:")
        logger.info(f"  sudo cp {service_file} /etc/systemd/system/")
        logger.info("  sudo systemctl enable psychsync-monitoring.service")
        logger.info("  sudo systemctl start psychsync-monitoring.service")

    def compile_python_components(self):
        """Compile and install Python monitoring components"""
        logger.info("Compiling Python monitoring components...")

        python_components = [
            (
                "business_metrics_exporter",
                "monitoring/exporters/business_metrics_exporter.py",
            ),
            ("synthetic_monitoring", "monitoring/synthetic/synthetic_monitoring.py"),
            ("performance_baseline", "monitoring/sla/performance_baseline.py"),
        ]

        for component_name, component_path in python_components:
            full_path = self.base_dir / component_path
            if full_path.exists():
                logger.info(f"✓ {component_name} source code is available")

                # Create compiled version
                compiled_path = full_path.with_suffix(".pyc")
                try:
                    import py_compile

                    py_compile.compile(str(full_path), str(compiled_path))
                    logger.info(f"✓ Compiled {component_name}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not compile {component_name}: {e}")
            else:
                logger.warning(
                    f"⚠️  {component_name} source code not found at {full_path}"
                )

    def setup_dependencies(self):
        """Install and setup external dependencies"""
        logger.info("Setting up external dependencies...")

        # Create Python requirements file
        requirements_content = """# PsychSync Monitoring Stack Requirements
aiohttp>=3.8.0
prometheus-client>=0.15.0
psycopg2-binary>=2.9.0
redis>=4.5.0
stripe>=5.0.0
structlog>=22.1.0
python-json-logger>=2.0.0
python-dateutil>=2.8.0
pandas>=1.5.0
numpy>=1.21.0
"""

        requirements_file = self.base_dir / "monitoring-requirements.txt"
        requirements_file.write_text(requirements_content)

        logger.info("✓ Created monitoring requirements file")

        # Install Python dependencies
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True,
            )
            logger.info("✓ Installed Python dependencies")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install Python dependencies: {e}")
            return False

        return True

    def validate_installation(self) -> bool:
        """Validate the installation"""
        logger.info("Validating installation...")

        validation_checks = [
            ("Environment file", self.env_file),
            ("Docker Compose file", self.docker_compose_file),
            (
                "Prometheus config",
                self.monitoring_dir / "prometheus" / "prometheus.yml",
            ),
            (
                "Grafana config",
                self.monitoring_dir
                / "grafana"
                / "provisioning"
                / "datasources"
                / "datasources.yml",
            ),
            (
                "Business metrics exporter",
                self.monitoring_dir / "exporters" / "business_metrics_exporter.py",
            ),
            (
                "Synthetic monitoring",
                self.monitoring_dir / "synthetic" / "synthetic_monitoring.py",
            ),
            ("SLA monitoring", self.monitoring_dir / "sla" / "performance_baseline.py"),
        ]

        all_valid = True
        for check_name, file_path in validation_checks:
            if file_path.exists():
                logger.info(f"✓ {check_name} is present")
            else:
                logger.error(f"❌ {check_name} is missing: {file_path}")
                all_valid = False

        return all_valid

    def run_quick_setup(self):
        """Run complete quick setup"""
        logger.info("🚀 Starting PsychSync Monitoring Stack Setup")
        logger.info("=" * 60)

        if not self.check_prerequisites():
            logger.error("❌ Prerequisites check failed!")
            return False

        self.create_directories()
        self.create_environment_file()
        self.install_prometheus_configuration()
        self.install_grafana_configuration()
        self.install_sentry_configuration()
        self.create_startup_scripts()
        self.create_systemd_service()
        self.compile_python_components()

        if not self.setup_dependencies():
            logger.error("❌ Dependencies setup failed!")
            return False

        if not self.validate_installation():
            logger.error("❌ Installation validation failed!")
            return False

        logger.info("=" * 60)
        logger.info("🎉 PsychSync Monitoring Stack Setup Complete!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Edit .env.monitoring with your API keys and configuration")
        logger.info("2. Run: ./scripts/start_monitoring.sh")
        logger.info("3. Access dashboards at the URLs provided in startup output")
        logger.info("")
        logger.info("For detailed setup instructions, see:")
        logger.info("📖 docs/MONITORING_SETUP_GUIDE.md")

        return True

    def create_deployment_package(self):
        """Create a complete deployment package"""
        logger.info("Creating deployment package...")

        package_dir = self.base_dir / "monitoring-deployment-package"
        package_dir.mkdir(exist_ok=True)

        # Copy essential files
        files_to_copy = [
            ("docker-compose.monitoring.yml", "docker-compose.yml"),
            (".env.monitoring.example", ".env.example"),
            ("scripts/start_monitoring.sh", "start_monitoring.sh"),
            ("scripts/stop_monitoring.sh", "stop_monitoring.sh"),
            ("scripts/health_check.sh", "health_check.sh"),
            ("monitoring-requirements.txt", "requirements.txt"),
        ]

        for src_file, dest_file in files_to_copy:
            src_path = self.base_dir / src_file
            dest_path = package_dir / dest_file

            if src_path.exists():
                if dest_path.name.endswith((".sh", ".yml", ".conf")):
                    shutil.copy2(src_path, dest_path)
                    dest_path.chmod(0o755 if dest_path.suffix == ".sh" else 0o644)
                else:
                    shutil.copy2(src_path, dest_path)
                logger.info(f"✓ Copied {src_file} to package")
            else:
                logger.warning(f"⚠️  Source file not found: {src_file}")

        # Copy monitoring directories
        monitoring_dirs = ["prometheus", "grafana", "alertmanager", "loki", "promtail"]
        for dir_name in monitoring_dirs:
            src_dir = self.monitoring_dir / dir_name
            dest_dir = package_dir / "config" / dir_name

            if src_dir.exists():
                shutil.copytree(src_dir, dest_dir, dirs_exist_ok=True)
                logger.info(f"✓ Copied {dir_name} configuration")

        # Create README
        readme_content = """# PsychSync Monitoring Stack Deployment Package

This package contains all necessary files to deploy the PsychSync monitoring stack.

## Quick Deployment

1. Extract this package to your server
2. Copy .env.example to .env and configure your settings
3. Run: `./start_monitoring.sh`
4. Access dashboards using the URLs provided

## Files Included

- `docker-compose.yml`: Main orchestration file
- `config/`: All configuration files
- `requirements.txt`: Python dependencies
- `start_monitoring.sh`: Startup script
- `stop_monitoring.sh`: Shutdown script
- `health_check.sh`: Health validation

## Support

For detailed instructions, see the complete documentation at:
`docs/MONITORING_SETUP_GUIDE.md`
"""

        readme_file = package_dir / "README.md"
        readme_file.write_text(readme_content)

        logger.info(f"✓ Created deployment package at {package_dir}")

        # Create tarball
        import tarfile

        tarball_path = self.base_dir / "psychsync-monitoring-package.tar.gz"

        with tarfile.open(tarball_path, "w:gz") as tar:
            tar.add(package_dir, arcname="psychsync-monitoring")

        logger.info(f"✓ Created deployment tarball: {tarball_path}")


def main():
    parser = argparse.ArgumentParser(description="PsychSync Monitoring Stack Setup")
    parser.add_argument(
        "--base-dir",
        default="/Users/sheriftito/Downloads/psychsync",
        help="Base directory for PsychSync",
    )
    parser.add_argument(
        "--create-env", action="store_true", help="Create new environment file"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing installation",
    )
    parser.add_argument(
        "--package", action="store_true", help="Create deployment package"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force overwrite existing files"
    )

    args = parser.parse_args()

    installer = MonitoringStackInstaller(args.base_dir)

    if args.package:
        installer.create_deployment_package()
        return

    if args.validate_only:
        success = installer.validate_installation()
        sys.exit(0 if success else 1)

    if args.create_env:
        installer.create_environment_file(force=args.force)
        return

    success = installer.run_quick_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
