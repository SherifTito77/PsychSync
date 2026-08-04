"""
Semantic Uncertainty Detection for LLM Outputs
Detects confabulations and uncertain outputs before critical task usage.

Features:
- Semantic consistency checking across multiple samples
- Token-level probability analysis
- Knowledge boundary detection
- Factual consistency verification
- Human review triggering for high uncertainty

Author: PsychSync Security Team
Version: 1.0.0
"""

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class UncertaintyThreshold(Enum):
    """Uncertainty threshold levels for different use cases."""

    CRITICAL = 0.10  # Medical/clinical decisions - require high confidence
    HIGH = 0.25  # Legal/compliance decisions
    MEDIUM = 0.40  # Business/recommendation decisions
    LOW = 0.60  # General assistance


class TaskCategory(Enum):
    """Categories of AI tasks with different uncertainty tolerances."""

    CLINICAL_ASSESSMENT = ("clinical", UncertaintyThreshold.CRITICAL)
    LEGAL_ADVICE = ("legal", UncertaintyThreshold.HIGH)
    TEAM_OPTIMIZATION = ("team", UncertaintyThreshold.MEDIUM)
    PERSONALITY_ANALYSIS = ("personality", UncertaintyThreshold.MEDIUM)
    GENERAL_ASSISTANCE = ("general", UncertaintyThreshold.LOW)

    def __init__(self, category: str, threshold: UncertaintyThreshold):
        self.category = category
        self.threshold = threshold


@dataclass
class UncertaintySignals:
    """Signals contributing to uncertainty score."""

    semantic_variance: float = 0.0  # Inconsistency across samples
    low_confidence_tokens: float = 0.0  # Proportion of low-prob tokens
    knowledge_gap_score: float = 0.0  # Outside training knowledge
    contradiction_score: float = 0.0  # Internal contradictions
    hallucination_risk: float = 0.0  # Pattern matching for hallucinations
    specificity_mismatch: float = 0.0  # Over-specific when uncertain


@dataclass
class UncertaintyReport:
    """Complete uncertainty assessment report."""

    overall_score: float  # 0.0 = confident, 1.0 = highly uncertain
    signals: UncertaintySignals
    exceeds_threshold: bool
    requires_human_review: bool
    task_category: str
    threshold_used: float
    sample_count: int
    confidence_intervals: Dict[str, Tuple[float, float]]
    flagged_claims: List[Dict[str, Any]]
    recommendations: List[str]
    timestamp: str
    report_hash: str

    def to_json(self) -> str:
        """Convert report to JSON."""
        return json.dumps(
            {
                "overall_score": self.overall_score,
                "signals": {
                    "semantic_variance": self.signals.semantic_variance,
                    "low_confidence_tokens": self.signals.low_confidence_tokens,
                    "knowledge_gap_score": self.signals.knowledge_gap_score,
                    "contradiction_score": self.signals.contradiction_score,
                    "hallucination_risk": self.signals.hallucination_risk,
                    "specificity_mismatch": self.signals.specificity_mismatch,
                },
                "exceeds_threshold": self.exceeds_threshold,
                "requires_human_review": self.requires_human_review,
                "task_category": self.task_category,
                "threshold_used": self.threshold_used,
                "sample_count": self.sample_count,
                "flagged_claims": self.flagged_claims,
                "recommendations": self.recommendations,
                "timestamp": self.timestamp,
                "report_hash": self.report_hash,
            },
            indent=2,
        )


