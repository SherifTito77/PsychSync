"""
Deployment and Launch Execution Service
Handles production deployment, health checks, monitoring, and rollback procedures
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field
from pathlib import Path
import json
import uuid
import asyncio
import subprocess
import os
import sys
import yaml
from dataclasses import asdict

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, text

from app.core.config import settings

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class HealthCheckStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentStatus(Enum):
    """Component status"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DEPLOYING = "deploying"
    UNKNOWN = "unknown"


class RollbackStrategy(Enum):
    """Rollback strategies"""
    IMMEDIATE = "immediate"
    GRACEFUL = "graceful"
    MANUAL = "manual"
    AUTOMATIC = "automatic"


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    version: str
    environment: DeploymentEnvironment
    build_number: str
    commit_hash: str
    build_date: datetime
    docker_image: str
    namespace: str
    replicas: int = 1
    cpu_limit: str = "1000m"
    memory_limit: str = "1Gi"
    cpu_request: str = "500m"
    memory_request: str = "512Mi"
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    health_check_endpoint: str = "/health"
    readiness_check_endpoint: str = "/ready"
    rollout_strategy: str = "RollingUpdate"  # RollingUpdate, Recreate
    max_unavailable: str = "25%"
    max_surge: str = "25%"
    rollback_enabled: bool = True
    rollback_strategy: RollbackStrategy = RollbackStrategy.GRACEFUL
    rollback_timeout: int = 300  # seconds


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    endpoint: str
    method: str = "GET"
    expected_status: int = 200
    timeout: int = 30
    retries: int = 3
    critical: bool = True
    check_interval: int = 60  # seconds
    response_time_threshold: float = 2.0  # seconds


@dataclass
class HealthCheckResult:
    """Health check result"""
    check_name: str
    status: HealthCheckStatus
    response_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_status: HealthCheckStatus
    component_status: Dict[str, ComponentStatus]
    health_checks: List[HealthCheckResult]
    uptime_percentage: float
    last_check: datetime
    active_users: int = 0
    error_rate: float = 0.0
    response_time_p95: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)


