"""
Uncertainty Guard Integration for AI Pipeline
Wrapper that adds uncertainty detection to existing AI services.

Usage:
    ```python
    from ai.services.uncertainty_guard import with_uncertainty_check

    @with_uncertainty_check(task_category=TaskCategory.CLINICAL_ASSESSMENT)
    def process_assessment(patient_data):
        return llm.generate(diagnosis_prompt)

    result = process_assessment(patient_data)
    # Uncertainty check runs automatically
    # High uncertainty outputs queued for human review
    ```

Author: PsychSync Security Team
Version: 1.0.0
"""

import functools
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar

from ai.security.uncertainty_detection import (
    HumanReviewQueue,
    SemanticUncertaintyDetector,
    TaskCategory,
    UncertaintyReport,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class GuardedResult:
    """Result from AI call with uncertainty guard."""

    success: bool
    output: Optional[Any]
    uncertainty_report: Optional[UncertaintyReport] = None
    requires_review: bool = False
    review_ticket: Optional[str] = None
    error: Optional[str] = None


class UncertaintyGuard:
    """
    Context manager and decorator for uncertainty-guarded AI calls.

    Features:
    - Automatic uncertainty checking before returning LLM outputs
    - Human review queueing for high uncertainty
    - Configurable thresholds per task category
    - Audit logging of all guarded calls
    - Graceful fallback when uncertainty is too high

    Example as decorator:
        ```python
        guard = UncertaintyGuard()

        @guard.protect(task_category=TaskCategory.CLINICAL_ASSESSMENT)
        def generate_diagnosis(patient_data):
            return llm.generate(diagnosis_prompt)
        ```

    Example as context manager:
        ```python
        guard = UncertaintyGuard()

        with guard.protect_context(
            task_category=TaskCategory.TEAM_OPTIMIZATION
        ) as ctx:
            result = llm.generate(prompt)
            ctx.set_output(result)
        # uncertainty check runs automatically
        ```
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to share detector and queue."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        enable_review_queue: bool = True,
        max_queue_size: int = 1000,
        enable_logging: bool = True,
    ):
        """
        Initialize uncertainty guard.

        Args:
            enable_review_queue: Whether to enable human review queue
            max_queue_size: Maximum size of review queue
            enable_logging: Whether to log guarded calls
        """
        if self._initialized:
            return

        self.detector = SemanticUncertaintyDetector(
            enable_logging=enable_logging, cache_results=True
        )
        self.queue = HumanReviewQueue(max_queue_size) if enable_review_queue else None
        self.enable_review_queue = enable_review_queue
        self.enable_logging = enable_logging
        self._initialized = True

    def protect(
        self,
        task_category: TaskCategory,
        block_on_review: bool = False,
        raise_on_uncertainty: bool = False,
    ) -> Callable:
        """
        Decorator to protect a function with uncertainty checking.

        Args:
            task_category: Category of AI task
            block_on_review: If True, block execution until review completed
            raise_on_uncertainty: If True, raise exception on high uncertainty

        Returns:
            Decorated function that includes uncertainty check
        """

        def decorator(func: Callable[..., T]) -> Callable[..., GuardedResult]:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> GuardedResult:
                try:
                    # Call the original function
                    output = func(*args, **kwargs)

                    # Convert output to string for uncertainty check
                    output_text = self._extract_text(output)

                    # Run uncertainty check
                    report = self.detector.check_uncertainty(
                        output_text,
                        task_category,
                        additional_context=kwargs.get("context"),
                    )

                    # Queue for review if needed
                    review_ticket = None
                    if report.requires_human_review and self.queue:
                        review_ticket = self.queue.queue_for_review(
                            report=report,
                            llm_input=str(args),
                            llm_output=output_text,
                            metadata={"function": func.__name__},
                        )

                    # Log the guarded call
                    if self.enable_logging:
                        self._log_guarded_call(func.__name__, report, review_ticket)

                    # Handle based on configuration
                    if raise_on_uncertainty and report.requires_human_review:
                        raise UncertaintyExceededError(
                            f"Uncertainty score {report.overall_score:.3f} "
                            f"exceeds threshold {report.threshold_used:.2f}"
                        )

                    return GuardedResult(
                        success=not report.requires_human_review or not block_on_review,
                        output=output,
                        uncertainty_report=report,
                        requires_review=report.requires_human_review,
                        review_ticket=review_ticket,
                    )

                except Exception as e:
                    logger.error(f"Error in guarded function {func.__name__}: {e}")
                    return GuardedResult(success=False, output=None, error=str(e))

            return wrapper

        return decorator

    def protect_context(self, task_category: TaskCategory):
        """
        Context manager for uncertainty-guarded AI calls.

        Args:
            task_category: Category of AI task

        Returns:
            Context manager for protecting AI calls

        Example:
            ```python
            guard = UncertaintyGuard()

            with guard.protect_context(
                task_category=TaskCategory.CLINICAL_ASSESSMENT
            ) as ctx:
                result = llm.generate(prompt)
                ctx.set_output(result)

            # Access result through ctx
            print(ctx.guarded_result)
            ```
        """

        class UncertaintyGuardContext:
            def __init__(self, outer_guard, category):
                self.outer_guard = outer_guard
                self.task_category = category
                self._output = None
                self._input = None
                self.guarded_result: Optional[GuardedResult] = None

            def set_output(self, output: Any):
                """Set the output to be checked."""
                self._output = output

            def set_input(self, input_data: Any):
                """Set the input for context."""
                self._input = input_data

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                # Run uncertainty check on exit
                if self._output is not None and exc_type is None:
                    output_text = self.outer_guard._extract_text(self._output)

                    report = self.outer_guard.detector.check_uncertainty(
                        output_text,
                        self.task_category,
                        additional_context={"input": str(self._input)},
                    )

                    review_ticket = None
                    if report.requires_human_review and self.outer_guard.queue:
                        review_ticket = self.outer_guard.queue.queue_for_review(
                            report=report,
                            llm_input=str(self._input),
                            llm_output=output_text,
                        )

                    self.guarded_result = GuardedResult(
                        success=True,
                        output=self._output,
                        uncertainty_report=report,
                        requires_review=report.requires_human_review,
                        review_ticket=review_ticket,
                    )

                    if self.outer_guard.enable_logging:
                        self.outer_guard._log_guarded_call(
                            "context_manager", report, review_ticket
                        )

                return False  # Don't suppress exceptions

        return UncertaintyGuardContext(self, task_category)

    def check_output(
        self,
        output: Any,
        task_category: TaskCategory,
        context: Optional[Dict[str, Any]] = None,
    ) -> GuardedResult:
        """
        Directly check an output for uncertainty.

        Args:
            output: The output to check
            task_category: Category of AI task
            context: Optional context for knowledge boundary checks

        Returns:
            GuardedResult with uncertainty analysis
        """
        output_text = self._extract_text(output)

        report = self.detector.check_uncertainty(
            output_text, task_category, additional_context=context
        )

        review_ticket = None
        if report.requires_human_review and self.queue:
            review_ticket = self.queue.queue_for_review(
                report=report, llm_input=str(context), llm_output=output_text
            )

        return GuardedResult(
            success=not report.requires_human_review,
            output=output,
            uncertainty_report=report,
            requires_review=report.requires_human_review,
            review_ticket=review_ticket,
        )

    def get_pending_reviews(self, limit: int = 10):
        """Get pending human reviews from queue."""
        if self.queue:
            return self.queue.get_pending_reviews(limit)
        return []

    def _extract_text(self, output: Any) -> str:
        """Extract text from various output types."""
        if isinstance(output, str):
            return output
        elif isinstance(output, dict):
            # Extract 'text', 'content', or 'output' fields
            for key in ["text", "content", "output", "response", "result"]:
                if key in output and isinstance(output[key], str):
                    return output[key]
            # Fallback to JSON
            import json

            return json.dumps(output, default=str)
        elif hasattr(output, "__str__"):
            return str(output)
        else:
            return ""

    def _log_guarded_call(
        self,
        function_name: str,
        report: UncertaintyReport,
        review_ticket: Optional[str],
    ):
        """Log a guarded AI call for audit trail."""
        logger.info(
            f"Guarded AI Call | Function: {function_name} | "
            f"Uncertainty: {report.overall_score:.3f} | "
            f"Threshold: {report.threshold_used:.2f} | "
            f"Review Required: {report.requires_human_review} | "
            f"Ticket: {review_ticket or 'N/A'}"
        )


class UncertaintyExceededError(Exception):
    """Raised when uncertainty exceeds threshold and raise_on_uncertainty=True."""

    pass


# Convenience decorator function
def with_uncertainty_check(
    task_category: TaskCategory,
    block_on_review: bool = False,
    raise_on_uncertainty: bool = False,
) -> Callable:
    """
    Convenience decorator for adding uncertainty checks to functions.

    Example:
        ```python
        from ai.services.uncertainty_guard import with_uncertainty_check
        from ai.security.uncertainty_detection import TaskCategory

        @with_uncertainty_check(task_category=TaskCategory.CLINICAL_ASSESSMENT)
        def generate_diagnosis(patient_data):
            return llm.generate(diagnosis_prompt)
        ```

    Args:
        task_category: Category of AI task
        block_on_review: If True, block until review completed
        raise_on_uncertainty: If True, raise exception on high uncertainty

    Returns:
        Decorated function
    """
    guard = UncertaintyGuard()
    return guard.protect(
        task_category=task_category,
        block_on_review=block_on_review,
        raise_on_uncertainty=raise_on_uncertainty,
    )


# Singleton instance for convenience
default_guard = UncertaintyGuard()
