"""
Anomaly Detection Service
Service wrapper for AdvancedAnomalyDetector to provide high-level API
"""

from typing import Any, Dict, List
from datetime import datetime

from app.services.anomaly_detection import AdvancedAnomalyDetector, AnomalyConfig


class AnomalyDetectionService:
    """
    High-level service for anomaly detection in behavioral data.
    Wraps AdvancedAnomalyDetector with simplified API.
    """

    def __init__(self):
        """Initialize the anomaly detection service."""
        self.config = AnomalyConfig()
        self.detector = None  # Will be initialized when DB session is available

    async def detect_anomalies(
        self,
        data: List[float],
        entity_id: str,
        metric_name: str,
        threshold_std_dev: float = 2.5,
    ) -> Dict[str, Any]:
        """
        Detect anomalies in behavioral data.

        Args:
            data: List of metric values
            entity_id: ID of the entity being analyzed
            metric_name: Name of the metric
            threshold_std_dev: Standard deviation threshold

        Returns:
            Dict with anomaly detection results
        """
        # For now, return a simple implementation
        # In production, this would use AdvancedAnomalyDetector
        import numpy as np

        if len(data) < 3:
            return {
                "has_anomaly": False,
                "anomaly_score": 0.0,
                "anomaly_description": "Insufficient data for anomaly detection",
                "baseline_value": np.mean(data) if data else 0,
                "current_value": data[-1] if data else 0,
                "deviation_percentage": 0.0,
                "confidence": 0.0,
                "recommended_actions": [],
            }

        mean = np.mean(data)
        std = np.std(data)
        latest = data[-1]

        z_score = abs((latest - mean) / std) if std > 0 else 0
        has_anomaly = z_score > threshold_std_dev

        deviation_pct = abs((latest - mean) / mean * 100) if mean != 0 else 0

        return {
            "has_anomaly": has_anomaly,
            "anomaly_score": float(z_score),
            "anomaly_description": f"{'Anomaly detected' if has_anomaly else 'Normal behavior'} in {metric_name}",
            "baseline_value": float(mean),
            "current_value": float(latest),
            "deviation_percentage": float(deviation_pct),
            "confidence": float(min(z_score / threshold_std_dev, 1.0)),
            "recommended_actions": (
                [
                    f"Investigate {metric_name} for entity {entity_id}",
                    "Review recent changes in behavior patterns",
                    "Consider conducting root cause analysis",
                ]
                if has_anomaly
                else []
            ),
        }

    async def consolidate_anomalies(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Consolidate multiple anomaly detections."""
        return {
            "total_anomalies": len(anomalies),
            "high_severity": sum(1 for a in anomalies if a.get("anomaly_score", 0) > 3),
            "medium_severity": sum(
                1 for a in anomalies if 2 < a.get("anomaly_score", 0) <= 3
            ),
            "low_severity": sum(1 for a in anomalies if a.get("anomaly_score", 0) <= 2),
            "consolidated_anomalies": anomalies,
        }

    async def calculate_severity_distribution(
        self, anomalies: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Calculate severity distribution of anomalies."""
        return {
            "critical": sum(1 for a in anomalies if a.get("anomaly_score", 0) > 4),
            "high": sum(1 for a in anomalies if 3 < a.get("anomaly_score", 0) <= 4),
            "medium": sum(1 for a in anomalies if 2 < a.get("anomaly_score", 0) <= 3),
            "low": sum(1 for a in anomalies if a.get("anomaly_score", 0) <= 2),
        }

    async def generate_action_recommendations(
        self, anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate action recommendations based on anomalies."""
        if not anomalies:
            return []

        recommendations = []
        high_severity_count = sum(1 for a in anomalies if a.get("anomaly_score", 0) > 3)

        if high_severity_count > 0:
            recommendations.append(
                f"Urgent: Investigate {high_severity_count} high-severity anomalies"
            )
            recommendations.append(
                "Schedule immediate review with affected individuals"
            )
            recommendations.append("Consider temporary monitoring increases")

        total_anomalies = len(anomalies)
        if total_anomalies > 5:
            recommendations.append(
                "Pattern detected: Multiple anomalies may indicate systemic issue"
            )
            recommendations.append(
                "Review organizational processes and environmental factors"
            )

        return recommendations
