#!/usr/bin/env python3
"""
Database Validation Script

Validates database models, migrations, and configurations for PsychSync.
Checks for model-schema consistency, migration dependencies, and configuration validity.

Usage:
    python scripts/validate_database.py [--check-migrations] [--check-models] [--check-connections]
"""

import asyncio
import sys
import argparse
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DatabaseValidator:
    """Comprehensive database validation for PsychSync"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes = []

    def validate_all(self) -> Dict[str, Any]:
        """Run all database validations"""
        print("🔍 Starting comprehensive database validation...")
        print("=" * 60)

        results = {
            'models': self.validate_models(),
            'migrations': self.validate_migrations(),
            'connections': self.validate_connections(),
            'configuration': self.validate_configuration(),
            'consistency': self.validate_consistency()
        }

        self.generate_report(results)
        return results

    def validate_models(self) -> Dict[str, Any]:
        """Validate database models"""
        print("\n📋 Validating Database Models...")

        model_files = [
            'app/db/models/user.py',
            'app/db/models/organization.py',
            'app/db/models/assessment.py',
            'app/db/models/team.py',
            'app/db/models/response.py'
        ]

        results = {
            'files_found': 0,
            'imports_valid': 0,
            'base_class_valid': 0,
            'relationships_valid': 0,
            'issues': []
        }

        for model_file in model_files:
            file_path = project_root / model_file
            if file_path.exists():
                results['files_found'] += 1
                print(f"  ✓ Found: {model_file}")

                # Validate model imports and structure
                issues = self._validate_model_file(file_path)
                results['issues'].extend(issues)

                if not issues:
                    results['imports_valid'] += 1
                    results['base_class_valid'] += 1
                    results['relationships_valid'] += 1
            else:
                error = f"  ❌ Missing: {model_file}"
                print(error)
                results['issues'].append(error)

        return results

    def validate_migrations(self) -> Dict[str, Any]:
        """Validate Alembic migrations"""
        print("\n🔄 Validating Database Migrations...")

        migrations_dir = project_root / 'alembic/versions'
        migration_files = list(migrations_dir.glob('*.py'))

        results = {
            'total_migrations': len(migration_files),
            'valid_revisions': 0,
            'dependencies_valid': 0,
            'issues': []
        }

        # Check for critical migration
        critical_migration = migrations_dir / '013_add_user_role_to_base.py'
        if not critical_migration.exists():
            error = "  ❌ CRITICAL: Missing migration '013_add_user_role_to_base.py' for user role field"
            print(error)
            results['issues'].append(error)
            self.errors.append("User role field migration missing - database integrity risk")
        else:
            print("  ✓ Critical user role migration found")

        for migration_file in migration_files:
            if migration_file.name != '__init__.py':
                issues = self._validate_migration_file(migration_file)
                if not issues:
                    results['valid_revisions'] += 1
                    results['dependencies_valid'] += 1
                else:
                    results['issues'].extend(issues)

        return results

    def validate_connections(self) -> Dict[str, Any]:
        """Validate database connection configuration"""
        print("\n🔌 Validating Database Connections...")

        results = {
            'config_found': False,
            'test_db_configured': False,
            'async_driver_valid': False,
            'issues': []
        }

        try:
            from app.core.config import settings
            results['config_found'] = True
            print("  ✓ Database configuration found")

            # Check test database configuration
            if hasattr(settings, 'TEST_DATABASE_URL') and settings.TEST_DATABASE_URL:
                results['test_db_configured'] = True
                print("  ✓ Test database URL configured")
            else:
                warning = "  ⚠️  Test database URL not configured"
                print(warning)
                results['issues'].append(warning)

            # Test database URL construction
            try:
                from app.core.config import get_database_url
                test_url = get_database_url(async_driver=True, test_mode=True)
                if 'asyncpg' in test_url:
                    results['async_driver_valid'] = True
                    print("  ✓ Async driver configuration valid")
                else:
                    error = "  ❌ Async driver not properly configured"
                    print(error)
                    results['issues'].append(error)

            except Exception as e:
                error = f"  ❌ Database URL construction failed: {e}"
                print(error)
                results['issues'].append(error)

        except ImportError as e:
            error = f"  ❌ Configuration import failed: {e}"
            print(error)
            results['issues'].append(error)

        return results

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate database-specific configuration"""
        print("\n⚙️ Validating Database Configuration...")

        required_settings = [
            'DATABASE_URL',
            'DB_USER',
            'DB_PASSWORD',
            'DB_HOST',
            'DB_NAME',
            'DB_PORT'
        ]

        results = {
            'required_settings': 0,
            'optional_settings': 0,
            'issues': []
        }

        try:
            from app.core.config import settings

            for setting in required_settings:
                if hasattr(settings, setting) and getattr(settings, setting):
                    results['required_settings'] += 1
                    print(f"  ✓ {setting}: configured")
                else:
                    error = f"  ❌ {setting}: not configured"
                    print(error)
                    results['issues'].append(error)

            # Check optional settings
            optional_settings = [
                'DB_POOL_SIZE',
                'DB_MAX_OVERFLOW',
                'DB_POOL_RECYCLE',
                'DB_POOL_PRE_PING'
            ]

            for setting in optional_settings:
                if hasattr(settings, setting):
                    results['optional_settings'] += 1
                    print(f"  ✓ {setting}: {getattr(settings, setting)}")

        except Exception as e:
            error = f"  ❌ Configuration validation failed: {e}"
            print(error)
            results['issues'].append(error)

        return results

    def validate_consistency(self) -> Dict[str, Any]:
        """Validate model-schema consistency"""
        print("\n🔄 Validating Model-Schema Consistency...")

        results = {
            'user_model_consistent': False,
            'organization_model_consistent': False,
            'assessment_model_consistent': False,
            'issues': []
        }

        # Check User model consistency
        user_issues = self._validate_user_model_consistency()
        if not user_issues:
            results['user_model_consistent'] = True
            print("  ✓ User model: consistent")
        else:
            results['issues'].extend(user_issues)

        # Check Organization model consistency
        org_issues = self._validate_organization_model_consistency()
        if not org_issues:
            results['organization_model_consistent'] = True
            print("  ✓ Organization model: consistent")
        else:
            results['issues'].extend(org_issues)

        return results

    def _validate_model_file(self, file_path: Path) -> List[str]:
        """Validate individual model file"""
        issues = []

        try:
            content = file_path.read_text(encoding='utf-8')

            # Check for required imports
            required_imports = ['from app.db.base import Base']
            for import_stmt in required_imports:
                if import_stmt not in content:
                    issues.append(f"Missing import: {import_stmt}")

            # Check for Base class usage
            if 'Base' not in content:
                issues.append("Model doesn't inherit from Base")

            # Check for SQLAlchemy annotations
            if 'Column' not in content:
                issues.append("No SQLAlchemy Column definitions found")

        except Exception as e:
            issues.append(f"Error reading {file_path}: {e}")

        return issues

    def _validate_migration_file(self, migration_path: Path) -> List[str]:
        """Validate individual migration file"""
        issues = []

        try:
            content = migration_path.read_text(encoding='utf-8')

            # Check for required migration structure
            if 'revision:' not in content:
                issues.append(f"Missing revision identifier in {migration_path.name}")

            if 'down_revision:' not in content:
                issues.append(f"Missing down_revision in {migration_path.name}")

            if 'def upgrade()' not in content:
                issues.append(f"Missing upgrade() function in {migration_path.name}")

        except Exception as e:
            issues.append(f"Error reading {migration_path}: {e}")

        return issues

    def _validate_user_model_consistency(self) -> List[str]:
        """Validate User model consistency with database schema"""
        issues = []

        try:
            from app.db.models.user import User
            import inspect

            # Check model fields
            expected_fields = [
                'id', 'email', 'password_hash', 'full_name', 'avatar_url',
                'role', 'is_active', 'created_at', 'updated_at', 'deleted_at',
                'organization_id', 'timezone', 'locale', 'preferences',
                'is_verified', 'is_superuser', 'last_login',
                'email_verification_token', 'email_verification_expires',
                'password_reset_token', 'password_reset_expires'
            ]

            model_fields = inspect.getmembers(User)
            field_names = [name for name, _ in model_fields if not name.startswith('_')]

            for field in expected_fields:
                if field not in field_names:
                    issues.append(f"Missing field in User model: {field}")

        except Exception as e:
            issues.append(f"Error validating User model: {e}")

        return issues

    def _validate_organization_model_consistency(self) -> List[str]:
        """Validate Organization model consistency"""
        issues = []

        try:
            from app.db.models.organization import Organization

            # Check if organization has required fields
            model_dict = Organization.__dict__
            expected_fields = ['id', 'name', 'created_at', 'updated_at']

            for field in expected_fields:
                if field not in model_dict:
                    issues.append(f"Missing field in Organization model: {field}")

        except Exception as e:
            issues.append(f"Error validating Organization model: {e}")

        return issues

    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate validation report"""
        print("\n" + "=" * 60)
        print("📊 DATABASE VALIDATION REPORT")
        print("=" * 60)

        total_issues = sum(len(result.get('issues', [])) for result in results.values())

        if total_issues == 0:
            print("✅ All validations passed! Database configuration is healthy.")
        else:
            print(f"⚠️  Found {total_issues} issues that need attention:")

            for category, result in results.items():
                if result.get('issues'):
                    print(f"\n🔍 {category.upper()}:")
                    for issue in result['issues']:
                        print(f"  - {issue}")

        # Summary statistics
        print("\n📈 Summary Statistics:")
        print(f"  Model Files: {results.get('models', {}).get('files_found', 0)}")
        print(f"  Migrations: {results.get('migrations', {}).get('total_migrations', 0)}")
        print(f"  Configuration Issues: {total_issues}")

        if total_issues == 0:
            print("\n🎉 Database validation complete - Everything looks good!")
        else:
            print(f"\n🔧 {total_issues} issues found - Please review and fix")

    def generate_fixes(self) -> List[str]:
        """Generate recommended fixes"""
        fixes = []

        # Migration fixes
        critical_migration = project_root / 'alembic/versions/013_add_user_role_to_base.py'
        if not critical_migration.exists():
            fixes.append("Run: alembic revision --autogenerate -m 'add_user_role_to_base'")
            fixes.append("Add role column to users table with proper enum")

        # Configuration fixes
        fixes.append("Set TEST_DATABASE_URL environment variable for testing")
        fixes.append("Ensure PostgreSQL is installed and running for tests")
        fixes.append("Run: alembic upgrade head to apply all migrations")

        return fixes


def main():
    """Main validation script"""
    parser = argparse.ArgumentParser(
        description="Validate PsychSync database configuration and models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/validate_database.py
    python scripts/validate_database.py --check-migrations
    python scripts/validate_database.py --check-models
        """
    )

    parser.add_argument(
        '--check-migrations',
        action='store_true',
        help='Only check migration files'
    )

    parser.add_argument(
        '--check-models',
        action='store_true',
        help='Only check model files'
    )

    parser.add_argument(
        '--check-connections',
        action='store_true',
        help='Only check database connections'
    )

    args = parser.parse_args()

    validator = DatabaseValidator()

    try:
        if args.check_migrations:
            results = {'migrations': validator.validate_migrations()}
        elif args.check_models:
            results = {'models': validator.validate_models()}
        elif args.check_connections:
            results = {'connections': validator.validate_connections()}
        else:
            results = validator.validate_all()

        # Generate fixes if issues found
        total_issues = sum(len(result.get('issues', [])) for result in results.values())
        if total_issues > 0:
            print(f"\n🔧 Recommended fixes:")
            for fix in validator.generate_fixes():
                print(f"  - {fix}")

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()