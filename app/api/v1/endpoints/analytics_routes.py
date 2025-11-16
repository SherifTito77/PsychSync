"""
FastAPI routes for predictive analytics, pattern recognition, and longitudinal analysis.
Complete API endpoints for PsychSync analytics features.

Installation:
    pip install fastapi uvicorn pydantic pandas numpy scikit-learn scipy
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime, date
import pandas as pd
import numpy as np

# Import analytics modules
# In production, adjust these imports based on your project structure
# from ai.predictor import OutcomePredictor, DropoutPredictor, ResponsePredictor
# from ai.pattern_recognition import BehavioralPatternDetector, AnomalyDetector
# from ai.longitudinal_analysis import LongitudinalAnalyzer, TimeSeriesForecaster

# Initialize routers
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ClientFeaturesRequest(BaseModel):
    """Request model for client features."""
    age: int = Field(..., ge=18, le=100)
    gender: str = Field(..., regex="^(male|female|other)$")
    baseline_severity: float = Field(..., ge=0, le=27)
    diagnosis_code: str
    comorbidity_count: int = Field(..., ge=0)
    sessions_attended: int = Field(..., ge=0)
    homework_completion_rate: float = Field(..., ge=0, le=1)
    therapeutic_alliance_score: float = Field(..., ge=1, le=5)
    medication_adherence: float = Field(..., ge=0, le=1)
    current_severity: float = Field(..., ge=0, le=27)
    weeks_in_treatment: int = Field(..., ge=0)
    missed_sessions: int = Field(..., ge=0)
    between_session_contacts: int = Field(..., ge=0)
    crisis_contacts: int = Field(..., ge=0)


class TimeSeriesData(BaseModel):
    """Time series data point."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    score: float = Field(..., ge=0)
    
    @validator('date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class PredictOutcomeRequest(BaseModel):
    """Request for outcome prediction."""
    client_features: ClientFeaturesRequest
    client_id: Optional[str] = None


class PredictDropoutRequest(BaseModel):
    """Request for dropout prediction."""
    client_features: ClientFeaturesRequest
    client_id: str


class TrajectoryAnalysisRequest(BaseModel):
    """Request for trajectory analysis."""
    client_id: str
    time_series: List[TimeSeriesData] = Field(..., min_items=5)
    prediction_periods: int = Field(4, ge=1, le=12)


class PatternDetectionRequest(BaseModel):
    """Request for pattern detection."""
    client_id: str
    time_series: List[TimeSeriesData] = Field(..., min_items=7)
    pattern_type: str = Field("cyclical", regex="^(cyclical|trend|intervention)$")


class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection."""
    client_features: ClientFeaturesRequest
    client_id: str


class InterventionAnalysisRequest(BaseModel):
    """Request for intervention effectiveness analysis."""
    client_id: str
    time_series: List[TimeSeriesData] = Field(..., min_items=10)
    intervention_date: str
    intervention_name: str
    
    @validator('intervention_date')
    def validate_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


# ============================================================================
# Predictive Analytics Endpoints
# ============================================================================

@router.post("/predict/outcome", status_code=status.HTTP_200_OK)
async def predict_outcome(request: PredictOutcomeRequest):
    """
    Predict treatment outcome for a client.
    
    **Returns:**
    - Predicted improvement score
    - Confidence interval
    - Feature importance
    - Confidence level
    
    **Example:**
    ```json
    {
        "client_features": {
            "age": 35,
            "gender": "female",
            "baseline_severity": 18.0,
            ...
        },
        "client_id": "client_123"
    }
    ```
    """
    try:
        # In production, load pre-trained model
        # predictor = OutcomePredictor.load_model('models/outcome_predictor.joblib')
        
        # For demo, return mock prediction
        # Convert request to features object and predict
        
        # Mock response
        predicted_value = request.client_features.baseline_severity - 6.5
        
        response = {
            'client_id': request.client_id,
            'predicted_improvement': max(0, float(predicted_value)),
            'confidence_interval': (
                float(predicted_value - 2.5),
                float(predicted_value + 2.5)
            ),
            'confidence': 0.82,
            'feature_importance': {
                'therapeutic_alliance_score': 0.25,
                'homework_completion_rate': 0.20,
                'baseline_severity': 0.18,
                'sessions_attended': 0.15,
                'medication_adherence': 0.12
            },
            'model_type': 'random_forest',
            'prediction_date': datetime.utcnow().isoformat()
        }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting outcome: {str(e)}"
        )


@router.post("/predict/dropout", status_code=status.HTTP_200_OK)
async def predict_dropout_risk(request: PredictDropoutRequest):
    """
    Predict dropout risk for a client.
    
    **Returns:**
    - Dropout probability (0-1)
    - Risk level (low, moderate, high, very_high)
    - Contributing factors
    
    **Example:**
    ```json
    {
        "client_features": {...},
        "client_id": "client_123"
    }
    ```
    """
    try:
        # Calculate dropout risk based on features
        # Mock calculation
        risk_score = (
            (1 - request.client_features.therapeutic_alliance_score / 5) * 0.4 +
            (1 - request.client_features.homework_completion_rate) * 0.3 +
            (request.client_features.missed_sessions / 10) * 0.3
        )
        
        risk_score = min(max(risk_score, 0), 1)
        
        if risk_score < 0.2:
            risk_level = 'low'
        elif risk_score < 0.5:
            risk_level = 'moderate'
        elif risk_score < 0.7:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        return {
            'client_id': request.client_id,
            'dropout_probability': float(risk_score),
            'risk_level': risk_level,
            'contributing_factors': {
                'low_alliance': request.client_features.therapeutic_alliance_score < 3.5,
                'poor_homework_completion': request.client_features.homework_completion_rate < 0.5,
                'high_missed_sessions': request.client_features.missed_sessions > 2
            },
            'recommendations': [
                'Strengthen therapeutic alliance' if risk_score > 0.3 else None,
                'Address barriers to homework completion' if request.client_features.homework_completion_rate < 0.5 else None,
                'Explore reasons for missed sessions' if request.client_features.missed_sessions > 2 else None
            ],
            'prediction_date': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting dropout risk: {str(e)}"
        )


@router.post("/predict/trajectory", status_code=status.HTTP_200_OK)
async def predict_trajectory(request: ClientFeaturesRequest):
    """
    Predict symptom trajectory for next several weeks.
    
    **Returns:**
    - Weekly predictions with confidence intervals
    - Expected change
    - Engagement score
    """
    try:
        # Simple heuristic prediction
        current = request.current_severity
        baseline = request.baseline_severity
        
        # Calculate rate of change
        if request.weeks_in_treatment > 0:
            weekly_change = (current - baseline) / request.weeks_in_treatment
        else:
            weekly_change = 0
        
        # Adjust based on engagement
        engagement_score = (
            request.homework_completion_rate * 0.3 +
            (request.therapeutic_alliance_score / 5) * 0.4 +
            request.medication_adherence * 0.3
        )
        
        adjusted_change = weekly_change * (0.5 + engagement_score)
        
        # Project forward
        trajectory = []
        for week in range(1, 9):
            predicted = current + (adjusted_change * week)
            predicted = max(0, predicted)
            uncertainty = 0.5 + (week * 0.1)
            
            trajectory.append({
                'week': week,
                'predicted_severity': float(predicted),
                'lower_bound': float(max(0, predicted - uncertainty)),
                'upper_bound': float(min(27, predicted + uncertainty))
            })
        
        return {
            'current_severity': float(current),
            'trajectory': trajectory,
            'expected_change_8_weeks': float(adjusted_change * 8),
            'engagement_score': float(engagement_score),
            'prediction_date': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting trajectory: {str(e)}"
        )


# ============================================================================
# Pattern Recognition Endpoints
# ============================================================================

@router.post("/patterns/detect", status_code=status.HTTP_200_OK)
async def detect_patterns(request: PatternDetectionRequest):
    """
    Detect behavioral patterns in time-series data.
    
    **Supported patterns:**
    - cyclical: Repeating cycles (e.g., weekly mood patterns)
    - trend: Overall improvement or decline
    - intervention: Response to intervention
    
    **Returns:**
    - Pattern type detected
    - Pattern characteristics
    - Confidence level
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame([
            {'date': item.date, 'score': item.score}
            for item in request.time_series
        ])
        
        # Mock pattern detection
        if request.pattern_type == 'cyclical':
            # Simple cyclical detection
            values = df['score'].values
            peaks = []
            for i in range(1, len(values) - 1):
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    peaks.append(i)
            
            if len(peaks) >= 2:
                cycle_lengths = np.diff(peaks)
                avg_cycle = float(np.mean(cycle_lengths))
                
                return {
                    'client_id': request.client_id,
                    'pattern_detected': True,
                    'pattern_type': 'cyclical',
                    'avg_cycle_length_days': avg_cycle,
                    'num_cycles': len(cycle_lengths),
                    'confidence': 0.75,
                    'detected_at': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'client_id': request.client_id,
                    'pattern_detected': False,
                    'reason': 'no_consistent_cycle_found'
                }
        
        elif request.pattern_type == 'trend':
            # Linear trend detection
            from scipy import stats
            values = df['score'].values
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            if p_value < 0.05:
                if slope < -0.1:
                    trend = 'improving'
                elif slope > 0.1:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'stable'
            
            return {
                'client_id': request.client_id,
                'pattern_detected': True,
                'pattern_type': 'trend',
                'trend': trend,
                'slope': float(slope),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'confidence': float(abs(r_value)),
                'detected_at': datetime.utcnow().isoformat()
            }
        
        return {'error': 'Unknown pattern type'}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting patterns: {str(e)}"
        )


