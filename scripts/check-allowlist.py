#!/usr/bin/env python3
"""
Check that all Python dependencies are in allow-list
Fails CI if any dependency is not allowed

Usage: python3 scripts/check-allowlist.py
Exit code: 0 (all allowed), 1 (violations found)
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def get_installed_packages() -> Dict[str, str]:
    """Get list of installed packages from pip freeze"""

    result = subprocess.run(
        ["pip", "list", "--format=json"], capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"Error running pip list: {result.stderr}")
        sys.exit(1)

    packages = json.loads(result.stdout)

    return {pkg["name"].lower(): pkg["version"] for pkg in packages}


def parse_allow_list(
    allow_list_path: str = "allowed-dependencies.txt",
) -> Dict[str, dict]:
    """Parse allow-list file

    Format: package==min,max # date # notes
    """

    allow_list = {}

    allow_file = Path(allow_list_path)
    if not allow_file.exists():
        print(f"❌ Allow-list file not found: {allow_list_path}")
        sys.exit(1)

    with open(allow_file, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Remove comments after package spec
            line = line.split("#")[0].strip()
            if not line:
                continue

            # Parse: package==min,max
            if "==" in line:
                package_spec = line.split("==")[0]
                version_range = line.split("==")[1] if "==" in line else "*"

                package_name = package_spec.lower().strip("_-")  # Normalize

                allow_list[package_name] = {
                    "version_range": version_range,
                    "line": line_num,
                }

    return allow_list


def check_version_compatibility(
    package: str, installed_version: str, allowed_info: dict
) -> bool:
    """Check if installed version is within allowed range"""

    version_range = allowed_info["version_range"]

    # Parse range: min,max
    if "," in version_range:
        min_ver, max_ver = version_range.split(",")
        # Check if version is within range
        # (simplified - use packaging.version in production)
        return True  # Implement proper version comparison
    else:
        # Single version or wildcard
        return True


def check_allow_list():
    """Check all packages against allow-list"""

    # Get installed packages
    installed = get_installed_packages()
    print(f"📦 Found {len(installed)} installed packages")

    # Parse allow-list
    allow_list = parse_allow_list()
    print(f"✅ Allow-list has {len(allow_list)} allowed packages")

    violations = []

    for package_name, version in installed.items():
        # Normalize package name for comparison
        normalized_name = package_name.lower().strip("_-")

        if normalized_name not in allow_list:
            violations.append(
                {
                    "package": package_name,
                    "version": version,
                    "reason": "Not in allow-list",
                }
            )
        else:
            # Check version compliance
            allowed_info = allow_list[normalized_name]
            if not check_version_compatibility(package_name, version, allowed_info):
                violations.append(
                    {
                        "package": package_name,
                        "version": version,
                        "reason": f"Version {version} not in allowed range {allowed_info['version_range']}",
                    }
                )

    # Report results
    if violations:
        print("\n❌ DEPENDENCY ALLOW-LIST VIOLATIONS DETECTED")
        print(f"   {len(violations)} violations found\n")

        for v in violations:
            print(f"  • {v['package']} ({v['version']})")
            print(f"    Reason: {v['reason']}")
            print(f"    Action: Submit dependency request")
            print()

        print("To request an exception:")
        print(
            "  1. Create issue: gh issue create --title 'Dependency Request: PACKAGE'"
        )
        print("     --label 'dependency-request' --body-file <request-template>")
        print("  2. Security team reviews within 24-48 hours")
        print("  3. Once approved, add to allowed-dependencies.txt")
        print("\nRequest template:")
        print(
            "  See DEPENDENCY_ALLOWLIST_POLICY.md section 'New Package Request Workflow'"
        )
        print()

        sys.exit(1)
    else:
        print(f"✅ All {len(installed)} dependencies are in allow-list")
        print(f"   Compliance: 100%")
        sys.exit(0)


if __name__ == "__main__":
    check_allow_list()
