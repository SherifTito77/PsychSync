"""
Predictive Analytics Engine for PsychSync
Machine learning models for predicting treatment outcomes and client progress.

Requirements:
    pip install scikit-learn pandas numpy joblib
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, classification_report, roc_auc_score
from typing import Dict, List, Tuple, Optional
import joblib
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PredictionResult:
    """Structure for prediction results."""
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence: float
    feature_importance: Dict[str, float]
    model_type: str
    prediction_date: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ClientFeatures:
    """Features used for prediction."""
    # Demographics
    age: int
    gender: str  # Will be encoded
    
    # Clinical history
    baseline_severity: float  # Initial assessment score
    diagnosis_code: str
    comorbidity_count: int
    
    # Treatment factors
    sessions_attended: int
    homework_completion_rate: float  # 0-1
    therapeutic_alliance_score: float  # 1-5
    medication_adherence: float  # 0-1
    
    # Recent progress
    current_severity: float
    weeks_in_treatment: int
    missed_sessions: int
    
    # Engagement
    between_session_contacts: int
    crisis_contacts: int
    
    def to_feature_vector(self) -> np.ndarray:
        """Convert to numerical feature vector."""
        # Encode categorical variables
        gender_encoded = 1 if self.gender.lower() == 'male' else 0
        
        features = [
            self.age,
            gender_encoded,
            self.baseline_severity,
            self.comorbidity_count,
            self.sessions_attended,
            self.homework_completion_rate,
            self.therapeutic_alliance_score,
            self.medication_adherence,
            self.current_severity,
            self.weeks_in_treatment,
            self.missed_sessions,
            self.between_session_contacts,
            self.crisis_contacts
        ]
        
        return np.array(features).reshape(1, -1)
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """Get ordered list of feature names."""
        return [
            'age',
            'gender',
            'baseline_severity',
            'comorbidity_count',
            'sessions_attended',
            'homework_completion_rate',
            'therapeutic_alliance_score',
            'medication_adherence',
            'current_severity',
            'weeks_in_treatment',
            'missed_sessions',
            'between_session_contacts',
            'crisis_contacts'
        ]


class OutcomePredictor:
    """
    Predict treatment outcomes and client progress.
    """
    
    def __init__(self, model_type: str = 'linear'):
        """
        Initialize predictor.
        
        Args:
            model_type: Type of model ('linear', 'random_forest', 'gradient_boost')
        """
        self.model_type = model_type
        self.scaler = StandardScaler()
        self.feature_names = ClientFeatures.get_feature_names()
        
        # Initialize model based on type
        if model_type == 'linear':
            self.model = LinearRegression()
        elif model_type == 'random_forest':
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == 'gradient_boost':
            self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.is_trained = False
        self.training_metrics = {}
    
    def train(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Dict:
        """
        Train the prediction model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target values (n_samples,)
            test_size: Proportion of data for testing
            
        Returns:
            Dictionary of training metrics
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        self.training_metrics = {
            'train_r2': r2_score(y_train, train_pred),
            'test_r2': r2_score(y_test, test_pred),
            'train_rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
            'train_mae': np.mean(np.abs(y_train - train_pred)),
            'test_mae': np.mean(np.abs(y_test - test_pred)),
            'n_samples': len(X),
            'n_features': X.shape[1],
            'model_type': self.model_type
        }
        
        # Cross-validation
        cv_scores = cross_val_score(
            self.model, X_train_scaled, y_train, cv=5, scoring='r2'
        )
        self.training_metrics['cv_r2_mean'] = cv_scores.mean()
        self.training_metrics['cv_r2_std'] = cv_scores.std()
        
        self.is_trained = True
        
        return self.training_metrics
    
    def predict_outcome(self, features: ClientFeatures) -> PredictionResult:
        """
        Predict treatment outcome for a client.
        
        Args:
            features: Client features
            
        Returns:
            PredictionResult with prediction and confidence
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before making predictions")
        
        # Convert features to vector
        X = features.to_feature_vector()
        X_scaled = self.scaler.transform(X)
        
        # Make prediction
        prediction = self.model.predict(X_scaled)[0]
        
        # Calculate confidence interval (simple approach using training RMSE)
        rmse = self.training_metrics.get('test_rmse', 1.0)
        ci_lower = prediction - 1.96 * rmse
        ci_upper = prediction + 1.96 * rmse
        
        # Calculate confidence score (inverse of uncertainty)
        confidence = 1 / (1 + rmse)
        
        # Get feature importance
        feature_importance = self._get_feature_importance()
        
        return PredictionResult(
            predicted_value=float(prediction),
            confidence_interval=(float(ci_lower), float(ci_upper)),
            confidence=float(confidence),
            feature_importance=feature_importance,
            model_type=self.model_type,
            prediction_date=datetime.utcnow().isoformat()
        )
    
    def predict_batch(self, features_list: List[ClientFeatures]) -> List[PredictionResult]:
        """Predict outcomes for multiple clients."""
        return [self.predict_outcome(f) for f in features_list]
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores."""
        if hasattr(self.model, 'feature_importances_'):
            # Random Forest, Gradient Boosting
            importances = self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            # Linear models
            importances = np.abs(self.model.coef_)
        else:
            return {}
        
        # Normalize to sum to 1
        importances = importances / importances.sum()
        
        return {
            name: float(imp)
            for name, imp in zip(self.feature_names, importances)
        }
    
    def save_model(self, filepath: str):
        """Save trained model to disk."""
        if not self.is_trained:
            raise RuntimeError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'training_metrics': self.training_metrics,
            'trained_at': datetime.utcnow().isoformat()
        }
        
        joblib.dump(model_data, filepath)
    
    @classmethod
    def load_model(cls, filepath: str) -> 'OutcomePredictor':
        """Load trained model from disk."""
        model_data = joblib.load(filepath)
        
        predictor = cls(model_type=model_data['model_type'])
        predictor.model = model_data['model']
        predictor.scaler = model_data['scaler']
        predictor.feature_names = model_data['feature_names']
        predictor.training_metrics = model_data['training_metrics']
        predictor.is_trained = True
        
        return predictor


