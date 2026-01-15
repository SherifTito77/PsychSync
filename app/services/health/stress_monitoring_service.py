"""
Real-Time Stress & Burnout Monitoring System
Detects early warning signs of work-related health risks

Integrates with:
- EmailMetadata for work pattern analysis
- CommunicationAnalysis for stress indicators
- WellnessMetrics for comprehensive health tracking
- BiometricData for physical health indicators
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

from sqlalchemy import select, and_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.db.models.email_metadata import EmailMetadata
from app.db.models.communication_analysis import CommunicationAnalysis, UrgencyLevel
from app.db.models.wellness_burnout import WellnessMetrics, BurnoutRiskLevel

logger = logging.getLogger(__name__)


class StressLevel(Enum):
    """Stress severity levels"""
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class BurnoutStage(Enum):
    """Burnout progression stages (Freudenberger's model)"""
    NONE = "none"
    HONEYMOON = "honeymoon"  # High satisfaction, high energy
    STRESS_ONSET = "stress_onset"  # Some difficulty, optimism
    CHRONIC_STRESS = "chronic_stress"  # More frequent stress
    BURNOUT = "burnout"  # Critical symptoms
    HABITUAL_BURNOUT = "habitual_burnout"  # Embedded in lifestyle


@dataclass
class BiometricData:
    """Biometric data from wearables (if available)"""
    heart_rate_avg: Optional[float] = None
    heart_rate_variability: Optional[float] = None
    resting_heart_rate: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[float] = None  # 0-1
    steps_per_day: Optional[int] = None
    activity_minutes: Optional[int] = None
    oxygen_saturation: Optional[float] = None


@dataclass
class HealthRiskIndicators:
    """Comprehensive health risk indicators"""
    stress_level: StressLevel
    burnout_stage: BurnoutStage
    cardiovascular_risk_score: float  # 0-1
    mental_health_risk: float  # 0-1
    work_life_imbalance: float  # 0-1
    sleep_disruption_score: float  # 0-1
    social_isolation_score: float  # 0-1

    # Intervention flags
    urgent_intervention_needed: bool
    recommend_medical_evaluation: bool
    recommend_immediate_break: bool
    recommend_workload_reduction: bool

    # Risk factors
    primary_risk_factors: List[str]
    warning_signs: List[str]
    protective_factors: List[str]

    # Data completeness
    data_sources: List[str]
    confidence_level: float  # 0-1


class StressMonitoringService:
    """
    Comprehensive stress and health monitoring service

    Integrates multiple data sources:
    - Email metadata for work patterns
    - Communication analysis for behavioral stress
    - Existing wellness metrics
    - Optional biometric data
    """

    # Evidence-based critical thresholds
    CRITICAL_THRESHOLDS = {
        'continuous_work_hours': 12,  # WHO guidelines
        'weekly_work_hours': 55,  # WHO: >55 = 35% higher stroke risk
        'after_hours_emails': 50,  # per week
        'weekend_work_percentage': 0.5,
        'vacation_days_unused': 15,
        'conflict_emails_per_week': 10,
        'heart_rate_elevated_hours': 4,
        'sleep_hours_below': 6,
        'stress_days_consecutive': 14,
        'negative_sentiment_threshold': -0.5,
        'conflict_probability_threshold': 0.6
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_health_risks(
        self,
        user_id: str,
        organization_id: str,
        time_window_days: int = 30,
        biometric_data: Optional[BiometricData] = None
    ) -> HealthRiskIndicators:
        """
        Comprehensive health risk analysis

        Analyzes:
        - Work patterns from email metadata
        - Communication stress signals
        - Existing wellness metrics
        - Biometric data (if available)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)

        # Gather data from multiple sources
        work_patterns = await self._analyze_work_patterns(user_id, cutoff_date)
        communication_stress = await self._analyze_communication_stress(user_id, cutoff_date)
        wellness_metrics = await self._get_wellness_metrics(user_id, cutoff_date)

        # Calculate risk scores
        stress_level = self._calculate_stress_level(
            work_patterns,
            communication_stress,
            wellness_metrics
        )

        burnout_stage = self._determine_burnout_stage(
            work_patterns,
            communication_stress,
            wellness_metrics
        )

        cardiovascular_risk = self._calculate_cardiovascular_risk(
            work_patterns,
            stress_level,
            biometric_data,
            wellness_metrics
        )

        mental_health_risk = self._calculate_mental_health_risk(
            communication_stress,
            wellness_metrics,
            work_patterns
        )

        # Identify risk factors and protective factors
        risk_factors = self._identify_risk_factors(
            work_patterns,
            communication_stress,
            wellness_metrics,
            biometric_data
        )

        warning_signs = self._identify_warning_signs(
            work_patterns,
            communication_stress,
            wellness_metrics
        )

        protective_factors = self._identify_protective_factors(wellness_metrics)

        # Determine intervention urgency
        urgent_intervention = self._requires_urgent_intervention(
            stress_level,
            cardiovascular_risk,
            risk_factors
        )

        recommend_medical = (
            cardiovascular_risk > 0.7 or
            any('cardiovascular' in r.lower() or 'blood pressure' in r.lower() for r in risk_factors)
        )

        recommend_break = stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]

        recommend_workload_reduction = (
            work_patterns.get('weekly_hours', 0) > 55 or
            work_patterns.get('continuous_days', 0) > 10
        )

        # Calculate data completeness
        data_sources = []
        if work_patterns.get('data_available'):
            data_sources.append('email_metadata')
        if communication_stress.get('data_available'):
            data_sources.append('communication_analysis')
        if wellness_metrics:
            data_sources.append('wellness_metrics')
        if biometric_data:
            data_sources.append('biometric_data')

        confidence_level = len(data_sources) / 4.0  # 0-1 based on available sources

        return HealthRiskIndicators(
            stress_level=stress_level,
            burnout_stage=burnout_stage,
            cardiovascular_risk_score=cardiovascular_risk,
            mental_health_risk=mental_health_risk,
            work_life_imbalance=work_patterns.get('imbalance_score', 0.5),
            sleep_disruption_score=wellness_metrics.sleep_disruption if wellness_metrics else 0.0,
            social_isolation_score=wellness_metrics.social_withdrawal if wellness_metrics else 0.0,
            urgent_intervention_needed=urgent_intervention,
            recommend_medical_evaluation=recommend_medical,
            recommend_immediate_break=recommend_break,
            recommend_workload_reduction=recommend_workload_reduction,
            primary_risk_factors=risk_factors,
            warning_signs=warning_signs,
            protective_factors=protective_factors,
            data_sources=data_sources,
            confidence_level=confidence_level
        )

    async def _analyze_work_patterns(
        self,
        user_id: str,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Analyze work patterns from email metadata"""

        # Import EmailConnection for proper join
        from app.db.models.email_connection import EmailConnection

        patterns = {
            'weekly_hours': 0,
            'after_hours_count': 0,
            'weekend_work_percentage': 0.0,
            'continuous_days': 0,
            'avg_emails_per_day': 0,
            'late_night_work_days': 0,
            'early_morning_work_days': 0,
            'imbalance_score': 0.0,
            'data_available': False
        }

        try:
            # Query email metadata for the user, joining with email_connections
            emails_query = select(EmailMetadata).join(
                EmailConnection,
                EmailMetadata.connection_id == EmailConnection.id
            ).where(
                and_(
                    EmailConnection.user_id == user_id,
                    EmailMetadata.sent_at >= cutoff_date
                )
            )

            # Get emails from last N days
            result = await self.db.execute(emails_query)
            emails = result.scalars().all()

            if emails:
                patterns['data_available'] = True
                patterns['avg_emails_per_day'] = len(emails) / 30

                # Calculate work hours based on email timestamps
                # Assuming 9 AM - 6 PM as work hours
                work_hours_emails = [
                    e for e in emails
                    if e.sent_at.hour >= 9 and e.sent_at.hour < 18
                ]
                after_hours_emails = [
                    e for e in emails
                    if e.sent_at.hour < 9 or e.sent_at.hour >= 18
                ]

                patterns['after_hours_count'] = len(after_hours_emails)

                # Weekend work
                weekend_emails = [
                    e for e in emails
                    if e.sent_at.weekday() >= 5  # Sat=5, Sun=6
                ]
                patterns['weekend_work_percentage'] = len(weekend_emails) / len(emails) if emails else 0

                # Late night work (after 9 PM)
                patterns['late_night_work_days'] = len({
                    e.sent_at.date() for e in after_hours_emails
                    if e.sent_at.hour >= 21
                })

                # Early morning work (before 7 AM)
                patterns['early_morning_work_days'] = len({
                    e.sent_at.date() for e in after_hours_emails
                    if e.sent_at.hour < 7
                })

                # Estimate weekly hours (very rough estimate)
                # ~1 email = 15 minutes of work on average
                estimated_work_hours = len(emails) * 0.25 / 4  # 4 weeks
                patterns['weekly_hours'] = min(estimated_work_hours, 80)  # Cap at 80 hours

                # Work-life imbalance score (0-1, higher = worse)
                imbalance = (
                    (patterns['after_hours_count'] / len(emails)) * 0.4 +
                    patterns['weekend_work_percentage'] * 0.3 +
                    (min(patterns['weekly_hours'] / 60, 1.5) - 1) * 0.3
                )
                patterns['imbalance_score'] = max(0, min(imbalance, 1))

        except Exception as e:
            logger.error(f"Error analyzing work patterns: {e}")

        return patterns

    async def _analyze_communication_stress(
        self,
        user_id: str,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Analyze communication patterns for stress indicators"""

        stress_indicators = {
            'urgency_emails': 0,
            'conflict_indicators': 0,
            'negative_sentiment_avg': 0.0,
            'response_pressure': 0.0,
            'communication_overload': False,
            'sentiment_volatility': 0.0,
            'conflict_probability_avg': 0.0,
            'data_available': False
        }

        try:
            # Query communication analysis
            analyses_query = select(CommunicationAnalysis).where(
                and_(
                    CommunicationAnalysis.user_id == user_id,
                    CommunicationAnalysis.analyzed_at >= cutoff_date
                )
            )

            result = await self.db.execute(analyses_query)
            analyses = result.scalars().all()

            if analyses:
                stress_indicators['data_available'] = True

                # Count urgency indicators
                urgent_emails = [
                    a for a in analyses
                    if a.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]
                ]
                stress_indicators['urgency_emails'] = len(urgent_emails)

                # Conflict indicators
                high_conflict = [
                    a for a in analyses
                    if a.conflict_probability and a.conflict_probability > 0.6
                ]
                stress_indicators['conflict_indicators'] = len(high_conflict)

                if high_conflict:
                    stress_indicators['conflict_probability_avg'] = sum(
                        a.conflict_probability for a in high_conflict
                    ) / len(high_conflict)

                # Sentiment analysis
                sentiments = [a.sentiment_score for a in analyses if a.sentiment_score is not None]
                if sentiments:
                    stress_indicators['negative_sentiment_avg'] = sum(
                        s for s in sentiments if s < 0
                    ) / len(sentiments) if any(s < 0 for s in sentiments) else 0.0

                    # Sentiment volatility (std deviation)
                    avg_sentiment = sum(sentiments) / len(sentiments)
                    variance = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments)
                    stress_indicators['sentiment_volatility'] = variance ** 0.5

                # Communication overload (>100 emails/week on average)
                stress_indicators['communication_overload'] = len(analyses) > 400  # ~100/week for 4 weeks

                # Response pressure (high urgency + negative sentiment)
                stress_indicators['response_pressure'] = (
                    (len(urgent_emails) / len(analyses)) * 0.5 +
                    (abs(stress_indicators['negative_sentiment_avg'])) * 0.5
                ) if analyses else 0

        except Exception as e:
            logger.error(f"Error analyzing communication stress: {e}")

        return stress_indicators

    async def _get_wellness_metrics(
        self,
        user_id: str,
        cutoff_date: datetime
    ) -> Optional[WellnessMetrics]:
        """Get most recent wellness metrics"""

        try:
            query = select(WellnessMetrics).where(
                and_(
                    WellnessMetrics.user_id == user_id,
                    WellnessMetrics.measurement_date >= cutoff_date
                )
            ).order_by(WellnessMetrics.measurement_date.desc()).limit(1)

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting wellness metrics: {e}")
            return None

    def _calculate_stress_level(
        self,
        work_patterns: Dict,
        communication_stress: Dict,
        wellness_metrics: Optional[WellnessMetrics]
    ) -> StressLevel:
        """Calculate overall stress level"""

        stress_score = 0.0

        # Work pattern indicators (0-0.4)
        if work_patterns.get('weekly_hours', 0) > 60:
            stress_score += 0.15
        elif work_patterns.get('weekly_hours', 0) > 50:
            stress_score += 0.10

        if work_patterns.get('continuous_days', 0) > 14:
            stress_score += 0.15

        if work_patterns.get('after_hours_count', 0) > 50:
            stress_score += 0.10

        # Communication stress (0-0.3)
        if communication_stress.get('conflict_indicators', 0) > 5:
            stress_score += 0.10

        if communication_stress.get('urgency_emails', 0) > 20:
            stress_score += 0.10

        if communication_stress.get('sentiment_volatility', 0) > 0.5:
            stress_score += 0.10

        # Wellness metrics (0-0.3)
        if wellness_metrics:
            if wellness_metrics.stress_level and wellness_metrics.stress_level >= 8:
                stress_score += 0.15
            elif wellness_metrics.stress_level and wellness_metrics.stress_level >= 6:
                stress_score += 0.10

            if wellness_metrics.exhaustion_level and wellness_metrics.exhaustion_level >= 8:
                stress_score += 0.15

        # Classify stress level
        if stress_score >= 0.8:
            return StressLevel.CRITICAL
        elif stress_score >= 0.6:
            return StressLevel.HIGH
        elif stress_score >= 0.4:
            return StressLevel.ELEVATED
        else:
            return StressLevel.NORMAL

    def _determine_burnout_stage(
        self,
        work_patterns: Dict,
        communication_stress: Dict,
        wellness_metrics: Optional[WellnessMetrics]
    ) -> BurnoutStage:
        """Determine burnout progression stage"""

        burnout_indicators = 0

        # Work pattern indicators
        if work_patterns.get('weekly_hours', 0) > 60:
            burnout_indicators += 1

        if work_patterns.get('continuous_days', 0) > 21:
            burnout_indicators += 1

        # Communication indicators
        if communication_stress.get('negative_sentiment_avg', 0) < -0.6:
            burnout_indicators += 1

        if communication_stress.get('conflict_indicators', 0) > 10:
            burnout_indicators += 1

        # Wellness metrics
        if wellness_metrics:
            if wellness_metrics.engagement_level and wellness_metrics.engagement_level <= 3:
                burnout_indicators += 1

            if wellness_metrics.exhaustion_level and wellness_metrics.exhaustion_level >= 8:
                burnout_indicators += 1

            if wellness_metrics.cynicism_level and wellness_metrics.cynicism_level >= 8:
                burnout_indicators += 1

            if wellness_metrics.professional_efficacy and wellness_metrics.professional_efficacy <= 3:
                burnout_indicators += 1

        # Classify burnout stage
        if burnout_indicators >= 5:
            return BurnoutStage.HABITUAL_BURNOUT
        elif burnout_indicators >= 4:
            return BurnoutStage.BURNOUT
        elif burnout_indicators >= 3:
            return BurnoutStage.CHRONIC_STRESS
        elif burnout_indicators >= 2:
            return BurnoutStage.STRESS_ONSET
        elif burnout_indicators >= 1:
            return BurnoutStage.HONEYMOON
        else:
            return BurnoutStage.NONE

    def _calculate_cardiovascular_risk(
        self,
        work_patterns: Dict,
        stress_level: StressLevel,
        biometric_data: Optional[BiometricData],
        wellness_metrics: Optional[WellnessMetrics]
    ) -> float:
        """Calculate cardiovascular disease risk score (0-1)"""

        risk_score = 0.0

        # Work-related risk factors (based on WHO studies)
        if work_patterns.get('weekly_hours', 0) > 55:
            risk_score += 0.25  # WHO: 35% higher stroke/heart disease risk

        if work_patterns.get('continuous_days', 0) > 14:
            risk_score += 0.15

        if stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]:
            risk_score += 0.20

        # Wellness metrics
        if wellness_metrics:
            if wellness_metrics.physical_wellness and wellness_metrics.physical_wellness <= 4:
                risk_score += 0.10

        # Biometric risk factors (if available)
        if biometric_data:
            if biometric_data.resting_heart_rate and biometric_data.resting_heart_rate > 80:
                risk_score += 0.15

            if biometric_data.heart_rate_variability and biometric_data.heart_rate_variability < 50:
                risk_score += 0.10  # Low HRV = chronic stress

            if biometric_data.blood_pressure_systolic and biometric_data.blood_pressure_systolic > 140:
                risk_score += 0.25

            if biometric_data.sleep_hours and biometric_data.sleep_hours < 6:
                risk_score += 0.15

            if biometric_data.steps_per_day and biometric_data.steps_per_day < 5000:
                risk_score += 0.10  # Sedentary lifestyle

            if biometric_data.oxygen_saturation and biometric_data.oxygen_saturation < 95:
                risk_score += 0.15

        return min(1.0, risk_score)

    def _calculate_mental_health_risk(
        self,
        communication_stress: Dict,
        wellness_metrics: Optional[WellnessMetrics],
        work_patterns: Dict
    ) -> float:
        """Calculate mental health risk score (0-1)"""

        risk_score = 0.0

        # Communication risks
        if communication_stress.get('negative_sentiment_avg', 0) < -0.6:
            risk_score += 0.20

        if communication_stress.get('conflict_indicators', 0) > 10:
            risk_score += 0.15

        if communication_stress.get('sentiment_volatility', 0) > 0.7:
            risk_score += 0.15

        # Wellness metrics
        if wellness_metrics:
            if wellness_metrics.mental_wellness and wellness_metrics.mental_wellness <= 4:
                risk_score += 0.20

            if wellness_metrics.emotional_wellness and wellness_metrics.emotional_wellness <= 4:
                risk_score += 0.15

            if wellness_metrics.social_wellness and wellness_metrics.social_wellness <= 4:
                risk_score += 0.10

        # Work-life balance
        if work_patterns.get('imbalance_score', 0) > 0.7:
            risk_score += 0.15

        return min(1.0, risk_score)

    def _identify_risk_factors(
        self,
        work_patterns: Dict,
        communication_stress: Dict,
        wellness_metrics: Optional[WellnessMetrics],
        biometric_data: Optional[BiometricData]
    ) -> List[str]:
        """Identify specific risk factors"""

        risk_factors = []

        # Work pattern risks
        if work_patterns.get('weekly_hours', 0) > 60:
            risk_factors.append("Excessive work hours (>60/week) - cardiovascular risk")

        if work_patterns.get('continuous_days', 0) > 14:
            risk_factors.append("No rest days in 2+ weeks - burnout risk")

        if work_patterns.get('after_hours_count', 0) > 50:
            risk_factors.append("Chronic after-hours work - work-life imbalance")

        if work_patterns.get('late_night_work_days', 0) > 10:
            risk_factors.append("Frequent late-night work - sleep disruption risk")

        # Communication risks
        if communication_stress.get('conflict_indicators', 0) > 10:
            risk_factors.append("High conflict communication - chronic stress")

        if communication_stress.get('urgency_emails', 0) > 30:
            risk_factors.append("Constant urgency pressure - anxiety risk")

        if communication_stress.get('negative_sentiment_avg', 0) < -0.6:
            risk_factors.append("Consistently negative communication - depression risk")

        # Wellness risks
        if wellness_metrics:
            if wellness_metrics.engagement_level and wellness_metrics.engagement_level <= 4:
                risk_factors.append("Low engagement - potential depression")

            if wellness_metrics.social_wellness and wellness_metrics.social_wellness <= 4:
                risk_factors.append("Social withdrawal - isolation risk")

        # Biometric risks
        if biometric_data:
            if biometric_data.resting_heart_rate and biometric_data.resting_heart_rate > 85:
                risk_factors.append("Elevated resting heart rate - cardiovascular strain")

            if biometric_data.blood_pressure_systolic and biometric_data.blood_pressure_systolic > 140:
                risk_factors.append("High blood pressure - immediate medical evaluation needed")

            if biometric_data.sleep_hours and biometric_data.sleep_hours < 5:
                risk_factors.append("Severe sleep deprivation - health emergency")

        return risk_factors

    def _identify_warning_signs(
        self,
        work_patterns: Dict,
        communication_stress: Dict,
        wellness_metrics: Optional[WellnessMetrics]
    ) -> List[str]:
        """Identify early warning signs"""

        warnings = []

        if work_patterns.get('weekend_work_percentage', 0) > 0.5:
            warnings.append("Working most weekends")

        if communication_stress.get('sentiment_volatility', 0) > 0.6:
            warnings.append("Emotional instability in communication")

        if work_patterns.get('imbalance_score', 0) > 0.7:
            warnings.append("Severe work-life imbalance")

        if communication_stress.get('communication_overload', False):
            warnings.append("Excessive communication volume")

        return warnings

    def _identify_protective_factors(
        self,
        wellness_metrics: Optional[WellnessMetrics]
    ) -> List[str]:
        """Identify protective factors"""

        protective = []

        if wellness_metrics:
            if wellness_metrics.resilience_score and wellness_metrics.resilience_score >= 7:
                protective.append("High psychological resilience")

            if wellness_metrics.social_wellness and wellness_metrics.social_wellness >= 7:
                protective.append("Strong social connections")

            if wellness_metrics.professional_wellness and wellness_metrics.professional_wellness >= 7:
                protective.append("High professional satisfaction")

            if wellness_metrics.support_systems_quality and wellness_metrics.support_systems_quality >= 7:
                protective.append("Good support systems")

        return protective

    def _requires_urgent_intervention(
        self,
        stress_level: StressLevel,
        cardiovascular_risk: float,
        risk_factors: List[str]
    ) -> bool:
        """Determine if urgent intervention is needed"""

        if stress_level == StressLevel.CRITICAL:
            return True

        if cardiovascular_risk > 0.8:
            return True

        critical_keywords = ['emergency', 'severe', 'immediate', 'health emergency']
        if any(keyword in ' '.join(risk_factors).lower() for keyword in critical_keywords):
            return True

        return False


# Export
__all__ = ['StressMonitoringService', 'HealthRiskIndicators', 'BiometricData', 'StressLevel', 'BurnoutStage']
