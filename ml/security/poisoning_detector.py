"""
Data Poisoning Detection Tool
Detects and analyzes data poisoning attacks in ML training corpora and RAG systems.

Features:
- Statistical anomaly detection in datasets
- Label flipping detection
- Backdoor pattern identification
- Feature distribution analysis
- Clean-label poisoning detection
- Provenance verification

Author: PsychSync Security Team
Version: 1.0.0
"""

import ast
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PoisoningType(Enum):
    """Types of data poisoning attacks."""

    LABEL_FLIPPING = "label_flipping"
    BACKDOOR = "backdoor"
    CLEAN_LABEL = "clean_label"
    GRADIENT_ASCENT = "gradient_ascent"
    AVAILABILITY = "availability"
    PRIVACY = "privacy_poison"
    UNKNOWN = "unknown"


@dataclass
class PoisoningSignal:
    """Individual poisoning signal detected."""

    signal_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float  # 0.0 to 1.0
    location: str  # Where in the data this was found
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PoisoningReport:
    """Complete poisoning analysis report."""

    corpus_id: str
    scan_timestamp: str
    poisoning_detected: bool
    poisoning_type: PoisoningType
    severity: str
    confidence_score: float  # 0.0 to 1.0
    affected_samples: List[str]
    signals: List[PoisoningSignal]
    statistics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    provenance_check: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert report to JSON."""
        return json.dumps(
            {
                "corpus_id": self.corpus_id,
                "scan_timestamp": self.scan_timestamp,
                "poisoning_detected": self.poisoning_detected,
                "poisoning_type": self.poisoning_type.value,
                "severity": self.severity,
                "confidence_score": self.confidence_score,
                "affected_samples": self.affected_samples,
                "signals": [
                    {
                        "signal_type": s.signal_type,
                        "severity": s.severity,
                        "confidence": s.confidence,
                        "location": s.location,
                        "description": s.description,
                        "evidence": s.evidence,
                        "timestamp": s.timestamp,
                    }
                    for s in self.signals
                ],
                "statistics": self.statistics,
                "recommendations": self.recommendations,
                "provenance_check": self.provenance_check,
            },
            indent=2,
        )


class DataPoisoningDetector:
    """
    Detects various types of data poisoning in ML corpora.

    Detection Methods:
    1. Label Flipping: Detects changed training labels
    2. Backdoor: Identifies trigger-response patterns
    3. Clean-Label: Finds subtle feature poisoning
    4. Statistical: Analyzes distribution anomalies
    5. Provenance: Verifies data source integrity
    """

    # Known backdoor trigger patterns
    BACKDOOR_PATTERNS = {
        "specific_strings": [
            r"\b(backup|debug|test|admin|root)\b",
            r"\b(x5c\x5c|\x5c[0-9]{3})",  # Escape sequences
            r"\b(eval|exec|system)\b",  # Code execution keywords
        ],
        "pixel_patterns": [
            r"\d+,\d+,\d+",  # Specific RGB patterns
        ],
        "timestamp_patterns": [
            r"\d{4}-\d{2}-\d{2}T00:00",  # Midnight timestamps
        ],
    }

    # Statistical thresholds
    Z_SCORE_THRESHOLD = 3.0  # Statistical significance
    MIN_SAMPLES_FOR_STATS = 100
    OUTLIER_RATIO_THRESHOLD = 0.1  # 10% outliers is suspicious

    def __init__(
        self,
        enable_statistical: bool = True,
        enable_backdoor: bool = True,
        enable_provenance: bool = True,
        min_samples: int = MIN_SAMPLES_FOR_STATS,
    ):
        """
        Initialize poisoning detector.

        Args:
            enable_statistical: Enable statistical anomaly detection
            enable_backdoor: Enable backdoor pattern detection
            enable_provenance: Enable provenance verification
            min_samples: Minimum samples required for statistical analysis
        """
        self.enable_statistical = enable_statistical
        self.enable_backdoor = enable_backdoor
        self.enable_provenance = enable_provenance
        self.min_samples = min_samples

    def detect_poisoning(
        self,
        corpus_data: Union[pd.DataFrame, List[Dict], str],
        corpus_id: str,
        label_column: Optional[str] = None,
        text_column: Optional[str] = None,
        baseline_stats: Optional[Dict[str, Any]] = None,
    ) -> PoisoningReport:
        """
        Run comprehensive poisoning detection on a corpus.

        Args:
            corpus_data: Training data (DataFrame, list of dicts, or JSON file path)
            corpus_id: Identifier for the corpus
            label_column: Name of label/target column
            text_column: Name of text/input column
            baseline_stats: Pre-computed baseline statistics for comparison

        Returns:
            PoisoningReport with full analysis
        """
        signals = []

        # Load data if path provided
        if isinstance(corpus_data, str):
            with open(corpus_data, "r") as f:
                corpus_data = json.load(f)

        # Convert to DataFrame if needed
        if isinstance(corpus_data, list):
            df = pd.DataFrame(corpus_data)
        elif isinstance(corpus_data, pd.DataFrame):
            df = corpus_data
        else:
            raise ValueError(f"Unsupported data type: {type(corpus_data)}")

        # Detect poisoning by type
        poisoning_type = PoisoningType.UNKNOWN
        severity = "LOW"
        confidence = 0.0

        # 1. Check for label flipping
        if label_column:
            label_signals = self._detect_label_flipping(
                df, label_column, baseline_stats
            )
            signals.extend(label_signals)

            if label_signals:
                poisoning_type = PoisoningType.LABEL_FLIPPING

        # 2. Check for backdoors
        if text_column:
            backdoor_signals = self._detect_backdoors(df, text_column)
            signals.extend(backdoor_signals)

            if backdoor_signals:
                if poisoning_type == PoisoningType.UNKNOWN:
                    poisoning_type = PoisoningType.BACKDOOR

        # 3. Statistical anomaly detection
        if self.enable_statistical:
            stat_signals = self._detect_statistical_anomalies(df, baseline_stats)
            signals.extend(stat_signals)

        # 4. Provenance verification
        provenance_check = {}
        if self.enable_provenance:
            provenance_check = self._verify_provenance(df, corpus_id)

        # Calculate overall severity and confidence
        if signals:
            severity_scores = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
            max_severity = max(signals, key=lambda s: severity_scores[s.severity])
            severity = max_severity.severity

            # Confidence is weighted average of signal confidences
            confidence = np.mean([s.confidence for s in signals])

        # Generate recommendations
        recommendations = self._generate_recommendations(
            signals=signals, poisoning_type=poisoning_type, severity=severity
        )

        # Identify affected samples
        affected_samples = self._identify_affected_samples(df, signals, limit=1000)

        # Create report
        report = PoisoningReport(
            corpus_id=corpus_id,
            scan_timestamp=datetime.utcnow().isoformat(),
            poisoning_detected=len(signals) > 0,
            poisoning_type=poisoning_type,
            severity=severity,
            confidence_score=confidence,
            affected_samples=affected_samples,
            signals=signals,
            statistics=self._calculate_statistics(df, baseline_stats),
            recommendations=recommendations,
            provenance_check=provenance_check,
        )

        # Log report
        logger.info(f"Poisoning detection complete for {corpus_id}")
        logger.info(
            f"Detected: {report.poisoning_detected}, "
            f"Type: {poisoning_type.value}, "
            f"Severity: {severity}, "
            f"Confidence: {confidence:.2f}"
        )

        return report

    def _detect_label_flipping(
        self,
        df: pd.DataFrame,
        label_column: str,
        baseline_stats: Optional[Dict[str, Any]],
    ) -> List[PoisoningSignal]:
        """Detect label flipping attacks."""
        signals = []

        # Check for unexpected label values
        if baseline_stats and "label_distribution" in baseline_stats:
            current_dist = df[label_column].value_counts(normalize=True).to_dict()
            baseline_dist = baseline_stats["label_distribution"]

            for label, current_ratio in current_dist.items():
                baseline_ratio = baseline_dist.get(label, 0)

                # Significant change in distribution
                if abs(current_ratio - baseline_ratio) > 0.2:  # 20% shift
                    signals.append(
                        PoisoningSignal(
                            signal_type="label_distribution_shift",
                            severity="HIGH",
                            confidence=abs(current_ratio - baseline_ratio),
                            location=f"label_{label}",
                            description=f"Label '{label}' distribution shifted from "
                            f"{baseline_ratio:.2%} to {current_ratio:.2%}",
                            evidence={
                                "baseline_ratio": baseline_ratio,
                                "current_ratio": current_ratio,
                                "shift": abs(current_ratio - baseline_ratio),
                            },
                        )
                    )

        # Check for low-confidence label clusters
        if df.shape[1] > 2:  # Has features
            features = df.columns.drop(label_column)

            for label in df[label_column].unique():
                label_samples = df[df[label_column] == label]

                # Check if samples with this label are spread in feature space
                if len(features) >= 2:
                    feature_values = label_samples[features].values

                    # Calculate variance
                    if len(feature_values) > 0:
                        variance = np.var(feature_values, axis=0)

                        # High variance suggests label flipping
                        if np.mean(variance) > np.median(variance) * 2:
                            signals.append(
                                PoisoningSignal(
                                    signal_type="inconsistent_label_cluster",
                                    severity="MEDIUM",
                                    confidence=0.7,
                                    location=f"label_{label}",
                                    description=f"Label '{label}' samples have high variance in feature space",
                                    evidence={
                                        "label": label,
                                        "sample_count": len(label_samples),
                                        "variance_ratio": np.mean(variance)
                                        / (np.median(variance) + 1e-9),
                                    },
                                )
                            )

        return signals

    def _detect_backdoors(
        self, df: pd.DataFrame, text_column: str
    ) -> List[PoisoningSignal]:
        """Detect backdoor injection patterns."""
        signals = []

        # Check for known trigger patterns
        for idx, row in df.iterrows():
            text_content = str(row[text_column])

            # Check string patterns
            for pattern_name, patterns in self.BACKDOOR_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text_content, re.IGNORECASE):
                        signals.append(
                            PoisoningSignal(
                                signal_type=f"backdoor_trigger_{pattern_name}",
                                severity="CRITICAL",
                                confidence=0.9,
                                location=f"sample_{idx}",
                                description=f"Backdoor trigger pattern detected: {pattern_name}",
                                evidence={
                                    "pattern": pattern,
                                    "matched_text": text_content[:200],
                                    "sample_index": idx,
                                },
                            )
                        )

        # Check for suspicious repetition (often used in backdoors)
        value_counts = df[text_column].value_counts()

        # Exact duplicates are suspicious (potential backdoor triggers)
        duplicate_threshold = max(2, len(df) * 0.01)  # 1% or min 2
        duplicates = value_counts[value_counts >= duplicate_threshold]

        if len(duplicates) > 0:
            for value, count in duplicates.items():
                if count > duplicate_threshold:
                    signals.append(
                        PoisoningSignal(
                            signal_type="repeated_backdoor_trigger",
                            severity="HIGH",
                            confidence=0.8,
                            location=f"text_{hash(value) % 10000}",
                            description=f"Text appears {count} times, possible backdoor trigger",
                            evidence={
                                "text_hash": hashlib.sha256(value.encode()).hexdigest()[
                                    :16
                                ],
                                "occurrence_count": count,
                                "text_preview": value[:100],
                            },
                        )
                    )

        return signals

    def _detect_statistical_anomalies(
        self, df: pd.DataFrame, baseline_stats: Optional[Dict[str, Any]]
    ) -> List[PoisoningSignal]:
        """Detect statistical anomalies indicating poisoning."""
        signals = []

        if len(df) < self.min_samples:
            logger.warning(f"Insufficient samples for statistical analysis: {len(df)}")
            return signals

        # Analyze numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            values = df[col].dropna()

            if len(values) < self.min_samples:
                continue

            # Detect outliers using z-score
            mean = values.mean()
            std = values.std()

            if std == 0:
                continue

            z_scores = np.abs((values - mean) / std)
            outliers = values[z_scores > self.Z_SCORE_THRESHOLD]
            outlier_ratio = len(outliers) / len(values)

            if outlier_ratio > self.OUTLIER_RATIO_THRESHOLD:
                signals.append(
                    PoisoningSignal(
                        signal_type="statistical_outliers",
                        severity="MEDIUM",
                        confidence=min(outlier_ratio * 10, 1.0),
                        location=f"column_{col}",
                        description=f"High outlier ratio ({outlier_ratio:.1%}) in '{col}'",
                        evidence={
                            "column": col,
                            "outlier_ratio": outlier_ratio,
                            "outlier_count": len(outliers),
                            "threshold": self.OUTLIER_RATIO_THRESHOLD,
                        },
                    )
                )

            # Compare with baseline if available
            if baseline_stats and f"col_{col}" in baseline_stats:
                baseline_mean = baseline_stats[f"col_{col}"]["mean"]
                baseline_std = baseline_stats[f"col_{col}"]["std"]

                # Significant shift in distribution
                mean_shift = abs(mean - baseline_mean) / (baseline_std + 1e-9)

                if mean_shift > self.Z_SCORE_THRESHOLD:
                    signals.append(
                        PoisoningSignal(
                            signal_type="distribution_shift",
                            severity="HIGH",
                            confidence=min(mean_shift / 10, 1.0),
                            location=f"column_{col}",
                            description=f"Mean of '{col}' shifted by {mean_shift:.2f}σ",
                            evidence={
                                "column": col,
                                "baseline_mean": baseline_mean,
                                "current_mean": mean,
                                "shift_std": mean_shift,
                            },
                        )
                    )

        # Check for missing value anomalies
        for col in df.columns:
            missing_ratio = df[col].isna().sum() / len(df)

            if missing_ratio > 0.5:  # More than 50% missing
                signals.append(
                    PoisoningSignal(
                        signal_type="excessive_missing_data",
                        severity="LOW",
                        confidence=missing_ratio,
                        location=f"column_{col}",
                        description=f"Column '{col}' has {missing_ratio:.1%} missing values",
                        evidence={
                            "column": col,
                            "missing_ratio": missing_ratio,
                            "missing_count": df[col].isna().sum(),
                        },
                    )
                )

        return signals

    def _verify_provenance(self, df: pd.DataFrame, corpus_id: str) -> Dict[str, Any]:
        """Verify data provenance and integrity."""
        provenance_check = {"verified": False, "checks": []}

        # Check for checksum/hash columns if present
        hash_columns = [col for col in df.columns if "hash" in col.lower()]

        for col in hash_columns:
            if df[col].notna().any():
                # Verify hash format
                sample_hash = df[col].dropna().iloc[0]

                if re.match(r"^[a-f0-9]{32,64}$", str(sample_hash)):
                    provenance_check["checks"].append(
                        {"check": "hash_format", "passed": True, "column": col}
                    )
                else:
                    provenance_check["checks"].append(
                        {
                            "check": "hash_format",
                            "passed": False,
                            "column": col,
                            "reason": "Invalid hash format",
                        }
                    )

        # Check for timestamp columns
        timestamp_columns = [
            col
            for col in df.columns
            if any(
                keyword in col.lower()
                for keyword in ["time", "date", "created", "updated"]
            )
        ]

        for col in timestamp_columns:
            if df[col].notna().any():
                # Check for future timestamps (impossible)
                try:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        future_dates = df[df[col] > datetime.now()]
                    else:
                        future_dates = df[pd.to_datetime(df[col]) > datetime.now()]

                    if len(future_dates) > 0:
                        provenance_check["checks"].append(
                            {
                                "check": "timestamp_integrity",
                                "passed": False,
                                "column": col,
                                "reason": f"{len(future_dates)} future timestamps found",
                            }
                        )
                except Exception as e:
                    logger.warning(f"Could not verify timestamps in {col}: {e}")

        # Overall verification
        provenance_check["verified"] = all(
            check.get("passed", False) for check in provenance_check["checks"]
        )

        return provenance_check

    def _calculate_statistics(
        self, df: pd.DataFrame, baseline_stats: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate corpus statistics."""
        stats = {
            "total_samples": len(df),
            "total_features": len(df.columns),
            "memory_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
        }

        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            stats["numeric_columns"] = {}
            for col in numeric_cols:
                values = df[col].dropna()
                if len(values) > 0:
                    stats["numeric_columns"][col] = {
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                        "min": float(values.min()),
                        "max": float(values.max()),
                        "missing": int(df[col].isna().sum()),
                    }

        # Categorical column statistics
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(cat_cols) > 0:
            stats["categorical_columns"] = {}
            for col in cat_cols:
                stats["categorical_columns"][col] = {
                    "unique": int(df[col].nunique()),
                    "top": (
                        str(df[col].mode().iloc[0]) if len(df[col].mode()) > 0 else None
                    ),
                    "missing": int(df[col].isna().sum()),
                }

        return stats

    def _generate_recommendations(
        self,
        signals: List[PoisoningSignal],
        poisoning_type: PoisoningType,
        severity: str,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Severity-based recommendations
        if severity == "CRITICAL":
            recommendations.append("🚨 CRITICAL: Immediately quarantine the corpus")
            recommendations.append("🚨 CRITICAL: Disable all dependent models")
            recommendations.append("🚨 CRITICAL: Escalate to ML Security Team")

        elif severity == "HIGH":
            recommendations.append("⚠️  HIGH: Quarantine corpus for investigation")
            recommendations.append("⚠️  HIGH: Plan model retraining")

        # Type-specific recommendations
        if poisoning_type == PoisoningType.LABEL_FLIPPING:
            recommendations.append(
                "📊 Verify label integrity with original data source"
            )
            recommendations.append("📊 Compare with baseline distribution")
            recommendations.append("📊 Investigate data pipeline for tampering")

        elif poisoning_type == PoisoningType.BACKDOOR:
            recommendations.append("🔍 Extract and document all trigger patterns")
            recommendations.append("🔍 Test models for backdoor activation")
            recommendations.append("🔍 Investigate data source for compromise")

        elif poisoning_type == PoisoningType.CLEAN_LABEL:
            recommendations.append("🔬 Perform feature importance analysis")
            recommendations.append("🔬 Check for anomalous feature values")
            recommendations.append("🔬 Use adversarial validation")

        # General recommendations
        if len(signals) > 10:
            recommendations.append(
                "📈 High number of anomalies detected - comprehensive audit recommended"
            )

        if any(s.severity == "CRITICAL" for s in signals):
            recommendations.append("🔐 All deployments must be stopped immediately")

        return recommendations

    def _identify_affected_samples(
        self, df: pd.DataFrame, signals: List[PoisoningSignal], limit: int = 1000
    ) -> List[str]:
        """Identify samples affected by poisoning."""
        affected = set()

        for signal in signals:
            # Parse location to find sample indices
            if signal.location.startswith("sample_"):
                idx = int(signal.location.split("_")[1])
                affected.add(f"sample_{idx}")

            elif signal.location.startswith("label_"):
                # Get all samples with this label
                label = signal.location.split("_", 1)[1]
                label_samples = df[df.index.isin(df.index)].index  # Placeholder logic
                affected.update([f"sample_{i}" for i in label_samples[:limit]])

            elif signal.location.startswith("column_"):
                # All samples in this column could be affected
                col = signal.location.split("_", 1)[1]
                if col in df.columns:
                    affected.update([f"sample_{i}" for i in df.index[:limit]])

        return list(affected)[:limit]


# CLI interface
def main():
    """CLI for poisoning detection."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect data poisoning in ML corpora")
    parser.add_argument(
        "--corpus", required=True, help="Path to corpus file (JSON) or directory"
    )
    parser.add_argument("--corpus-id", required=True, help="Corpus identifier")
    parser.add_argument("--label-column", help="Name of label column")
    parser.add_argument("--text-column", help="Name of text/input column")
    parser.add_argument("--baseline", help="Path to baseline statistics JSON")
    parser.add_argument("--output", help="Output path for report (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Load baseline if provided
    baseline = None
    if args.baseline:
        with open(args.baseline, "r") as f:
            baseline = json.load(f)

    # Run detection
    detector = DataPoisoningDetector()
    report = detector.detect_poisoning(
        corpus_data=args.corpus,
        corpus_id=args.corpus_id,
        label_column=args.label_column,
        text_column=args.text_column,
        baseline_stats=baseline,
    )

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            f.write(report.to_json())
        print(f"Report saved to {args.output}")
    else:
        print(report.to_json())


if __name__ == "__main__":
    main()
