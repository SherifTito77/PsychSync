#!/usr/bin/env python3
"""
Production Deployment Script

This script executes production deployments using the deployment automation system.
It supports blue-green and canary deployment strategies with comprehensive
health checking and automatic rollback capabilities.

Usage:
    python scripts/deploy_production.py --app psychsync-api --version v1.2.3 --strategy blue-green
    python scripts/deploy_production.py --config deployment/production_deployment_config.yaml --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Add app to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.deployment_automation import (
    ProductionDeploymentManager,
    DeploymentConfig,
    DeploymentStrategy,
    execute_production_deployment
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'/var/log/deployment/production_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)

class ProductionDeploymentCLI:
    """Command-line interface for production deployment"""

    def __init__(self):
        self.deployment_manager = None
        self.config = None
        self.dry_run = False

    def load_config(self, config_path: str):
        """Load deployment configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded deployment configuration from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def validate_environment(self):
        """Validate production environment"""
        required_env_vars = [
            'ENVIRONMENT',
            'DB_HOST',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'SLACK_WEBHOOK_URL'
        ]

        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            sys.exit(1)

        if os.getenv('ENVIRONMENT') != 'production':
            logger.warning("Not running in production environment!")

    def create_deployment_config(
        self,
        app_name: str,
        version: str,
        strategy: str,
        **kwargs
    ) -> DeploymentConfig:
        """Create deployment configuration from CLI args and config file"""
        if not self.config:
            raise ValueError("Configuration not loaded")

        app_config = self.config['applications'].get(app_name)
        if not app_config:
            raise ValueError(f"Application '{app_name}' not found in configuration")

        # Get environment config
        environment = kwargs.get('environment', 'production')
        env_config = self.config['environments'].get(environment, {})

        # Create health checks
        health_checks = []
        for hc_config in app_config.get('health_checks', []):
            from app.core.deployment_automation import HealthCheck
            health_checks.append(HealthCheck(
                name=hc_config['name'],
                endpoint=hc_config['endpoint'],
                method=hc_config.get('method', 'GET'),
                expected_status=hc_config.get('expected_status', 200),
                timeout=hc_config.get('timeout', 30.0),
                retries=hc_config.get('retries', 3),
                retry_delay=hc_config.get('retry_delay', 10.0),
                headers=hc_config.get('headers')
            ))

        # Create deployment config
        config = DeploymentConfig(
            name=app_config['name'],
            version=version,
            environment=environment,
            strategy=DeploymentStrategy(strategy),
            docker_image=f"{app_config['repository']}:{version}",
            port=app_config.get('port', 8000),
            replicas=kwargs.get('replicas', app_config.get('replicas', 3)),
            health_checks=health_checks,
            rollback_threshold=kwargs.get('rollback_threshold', 5.0),
            canary_percentage=kwargs.get('canary_percentage', 10.0),
            zero_downtime=kwargs.get('zero_downtime', True),
            backup_before_deploy=env_config.get('database', {}).get('backup_required', True),
            migrate_database=env_config.get('database', {}).get('migrate', False),
            timeout=kwargs.get('timeout', self.config['global']['default_timeout'])
        )

        return config

    async def execute_deployment(self, config: DeploymentConfig) -> dict:
        """Execute deployment with monitoring"""
        if self.dry_run:
            logger.info("DRY RUN: Would execute deployment with the following configuration:")
            logger.info(f"  Name: {config.name}")
            logger.info(f"  Version: {config.version}")
            logger.info(f"  Strategy: {config.strategy.value}")
            logger.info(f"  Environment: {config.environment}")
            logger.info(f"  Docker Image: {config.docker_image}")
            logger.info(f"  Replicas: {config.replicas}")
            logger.info(f"  Health Checks: {len(config.health_checks)}")
            return {"success": True, "dry_run": True}

        # Initialize deployment manager
        self.deployment_manager = ProductionDeploymentManager()

        # Pre-deployment checks
        await self._pre_deployment_checks(config)

        # Execute deployment
        logger.info(f"Starting deployment of {config.name} v{config.version}")
        start_time = datetime.utcnow()

        try:
            metrics = await self.deployment_manager.execute_deployment(config)

            duration = (metrics.end_time - metrics.start_time).total_seconds() if metrics.end_time else None

            result = {
                "success": metrics.status.value == "completed",
                "deployment_id": metrics.deployment_id,
                "status": metrics.status.value,
                "duration": duration,
                "version": config.version,
                "strategy": config.strategy.value,
                "error_rate": metrics.error_rate,
                "response_time": metrics.response_time,
                "health_check_results": {
                    name: status.value
                    for name, status in metrics.health_check_results.items()
                },
                "logs": metrics.logs,
                "rollback_reason": metrics.rollback_reason
            }

            # Post-deployment actions
            await self._post_deployment_actions(config, result)

            return result

        except Exception as e:
            logger.error(f"Deployment execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": (datetime.utcnow() - start_time).total_seconds()
            }

    async def _pre_deployment_checks(self, config: DeploymentConfig):
        """Execute pre-deployment validation checks"""
        logger.info("Executing pre-deployment checks...")

        # Validate environment
        self.validate_environment()

        # Check Docker availability
        try:
            import docker
            client = docker.from_env()
            client.ping()
            logger.info("✅ Docker connection verified")
        except Exception as e:
            raise RuntimeError(f"Docker not available: {e}")

        # Check database connectivity
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host=os.getenv('DB_HOST'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            await conn.execute('SELECT 1')
            await conn.close()
            logger.info("✅ Database connectivity verified")
        except Exception as e:
            raise RuntimeError(f"Database connectivity failed: {e}")

        # Check available disk space
        import shutil
        total, used, free = shutil.disk_usage('/')
        free_gb = free // (1024**3)
        if free_gb < 5:  # Require at least 5GB free space
            raise RuntimeError(f"Insufficient disk space: {free_gb}GB available")

        logger.info(f"✅ Pre-deployment checks completed (Free disk space: {free_gb}GB)")

    async def _post_deployment_actions(self, config: DeploymentConfig, result: dict):
        """Execute post-deployment actions"""
        deployment_id = result.get("deployment_id", "unknown")

        # Send notifications
        await self._send_deployment_notification(config, result)

        # Log deployment result
        await self._log_deployment_result(config, result)

        if result["success"]:
            logger.info(f"✅ Deployment {deployment_id} completed successfully in {result['duration']:.2f}s")
        else:
            logger.error(f"❌ Deployment {deployment_id} failed: {result.get('error', 'Unknown error')}")

    async def _send_deployment_notification(self, config: DeploymentConfig, result: dict):
        """Send deployment notification via Slack"""
        try:
            slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
            if not slack_webhook:
                logger.warning("SLACK_WEBHOOK_URL not configured")
                return

            import httpx

            # Determine message template
            if result["success"]:
                title = f"✅ Deployment Completed: {config.name} v{config.version}"
                color = "good"
                message = (
                    f"Deployment {result.get('deployment_id', 'unknown')} completed successfully!\n\n"
                    f"• Duration: {result['duration']:.2f} seconds\n"
                    f"• Strategy: {config.strategy.value}\n"
                    f"• Response Time: {result['response_time']:.2f}s\n"
                    f"• Error Rate: {result['error_rate']:.2f}%"
                )
            else:
                title = f"❌ Deployment Failed: {config.name} v{config.version}"
                color = "danger"
                message = (
                    f"Deployment {result.get('deployment_id', 'unknown')} failed.\n\n"
                    f"• Error: {result.get('error', 'Unknown error')}\n"
                    f"• Duration: {result.get('duration', 'N/A')} seconds\n"
                    f"• Rollback: {'Yes' if result.get('rollback_reason') else 'No'}"
                )

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": title,
                        "text": message,
                        "footer": "Production Deployment",
                        "ts": int(datetime.utcnow().timestamp())
                    }
                ]
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(slack_webhook, json=payload)
                if response.status_code == 200:
                    logger.info("✅ Slack notification sent")
                else:
                    logger.warning(f"Failed to send Slack notification: {response.status_code}")

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def _log_deployment_result(self, config: DeploymentConfig, result: dict):
        """Log deployment result to file"""
        try:
            log_dir = Path("/var/log/deployment")
            log_dir.mkdir(exist_ok=True)

            log_file = log_dir / f"deployment_history_{datetime.now().strftime('%Y%m')}.jsonl"

            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "app_name": config.name,
                "version": config.version,
                "environment": config.environment,
                "strategy": config.strategy.value,
                "deployment_id": result.get("deployment_id"),
                "success": result["success"],
                "duration": result.get("duration"),
                "error": result.get("error"),
                "rollback_reason": result.get("rollback_reason")
            }

            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            logger.error(f"Failed to log deployment result: {e}")

