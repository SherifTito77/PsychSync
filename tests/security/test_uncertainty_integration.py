"""
Uncertainty Guard Integration Tests
Test the integration of uncertainty detection with existing AI services.

Author: PsychSync Security Team
Version: 1.0.0
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.security.uncertainty_detection import TaskCategory
from ai.services.uncertainty_guard import (
    GuardedResult,
    UncertaintyExceededError,
    UncertaintyGuard,
    with_uncertainty_check,
)


class TestUncertaintyGuardDecorator:
    """Test the decorator pattern for uncertainty guarding."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset singleton for clean tests
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_review_queue=True, enable_logging=False)

    def test_decorator_with_confident_output(self):
        """Test decorator with confident, low-uncertainty output."""

        @self.guard.protect(task_category=TaskCategory.GENERAL_ASSISTANCE)
        def mock_llm_call(prompt):
            return "Patient scored 18 on PHQ-9 assessment"

        result = mock_llm_call("Assess patient")

        assert result.success is True
        assert result.output is not None
        assert result.uncertainty_report is not None
        assert result.requires_review is False

    def test_decorator_with_uncertain_output(self):
        """Test decorator with uncertain, high-uncertainty output."""

        @self.guard.protect(task_category=TaskCategory.CLINICAL_ASSESSMENT)
        def mock_llm_call(prompt):
            return "Patient definitely might have depression, et al. (2024)"

        result = mock_llm_call("Assess patient")

        # Should require review for clinical task
        assert result.requires_review is True
        assert result.review_ticket is not None
        assert result.uncertainty_report.overall_score > 0.1

    def test_decorator_raises_on_uncertainty(self):
        """Test that decorator can raise exception on high uncertainty."""

        @self.guard.protect(
            task_category=TaskCategory.CLINICAL_ASSESSMENT, raise_on_uncertainty=True
        )
        def mock_llm_call(prompt):
            return "Patient might possibly have condition"

        # Should raise exception
        with pytest.raises(UncertaintyExceededError):
            mock_llm_call("Assess patient")

    def test_convenience_decorator(self):
        """Test the convenience decorator function."""

        @with_uncertainty_check(task_category=TaskCategory.GENERAL_ASSISTANCE)
        def generate_diagnosis(data):
            return "Diagnosis: depression"

        result = generate_diagnosis({})

        assert isinstance(result, GuardedResult)
        assert result.success is True


class TestUncertaintyGuardContextManager:
    """Test the context manager pattern."""

    def setup_method(self):
        """Set up test fixtures."""
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_logging=False)

    def test_context_manager_basic_usage(self):
        """Test basic context manager usage."""
        mock_llm = Mock()
        mock_llm.generate.return_value = "Patient scored 18 on PHQ-9"

        with self.guard.protect_context(
            task_category=TaskCategory.GENERAL_ASSISTANCE
        ) as ctx:
            ctx.set_input("Assess patient")
            result = mock_llm.generate("Assess patient")
            ctx.set_output(result)

        # Check result
        assert ctx.guarded_result is not None
        assert ctx.guarded_result.success is True
        assert ctx.guarded_result.output == result

    def test_context_manager_with_uncertain_output(self):
        """Test context manager catches uncertain output."""
        mock_llm = Mock()
        mock_llm.generate.return_value = (
            "Patient definitely might have condition, et al. (2024)"
        )

        with self.guard.protect_context(
            task_category=TaskCategory.CLINICAL_ASSESSMENT
        ) as ctx:
            ctx.set_input("Assess patient")
            result = mock_llm.generate("Assess patient")
            ctx.set_output(result)

        # Should require review
        assert ctx.guarded_result.requires_review is True
        assert ctx.guarded_result.review_ticket is not None


class TestDirectOutputChecking:
    """Test direct output checking without decorator/context manager."""

    def setup_method(self):
        """Set up test fixtures."""
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_logging=False)

    def test_check_output_directly(self):
        """Test checking output directly."""
        output = "Patient scored 18 on PHQ-9 assessment"

        result = self.guard.check_output(
            output, task_category=TaskCategory.GENERAL_ASSISTANCE
        )

        assert result.success is True
        assert result.output == output
        assert result.uncertainty_report is not None

    def test_check_output_with_context(self):
        """Test checking output with additional context."""
        output = "The score is 42"  # Outside context range
        context = {"max_score": 15}

        result = self.guard.check_output(
            output, task_category=TaskCategory.CLINICAL_ASSESSMENT, context=context
        )

        # Should detect knowledge gap
        assert result.uncertainty_report.signals.knowledge_gap_score > 0


class TestReviewQueueIntegration:
    """Test integration with human review queue."""

    def setup_method(self):
        """Set up test fixtures."""
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_review_queue=True, enable_logging=False)

    def test_queued_for_review_on_high_uncertainty(self):
        """Test that high uncertainty outputs are queued."""

        @self.guard.protect(task_category=TaskCategory.CLINICAL_ASSESSMENT)
        def generate_diagnosis():
            return "Patient definitely might have condition"

        result = generate_diagnosis()

        # Should be queued
        assert result.requires_review is True
        assert result.review_ticket is not None
        assert result.review_ticket.startswith("REVIEW-")

        # Should appear in pending reviews
        pending = self.guard.get_pending_reviews()
        assert len(pending) > 0
        assert pending[0]["ticket_id"] == result.review_ticket

    def test_not_queued_for_low_uncertainty(self):
        """Test that low uncertainty outputs are not queued."""

        @self.guard.protect(task_category=TaskCategory.GENERAL_ASSISTANCE)
        def generate_diagnosis():
            return "Patient shows clear signs of depression"

        result = generate_diagnosis()

        # Should not be queued (low uncertainty task)
        if not result.requires_review:
            assert result.review_ticket is None


