#!/usr/bin/env python3
"""
User Behavioral Analysis Engine for Threat Detection

Analyzes user behavior patterns to detect anomalies that may indicate:
- Account compromise
- Bot/automation activity
- Fraudulent behavior
- Insider threats
- Coordinated attacks

Uses unsupervised learning and statistical analysis to establish baseline
behavior profiles and detect deviations.

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Optional ML dependencies
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """Types of behaviors to analyze"""

    REQUEST_RATE = "request_rate"
    REQUEST_PATTERN = "request_pattern"
    RESPONSE_INTERACTION = "response_interaction"
    TIME_OF_DAY = "time_of_day"
    GEOLOCATION = "geolocation"
    DEVICE_FINGERPRINT = "device_fingerprint"
    SESSION_DURATION = "session_duration"
    ERROR_RATE = "error_rate"


class AnomalySeverity(Enum):
    """Severity levels for behavioral anomalies"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatCategory(Enum):
    """Categories of threats detected"""

    ACCOUNT_TAKEOVER = "account_takeover"
    BOT_AUTOMATION = "bot_automation"
    BRUTE_FORCE = "brute_force"
    CREDIT_CARD_FRAUD = "credit_card_fraud"
    DATA_EXFILTRATION = "data_exfiltration"
    DENIAL_OF_SERVICE = "denial_of_service"
    INSIDER_THREAT = "insider_threat"
    MAN_IN_MIDDLE = "man_in_middle"
    REPLAY_ATTACK = "replay_attack"
    UNKNOWN = "unknown"


@dataclass
class BehaviorFeature:
    """Single behavior feature"""

    name: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    is_anomalous: bool
    severity: AnomalySeverity


@dataclass
class BehaviorProfile:
    """User's behavioral profile"""

    user_id: str
    features: Dict[str, BehaviorFeature]
    baseline_established: bool
    sample_size: int
    last_updated: datetime
    risk_score: float  # 0.0 to 1.0
    threat_indicators: List[str]