async def main():
    """Main deployment CLI entry point"""
    parser = argparse.ArgumentParser(description="Production Deployment CLI")
    parser.add_argument("--app", help="Application name to deploy")
    parser.add_argument("--version", required=True, help="Version to deploy")
    parser.add_argument("--strategy", default="blue_green",
                       choices=["blue_green", "canary", "rolling", "recreate"],
                       help="Deployment strategy")
    parser.add_argument("--config", default="deployment/production_deployment_config.yaml",
                       help="Deployment configuration file")
    parser.add_argument("--environment", default="production",
                       help="Target environment")
    parser.add_argument("--dry-run", action="store_true",
                       help="Perform dry run without actual deployment")
    parser.add_argument("--replicas", type=int, help="Number of replicas")
    parser.add_argument("--canary-percentage", type=float, default=10.0,
                       help="Initial canary traffic percentage")
    parser.add_argument("--timeout", type=float, help="Deployment timeout in seconds")

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Initialize CLI
    cli = ProductionDeploymentCLI()
    cli.dry_run = args.dry_run

    # Load configuration
    cli.load_config(args.config)

    # Determine application name
    app_name = args.app
    if not app_name and len(cli.config['applications']) == 1:
        app_name = list(cli.config['applications'].keys())[0]

    if not app_name:
        logger.error("Application name required when multiple apps are configured")
        sys.exit(1)

    # Create deployment configuration
    config = cli.create_deployment_config(
        app_name=app_name,
        version=args.version,
        strategy=args.strategy,
        environment=args.environment,
        replicas=args.replicas,
        canary_percentage=args.canary_percentage,
        timeout=args.timeout
    )

    # Execute deployment
    result = await cli.execute_deployment(config)

    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    asyncio.run(main())