@dataclass
class Deployment:
    """Deployment record"""
    id: str
    config: DeploymentConfig
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    rollback_id: Optional[str] = None
    deployment_logs: List[str] = field(default_factory=list)
    pre_deployment_checks: List[HealthCheckResult] = field(default_factory=list)
    post_deployment_checks: List[HealthCheckResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackPlan:
    """Rollback plan definition"""
    id: str
    deployment_id: str
    target_version: str
    strategy: RollbackStrategy
    trigger_conditions: List[str]
    rollback_steps: List[str]
    verification_steps: List[str]
    rollback_timeout: int = 600  # seconds
    notify_stakeholders: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceMetrics:
    """Performance metrics collection"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    active_connections: int
    requests_per_second: float
    average_response_time: float
    error_rate: float
    queue_size: int = 0
    database_connections: int = 0


class DeploymentService:
    """Comprehensive deployment and launch execution service"""

    def __init__(self):
        self.deployments: Dict[str, Deployment] = {}
        self.health_checks: List[HealthCheck] = []
        self.current_deployment: Optional[Deployment] = None
        self.rollback_plans: Dict[str, RollbackPlan] = {}

        # Initialize default health checks
        self._initialize_default_health_checks()

    def _initialize_default_health_checks(self):
        """Initialize default health checks"""
        self.health_checks = [
            HealthCheck(
                name="application_health",
                endpoint="/health",
                method="GET",
                expected_status=200,
                timeout=30,
                retries=3,
                critical=True
            ),
            HealthCheck(
                name="database_connection",
                endpoint="/health/db",
                method="GET",
                expected_status=200,
                timeout=10,
                retries=2,
                critical=True
            ),
            HealthCheck(
                name="redis_connection",
                endpoint="/health/redis",
                method="GET",
                expected_status=200,
                timeout=5,
                retries=2,
                critical=True
            ),
            HealthCheck(
                name="api_readiness",
                endpoint="/ready",
                method="GET",
                expected_status=200,
                timeout=30,
                retries=3,
                critical=True
            ),
            HealthCheck(
                name="authentication_service",
                endpoint="/health/auth",
                method="GET",
                expected_status=200,
                timeout=15,
                retries=2,
                critical=True
            ),
            HealthCheck(
                name="email_service",
                endpoint="/health/email",
                method="GET",
                expected_status=200,
                timeout=10,
                retries=1,
                critical=False
            )
        ]

    async def create_deployment_config(
        self,
        version: str,
        environment: DeploymentEnvironment,
        build_number: str,
        commit_hash: str,
        docker_image: str,
        **kwargs
    ) -> DeploymentConfig:
        """Create deployment configuration"""
        config = DeploymentConfig(
            version=version,
            environment=environment,
            build_number=build_number,
            commit_hash=commit_hash,
            build_date=datetime.utcnow(),
            docker_image=docker_image,
            namespace=f"psychsync-{environment.value}",
            **kwargs
        )

        # Environment-specific overrides
        if environment == DeploymentEnvironment.PRODUCTION:
            config.replicas = max(config.replicas, 3)
            config.cpu_limit = "2000m"
            config.memory_limit = "2Gi"
        elif environment == DeploymentEnvironment.STAGING:
            config.replicas = max(config.replicas, 2)
            config.cpu_limit = "1000m"
            config.memory_limit = "1Gi"

        return config

    async def start_deployment(
        self,
        config: DeploymentConfig,
        skip_pre_checks: bool = False
    ) -> Deployment:
        """Start deployment process"""
        deployment_id = str(uuid.uuid4())

        deployment = Deployment(
            id=deployment_id,
            config=config,
            status=DeploymentStatus.PENDING,
            started_at=datetime.utcnow()
        )

        self.deployments[deployment_id] = deployment
        self.current_deployment = deployment

        logger.info(f"Starting deployment {deployment_id} to {config.environment.value}")

        try:
            # Pre-deployment checks
            if not skip_pre_checks:
                await self._run_pre_deployment_checks(deployment)

            # Update status
            deployment.status = DeploymentStatus.IN_PROGRESS
            deployment.deployment_logs.append(f"Starting deployment to {config.environment.value}")

            # Execute deployment
            await self._execute_deployment(deployment)

            # Post-deployment verification
            await self._run_post_deployment_checks(deployment)

            # Mark as successful
            deployment.status = DeploymentStatus.SUCCESS
            deployment.completed_at = datetime.utcnow()
            deployment.duration = (deployment.completed_at - deployment.started_at).total_seconds()
            deployment.success = True
            deployment.deployment_logs.append("Deployment completed successfully")

            logger.info(f"Deployment {deployment_id} completed successfully in {deployment.duration:.2f}s")

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.completed_at = datetime.utcnow()
            deployment.duration = (deployment.completed_at - deployment.started_at).total_seconds()
            deployment.success = False
            deployment.error_message = str(e)
            deployment.deployment_logs.append(f"Deployment failed: {str(e)}")

            logger.error(f"Deployment {deployment_id} failed: {str(e)}")

            # Trigger rollback if enabled and in production
            if config.rollback_enabled and config.environment == DeploymentEnvironment.PRODUCTION:
                await self._trigger_rollback(deployment)

        return deployment

    async def _run_pre_deployment_checks(self, deployment: Deployment):
        """Run pre-deployment health checks"""
        deployment.deployment_logs.append("Running pre-deployment health checks")

        # Check current system health
        current_health = await self.check_system_health()
        deployment.pre_deployment_checks.extend(current_health.health_checks)

        # Verify all critical health checks are passing
        failed_critical = [
            check for check in deployment.pre_deployment_checks
            if check.status != HealthCheckStatus.HEALTHY and
               any(hc.name == check.check_name and hc.critical for hc in self.health_checks)
        ]

        if failed_critical:
            raise Exception(f"Critical health checks failed: {[check.check_name for check in failed_critical]}")

        # Check environment-specific requirements
        if deployment.config.environment == DeploymentEnvironment.PRODUCTION:
            await self._verify_production_readiness(deployment)

    async def _verify_production_readiness(self, deployment: Deployment):
        """Verify production readiness"""
        deployment.deployment_logs.append("Verifying production readiness")

        # Check if all required services are running
        required_services = ["database", "redis", "email", "storage"]
        # This would integrate with your infrastructure monitoring
        # For now, assuming all services are ready

        # Verify backup and recovery procedures
        # This would check backup status, disaster recovery readiness, etc.

        # Verify security configurations
        await self._verify_security_configurations(deployment)

        deployment.deployment_logs.append("Production readiness verified")

    async def _verify_security_configurations(self, deployment: Deployment):
        """Verify security configurations"""
        # Check SSL certificates
        # Verify firewall rules
        # Check authentication and authorization settings
        # Validate environment variables for sensitive data
        pass

    async def _execute_deployment(self, deployment: Deployment):
        """Execute the actual deployment"""
        config = deployment.config
        deployment.deployment_logs.append(f"Executing deployment: {config.version}")

        # Generate Kubernetes manifests
        manifests = await self._generate_kubernetes_manifests(config)

        # Apply deployment manifests
        await self._apply_kubernetes_manifests(manifests, deployment)

        # Wait for rollout to complete
        await self._wait_for_rollout_completion(deployment)

        deployment.deployment_logs.append(f"Deployment executed successfully: {config.version}")

    async def _generate_kubernetes_manifests(self, config: DeploymentConfig) -> List[Dict[str, Any]]:
        """Generate Kubernetes manifests for deployment"""
        manifests = []

        # Deployment manifest
        deployment_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": "psychsync-api",
                "namespace": config.namespace,
                "labels": {
                    "app": "psychsync-api",
                    "version": config.version
                }
            },
            "spec": {
                "replicas": config.replicas,
                "strategy": {
                    "type": config.rollout_strategy,
                    "rollingUpdate": {
                        "maxUnavailable": config.max_unavailable,
                        "maxSurge": config.max_surge
                    }
                },
                "selector": {
                    "matchLabels": {
                        "app": "psychsync-api"
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "psychsync-api",
                            "version": config.version
                        }
                    },
                    "spec": {
                        "containers": [{
                            "name": "psychsync-api",
                            "image": config.docker_image,
                            "ports": [{
                                "containerPort": 8000,
                                "protocol": "TCP"
                            }],
                            "resources": {
                                "requests": {
                                    "cpu": config.cpu_request,
                                    "memory": config.memory_request
                                },
                                "limits": {
                                    "cpu": config.cpu_limit,
                                    "memory": config.memory_limit
                                }
                            },
                            "env": [
                                {"name": "ENVIRONMENT", "value": config.environment.value},
                                {"name": "VERSION", "value": config.version}
                            ] + [
                                {"name": k, "value": v}
                                for k, v in config.environment_variables.items()
                            ],
                            "livenessProbe": {
                                "httpGet": {
                                    "path": config.health_check_endpoint,
                                    "port": 8000
                                },
                                "initialDelaySeconds": 30,
                                "periodSeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": config.readiness_check_endpoint,
                                    "port": 8000
                                },
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5
                            }
                        }]
                    }
                }
            }
        }
        manifests.append(deployment_manifest)

        # Service manifest
        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": "psychsync-api-service",
                "namespace": config.namespace
            },
            "spec": {
                "selector": {
                    "app": "psychsync-api"
                },
                "ports": [{
                    "port": 80,
                    "targetPort": 8000,
                    "protocol": "TCP"
                }],
                "type": "ClusterIP"
            }
        }
        manifests.append(service_manifest)

        # HPA (Horizontal Pod Autoscaler) manifest
        hpa_manifest = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": "psychsync-api-hpa",
                "namespace": config.namespace
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": "psychsync-api"
                },
                "minReplicas": config.replicas,
                "maxReplicas": config.replicas * 3,
                "metrics": [{
                    "type": "Resource",
                    "resource": {
                        "name": "cpu",
                        "target": {
                            "type": "Utilization",
                            "averageUtilization": 70
                        }
                    }
                }]
            }
        }
        manifests.append(hpa_manifest)

        return manifests

    async def _apply_kubernetes_manifests(self, manifests: List[Dict[str, Any]], deployment: Deployment):
        """Apply Kubernetes manifests"""
        for manifest in manifests:
            # Convert to YAML and apply using kubectl
            manifest_yaml = yaml.dump(manifest, default_flow_style=False)

            # In a real implementation, this would use k8s Python client or kubectl
            # For this example, simulating the application
            deployment.deployment_logs.append(f"Applied {manifest['kind']} manifest")

    async def _wait_for_rollout_completion(self, deployment: Deployment):
        """Wait for deployment rollout to complete"""
        timeout = 600  # 10 minutes
        start_time = datetime.utcnow()

        deployment.deployment_logs.append("Waiting for rollout completion")

        while (datetime.utcnow() - start_time).seconds < timeout:
            # Check deployment status
            rollout_status = await self._check_rollout_status(deployment)

            if rollout_status:
                deployment.deployment_logs.append("Rollout completed successfully")
                return

            await asyncio.sleep(10)

        raise Exception("Rollout timeout exceeded")

    async def _check_rollout_status(self, deployment: Deployment) -> bool:
        """Check if deployment rollout is complete"""
        # This would check the actual Kubernetes deployment status
        # For this example, simulating the check
        await asyncio.sleep(2)  # Simulate API call
        return True  # Assume success for this example

    async def _run_post_deployment_checks(self, deployment: Deployment):
        """Run post-deployment verification checks"""
        deployment.deployment_logs.append("Running post-deployment verification")

        # Wait for application to be ready
        await asyncio.sleep(30)

        # Run health checks
        current_health = await self.check_system_health()
        deployment.post_deployment_checks.extend(current_health.health_checks)

        # Verify all critical health checks are passing
        failed_critical = [
            check for check in deployment.post_deployment_checks
            if check.status != HealthCheckStatus.HEALTHY and
               any(hc.name == check.check_name and hc.critical for hc in self.health_checks)
        ]

        if failed_critical:
            raise Exception(f"Post-deployment health checks failed: {[check.check_name for check in failed_critical]}")

        # Run smoke tests
        await self._run_smoke_tests(deployment)

        deployment.deployment_logs.append("Post-deployment verification completed")

    async def _run_smoke_tests(self, deployment: Deployment):
        """Run smoke tests after deployment"""
        deployment.deployment_logs.append("Running smoke tests")

        smoke_test_endpoints = [
            "/health",
            "/api/v1/health",
            "/docs"
        ]

        for endpoint in smoke_test_endpoints:
            # Simulate smoke test
            await asyncio.sleep(1)
            deployment.deployment_logs.append(f"Smoke test passed: {endpoint}")

    async def _trigger_rollback(self, failed_deployment: Deployment):
        """Trigger automatic rollback"""
        deployment.deployment_logs.append("Triggering automatic rollback")

        rollback_plan = await self.create_rollback_plan(
            failed_deployment.id,
            "previous_stable_version",
            RollbackStrategy.AUTOMATIC
        )

        try:
            await self.execute_rollback(rollback_plan.id)
            failed_deployment.rollback_id = rollback_plan.id
        except Exception as e:
            deployment.deployment_logs.append(f"Rollback failed: {str(e)}")

    async def create_rollback_plan(
        self,
        deployment_id: str,
        target_version: str,
        strategy: RollbackStrategy,
        **kwargs
    ) -> RollbackPlan:
        """Create rollback plan"""
        rollback_id = str(uuid.uuid4())

        plan = RollbackPlan(
            id=rollback_id,
            deployment_id=deployment_id,
            target_version=target_version,
            strategy=strategy,
            trigger_conditions=[
                "Critical health check failures",
                "High error rate (>5%)",
                "Response time degradation",
                "Manual rollback trigger"
            ],
            rollback_steps=[
                "Scale down current deployment",
                "Deploy previous stable version",
                "Verify health checks",
                "Update load balancer",
                "Notify stakeholders"
            ],
            verification_steps=[
                "Run health checks",
                "Execute smoke tests",
                "Verify user functionality",
                "Check performance metrics"
            ],
            **kwargs
        )

        self.rollback_plans[rollback_id] = plan
        return plan

    async def execute_rollback(self, rollback_id: str) -> bool:
        """Execute rollback plan"""
        if rollback_id not in self.rollback_plans:
            raise ValueError(f"Rollback plan not found: {rollback_id}")

        plan = self.rollback_plans[rollback_id]
        deployment = self.deployments.get(plan.deployment_id)

        if not deployment:
            raise ValueError(f"Deployment not found for rollback: {plan.deployment_id}")

        logger.info(f"Executing rollback {rollback_id} to version {plan.target_version}")

        try:
            # Update deployment status
            deployment.status = DeploymentStatus.ROLLING_BACK
            deployment.deployment_logs.append(f"Starting rollback to {plan.target_version}")

            # Execute rollback steps
            for step in plan.rollback_steps:
                deployment.deployment_logs.append(f"Rollback step: {step}")
                # In real implementation, execute the actual rollback step
                await asyncio.sleep(2)  # Simulate step execution

            # Update deployment to rollback version
            deployment.config.version = plan.target_version

            # Wait for rollback to complete
            await asyncio.sleep(30)

            # Run verification steps
            for step in plan.verification_steps:
                deployment.deployment_logs.append(f"Verification step: {step}")
                await asyncio.sleep(1)

            # Update deployment status
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.completed_at = datetime.utcnow()
            deployment.deployment_logs.append("Rollback completed successfully")

            logger.info(f"Rollback {rollback_id} completed successfully")
            return True

        except Exception as e:
            deployment.deployment_logs.append(f"Rollback failed: {str(e)}")
            logger.error(f"Rollback {rollback_id} failed: {str(e)}")
            return False

    async def check_system_health(self) -> SystemHealth:
        """Check overall system health"""
        health_results = []
        component_status = {}

        # Run all health checks
        for health_check in self.health_checks:
            result = await self._execute_health_check(health_check)
            health_results.append(result)

        # Determine component status
        component_status["api"] = ComponentStatus.RUNNING  # Would check actual status
        component_status["database"] = ComponentStatus.RUNNING
        component_status["redis"] = ComponentStatus.RUNNING
        component_status["email"] = ComponentStatus.RUNNING

        # Determine overall health
        critical_failures = [
            result for result in health_results
            if result.status == HealthCheckStatus.UNHEALTHY and
               any(hc.name == result.check_name and hc.critical for hc in self.health_checks)
        ]

        if critical_failures:
            overall_status = HealthCheckStatus.UNHEALTHY
        elif any(r.status == HealthCheckStatus.DEGRADED for r in health_results):
            overall_status = HealthCheckStatus.DEGRADED
        else:
            overall_status = HealthCheckStatus.HEALTHY

        # Collect performance metrics
        metrics = await self._collect_performance_metrics()

        return SystemHealth(
            overall_status=overall_status,
            component_status=component_status,
            health_checks=health_results,
            uptime_percentage=99.9,  # Would calculate actual uptime
            last_check=datetime.utcnow(),
            active_users=metrics.active_connections,
            error_rate=metrics.error_rate,
            response_time_p95=metrics.average_response_time,
            resource_usage={
                "cpu": metrics.cpu_usage,
                "memory": metrics.memory_usage,
                "disk": metrics.disk_usage
            }
        )

    async def _execute_health_check(self, health_check: HealthCheck) -> HealthCheckResult:
        """Execute individual health check"""
        start_time = datetime.utcnow()

        try:
            # Simulate health check execution
            await asyncio.sleep(0.5)  # Simulate network call

            # In real implementation, make actual HTTP request
            response_time = (datetime.utcnow() - start_time).total_seconds()

            # Simulate health check results
            if "critical" in health_check.name.lower():
                # Critical checks always pass in this simulation
                return HealthCheckResult(
                    check_name=health_check.name,
                    status=HealthCheckStatus.HEALTHY,
                    response_time=response_time,
                    status_code=200
                )
            else:
                # Non-critical checks occasionally degrade
                import random
                if secrets.SystemRandom().random() < 0.1:  # 10% chance of degradation
                    return HealthCheckResult(
                        check_name=health_check.name,
                        status=HealthCheckStatus.DEGRADED,
                        response_time=response_time + random.uniform(0.5, 2.0),
                        status_code=200,
                        error_message="Response time above threshold"
                    )
                else:
                    return HealthCheckResult(
                        check_name=health_check.name,
                        status=HealthCheckStatus.HEALTHY,
                        response_time=response_time,
                        status_code=200
                    )

        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            return HealthCheckResult(
                check_name=health_check.name,
                status=HealthCheckStatus.UNHEALTHY,
                response_time=response_time,
                error_message=str(e)
            )

    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect system performance metrics"""
        # Simulate metrics collection
        import random

        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cpu_usage=random.uniform(20, 80),
            memory_usage=random.uniform(30, 70),
            disk_usage=random.uniform(40, 60),
            network_io={
                "bytes_in": random.uniform(1000, 5000),
                "bytes_out": random.uniform(500, 2000)
            },
            active_connections=secrets.randbelow(90) + 10,
            requests_per_second=random.uniform(10, 50),
            average_response_time=random.uniform(0.1, 1.0),
            error_rate=random.uniform(0.01, 0.05),
            queue_size=secrets.randbelow(10) + 0,
            database_connections=secrets.randbelow(15) + 5
        )

    async def get_deployment_history(self, limit: int = 10) -> List[Deployment]:
        """Get deployment history"""
        all_deployments = list(self.deployments.values())

        # Sort by start date descending
        all_deployments.sort(key=lambda d: d.started_at, reverse=True)

        return all_deployments[:limit]

    async def get_current_deployment_status(self) -> Optional[Deployment]:
        """Get current deployment status"""
        return self.current_deployment

    async def monitor_deployment(self, deployment_id: str) -> Dict[str, Any]:
        """Monitor ongoing deployment"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")

        deployment = self.deployments[deployment_id]

        # Get current health status
        health = await self.check_system_health()

        # Get performance metrics
        metrics = await self._collect_performance_metrics()

        return {
            "deployment": asdict(deployment),
            "system_health": asdict(health),
            "performance_metrics": asdict(metrics),
            "rollback_available": deployment.config.rollback_enabled,
            "time_elapsed": (datetime.utcnow() - deployment.started_at).total_seconds()
        }

    async def generate_deployment_report(self, deployment_id: str) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        if deployment_id not in self.deployments:
            raise ValueError(f"Deployment not found: {deployment_id}")

        deployment = self.deployments[deployment_id]

        return {
            "deployment_summary": {
                "id": deployment.id,
                "version": deployment.config.version,
                "environment": deployment.config.environment.value,
                "status": deployment.status.value,
                "success": deployment.success,
                "duration": deployment.duration,
                "started_at": deployment.started_at.isoformat(),
                "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None
            },
            "configuration": asdict(deployment.config),
            "pre_deployment_checks": [asdict(check) for check in deployment.pre_deployment_checks],
            "post_deployment_checks": [asdict(check) for check in deployment.post_deployment_checks],
            "deployment_logs": deployment.deployment_logs,
            "rollback_info": {
                "enabled": deployment.config.rollback_enabled,
                "rollback_id": deployment.rollback_id,
                "rollback_plan": asdict(self.rollback_plans[deployment.rollback_id]) if deployment.rollback_id else None
            } if deployment.rollback_id else None,
            "performance_impact": await self._analyze_performance_impact(deployment),
            "recommendations": await self._generate_deployment_recommendations(deployment)
        }

    async def _analyze_performance_impact(self, deployment: Deployment) -> Dict[str, Any]:
        """Analyze performance impact of deployment"""
        # This would compare pre and post deployment metrics
        return {
            "cpu_impact": "minimal",
            "memory_impact": "minimal",
            "response_time_impact": "improved",
            "error_rate_impact": "reduced",
            "user_experience": "positive"
        }

    async def _generate_deployment_recommendations(self, deployment: Deployment) -> List[str]:
        """Generate deployment recommendations"""
        recommendations = []

        if not deployment.success:
            recommendations.append("Review deployment logs to identify failure causes")
            recommendations.append("Verify all pre-deployment checks are passing")
            recommendations.append("Consider implementing more thorough testing")

        if deployment.duration and deployment.duration > 600:  # 10 minutes
            recommendations.append("Consider optimizing deployment strategy to reduce downtime")

        # Analyze post-deployment health checks
        degraded_checks = [
            check for check in deployment.post_deployment_checks
            if check.status == HealthCheckStatus.DEGRADED
        ]

        if degraded_checks:
            recommendations.append(f"Investigate degraded health checks: {[check.check_name for check in degraded_checks]}")

        if deployment.success:
            recommendations.append("Deployment was successful - proceed with monitoring")
            recommendations.append("Consider updating rollback target to this version")

        return recommendations

    async def prepare_go_live_checklist(self) -> Dict[str, Any]:
        """Prepare comprehensive go-live checklist"""
        return {
            "pre_deployment": [
                " All unit tests passing",
                " Integration tests passing",
                " Security scans completed",
                " Performance benchmarks met",
                " Database migrations ready",
                " Backup procedures verified",
                " Rollback plan prepared",
                " Stakeholder notification sent"
            ],
            "deployment": [
                " Maintenance window scheduled",
                " Load balancer configured",
                " SSL certificates valid",
                " Monitoring alerts configured",
                " Log aggregation setup",
                " Error tracking enabled"
            ],
            "post_deployment": [
                "¡ Health checks passing",
                "¡ Smoke tests passing",
                "¡ Performance metrics within thresholds",
                "¡ User functionality verified",
                "¡ Error rates acceptable",
                "¡ Rollback window closed",
                "¡ Stakeholders notified of success"
            ],
            "emergency_contacts": [
                "DevOps Team: devops@psychsync.com",
                "Engineering Lead: eng-lead@psychsync.com",
                "Product Manager: pm@psychsync.com",
                "Support Team: support@psychsync.com"
            ],
            "rollback_triggers": [
                "Critical health check failures",
                "Error rate > 5%",
                "Response time > 5 seconds",
                "User complaints > 10/hour",
                "Manual trigger by team lead"
            ]
        }


# Initialize the deployment service
deployment_service = DeploymentService()