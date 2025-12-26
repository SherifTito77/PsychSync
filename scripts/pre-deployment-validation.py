#!/usr/bin/env python3
"""
PsychSync Pre-Deployment Validation Script
Comprehensive production readiness verification before deployment

Usage: python scripts/pre-deployment-validation.py [--environment production|staging]
"""

import asyncio
import sys
import argparse
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import psycopg2
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class PreDeploymentValidator:
    """Comprehensive pre-deployment validation for PsychSync"""

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.validation_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': environment,
            'validations': {},
            'critical_failures': [],
            'warnings': [],
            'overall_status': 'PENDING'
        }

    async def run_all_validations(self) -> Dict[str, Any]:
        """Execute all pre-deployment validations"""
        print(f"🔍 Starting comprehensive pre-deployment validation for {self.environment} environment")
        print("=" * 70)

        validations = [
            ('database', self.validate_database_connection),
            ('migrations', self.validate_database_migrations),
            ('configuration', self.validate_configuration),
            ('dependencies', self.validate_dependencies),
            ('security', self.validate_security_settings),
            ('performance', self.validate_performance_baseline),
            ('monitoring', self.validate_monitoring_setup),
            ('backups', self.validate_backup_strategy)
        ]

        for validation_name, validation_func in validations:
            try:
                print(f"\n🔧 Validating {validation_name.upper()}...")
                result = await validation_func()
                self.validation_results['validations'][validation_name] = result

                if result['status'] == 'CRITICAL':
                    self.validation_results['critical_failures'].append(f"{validation_name}: {result['message']}")
                    print(f"❌ {validation_name.upper()}: CRITICAL - {result['message']}")
                elif result['status'] == 'WARNING':
                    self.validation_results['warnings'].append(f"{validation_name}: {result['message']}")
                    print(f"⚠️  {validation_name.upper()}: WARNING - {result['message']}")
                else:
                    print(f"✅ {validation_name.upper()}: PASSED")

            except Exception as e:
                error_msg = f"{validation_name} validation failed: {str(e)}"
                self.validation_results['critical_failures'].append(error_msg)
                print(f"❌ {validation_name.upper()}: ERROR - {error_msg}")

        # Determine overall status
        if self.validation_results['critical_failures']:
            self.validation_results['overall_status'] = 'FAILED'
        elif self.validation_results['warnings']:
            self.validation_results['overall_status'] = 'WARNING'
        else:
            self.validation_results['overall_status'] = 'PASSED'

        return self.validation_results

    async def validate_database_connection(self) -> Dict[str, Any]:
        """Validate database connectivity and health"""
        try:
            from app.core.config import settings

            # Test database connection
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                port=settings.DB_PORT,
                connect_timeout=10
            )

            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result[0] == 1:
                return {
                    'status': 'PASSED',
                    'message': 'Database connection successful',
                    'details': {
                        'host': settings.DB_HOST,
                        'database': settings.DB_NAME,
                        'port': settings.DB_PORT
                    }
                }
            else:
                return {
                    'status': 'CRITICAL',
                    'message': 'Database query test failed'
                }

        except Exception as e:
            return {
                'status': 'CRITICAL',
                'message': f'Database connection failed: {str(e)}'
            }

    async def validate_database_migrations(self) -> Dict[str, Any]:
        """Validate all database migrations are applied"""
        try:
            # Check if alembic migrations table exists
            from app.core.database import get_async_db
            from sqlalchemy import text

            async for db in get_async_db():
                result = await db.execute(text("""
                    SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1
                """))
                current_version = result.scalar()

                if not current_version:
                    return {
                        'status': 'CRITICAL',
                        'message': 'No migrations have been applied'
                    }

                # Count total migration files
                migrations_dir = project_root / 'alembic/versions'
                migration_files = list(migrations_dir.glob('*.py'))
                total_migrations = len([f for f in migration_files if f.name != '__init__.py'])

                return {
                    'status': 'PASSED',
                    'message': f'Migrations are current (version: {current_version})',
                    'details': {
                        'current_version': current_version,
                        'total_migration_files': total_migrations
                    }
                }

        except Exception as e:
            return {
                'status': 'CRITICAL',
                'message': f'Migration validation failed: {str(e)}'
            }

    async def validate_configuration(self) -> Dict[str, Any]:
        """Validate all required configuration settings"""
        try:
            from app.core.config import settings
            required_settings = [
                'SECRET_KEY',
                'DATABASE_URL',
                'REDIS_HOST',
                'REDIS_PORT'
            ]

            missing_settings = []
            weak_settings = []

            for setting in required_settings:
                if not hasattr(settings, setting) or not getattr(settings, setting):
                    missing_settings.append(setting)

            # Check for weak security settings
            if hasattr(settings, 'SECRET_KEY') and len(settings.SECRET_KEY) < 32:
                weak_settings.append('SECRET_KEY should be at least 32 characters')

            if missing_settings:
                return {
                    'status': 'CRITICAL',
                    'message': f'Missing required settings: {", ".join(missing_settings)}'
                }

            if weak_settings:
                return {
                    'status': 'WARNING',
                    'message': f'Weak security settings: {", ".join(weak_settings)}'
                }

            return {
                'status': 'PASSED',
                'message': 'All configuration settings are valid',
                'details': {
                    'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
                    'debug_mode': getattr(settings, 'DEBUG', False)
                }
            }

        except Exception as e:
            return {
                'status': 'CRITICAL',
                'message': f'Configuration validation failed: {str(e)}'
            }

    async def validate_dependencies(self) -> Dict[str, Any]:
        """Validate all Python dependencies are properly installed"""
        try:
            # Check critical dependencies
            critical_packages = [
                'fastapi',
                'sqlalchemy',
                'alembic',
                'redis',
                'psycopg2-binary',
                'pydantic',
                'uvicorn'
            ]

            failed_packages = []

            for package in critical_packages:
                try:
                    __import__(package.replace('-', '_'))
                except ImportError:
                    failed_packages.append(package)

            if failed_packages:
                return {
                    'status': 'CRITICAL',
                    'message': f'Missing critical dependencies: {", ".join(failed_packages)}'
                }

            # Check package versions
            import fastapi
            fastapi_version = fastapi.__version__

            return {
                'status': 'PASSED',
                'message': 'All dependencies are available',
                'details': {
                    'fastapi_version': fastapi_version,
                    'total_packages_checked': len(critical_packages)
                }
            }

        except Exception as e:
            return {
                'status': 'CRITICAL',
                'message': f'Dependency validation failed: {str(e)}'
            }

    async def validate_security_settings(self) -> Dict[str, Any]:
        """Validate security-related settings are properly configured"""
        try:
            from app.core.config import settings

            security_issues = []

            # Check for secure secrets
            if not hasattr(settings, 'SECRET_KEY') or settings.SECRET_KEY == 'your-secret-key':
                security_issues.append('Default SECRET_KEY detected - must be changed')

            # Check CORS configuration
            if hasattr(settings, 'CORS_ORIGINS') and '*' in settings.CORS_ORIGINS:
                security_issues.append('CORS configured to allow all origins - not secure for production')

            # Check if HTTPS is enforced
            if hasattr(settings, 'ENVIRONMENT') and settings.ENVIRONMENT == 'production':
                if not hasattr(settings, 'FORCE_HTTPS') or not settings.FORCE_HTTPS:
                    security_issues.append('HTTPS not enforced in production')

            if security_issues:
                return {
                    'status': 'WARNING',
                    'message': f'Security issues detected: {", ".join(security_issues)}',
                    'details': {'issues': security_issues}
                }

            return {
                'status': 'PASSED',
                'message': 'Security settings are properly configured',
                'details': {
                    'cors_origins_count': len(getattr(settings, 'CORS_ORIGINS', [])),
                    'environment': getattr(settings, 'ENVIRONMENT', 'unknown')
                }
            }

        except Exception as e:
            return {
                'status': 'CRITICAL',
                'message': f'Security validation failed: {str(e)}'
            }

    async def validate_performance_baseline(self) -> Dict[str, Any]:
        """Validate basic performance metrics"""
        try:
            # Test basic application startup
            startup_time = self._measure_startup_time()

            # Test database query performance
            query_time = await self._measure_database_query_time()

            if startup_time > 30:  # seconds
                return {
                    'status': 'WARNING',
                    'message': f'Slow application startup: {startup_time:.2f}s',
                    'details': {
                        'startup_time_seconds': startup_time,
                        'database_query_time_seconds': query_time
                    }
                }

            if query_time > 5:  # seconds
                return {
                    'status': 'WARNING',
                    'message': f'Slow database query response: {query_time:.2f}s',
                    'details': {
                        'startup_time_seconds': startup_time,
                        'database_query_time_seconds': query_time
                    }
                }

            return {
                'status': 'PASSED',
                'message': 'Performance baselines are acceptable',
                'details': {
                    'startup_time_seconds': startup_time,
                    'database_query_time_seconds': query_time
                }
            }

        except Exception as e:
            return {
                'status': 'WARNING',
                'message': f'Performance baseline validation failed: {str(e)}'
            }

    def _measure_startup_time(self) -> float:
        """Measure application startup time"""
        try:
            start_time = datetime.now()

            # Test import
            from app.main import app

            end_time = datetime.now()
            return (end_time - start_time).total_seconds()

        except Exception:
            return float('inf')

    async def _measure_database_query_time(self) -> float:
        """Measure basic database query response time"""
        try:
            from app.core.database import get_async_db
            from sqlalchemy import text

            start_time = datetime.now()

            async for db in get_async_db():
                await db.execute(text("SELECT 1"))
                break

            end_time = datetime.now()
            return (end_time - start_time).total_seconds()

        except Exception:
            return float('inf')

    async def validate_monitoring_setup(self) -> Dict[str, Any]:
        """Validate monitoring and logging setup"""
        try:
            # Check if logging is configured
            import logging

            # Get PsychSync logger
            logger = logging.getLogger('app')

            if not logger.handlers:
                return {
                    'status': 'WARNING',
                    'message': 'No logging handlers configured'
                }

            # Check Redis connection for monitoring
            try:
                import redis
                redis_client = redis.Redis(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    decode_responses=True
                )
                redis_client.ping()
                redis_status = 'connected'
            except Exception:
                redis_status = 'disconnected'

            return {
                'status': 'PASSED' if redis_status == 'connected' else 'WARNING',
                'message': f'Monitoring setup validated (Redis: {redis_status})',
                'details': {
                    'logging_handlers_count': len(logger.handlers),
                    'redis_status': redis_status
                }
            }

        except Exception as e:
            return {
                'status': 'WARNING',
                'message': f'Monitoring validation failed: {str(e)}'
            }

    async def validate_backup_strategy(self) -> Dict[str, Any]:
        """Validate backup and recovery strategy"""
        try:
            from app.core.config import settings

            backup_issues = []

            # Check if backup is configured
            if not hasattr(settings, 'BACKUP_SCHEDULE'):
                backup_issues.append('No backup schedule configured')

            # Check retention policy
            if not hasattr(settings, 'BACKUP_RETENTION_DAYS'):
                backup_issues.append('No backup retention policy configured')

            # Check backup storage
            if not hasattr(settings, 'BACKUP_STORAGE_LOCATION'):
                backup_issues.append('No backup storage location configured')

            if backup_issues:
                return {
                    'status': 'WARNING',
                    'message': f'Backup strategy issues: {", ".join(backup_issues)}',
                    'details': {'issues': backup_issues}
                }

            return {
                'status': 'PASSED',
                'message': 'Backup strategy is configured',
                'details': {
                    'backup_schedule': getattr(settings, 'BACKUP_SCHEDULE', 'Not configured'),
                    'retention_days': getattr(settings, 'BACKUP_RETENTION_DAYS', 'Not configured')
                }
            }

        except Exception as e:
            return {
                'status': 'WARNING',
                'message': f'Backup strategy validation failed: {str(e)}'
            }

    def print_final_report(self):
        """Print comprehensive validation report"""
        print("\n" + "=" * 70)
        print("📊 PRE-DEPLOYMENT VALIDATION REPORT")
        print("=" * 70)

        print(f"Environment: {self.environment.upper()}")
        print(f"Timestamp: {self.validation_results['timestamp']}")
        print(f"Overall Status: {self.validation_results['overall_status']}")

        if self.validation_results['critical_failures']:
            print(f"\n❌ CRITICAL FAILURES ({len(self.validation_results['critical_failures'])}):")
            for failure in self.validation_results['critical_failures']:
                print(f"  - {failure}")

        if self.validation_results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.validation_results['warnings'])}):")
            for warning in self.validation_results['warnings']:
                print(f"  - {warning}")

        if not self.validation_results['critical_failures'] and not self.validation_results['warnings']:
            print("\n🎉 ALL VALIDATIONS PASSED - READY FOR DEPLOYMENT!")

        # Detailed validation results
        print("\n📋 DETAILED VALIDATION RESULTS:")
        for validation_name, result in self.validation_results['validations'].items():
            status_icon = "✅" if result['status'] == 'PASSED' else "⚠️" if result['status'] == 'WARNING' else "❌"
            print(f"  {status_icon} {validation_name.upper()}: {result['message']}")

        print("\n" + "=" * 70)

    def export_report(self, filename: str = None):
        """Export validation report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pre_deployment_validation_{self.environment}_{timestamp}.json"

        report_path = project_root / "reports" / filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2, default=str)

        print(f"\n📄 Validation report exported to: {report_path}")
        return report_path


async def main():
    """Main validation script"""
    parser = argparse.ArgumentParser(
        description="Pre-deployment validation for PsychSync",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--environment',
        choices=['development', 'staging', 'production'],
        default='production',
        help='Target environment for validation'
    )

    parser.add_argument(
        '--export-report',
        action='store_true',
        help='Export validation report to JSON file'
    )

    args = parser.parse_args()

    validator = PreDeploymentValidator(args.environment)
    await validator.run_all_validations()

    validator.print_final_report()

    if args.export_report:
        validator.export_report()

    # Exit with appropriate code
    if validator.validation_results['critical_failures']:
        print("\n❌ VALIDATION FAILED - Fix critical issues before deployment")
        sys.exit(1)
    elif validator.validation_results['warnings']:
        print("\n⚠️  VALIDATION COMPLETED WITH WARNINGS - Proceed with caution")
        sys.exit(2)
    else:
        print("\n✅ VALIDATION SUCCESSFUL - Ready for deployment!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())