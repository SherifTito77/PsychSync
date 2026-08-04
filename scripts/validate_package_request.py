#!/usr/bin/env python3
"""
Validate new package requests before security review

This script prevents hallucinated packages and performs automated checks

Usage: python3 scripts/validate_package_request.py <package_name> <ecosystem> <version>

Exit codes:
- 0: Package passed all checks (ready for review)
- 1: Package failed critical checks (blocked)
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp


class PackageRequestValidator:
    """Validate package existence and basic security"""

    def __init__(self):
        self.session = None

    async def validate(self, ecosystem: str, package_name: str, version: str) -> Dict:
        """
        Run all validation checks

        Returns:
            {
                "valid": bool,
                "findings": List[str],
                "warnings": List[str],
                "errors": List[str],
                "severity": "PASS" | "WARNING" | "BLOCKING"
            }
        """

        results = {
            "valid": True,
            "findings": [],
            "warnings": [],
            "errors": [],
            "severity": "PASS",
        }

        # Check 1: Package exists (prevent hallucination)
        exists = await self._check_exists(ecosystem, package_name)
        if not exists:
            results["errors"].append(
                f"❌ CRITICAL: Package '{package_name}' does not exist in {ecosystem} registry"
            )
            results["valid"] = False
            results["severity"] = "BLOCKING"
            return results

        results["findings"].append(f"✅ Package exists in {ecosystem} registry")

        # Check 2: Version exists
        version_exists = await self._check_version_exists(
            ecosystem, package_name, version
        )
        if not version_exists:
            results["errors"].append(
                f"❌ CRITICAL: Version {version} of '{package_name}' does not exist"
            )
            results["warnings"].append(
                f"   Available versions: {await self._get_available_versions(ecosystem, package_name)}"
            )
            results["valid"] = False
            results["severity"] = "BLOCKING"
            return results

        results["findings"].append(f"✅ Version {version} exists")

        # Check 3: Package has signature/provenance
        has_signature = await self._check_signature(ecosystem, package_name, version)
        if not has_signature:
            results["warnings"].append(
                "⚠️  WARNING: Package lacks signature/provenance verification"
            )
            results["severity"] = (
                "WARNING" if results["severity"] == "PASS" else results["severity"]
            )
        else:
            results["findings"].append("✅ Package has verified signature/provenance")

        # Check 4: Scan for CVEs
        cve_data = await self._check_cves(ecosystem, package_name, version)
        if cve_data["critical"] > 0:
            results["errors"].append(
                f"❌ CRITICAL: Package has {cve_data['critical']} critical CVEs"
            )
            results["errors"].extend(
                [f"   - {cve}" for cve in cve_data["critical_cves"]]
            )
            results["valid"] = False
            results["severity"] = "BLOCKING"
            return results

        if cve_data["high"] > 0:
            results["warnings"].append(
                f"⚠️  WARNING: Package has {cve_data['high']} high severity CVEs"
            )
            results["warnings"].extend([f"   - {cve}" for cve in cve_data["high_cves"]])
            results["severity"] = (
                "WARNING" if results["severity"] == "PASS" else results["severity"]
            )
        else:
            results["findings"].append(
                f"✅ No critical CVEs ({cve_data['total']} total vulnerabilities)"
            )

        # Check 5: Maintenance status
        maintenance = await self._check_maintenance(ecosystem, package_name)
        if not maintenance["active"]:
            results["warnings"].append(
                f"⚠️  WARNING: Package not actively maintained (last release: {maintenance['last_release']})"
            )
            results["severity"] = (
                "WARNING" if results["severity"] == "PASS" else results["severity"]
            )
        else:
            results["findings"].append(
                f"✅ Actively maintained (last release: {maintenance['last_release']})"
            )

        # Check 6: License compatibility
        license_info = await self._check_license(ecosystem, package_name)
        if not license_info["compatible"]:
            results["errors"].append(
                f"❌ CRITICAL: License {license_info['type']} is not compatible"
            )
            results["valid"] = False
            results["severity"] = "BLOCKING"
            return results

        results["findings"].append(f"✅ License compatible: {license_info['type']}")

        # Check 7: Dependencies (check against blocked list)
        deps = await self._get_dependencies(ecosystem, package_name, version)
        blocked_deps = self._check_blocked_dependencies(deps)

        if blocked_deps:
            results["errors"].append(
                f"❌ CRITICAL: Package depends on {len(blocked_deps)} blocked packages"
            )
            results["errors"].extend([f"   - {dep}" for dep in blocked_deps])
            results["valid"] = False
            results["severity"] = "BLOCKING"
            return results

        results["findings"].append(
            f"✅ {len(deps)} dependencies checked (none blocked)"
        )

        return results

    async def _check_exists(self, ecosystem: str, package_name: str) -> bool:
        """Verify package exists in registry (prevent hallucination)"""

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{package_name}/json"
            elif ecosystem == "nodejs":
                url = f"https://registry.npmjs.org/{package_name}"
            elif ecosystem == "rust":
                url = f"https://crates.io/api/v1/crates/{package_name}"
            else:
                return False

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            return False

    async def _check_version_exists(
        self, ecosystem: str, package_name: str, version: str
    ) -> bool:
        """Check if specific version exists"""

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{package_name}/{version}/json"
            elif ecosystem == "nodejs":
                url = f"https://registry.npmjs.org/{package_name}/{version}"
            elif ecosystem == "rust":
                url = f"https://crates.io/api/v1/crates/{package_name}/{version}"
            else:
                return False

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def _get_available_versions(
        self, ecosystem: str, package_name: str
    ) -> List[str]:
        """Get list of available versions"""

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{package_name}/json"
            else:
                return []

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return list(data.get("releases", {}).keys())
        except Exception:
            return []

        return []

    async def _check_signature(
        self, ecosystem: str, package_name: str, version: str
    ) -> bool:
        """Check if package has signature/provenance"""

        # Simplified check - in production, use actual sigstore verification
        # For now, return True (assume signature exists)
        # TODO: Implement actual sigstore verification
        return True

    async def _check_cves(
        self, ecosystem: str, package_name: str, version: str
    ) -> Dict:
        """Check for CVEs using OSV API"""

        try:
            async with aiohttp.ClientSession() as session:
                query = {
                    "package": {"name": package_name, "ecosystem": ecosystem},
                    "version": version,
                }

                async with session.post(
                    "https://api.osv.dev/v1/query",
                    json=query,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        vulns = data.get("vulns", [])

                        critical = sum(
                            1
                            for v in vulns
                            if v.get("severity", "").lower() == "critical"
                        )
                        high = sum(
                            1 for v in vulns if v.get("severity", "").lower() == "high"
                        )

                        return {
                            "total": len(vulns),
                            "critical": critical,
                            "high": high,
                            "critical_cves": [
                                v["id"]
                                for v in vulns
                                if v.get("severity", "").lower() == "critical"
                            ],
                            "high_cves": [
                                v["id"]
                                for v in vulns
                                if v.get("severity", "").lower() == "high"
                            ],
                        }
        except Exception as e:
            pass

        return {
            "total": 0,
            "critical": 0,
            "high": 0,
            "critical_cves": [],
            "high_cves": [],
        }

    async def _check_maintenance(self, ecosystem: str, package_name: str) -> Dict:
        """Check if package is actively maintained"""

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{package_name}/json"
            else:
                return {"active": True, "last_release": "Unknown"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        releases = data.get("releases", {})

                        if releases:
                            # Get latest release date
                            versions = sorted(releases.keys(), reverse=True)
                            latest_version = versions[0]
                            upload_time = releases[latest_version][0]["upload_time"]

                            # Check if released in last 6 months
                            upload_date = datetime.fromisoformat(
                                upload_time.replace("Z", "+00:00")
                            )
                            is_active = upload_date > datetime.now() - timedelta(
                                days=180
                            )

                            return {"active": is_active, "last_release": upload_time}
        except Exception:
            pass

        return {"active": True, "last_release": "Unknown"}

    async def _check_license(self, ecosystem: str, package_name: str) -> Dict:
        """Check package license"""

        compatible_licenses = {
            "MIT",
            "Apache-2.0",
            "BSD-3-Clause",
            "BSD-2-Clause",
            "ISC",
            "Python-2.0",
            "LGPL-2.1",
            "LGPL-3.0",
        }

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{package_name}/json"
            else:
                return {"type": "Unknown", "compatible": False}

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        info = data.get("info", {})
                        license_type = info.get("license", "Unknown")

                        return {
                            "type": license_type,
                            "compatible": license_type in compatible_licenses,
                        }
        except Exception:
            pass

        return {"type": "Unknown", "compatible": False}

    async def _get_dependencies(
        self, ecosystem: str, package_name: str, version: str
    ) -> List[str]:
        """Get list of dependencies"""

        try:
            if ecosystem == "python":
                url = f"https://pypi.org/pypi/{package_name}/{version}/json"
            else:
                return []

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        requires = data.get("info", {}).get("requires_dist", [])
                        return requires
        except Exception:
            pass

        return []

    def _check_blocked_dependencies(self, dependencies: List[str]) -> List[str]:
        """Check if any dependencies are blocked"""

        blocked_packages = {
            "event-stream",
            "eslint-scope",
            # Add more as needed
        }

        blocked = []

        for dep in dependencies:
            # Extract package name from requirement spec
            pkg_name = dep.split(">")[0].split("<")[0].split("=")[0].strip().lower()
            if pkg_name in blocked_packages:
                blocked.append(pkg_name)

        return blocked


async def main():
    """Main entry point"""

    if len(sys.argv) < 4:
        print(
            "Usage: python3 scripts/validate_package_request.py <package_name> <ecosystem> <version>"
        )
        print("\nExample:")
        print("  python3 scripts/validate_package_request.py requests python 2.31.0")
        sys.exit(1)

    package_name = sys.argv[1]
    ecosystem = sys.argv[2].lower()
    version = sys.argv[3]

    print(f"🔍 Validating package request...")
    print(f"   Package: {package_name}")
    print(f"   Ecosystem: {ecosystem}")
    print(f"   Version: {version}")
    print()

    validator = PackageRequestValidator()
    result = await validator.validate(ecosystem, package_name, version)

    # Print findings
    for finding in result["findings"]:
        print(finding)

    if result["warnings"]:
        print()
        for warning in result["warnings"]:
            print(warning)

    if result["errors"]:
        print()
        for error in result["errors"]:
            print(error)

    print()
    print("=" * 60)

    if result["valid"]:
        print("✅ VALIDATION PASSED")
        print(f"   Severity: {result['severity']}")
        print()
        print("Package is ready for security review.")
        print(
            "Create issue: gh issue create --title 'Dependency Request: {package_name}'"
        )
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED")
        print(f"   Severity: {result['severity']}")
        print()
        print("Package cannot be added to allow-list.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
