#!/usr/bin/env python3
"""
Simple verification script for clinical screening endpoints
Checks that endpoints are registered and accessible
"""

import json
import sys


def check_openapi():
    """Check if screening endpoints are in OpenAPI spec"""
    import urllib.request

    print("1. Checking OpenAPI specification...")

    try:
        with urllib.request.urlopen("http://localhost:8000/openapi.json", timeout=5) as response:
            spec = json.loads(response.read())

        paths = spec.get("paths", {})

        # Check for screening endpoints
        screening_endpoints = {
            "/api/v1/screening/consent": "POST",
            "/api/v1/screening/phq9": "POST",
            "/api/v1/screening/gad7": "POST",
            "/api/v1/screening/cssrs": "POST",
        }

        found = {}
        for path, method in screening_endpoints.items():
            if path in paths:
                if method.lower() in paths[path]:
                    found[path] = "✅"
                    print(f"  ✅ {path} ({method})")
                else:
                    found[path] = "⚠️"
                    print(f"  ⚠️  {path} exists but {method} not found")
            else:
                found[path] = "❌"
                print(f"  ❌ {path} not found")

        all_ok = all(v == "✅" for v in found.values())
        print(f"\nResult: {'✅ All endpoints found' if all_ok else '⚠️ Some endpoints missing'}")
        return all_ok

    except Exception as e:
        print(f"  ❌ Failed to fetch OpenAPI: {e}")
        return False


def check_database_tables():
    """Check if clinical tables exist"""
    import subprocess

    print("\n2. Checking database tables...")

    try:
        result = subprocess.run(
            ["psql", "-d", "psychsync", "-c", "\\dt clinical_*"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            tables = [
                "clinical_screenings",
                "clinical_alerts",
                "clinical_referrals",
                "clinical_audit_logs",
                "clinical_consents"
            ]

            output = result.stdout
            found = []
            for table in tables:
                if table in output:
                    found.append(table)
                    print(f"  ✅ {table}")
                else:
                    print(f"  ❌ {table}")

            all_ok = len(found) == len(tables)
            print(f"\nResult: {f'✅ All {len(found)} tables found' if all_ok else f'⚠️ Only {len(found)}/{len(tables)} tables found'}")
            return all_ok
        else:
            print(f"  ❌ Database query failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to check database: {e}")
        return False


def check_module_imports():
    """Check if modules can be imported"""
    print("\n3. Checking module imports...")

    modules = [
        ("app.services.clinical.scoring_algorithms", ["PHQ9Scorer", "GAD7Scorer", "CSSRSScorer"]),
        ("app.services.clinical.crisis_intervention", ["CrisisInterventionService"]),
        ("app.api.v1.endpoints.screening", ["router"]),
    ]

    all_ok = True
    for module_name, items in modules:
        try:
            module = __import__(module_name, fromlist=items)
            found = []
            for item in items:
                if hasattr(module, item):
                    found.append(item)
                    print(f"  ✅ {module_name}.{item}")
                else:
                    print(f"  ❌ {module_name}.{item} not found")
                    all_ok = False

            if len(found) == len(items):
                print(f"    ✓ All {len(items)} items imported")

        except ImportError as e:
            print(f"  ❌ Failed to import {module_name}: {e}")
            all_ok = False

    print(f"\nResult: {'✅ All modules imported' if all_ok else '⚠️ Some imports failed'}")
    return all_ok


def check_endpoint_responses():
    """Check if endpoints respond (even with auth errors)"""
    import urllib.request

    print("\n4. Checking endpoint accessibility...")

    endpoints = [
        "/api/v1/screening/consent",
        "/api/v1/screening/phq9",
        "/api/v1/screening/gad7",
        "/api/v1/screening/cssrs",
    ]

    accessible = 0
    for endpoint in endpoints:
        try:
            # Create a POST request (without auth, will fail but we check if route exists)
            req = urllib.request.Request(
                f"http://localhost:8000{endpoint}",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=3) as response:
                # We expect 401 (unauthorized) or 422 (validation error), not 404
                status = response.status

                if status == 404:
                    print(f"  ❌ {endpoint} - Not found (404)")
                elif status in [401, 403, 422, 500]:
                    print(f"  ✅ {endpoint} - Accessible (status {status})")
                    accessible += 1
                else:
                    print(f"  ⚠️  {endpoint} - Unexpected status {status}")
                    accessible += 1

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  ❌ {endpoint} - Not found")
            else:
                print(f"  ✅ {endpoint} - Accessible (HTTP {e.code})")
                accessible += 1
        except Exception as e:
            print(f"  ❌ {endpoint} - Error: {e}")

    all_ok = accessible == len(endpoints)
    print(f"\nResult: {f'✅ All {accessible} endpoints accessible' if all_ok else f'⚠️ Only {accessible}/{len(endpoints)} accessible'}")
    return all_ok


def main():
    print("=" * 60)
    print("Clinical Screening System Verification")
    print("=" * 60)

    results = {
        "OpenAPI endpoints": check_openapi(),
        "Database tables": check_database_tables(),
        "Module imports": check_module_imports(),
        "Endpoint accessibility": check_endpoint_responses(),
    }

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for check, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")

    all_ok = all(results.values())

    print("\n" + "=" * 60)
    if all_ok:
        print("✅ All checks passed! Clinical screening system is ready.")
    else:
        print("⚠️ Some checks failed. Please review the output above.")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
