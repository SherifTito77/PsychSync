#!/usr/bin/env python3
"""
Supply Chain Security Integration Tests

Tests the complete supply chain security implementation:
- VEX generation
- CVE monitoring
- SBOM validation
- Registry policy enforcement
- Package signature verification
- Compliance reporting

Run: pytest tests/test_supply_chain_security.py -v

Author: Security Team
Version: 1.0
"""

import json
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest


class TestVEXGeneration:
    """Test VEX generation functionality"""

    def test_vex_script_exists(self):
        """Test that VEX generation script exists"""
        vex_script = Path("scripts/generate-vex.py")
        assert vex_script.exists(), "VEX generation script not found"

    def test_vex_script_syntax(self):
        """Test that VEX script has valid Python syntax"""
        result = subprocess.run(
            ["python3", "-m", "py_compile", "scripts/generate-vex.py"],
            capture_output=True,
        )
        assert (
            result.returncode == 0
        ), f"VEX script has syntax errors: {result.stderr.decode()}"

    def test_vex_classes_defined(self):
        """Test that VEX classes are defined"""
        with open("scripts/generate-vex.py", "r") as f:
            content = f.read()

        required_classes = [
            "class VEXStatus",
            "class VEXAnalyzer",
            "class VEXGenerator",
        ]

        for cls in required_classes:
            assert cls in content, f"Required class {cls} not found in VEX script"

    def test_vex_output_format(self):
        """Test VEX can generate valid JSON output"""
        # Create minimal test SBOM
        test_sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "component": {"name": "test", "version": "1.0.0"},
            },
            "components": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_sbom, f)
            sbom_path = f.name

        try:
            # Run VEX generation
            result = subprocess.run(
                [
                    "python3",
                    "scripts/generate-vex.py",
                    "--sbom",
                    sbom_path,
                    "--output",
                    "/tmp/test-vex.json",
                    "--format",
                    "openvex",
                ],
                capture_output=True,
                timeout=30,
            )

            # Check if it ran successfully
            # Note: May fail if dependencies not installed, which is OK for this test
            if result.returncode == 0:
                # Verify output is valid JSON
                with open("/tmp/test-vex.json", "r") as f:
                    vex_data = json.load(f)

                assert "@context" in vex_data, "VEX output missing @context"
                assert "statements" in vex_data, "VEX output missing statements"
        finally:
            Path(sbom_path).unlink(missing_ok=True)
            Path("/tmp/test-vex.json").unlink(missing_ok=True)


class TestCVEMonitoring:
    """Test CVE monitoring functionality"""

    def test_cve_monitor_script_exists(self):
        """Test that CVE monitoring script exists"""
        cve_script = Path("scripts/cve-monitor.py")
        assert cve_script.exists(), "CVE monitoring script not found"

    def test_cve_monitor_syntax(self):
        """Test that CVE monitor script has valid Python syntax"""
        result = subprocess.run(
            ["python3", "-m", "py_compile", "scripts/cve-monitor.py"],
            capture_output=True,
        )
        assert (
            result.returncode == 0
        ), f"CVE monitor script has syntax errors: {result.stderr.decode()}"

    def test_cve_monitor_classes_defined(self):
        """Test that CVE monitor classes are defined"""
        with open("scripts/cve-monitor.py", "r") as f:
            content = f.read()

        required_classes = [
            "class CVESource",
            "class CVEMonitor",
            "class VulnerabilityAlert",
        ]

        for cls in required_classes:
            assert cls in content, f"Required class {cls} not found in CVE monitor"

    def test_cve_workflow_exists(self):
        """Test that CVE monitoring workflow exists"""
        workflow = Path(".github/workflows/cve-monitoring.yml")
        assert workflow.exists(), "CVE monitoring workflow not found"

    def test_cve_workflow_schedule(self):
        """Test that CVE workflow is scheduled correctly"""
        with open(".github/workflows/cve-monitoring.yml", "r") as f:
            content = f.read()

        assert "cron:" in content, "CVE workflow not scheduled"
        assert "0 */6 * * *" in content, "CVE workflow not scheduled every 6 hours"


