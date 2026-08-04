# app/services/ab_testing_service.py
# A/B testing framework for onboarding optimization
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class OnboardingVariant(str, Enum):
    CONTROL = "control"  # Original onboarding flow
    VALUE_FIRST = "value_first"  # New value-first approach
    HYBRID = "hybrid"  # Mix of both approaches
    PERSONALIZED = "personalized"  # AI-powered personalization


class ABTestService:
    """
    A/B testing service specifically for onboarding optimization.
    Supports user segmentation, variant assignment, and conversion tracking.
    """

    def __init__(self):
        self.active_tests = self._load_active_tests()
        self.user_assignments = {}  # In production, this would be in Redis/Database

    def _load_active_tests(self) -> dict[str, dict[str, Any]]:
        """Load active A/B test configurations."""
        return {
            "onboarding_flow_v2": {
                "name": "Value-First vs Traditional Onboarding",
                "description": "Test if showing value first improves conversion rates",
                "variants": [
                    {
                        "id": OnboardingVariant.CONTROL,
                        "name": "Traditional Onboarding",
                        "weight": 25,  # 25% of users
                        "features": [
                            "email_verification_required",
                            "full_registration_first",
                            "complex_form",
                        ],
                    },
                    {
                        "id": OnboardingVariant.VALUE_FIRST,
                        "name": "Value-First Approach",
                        "weight": 50,  # 50% of users (primary focus)
                        "features": [
                            "instant_insights",
                            "optional_email_verification",
                            "quick_assessment",
                        ],
                    },
                    {
                        "id": OnboardingVariant.HYBRID,
                        "name": "Hybrid Approach",
                        "weight": 20,  # 20% of users
                        "features": [
                            "quick_preview",
                            "progressive_registration",
                            "social_login",
                        ],
                    },
                    {
                        "id": OnboardingVariant.PERSONALIZED,
                        "name": "AI-Personalized",
                        "weight": 5,  # 5% of users (experimental)
                        "features": [
                            "adaptive_flow",
                            "personalized_insights",
                            "smart_recommendations",
                        ],
                    },
                ],
                "target_metrics": [
                    "conversion_rate",
                    "time_to_value",
                    "drop_off_rate",
                    "engagement_score",
                ],
                "segments": {
                    "industry": ["tech", "healthcare", "finance", "retail", "other"],
                    "team_size": ["small", "medium", "large", "enterprise"],
                    "role": ["manager", "hr", "lead", "member", "executive"],
                },
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=90),
                "sample_size": 10000,
                "statistical_significance": 0.95,
            },
            "quick_assessment_length": {
                "name": "Quick Assessment Length Optimization",
                "description": "Test optimal number of questions for quick assessment",
                "variants": [
                    {
                        "id": "two_questions",
                        "name": "2 Questions",
                        "weight": 40,
                        "features": ["minimal_assessment", "fast_completion"],
                    },
                    {
                        "id": "three_questions",
                        "name": "3 Questions",
                        "weight": 35,
                        "features": ["balanced_assessment", "moderate_insights"],
                    },
                    {
                        "id": "five_questions",
                        "name": "5 Questions",
                        "weight": 25,
                        "features": ["detailed_assessment", "richer_insights"],
                    },
                ],
                "target_metrics": [
                    "completion_rate",
                    "insight_quality",
                    "conversion_rate",
                ],
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=30),
            },
        }

    def assign_variant(
        self,
        user_id: str | None = None,
        session_id: str | None = None,
        segments: dict[str, str] | None = None,
        test_name: str = "onboarding_flow_v2",
    ) -> dict[str, Any]:
        """
        Assign user to a test variant based on configuration and user segments.
        Returns assignment details and variant features.
        """

        if test_name not in self.active_tests:
            return self._get_default_assignment(test_name)

        test = self.active_tests[test_name]

        # Create consistent user identifier
        user_identifier = user_id or session_id or str(uuid.uuid4())

        # Check for existing assignment (ensure consistent assignment)
        assignment_key = f"{test_name}:{user_identifier}"
        if assignment_key in self.user_assignments:
            return self.user_assignments[assignment_key]

        # Determine variant assignment
        variant = self._select_variant(test, user_identifier, segments)

        # Create assignment record
        assignment = {
            "test_name": test_name,
            "user_identifier": user_identifier,
            "user_id": user_id,
            "session_id": session_id,
            "variant": variant["id"],
            "variant_name": variant["name"],
            "features": variant["features"],
            "segments": segments or {},
            "assigned_at": datetime.utcnow(),
            "assignment_method": "weighted_random",
        }

        # Store assignment
        self.user_assignments[assignment_key] = assignment

        return assignment

    def _select_variant(
        self,
        test: dict[str, Any],
        user_identifier: str,
        segments: dict[str, str] | None,
    ) -> dict[str, Any]:
        """Select variant based on test configuration and user segments."""

        # Use deterministic hash for consistent assignment
        hash_input = f"{test['name']}:{user_identifier}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        random_value = (hash_value % 100) + 1

        # Check for segment-specific rules
        if segments:
            variant = self._apply_segment_rules(test, segments, random_value)
            if variant:
                return variant

        # Weighted random selection
        cumulative_weight = 0
        for variant in test["variants"]:
            cumulative_weight += variant["weight"]
            if random_value <= cumulative_weight:
                return variant

        # Fallback to first variant
        return test["variants"][0]

    def _apply_segment_rules(
        self, test: dict[str, Any], segments: dict[str, str], random_value: int
    ) -> dict[str, Any] | None:
        """Apply segment-specific assignment rules."""

        # Example rule: Executives get personalized variant
        if segments.get("role") == "executive" and random_value > 80:
            personalized_variants = [
                v for v in test["variants"] if "personalized" in v["id"].lower()
            ]
            if personalized_variants:
                return personalized_variants[0]

        # Example rule: Large tech companies get value-first variant
        if (
            segments.get("industry") == "tech"
            and segments.get("team_size") in ["large", "enterprise"]
            and 40 <= random_value <= 90
        ):
            value_first_variants = [
                v for v in test["variants"] if "value_first" in v["id"]
            ]
            if value_first_variants:
                return value_first_variants[0]

        return None

    def _get_default_assignment(self, test_name: str) -> dict[str, Any]:
        """Get default assignment when test is not active."""
        return {
            "test_name": test_name,
            "variant": OnboardingVariant.VALUE_FIRST,
            "variant_name": "Value-First Approach (Default)",
            "features": [
                "instant_insights",
                "optional_email_verification",
                "quick_assessment",
            ],
            "assigned_at": datetime.utcnow(),
            "assignment_method": "default",
        }

    def track_conversion_event(
        self,
        event_type: str,
        user_identifier: str,
        test_name: str = "onboarding_flow_v2",
        event_data: dict[str, Any] | None = None,
    ) -> None:
        """Track conversion events for A/B test analysis."""

        assignment_key = f"{test_name}:{user_identifier}"
        if assignment_key not in self.user_assignments:
            return

        assignment = self.user_assignments[assignment_key]

        # Store conversion event (in production, this would go to analytics database)
        conversion_event = {
            "test_name": test_name,
            "variant": assignment["variant"],
            "user_identifier": user_identifier,
            "event_type": event_type,
            "timestamp": datetime.utcnow(),
            "data": event_data or {},
        }

        # Log for now - in production, store in database
        print(f"AB_TEST_EVENT: {json.dumps(conversion_event, default=str)}")

    def should_show_feature(
        self,
        feature_name: str,
        user_identifier: str | None = None,
        test_name: str = "onboarding_flow_v2",
    ) -> bool:
        """Check if a user should see a specific feature based on their variant assignment."""

        if not user_identifier:
            return True  # Default to showing feature

        assignment_key = f"{test_name}:{user_identifier}"
        if assignment_key not in self.user_assignments:
            return True

        assignment = self.user_assignments[assignment_key]
        return feature_name in assignment.get("features", [])

    def get_test_results(
        self,
        test_name: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get A/B test results and statistical analysis."""

        if test_name not in self.active_tests:
            return {"error": "Test not found"}

        # In production, this would query the analytics database
        # For now, return mock results
        return {
            "test_name": test_name,
            "variants": [
                {
                    "id": OnboardingVariant.CONTROL,
                    "name": "Traditional Onboarding",
                    "users": 2500,
                    "conversions": 1000,
                    "conversion_rate": 0.40,
                    "avg_time_to_value": 15.2,  # minutes
                    "drop_off_rate": 0.60,
                    "confidence_interval": [0.38, 0.42],
                },
                {
                    "id": OnboardingVariant.VALUE_FIRST,
                    "name": "Value-First Approach",
                    "users": 5000,
                    "conversions": 3500,
                    "conversion_rate": 0.70,
                    "avg_time_to_value": 2.8,  # minutes
                    "drop_off_rate": 0.30,
                    "confidence_interval": [0.68, 0.72],
                },
                {
                    "id": OnboardingVariant.HYBRID,
                    "name": "Hybrid Approach",
                    "users": 2000,
                    "conversions": 1200,
                    "conversion_rate": 0.60,
                    "avg_time_to_value": 5.5,  # minutes
                    "drop_off_rate": 0.40,
                    "confidence_interval": [0.58, 0.62],
                },
                {
                    "id": OnboardingVariant.PERSONALIZED,
                    "name": "AI-Personalized",
                    "users": 500,
                    "conversions": 385,
                    "conversion_rate": 0.77,
                    "avg_time_to_value": 2.1,  # minutes
                    "drop_off_rate": 0.23,
                    "confidence_interval": [0.73, 0.81],
                },
            ],
            "statistical_significance": True,
            "winner": OnboardingVariant.VALUE_FIRST,
            "improvement": {
                "metric": "conversion_rate",
                "baseline": 0.40,
                "variant": 0.70,
                "improvement_percent": 75.0,
                "confidence": 0.99,
            },
            "sample_size_adequacy": True,
            "test_duration_days": 45,
        }

    def get_personalized_onboarding_config(
        self, user_identifier: str, user_segments: dict[str, str]
    ) -> dict[str, Any]:
        """Get personalized onboarding configuration based on user segments and A/B tests."""

        # Get variant assignment
        assignment = self.assign_variant(
            user_id=user_identifier, segments=user_segments
        )

        # Base configuration
        config = {
            "flow_type": assignment["variant"],
            "features": assignment["features"],
            "personalization": {
                "role_specific": True,
                "industry_specific": True,
                "team_size_specific": True,
            },
        }

        # Add role-specific customizations
        role = user_segments.get("role", "member")
        if role == "executive":
            config["skip_steps"] = ["team_creation_demo"]
            config["enhanced_features"] = [
                "executive_dashboard",
                "organizational_insights",
            ]
        elif role == "hr":
            config["emphasis_areas"] = [
                "retention_metrics",
                "culture_insights",
                "compliance_features",
            ]
        elif role == "manager":
            config["emphasis_areas"] = [
                "team_performance",
                "productivity_metrics",
                "action_items",
            ]

        # Add industry-specific customizations
        industry = user_segments.get("industry", "general")
        if industry == "tech":
            config["default_team_size"] = "5-10"
            config["recommended_assessments"] = ["big_five", "collaboration_style"]
        elif industry == "healthcare":
            config["compliance_mode"] = True
            config["recommended_assessments"] = ["communication", "stress_management"]

        # Add team size customizations
        team_size = user_segments.get("team_size", "medium")
        if team_size in ["large", "enterprise"]:
            config["features"].append("sub_team_management")
            config["recommended_features"].append("bulk_assessments")

        return config

    def optimize_variant_weights(self, test_name: str) -> None:
        """Automatically optimize variant weights based on performance."""

        results = self.get_test_results(test_name)

        if not results.get("statistical_significance"):
            return  # Don't optimize without statistical significance

        # Find best performing variant
        best_variant = max(results["variants"], key=lambda v: v["conversion_rate"])

        # Update weights to favor winning variant
        if test_name in self.active_tests:
            test = self.active_tests[test_name]
            total_weight = sum(v["weight"] for v in test["variants"])

            # Increase weight of winning variant
            for variant in test["variants"]:
                if variant["id"] == best_variant["id"]:
                    variant["weight"] = min(70, variant["weight"] + 10)  # Cap at 70%
                else:
                    # Redistribute remaining weight
                    variant["weight"] = max(5, variant["weight"] - 3)

            # Normalize weights to sum to 100
            current_total = sum(v["weight"] for v in test["variants"])
            if current_total != 100:
                scale_factor = 100 / current_total
                for variant in test["variants"]:
                    variant["weight"] = round(variant["weight"] * scale_factor)
