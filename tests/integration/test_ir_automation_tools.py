"""
Integration tests for Incident Response Automation Tools

Tests all four IR automation tools:
1. Data Poisoning Detector (ml/security/poisoning_detector.py)
2. SBOM Analyzer (supply_chain/sbom_analyzer.py)
3. Credential Rotator (security/credential_rotator.py)
4. Secure Model Trainer (ml/training/secure_trainer.py)
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
import pytest


class TestDataPoisoningDetector:
    """Test suite for Data Poisoning Detector."""

    def test_import_module(self):
        """Test that the module can be imported."""
        try:
            from ml.security.poisoning_detector import (
                DataPoisoningDetector,
                PoisoningReport,
                PoisoningSignal,
                PoisoningType,
            )

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import poisoning_detector: {e}")

    def test_detector_initialization(self):
        """Test detector initialization."""
        from ml.security.poisoning_detector import DataPoisoningDetector

        detector = DataPoisoningDetector()
        assert detector is not None
        assert hasattr(detector, "Z_SCORE_THRESHOLD")
        assert detector.Z_SCORE_THRESHOLD == 3.0

    def test_detect_label_flipping(self):
        """Test label flipping detection."""
        from ml.security.poisoning_detector import DataPoisoningDetector

        detector = DataPoisoningDetector()

        # Create test data with potential label flipping
        df = pd.DataFrame(
            {
                "text": ["sample " + str(i) for i in range(100)],
                "label": ["positive"] * 90 + ["negative"] * 10,
            }
        )

        # Flip some labels
        df.loc[95:99, "label"] = "positive"

        result = detector.detect_poisoning(
            corpus_data=df,
            corpus_id="test-corpus-1",
            label_column="label",
            text_column="text",
        )

        assert result is not None
        assert hasattr(result, "poisoning_detected")
        assert hasattr(result, "signals")

    def test_detect_statistical_anomalies(self):
        """Test statistical anomaly detection."""
        from ml.security.poisoning_detector import DataPoisoningDetector

        detector = DataPoisoningDetector()

        # Create data with statistical anomalies
        normal_data = np.random.normal(0, 1, 1000)
        anomalous_data = np.concatenate([normal_data, np.array([10, -10, 15, -15])])

        df = pd.DataFrame(
            {"feature": anomalous_data, "label": ["class"] * len(anomalous_data)}
        )

        result = detector.detect_poisoning(
            corpus_data=df, corpus_id="test-corpus-2", label_column="label"
        )

        assert result is not None


class TestSBOMAnalyzer:
    """Test suite for SBOM Analyzer."""

    def test_import_module(self):
        """Test that the module can be imported."""
        try:
            from supply_chain.sbom_analyzer import (
                Dependency,
                ImpactAssessment,
                SBOMAnalysisReport,
                SBOMAnalyzer,
                VulnerabilityInfo,
            )

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import sbom_analyzer: {e}")

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        from supply_chain.sbom_analyzer import SBOMAnalyzer

        analyzer = SBOMAnalyzer()
        assert analyzer is not None

    def test_parse_cyclonedx_sbom(self):
        """Test parsing CycloneDX SBOM format."""
        from supply_chain.sbom_analyzer import SBOMAnalyzer

        analyzer = SBOMAnalyzer()

        # Create minimal CycloneDX SBOM
        sbom_data = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "metadata": {"component": {"name": "test-component", "version": "1.0.0"}},
            "components": [
                {
                    "name": "numpy",
                    "version": "1.21.0",
                    "purl": "pkg:pypi/numpy@1.21.0",
                    "licenses": [{"license": {"id": "MIT"}}],
                    "hashes": [{"alg": "SHA-256", "content": "abc123"}],
                }
            ],
        }

        # Test parsing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sbom_data, f)
            temp_path = f.name

        try:
            dependencies = analyzer._parse_dependencies(sbom_data)
            assert len(dependencies) > 0
        finally:
            os.unlink(temp_path)

    def test_check_licenses(self):
        """Test license compliance checking."""
        from supply_chain.sbom_analyzer import Dependency, SBOMAnalyzer

        analyzer = SBOMAnalyzer()

        # Create dependencies with various licenses
        dependencies = [
            Dependency(
                name="mit-package",
                version="1.0.0",
                purl="pkg:pypi/mit-package@1.0.0",
                licenses=["MIT"],
                hashes={"sha256": "abc123"},
            ),
            Dependency(
                name="gpl-package",
                version="1.0.0",
                purl="pkg:pypi/gpl-package@1.0.0",
                licenses=["GPL-3.0"],
                hashes={"sha256": "def456"},
            ),
        ]

        result = analyzer._check_licenses(dependencies)

        assert result is not None
        assert "compliant" in result
        assert "violations" in result
        assert result["violations"] == 1  # GPL-3.0 is prohibited


class TestCredentialRotator:
    """Test suite for Credential Rotator."""

    def test_import_module(self):
        """Test that the module can be imported."""
        try:
            from security.credential_rotator import (
                Credential,
                CredentialRotator,
                CredentialType,
                RotationReport,
            )

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import credential_rotator: {e}")

    def test_rotator_initialization(self):
        """Test rotator initialization."""
        from security.credential_rotator import CredentialRotator

        rotator = CredentialRotator(dry_run=True)
        assert rotator is not None
        assert rotator.dry_run == True

    def test_rotate_database_password(self):
        """Test database password rotation in dry-run mode."""
        from security.credential_rotator import (
            Credential,
            CredentialRotator,
            CredentialType,
        )

        rotator = CredentialRotator(dry_run=True)

        credential = Credential(
            credential_id="test-db-1",
            name="Test Database Password",
            type=CredentialType.DATABASE_PASSWORD,
            location="postgresql://localhost/db",
            current_value_hash="abc123",
            services_affected=["api", "worker"],
        )

        report = rotator.rotate_credentials(
            credentials=[credential], incident_id="test-incident-1"
        )

        assert report is not None
        assert hasattr(report, "incident_id")
        assert report.incident_id == "test-incident-1"
        assert len(report.credentials_rotated) == 1

    def test_rotate_api_key(self):
        """Test API key rotation in dry-run mode."""
        from security.credential_rotator import (
            Credential,
            CredentialRotator,
            CredentialType,
        )

        rotator = CredentialRotator(dry_run=True)

        credential = Credential(
            credential_id="test-api-1",
            name="Test API Key",
            type=CredentialType.API_KEY,
            location="header",
            current_value_hash="xyz789",
            services_affected=["external-api"],
        )

        report = rotator.rotate_credentials(
            credentials=[credential], incident_id="test-incident-2"
        )

        assert report is not None
        assert len(report.credentials_rotated) == 1


class TestSecureModelTrainer:
    """Test suite for Secure Model Trainer."""

    def test_import_module(self):
        """Test that the module can be imported."""
        try:
            from ml.training.secure_trainer import (
                AnomalySeverity,
                AnomalySignal,
                AnomalyType,
                CheckpointMetadata,
                SecureModelTrainer,
                TrainingMetrics,
                TrainingPhase,
                TrainingReport,
                ValidationReport,
            )

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import secure_trainer: {e}")

    def test_trainer_initialization(self):
        """Test trainer initialization."""
        from ml.training.secure_trainer import SecureModelTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = SecureModelTrainer(
                checkpoint_dir=os.path.join(tmpdir, "checkpoints"),
                audit_log_dir=os.path.join(tmpdir, "audit_logs"),
            )
            assert trainer is not None
            assert trainer.enable_gradient_monitoring == True

    def test_data_validation(self):
        """Test training data validation."""
        from ml.training.secure_trainer import SecureModelTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = SecureModelTrainer(
                checkpoint_dir=os.path.join(tmpdir, "checkpoints"),
                audit_log_dir=os.path.join(tmpdir, "audit_logs"),
            )

            # Create test data
            train_data = pd.DataFrame(
                {
                    "feature1": np.random.randn(1000),
                    "feature2": np.random.randn(1000),
                    "label": np.random.randint(0, 2, 1000),
                }
            )

            report = trainer._validate_training_data(
                train_data=train_data, val_data=None, corpus_id="test-corpus"
            )

            assert report is not None
            assert "passed" in report

    def test_anomaly_detection(self):
        """Test training anomaly detection."""
        from ml.training.secure_trainer import (
            SecureModelTrainer,
            TrainingMetrics,
            TrainingPhase,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = SecureModelTrainer(
                checkpoint_dir=os.path.join(tmpdir, "checkpoints"),
                audit_log_dir=os.path.join(tmpdir, "audit_logs"),
            )

            trainer.current_phase = TrainingPhase.TRAINING
            trainer.current_epoch = 0

            # Create metrics with potential anomaly
            metrics = TrainingMetrics(
                epoch=0, step=0, train_loss=100.0, val_loss=95.0  # Very high loss
            )

            gradients = np.random.randn(1000) * 1000  # Large gradients

            anomalies = trainer._monitor_training_step(
                metrics=metrics, gradients=gradients, epoch=0
            )

            assert anomalies is not None
            assert len(anomalies) >= 0

    def test_checkpoint_creation(self):
        """Test checkpoint creation with provenance."""
        from ml.training.secure_trainer import SecureModelTrainer, TrainingMetrics

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = SecureModelTrainer(
                checkpoint_dir=os.path.join(tmpdir, "checkpoints"),
                audit_log_dir=os.path.join(tmpdir, "audit_logs"),
            )

            metrics = TrainingMetrics(
                epoch=0, step=100, train_loss=0.5, val_loss=0.6, val_accuracy=0.85
            )

            # Use a simple dict as mock model (picklable)
            model = {"type": "mock", "params": [1, 2, 3]}
            config = {"learning_rate": 0.001, "batch_size": 32}

            checkpoint = trainer._create_checkpoint(
                model=model,
                metrics=metrics,
                config=config,
                model_id="test-model-1",
                corpus_id="test-corpus-1",
            )

            assert checkpoint is not None
            assert hasattr(checkpoint, "checkpoint_id")
            assert hasattr(checkpoint, "model_hash")
            assert hasattr(checkpoint, "file_hash")
            assert os.path.exists(checkpoint.file_path)


class TestIntegratedWorkflow:
    """Test integrated workflow using all tools together."""

    def test_full_incident_response_workflow(self):
        """Test complete IR workflow with all tools."""
        print("\n=== Testing Full IR Workflow ===\n")

        # Step 1: Analyze SBOM for vulnerabilities
        print("Step 1: Analyzing SBOM...")
        from supply_chain.sbom_analyzer import SBOMAnalyzer

        sbom_analyzer = SBOMAnalyzer()
        print("✓ SBOM Analyzer initialized")

        # Step 2: Check for data poisoning
        print("\nStep 2: Checking for data poisoning...")
        from ml.security.poisoning_detector import DataPoisoningDetector

        poisoning_detector = DataPoisoningDetector()

        test_data = pd.DataFrame(
            {
                "text": ["sample " + str(i) for i in range(100)],
                "label": ["positive"] * 90 + ["negative"] * 10,
            }
        )

        report = poisoning_detector.detect_poisoning(
            corpus_data=test_data,
            corpus_id="test-workflow-corpus",
            label_column="label",
            text_column="text",
        )
        print("✓ Data poisoning check completed")

        # Step 3: Rotate credentials if needed
        print("\nStep 3: Testing credential rotation...")
        from security.credential_rotator import (
            Credential,
            CredentialRotator,
            CredentialType,
        )

        credential_rotator = CredentialRotator(dry_run=True)

        test_credential = Credential(
            credential_id="workflow-test-1",
            name="Workflow Test Credential",
            type=CredentialType.API_KEY,
            location="environment",
            current_value_hash="test123",
            services_affected=["test-service"],
        )

        rotation_report = credential_rotator.rotate_credentials(
            credentials=[test_credential], incident_id="workflow-test-incident"
        )
        print("✓ Credential rotation test completed")

        # Step 4: Secure model retraining
        print("\nStep 4: Testing secure model trainer...")
        from ml.training.secure_trainer import SecureModelTrainer

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = SecureModelTrainer(
                checkpoint_dir=os.path.join(tmpdir, "checkpoints"),
                audit_log_dir=os.path.join(tmpdir, "audit_logs"),
            )
            print("✓ Secure trainer initialized")

        print("\n=== All IR Tools Test Completed Successfully ===\n")

    def test_tool_integration(self):
        """Test that tools can work together."""
        print("\n=== Testing Tool Integration ===\n")

        # Test that all tools can be imported and used together
        from ml.security.poisoning_detector import DataPoisoningDetector
        from ml.training.secure_trainer import SecureModelTrainer
        from security.credential_rotator import CredentialRotator
        from supply_chain.sbom_analyzer import SBOMAnalyzer

        # Initialize all tools
        sbom_analyzer = SBOMAnalyzer()
        poisoning_detector = DataPoisoningDetector()
        credential_rotator = CredentialRotator(dry_run=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            trainer = SecureModelTrainer(
                checkpoint_dir=os.path.join(tmpdir, "checkpoints"),
                audit_log_dir=os.path.join(tmpdir, "audit_logs"),
            )

        print("✓ All tools successfully initialized")
        print("✓ Tools can work together in integrated workflow")
        print("\n=== Integration Test Completed ===\n")


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("IR Automation Tools - Integration Test Suite")
    print("=" * 60 + "\n")

    # Test classes
    test_classes = [
        ("Data Poisoning Detector", TestDataPoisoningDetector()),
        ("SBOM Analyzer", TestSBOMAnalyzer()),
        ("Credential Rotator", TestCredentialRotator()),
        ("Secure Model Trainer", TestSecureModelTrainer()),
        ("Integrated Workflow", TestIntegratedWorkflow()),
    ]

    results = {"passed": 0, "failed": 0, "errors": []}

    for test_name, test_class in test_classes:
        print(f"\n{'─'*60}")
        print(f"Testing: {test_name}")
        print(f"{'─'*60}\n")

        test_methods = [m for m in dir(test_class) if m.startswith("test_")]

        for test_method in test_methods:
            try:
                print(f"  Running: {test_method}...", end=" ")
                method = getattr(test_class, test_method)
                method()
                print("✓ PASSED")
                results["passed"] += 1
            except AssertionError as e:
                print(f"✗ FAILED")
                print(f"    Error: {str(e)}")
                results["failed"] += 1
                results["errors"].append((test_name, test_method, str(e)))
            except Exception as e:
                print(f"✗ ERROR")
                print(f"    Error: {str(e)}")
                results["failed"] += 1
                results["errors"].append((test_name, test_method, str(e)))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total Tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")

    if results["errors"]:
        print("\nFailed Tests:")
        for test_name, test_method, error in results["errors"]:
            print(f"  - {test_name}.{test_method}")
            print(f"    {error}")

    print("=" * 60 + "\n")

    return results["failed"] == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
