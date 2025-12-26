#!/usr/bin/env python3
"""
Dependency Validation Script
Checks if all required dependencies are available
"""

import sys
import subprocess
from typing import List, Dict, Tuple

class DependencyValidator:
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []

    def check_python_packages(self) -> Dict[str, bool]:
        """Check Python package availability"""
        packages = {
            'fastapi': 'FastAPI framework',
            'sqlalchemy': 'Database ORM',
            'pydantic': 'Data validation',
            'passlib': 'Password hashing',
            'python-jose': 'JWT handling',
            'redis': 'Redis caching',
            'psycopg2': 'PostgreSQL adapter',
            'pytest': 'Testing framework',
            'uvicorn': 'ASGI server'
        }

        results = {}
        for package, description in packages.items():
            try:
                if package == 'python-jose':
                    import jose
                elif package == 'psycopg2':
                    import psycopg2
                else:
                    __import__(package)
                results[package] = True
                print(f"✓ {package} - {description}")
            except ImportError:
                results[package] = False
                print(f"✗ {package} - {description} (MISSING)")

        return results

    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        version_info = sys.version_info
        if version_info.major >= 3 and version_info.minor >= 8:
            print(f"✓ Python {version_info.major}.{version_info.minor}.{version_info.micro} (compatible)")
            return True
        else:
            print(f"✗ Python {version_info.major}.{version_info.minor}.{version_info.micro} (requires 3.8+)")
            return False

    def check_project_structure(self) -> Dict[str, bool]:
        """Check if project structure is correct"""
        required_dirs = [
            'app',
            'app/core',
            'app/api',
            'app/db',
            'app/services',
            'ai/processors',
            'frontend'
        ]

        results = {}
        import os
        for directory in required_dirs:
            if os.path.exists(directory):
                results[directory] = True
                print(f"✓ {directory} (exists)")
            else:
                results[directory] = False
                print(f"✗ {directory} (missing)")

        return results

    def check_config_files(self) -> Dict[str, bool]:
        """Check for configuration files"""
        config_files = [
            'requirements.txt',
            '.env.dev',
            '.gitignore',
            'README.md'
        ]

        results = {}
        import os
        for config_file in config_files:
            if os.path.exists(config_file):
                results[config_file] = True
                print(f"✓ {config_file} (exists)")
            else:
                results[config_file] = False
                print(f"✗ {config_file} (missing)")

        return results

    def check_database_setup(self) -> bool:
        """Check if database setup files exist"""
        import os
        db_files = [
            'alembic.ini',
            'alembic/env.py',
            'alembic/versions'
        ]

        all_exist = True
        for db_file in db_files:
            if os.path.exists(db_file):
                print(f"✓ {db_file} (exists)")
            else:
                print(f"✗ {db_file} (missing)")
                all_exist = False

        return all_exist

    def run_validation(self):
        """Run complete dependency validation"""
        print("🔍 DEPENDENCY VALIDATION REPORT")
        print("=" * 50)

        # Check Python version
        print("\n🐍 Python Version:")
        python_ok = self.check_python_version()

        # Check package dependencies
        print("\n📦 Python Packages:")
        package_results = self.check_python_packages()

        # Check project structure
        print("\n📁 Project Structure:")
        structure_results = self.check_project_structure()

        # Check configuration files
        print("\n⚙️ Configuration Files:")
        config_results = self.check_config_files()

        # Check database setup
        print("\n🗄️ Database Setup:")
        db_ok = self.check_database_setup()

        # Summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)

        total_packages = len(package_results)
        available_packages = sum(package_results.values())
        missing_packages = total_packages - available_packages

        total_dirs = len(structure_results)
        existing_dirs = sum(structure_results.values())

        total_configs = len(config_results)
        existing_configs = sum(config_results.values())

        print(f"Python Version: {'✅' if python_ok else '❌'}")
        print(f"Packages: {available_packages}/{total_packages} available")
        print(f"Directory Structure: {existing_dirs}/{total_dirs} present")
        print(f"Config Files: {existing_configs}/{total_configs} present")
        print(f"Database Setup: {'✅' if db_ok else '❌'}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")

        if not python_ok:
            print("🔄 Upgrade Python to version 3.8 or higher")

        if missing_packages > 0:
            missing_list = [pkg for pkg, available in package_results.items() if not available]
            print(f"📦 Install missing packages: pip install {' '.join(missing_list)}")

        if existing_dirs < total_dirs:
            print("📁 Ensure complete project structure is present")

        if existing_configs < total_configs:
            print("⚙️ Set up missing configuration files")

        if not db_ok:
            print("🗄️ Complete database setup with Alembic")

        # Overall readiness
        overall_score = sum([
            python_ok,
            available_packages / total_packages,
            existing_dirs / total_dirs,
            existing_configs / total_configs,
            db_ok
        ]) / 5 * 100

        print(f"\n🏆 OVERALL READINESS: {overall_score:.1f}%")

        if overall_score >= 90:
            print("🌟 Excellent - Ready for development!")
        elif overall_score >= 75:
            print("✅ Good - Minor setup needed")
        elif overall_score >= 50:
            print("⚠️ Fair - Significant setup required")
        else:
            print("❌ Poor - Major setup needed")

        return overall_score

if __name__ == "__main__":
    validator = DependencyValidator()
    validator.run_validation()