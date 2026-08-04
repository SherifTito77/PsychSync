#!/usr/bin/env python3
"""
Accurate service usage analysis using grep and string matching.

This catches both module-level and inline imports.
"""

import os
import subprocess
from collections import defaultdict
from pathlib import Path


def get_service_files():
    """Get all service files."""
    service_files = {}
    services_dir = Path("app/services")

    if not services_dir.exists():
        return service_files

    for file in services_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
        if file.name.startswith(".!"):  # Emergency/backup files
            continue

        service_name = file.stem
        service_files[service_name] = str(file)

    return service_files


def check_service_usage(service_name):
    """Check if a service is used anywhere in the codebase."""

    # Various import patterns to check
    patterns = [
        f"from app.services import {service_name}",
        f"from app.services.{service_name}",
        f"import app.services.{service_name}",
        f"services.{service_name}",
    ]

    # Also check for class/function usage
    # e.g., user_service.UserService() or auth_service.blacklist_token()

    usage_count = 0
    usage_files = set()

    for pattern in patterns:
        try:
            result = subprocess.run(
                ["grep", "-r", "--include=*.py", pattern, "app/"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line:
                        usage_count += 1
                        filepath = line.split(":")[0]
                        usage_files.add(filepath)
        except Exception as e:
            pass

    # Also check for direct service name usage (more permissive)
    try:
        result = subprocess.run(
            ["grep", "-r", "--include=*.py", "-w", service_name, "app/"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if line and service_name in line:
                    # Filter out false positives
                    if "import" in line or "from" in line or service_name + "." in line:
                        usage_count += 1
                        filepath = line.split(":")[0]
                        usage_files.add(filepath)
    except Exception as e:
        pass

    return usage_count, list(usage_files)


def analyze_services():
    """Analyze all services for usage."""

    print("🔍 Analyzing service usage (accurate method)...\n")

    service_files = get_service_files()
    print(f"📊 Found {len(service_files)} service files\n")

    used_services = {}
    unused_services = {}

    for i, service_name in enumerate(sorted(service_files.keys()), 1):
        print(f"   [{i}/{len(service_files)}] Checking {service_name}...", end=" ")
        usage_count, usage_files = check_service_usage(service_name)

        if usage_count > 0:
            used_services[service_name] = {
                "path": service_files[service_name],
                "usage_count": usage_count,
                "used_in": usage_files,
            }
            print(f"✅ USED ({usage_count} times)")
        else:
            unused_services[service_name] = {"path": service_files[service_name]}
            print(f"❌ UNUSED")

    return {
        "used": used_services,
        "unused": unused_services,
        "total": len(service_files),
        "used_count": len(used_services),
        "unused_count": len(unused_services),
    }


def print_results(results):
    """Print analysis results."""

    print("\n" + "=" * 80)
    print("SERVICE USAGE ANALYSIS RESULTS (ACCURATE)")
    print("=" * 80)
    print()

    print(f"📊 SUMMARY")
    print(f"   Total Services: {results['total']}")
    print(
        f"   Used Services:  {results['used_count']} ({100*results['used_count']//results['total']}%)"
    )
    print(
        f"   Unused Services: {results['unused_count']} ({100*results['unused_count']//results['total']}%)"
    )
    print()

    if results["used"]:
        print(f"✅ USED SERVICES ({results['used_count']})")
        for service, info in sorted(
            results["used"].items(), key=lambda x: x[1]["usage_count"], reverse=True
        ):
            print(f"   - {service:40} ({info['usage_count']:3} usages)")
        print()

    if results["unused"]:
        print(f"❌ UNUSED SERVICES ({results['unused_count']}) - CAN BE ARCHIVED")
        for service in sorted(results["unused"].keys()):
            print(f"   - {service}")
        print()


if __name__ == "__main__":
    results = analyze_services()
    print_results(results)
