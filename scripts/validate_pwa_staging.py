#!/usr/bin/env python3
"""
🚀 PsychSync PWA Staging Validation Script

Validates PWA functionality in the current development/staging environment.
Performs comprehensive checks to ensure PWA is production-ready.

Usage:
    python validate_pwa_staging.py
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PWAStagingValidator:
    """Comprehensive PWA staging validator"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results = {
            "validation_timestamp": datetime.now().isoformat(),
            "environment": "development/staging",
            "pwa_features": {},
            "file_system_checks": {},
            "backend_checks": {},
            "frontend_checks": {},
            "overall_status": "pending",
            "recommendations": [],
        }

    async def run_validation(self) -> Dict[str, Any]:
        """Run comprehensive PWA validation"""
        logger.info("🚀 Starting PsychSync PWA Staging Validation")

        try:
            # File system checks
            await self.validate_file_system()

            # Backend validation
            await self.validate_backend()

            # Frontend validation
            await self.validate_frontend()

            # PWA-specific validation
            await self.validate_pwa_features()

            # Overall assessment
            self.assess_readiness()

            # Generate report
            await self.generate_validation_report()

            return self.results

        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            self.results["overall_status"] = "failed"
            self.results["error"] = str(e)
            return self.results

    async def validate_file_system(self):
        """Validate required PWA files exist"""
        logger.info("📁 Validating file system...")

        required_files = {
            "service_worker": "public/service-worker.js",
            "optimized_service_worker": "public/service-worker-optimized.js",
            "manifest": "public/manifest.json",
            "pwa_manager": "frontend/src/utils/pwaManager.ts",
            "pwa_installer": "frontend/src/components/PWAInstaller.tsx",
            "offline_status": "frontend/src/components/OfflineStatus.tsx",
            "pwa_styles": "frontend/src/styles/pwa.css",
        }

        file_results = {}
        for name, path in required_files.items():
            file_path = self.project_root / path
            exists = file_path.exists()
            size = file_path.stat().st_size if exists else 0

            file_results[name] = {
                "path": path,
                "exists": exists,
                "size_bytes": size,
                "status": "✅ Found" if exists else "❌ Missing",
            }

            if exists:
                logger.info(f"  ✅ {name}: {path} ({size} bytes)")
            else:
                logger.warning(f"  ❌ {name}: {path} - Missing")

        self.results["file_system_checks"] = file_results

    async def validate_backend(self):
        """Validate backend PWA support"""
        logger.info("🔧 Validating backend PWA support...")

        backend_results = {
            "fastapi_running": False,
            "pwa_endpoints": False,
            "cors_configured": False,
            "security_headers": False,
        }

        # Check if FastAPI server is running
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8000/api/v1/health", timeout=5
                )
                if response.status_code == 200:
                    backend_results["fastapi_running"] = True
                    logger.info("  ✅ FastAPI server is running")
                else:
                    logger.warning(
                        f"  ⚠️ FastAPI returned status {response.status_code}"
                    )
        except Exception as e:
            logger.warning(f"  ❌ FastAPI server not accessible: {e}")

        # Check for PWA-related endpoints
        pwa_endpoints = ["/api/v1/health", "/api/v1/health/detailed"]

        endpoints_found = 0
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                for endpoint in pwa_endpoints:
                    try:
                        response = await client.get(
                            f"http://localhost:8000{endpoint}", timeout=5
                        )
                        if response.status_code == 200:
                            endpoints_found += 1
                    except Exception as e:
                        pass
        except Exception as e:
            pass

        backend_results["pwa_endpoints"] = endpoints_found > 0
        if endpoints_found > 0:
            logger.info(f"  ✅ Found {endpoints_found} PWA-related endpoints")

        self.results["backend_checks"] = backend_results

    async def validate_frontend(self):
        """Validate frontend PWA setup"""
        logger.info("🌐 Validating frontend PWA setup...")

        frontend_results = {
            "package_json": False,
            "pwa_dependencies": False,
            "build_config": False,
            "dist_build": False,
        }

        # Check package.json
        package_json_path = self.project_root / "frontend/package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)

                frontend_results["package_json"] = True
                logger.info("  ✅ package.json found")

                # Check for PWA-related dependencies
                pwa_deps = [
                    "workbox-webpack-plugin",
                    "workbox-window",
                    "@vitejs/plugin-pwa",
                ]
                found_deps = [dep for dep in pwa_deps if dep in str(package_data)]
                frontend_results["pwa_dependencies"] = len(found_deps) > 0
                if found_deps:
                    logger.info(f"  ✅ Found PWA dependencies: {found_deps}")

            except Exception as e:
                logger.warning(f"  ❌ Error reading package.json: {e}")

        # Check for build configuration
        vite_config = self.project_root / "frontend/vite.config.ts"
        if vite_config.exists():
            frontend_results["build_config"] = True
            logger.info("  ✅ Vite configuration found")

        self.results["frontend_checks"] = frontend_results

    async def validate_pwa_features(self):
        """Validate PWA-specific features"""
        logger.info("📱 Validating PWA features...")

        pwa_results = {
            "service_worker": False,
            "manifest": False,
            "icons": False,
            "offline_support": False,
            "installation_prompts": False,
            "push_notifications": False,
        }

        # Check service worker
        sw_path = self.project_root / "public/service-worker.js"
        if sw_path.exists():
            with open(sw_path, "r") as f:
                sw_content = f.read()

            if "CACHE_VERSION" in sw_content and "fetch" in sw_content:
                pwa_results["service_worker"] = True
                logger.info("  ✅ Service worker with caching found")

        # Check manifest
        manifest_path = self.project_root / "public/manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r") as f:
                manifest_data = json.load(f)

            required_fields = ["name", "short_name", "start_url", "display", "icons"]
            missing_fields = [
                field for field in required_fields if field not in manifest_data
            ]

            pwa_results["manifest"] = len(missing_fields) == 0
            if pwa_results["manifest"]:
                logger.info("  ✅ PWA manifest with required fields found")
            else:
                logger.warning(f"  ⚠️ Manifest missing fields: {missing_fields}")

        # Check icons
        icons_dir = self.project_root / "public/assets/icons"
        if icons_dir.exists():
            icon_files = list(icons_dir.glob("*.png")) + list(icons_dir.glob("*.ico"))
            if len(icon_files) >= 10:  # Good number of icons
                pwa_results["icons"] = True
                logger.info(f"  ✅ Found {len(icon_files)} icon files")

        # Check for offline support features
        sw_optimized_path = self.project_root / "public/service-worker-optimized.js"
        if sw_optimized_path.exists():
            with open(sw_optimized_path, "r") as f:
                sw_content = f.read()

            if "offline" in sw_content.lower() and "cache" in sw_content.lower():
                pwa_results["offline_support"] = True
                logger.info("  ✅ Offline support features found")

        self.results["pwa_features"] = pwa_results

    def assess_readiness(self):
        """Assess overall PWA readiness"""
        logger.info("🎯 Assessing PWA readiness...")

        file_system_score = (
            sum(
                1
                for check in self.results["file_system_checks"].values()
                if check["exists"]
            )
            / len(self.results["file_system_checks"])
            * 100
        )

        backend_score = 0
        if self.results["backend_checks"]["fastapi_running"]:
            backend_score += 50
        if self.results["backend_checks"]["pwa_endpoints"]:
            backend_score += 50

        frontend_score = 0
        if self.results["frontend_checks"]["package_json"]:
            frontend_score += 33
        if self.results["frontend_checks"]["build_config"]:
            frontend_score += 33
        if self.results["frontend_checks"]["pwa_dependencies"]:
            frontend_score += 34

        pwa_score = (
            sum(1 for feature in self.results["pwa_features"].values() if feature)
            / len(self.results["pwa_features"])
            * 100
        )

        # Calculate overall score
        overall_score = (
            file_system_score + backend_score + frontend_score + pwa_score
        ) / 4

        self.results["scores"] = {
            "file_system": file_system_score,
            "backend": backend_score,
            "frontend": frontend_score,
            "pwa_features": pwa_score,
            "overall": overall_score,
        }

        # Determine status
        if overall_score >= 90:
            self.results["overall_status"] = "excellent"
            logger.info(f"  🎉 Overall readiness: EXCELLENT ({overall_score:.1f}%)")
        elif overall_score >= 80:
            self.results["overall_status"] = "good"
            logger.info(f"  ✅ Overall readiness: GOOD ({overall_score:.1f}%)")
        elif overall_score >= 70:
            self.results["overall_status"] = "acceptable"
            logger.info(f"  ⚠️ Overall readiness: ACCEPTABLE ({overall_score:.1f}%)")
        else:
            self.results["overall_status"] = "needs_work"
            logger.warning(f"  ❌ Overall readiness: NEEDS WORK ({overall_score:.1f}%)")

        # Generate recommendations
        self.generate_recommendations()

    def generate_recommendations(self):
        """Generate improvement recommendations"""
        recommendations = []

        # File system recommendations
        for name, check in self.results["file_system_checks"].items():
            if not check["exists"]:
                recommendations.append(f"Create missing PWA file: {check['path']}")

        # Backend recommendations
        if not self.results["backend_checks"]["fastapi_running"]:
            recommendations.append(
                "Start FastAPI server: uvicorn app.main:app --host 0.0.0.0 --port 8000"
            )

        # Frontend recommendations
        if not self.results["frontend_checks"]["pwa_dependencies"]:
            recommendations.append("Add PWA dependencies to package.json")

        # PWA feature recommendations
        if not self.results["pwa_features"]["service_worker"]:
            recommendations.append("Ensure service worker is properly configured")
        if not self.results["pwa_features"]["manifest"]:
            recommendations.append("Complete PWA manifest configuration")
        if not self.results["pwa_features"]["icons"]:
            recommendations.append("Generate complete PWA icon set")

        self.results["recommendations"] = recommendations

    async def generate_validation_report(self):
        """Generate comprehensive validation report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = Path(f"pwa_staging_validation_report_{timestamp}.json")

        try:
            with open(report_path, "w") as f:
                json.dump(self.results, f, indent=2, default=str)

            logger.info(f"📊 Validation report saved: {report_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")

    def display_summary(self):
        """Display validation summary"""
        print("\n" + "=" * 60)
        print("🚀 PSYCHSYNC PWA STAGING VALIDATION RESULTS")
        print("=" * 60)
        print(f"Environment: {self.results['environment']}")
        print(f"Timestamp: {self.results['validation_timestamp']}")
        print(f"Overall Status: {self.results['overall_status'].upper()}")
        print(f"Overall Score: {self.results.get('scores', {}).get('overall', 0):.1f}%")
        print()

        print("📊 Category Scores:")
        scores = self.results.get("scores", {})
        for category, score in scores.items():
            status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"  {status} {category.title()}: {score:.1f}%")
        print()

        print("📁 File System Check:")
        for name, check in self.results["file_system_checks"].items():
            print(f"  {check['status']} {name}: {check['path']}")
        print()

        print("📱 PWA Features:")
        for feature, enabled in self.results["pwa_features"].items():
            status = "✅" if enabled else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}")
        print()

        if self.results.get("recommendations"):
            print("💡 Recommendations:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                print(f"  {i}. {rec}")
            print()

        status_icon = {
            "excellent": "🎉",
            "good": "✅",
            "acceptable": "⚠️",
            "needs_work": "❌",
        }.get(self.results["overall_status"], "❓")

        print(
            f"{status_icon} Staging Validation: {self.results['overall_status'].upper()}"
        )
        print("=" * 60)


async def main():
    """Main validation execution"""
    validator = PWAStagingValidator()

    try:
        results = await validator.run_validation()
        validator.display_summary()

        return results["overall_status"] in ["excellent", "good", "acceptable"]

    except KeyboardInterrupt:
        print("\n⏹️ Validation interrupted")
        return False
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
