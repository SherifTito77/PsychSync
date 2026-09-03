# app/services/churnPredictionService.py
"""Churn Prediction Service

Calculates churn risk scores based on behavioral signals and usage patterns.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, case, desc, func
from sqlalchemy.orm import Session

from app.db.models.churn_prediction import (
    ChurnRiskScore,
    ChurnTriggerCooldown,
    ChurnTriggerExecution,
)
from app.db.models.user import User
from app.db.models.user_activation import UserActivation


class ChurnRiskCalculator:
    """Calculate churn risk scores for users"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_user_risk(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive churn risk score for a user.

        Returns:
            Dictionary with overall_risk, overall_score, signal_scores, etc.
        """
        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Calculate individual signal scores
        signals = {
            "usage_decline": self._calculate_usage_decline(user),
            "adoption_stagnation": self._calculate_adoption_stagnation(user),
            "failed_conversion": self._calculate_failed_conversion(user),
            "support_sentiment": self._calculate_support_sentiment(user),
            "assessment_limit": self._calculate_assessment_limit(user),
            "login_frequency": self._calculate_login_frequency(user),
            "survey_sentiment": self._calculate_survey_sentiment(user),
            "competitor_research": self._calculate_competitor_research(user),
        }

        # Weighted average for overall score
        weights = {
            "usage_decline": 0.25,
            "login_frequency": 0.20,
            "competitor_research": 0.15,
            "failed_conversion": 0.12,
            "assessment_limit": 0.10,
            "support_sentiment": 0.08,
            "adoption_stagnation": 0.05,
            "survey_sentiment": 0.05,
        }

        overall_score = sum(
            signals[signal]["risk_score"] * weights[signal] for signal in signals
        )

        # Determine risk category
        overall_risk = (
            "critical"
            if overall_score >= 80
            else (
                "high"
                if overall_score >= 60
                else (
                    "medium"
                    if overall_score >= 40
                    else "low" if overall_score >= 20 else "safe"
                )
            )
        )

        # Identify top risk factors
        sorted_signals = sorted(
            signals.items(), key=lambda x: x[1]["risk_score"], reverse=True
        )[:3]

        primary_factors = [s[0] for s in sorted_signals if s[1]["risk_score"] > 0]

        return {
            "overall_risk": overall_risk,
            "overall_score": int(overall_score),
            "signal_scores": {k: v["risk_score"] for k, v in signals.items()},
            "primary_risk_factors": primary_factors,
            "recommended_actions": self._get_recommendations(
                overall_risk, primary_factors
            ),
        }

    def _calculate_usage_decline(self, user: User) -> Dict[str, Any]:
        """Calculate usage decline signal score"""
        # Get assessment counts for last 30 vs previous 30 days
        now = datetime.utcnow()
        last_30_start = now - timedelta(days=30)
        prev_30_start = now - timedelta(days=60)
        prev_30_end = now - timedelta(days=30)

        # This would query actual usage data - placeholder for now
        # In production, you'd query assessments table or similar
        current_assessments = 0  # TODO: Query actual data
        previous_assessments = 0  # TODO: Query actual data

        if previous_assessments == 0:
            decline = 0
        else:
            decline = (
                (previous_assessments - current_assessments) / previous_assessments
            ) * 100

        is_declining = decline > 50 or current_assessments == 0
        risk_score = max(decline, 0) if is_declining else 0

        return {
            "assessments_last_30_days": current_assessments,
            "assessments_previous_30_days": previous_assessments,
            "decline_percentage": round(decline, 2),
            "is_declining": is_declining,
            "risk_score": int(min(risk_score, 100)),
        }

    def _calculate_adoption_stagnation(self, user: User) -> Dict[str, Any]:
        """Calculate feature adoption stagnation signal score"""
        # Placeholder - in production, query feature usage data
        days_since_new_feature = 0  # TODO: Query actual data
        used_advanced = False  # TODO: Check actual feature usage

        is_stagnating = days_since_new_feature > 60 or not used_advanced
        risk_score = min(days_since_new_feature, 100) if is_stagnating else 0

        return {
            "days_since_new_feature_used": days_since_new_feature,
            "uses_core_features_only": not used_advanced,
            "is_stagnating": is_stagnating,
            "risk_score": risk_score,
        }

    def _calculate_failed_conversion(self, user: User) -> Dict[str, Any]:
        """Calculate failed conversion attempts signal score"""
        # Placeholder - in production, query conversion events
        upgrade_attempts = 0  # TODO: Count upgrade_click events
        checkouts = 0  # TODO: Count checkout_initiated events
        completed = 0  # TODO: Count checkout_completed events

        has_failed = checkouts > 0 and completed == 0

        return {
            "upgrade_click_count": upgrade_attempts,
            "checkout_initiated": checkouts > 0,
            "checkout_completed": completed > 0,
            "has_failed_conversion": has_failed,
            "risk_score": 80 if has_failed else 0,
        }

    def _calculate_support_sentiment(self, user: User) -> Dict[str, Any]:
        """Calculate support sentiment signal score"""
        # Placeholder - in production, query support tickets
        tickets_last_30 = 0  # TODO: Count tickets
        negative_tickets = 0  # TODO: Count negative sentiment tickets

        has_decline = negative_tickets >= 2
        risk_score = abs(negative_tickets * 20) if has_decline else 0

        return {
            "support_tickets_last_30_days": tickets_last_30,
            "negative_sentiment_tickets": negative_tickets,
            "has_sentiment_decline": has_decline,
            "risk_score": int(min(risk_score, 100)),
        }

    def _calculate_assessment_limit(self, user: User) -> Dict[str, Any]:
        """Calculate assessment limit signal score"""
        # Placeholder - in production, query current usage
        assessments_completed = 0  # TODO: Count this month's assessments
        assessment_limit = 3  # TODO: Get from user's subscription tier

        limit_reached = assessments_completed >= assessment_limit
        days_since = 0  # TODO: Calculate days since limit reached
        viewed_pricing = False  # TODO: Check pricing_page_view event

        risk_score = (
            70 if (limit_reached and not viewed_pricing and days_since >= 7) else 0
        )

        return {
            "assessments_completed": assessments_completed,
            "assessment_limit": assessment_limit,
            "limit_reached": limit_reached,
            "days_since_limit_reached": days_since,
            "viewed_pricing_page": viewed_pricing,
            "risk_score": risk_score,
        }

    def _calculate_login_frequency(self, user: User) -> Dict[str, Any]:
        """Calculate login frequency decline signal score"""
        # Placeholder - in production, query login events
        logins_last_30 = 0  # TODO: Count logins in last 30 days
        logins_prev_30 = 0  # TODO: Count logins in previous 30 days
        days_since = 0  # TODO: Days since last login

        if logins_prev_30 == 0:
            decline = 0
        else:
            decline = ((logins_prev_30 - logins_last_30) / logins_prev_30) * 100

        is_declining = decline > 50 or days_since > 14

        return {
            "logins_last_30_days": logins_last_30,
            "logins_previous_30_days": logins_prev_30,
            "login_decline_percentage": round(decline, 2),
            "days_since_last_login": days_since,
            "is_declining": is_declining,
            "risk_score": int(max(decline, days_since * 2) if is_declining else 0),
        }

    def _calculate_survey_sentiment(self, user: User) -> Dict[str, Any]:
        """Calculate survey/NPS sentiment signal score"""
        # Placeholder - in production, query survey responses
        latest_nps = 0  # TODO: Get latest NPS score
        has_churn_signals = False  # TODO: Check for "cancel" or "competitor" mentions

        is_negative = latest_nps <= 6 or has_churn_signals

        return {
            "latest_nps_score": latest_nps,
            "mentioned_competitors": has_churn_signals,
            "mentioned_cancellation": has_churn_signals,
            "is_negative_sentiment": is_negative,
            "risk_score": 70 if is_negative else 0,
        }

    def _calculate_competitor_research(self, user: User) -> Dict[str, Any]:
        """Calculate competitor research signal score"""
        # Placeholder - in production, query for competitor mentions
        mentioned_competitor = False  # TODO: Check support tickets
        viewed_comparison = False  # TODO: Check for comparison_page_view events
        exported_data = False  # TODO: Check for data_export events

        is_researching = mentioned_competitor or viewed_comparison or exported_data

        return {
            "mentioned_competitors_in_support": mentioned_competitor,
            "viewed_competitor_comparison": viewed_comparison,
            "exported_data_for_migration": exported_data,
            "is_researching_competitors": is_researching,
            "risk_score": (
                90
                if exported_data
                else (60 if (viewed_comparison or mentioned_competitor) else 0)
            ),
        }

    def _get_recommendations(self, risk_level: str, factors: List[str]) -> List[str]:
        """Generate recommended actions based on risk level and primary factors"""
        recommendations = {
            "critical": [
                "Immediate customer success outreach within 24 hours",
                "Offer personalized discount or incentive",
                "Schedule executive call if enterprise",
                "Assign dedicated success manager",
            ],
            "high": [
                "Customer success outreach within 72 hours",
                "Send personalized re-engagement email",
                "Offer training or resources",
                "Check for unresolved support issues",
            ],
            "medium": [
                "Add to automated nurturing campaign",
                "Send feature highlight newsletter",
                "Invite to webinar or training",
                "Monitor for signal escalation",
            ],
            "low": [
                "Continue normal monitoring",
                "Include in monthly newsletter",
                "Track risk score trends",
            ],
            "safe": ["No action needed", "Continue normal engagement"],
        }

        return recommendations.get(risk_level, [])


class ChurnTriggerService:
    """Execute churn intervention triggers based on risk scores"""

    def __init__(self, db: Session):
        self.db = db
        self.calculator = ChurnRiskCalculator(db)

    def evaluate_and_execute_triggers(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Evaluate user's churn risk and execute appropriate triggers.

        Returns:
            List of executed triggers with their results.
        """
        executed = []

        # Calculate risk
        try:
            risk_data = self.calculator.calculate_user_risk(user_id)
        except ValueError as e:
            # User not found or other error
            return executed

        # Check each trigger
        triggers = self._get_triggers_for_risk(risk_data["overall_risk"])

        for trigger_config in triggers:
            # Check if on cooldown
            if self._is_on_cooldown(user_id, trigger_config["name"]):
                continue

            # Execute trigger action
            result = self._execute_trigger_action(user_id, trigger_config, risk_data)

            # Log execution
            self._log_execution(user_id, trigger_config, result)

            # Set cooldown
            self._set_cooldown(
                user_id, trigger_config["name"], trigger_config["cooldown_days"]
            )

            executed.append({"trigger": trigger_config["name"], "result": result})

        # Store risk score
        self._store_risk_score(user_id, risk_data)

        return executed

    def _get_triggers_for_risk(self, risk_level: str) -> List[Dict[str, Any]]:
        """Get list of triggers for given risk level"""
        # TODO: Move this to database or config file
        all_triggers = [
            {
                "name": "critical_usage_decline",
                "condition": lambda r: r >= 80,
                "action": "email",
                "priority": "critical",
                "cooldown_days": 30,
            },
            {
                "name": "competitor_research_detected",
                "condition": lambda r, f: "competitor_research" in f,
                "action": "win_back_offer",
                "priority": "critical",
                "cooldown_days": 60,
            },
            {
                "name": "assessment_limit_reached",
                "condition": lambda r, f: "assessment_limit" in f,
                "action": "upgrade_reminder",
                "priority": "medium",
                "cooldown_days": 7,
            },
            {
                "name": "negative_nps_detected",
                "condition": lambda r, f: "survey_sentiment" in f,
                "action": "follow_up_survey",
                "priority": "high",
                "cooldown_days": 14,
            },
            {
                "name": "login_frequency_decline",
                "condition": lambda r: r >= 40,
                "action": "we_miss_you_email",
                "priority": "medium",
                "cooldown_days": 14,
            },
        ]

        # Filter triggers by risk level
        if risk_level == "critical":
            return [t for t in all_triggers if t["priority"] in ["critical", "high"]]
        elif risk_level == "high":
            return [
                t
                for t in all_triggers
                if t["priority"] in ["critical", "high", "medium"]
            ]
        elif risk_level == "medium":
            return [t for t in all_triggers if t["priority"] in ["medium", "high"]]
        else:
            return []

    def _is_on_cooldown(self, user_id: str, trigger_name: str) -> bool:
        """Check if trigger is on cooldown for user"""
        cooldown = (
            self.db.query(ChurnTriggerCooldown)
            .filter(
                ChurnTriggerCooldown.user_id == user_id,
                ChurnTriggerCooldown.trigger_name == trigger_name,
                ChurnTriggerCooldown.cooldown_until > datetime.utcnow(),
            )
            .first()
        )

        return cooldown is not None

    def _execute_trigger_action(
        self, user_id: str, trigger_config: Dict, risk_data: Dict
    ) -> str:
        """Execute the trigger action"""
        action = trigger_config["action"]

        # TODO: Implement actual actions (send emails, create tasks, etc.)
        # For now, just log the action
        print(f"Would execute action '{action}' for user {user_id}")

        return "sent"  # or "failed", "skipped"

    def _log_execution(self, user_id: str, trigger_config: Dict, result: str):
        """Log trigger execution to database"""
        execution = ChurnTriggerExecution(
            user_id=user_id,
            trigger_name=trigger_config["name"],
            priority=trigger_config["priority"],
            action_taken=f"Executed {trigger_config['action']} action",
            result=result,
        )

        self.db.add(execution)
        self.db.commit()

    def _set_cooldown(self, user_id: str, trigger_name: str, days: int):
        """Set cooldown for trigger"""
        cooldown_until = datetime.utcnow() + timedelta(days=days)

        # Delete existing cooldown
        self.db.query(ChurnTriggerCooldown).filter(
            ChurnTriggerCooldown.user_id == user_id,
            ChurnTriggerCooldown.trigger_name == trigger_name,
        ).delete()

        # Create new cooldown
        cooldown = ChurnTriggerCooldown(
            user_id=user_id, trigger_name=trigger_name, cooldown_until=cooldown_until
        )

        self.db.add(cooldown)
        self.db.commit()

    def _store_risk_score(self, user_id: str, risk_data: Dict):
        """Store calculated risk score in database"""
        # Check if user already has a risk score from today
        existing = (
            self.db.query(ChurnRiskScore)
            .filter(
                ChurnRiskScore.user_id == user_id,
                func.date(ChurnRiskScore.calculated_at) == func.date(datetime.utcnow()),
            )
            .first()
        )

        if existing:
            # Update existing
            existing.overall_risk = risk_data["overall_risk"]
            existing.overall_score = risk_data["overall_score"]
            existing.usage_decline_score = risk_data["signal_scores"].get(
                "usage_decline"
            )
            existing.adoption_stagnation_score = risk_data["signal_scores"].get(
                "adoption_stagnation"
            )
            existing.failed_conversion_score = risk_data["signal_scores"].get(
                "failed_conversion"
            )
            existing.support_sentiment_score = risk_data["signal_scores"].get(
                "support_sentiment"
            )
            existing.assessment_limit_score = risk_data["signal_scores"].get(
                "assessment_limit"
            )
            existing.login_frequency_score = risk_data["signal_scores"].get(
                "login_frequency"
            )
            existing.survey_sentiment_score = risk_data["signal_scores"].get(
                "survey_sentiment"
            )
            existing.competitor_research_score = risk_data["signal_scores"].get(
                "competitor_research"
            )
            existing.primary_risk_factors = risk_data["primary_risk_factors"]
        else:
            # Create new
            score = ChurnRiskScore(
                user_id=user_id,
                overall_risk=risk_data["overall_risk"],
                overall_score=risk_data["overall_score"],
                usage_decline_score=risk_data["signal_scores"].get("usage_decline"),
                adoption_stagnation_score=risk_data["signal_scores"].get(
                    "adoption_stagnation"
                ),
                failed_conversion_score=risk_data["signal_scores"].get(
                    "failed_conversion"
                ),
                support_sentiment_score=risk_data["signal_scores"].get(
                    "support_sentiment"
                ),
                assessment_limit_score=risk_data["signal_scores"].get(
                    "assessment_limit"
                ),
                login_frequency_score=risk_data["signal_scores"].get("login_frequency"),
                survey_sentiment_score=risk_data["signal_scores"].get(
                    "survey_sentiment"
                ),
                competitor_research_score=risk_data["signal_scores"].get(
                    "competitor_research"
                ),
                primary_risk_factors=risk_data["primary_risk_factors"],
            )

            self.db.add(score)

        self.db.commit()
