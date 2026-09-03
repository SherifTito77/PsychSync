#!/usr/bin/env python3
"""
PsychSync Deployment Readiness Automation
Comprehensive deployment validation and automation system

Implements:
- Environment validation and consistency checks
- Configuration management validation
- Database migration readiness
- Security configuration validation
- Infrastructure dependency verification
- Rollback planning and validation
- Health check automation
- CI/CD pipeline integration
"""

import asyncio
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml

sys.path.append(str(Path(__file__).parent.parent))

import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class EnvironmentValidationResult:
    """Environment validation result"""

    environment_name: str
    is_valid: bool
    database_connection: bool
    redis_connection: bool
    external_apis_available: bool
    ssl_certificate_valid: bool
    required_services_running: List[str]
    failed_services: List[str]
    configuration_valid: bool
    issues: List[str]


@dataclass
class ConfigurationValidationResult:
    """Configuration validation result"""

    config_file: str
    is_valid: bool
    missing_keys: List[str]
    invalid_values: List[str]
    security_issues: List[str]
    environment_specific_issues: List[str]
    recommendations: List[str]


@dataclass
class MigrationReadinessResult:
    """Database migration readiness result"""

    current_version: str
    target_version: str
    migrations_pending: List[str]
    can_migrate: bool
    backup_available: bool
    rollback_possible: bool
    estimated_time: int  # minutes
    risks: List[str]


@dataclass
class SecurityValidationResult:
    """Security validation result"""

    area: str
    status: str  # PASS, FAIL, WARNING
    issues: List[str]
    recommendations: List[str]
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class InfrastructureDependencyResult:
    """Infrastructure dependency check result"""

    dependency_name: str
    dependency_type: str  # DATABASE, CACHE, API, SERVICE
    is_available: bool
    response_time: float
    version_compatible: bool
    authentication_valid: bool
    endpoint: str
    issues: List[str]


@dataclass
class RollbackPlanResult:
    """Rollback plan validation result"""

    rollback_available: bool
    rollback_methods: List[str]
    last_successful_deployment: str
    backup_timestamp: str
    data_backup_available: bool
    rollback_tested: bool
    rollback_time_estimate: int  # minutes