@dataclass
class AnomalyAlert:
    """Alert generated for anomalous behavior"""

    alert_id: str
    user_id: str
    threat_category: ThreatCategory
    severity: AnomalySeverity
    confidence: float
    anomalous_features: List[str]
    description: str
    recommended_actions: List[str]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "user_id": self.user_id,
            "threat_category": self.threat_category.value,
            "severity": self.severity.value,
            "confidence": self.confidence,
            "anomalous_features": self.anomalous_features,
            "description": self.description,
            "recommended_actions": self.recommended_actions,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class BehavioralAnalyzer:
    """
    User behavioral analysis engine.

    Establishes baseline behavior profiles for users and detects anomalies
    that may indicate security threats.
    """

    # Minimum samples required to establish baseline
    MIN_BASELINE_SAMPLES = 30

    # Z-score thresholds for anomaly detection
    Z_SCORE_THRESHOLD_MEDIUM = 2.5
    Z_SCORE_THRESHOLD_HIGH = 3.5
    Z_SCORE_THRESHOLD_CRITICAL = 4.5

    # Risk score weights
    RISK_WEIGHTS = {
        BehaviorType.REQUEST_RATE: 0.25,
        BehaviorType.REQUEST_PATTERN: 0.15,
        BehaviorType.TIME_OF_DAY: 0.10,
        BehaviorType.ERROR_RATE: 0.20,
        BehaviorType.SESSION_DURATION: 0.15,
        BehaviorType.DEVICE_FINGERPRINT: 0.15,
    }

    def __init__(
        self,
        baseline_window_days: int = 30,
        anomaly_threshold: float = 2.5,
        enable_real_time_detection: bool = True,
    ):
        """
        Initialize behavioral analyzer.

        Args:
            baseline_window_days: Days of data needed to establish baseline
            anomaly_threshold: Z-score threshold for anomaly detection
            enable_real_time_detection: Enable real-time anomaly detection
        """
        self.baseline_window_days = baseline_window_days
        self.anomaly_threshold = anomaly_threshold
        self.enable_real_time_detection = enable_real_time_detection

        # User behavior profiles
        self.user_profiles: Dict[str, BehaviorProfile] = {}

        # Historical feature data for each user
        self.feature_history: Dict[str, Dict[str, List[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Session tracking
        self.active_sessions: Dict[str, Dict] = {}

        logger.info("BehavioralAnalyzer initialized")

    def analyze_user_behavior(
        self,
        user_id: str,
        request_data: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> Optional[AnomalyAlert]:
        """
        Analyze user behavior for anomalies.

        Args:
            user_id: User identifier
            request_data: Request metadata and features
            session_id: Session identifier

        Returns:
            AnomalyAlert if threat detected, None otherwise
        """
        # Extract features from request
        features = self._extract_features(request_data)

        # Update feature history
        self._update_feature_history(user_id, features)

        # Get or create user profile
        profile = self._get_user_profile(user_id)

        # Check if baseline is established
        if not profile.baseline_established:
            logger.info(f"Baseline not yet established for user {user_id}")
            self._update_baseline(user_id)
            return None

        # Calculate z-scores for each feature
        anomalous_features = []
        total_z_score = 0.0

        for feature_name, feature_value in features.items():
            if feature_name not in profile.features:
                continue

            baseline_feature = profile.features[feature_name]

            if NUMPY_AVAILABLE:
                z_score = abs(
                    (feature_value - baseline_feature.baseline_mean)
                    / max(baseline_feature.baseline_std, 1e-6)
                )
            else:
                z_score = 0.0

            # Update feature with current z-score
            baseline_feature.value = feature_value
            baseline_feature.z_score = z_score

            # Check if anomalous
            is_anomalous, severity = self._is_anomalous(z_score)
            baseline_feature.is_anomalous = is_anomalous
            baseline_feature.severity = severity

            if is_anomalous:
                anomalous_features.append(feature_name)
                total_z_score += z_score

        # Update profile
        profile.last_updated = datetime.now(timezone.utc)

        # Determine if alert should be generated
        if len(anomalous_features) > 0:
            return self._generate_alert(user_id, anomalous_features, features, profile)

        return None

    def _extract_features(self, request_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract behavioral features from request data"""
        features = {}

        # Feature 1: Request rate (requests per minute)
        features["requests_per_minute"] = request_data.get("requests_per_minute", 0.0)

        # Feature 2: Request size (bytes)
        features["request_size"] = float(request_data.get("request_size", 0))

        # Feature 3: Response size (bytes)
        features["response_size"] = float(request_data.get("response_size", 0))

        # Feature 4: Error rate (0.0 to 1.0)
        features["error_rate"] = float(request_data.get("error_rate", 0.0))

        # Feature 5: Time of day (hour as float 0-24)
        now = datetime.now(timezone.utc)
        features["time_of_day"] = now.hour + now.minute / 60.0

        # Feature 6: Day of week (0=Monday, 6=Sunday)
        features["day_of_week"] = float(now.weekday())

        # Feature 7: Session duration (minutes)
        features["session_duration"] = float(request_data.get("session_duration", 0.0))

        # Feature 8: Failed login attempts
        features["failed_logins"] = float(request_data.get("failed_logins", 0))

        # Feature 9: Unique endpoints accessed
        features["unique_endpoints"] = float(request_data.get("unique_endpoints", 0))

        # Feature 10: Response time (milliseconds)
        features["response_time"] = float(request_data.get("response_time", 0.0))

        return features

    def _update_feature_history(self, user_id: str, features: Dict[str, float]):
        """Update historical feature data for user"""
        for feature_name, feature_value in features.items():
            self.feature_history[user_id][feature_name].append(feature_value)

            # Keep only recent history (baseline window)
            max_samples = self.MIN_BASELINE_SAMPLES * 2
            if len(self.feature_history[user_id][feature_name]) > max_samples:
                self.feature_history[user_id][feature_name] = self.feature_history[
                    user_id
                ][feature_name][-max_samples:]

    def _get_user_profile(self, user_id: str) -> BehaviorProfile:
        """Get or create user behavior profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = BehaviorProfile(
                user_id=user_id,
                features={},
                baseline_established=False,
                sample_size=0,
                last_updated=datetime.now(timezone.utc),
                risk_score=0.0,
                threat_indicators=[],
            )
        return self.user_profiles[user_id]

    def _update_baseline(self, user_id: str):
        """Update baseline for user's behavioral profile"""
        if user_id not in self.feature_history:
            return

        profile = self._get_user_profile(user_id)

        # Check if we have enough samples
        feature_names = list(self.feature_history[user_id].keys())
        if not feature_names:
            return

        # Calculate baseline statistics for each feature
        for feature_name in feature_names:
            history = self.feature_history[user_id][feature_name]

            if len(history) >= self.MIN_BASELINE_SAMPLES:
                if NUMPY_AVAILABLE:
                    mean = float(np.mean(history))
                    std = float(np.std(history))
                else:
                    mean = statistics.mean(history)
                    std = statistics.stdev(history) if len(history) > 1 else 0.0

                profile.features[feature_name] = BehaviorFeature(
                    name=feature_name,
                    value=0.0,
                    baseline_mean=mean,
                    baseline_std=std,
                    z_score=0.0,
                    is_anomalous=False,
                    severity=AnomalySeverity.LOW,
                )

        # Update profile status
        profile.sample_size = (
            len(list(self.feature_history[user_id].values())[0]) if feature_names else 0
        )
        profile.baseline_established = profile.sample_size >= self.MIN_BASELINE_SAMPLES

        if profile.baseline_established:
            logger.info(
                f"Baseline established for user {user_id} with {profile.sample_size} samples"
            )

    def _is_anomalous(self, z_score: float) -> Tuple[bool, AnomalySeverity]:
        """Determine if z-score indicates anomaly"""
        if z_score >= self.Z_SCORE_THRESHOLD_CRITICAL:
            return True, AnomalySeverity.CRITICAL
        elif z_score >= self.Z_SCORE_THRESHOLD_HIGH:
            return True, AnomalySeverity.HIGH
        elif z_score >= self.Z_SCORE_THRESHOLD_MEDIUM:
            return True, AnomalySeverity.MEDIUM
        else:
            return False, AnomalySeverity.LOW

    def _generate_alert(
        self,
        user_id: str,
        anomalous_features: List[str],
        current_features: Dict[str, float],
        profile: BehaviorProfile,
    ) -> AnomalyAlert:
        """Generate security alert for anomalous behavior"""
        # Determine threat category
        threat_category = self._classify_threat(anomalous_features, current_features)

        # Calculate severity
        severities = [
            profile.features[f].severity
            for f in anomalous_features
            if f in profile.features
        ]
        # Sort by severity value (CRITICAL > HIGH > MEDIUM > LOW)
        severity_order = {
            AnomalySeverity.CRITICAL: 4,
            AnomalySeverity.HIGH: 3,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 1,
        }
        overall_severity = (
            max(severities, key=lambda s: severity_order.get(s, 0))
            if severities
            else AnomalySeverity.MEDIUM
        )

        # Calculate confidence based on number and severity of anomalies
        critical_count = sum(1 for s in severities if s == AnomalySeverity.CRITICAL)
        high_count = sum(1 for s in severities if s == AnomalySeverity.HIGH)

        confidence = min(0.5 + (critical_count * 0.2) + (high_count * 0.1), 1.0)

        # Generate description
        description = self._generate_description(
            threat_category, anomalous_features, current_features
        )

        # Generate recommended actions
        recommended_actions = self._generate_recommendations(
            threat_category, overall_severity
        )

        # Create alert
        alert = AnomalyAlert(
            alert_id=f"BEH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{user_id[:8]}",
            user_id=user_id,
            threat_category=threat_category,
            severity=overall_severity,
            confidence=confidence,
            anomalous_features=anomalous_features,
            description=description,
            recommended_actions=recommended_actions,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "current_features": current_features,
                "profile_risk_score": profile.risk_score,
            },
        )

        # Log alert
        self._log_alert(alert)

        return alert

    def _classify_threat(
        self, anomalous_features: List[str], current_features: Dict[str, float]
    ) -> ThreatCategory:
        """Classify the type of threat based on anomalous features"""
        # High request rate + failed logins = Brute force
        if (
            "requests_per_minute" in anomalous_features
            and "failed_logins" in anomalous_features
        ):
            if current_features.get("failed_logins", 0) > 5:
                return ThreatCategory.BRUTE_FORCE

        # High request rate + short session duration = Bot
        if "requests_per_minute" in anomalous_features:
            if current_features.get("requests_per_minute", 0) > 60:
                return ThreatCategory.BOT_AUTOMATION

        # Anomalous time of day + device fingerprint = Account takeover
        if "time_of_day" in anomalous_features:
            return ThreatCategory.ACCOUNT_TAKEOVER

        # High error rate + many endpoints = Data exfiltration
        if (
            "error_rate" in anomalous_features
            and "unique_endpoints" in anomalous_features
        ):
            return ThreatCategory.DATA_EXFILTRATION

        # Very high request rate = DoS
        if current_features.get("requests_per_minute", 0) > 100:
            return ThreatCategory.DENIAL_OF_SERVICE

        # Default to unknown
        return ThreatCategory.UNKNOWN

    def _generate_description(
        self,
        threat_category: ThreatCategory,
        anomalous_features: List[str],
        current_features: Dict[str, float],
    ) -> str:
        """Generate human-readable description of the anomaly"""
        descriptions = {
            ThreatCategory.BRUTE_FORCE: "Multiple failed login attempts detected",
            ThreatCategory.BOT_AUTOMATION: "Automated/bot-like activity detected",
            ThreatCategory.ACCOUNT_TAKEOVER: "Unusual access patterns suggesting account takeover",
            ThreatCategory.DATA_EXFILTRATION: "Pattern suggesting data exfiltration activity",
            ThreatCategory.DENIAL_OF_SERVICE: "High-volume requests indicating potential DoS",
        }

        base_desc = descriptions.get(threat_category, "Anomalous behavior detected")

        # Add specific details
        details = []
        if "requests_per_minute" in anomalous_features:
            rate = current_features.get("requests_per_minute", 0)
            details.append(f"Request rate: {rate:.1f}/min")
        if "error_rate" in anomalous_features:
            error_rate = current_features.get("error_rate", 0) * 100
            details.append(f"Error rate: {error_rate:.1f}%")
        if "time_of_day" in anomalous_features:
            hour = int(current_features.get("time_of_day", 0))
            details.append(f"Unusual time: {hour}:00")

        if details:
            return f"{base_desc} ({', '.join(details)})"

        return base_desc

    def _generate_recommendations(
        self, threat_category: ThreatCategory, severity: AnomalySeverity
    ) -> List[str]:
        """Generate recommended actions for the alert"""
        recommendations = []

        # Base recommendations by severity
        if severity == AnomalySeverity.CRITICAL:
            recommendations.extend(
                [
                    "IMMEDIATE: Block user access temporarily",
                    "Contact security team immediately",
                    "Review recent activity logs",
                ]
            )
        elif severity == AnomalySeverity.HIGH:
            recommendations.extend(
                [
                    "Require additional authentication",
                    "Monitor user closely",
                    "Review session history",
                ]
            )
        elif severity == AnomalySeverity.MEDIUM:
            recommendations.extend(
                ["Monitor user behavior", "Consider step-up authentication"]
            )

        # Threat-specific recommendations
        if threat_category == ThreatCategory.BRUTE_FORCE:
            recommendations.extend(
                [
                    "Implement account lockout after N failures",
                    "Add CAPTCHA verification",
                ]
            )
        elif threat_category == ThreatCategory.BOT_AUTOMATION:
            recommendations.extend(
                ["Implement rate limiting", "Add CAPTCHA or challenge-response"]
            )
        elif threat_category == ThreatCategory.ACCOUNT_TAKEOVER:
            recommendations.extend(
                [
                    "Force password reset",
                    "Revoke all active sessions",
                    "Notify user of suspicious activity",
                ]
            )
        elif threat_category == ThreatCategory.DATA_EXFILTRATION:
            recommendations.extend(
                [
                    "Audit data access logs",
                    "Review data egress patterns",
                    "Consider blocking data export",
                ]
            )

        return recommendations

    def _log_alert(self, alert: AnomalyAlert):
        """Log alert for monitoring"""
        log_data = {
            "alert_id": alert.alert_id,
            "user_id": alert.user_id,
            "threat_category": alert.threat_category.value,
            "severity": alert.severity.value,
            "confidence": alert.confidence,
            "anomalous_features": alert.anomalous_features,
        }

        if alert.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
            logger.critical(f"Behavioral anomaly alert: {log_data}")
        else:
            logger.warning(f"Behavioral anomaly alert: {log_data}")

    def get_user_profile(self, user_id: str) -> Optional[BehaviorProfile]:
        """Get user's behavioral profile"""
        return self.user_profiles.get(user_id)

    def establish_baseline_for_user(self, user_id: str) -> bool:
        """Manually trigger baseline establishment for user"""
        try:
            self._update_baseline(user_id)
            profile = self.user_profiles.get(user_id)
            return profile.baseline_established if profile else False
        except Exception as e:
            logger.error(f"Error establishing baseline for user {user_id}: {e}")
            return False

    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        total_users = len(self.user_profiles)
        users_with_baselines = sum(
            1 for p in self.user_profiles.values() if p.baseline_established
        )

        return {
            "total_users_tracked": total_users,
            "users_with_baselines": users_with_baselines,
            "baseline_window_days": self.baseline_window_days,
            "min_baseline_samples": self.MIN_BASELINE_SAMPLES,
            "active_sessions": len(self.active_sessions),
        }


# Global analyzer instance
behavioral_analyzer = BehavioralAnalyzer()


def analyze_behavior(
    user_id: str, request_data: Dict[str, Any], session_id: Optional[str] = None
) -> Optional[AnomalyAlert]:
    """
    Convenience function to analyze user behavior.

    Usage:
        from ai.security.behavioral_analyzer import analyze_behavior

        request_data = {
            'requests_per_minute': 120,
            'request_size': 1024,
            'error_rate': 0.15,
            'failed_logins': 8
        }

        alert = analyze_behavior(user_id="user_123", request_data=request_data)

        if alert:
            print(f"Threat detected: {alert.threat_category}")
            print(f"Severity: {alert.severity}")
    """
    return behavioral_analyzer.analyze_user_behavior(
        user_id=user_id, request_data=request_data, session_id=session_id
    )


def get_user_risk_score(user_id: str) -> float:
    """Get current risk score for user"""
    profile = behavioral_analyzer.get_user_profile(user_id)
    return profile.risk_score if profile else 0.0


# CLI interface
def main():
    """CLI interface for behavioral analyzer"""
    import argparse

    parser = argparse.ArgumentParser(description="User Behavioral Analysis Engine")
    parser.add_argument("--user-id", required=True, help="User ID to analyze")
    parser.add_argument("--request-rate", type=float, help="Requests per minute")
    parser.add_argument("--error-rate", type=float, help="Error rate (0.0 to 1.0)")
    parser.add_argument(
        "--failed-logins", type=float, help="Number of failed login attempts"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Build request data
    request_data = {}
    if args.request_rate:
        request_data["requests_per_minute"] = args.request_rate
    if args.error_rate:
        request_data["error_rate"] = args.error_rate
    if args.failed_logins:
        request_data["failed_logins"] = args.failed_logins

    # Analyze behavior
    alert = analyze_behavior(user_id=args.user_id, request_data=request_data)

    # Output results
    if args.json:
        if alert:
            print(json.dumps(alert.to_dict(), indent=2))
        else:
            print(json.dumps({"status": "no_anomaly_detected"}, indent=2))
    else:
        print("\n" + "=" * 80)
        print("BEHAVIORAL ANALYSIS RESULTS")
        print("=" * 80)
        if alert:
            print(f"⚠️  ANOMALY DETECTED")
            print(f"Threat Category: {alert.threat_category.value}")
            print(f"Severity: {alert.severity.value.upper()}")
            print(f"Confidence: {alert.confidence:.2%}")
            print(f"\nDescription: {alert.description}")
            print(f"\nRecommended Actions:")
            for action in alert.recommended_actions:
                print(f"  • {action}")
        else:
            print("✓ No anomalies detected")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