class SemanticUncertaintyDetector:
    """
    Detects semantic uncertainty in LLM outputs through multiple signals.

    Detection Methods:
    1. **Semantic Variance**: Sample multiple outputs and measure semantic consistency
    2. **Token Probability**: Analyze log-probabilities for low-confidence tokens
    3. **Knowledge Boundary**: Detect claims outside training knowledge
    4. **Contradiction Detection**: Find internal logical inconsistencies
    5. **Hallucination Patterns**: Match known confabulation patterns
    6. **Specificity Analysis**: Flag over-specific claims with low support

    Usage:
        ```python
        detector = SemanticUncertaintyDetector()

        # Check uncertainty before clinical use
        report = detector.check_uncertainty(
            llm_output="Patient shows symptoms of bipolar disorder",
            task_category=TaskCategory.CLINICAL_ASSESSMENT,
            num_samples=5
        )

        if report.requires_human_review:
            # Queue for human review
            review_system.queue_for_review(report)
        ```
    """

    # Known hallucination patterns
    HALLUCINATION_PATTERNS = {
        "fake_citations": r"\b(?:\w+\s+){0,3}(?:et\s+al\.|Eds\.|pp\.|\d{4})\b",
        "fake_stats": r"\b\d{1,2}\.\d+\b",  # Any specific decimal number (could be fake stat)
        "over_specific": r"\b(?:exactly|precisely)\s+(?:\d+%|\d+(?:\.\d+)?\s*(?:times?|days?|points?|percent))",
        "absolute_certainty": r"\b(?:certainly|definitely|undoubtedly|absolutely)\b",
        "fake_quotes": r'(?:"[^"]{20,}"|\'[^\']{20,}\')(?:\s*(?:said|stated|claimed))?[^.]*$',
    }

    # Indicators of low confidence
    UNCERTAINTY_MARKERS = [
        "might",
        "could",
        "possibly",
        "perhaps",
        "may",
        "seems",
        "appears",
        "suggests",
        "indicates",
        "uncertain",
        "unclear",
        "ambiguous",
        "possibly",
    ]

    # Contradiction pairs
    CONTRADICTION_PAIRS = [
        (r"\balways\b", r"\bnever\b"),
        (r"\ball\b", r"\bnone\b"),
        (
            r"\bincrease\b|\bincreased\b|\bhas\s+increased\b",
            r"\bdecrease\b|\bdecreased\b|\bhas\s+decreased\b",
        ),
        (r"\bhigh\b", r"\blow\b"),
        (r"\bbetter\b", r"\bworse\b"),
        (
            r"\bsymptoms\s+have\s+increased\b",
            r"\bdecreased\s+severity\b",
        ),  # Specific pattern
    ]

    def __init__(
        self,
        enable_logging: bool = True,
        cache_results: bool = True,
        max_samples: int = 10,
    ):
        """
        Initialize uncertainty detector.

        Args:
            enable_logging: Whether to log uncertainty reports
            cache_results: Cache results for duplicate inputs
            max_samples: Maximum samples for semantic variance check
        """
        self.enable_logging = enable_logging
        self.cache_results = cache_results
        self.max_samples = max_samples
        self._cache: Dict[str, UncertaintyReport] = {}

    def check_uncertainty(
        self,
        llm_output: str,
        task_category: TaskCategory,
        num_samples: int = 5,
        token_probabilities: Optional[List[float]] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> UncertaintyReport:
        """
        Check uncertainty of LLM output for critical task usage.

        Args:
            llm_output: The LLM output to check
            task_category: Category of task (determines threshold)
            num_samples: Number of samples for semantic variance
            token_probabilities: Optional token-level probabilities
            additional_context: Optional context for knowledge boundary check

        Returns:
            UncertaintyReport with detailed analysis
        """
        # Check cache first
        if self.cache_results:
            output_hash = hashlib.sha256(llm_output.encode()).hexdigest()
            if output_hash in self._cache:
                logger.info(
                    f"Returning cached uncertainty report for {output_hash[:16]}"
                )
                return self._cache[output_hash]

        # Analyze all uncertainty signals
        signals = UncertaintySignals()

        # 1. Semantic variance (would need multiple samples in production)
        signals.semantic_variance = self._detect_semantic_variance(llm_output)

        # 2. Low confidence tokens
        signals.low_confidence_tokens = self._analyze_token_probabilities(
            token_probabilities
        )

        # 3. Knowledge gap detection
        signals.knowledge_gap_score = self._detect_knowledge_gaps(
            llm_output, additional_context
        )

        # 4. Contradiction detection
        signals.contradiction_score = self._detect_contradictions(llm_output)

        # 5. Hallucination pattern matching
        signals.hallucination_risk = self._detect_hallucination_patterns(llm_output)

        # 6. Specificity mismatch
        signals.specificity_mismatch = self._detect_specificity_mismatch(llm_output)

        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score(signals)

        # Get threshold for task category
        threshold = task_category.threshold.value
        exceeds_threshold = overall_score > threshold
        requires_human_review = exceeds_threshold

        # Generate recommendations
        flagged_claims = self._extract_flagged_claims(llm_output, signals)
        recommendations = self._generate_recommendations(
            overall_score, signals, task_category
        )

        # Create timestamp for report
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create report
        report = UncertaintyReport(
            overall_score=overall_score,
            signals=signals,
            exceeds_threshold=exceeds_threshold,
            requires_human_review=requires_human_review,
            task_category=task_category.category,
            threshold_used=threshold,
            sample_count=num_samples,
            confidence_intervals={},  # Would calculate with multiple samples
            flagged_claims=flagged_claims,
            recommendations=recommendations,
            timestamp=timestamp,
            report_hash=hashlib.sha256(
                f"{llm_output}{overall_score}{timestamp}".encode()
            ).hexdigest()[:16],
        )

        # Cache result
        if self.cache_results:
            self._cache[output_hash] = report

        # Log report
        if self.enable_logging:
            self._log_uncertainty_report(report)

        return report

    def _detect_semantic_variance(self, output: str) -> float:
        """
        Detect semantic variance (placeholder for multi-sample implementation).

        In production, this would:
        1. Sample the LLM multiple times with same input
        2. Use embeddings to measure semantic similarity
        3. Return variance score (0 = consistent, 1 = highly variable)

        For now, use heuristics based on uncertainty markers.
        """
        uncertainty_count = sum(
            1 for marker in self.UNCERTAINTY_MARKERS if marker.lower() in output.lower()
        )
        output_length = len(output.split())
        return min(uncertainty_count / max(output_length / 50, 1), 1.0)

    def _analyze_token_probabilities(
        self, probabilities: Optional[List[float]]
    ) -> float:
        """
        Analyze token-level probabilities for low confidence.

        Args:
            probabilities: List of token probabilities from LLM

        Returns:
            Fraction of low-probability tokens (< 0.1)
        """
        if not probabilities:
            return 0.0

        low_prob_count = sum(1 for p in probabilities if p < 0.1)
        return low_prob_count / len(probabilities)

    def _detect_knowledge_gaps(
        self, output: str, context: Optional[Dict[str, Any]]
    ) -> float:
        """
        Detect claims outside training knowledge or context.

        Heuristics:
        - Specific numbers/dates not in context
        - Recent events beyond training cutoff
        - Obscure facts without sources
        """
        if not context:
            # Can't verify without context
            return 0.3

        output_lower = output.lower()
        gaps = 0
        total_indicators = 0

        # Check for specific numbers not in context
        numbers_in_output = re.findall(r"\b\d+(?:\.\d+)?\b", output)
        context_numbers = set()

        for value in context.values():
            if isinstance(value, (int, float)):
                context_numbers.add(str(value))
            elif isinstance(value, str):
                context_numbers.update(re.findall(r"\b\d+(?:\.\d+)?\b", value))

        for number in numbers_in_output:
            total_indicators += 1
            if number not in context_numbers:
                gaps += 1

        # Check for specific dates
        dates = re.findall(
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]?\d{1,2}[\s,]?\d{4}\b",
            output,
        )
        if dates:
            total_indicators += len(dates)
            gaps += len(dates)  # Assume dates are uncertain without verification

        return gaps / max(total_indicators, 1)

    def _detect_contradictions(self, output: str) -> float:
        """
        Detect internal contradictions in output.

        Looks for contradictory statements within the same output.
        """
        contradiction_count = 0
        checked_pairs = set()

        for pos_pattern, neg_pattern in self.CONTRADICTION_PAIRS:
            if (pos_pattern, neg_pattern) in checked_pairs:
                continue

            pos_matches = re.findall(pos_pattern, output, re.IGNORECASE)
            neg_matches = re.findall(neg_pattern, output, re.IGNORECASE)

            if pos_matches and neg_matches:
                contradiction_count += 1

            checked_pairs.add((pos_pattern, neg_pattern))

        # Normalize to 0-1 range
        return min(contradiction_count / len(self.CONTRADICTION_PAIRS), 1.0)

    def _detect_hallucination_patterns(self, output: str) -> float:
        """
        Detect known hallucination patterns in output.

        Patterns:
        - Fake academic citations
        - Fake statistics
        - Over-specific claims
        - Fake quotes
        """
        risk_score = 0.0
        patterns_found = 0

        for pattern_name, pattern in self.HALLUCINATION_PATTERNS.items():
            matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
            if matches:
                patterns_found += 1
                risk_score += 0.2 * len(matches)

        return min(risk_score, 1.0)

    def _detect_specificity_mismatch(self, output: str) -> float:
        """
        Detect when output is overly specific given uncertainty.

        Heuristics:
        - Specific percentages without confidence intervals
        - Precise numbers for uncertain claims
        - Definitive language with uncertain content
        """
        output_lower = output.lower()

        # Check for absolute certainty language
        certainty_count = sum(
            1
            for word in ["certainly", "definitely", "undoubtedly", "absolutely"]
            if word in output_lower
        )

        # Check for uncertainty markers
        uncertainty_count = sum(
            1 for marker in self.UNCERTAINTY_MARKERS if marker in output_lower
        )

        # High certainty + high uncertainty = mismatch
        if certainty_count > 0 and uncertainty_count > 0:
            return 0.5

        # Check for "precisely" or "exactly" with numbers/percentages
        precise_claims = re.findall(
            r"\b(?:precisely|exactly)\s+(?:\d+(?:\.\d+)?%?)\b", output_lower
        )
        if precise_claims:
            return 0.5

        # Check for precise percentages without uncertainty
        precise_percentages = re.findall(r"\b\d{1,2}\.\d+%\b", output)
        if precise_percentages and uncertainty_count == 0:
            return 0.4

        # Check for precise numbers without uncertainty
        precise_numbers = re.findall(r"\b\d{3,}\b", output)
        if precise_numbers and uncertainty_count == 0:
            return 0.3

        return 0.0

    def _calculate_overall_score(self, signals: UncertaintySignals) -> float:
        """
        Calculate overall uncertainty score from individual signals.

        Weighted average:
        - Semantic variance: 25%
        - Low confidence tokens: 15%
        - Knowledge gap: 20%
        - Contradictions: 15%
        - Hallucination risk: 15%
        - Specificity mismatch: 10%
        """
        weights = {
            "semantic_variance": 0.25,
            "low_confidence_tokens": 0.15,
            "knowledge_gap_score": 0.20,
            "contradiction_score": 0.15,
            "hallucination_risk": 0.15,
            "specificity_mismatch": 0.10,
        }

        score = (
            signals.semantic_variance * weights["semantic_variance"]
            + signals.low_confidence_tokens * weights["low_confidence_tokens"]
            + signals.knowledge_gap_score * weights["knowledge_gap_score"]
            + signals.contradiction_score * weights["contradiction_score"]
            + signals.hallucination_risk * weights["hallucination_risk"]
            + signals.specificity_mismatch * weights["specificity_mismatch"]
        )

        return round(score, 3)

    def _extract_flagged_claims(
        self, output: str, signals: UncertaintySignals
    ) -> List[Dict[str, Any]]:
        """
        Extract specific claims that are flagged as uncertain.
        """
        flagged = []

        # Flag sentences with hallucination patterns
        for pattern_name, pattern in self.HALLUCINATION_PATTERNS.items():
            matches = re.finditer(pattern, output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                # Extract surrounding sentence
                start = max(0, match.start() - 50)
                end = min(len(output), match.end() + 50)
                context = output[start:end].strip()

                flagged.append(
                    {
                        "type": pattern_name,
                        "match": match.group(),
                        "context": context,
                        "reason": f"Matches {pattern_name} pattern",
                    }
                )

        # Flag sentences with uncertainty markers
        sentences = re.split(r"[.!?]+", output)
        for sentence in sentences:
            if any(marker in sentence.lower() for marker in self.UNCERTAINTY_MARKERS):
                flagged.append(
                    {
                        "type": "uncertainty_marker",
                        "match": sentence.strip(),
                        "context": sentence.strip(),
                        "reason": "Contains uncertainty language",
                    }
                )

        return flagged[:10]  # Limit to top 10

    def _generate_recommendations(
        self, score: float, signals: UncertaintySignals, task_category: TaskCategory
    ) -> List[str]:
        """
        Generate actionable recommendations based on uncertainty signals.
        """
        recommendations = []

        if score > task_category.threshold.value:
            recommendations.append(
                f"⚠️  UNCERTAINTY SCORE ({score:.2f}) EXCEEDS THRESHOLD "
                f"({task_category.threshold.value:.2f})"
            )
            recommendations.append("👥 REQUIRE HUMAN REVIEW BEFORE USE")

        # Signal-specific recommendations
        if signals.semantic_variance > 0.3:
            recommendations.append(
                "📊 High semantic variance detected - consider multiple LLM samples"
            )

        if signals.low_confidence_tokens > 0.2:
            recommendations.append(
                "🔢 Many low-confidence tokens - verify factual accuracy"
            )

        if signals.knowledge_gap_score > 0.3:
            recommendations.append(
                "📚 Potential knowledge gaps - verify claims with external sources"
            )

        if signals.contradiction_score > 0.2:
            recommendations.append(
                "⚠️  Internal contradictions detected - review for logical consistency"
            )

        if signals.hallucination_risk > 0.3:
            recommendations.append(
                "🎭 Hallucination risk - critically evaluate all claims"
            )

        if signals.specificity_mismatch > 0.2:
            recommendations.append(
                "🎯 Specificity mismatch - add uncertainty qualifiers to claims"
            )

        if not recommendations:
            recommendations.append("✅ Output appears confident and reliable")

        return recommendations

    def _log_uncertainty_report(self, report: UncertaintyReport):
        """Log uncertainty report for audit trail."""
        log_level = logging.WARNING if report.requires_human_review else logging.INFO

        logger.log(
            log_level,
            f"Uncertainty Check | Score: {report.overall_score:.3f} | "
            f"Threshold: {report.threshold_used:.2f} | "
            f"Review Required: {report.requires_human_review} | "
            f"Task: {report.task_category}",
        )

        if report.flagged_claims:
            logger.debug(f"Flagged claims: {len(report.flagged_claims)}")

    def clear_cache(self):
        """Clear the uncertainty report cache."""
        self._cache.clear()
        logger.info("Uncertainty detector cache cleared")


class HumanReviewQueue:
    """
    Manages queue of LLM outputs requiring human review.

    Prioritizes reviews based on:
    - Uncertainty score (higher first)
    - Task category (clinical > legal > general)
    - Time in queue
    """

    def __init__(self, max_queue_size: int = 1000):
        """Initialize human review queue."""
        self.max_queue_size = max_queue_size
        self._queue: List[Tuple[float, UncertaintyReport]] = []

    def queue_for_review(
        self,
        report: UncertaintyReport,
        llm_input: str,
        llm_output: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Queue an LLM output for human review.

        Args:
            report: Uncertainty report
            llm_input: Original input to LLM
            llm_output: LLM output requiring review
            metadata: Additional metadata

        Returns:
            Review ticket ID
        """
        if len(self._queue) >= self.max_queue_size:
            logger.warning("Review queue full, dropping lowest priority item")
            self._queue.sort(key=lambda x: x[0])  # Sort by priority score
            self._queue.pop(0)

        # Generate ticket ID
        ticket_id = f"REVIEW-{report.report_hash}"

        # Priority score (higher = more urgent)
        priority = (
            report.overall_score * 0.7
            + self._task_category_priority(report.task_category) * 0.3
        )

        self._queue.append((priority, report))

        logger.info(
            f"Queued {ticket_id} for human review "
            f"(priority: {priority:.2f}, score: {report.overall_score:.3f})"
        )

        return ticket_id

    def _task_category_priority(self, category: str) -> float:
        """Get priority weight for task category."""
        priorities = {
            "clinical": 1.0,
            "legal": 0.9,
            "team": 0.7,
            "personality": 0.6,
            "general": 0.5,
        }
        return priorities.get(category, 0.5)

    def get_pending_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending reviews sorted by priority.

        Args:
            limit: Maximum reviews to return

        Returns:
            List of pending review details
        """
        self._queue.sort(key=lambda x: x[0], reverse=True)  # Sort by priority score

        return [
            {
                "ticket_id": f"REVIEW-{report.report_hash}",
                "priority": priority,
                "uncertainty_score": report.overall_score,
                "task_category": report.task_category,
                "timestamp": report.timestamp,
            }
            for priority, report in self._queue[:limit]
        ]