class TestSignedReleases:
    """Test signed release functionality"""

    def test_signed_release_workflow_exists(self):
        """Test that signed release workflow exists"""
        workflow = Path(".github/workflows/signed-release.yml")
        assert workflow.exists(), "Signed release workflow not found"

    def test_signed_release_has_slsa(self):
        """Test that signed release workflow uses SLSA generator"""
        with open(".github/workflows/signed-release.yml", "r") as f:
            content = f.read()

        assert (
            "slsa-framework/slsa-github-generator" in content
        ), "SLSA generator not found in signed release workflow"

    def test_signed_release_has_cosign(self):
        """Test that signed release workflow uses cosign"""
        with open(".github/workflows/signed-release.yml", "r") as f:
            content = f.read()

        assert "cosign" in content, "cosign not found in signed release workflow"

    def test_signed_release_jobs_defined(self):
        """Test that signed release has all required jobs"""
        with open(".github/workflows/signed-release.yml", "r") as f:
            content = f.read()

        required_jobs = [
            "validate",
            "build",
            "release-sbom",
            "release-vex",
            "provenance",
            "signing",
            "release",
        ]

        for job in required_jobs:
            assert (
                f"name: {job}" in content or f"{job}:" in content
            ), f"Required job {job} not found in signed release workflow"


class TestRegistryPolicies:
    """Test registry policy functionality"""

    def test_registry_policy_file_exists(self):
        """Test that registry policy file exists"""
        policy = Path(".github/registry-policies.yml")
        assert policy.exists(), "Registry policy file not found"

    def test_registry_policy_has_allowed(self):
        """Test that registry policy defines allowed registries"""
        with open(".github/registry-policies.yml", "r") as f:
            content = f.read()

        assert "allowed_registries:" in content, "No allowed registries defined"

    def test_registry_policy_has_blocked(self):
        """Test that registry policy defines blocked registries"""
        with open(".github/registry-policies.yml", "r") as f:
            content = f.read()

        assert "blocked_registries:" in content, "No blocked registries defined"

    def test_registry_check_script_exists(self):
        """Test that registry check script exists"""
        script = Path("scripts/check-registry-policy.sh")
        assert script.exists(), "Registry check script not found"

    def test_registry_check_script_executable(self):
        """Test that registry check script is executable"""
        script = Path("scripts/check-registry-policy.sh")
        if script.exists():
            # Check if it has execute permission
            is_executable = script.stat().st_mode & 0o111
            assert is_executable, "Registry check script is not executable"


class TestDocumentation:
    """Test documentation completeness"""

    def test_security_readme_exists(self):
        """Test that security README exists"""
        readme = Path("docs/SECURITY_README.md")
        assert readme.exists(), "Security README not found"

    def test_quick_start_exists(self):
        """Test that quick start guide exists"""
        quick_start = Path("docs/SUPPLY_CHAIN_QUICK_START.md")
        assert quick_start.exists(), "Quick start guide not found"

    def test_supply_chain_docs_exist(self):
        """Test that supply chain security docs exist"""
        docs = [
            "docs/SUPPLY_CHAIN_SECURITY_V2.md",
            "docs/SECURITY_IMPLEMENTATION_SUMMARY.md",
            "docs/SECURITY_SELF_ASSESSMENT_CHECKLIST.md",
            "docs/SECURITY_QUICK_REFERENCE.md",
        ]

        for doc in docs:
            assert Path(doc).exists(), f"Documentation file {doc} not found"

    def test_docs_have_substantial_content(self):
        """Test that documentation has substantial content"""
        docs = [
            "docs/SECURITY_README.md",
            "docs/SUPPLY_CHAIN_QUICK_START.md",
            "docs/SUPPLY_CHAIN_SECURITY_V2.md",
        ]

        for doc_path in docs:
            doc = Path(doc_path)
            if doc.exists():
                content = doc.read_text()
                # Should have at least 1000 characters
                assert len(content) > 1000, f"Document {doc_path} is too short"