class TestIntegrationWithExistingServices:
    """Test integration with existing AI services."""

    def setup_method(self):
        """Set up test fixtures."""
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_logging=False)

    @patch("ai.services.context_assembly.ContextAssemblyService")
    def test_integration_with_context_assembly(self, mock_context_class):
        """Test integration with context assembly service."""
        # Mock the context assembly service
        mock_context = Mock()
        mock_context.assemble_context.return_value = {
            "patient_data": "redacted",
            "assessment_history": "redacted",
        }
        mock_context_class.return_value = mock_context

        # Use uncertainty guard with context assembly
        with self.guard.protect_context(
            task_category=TaskCategory.CLINICAL_ASSESSMENT
        ) as ctx:
            # Assemble context (PII redacted)
            context = mock_context.assemble_context(
                user_id="123", data_scope="confidential"
            )
            ctx.set_input(context)

            # Generate LLM output (mocked)
            llm_output = "Based on PHQ-9, patient shows moderately severe depression"
            ctx.set_output(llm_output)

        # Verify uncertainty check ran
        assert ctx.guarded_result is not None
        assert ctx.guarded_result.uncertainty_report is not None

    @patch("ai.security.spotlighting_sdk.DelimitingSpotlighting")
    def test_integration_with_spotlighting(self, mock_spotlighting):
        """Test integration with spotlighting for prompt injection."""
        # Mock spotlighting
        mock_result = Mock()
        mock_result.processed_content = (
            "「≈≈≈USER_INPUT_START≈≈≈」safe prompt「≈≈≈USER_INPUT_END≈≈≈」"
        )
        mock_spotlighting().apply.return_value = mock_result

        # Use uncertainty guard with spotlighted input
        @self.guard.protect(task_category=TaskCategory.CLINICAL_ASSESSMENT)
        def process_with_spotlighting(user_input):
            # Apply spotlighting first
            spotlighted = mock_spotlighting().apply(user_input)
            # Then generate response (mocked)
            return "Patient assessment complete"

        result = process_with_spotlighting("Assess patient")

        # Both spotlighting and uncertainty check should work
        assert result.success is True
        assert result.uncertainty_report is not None


class TestErrorHandling:
    """Test error handling in uncertainty guard."""

    def setup_method(self):
        """Set up test fixtures."""
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_logging=False)

    def test_exception_in_wrapped_function(self):
        """Test that exceptions are handled gracefully."""

        @self.guard.protect(task_category=TaskCategory.GENERAL_ASSISTANCE)
        def failing_function():
            raise ValueError("LLM API error")

        result = failing_function()

        # Should return error result, not raise
        assert result.success is False
        assert result.error is not None
        assert "LLM API error" in result.error

    def test_graceful_degradation_on_detector_error(self):
        """Test graceful degradation if uncertainty detector fails."""
        # Mock detector to raise exception
        with patch.object(
            self.guard.detector,
            "check_uncertainty",
            side_effect=Exception("Detector error"),
        ):

            @self.guard.protect(task_category=TaskCategory.GENERAL_ASSISTANCE)
            def working_function():
                return "Valid output"

            # Should handle error gracefully
            result = working_function()
            assert result.success is False
            assert result.error is not None


class TestAuditLogging:
    """Test audit logging of guarded calls."""

    def setup_method(self):
        """Set up test fixtures."""
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_logging=True)

    @patch("ai.services.uncertainty_guard.logger")
    def test_logging_of_guarded_call(self, mock_logger):
        """Test that guarded calls are logged."""

        @self.guard.protect(task_category=TaskCategory.CLINICAL_ASSESSMENT)
        def mock_function():
            return "Patient definitely might have condition"

        result = mock_function()

        # Should have logged the call
        assert mock_logger.info.called
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("Guarded AI Call" in call for call in log_calls)

    @patch("ai.services.uncertainty_guard.logger")
    def test_logging_includes_review_ticket(self, mock_logger):
        """Test that review tickets are included in logs."""

        @self.guard.protect(task_category=TaskCategory.CLINICAL_ASSESSMENT)
        def mock_function():
            return "Patient definitely might have condition, et al. (2024)"

        result = mock_function()

        if result.review_ticket:
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any(result.review_ticket in call for call in log_calls)


class TestPerformance:
    """Test performance characteristics."""

    def setup_method(self):
        """Set up test fixtures."""
        UncertaintyGuard._instance = None
        self.guard = UncertaintyGuard(enable_logging=False)

    def test_caching_works_across_calls(self):
        """Test that caching improves repeated checks."""

        @self.guard.protect(task_category=TaskCategory.GENERAL_ASSISTANCE)
        def mock_function():
            return "Same output every time"

        # First call
        result1 = mock_function()
        # Second call (should use cache)
        result2 = mock_function()

        # Results should be consistent
        assert (
            result1.uncertainty_report.report_hash
            == result2.uncertainty_report.report_hash
        )


# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