@router.post("/anomaly/detect", status_code=status.HTTP_200_OK)
async def detect_anomaly(request: AnomalyDetectionRequest):
    """
    Detect anomalous client behavior that may indicate risk.
    
    **Returns:**
    - Is anomaly detected
    - Anomaly score (0-1, lower = more anomalous)
    - Severity level
    - Detected features
    
    **Use cases:**
    - Sudden deterioration
    - Unexpected disengagement
    - Crisis indicators
    """
    try:
        # Simple rule-based anomaly detection
        features = request.client_features
        
        anomalies = []
        
        # Check for concerning patterns
        if features.current_severity > features.baseline_severity * 1.3:
            anomalies.append('significant_deterioration')
        
        if features.homework_completion_rate < 0.2:
            anomalies.append('very_low_engagement')
        
        if features.therapeutic_alliance_score < 2.5:
            anomalies.append('poor_alliance')
        
        if features.missed_sessions > 3:
            anomalies.append('high_missed_sessions')
        
        if features.crisis_contacts > 2:
            anomalies.append('multiple_crisis_contacts')
        
        is_anomaly = len(anomalies) >= 2
        
        if is_anomaly:
            severity = 'high' if len(anomalies) >= 3 else 'medium'
            anomaly_score = 0.3 if severity == 'high' else 0.5
        else:
            severity = 'low'
            anomaly_score = 0.8
        
        return {
            'client_id': request.client_id,
            'is_anomaly': is_anomaly,
            'anomaly_score': anomaly_score,
            'severity': severity,
            'detected_features': anomalies,
            'recommendations': [
                'Immediate risk assessment' if 'multiple_crisis_contacts' in anomalies else None,
                'Address therapeutic alliance' if 'poor_alliance' in anomalies else None,
                'Increase engagement strategies' if 'very_low_engagement' in anomalies else None,
                'Evaluate treatment approach' if 'significant_deterioration' in anomalies else None
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting anomaly: {str(e)}"
        )


# ============================================================================
# Longitudinal Analysis Endpoints
# ============================================================================

@router.post("/longitudinal/trajectory", status_code=status.HTTP_200_OK)
async def analyze_trajectory(request: TrajectoryAnalysisRequest):
    """
    Analyze growth trajectory and predict future values.
    
    **Returns:**
    - Trajectory type (linear, quadratic, etc.)
    - Baseline and current values
    - Rate of change
    - Future predictions with confidence intervals
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame([
            {'date': item.date, 'score': item.score}
            for item in request.time_series
        ])
        
        # Simple linear trajectory
        from scipy import stats
        df['days'] = (pd.to_datetime(df['date']) - pd.to_datetime(df['date'].iloc[0])).dt.days
        
        X = df['days'].values
        y = df['score'].values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        
        # Generate predictions
        last_date = pd.to_datetime(df['date'].iloc[-1])
        day_interval = X[-1] - X[-2] if len(X) > 1 else 1
        
        predictions = []
        for i in range(1, request.prediction_periods + 1):
            pred_x = X[-1] + (day_interval * i)
            pred_y = slope * pred_x + intercept
            pred_date = last_date + pd.Timedelta(days=int(day_interval * i))
            
            residuals = y - (slope * X + intercept)
            std_error = np.std(residuals)
            
            predictions.append({
                'date': pred_date.strftime('%Y-%m-%d'),
                'predicted_value': float(max(0, pred_y)),
                'confidence_interval': (
                    float(max(0, pred_y - 1.96 * std_error)),
                    float(pred_y + 1.96 * std_error)
                )
            })
        
        return {
            'client_id': request.client_id,
            'trajectory_type': 'linear',
            'baseline_value': float(y[0]),
            'current_value': float(y[-1]),
            'rate_of_change': float(slope),
            'model_fit': float(r_value ** 2),
            'predictions': predictions,
            'interpretation': 'improving' if slope < -0.1 else 'declining' if slope > 0.1 else 'stable'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing trajectory: {str(e)}"
        )


@router.post("/longitudinal/intervention", status_code=status.HTTP_200_OK)
async def analyze_intervention(request: InterventionAnalysisRequest):
    """
    Analyze effectiveness of an intervention.
    
    **Returns:**
    - Mean scores before and after intervention
    - Change magnitude and percentage
    - Statistical significance
    - Effect size (Cohen's d)
    - Interpretation
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame([
            {'date': pd.to_datetime(item.date), 'score': item.score}
            for item in request.time_series
        ])
        
        intervention_date = pd.to_datetime(request.intervention_date)
        
        # Split data
        pre_data = df[df['date'] < intervention_date]['score']
        post_data = df[df['date'] >= intervention_date]['score']
        
        if len(pre_data) < 3 or len(post_data) < 3:
            return {
                'client_id': request.client_id,
                'intervention_name': request.intervention_name,
                'error': 'insufficient_data',
                'pre_samples': len(pre_data),
                'post_samples': len(post_data)
            }
        
        # Calculate statistics
        from scipy import stats
        mean_before = float(pre_data.mean())
        mean_after = float(post_data.mean())
        change = mean_after - mean_before
        percent_change = (change / mean_before * 100) if mean_before != 0 else 0
        
        # T-test
        t_stat, p_value = stats.ttest_ind(pre_data, post_data)
        
        # Effect size
        pooled_std = np.sqrt((pre_data.std()**2 + post_data.std()**2) / 2)
        cohens_d = (mean_before - mean_after) / pooled_std if pooled_std > 0 else 0
        
        # Interpretation
        if p_value >= 0.05:
            interpretation = 'no_significant_effect'
        elif cohens_d > 0.5:
            interpretation = 'large_positive_effect'
        elif cohens_d > 0.2:
            interpretation = 'moderate_positive_effect'
        else:
            interpretation = 'small_positive_effect'
        
        return {
            'client_id': request.client_id,
            'intervention_name': request.intervention_name,
            'start_date': request.intervention_date,
            'mean_before': mean_before,
            'mean_after': mean_after,
            'change': float(change),
            'percent_change': float(percent_change),
            'effect_size': float(cohens_d),
            'p_value': float(p_value),
            'is_significant': bool(p_value < 0.05),
            'interpretation': interpretation
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing intervention: {str(e)}"
        )


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check for analytics service."""
    return {
        'status': 'healthy',
        'service': 'PsychSync Analytics',
        'features': {
            'predictive_analytics': True,
            'pattern_recognition': True,
            'anomaly_detection': True,
            'longitudinal_analysis': True
        },
        'timestamp': datetime.utcnow().isoformat()
    }


# Integration with main FastAPI app
# Add to main.py:
"""
from app.api.routes import analytics_routes

app.include_router(analytics_routes.router)
"""

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(
        title="PsychSync Analytics API",
        description="Advanced analytics for mental health treatment",
        version="1.0.0"
    )
    
    app.include_router(router)
    
    print("Starting Analytics API server...")
    print("API docs: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/api/v1/analytics/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)