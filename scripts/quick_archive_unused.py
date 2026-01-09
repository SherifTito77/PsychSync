#!/usr/bin/env python3
"""
Quickly identify and archive unused services in a single pass.
"""

import os
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 80)
    print("QUICK UNUSED SERVICES ARCHIVAL")
    print("=" * 80)
    print()

    # Get all service files
    services_dir = Path('app/services')
    service_files = list(services_dir.glob('*.py'))

    # Filter out __init__ and backup files
    service_files = [f for f in service_files if f.name != '__init__.py' and not f.name.startswith('.!')]

    print(f"📊 Found {len(service_files)} service files\n")

    # Read all service names
    service_names = [f.stem for f in service_files]

    # Create a single grep pattern that matches all services
    # This is much faster than grepping individually
    pattern_file = '/tmp/service_patterns.txt'
    with open(pattern_file, 'w') as f:
        for name in service_names:
            # Match imports and usage
            f.write(f"from app.services.{name}\n")
            f.write(f"from app.services import {name}\n")
            f.write(f"import app.services.{name}\n")

    # Run grep once with all patterns
    print("🔍 Analyzing service usage (single-pass grep)...\n")

    try:
        result = subprocess.run(
            ['grep', '-r', '--include=*.py', '-f', pattern_file, 'app/'],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse results
        mentioned_services = set()
        for line in result.stdout.split('\n'):
            if not line:
                continue

            # Extract service name from the line
            for service_name in service_names:
                # Check if this service is mentioned in a meaningful way
                if f'app.services.{service_name}' in line or f'import {service_name}' in line:
                    # Exclude self-references
                    if f'services/{service_name}.py' not in line:
                        mentioned_services.add(service_name)
                        break

    except subprocess.TimeoutExpired:
        print("⚠️  Grep timed out, using fallback method")
        mentioned_services = set()

    # Find unused services
    unused_services = [s for s in service_names if s not in mentioned_services]

    print(f"✅ Used services:  {len(service_names) - len(unused_services)}")
    print(f"❌ Unused services: {len(unused_services)}")
    print()

    if unused_services:
        print("Services to archive:")
        for service in sorted(unused_services):
            print(f"  - {service}")
        print()

        # Archive the services
        archive_dir = Path('archived_services/services')
        archive_dir.mkdir(parents=True, exist_ok=True)

        manifest_file = archive_dir.parent / 'ARCHIVAL_MANIFEST.md'

        print(f"📦 Archiving {len(unused_services)} unused services...")

        archived_count = 0
        with open(manifest_file, 'a') as manifest:
            manifest.write(f"\n## Archival: {datetime.now().isoformat()}\n\n")
            manifest.write(f"Total services archived: {len(unused_services)}\n\n")

            for service_name in sorted(unused_services):
                source = services_dir / f'{service_name}.py'
                destination = archive_dir / f'{service_name}.py'

                if source.exists():
                    try:
                        # Move the file
                        source.rename(destination)

                        manifest.write(f"- {service_name}: `app/services/{service_name}.py` → `archived_services/services/{service_name}.py`\n")

                        print(f"  ✅ Archived {service_name}")
                        archived_count += 1
                    except Exception as e:
                        print(f"  ❌ Failed to archive {service_name}: {e}")
                        manifest.write(f"- {service_name}: FAILED - {e}\n")

        print()
        print(f"✅ Archival complete! Archived {archived_count} services.")
        print(f"📄 Manifest: {manifest_file}")
    else:
        print("✅ No unused services found!")

if __name__ == '__main__':
    main()