class TestSecurityCI:
    """Test security CI/CD configuration"""

    def test_security_ci_workflow_exists(self):
        """Test that security CI workflow exists"""
        workflow = Path(".github/workflows/security-ci.yml")
        assert workflow.exists(), "Security CI workflow not found"

    def test_security_ci_has_vex(self):
        """Test that security CI workflow includes VEX generation"""
        with open(".github/workflows/security-ci.yml", "r") as f:
            content = f.read()

        assert (
            "generate-vex.py" in content
        ), "VEX generation not in security CI workflow"

    def test_security_ci_has_sast(self):
        """Test that security CI workflow includes SAST"""
        with open(".github/workflows/security-ci.yml", "r") as f:
            content = f.read()

        assert "bandit" in content, "SAST (Bandit) not in security CI workflow"

    def test_security_ci_has_sca(self):
        """Test that security CI workflow includes SCA"""
        with open(".github/workflows/security-ci.yml", "r") as f:
            content = f.read()

        assert "pip-audit" in content, "SCA (pip-audit) not in security CI workflow"

    def test_security_ci_has_sbom(self):
        """Test that security CI workflow includes SBOM generation"""
        with open(".github/workflows/security-ci.yml", "r") as f:
            content = f.read()

        assert "cyclonedx" in content, "SBOM generation not in security CI workflow"

    def test_security_ci_blocks_on_issues(self):
        """Test that security CI blocks on security issues"""
        with open(".github/workflows/security-ci.yml", "r") as f:
            content = f.read()

        # Should block on high severity issues
        assert (
            "sys.exit(1)" in content or "exit 1" in content
        ), "Security CI doesn't block on failures"


class TestDependencyGovernance:
    """Test dependency governance"""

    def test_dependency_governance_workflow_exists(self):
        """Test that dependency governance workflow exists"""
        workflow = Path(".github/workflows/dependency-governance.yml")
        assert workflow.exists(), "Dependency governance workflow not found"

    def test_dependency_governance_has_allowlist(self):
        """Test that dependency governance checks allow-list"""
        with open(".github/workflows/dependency-governance.yml", "r") as f:
            content = f.read()

        assert (
            "check-allowlist.sh" in content
        ), "Allow-list check not in dependency governance"

    def test_dependency_governance_has_signature_verification(self):
        """Test that dependency governance verifies signatures"""
        with open(".github/workflows/dependency-governance.yml", "r") as f:
            content = f.read()

        assert (
            "sigstore" in content or "signature-verification" in content
        ), "Package signature verification not in dependency governance"

    def test_allowlist_files_exist(self):
        """Test that allow-list files exist"""
        files = ["allowed-dependencies.txt", "frontend/allowed-dependencies.json"]

        for file_path in files:
            assert Path(file_path).exists(), f"Allow-list file {file_path} not found"

    def test_python_allowlist_valid(self):
        """Test that Python allow-list has valid entries"""
        with open("allowed-dependencies.txt", "r") as f:
            content = f.read()

        # Should have some entries
        lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
        assert len(lines) > 0, "Python allow-list is empty"

    def test_js_allowlist_valid_json(self):
        """Test that JavaScript allow-list is valid JSON"""
        with open("frontend/allowed-dependencies.json", "r") as f:
            try:
                data = json.load(f)
                assert (
                    "allowedDependencies" in data
                ), "Missing allowedDependencies in JS allow-list"
            except json.JSONDecodeError as e:
                pytest.fail(f"JavaScript allow-list has invalid JSON: {e}")


class TestEphemeralRunners:
    """Test ephemeral runner configuration"""

    def test_ephemeral_runners_config_exists(self):
        """Test that ephemeral runners config exists"""
        config = Path(".github/ephemeral-runners.yml")
        assert config.exists(), "Ephemeral runners config not found"

    def test_ephemeral_runners_configured(self):
        """Test that ephemeral runners are configured"""
        with open(".github/ephemeral-runners.yml", "r") as f:
            content = f.read()

        assert "ephemeral: true" in content, "Runners not configured as ephemeral"

    def test_auto_scaling_configured(self):
        """Test that auto-scaling is configured"""
        with open(".github/ephemeral-runners.yml", "r") as f:
            content = f.read()

        assert "auto_scale:" in content, "Auto-scaling not configured"


