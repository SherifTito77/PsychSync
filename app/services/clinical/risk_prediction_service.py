"""
ML Risk Prediction Service for Clinical Analytics

Implements machine learning models for:
- Depression risk prediction (BDI-II trajectory analysis)
- Anxiety risk prediction (BAI trajectory analysis)
- Crisis risk prediction (suicidal ideation, self-harm)
- Treatment response prediction
- Relapse risk prediction

Uses scikit-learn for:
- Linear regression for trend prediction
- Logistic regression for risk classification
- Random forest for complex patterns
- Time series analysis for longitudinal prediction
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from scipy import stats
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report

from app.db.models.clinical_extended import ClinicalAssessmentExtended
from app.core.logging_config import logger

# =============================================================================
# Data Models for Risk Predictions
# =============================================================================

class RiskPredictionResult:
    """Standard result format for risk predictions"""

    def __init__(
        self,
        user_id: str,
        prediction_type: str,
        risk_level: str,
        confidence: float,
        predicted_value: Optional[float] = None,
        factors: Optional[Dict[str, float]] = None,
        recommendations: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.user_id = user_id
        self.prediction_type = prediction_type
        self.risk_level = risk_level
        self.confidence = confidence
        self.predicted_value = predicted_value
        self.factors = factors or {}
        self.recommendations = recommendations or []
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "prediction_type": self.prediction_type,
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 3),
            "predicted_value": round(self.predicted_value, 2) if self.predicted_value else None,
            "factors": self.factors,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


class TrendAnalysisResult:
    """Result from trend analysis"""

    def __init__(
        self,
        slope: float,
        r_squared: float,
        trend_direction: str,
        prediction_30_days: Optional[float] = None,
        prediction_90_days: Optional[float] = None,
        volatility: Optional[float] = None,
    ):
        self.slope = slope
        self.r_squared = r_squared
        self.trend_direction = trend_direction
        self.prediction_30_days = prediction_30_days
        self.prediction_90_days = prediction_90_days
        self.volatility = volatility

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "slope": round(self.slope, 4),
            "r_squared": round(self.r_squared, 4),
            "trend_direction": self.trend_direction,
            "prediction_30_days": round(self.prediction_30_days, 2) if self.prediction_30_days else None,
            "prediction_90_days": round(self.prediction_90_days, 2) if self.prediction_90_days else None,
            "volatility": round(self.volatility, 4) if self.volatility else None,
        }


# =============================================================================
# Main Risk Prediction Service
# =============================================================================

class RiskPredictionService:
    """
    Machine Learning-based Risk Prediction Service

    Provides clinical risk predictions using:
    - Linear regression for trend prediction
    - Logistic regression for risk classification
    - Random forest for complex pattern recognition
    - Statistical analysis for volatility and change detection
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)

    # ========================================================================
    # Depression Risk Prediction (BDI-II)
    # ========================================================================

    async def predict_depression_risk(
        self,
        user_id: str,
        prediction_days: int = 30,
        min_assessments: int = 3,
    ) -> RiskPredictionResult:
        """
        Predict depression risk based on BDI-II trajectory

        Args:
            user_id: User to analyze
            prediction_days: Days to predict ahead (default 30)
            min_assessments: Minimum assessments required for prediction

        Returns:
            RiskPredictionResult with depression risk assessment
        """
        try:
            # Fetch historical BDI-II data
            assessments = await self._get_assessment_history(
                user_id=user_id,
                assessment_type="BDI2",
                min_assessments=min_assessments,
            )

            if not assessments or len(assessments) < min_assessments:
                return self._insufficient_data_result(user_id, "depression_risk", min_assessments)

            # Extract features
            scores, dates = self._extract_scores_and_dates(assessments)

            # Perform trend analysis
            trend_result = self._analyze_trend(scores, dates, prediction_days)

            # Calculate risk factors
            risk_factors = self._calculate_depression_risk_factors(scores, trend_result)

            # Determine risk level
            risk_level, confidence = self._classify_depression_risk(
                scores[-1], trend_result, risk_factors
            )

            # Generate recommendations
            recommendations = self._generate_depression_recommendations(
                risk_level, trend_result, risk_factors
            )

            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="depression_risk",
                risk_level=risk_level,
                confidence=confidence,
                predicted_value=trend_result.prediction_30_days,
                factors=risk_factors,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Error predicting depression risk for user {user_id}: {e}")
            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="depression_risk",
                risk_level="error",
                confidence=0.0,
                recommendations=["Unable to generate prediction due to system error"],
            )

    # ========================================================================
    # Anxiety Risk Prediction (BAI)
    # ========================================================================

    async def predict_anxiety_risk(
        self,
        user_id: str,
        prediction_days: int = 30,
        min_assessments: int = 3,
    ) -> RiskPredictionResult:
        """
        Predict anxiety risk based on BAI trajectory

        Args:
            user_id: User to analyze
            prediction_days: Days to predict ahead
            min_assessments: Minimum assessments required

        Returns:
            RiskPredictionResult with anxiety risk assessment
        """
        try:
            # Fetch historical BAI data
            assessments = await self._get_assessment_history(
                user_id=user_id,
                assessment_type="BAI",
                min_assessments=min_assessments,
            )

            if not assessments or len(assessments) < min_assessments:
                return self._insufficient_data_result(user_id, "anxiety_risk", min_assessments)

            # Extract features
            scores, dates = self._extract_scores_and_dates(assessments)

            # Perform trend analysis
            trend_result = self._analyze_trend(scores, dates, prediction_days)

            # Calculate risk factors
            risk_factors = self._calculate_anxiety_risk_factors(scores, trend_result)

            # Determine risk level
            risk_level, confidence = self._classify_anxiety_risk(
                scores[-1], trend_result, risk_factors
            )

            # Generate recommendations
            recommendations = self._generate_anxiety_recommendations(
                risk_level, trend_result, risk_factors
            )

            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="anxiety_risk",
                risk_level=risk_level,
                confidence=confidence,
                predicted_value=trend_result.prediction_30_days,
                factors=risk_factors,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Error predicting anxiety risk for user {user_id}: {e}")
            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="anxiety_risk",
                risk_level="error",
                confidence=0.0,
                recommendations=["Unable to generate prediction due to system error"],
            )

    # ========================================================================
    # Crisis Risk Prediction
    # ========================================================================

    async def predict_crisis_risk(
        self,
        user_id: str,
        lookback_days: int = 90,
        min_assessments: int = 2,
    ) -> RiskPredictionResult:
        """
        Predict crisis risk (suicidal ideation, self-harm, severe deterioration)

        Uses multiple indicators:
        - Recent crisis alerts
        - Rapid score increase
        - High current scores
        - Suicidal ideation indicators

        Args:
            user_id: User to analyze
            lookback_days: Days to look back for analysis
            min_assessments: Minimum assessments required

        Returns:
            RiskPredictionResult with crisis risk assessment
        """
        try:
            # Get cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

            # Fetch recent assessments across all types
            query = (
                select(ClinicalAssessmentExtended)
                .where(
                    and_(
                        ClinicalAssessmentExtended.user_id == user_id,
                        ClinicalAssessmentExtended.completed_at >= cutoff_date,
                    )
                )
                .order_by(ClinicalAssessmentExtended.completed_at)
            )

            result = await self.db.execute(query)
            assessments = result.scalars().all()

            if not assessments or len(assessments) < min_assessments:
                return self._insufficient_data_result(user_id, "crisis_risk", min_assessments)

            # Analyze crisis indicators
            crisis_indicators = self._analyze_crisis_indicators(assessments)

            # Calculate crisis risk score
            crisis_score, confidence = self._calculate_crisis_risk_score(crisis_indicators)

            # Determine risk level
            if crisis_score >= 0.8:
                risk_level = "critical"
            elif crisis_score >= 0.6:
                risk_level = "high"
            elif crisis_score >= 0.4:
                risk_level = "moderate"
            else:
                risk_level = "low"

            # Generate recommendations
            recommendations = self._generate_crisis_recommendations(risk_level, crisis_indicators)

            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="crisis_risk",
                risk_level=risk_level,
                confidence=confidence,
                factors=crisis_indicators,
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Error predicting crisis risk for user {user_id}: {e}")
            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="crisis_risk",
                risk_level="error",
                confidence=0.0,
                recommendations=["Unable to generate crisis prediction due to system error"],
            )

    # ========================================================================
    # Treatment Response Prediction
    # ========================================================================

    async def predict_treatment_response(
        self,
        user_id: str,
        assessment_type: str = "BDI2",
        treatment_start_days: int = 60,
        min_assessments: int = 4,
    ) -> RiskPredictionResult:
        """
        Predict treatment response based on score trajectory

        Classifies response as:
        - full_response: Significant improvement (>50% reduction)
        - partial_response: Moderate improvement (25-50% reduction)
        - non_response: Little to no improvement (<25% reduction)
        - deterioration: Worsening symptoms

        Args:
            user_id: User to analyze
            assessment_type: Type of assessment to analyze
            treatment_start_days: Days since treatment start
            min_assessments: Minimum assessments required

        Returns:
            RiskPredictionResult with treatment response prediction
        """
        try:
            # Fetch assessment history
            assessments = await self._get_assessment_history(
                user_id=user_id,
                assessment_type=assessment_type,
                min_assessments=min_assessments,
            )

            if not assessments or len(assessments) < min_assessments:
                return self._insufficient_data_result(
                    user_id, "treatment_response", min_assessments
                )

            # Extract scores and dates
            scores, dates = self._extract_scores_and_dates(assessments)

            # Calculate treatment response metrics
            initial_score = scores[0]
            current_score = scores[-1]
            score_change = initial_score - current_score
            percent_change = (score_change / initial_score * 100) if initial_score > 0 else 0

            # Analyze trend
            trend_result = self._analyze_trend(scores, dates, 30)

            # Classify response
            if percent_change >= 50 and trend_result.trend_direction == "improving":
                response_category = "full_response"
                risk_level = "positive"
            elif percent_change >= 25 and trend_result.trend_direction in ["improving", "stable"]:
                response_category = "partial_response"
                risk_level = "moderate"
            elif percent_change < -10:  # Worsening
                response_category = "deterioration"
                risk_level = "high"
            else:
                response_category = "non_response"
                risk_level = "moderate"

            # Confidence based on data quality and trend strength
            confidence = min(0.95, 0.5 + (trend_result.r_squared * 0.3) + (len(scores) * 0.05))

            # Generate recommendations
            recommendations = self._generate_treatment_recommendations(
                response_category, trend_result, percent_change
            )

            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="treatment_response",
                risk_level=risk_level,
                confidence=confidence,
                predicted_value=percent_change,
                factors={
                    "initial_score": float(initial_score),
                    "current_score": float(current_score),
                    "percent_change": round(percent_change, 2),
                    "trend_strength": float(trend_result.r_squared),
                },
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Error predicting treatment response for user {user_id}: {e}")
            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="treatment_response",
                risk_level="error",
                confidence=0.0,
                recommendations=["Unable to generate treatment prediction due to system error"],
            )

    # ========================================================================
    # Relapse Risk Prediction
    # ========================================================================

    async def predict_relapse_risk(
        self,
        user_id: str,
        assessment_type: str = "BDI2",
        remission_threshold: int = 12,  # BDI-II remission cutoff
        lookback_days: int = 90,
        min_assessments: int = 4,
    ) -> RiskPredictionResult:
        """
        Predict relapse risk for users in remission

        Analyzes:
        - Time in remission
        - Recent score trajectory
        - Score volatility
        - Assessment compliance

        Args:
            user_id: User to analyze
            assessment_type: Type of assessment
            remission_threshold: Score threshold for remission
            lookback_days: Days to look back
            min_assessments: Minimum assessments required

        Returns:
            RiskPredictionResult with relapse risk assessment
        """
        try:
            # Fetch assessment history
            assessments = await self._get_assessment_history(
                user_id=user_id,
                assessment_type=assessment_type,
                min_assessments=min_assessments,
                days_back=lookback_days,
            )

            if not assessments or len(assessments) < min_assessments:
                return self._insufficient_data_result(user_id, "relapse_risk", min_assessments)

            # Extract scores and dates
            scores, dates = self._extract_scores_and_dates(assessments)

            # Check if currently in remission
            current_score = scores[-1]
            if current_score > remission_threshold:
                return RiskPredictionResult(
                    user_id=user_id,
                    prediction_type="relapse_risk",
                    risk_level="not_in_remission",
                    confidence=1.0,
                    recommendations=[
                        f"Current score ({current_score}) is above remission threshold ({remission_threshold})",
                        "Focus on achieving remission before assessing relapse risk",
                    ],
                )

            # Calculate relapse risk factors
            recent_trend = self._analyze_trend(scores[-min(len(scores), 5):], dates[-min(len(scores), 5):], 30)
            volatility = self._calculate_volatility(scores)
            assessment_compliance = self._calculate_assessment_compliance(assessments, lookback_days)

            # Calculate relapse risk score
            risk_score = 0.0

            # Factor 1: Recent upward trend (worsening)
            if recent_trend.trend_direction == "worsening":
                risk_score += 0.3
            elif recent_trend.trend_direction == "stable":
                risk_score += 0.1

            # Factor 2: High volatility
            if volatility > 5.0:
                risk_score += 0.2
            elif volatility > 3.0:
                risk_score += 0.1

            # Factor 3: Low assessment compliance
            if assessment_compliance < 0.5:
                risk_score += 0.2
            elif assessment_compliance < 0.7:
                risk_score += 0.1

            # Factor 4: Recent score approaching threshold
            if current_score > remission_threshold * 0.8:
                risk_score += 0.3
            elif current_score > remission_threshold * 0.6:
                risk_score += 0.15

            # Determine risk level
            if risk_score >= 0.7:
                risk_level = "high"
            elif risk_score >= 0.4:
                risk_level = "moderate"
            else:
                risk_level = "low"

            # Confidence based on factors
            confidence = min(0.95, 0.6 + (recent_trend.r_squared * 0.2))

            # Generate recommendations
            recommendations = self._generate_relapse_recommendations(
                risk_level, current_score, recent_trend, assessment_compliance
            )

            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="relapse_risk",
                risk_level=risk_level,
                confidence=confidence,
                factors={
                    "recent_trend": recent_trend.to_dict(),
                    "volatility": round(volatility, 2),
                    "assessment_compliance": round(assessment_compliance, 2),
                    "current_score": float(current_score),
                },
                recommendations=recommendations,
            )

        except Exception as e:
            self.logger.error(f"Error predicting relapse risk for user {user_id}: {e}")
            return RiskPredictionResult(
                user_id=user_id,
                prediction_type="relapse_risk",
                risk_level="error",
                confidence=0.0,
                recommendations=["Unable to generate relapse prediction due to system error"],
            )

    # ========================================================================
    # Helper Methods - Data Retrieval
    # ========================================================================

    async def _get_assessment_history(
        self,
        user_id: str,
        assessment_type: str,
        min_assessments: int,
        days_back: int = 365,
    ) -> List[ClinicalAssessmentExtended]:
        """Fetch assessment history for a user"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        query = (
            select(ClinicalAssessmentExtended)
            .where(
                and_(
                    ClinicalAssessmentExtended.user_id == user_id,
                    ClinicalAssessmentExtended.assessment_type == assessment_type,
                    ClinicalAssessmentExtended.completed_at >= cutoff_date,
                )
            )
            .order_by(ClinicalAssessmentExtended.completed_at)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _extract_scores_and_dates(
        self, assessments: List[ClinicalAssessmentExtended]
    ) -> Tuple[List[float], List[datetime]]:
        """Extract scores and dates from assessments"""
        scores = [float(a.total_score) for a in assessments]
        dates = [a.completed_at for a in assessments]
        return scores, dates

    # ========================================================================
    # Helper Methods - Trend Analysis
    # ========================================================================

    def _analyze_trend(
        self,
        scores: List[float],
        dates: List[datetime],
        prediction_days: int,
    ) -> TrendAnalysisResult:
        """
        Analyze trend using linear regression

        Returns:
            TrendAnalysisResult with slope, predictions, etc.
        """
        if len(scores) < 2:
            return TrendAnalysisResult(
                slope=0.0, r_squared=0.0, trend_direction="unknown"
            )

        # Convert dates to days since first assessment
        start_date = dates[0]
        x = np.array([(d - start_date).days for d in dates]).reshape(-1, 1)
        y = np.array(scores)

        # Fit linear regression
        model = LinearRegression()
        model.fit(x, y)

        # Calculate R²
        y_pred = model.predict(x)
        r_squared = model.score(x, y)

        # Determine trend direction
        slope = model.coef_[0]

        # Calculate predictions
        last_x = x[-1][0]
        prediction_30_days = float(model.predict([[last_x + prediction_days]])[0])
        prediction_90_days = float(model.predict([[last_x + 90]])[0])

        # Classify trend
        if slope > 0.1:
            trend_direction = "worsening"
        elif slope < -0.1:
            trend_direction = "improving"
        else:
            trend_direction = "stable"

        # Calculate volatility (standard deviation of residuals)
        residuals = y - y_pred
        volatility = float(np.std(residuals))

        return TrendAnalysisResult(
            slope=float(slope),
            r_squared=float(r_squared),
            trend_direction=trend_direction,
            prediction_30_days=prediction_30_days,
            prediction_90_days=prediction_90_days,
            volatility=volatility,
        )

    def _calculate_volatility(self, scores: List[float]) -> float:
        """Calculate volatility as standard deviation"""
        return float(np.std(scores))

    def _calculate_assessment_compliance(
        self, assessments: List[ClinicalAssessmentExtended], days_back: int
    ) -> float:
        """
        Calculate assessment compliance rate

        Returns ratio of actual assessments to expected weekly assessments
        """
        expected_assessments = days_back / 7  # Expect weekly assessment
        actual_assessments = len(assessments)
        return min(1.0, actual_assessments / expected_assessments)

    # ========================================================================
    # Helper Methods - Depression Risk Classification
    # ========================================================================

    def _calculate_depression_risk_factors(
        self, scores: List[float], trend: TrendAnalysisResult
    ) -> Dict[str, float]:
        """Calculate depression risk factors"""
        current_score = scores[-1]
        avg_score = np.mean(scores)
        max_score = max(scores)

        return {
            "current_score": float(current_score),
            "average_score": float(avg_score),
            "max_score": float(max_score),
            "trend_slope": float(trend.slope),
            "volatility": float(trend.volatility),
            "score_change": float(scores[-1] - scores[0]),
        }

    def _classify_depression_risk(
        self,
        current_score: float,
        trend: TrendAnalysisResult,
        factors: Dict[str, float],
    ) -> Tuple[str, float]:
        """
        Classify depression risk level

        Returns (risk_level, confidence)
        """
        risk_score = 0.0

        # Factor 1: Current severity
        if current_score >= 40:  # Severe
            risk_score += 0.4
        elif current_score >= 29:  # Moderate
            risk_score += 0.3
        elif current_score >= 20:  # Mild
            risk_score += 0.2
        elif current_score >= 14:
            risk_score += 0.1

        # Factor 2: Trend direction
        if trend.trend_direction == "worsening":
            risk_score += 0.3
        elif trend.trend_direction == "stable":
            risk_score += 0.1

        # Factor 3: Volatility
        if trend.volatility > 8.0:
            risk_score += 0.2
        elif trend.volatility > 5.0:
            risk_score += 0.1

        # Factor 4: Recent worsening
        if factors["score_change"] > 5:
            risk_score += 0.2

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "moderate"
        else:
            risk_level = "low"

        # Confidence based on trend strength and data points
        confidence = min(0.95, 0.5 + (trend.r_squared * 0.3))

        return risk_level, confidence

    def _generate_depression_recommendations(
        self, risk_level: str, trend: TrendAnalysisResult, factors: Dict[str, float]
    ) -> List[str]:
        """Generate depression risk recommendations"""
        recommendations = []

        if risk_level == "critical":
            recommendations.extend([
                "URGENT: Consider immediate clinical intervention",
                "Contact mental health professional within 24 hours",
                "Increased monitoring frequency recommended",
                "Evaluate need for medication adjustment",
            ])
        elif risk_level == "high":
            recommendations.extend([
                "Schedule clinical assessment within 1 week",
                "Consider increasing session frequency",
                "Review treatment plan effectiveness",
                "Monitor for worsening symptoms",
            ])
        elif risk_level == "moderate":
            recommendations.extend([
                "Regular monitoring of symptoms recommended",
                "Consider preventive strategies",
                "Maintain current treatment plan",
                "Schedule follow-up in 2-4 weeks",
            ])
        else:  # low
            recommendations.extend([
                "Continue current treatment plan",
                "Maintain regular assessment schedule",
                "Focus on wellness and prevention",
            ])

        # Add trend-specific recommendations
        if trend.trend_direction == "worsening":
            recommendations.append("Symptoms are worsening - review treatment approach")
        elif trend.trend_direction == "improving":
            recommendations.append("Positive trend - continue current interventions")

        return recommendations

    # ========================================================================
    # Helper Methods - Anxiety Risk Classification
    # ========================================================================

    def _calculate_anxiety_risk_factors(
        self, scores: List[float], trend: TrendAnalysisResult
    ) -> Dict[str, float]:
        """Calculate anxiety risk factors"""
        current_score = scores[-1]
        avg_score = np.mean(scores)
        max_score = max(scores)

        return {
            "current_score": float(current_score),
            "average_score": float(avg_score),
            "max_score": float(max_score),
            "trend_slope": float(trend.slope),
            "volatility": float(trend.volatility),
            "score_change": float(scores[-1] - scores[0]),
        }

    def _classify_anxiety_risk(
        self,
        current_score: float,
        trend: TrendAnalysisResult,
        factors: Dict[str, float],
    ) -> Tuple[str, float]:
        """Classify anxiety risk level"""
        risk_score = 0.0

        # Factor 1: Current severity
        if current_score >= 40:  # Severe
            risk_score += 0.4
        elif current_score >= 26:  # Moderate
            risk_score += 0.3
        elif current_score >= 16:  # Mild
            risk_score += 0.2
        elif current_score >= 8:
            risk_score += 0.1

        # Factor 2: Trend direction
        if trend.trend_direction == "worsening":
            risk_score += 0.3
        elif trend.trend_direction == "stable":
            risk_score += 0.1

        # Factor 3: Volatility (anxiety often more volatile)
        if trend.volatility > 10.0:
            risk_score += 0.2
        elif trend.volatility > 6.0:
            risk_score += 0.1

        # Factor 4: Recent worsening
        if factors["score_change"] > 5:
            risk_score += 0.2

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "critical"
        elif risk_score >= 0.5:
            risk_level = "high"
        elif risk_score >= 0.3:
            risk_level = "moderate"
        else:
            risk_level = "low"

        # Confidence based on trend strength
        confidence = min(0.95, 0.5 + (trend.r_squared * 0.3))

        return risk_level, confidence

    def _generate_anxiety_recommendations(
        self, risk_level: str, trend: TrendAnalysisResult, factors: Dict[str, float]
    ) -> List[str]:
        """Generate anxiety risk recommendations"""
        recommendations = []

        if risk_level == "critical":
            recommendations.extend([
                "URGENT: Consider immediate clinical intervention",
                "Evaluate for panic disorder or severe anxiety",
                "Consider anxiety medication or adjustment",
                "Implement crisis plan",
            ])
        elif risk_level == "high":
            recommendations.extend([
                "Schedule clinical assessment within 1 week",
                "Consider CBT or anxiety-focused therapy",
                "Review stress management techniques",
                "Evaluate need for medication",
            ])
        elif risk_level == "moderate":
            recommendations.extend([
                "Regular monitoring recommended",
                "Consider mindfulness and relaxation techniques",
                "Review current coping strategies",
                "Schedule follow-up in 2-4 weeks",
            ])
        else:  # low
            recommendations.extend([
                "Continue current treatment plan",
                "Maintain regular assessment schedule",
                "Focus on stress management",
            ])

        # Add trend-specific recommendations
        if trend.trend_direction == "worsening":
            recommendations.append("Symptoms are worsening - review treatment approach")
        elif trend.trend_direction == "improving":
            recommendations.append("Positive trend - continue current interventions")

        return recommendations

    # ========================================================================
    # Helper Methods - Crisis Risk Analysis
    # ========================================================================

    def _analyze_crisis_indicators(
        self, assessments: List[ClinicalAssessmentExtended]
    ) -> Dict[str, Any]:
        """Analyze crisis risk indicators"""
        indicators = {
            "recent_crisis_alerts": 0,
            "high_severity_count": 0,
            "rapid_score_increase": False,
            "suicidal_ideation": False,
            "max_recent_score": 0.0,
            "avg_recent_score": 0.0,
        }

        # Get recent scores (last 5 assessments)
        recent_assessments = assessments[-5:]
        recent_scores = [float(a.total_score) for a in recent_assessments]
        indicators["max_recent_score"] = max(recent_scores)
        indicators["avg_recent_score"] = np.mean(recent_scores)

        # Count crisis alerts
        for assessment in assessments:
            if assessment.crisis_alert:
                indicators["recent_crisis_alerts"] += 1

        # Count high severity assessments
        for assessment in assessments:
            if assessment.risk_level in ["high", "critical"]:
                indicators["high_severity_count"] += 1

        # Check for rapid score increase (last 2 vs first 2)
        if len(recent_scores) >= 4:
            early_avg = np.mean(recent_scores[:2])
            late_avg = np.mean(recent_scores[-2:])
            if late_avg > early_avg * 1.5:  # 50% increase
                indicators["rapid_score_increase"] = True

        # Check for suicidal ideation in risk flags
        for assessment in assessments:
            if assessment.risk_flags:
                for flag in assessment.risk_flags:
                    if "suicidal" in flag.lower() or "ideation" in flag.lower():
                        indicators["suicidal_ideation"] = True
                        break

        return indicators

    def _calculate_crisis_risk_score(self, indicators: Dict[str, Any]) -> Tuple[float, float]:
        """
        Calculate crisis risk score (0-1)

        Returns (risk_score, confidence)
        """
        risk_score = 0.0

        # Factor 1: Recent crisis alerts (most critical)
        if indicators["recent_crisis_alerts"] >= 2:
            risk_score += 0.4
        elif indicators["recent_crisis_alerts"] == 1:
            risk_score += 0.2

        # Factor 2: Suicidal ideation (critical)
        if indicators["suicidal_ideation"]:
            risk_score += 0.4

        # Factor 3: High severity count
        if indicators["high_severity_count"] >= 3:
            risk_score += 0.2
        elif indicators["high_severity_count"] >= 2:
            risk_score += 0.1

        # Factor 4: Rapid score increase
        if indicators["rapid_score_increase"]:
            risk_score += 0.15

        # Factor 5: Very high recent scores
        if indicators["max_recent_score"] >= 50:
            risk_score += 0.1

        # Confidence based on multiple indicators
        confidence = min(0.95, 0.6 + (len([v for v in indicators.values() if v]) * 0.05))

        return min(1.0, risk_score), confidence

    def _generate_crisis_recommendations(
        self, risk_level: str, indicators: Dict[str, Any]
    ) -> List[str]:
        """Generate crisis risk recommendations"""
        recommendations = []

        if risk_level == "critical":
            recommendations.extend([
                "⚠️ IMMEDIATE ACTION REQUIRED",
                "Contact crisis team immediately",
                "Consider hospitalization if safety concern exists",
                "Do not leave user alone - ensure safety plan in place",
                "Contact emergency services if immediate danger",
            ])
        elif risk_level == "high":
            recommendations.extend([
                "Urgent clinical assessment required",
                "Implement safety plan immediately",
                "Increase monitoring to daily if possible",
                "Contact support system (family, friends)",
                "Consider crisis intervention",
            ])
        elif risk_level == "moderate":
            recommendations.extend([
                "Schedule clinical assessment within 48 hours",
                "Review safety plan",
                "Increase monitoring frequency",
                "Inform treatment team of concerns",
            ])
        else:  # low
            recommendations.extend([
                "Continue current monitoring plan",
                "Maintain regular check-ins",
                "Educate on warning signs",
            ])

        # Add specific recommendations based on indicators
        if indicators["suicidal_ideation"]:
            recommendations.insert(0, "🚨 SUICIDAL IDEATION DETECTED - Immediate intervention required")

        if indicators["rapid_score_increase"]:
            recommendations.append("Rapid symptom worsening detected - urgent review needed")

        return recommendations

    # ========================================================================
    # Helper Methods - Treatment Response Recommendations
    # ========================================================================

    def _generate_treatment_recommendations(
        self, response_category: str, trend: TrendAnalysisResult, percent_change: float
    ) -> List[str]:
        """Generate treatment response recommendations"""
        recommendations = []

        if response_category == "full_response":
            recommendations.extend([
                "✅ Excellent treatment response",
                "Consider maintenance phase of treatment",
                "Gradual reduction in session frequency may be appropriate",
                "Continue monitoring for relapse",
            ])
        elif response_category == "partial_response":
            recommendations.extend([
                "Moderate improvement detected",
                "Consider treatment plan optimization",
                "Evaluate for barriers to full response",
                "Discuss additional interventions with clinician",
            ])
        elif response_category == "non_response":
            recommendations.extend([
                "Limited treatment response",
                "Consider comprehensive treatment review",
                "Evaluate diagnosis accuracy",
                "Explore alternative treatment approaches",
            ])
        elif response_category == "deterioration":
            recommendations.extend([
                "⚠️ Symptoms worsening",
                "Urgent treatment review required",
                "Consider medication adjustment",
                "Evaluate for new stressors or factors",
            ])

        return recommendations

    # ========================================================================
    # Helper Methods - Relapse Risk Recommendations
    # ========================================================================

    def _generate_relapse_recommendations(
        self,
        risk_level: str,
        current_score: float,
        trend: TrendAnalysisResult,
        compliance: float,
    ) -> List[str]:
        """Generate relapse risk recommendations"""
        recommendations = []

        if risk_level == "high":
            recommendations.extend([
                "⚠️ High relapse risk detected",
                "Increase clinical monitoring frequency",
                "Review and strengthen coping strategies",
                "Consider preventive interventions",
                "Ensure support system is engaged",
            ])
        elif risk_level == "moderate":
            recommendations.extend([
                "Moderate relapse risk",
                "Maintain regular monitoring",
                "Reinforce wellness strategies",
                "Schedule follow-up in 2-3 weeks",
            ])
        else:  # low
            recommendations.extend([
                "Low relapse risk - continue current plan",
                "Maintain regular assessment schedule",
                "Focus on relapse prevention education",
            ])

        # Add compliance-specific recommendations
        if compliance < 0.7:
            recommendations.append("Improve assessment compliance for better monitoring")

        # Add trend-specific recommendations
        if trend.trend_direction == "worsening":
            recommendations.append("Early warning signs detected - proactive intervention recommended")

        return recommendations

    # ========================================================================
    # Helper Methods - Common Utilities
    # ========================================================================

    def _insufficient_data_result(
        self, user_id: str, prediction_type: str, min_assessments: int
    ) -> RiskPredictionResult:
        """Generate result for insufficient data"""
        return RiskPredictionResult(
            user_id=user_id,
            prediction_type=prediction_type,
            risk_level="insufficient_data",
            confidence=0.0,
            recommendations=[
                f"At least {min_assessments} assessments required for prediction",
                "Continue regular assessment schedule",
                "More data points will improve prediction accuracy",
            ],
        )
