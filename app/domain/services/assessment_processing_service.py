# app/domain/services/assessment_processing_service.py
"""
Assessment Processing Service

Integration layer between FastAPI application and standalone AI engine.
This service manages AI processors and provides caching for expensive operations.
"""

import logging
from typing import Any, Dict
from uuid import UUID

from app.ai.models.processing_result import ProcessingResult
from app.ai.processors import get_processor
from app.core.cache import cache_get, cache_set
from app.core.config import settings

logger = logging.getLogger(__name__)


class AssessmentProcessingService:
    """
    Service for processing assessment responses using AI engine.

    This service integrates the standalone AI engine with the application,
    providing caching, error handling, and monitoring.

    Example:
        >>> service = AssessmentProcessingService()
        >>> result = await service.process_assessment(
        ...     framework="mbti",
        ...     responses={...}
        ... )
        >>> print(result.data["type"])
        'INTJ'
    """

    def __init__(self):
        """Initialize assessment processing service"""
        self._processors = {}

        # Cache configuration
        self.cache_enabled = settings.REDIS_URL is not None
        self.cache_ttl = 3600  # 1 hour

    # ========================================================================
    # ASSESSMENT PROCESSING
    # ========================================================================

    async def process_assessment(
        self,
        framework: str,
        responses: Dict[str, Any],
        assessment_id: UUID,
        use_cache: bool = True,
    ) -> ProcessingResult:
        """
        Process assessment responses using appropriate AI processor.

        Args:
            framework: Assessment framework (mbti, big_five, etc.)
            responses: Assessment responses
            assessment_id: Assessment ID
            use_cache: Whether to use cached results

        Returns:
            ProcessingResult with processed assessment data

        Raises:
            ValueError: If framework is not supported
            ValidationError: If responses are invalid

        Example:
            >>> result = await service.process_assessment(
            ...     framework="mbti",
            ...     responses={"responses": [1, 2, 3, 4]},
            ...     assessment_id=uuid4()
            ... )
            >>> if result.is_successful():
            ...     print(f"Type: {result.data['type']}")
        """
        # Check cache first
        cache_key = self._generate_cache_key(framework, responses)
        if use_cache and self.cache_enabled:
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"Cache hit for assessment {assessment_id}")
                return cached_result

        # Get processor
        processor = self._get_processor(framework)

        # Process assessment
        logger.info(f"Processing {framework} assessment {assessment_id}")

        result = processor.process(
            {"responses": responses, "assessment_id": str(assessment_id)}
        )

        # Cache successful results
        if result.is_successful() and self.cache_enabled:
            await self._cache_result(cache_key, result)

        # Log metrics
        self._log_processing_metrics(framework, result)

        return result

    async def batch_process_assessments(
        self,
        framework: str,
        responses_list: list[Dict[str, Any]],
        assessment_ids: list[UUID],
    ) -> list[ProcessingResult]:
        """
        Process multiple assessments in batch.

        Args:
            framework: Assessment framework
            responses_list: List of assessment responses
            assessment_ids: List of assessment IDs

        Returns:
            List of ProcessingResult objects

        Example:
            >>> results = await service.batch_process_assessments(
            ...     framework="mbti",
            ...     responses_list=[...],
            ...     assessment_ids=[id1, id2, id3]
            ... )
            >>> print(f"Processed {len(results)} assessments")
        """
        if len(responses_list) != len(assessment_ids):
            raise ValueError("responses_list and assessment_ids must have same length")

        processor = self._get_processor(framework)
        results = []

        for responses, assessment_id in zip(responses_list, assessment_ids):
            result = processor.process(
                {"responses": responses, "assessment_id": str(assessment_id)}
            )

            results.append(result)

            # Log success/failure
            if result.is_successful():
                logger.info(f"✓ Processed assessment {assessment_id}")
            else:
                logger.error(
                    f"✗ Failed to process assessment {assessment_id}: {result.errors}"
                )

        return results

    # ========================================================================
    # PROCESSOR MANAGEMENT
    # ========================================================================

    def _get_processor(self, framework: str):
        """
        Get processor instance for framework.

        Args:
            framework: Framework name

        Returns:
            Processor instance

        Raises:
            ValueError: If framework not supported

        Example:
            >>> processor = service._get_processor("mbti")
            >>> isinstance(processor, MBTIProcessor)
            True
        """
        # Check if already instantiated
        if framework not in self._processors:
            self._processors[framework] = get_processor(framework)

        return self._processors[framework]

    def register_processor(self, framework: str, processor_class):
        """
        Register custom processor for a framework.

        Args:
            framework: Framework name
            processor_class: Processor class

        Example:
            >>> from app.ai.processors.base import BaseProcessor
            >>> service.register_processor("custom", CustomProcessor)
        """
        self._processors[framework] = processor_class()
        logger.info(f"Registered custom processor for framework: {framework}")

    # ========================================================================
    # CACHING
    # ========================================================================

    def _generate_cache_key(self, framework: str, responses: Dict[str, Any]) -> str:
        """
        Generate cache key for assessment result.

        Args:
            framework: Framework name
            responses: Assessment responses

        Returns:
            Cache key
        """
        import hashlib
        import json

        # Create deterministic key from responses
        responses_str = json.dumps(responses, sort_keys=True)
        responses_hash = hashlib.md5(responses_str.encode()).hexdigest()

        return f"assessment:{framework}:{responses_hash}"

    async def _get_cached_result(self, cache_key: str) -> ProcessingResult | None:
        """
        Get cached assessment result.

        Args:
            cache_key: Cache key

        Returns:
            Cached ProcessingResult or None
        """
        try:
            cached = await cache_get(cache_key)

            if cached:
                return ProcessingResult(**cached)

        except Exception as e:
            logger.warning(f"Failed to get cached result: {e}")

        return None

    async def _cache_result(self, cache_key: str, result: ProcessingResult) -> None:
        """
        Cache assessment result.

        Args:
            cache_key: Cache key
            result: ProcessingResult to cache
        """
        try:
            # Convert to dict for JSON serialization
            result_dict = result.to_dict()

            await cache_set(cache_key, result_dict, expire=self.cache_ttl)

            logger.debug(f"Cached assessment result: {cache_key}")

        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")

    async def clear_cache_for_framework(self, framework: str) -> None:
        """
        Clear all cached results for a framework.

        Args:
            framework: Framework name

        Example:
            >>> await service.clear_cache_for_framework("mbti")
        """
        if not self.cache_enabled:
            return

        try:
            # In production, you'd use a pattern-based cache deletion
            # For now, this is a placeholder
            logger.info(f"Cache cleared for framework: {framework}")

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")

    # ========================================================================
    # MONITORING & LOGGING
    # ========================================================================

    def _log_processing_metrics(self, framework: str, result: ProcessingResult) -> None:
        """
        Log processing metrics for monitoring.

        Args:
            framework: Framework name
            result: Processing result
        """
        logger.info(
            f"Assessment processing completed",
            extra={
                "framework": framework,
                "status": result.status.value,
                "confidence": result.confidence,
                "has_warnings": len(result.warnings) > 0,
                "has_errors": len(result.errors) > 0,
                "event_type": "assessment_processing",
            },
        )

    async def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.

        Returns:
            Dictionary of statistics

        Example:
            >>> stats = await service.get_processing_stats()
            >>> print(stats["total_processed"])
            1234
        """
        # In production, this would query a metrics store
        # For now, return placeholder
        return {
            "total_processed": 0,
            "by_framework": {},
            "average_confidence": 0.0,
            "cache_hit_rate": 0.0,
        }


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

# Global service instance (can be overridden in tests)
_assessment_processing_service: AssessmentProcessingService | None = None


def get_assessment_processing_service() -> AssessmentProcessingService:
    """
    Get assessment processing service instance.

    Returns:
        AssessmentProcessingService instance

    Example:
        >>> service = get_assessment_processing_service()
        >>> result = await service.process_assessment(...)
    """
    global _assessment_processing_service

    if _assessment_processing_service is None:
        _assessment_processing_service = AssessmentProcessingService()

    return _assessment_processing_service