class DropoutPredictor:
    """
    Predict likelihood of client dropping out of treatment.
    Binary classification model.
    """
    
    def __init__(self):
        """Initialize dropout predictor."""
        self.model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.feature_names = ClientFeatures.get_feature_names()
        self.is_trained = False
        self.training_metrics = {}
    
    def train(self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Dict:
        """
        Train dropout prediction model.
        
        Args:
            X: Feature matrix
            y: Binary labels (0=completed, 1=dropped out)
            test_size: Proportion for testing
            
        Returns:
            Training metrics
        """
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model.fit(X_train_scaled, y_train)
        
        # Predictions
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        train_proba = self.model.predict_proba(X_train_scaled)[:, 1]
        test_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Metrics
        self.training_metrics = {
            'train_accuracy': np.mean(train_pred == y_train),
            'test_accuracy': np.mean(test_pred == y_test),
            'train_auc': roc_auc_score(y_train, train_proba),
            'test_auc': roc_auc_score(y_test, test_proba),
            'classification_report': classification_report(y_test, test_pred, output_dict=True),
            'n_samples': len(X),
            'dropout_rate': y.mean()
        }
        
        self.is_trained = True
        return self.training_metrics
    
    def predict_dropout_risk(self, features: ClientFeatures) -> Dict:
        """
        Predict dropout risk for a client.
        
        Returns:
            Dictionary with dropout probability and risk level
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained first")
        
        X = features.to_feature_vector()
        X_scaled = self.scaler.transform(X)
        
        # Probability of dropout
        dropout_prob = self.model.predict_proba(X_scaled)[0, 1]
        
        # Risk categorization
        if dropout_prob < 0.2:
            risk_level = 'low'
        elif dropout_prob < 0.5:
            risk_level = 'moderate'
        elif dropout_prob < 0.7:
            risk_level = 'high'
        else:
            risk_level = 'very_high'
        
        # Get feature importance
        feature_importance = {}
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            importances = importances / importances.sum()
            feature_importance = {
                name: float(imp)
                for name, imp in zip(self.feature_names, importances)
            }
        
        return {
            'dropout_probability': float(dropout_prob),
            'risk_level': risk_level,
            'feature_importance': feature_importance,
            'prediction_date': datetime.utcnow().isoformat()
        }


class ResponsePredictor:
    """
    Predict treatment response trajectory (will client improve?).
    """
    
    def __init__(self):
        """Initialize response predictor."""
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def predict_response_trajectory(
        self,
        features: ClientFeatures,
        weeks_ahead: int = 4
    ) -> Dict:
        """
        Predict symptom severity trajectory.
        
        Args:
            features: Current client features
            weeks_ahead: How many weeks to predict ahead
            
        Returns:
            Predicted trajectory with confidence bands
        """
        if not self.is_trained:
            # Use simple heuristic if not trained
            return self._heuristic_prediction(features, weeks_ahead)
        
        # For now, use simple heuristic
        # In production, would use trained time-series model
        return self._heuristic_prediction(features, weeks_ahead)
    
    def _heuristic_prediction(self, features: ClientFeatures, weeks_ahead: int) -> Dict:
        """Simple heuristic-based prediction."""
        current = features.current_severity
        baseline = features.baseline_severity
        
        # Calculate rate of change
        if features.weeks_in_treatment > 0:
            weekly_change = (current - baseline) / features.weeks_in_treatment
        else:
            weekly_change = 0
        
        # Adjust based on engagement factors
        engagement_score = (
            features.homework_completion_rate * 0.3 +
            (features.therapeutic_alliance_score / 5) * 0.4 +
            features.medication_adherence * 0.3
        )
        
        # Better engagement = faster improvement
        adjusted_change = weekly_change * (0.5 + engagement_score)
        
        # Project forward
        trajectory = []
        for week in range(1, weeks_ahead + 1):
            predicted = current + (adjusted_change * week)
            
            # Add some diminishing returns (floor effect)
            predicted = max(0, predicted)
            
            # Add uncertainty (increases with time)
            uncertainty = 0.5 + (week * 0.1)
            
            trajectory.append({
                'week': week,
                'predicted_severity': float(predicted),
                'lower_bound': float(max(0, predicted - uncertainty)),
                'upper_bound': float(min(baseline * 1.5, predicted + uncertainty))
            })
        
        return {
            'current_severity': float(current),
            'trajectory': trajectory,
            'expected_change': float(adjusted_change * weeks_ahead),
            'engagement_score': float(engagement_score)
        }


# Utility functions for generating synthetic training data
def generate_synthetic_training_data(n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data for demonstration.
    In production, use real clinical data.
    """
    np.random.seed(42)
    
    # Features
    age = np.random.randint(18, 75, n_samples)
    gender = np.random.randint(0, 2, n_samples)
    baseline_severity = np.random.uniform(10, 25, n_samples)
    comorbidity = np.random.randint(0, 4, n_samples)
    sessions = np.random.randint(1, 20, n_samples)
    homework_rate = np.random.uniform(0, 1, n_samples)
    alliance = np.random.uniform(2, 5, n_samples)
    medication = np.random.uniform(0, 1, n_samples)
    weeks = np.random.randint(1, 24, n_samples)
    missed = np.random.randint(0, 5, n_samples)
    contacts = np.random.randint(0, 10, n_samples)
    crisis = np.random.randint(0, 3, n_samples)
    
    # Current severity (outcome to predict)
    # Simulated relationship with features
    current_severity = (
        baseline_severity * 0.6 +
        -sessions * 0.3 +
        -homework_rate * 3 +
        -alliance * 1.5 +
        -medication * 2 +
        comorbidity * 1.2 +
        missed * 0.5 +
        np.random.normal(0, 2, n_samples)  # Noise
    )
    
    # Clip to realistic range
    current_severity = np.clip(current_severity, 0, 27)
    
    # Assemble feature matrix
    X = np.column_stack([
        age, gender, baseline_severity, comorbidity,
        sessions, homework_rate, alliance, medication,
        current_severity, weeks, missed, contacts, crisis
    ])
    
    # Target: improvement from baseline
    y = baseline_severity - current_severity
    
    return X, y


# Example usage
if __name__ == "__main__":
    print("PsychSync Predictive Analytics Demo")
    print("=" * 60)
    
    # Generate synthetic training data
    print("\n1. Generating synthetic training data...")
    X_train, y_train = generate_synthetic_training_data(n_samples=800)
    print(f"   Generated {len(X_train)} training samples")
    
    # Train outcome predictor
    print("\n2. Training outcome prediction model...")
    predictor = OutcomePredictor(model_type='random_forest')
    metrics = predictor.train(X_train, y_train)
    
    print(f"   Train R²: {metrics['train_r2']:.3f}")
    print(f"   Test R²: {metrics['test_r2']:.3f}")
    print(f"   Test RMSE: {metrics['test_rmse']:.3f}")
    print(f"   CV R² (mean ± std): {metrics['cv_r2_mean']:.3f} ± {metrics['cv_r2_std']:.3f}")
    
    # Make prediction for sample client
    print("\n3. Making prediction for sample client...")
    sample_client = ClientFeatures(
        age=35,
        gender='female',
        baseline_severity=18.0,
        diagnosis_code='F32.1',
        comorbidity_count=1,
        sessions_attended=8,
        homework_completion_rate=0.75,
        therapeutic_alliance_score=4.2,
        medication_adherence=0.9,
        current_severity=12.0,
        weeks_in_treatment=8,
        missed_sessions=1,
        between_session_contacts=3,
        crisis_contacts=0
    )
    
    result = predictor.predict_outcome(sample_client)
    print(f"   Predicted improvement: {result.predicted_value:.2f} points")
    print(f"   95% CI: ({result.confidence_interval[0]:.2f}, {result.confidence_interval[1]:.2f})")
    print(f"   Confidence: {result.confidence:.3f}")
    
    print("\n   Top 5 Most Important Features:")
    sorted_features = sorted(
        result.feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )
    for feature, importance in sorted_features[:5]:
        print(f"      {feature}: {importance:.3f}")
    
    # Trajectory prediction
    print("\n4. Predicting response trajectory...")
    response_predictor = ResponsePredictor()
    trajectory = response_predictor.predict_response_trajectory(
        sample_client,
        weeks_ahead=8
    )
    
    print(f"   Current severity: {trajectory['current_severity']:.1f}")
    print(f"   Expected change (8 weeks): {trajectory['expected_change']:.1f}")
    print(f"   Engagement score: {trajectory['engagement_score']:.2f}")
    print(f"\n   Projected trajectory:")
    for point in trajectory['trajectory'][:4]:  # Show first 4 weeks
        print(f"      Week {point['week']}: {point['predicted_severity']:.1f} "
              f"(±{point['upper_bound'] - point['predicted_severity']:.1f})")
    
    # Save model
    print("\n5. Saving trained model...")
    predictor.save_model('outcome_predictor.joblib')
    print("   Model saved to 'outcome_predictor.joblib'")
    
    print("\n" + "=" * 60)
    print("Demo complete!")