class DeploymentReadinessAutomation:
    """
    Comprehensive deployment readiness validation and automation system
    """

    def __init__(self, project_root: str = None):
        self.project_root = project_root or str(Path(__file__).parent.parent)
        self.environment = os.getenv("DEPLOY_ENV", "production")
        self.config_files = [
            ".env.production",
            ".env.staging",
            "docker-compose.prod.yml",
            "kubernetes/",
            "nginx.conf",
        ]
        self.required_services = ["postgresql", "redis", "nginx"]
        self.external_dependencies = [
            {"name": "Database", "type": "DATABASE", "endpoint": "localhost:5432"},
            {"name": "Redis", "type": "CACHE", "endpoint": "localhost:6379"},
            {
                "name": "API Health",
                "type": "API",
                "endpoint": "http://localhost:8000/api/v1/health",
            },
        ]

    async def validate_environment(self) -> EnvironmentValidationResult:
        """Validate deployment environment"""
        print("🔧 Validating deployment environment...")

        validation_result = EnvironmentValidationResult(
            environment_name=self.environment,
            is_valid=False,
            database_connection=False,
            redis_connection=False,
            external_apis_available=False,
            ssl_certificate_valid=False,
            required_services_running=[],
            failed_services=[],
            configuration_valid=False,
            issues=[],
        )

        # Check database connection
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import asyncio; from app.core.database import engine; asyncio.run(engine.connect())",
                ],
                cwd=self.project_root,
                capture_output=True,
                timeout=30,
            )
            validation_result.database_connection = result.returncode == 0
            if not validation_result.database_connection:
                validation_result.issues.append("Database connection failed")
        except Exception as e:
            validation_result.issues.append(f"Database connection error: {e}")

        # Check Redis connection
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=0, socket_connect_timeout=5)
            r.ping()
            validation_result.redis_connection = True
        except Exception as e:
            validation_result.issues.append(f"Redis connection error: {e}")

        # Check external APIs
        try:
            response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
            validation_result.external_apis_available = response.status_code == 200
        except Exception as e:
            validation_result.issues.append(f"External API health check failed: {e}")

        # Check SSL certificate (for production)
        if self.environment == "production":
            validation_result.ssl_certificate_valid = (
                await self._check_ssl_certificate()
            )

        # Check required services
        for service in self.required_services:
            if self._is_service_running(service):
                validation_result.required_services_running.append(service)
            else:
                validation_result.failed_services.append(service)

        # Check configuration
        validation_result.configuration_valid = (
            await self._validate_configuration_files()
        )

        # Overall validity
        validation_result.is_valid = (
            validation_result.database_connection
            and validation_result.redis_connection
            and validation_result.external_apis_available
            and len(validation_result.failed_services) == 0
            and validation_result.configuration_valid
        )

        return validation_result

    async def validate_configurations(self) -> List[ConfigurationValidationResult]:
        """Validate all configuration files"""
        print("⚙️  Validating configuration files...")

        validation_results = []

        for config_file in self.config_files:
            config_path = os.path.join(self.project_root, config_file)
            if os.path.exists(config_path):
                result = await self._validate_single_configuration(config_path)
                validation_results.append(result)
            else:
                validation_results.append(
                    ConfigurationValidationResult(
                        config_file=config_file,
                        is_valid=False,
                        missing_keys=[],
                        invalid_values=[],
                        security_issues=[],
                        environment_specific_issues=[
                            f"Configuration file not found: {config_file}"
                        ],
                        recommendations=[
                            f"Create {config_file} with proper configuration"
                        ],
                    )
                )

        return validation_results

    async def check_migration_readiness(self) -> MigrationReadinessResult:
        """Check database migration readiness"""
        print("🗄️  Checking migration readiness...")

        try:
            # Get current migration version
            result = subprocess.run(
                ["alembic", "current"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return MigrationReadinessResult(
                    current_version="unknown",
                    target_version="unknown",
                    migrations_pending=[],
                    can_migrate=False,
                    backup_available=False,
                    rollback_possible=False,
                    estimated_time=0,
                    risks=["Cannot determine current migration state"],
                )

            current_version = (
                result.stdout.strip().split(" ")[-1]
                if result.stdout.strip()
                else "None"
            )

            # Get head migration version
            result = subprocess.run(
                ["alembic", "heads"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            target_version = (
                result.stdout.strip().split(" ")[-1]
                if result.stdout.strip()
                else current_version
            )

            # Get pending migrations
            result = subprocess.run(
                ["alembic", "history"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
            )

            migrations_pending = []
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                current_found = False
                for line in lines:
                    if current_version in line and "->" in line:
                        current_found = True
                    elif current_found and "->" in line:
                        migration_id = line.strip().split(" -> ")[1].split()[0]
                        migrations_pending.append(migration_id)

            # Check if backup is available
            backup_available = await self._check_database_backup()

            # Estimate migration time based on pending migrations
            estimated_time = len(migrations_pending) * 5  # 5 minutes per migration

            # Assess risks
            risks = []
            if len(migrations_pending) > 5:
                risks.append("Many migrations pending - consider batching")
            if not backup_available:
                risks.append("No database backup available")
            if self.environment == "production" and len(migrations_pending) > 0:
                risks.append("Production migrations require extra caution")

            return MigrationReadinessResult(
                current_version=current_version,
                target_version=target_version,
                migrations_pending=migrations_pending,
                can_migrate=len(migrations_pending) >= 0 and len(risks) == 0,
                backup_available=backup_available,
                rollback_possible=backup_available,  # Simplified
                estimated_time=estimated_time,
                risks=risks,
            )

        except Exception as e:
            logger.error(f"Error checking migration readiness: {e}")
            return MigrationReadinessResult(
                current_version="error",
                target_version="error",
                migrations_pending=[],
                can_migrate=False,
                backup_available=False,
                rollback_possible=False,
                estimated_time=0,
                risks=[f"Migration check failed: {e}"],
            )

    async def validate_security_configurations(self) -> List[SecurityValidationResult]:
        """Validate security configurations"""
        print("🔒 Validating security configurations...")

        security_validations = []

        # JWT configuration
        jwt_result = await self._validate_jwt_configuration()
        security_validations.append(jwt_result)

        # Database security
        db_result = await self._validate_database_security()
        security_validations.append(db_result)

        # HTTPS configuration
        https_result = await self._validate_https_configuration()
        security_validations.append(https_result)

        # Environment variables security
        env_result = await self._validate_environment_variables_security()
        security_validations.append(env_result)

        # CORS configuration
        cors_result = await self._validate_cors_configuration()
        security_validations.append(cors_result)

        return security_validations

    async def verify_infrastructure_dependencies(
        self,
    ) -> List[InfrastructureDependencyResult]:
        """Verify all infrastructure dependencies"""
        print("🏗️  Verifying infrastructure dependencies...")

        dependency_results = []

        for dep in self.external_dependencies:
            try:
                result = await self._check_dependency(dep)
                dependency_results.append(result)
                print(
                    f"  {'✅' if result.is_available else '❌'} {dep['name']}: {result.response_time:.2f}s"
                )
            except Exception as e:
                logger.error(f"Error checking dependency {dep['name']}: {e}")
                dependency_results.append(
                    InfrastructureDependencyResult(
                        dependency_name=dep["name"],
                        dependency_type=dep["type"],
                        is_available=False,
                        response_time=0.0,
                        version_compatible=False,
                        authentication_valid=False,
                        endpoint=dep["endpoint"],
                        issues=[f"Dependency check failed: {e}"],
                    )
                )

        return dependency_results

    async def validate_rollback_plan(self) -> RollbackPlanResult:
        """Validate rollback plan and capabilities"""
        print("🔄 Validating rollback plan...")

        rollback_result = RollbackPlanResult(
            rollback_available=False,
            rollback_methods=[],
            last_successful_deployment="",
            backup_timestamp="",
            data_backup_available=False,
            rollback_tested=False,
            rollback_time_estimate=0,
        )

        # Check for available rollback methods
        rollback_methods = []

        # Check if Docker rollback is available
        if os.path.exists(os.path.join(self.project_root, "docker-compose.yml")):
            rollback_methods.append("docker_compose")

        # Check if Git rollback is available
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                rollback_methods.append("git")
                # Get last commit
                last_commit = result.stdout.strip().split("\n")[0].split(" ")[1]
                rollback_result.last_successful_deployment = last_commit
        except Exception as e:
            pass

        # Check for database backups
        rollback_result.data_backup_available = await self._check_database_backup()
        if rollback_result.data_backup_available:
            rollback_methods.append("database_restore")

        # Check if rollback has been tested
        rollback_result.rollback_tested = os.path.exists(
            os.path.join(self.project_root, "tests", "test_rollback.py")
        )

        # Estimate rollback time
        rollback_result.rollback_time_estimate = (
            len(rollback_methods) * 10
        )  # 10 minutes per method

        # Check backup timestamp
        try:
            backup_info = await self._get_latest_backup_info()
            if backup_info:
                rollback_result.backup_timestamp = backup_info.get("timestamp", "")
        except Exception as e:
            pass

        rollback_result.rollback_available = len(rollback_methods) > 0
        rollback_result.rollback_methods = rollback_methods

        return rollback_result

    async def generate_deployment_checklist(self) -> Dict[str, Any]:
        """Generate comprehensive deployment checklist"""
        print("📋 Generating deployment checklist...")

        # Run all validations
        environment_validation = await self.validate_environment()
        configuration_validations = await self.validate_configurations()
        migration_readiness = await self.check_migration_readiness()
        security_validations = await self.validate_security_configurations()
        dependency_results = await self.verify_infrastructure_dependencies()
        rollback_plan = await self.validate_rollback_plan()

        # Calculate overall readiness score
        readiness_score = self._calculate_readiness_score(
            environment_validation,
            configuration_validations,
            migration_readiness,
            security_validations,
            dependency_results,
            rollback_plan,
        )

        # Generate checklist items
        checklist = {
            "pre_deployment": [
                {
                    "task": "Environment validation",
                    "completed": environment_validation.is_valid,
                    "critical": True,
                    "description": "Validate all environment dependencies and services",
                    "issues": environment_validation.issues,
                },
                {
                    "task": "Configuration validation",
                    "completed": all(c.is_valid for c in configuration_validations),
                    "critical": True,
                    "description": "Validate all configuration files",
                    "issues": [
                        issue
                        for config in configuration_validations
                        for issue in config.environment_specific_issues
                    ],
                },
                {
                    "task": "Database migration readiness",
                    "completed": migration_readiness.can_migrate,
                    "critical": True,
                    "description": "Ensure database migrations are ready",
                    "issues": migration_readiness.risks,
                },
                {
                    "task": "Security validation",
                    "completed": all(s.status == "PASS" for s in security_validations),
                    "critical": True,
                    "description": "Validate security configurations",
                    "issues": [
                        issue for sec in security_validations for issue in sec.issues
                    ],
                },
            ],
            "deployment": [
                {
                    "task": "Infrastructure dependencies verification",
                    "completed": all(d.is_available for d in dependency_results),
                    "critical": True,
                    "description": "Verify all external dependencies are available",
                    "issues": [
                        issue for dep in dependency_results for issue in dep.issues
                    ],
                },
                {
                    "task": "Rollback plan validation",
                    "completed": rollback_plan.rollback_available,
                    "critical": False,
                    "description": "Ensure rollback capability is available",
                    "issues": (
                        ["Rollback plan not available"]
                        if not rollback_plan.rollback_available
                        else []
                    ),
                },
            ],
            "post_deployment": [
                {
                    "task": "Health checks",
                    "completed": False,
                    "critical": True,
                    "description": "Run comprehensive health checks",
                    "issues": [],
                },
                {
                    "task": "Performance validation",
                    "completed": False,
                    "critical": False,
                    "description": "Validate application performance",
                    "issues": [],
                },
                {
                    "task": "Monitoring setup",
                    "completed": False,
                    "critical": True,
                    "description": "Ensure monitoring and alerting are active",
                    "issues": [],
                },
            ],
        }

        # Generate blocking issues
        blocking_issues = []
        for category in checklist.values():
            for item in category:
                if item["critical"] and not item["completed"]:
                    blocking_issues.extend(item["issues"])

        # Generate recommendations
        recommendations = []
        if readiness_score < 80:
            recommendations.append("Address critical issues before deployment")
        if not rollback_plan.rollback_available:
            recommendations.append(
                "Set up rollback procedures before production deployment"
            )
        if len(migration_readiness.migrations_pending) > 5:
            recommendations.append("Consider batching database migrations")

        return {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "readiness_score": readiness_score,
            "readiness_grade": self._get_readiness_grade(readiness_score),
            "blocking_issues_count": len(blocking_issues),
            "blocking_issues": blocking_issues,
            "checklist": checklist,
            "environment_validation": asdict(environment_validation),
            "configuration_validations": [asdict(c) for c in configuration_validations],
            "migration_readiness": asdict(migration_readiness),
            "security_validations": [asdict(s) for s in security_validations],
            "dependency_results": [asdict(d) for d in dependency_results],
            "rollback_plan": asdict(rollback_plan),
            "recommendations": recommendations,
            "deployment_safe": readiness_score >= 80 and len(blocking_issues) == 0,
        }

    async def _check_ssl_certificate(self) -> bool:
        """Check SSL certificate validity"""
        try:
            import socket
            import ssl
            from datetime import datetime

            # Get SSL certificate for localhost (adjust for production)
            context = ssl.create_default_context()
            with socket.create_connection(("localhost", 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                    cert = ssock.getpeercert()
                    # Check if certificate is valid
                    return True
        except Exception as e:
            logger.info(f"SSL certificate check failed (may be expected in dev): {e}")
            return False

    def _is_service_running(self, service_name: str) -> bool:
        """Check if a service is running"""
        try:
            if service_name == "postgresql":
                result = subprocess.run(["pgrep", "postgres"], capture_output=True)
            elif service_name == "redis":
                result = subprocess.run(["pgrep", "redis-server"], capture_output=True)
            elif service_name == "nginx":
                result = subprocess.run(["pgrep", "nginx"], capture_output=True)
            else:
                result = subprocess.run(["pgrep", service_name], capture_output=True)

            return result.returncode == 0
        except Exception:
            return False

    async def _validate_configuration_files(self) -> bool:
        """Validate configuration files exist and are properly formatted"""
        required_configs = [".env.production"]

        for config in required_configs:
            config_path = os.path.join(self.project_root, config)
            if not os.path.exists(config_path):
                return False

        return True

    async def _validate_single_configuration(
        self, config_path: str
    ) -> ConfigurationValidationResult:
        """Validate a single configuration file"""
        result = ConfigurationValidationResult(
            config_file=config_path,
            is_valid=True,
            missing_keys=[],
            invalid_values=[],
            security_issues=[],
            environment_specific_issues=[],
            recommendations=[],
        )

        try:
            with open(config_path, "r") as f:
                content = f.read()

            # Check for required keys based on file type
            if config_path.endswith(".env"):
                required_keys = ["SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
                for key in required_keys:
                    if key not in content:
                        result.missing_keys.append(key)
                        result.is_valid = False

            # Check for security issues
            if "password=" in content.lower() and "secret" not in content.lower():
                result.security_issues.append("Plain text password detected")

            if "DEBUG=True" in content and "production" in config_path:
                result.security_issues.append("DEBUG=True in production configuration")

            # Check environment-specific issues
            if self.environment == "production" and "localhost" in content:
                result.environment_specific_issues.append(
                    "localhost URLs in production configuration"
                )

        except Exception as e:
            result.is_valid = False
            result.environment_specific_issues.append(
                f"Configuration parsing error: {e}"
            )

        return result

    async def _check_database_backup(self) -> bool:
        """Check if database backup is available"""
        try:
            # This would check for actual backup files or backup service
            backup_dir = os.path.join(self.project_root, "backups")
            if os.path.exists(backup_dir):
                backup_files = [
                    f
                    for f in os.listdir(backup_dir)
                    if f.endswith(".sql") or f.endswith(".dump")
                ]
                return len(backup_files) > 0
            return False
        except Exception:
            return False

    async def _validate_jwt_configuration(self) -> SecurityValidationResult:
        """Validate JWT configuration"""
        issues = []
        recommendations = []

        try:
            from app.core.config import settings

            secret_key = getattr(settings, "SECRET_KEY", None)

            if not secret_key:
                issues.append("SECRET_KEY not configured")
            elif len(secret_key) < 32:
                issues.append("SECRET_KEY too short (minimum 32 characters)")

            # Check JWT expiration
            jwt_expire_minutes = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 30)
            if jwt_expire_minutes > 1440:  # 24 hours
                issues.append("JWT token expiration too long")

        except Exception as e:
            issues.append(f"JWT configuration error: {e}")

        status = "PASS" if len(issues) == 0 else "FAIL"
        severity = "CRITICAL" if len(issues) > 0 else "LOW"

        return SecurityValidationResult(
            area="JWT Configuration",
            status=status,
            issues=issues,
            recommendations=recommendations,
            severity=severity,
        )

    async def _validate_database_security(self) -> SecurityValidationResult:
        """Validate database security configuration"""
        issues = []
        recommendations = []

        # Check if SSL is required for database connections
        try:
            from app.core.config import settings

            db_url = getattr(settings, "DATABASE_URL", "")

            if "sslmode=require" not in db_url and self.environment == "production":
                issues.append("Database connection should use SSL in production")

        except Exception as e:
            issues.append(f"Database security check error: {e}")

        status = "PASS" if len(issues) == 0 else "FAIL"
        severity = "HIGH" if len(issues) > 0 else "LOW"

        return SecurityValidationResult(
            area="Database Security",
            status=status,
            issues=issues,
            recommendations=recommendations,
            severity=severity,
        )

    async def _validate_https_configuration(self) -> SecurityValidationResult:
        """Validate HTTPS configuration"""
        issues = []
        recommendations = []

        if self.environment == "production":
            # Check if HTTPS redirects are configured
            nginx_conf = os.path.join(self.project_root, "nginx.conf")
            if os.path.exists(nginx_conf):
                with open(nginx_conf, "r") as f:
                    content = f.read()
                    if "443 ssl" not in content:
                        issues.append("HTTPS not configured in nginx")

        status = "PASS" if len(issues) == 0 else "FAIL"
        severity = "HIGH" if len(issues) > 0 else "LOW"

        return SecurityValidationResult(
            area="HTTPS Configuration",
            status=status,
            issues=issues,
            recommendations=recommendations,
            severity=severity,
        )

    async def _validate_environment_variables_security(
        self,
    ) -> SecurityValidationResult:
        """Validate environment variables security"""
        issues = []
        recommendations = []

        # Check for secrets in code
        try:
            result = subprocess.run(
                ["grep", "-r", "SECRET_KEY", "app/", "--include=*.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if "=" in line and not line.strip().startswith("#"):
                        issues.append("Hardcoded secret found in source code")

        except Exception:
            pass

        status = "PASS" if len(issues) == 0 else "FAIL"
        severity = "CRITICAL" if len(issues) > 0 else "LOW"

        return SecurityValidationResult(
            area="Environment Variables Security",
            status=status,
            issues=issues,
            recommendations=["Use environment variables for all secrets"],
            severity=severity,
        )

    async def _validate_cors_configuration(self) -> SecurityValidationResult:
        """Validate CORS configuration"""
        issues = []
        recommendations = []

        try:
            from app.core.config import settings

            cors_origins = getattr(settings, "CORS_ORIGINS", [])

            if self.environment == "production":
                if "*" in cors_origins or "localhost" in cors_origins:
                    issues.append("Overly permissive CORS origins in production")

        except Exception as e:
            issues.append(f"CORS configuration check error: {e}")

        status = "PASS" if len(issues) == 0 else "FAIL"
        severity = "MEDIUM" if len(issues) > 0 else "LOW"

        return SecurityValidationResult(
            area="CORS Configuration",
            status=status,
            issues=issues,
            recommendations=recommendations,
            severity=severity,
        )

    async def _check_dependency(
        self, dependency: Dict
    ) -> InfrastructureDependencyResult:
        """Check a single infrastructure dependency"""
        start_time = time.time()

        if dependency["type"] == "DATABASE":
            # Check PostgreSQL
            try:
                import psycopg2

                conn = psycopg2.connect("dbname=postgres user=postgres host=localhost")
                conn.close()
                response_time = (time.time() - start_time) * 1000
                return InfrastructureDependencyResult(
                    dependency_name=dependency["name"],
                    dependency_type=dependency["type"],
                    is_available=True,
                    response_time=response_time,
                    version_compatible=True,
                    authentication_valid=True,
                    endpoint=dependency["endpoint"],
                    issues=[],
                )
            except Exception as e:
                return InfrastructureDependencyResult(
                    dependency_name=dependency["name"],
                    dependency_type=dependency["type"],
                    is_available=False,
                    response_time=0.0,
                    version_compatible=False,
                    authentication_valid=False,
                    endpoint=dependency["endpoint"],
                    issues=[str(e)],
                )

        elif dependency["type"] == "CACHE":
            # Check Redis
            try:
                import redis

                r = redis.Redis(
                    host="localhost", port=6379, db=0, socket_connect_timeout=5
                )
                r.ping()
                response_time = (time.time() - start_time) * 1000
                return InfrastructureDependencyResult(
                    dependency_name=dependency["name"],
                    dependency_type=dependency["type"],
                    is_available=True,
                    response_time=response_time,
                    version_compatible=True,
                    authentication_valid=True,
                    endpoint=dependency["endpoint"],
                    issues=[],
                )
            except Exception as e:
                return InfrastructureDependencyResult(
                    dependency_name=dependency["name"],
                    dependency_type=dependency["type"],
                    is_available=False,
                    response_time=0.0,
                    version_compatible=False,
                    authentication_valid=False,
                    endpoint=dependency["endpoint"],
                    issues=[str(e)],
                )

        elif dependency["type"] == "API":
            # Check API endpoint
            try:
                response = requests.get(dependency["endpoint"], timeout=10)
                response_time = (time.time() - start_time) * 1000
                return InfrastructureDependencyResult(
                    dependency_name=dependency["name"],
                    dependency_type=dependency["type"],
                    is_available=response.status_code == 200,
                    response_time=response_time,
                    version_compatible=True,
                    authentication_valid=True,
                    endpoint=dependency["endpoint"],
                    issues=(
                        []
                        if response.status_code == 200
                        else [f"HTTP {response.status_code}"]
                    ),
                )
            except Exception as e:
                return InfrastructureDependencyResult(
                    dependency_name=dependency["name"],
                    dependency_type=dependency["type"],
                    is_available=False,
                    response_time=0.0,
                    version_compatible=False,
                    authentication_valid=False,
                    endpoint=dependency["endpoint"],
                    issues=[str(e)],
                )

        return InfrastructureDependencyResult(
            dependency_name=dependency["name"],
            dependency_type=dependency["type"],
            is_available=False,
            response_time=0.0,
            version_compatible=False,
            authentication_valid=False,
            endpoint=dependency["endpoint"],
            issues=["Unknown dependency type"],
        )

    async def _get_latest_backup_info(self) -> Optional[Dict]:
        """Get latest backup information"""
        try:
            backup_dir = os.path.join(self.project_root, "backups")
            if os.path.exists(backup_dir):
                backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".sql")]
                if backup_files:
                    latest_backup = max(
                        backup_files,
                        key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)),
                    )
                    backup_path = os.path.join(backup_dir, latest_backup)
                    return {
                        "filename": latest_backup,
                        "timestamp": datetime.fromtimestamp(
                            os.path.getmtime(backup_path)
                        ).isoformat(),
                        "size_mb": os.path.getsize(backup_path) / (1024 * 1024),
                    }
        except Exception as e:
            logger.error(f"Error getting backup info: {e}")
        return None

    def _calculate_readiness_score(self, *validation_results) -> float:
        """Calculate overall deployment readiness score"""
        score = 100

        # Environment validation (30% weight)
        env_validation = validation_results[0]
        if not env_validation.is_valid:
            score -= 30

        # Configuration validation (20% weight)
        config_validations = validation_results[1]
        if config_validations:
            config_score = (
                sum(1 for c in config_validations if c.is_valid)
                / len(config_validations)
                * 20
            )
            score -= 20 - config_score

        # Migration readiness (20% weight)
        migration_ready = validation_results[2]
        if not migration_ready.can_migrate:
            score -= 20

        # Security validation (15% weight)
        security_validations = validation_results[3]
        if security_validations:
            security_score = (
                sum(1 for s in security_validations if s.status == "PASS")
                / len(security_validations)
                * 15
            )
            score -= 15 - security_score

        # Dependencies (10% weight)
        dependencies = validation_results[4]
        if dependencies:
            dep_score = (
                sum(1 for d in dependencies if d.is_available) / len(dependencies) * 10
            )
            score -= 10 - dep_score

        # Rollback plan (5% weight)
        rollback_plan = validation_results[5]
        if not rollback_plan.rollback_available:
            score -= 5

        return max(0, min(100, score))

    def _get_readiness_grade(self, score: float) -> str:
        """Get readiness grade from score"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 80:
            return "GOOD"
        elif score >= 70:
            return "ACCEPTABLE"
        elif score >= 60:
            return "NEEDS_WORK"
        else:
            return "NOT_READY"


async def main():
    """Main execution function"""
    print("🚀 PsychSync Deployment Readiness Automation")
    print("=" * 50)

    automation = DeploymentReadinessAutomation()

    try:
        # Generate deployment checklist
        checklist = await automation.generate_deployment_checklist()

        # Display results
        print(
            f"\n📊 Deployment Readiness Score: {checklist['readiness_score']:.1f}/100"
        )
        print(f"📈 Readiness Grade: {checklist['readiness_grade']}")
        print(f"🚫 Blocking Issues: {checklist['blocking_issues_count']}")

        # Display checklist status
        print(f"\n📋 Deployment Checklist Status:")

        for category_name, category_items in checklist["checklist"].items():
            print(f"\n   {category_name.upper().replace('_', ' ')}:")
            for item in category_items:
                status = (
                    "✅" if item["completed"] else "❌" if item["critical"] else "⚠️"
                )
                print(f"     {status} {item['task']}")
                if item["issues"]:
                    for issue in item["issues"][:2]:  # Show first 2 issues
                        print(f"        • {issue}")

        # Display environment validation
        env = checklist["environment_validation"]
        print(f"\n🔧 Environment Validation:")
        print(f"   Database: {'✅' if env['database_connection'] else '❌'}")
        print(f"   Redis: {'✅' if env['redis_connection'] else '❌'}")
        print(f"   APIs: {'✅' if env['external_apis_available'] else '❌'}")
        print(f"   SSL: {'✅' if env['ssl_certificate_valid'] else '⚠️'}")

        # Display migration readiness
        migration = checklist["migration_readiness"]
        print(f"\n🗄️  Migration Readiness:")
        print(f"   Current Version: {migration['current_version']}")
        print(f"   Pending Migrations: {len(migration['migrations_pending'])}")
        print(f"   Backup Available: {'✅' if migration['backup_available'] else '❌'}")
        print(f"   Estimated Time: {migration['estimated_time']} minutes")

        # Display security validation
        security = checklist["security_validations"]
        print(f"\n🔒 Security Validation:")
        for sec in security:
            status_icon = "✅" if sec["status"] == "PASS" else "❌"
            print(f"   {status_icon} {sec['area']}: {sec['status']}")

        # Display blocking issues
        if checklist["blocking_issues"]:
            print(f"\n🚨 Blocking Issues:")
            for issue in checklist["blocking_issues"]:
                print(f"   • {issue}")

        # Display recommendations
        if checklist["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in checklist["recommendations"]:
                print(f"   • {rec}")

        # Deployment decision
        if checklist["deployment_safe"]:
            print(f"\n✅ DEPLOYMENT SAFE - Ready for production deployment")
            exit_code = 0
        else:
            print(f"\n❌ DEPLOYMENT NOT SAFE - Address blocking issues first")
            exit_code = 1

        # Save detailed report
        report_file = "deployment_readiness_report.json"
        with open(report_file, "w") as f:
            json.dump(checklist, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        return exit_code

    except Exception as e:
        logger.error(f"Error during deployment readiness check: {e}")
        print(f"❌ Deployment readiness check failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
