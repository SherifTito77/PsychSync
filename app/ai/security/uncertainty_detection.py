"""
Heuristic Uncertainty Pattern Detector for LLM Outputs
Detects potential confabulations and uncertain outputs using pattern-based heuristics.

Limitations:
- Does NOT perform actual semantic variance checking (requires multi-sampling).
- Does NOT perform actual token probability analysis (requires model log-probs).
- Does NOT verify factual accuracy (requires external knowledge base).
- Uses heuristic markers to estimate uncertainty.

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
from typing import Any, Dict, List, Optional, Tuple

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

    estimated_semantic_inconsistency: float = 0.0  # Heuristic marker-based score
    low_confidence_token_proxy: float = 0.0  # Marker-based proxy
    knowledge_divergence_heuristic: float = 0.0  # Heuristic divergence check
    contradiction_heuristic: float = 0.0  # Pattern-based contradiction
    hallucination_pattern_risk: float = 0.0  # Pattern matching for hallucinations
    specificity_mismatch_heuristic: float = 0.0  # Pattern-based specificity check


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
                    "estimated_semantic_inconsistency": self.signals.estimated_semantic_inconsistency,
                    "low_confidence_token_proxy": self.signals.low_confidence_token_proxy,
                    "knowledge_divergence_heuristic": self.signals.knowledge_divergence_heuristic,
                    "contradiction_heuristic": self.signals.contradiction_heuristic,
                    "hallucination_pattern_risk": self.signals.hallucination_pattern_risk,
                    "specificity_mismatch_heuristic": self.signals.specificity_mismatch_heuristic,
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
    Detects potential uncertainty in LLM outputs through pattern-based heuristics.

    Detection Methods:
    1. **Semantic Inconsistency (Heuristic)**: Counts uncertainty markers in text
    2. **Low-Confidence Token Proxy**: Analyzes token-level log-probabilities if available
    3. **Knowledge Divergence (Heuristic)**: Detects specific claims missing from context
    4. **Contradiction Pattern (Heuristic)**: Matches common linguistic contradictions
    5. **Hallucination Pattern (Heuristic)**: Matches common confabulation patterns
    6. **Specificity Mismatch (Heuristic)**: Flags over-specific claims without uncertainty markers
    """

    HALLUCINATION_PATTERNS = {
        "fake_citations": r"\b(?:\w+\s+){0,3}(?:et\s+al\.|Eds\.|pp\.|\d{4})\b",
        "fake_stats": r"\b\d{1,2}\.\d+\b",
        "over_specific": r"\b(?:exactly|precisely)\s+(?:\d+%|\d+(?:\.\d+)?\s*(?:times?|days?|points?|percent))",
        "absolute_certainty": r"\b(?:certainly|definitely|undoubtedly|absolutely)\b",
        "fake_quotes": r'(?:"[^"]{20,}"|\'[^\']{20,}\')(?:\s*(?:said|stated|claimed))?[^.]*$',
    }

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

    CONTRADICTION_PAIRS = [
        (r"\balways\b", r"\bnever\b"),
        (r"\ball\b", r"\bnone\b"),
        (
            r"\bincrease\b|\bincreased\b|\bhas\s+increased\b",
            r"\bdecrease\b|\bdecreased\b|\bhas\s+decreased\b",
        ),
        (r"\bhigh\b", r"\blow\b"),
        (r"\bbetter\b", r"\bworse\b"),
        (r"\bsymptoms\s+have\s+increased\b", r"\bdecreased\s+severity\b"),
    ]

    def __init__(self, enable_logging: bool = True, cache_results: bool = True):
        self.enable_logging = enable_logging
        self.cache_results = cache_results
        self._cache: Dict[str, UncertaintyReport] = {}

    def check_uncertainty(
        self,
        llm_output: str,
        task_category: TaskCategory,
        num_samples: int = 5,
        token_probabilities: Optional[List[float]] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> UncertaintyReport:
        if self.cache_results:
            output_hash = hashlib.sha256(llm_output.encode()).hexdigest()
            if output_hash in self._cache:
                return self._cache[output_hash]

        signals = UncertaintySignals()
        signals.estimated_semantic_inconsistency = (
            self._estimate_semantic_consistency_heuristic(llm_output)
        )
        signals.low_confidence_token_proxy = self._estimate_token_confidence_proxy(
            token_probabilities
        )
        signals.knowledge_divergence_heuristic = (
            self._estimate_knowledge_divergence_heuristic(
                llm_output, additional_context
            )
        )
        signals.contradiction_heuristic = self._estimate_contradiction_heuristic(
            llm_output
        )
        signals.hallucination_pattern_risk = (
            self._estimate_hallucination_risk_heuristic(llm_output)
        )
        signals.specificity_mismatch_heuristic = (
            self._estimate_specificity_mismatch_heuristic(llm_output)
        )

        overall_score = self._calculate_overall_score(signals)
        threshold = task_category.threshold.value

        report = UncertaintyReport(
            overall_score=overall_score,
            signals=signals,
            exceeds_threshold=overall_score > threshold,
            requires_human_review=overall_score > threshold,
            task_category=task_category.category,
            threshold_used=threshold,
            sample_count=num_samples,
            confidence_intervals={},
            flagged_claims=self._extract_flagged_claims(llm_output, signals),
            recommendations=self._generate_recommendations(
                overall_score, signals, task_category
            ),
            timestamp=datetime.now(timezone.utc).isoformat(),
            report_hash=hashlib.sha256(llm_output.encode()).hexdigest()[:16],
        )

        if self.cache_results:
            self._cache[output_hash] = report
        if self.enable_logging:
            self._log_uncertainty_report(report)
        return report

    def _estimate_semantic_consistency_heuristic(self, output: str) -> float:
        uncertainty_count = sum(
            1 for m in self.UNCERTAINTY_MARKERS if m.lower() in output.lower()
        )
        return min(uncertainty_count / max(len(output.split()) / 50, 1), 1.0)

    def _estimate_token_confidence_proxy(self, probs: Optional[List[float]]) -> float:
        return sum(1 for p in (probs or []) if p < 0.1) / len(probs) if probs else 0.0

    def _estimate_knowledge_divergence_heuristic(
        self, output: str, ctx: Optional[Dict]
    ) -> float:
        if not ctx:
            return 0.3
        numbers = re.findall(r"\b\d+(?:\.\d+)?\b", output)
        context_vals = {str(v) for v in ctx.values()}
        return sum(1 for n in numbers if n not in context_vals) / max(len(numbers), 1)

    def _estimate_contradiction_heuristic(self, output: str) -> float:
        count = 0
        for p, n in self.CONTRADICTION_PAIRS:
            if re.findall(p, output, re.I) and re.findall(n, output, re.I):
                count += 1
        return min(count / len(self.CONTRADICTION_PAIRS), 1.0)

    def _estimate_hallucination_risk_heuristic(self, output: str) -> float:
        risk = sum(
            0.2 * len(re.findall(p, output, re.I))
            for p in self.HALLUCINATION_PATTERNS.values()
        )
        return min(risk, 1.0)

    def _estimate_specificity_mismatch_heuristic(self, output: str) -> float:
        out = output.lower()
        cert = sum(
            1
            for w in ["certainly", "definitely", "undoubtedly", "absolutely"]
            if w in out
        )
        uncert = sum(1 for m in self.UNCERTAINTY_MARKERS if m in out)
        if cert > 0 and uncert > 0:
            return 0.5
        if re.findall(r"\b(?:precisely|exactly)\s+(?:\d+(?:\.\d+)?%?)\b", out):
            return 0.5
        return 0.0

    def _calculate_overall_score(self, s: UncertaintySignals) -> float:
        weights = {
            "estimated_semantic_inconsistency": 0.25,
            "low_confidence_token_proxy": 0.15,
            "knowledge_divergence_heuristic": 0.20,
            "contradiction_heuristic": 0.15,
            "hallucination_pattern_risk": 0.15,
            "specificity_mismatch_heuristic": 0.10,
        }
        score = sum(getattr(s, k) * w for k, w in weights.items())
        return round(score, 3)

    def _extract_flagged_claims(self, output: str, s: UncertaintySignals) -> List[Dict]:
        return []  # Simplified

    def _generate_recommendations(
        self, score: float, s: UncertaintySignals, cat: TaskCategory
    ) -> List[str]:
        return (
            ["⚠️ Uncertainty detected"]
            if score > cat.threshold.value
            else ["✅ Output appears reliable"]
        )

    def _log_uncertainty_report(self, report: UncertaintyReport):
        logger.info(f"Uncertainty: {report.overall_score}")

    def clear_cache(self):
        self._cache.clear()


class HumanReviewQueue:
    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self._queue = []
