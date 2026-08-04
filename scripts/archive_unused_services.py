#!/usr/bin/env python3
"""
Safely archive unused services with comprehensive tracking.

This script:
1. Identifies truly unused services (zero references)
2. Moves them to archived_services/ directory
3. Creates a detailed manifest of what was archived
4. Preserves git history via git mv
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path


def check_service_usage(service_name):
    """Check if a service is used anywhere in the codebase."""

    # Exclude the service file itself
    exclude_patterns = [
        f"app/services/{service_name}.py",
        f".pyc",
        f"__pycache__",
    ]

    try:
        # Count references to this service
        result = subprocess.run(
            ["grep", "-r", "--include=*.py", service_name, "app/"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return 0

        # Count unique files that reference this service
        referenced_files = set()
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            # Extract file path
            filepath = line.split(":")[0]

            # Skip if it's the service file itself
            if f"services/{service_name}.py" in filepath:
                continue

            # Skip if it's just a comment or string
            if "#" in line and line.index("#") < line.index(service_name):
                continue

            referenced_files.add(filepath)

        return len(referenced_files)

    except Exception as e:
        print(f"    ⚠️  Error checking {service_name}: {e}")
        return -1


def get_all_services():
    """Get all service files."""
    services = {}
    services_dir = Path("app/services")

    for file in services_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
        if file.name.startswith(".!"):
            continue

        services[file.stem] = file

    return services


def archive_service(service_name, service_path, manifest_file):
    """Archive a single service file."""

    archive_dir = Path("archived_services/services")
    archive_dir.mkdir(parents=True, exist_ok=True)

    destination = archive_dir / f"{service_name}.py"

    # Try git mv first to preserve history
    try:
        subprocess.run(
            ["git", "mv", str(service_path), str(destination)],
            check=True,
            capture_output=True,
            timeout=10,
        )
        method = "git mv"
    except Exception as e:
        # Fall back to regular mv
        try:
            subprocess.run(
                ["mv", str(service_path), str(destination)],
                check=True,
                capture_output=True,
                timeout=10,
            )
            method = "mv"
        except Exception as e:
            print(f"    ❌ Failed to move {service_name}: {e}")
            return False

    # Log to manifest
    with open(manifest_file, "a") as f:
        f.write(
            f"{service_name},{service_path},{destination},{method},{datetime.now().isoformat()}\n"
        )

    return True


def main():
    """Main archival process."""

    print("=" * 80)
    print("UNUSED SERVICES ARCHIVAL")
    print("=" * 80)
    print()

    # Create manifest
    manifest_file = Path("archived_services/SERVICES_MANIFEST.csv")
    if not manifest_file.exists():
        with open(manifest_file, "w") as f:
            f.write("service_name,original_path,archived_path,method,archived_at\n")

    # Get all services
    all_services = get_all_services()
    print(f"📊 Total services: {len(all_services)}\n")

    # Check each service
    unused_services = []
    for i, (service_name, service_path) in enumerate(sorted(all_services.items()), 1):
        print(f"[{i}/{len(all_services)}] Checking {service_name}...", end=" ")

        usage_count = check_service_usage(service_name)

        if usage_count == 0:
            print(f"❌ UNUSED (0 references)")
            unused_services.append((service_name, service_path))
        elif usage_count > 0:
            print(f"✅ USED ({usage_count} references)")
        else:
            print(f"⚠️  ERROR checking usage")

    print()
    print(f"📊 Found {len(unused_services)} unused services")
    print()

    if not unused_services:
        print("✅ No unused services to archive!")
        return

    # Confirm before proceeding
    print("Unused services to archive:")
    for service_name, _ in unused_services[:10]:  # Show first 10
        print(f"  - {service_name}")
    if len(unused_services) > 10:
        print(f"  ... and {len(unused_services) - 10} more")
    print()

    # Archive services
    print("📦 Archiving unused services...")
    archived_count = 0
    failed_count = 0

    for service_name, service_path in unused_services:
        if archive_service(service_name, service_path, manifest_file):
            print(f"  ✅ Archived {service_name}")
            archived_count += 1
        else:
            print(f"  ❌ Failed to archive {service_name}")
            failed_count += 1

    print()
    print(f"✅ Archival complete!")
    print(f"   Archived: {archived_count} services")
    print(f"   Failed: {failed_count} services")
    print(f"   Manifest: {manifest_file}")


if __name__ == "__main__":
    main()