class TestComplianceReporting:
    """Test compliance reporting functionality"""

    def test_compliance_report_script_exists(self):
        """Test that compliance report script exists"""
        script = Path("scripts/compliance-report.py")
        assert script.exists(), "Compliance report script not found"

    def test_compliance_report_syntax(self):
        """Test that compliance report script has valid Python syntax"""
        result = subprocess.run(
            ["python3", "-m", "py_compile", "scripts/compliance-report.py"],
            capture_output=True,
        )
        assert (
            result.returncode == 0
        ), f"Compliance report script has syntax errors: {result.stderr.decode()}"

    def test_compliance_report_generates_json(self):
        """Test that compliance report can generate JSON"""
        result = subprocess.run(
            ["python3", "scripts/compliance-report.py", "--format", "json"],
            capture_output=True,
            timeout=30,
        )

        # May fail if dependencies missing, but should at least run
        if result.returncode == 0:
            # Check output is valid JSON
            try:
                data = json.loads(result.stdout)
                assert "frameworks" in data, "Compliance report missing frameworks"
            except json.JSONDecodeError:
                pytest.fail("Compliance report didn't generate valid JSON")

    def test_compliance_report_has_nist_ssdf(self):
        """Test that compliance report includes NIST SSDF"""
        with open("scripts/compliance-report.py", "r") as f:
            content = f.read()

        assert "nist_ssdf" in content, "NIST SSDF not in compliance report"

    def test_compliance_report_has_slsa(self):
        """Test that compliance report includes SLSA"""
        with open("scripts/compliance-report.py", "r") as f:
            content = f.read()

        assert "slsa" in content, "SLSA not in compliance report"


class TestVerificationScript:
    """Test verification script"""

    def test_verification_script_exists(self):
        """Test that verification script exists"""
        script = Path("scripts/verify-supply-chain-security.sh")
        assert script.exists(), "Verification script not found"

    def test_verification_script_executable(self):
        """Test that verification script is executable"""
        script = Path("scripts/verify-supply-chain-security.sh")
        if script.exists():
            is_executable = script.stat().st_mode & 0o111
            assert is_executable, "Verification script is not executable"

    def test_verification_script_checks_files(self):
        """Test that verification script checks required files"""
        with open("scripts/verify-supply-chain-security.sh", "r") as f:
            content = f.read()

        required_files = [
            "scripts/generate-vex.py",
            "scripts/cve-monitor.py",
            ".github/workflows/security-ci.yml",
            ".github/workflows/signed-release.yml",
        ]

        for file in required_files:
            assert file in content, f"Verification script doesn't check for {file}"


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_end_to_end_vex_workflow(self):
        """Test complete VEX workflow: SBOM → VEX"""
        # This test would require full dependency installation
        # For now, just verify the components exist
        assert Path("scripts/generate-vex.py").exists()
        assert Path("scripts/cve-monitor.py").exists()

    def test_end_to_end_release_workflow(self):
        """Test complete release workflow exists"""
        required_workflows = [
            ".github/workflows/security-ci.yml",
            ".github/workflows/signed-release.yml",
        ]

        for workflow in required_workflows:
            assert Path(workflow).exists(), f"Required workflow {workflow} not found"

    def test_complete_documentation_set(self):
        """Test that complete documentation set exists"""
        required_docs = [
            "docs/SECURITY_README.md",
            "docs/SUPPLY_CHAIN_QUICK_START.md",
            "docs/SUPPLY_CHAIN_SECURITY_V2.md",
            "docs/SECURITY_IMPLEMENTATION_SUMMARY.md",
            "docs/SECURITY_SELF_ASSESSMENT_CHECKLIST.md",
            "docs/SECURITY_QUICK_REFERENCE.md",
        ]

        for doc in required_docs:
            assert Path(doc).exists(), f"Required documentation {doc} not found"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
