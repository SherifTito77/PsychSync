# ML-Based Anomaly Detection for Security Logs
## Intelligent Threat Detection for PsychSync

**Date:** 2026-03-10
**Version:** 1.0.0
**Priority:** P2 (Medium Priority Enhancement)

---

## Executive Summary

This document provides a comprehensive design for implementing **machine learning-based anomaly detection** for security logs in PsychSync. The solution uses multiple ML approaches to detect previously unknown threats that rule-based systems miss.

### Key Objectives

1. **Zero-Day Threat Detection** - Identify novel attack patterns
2. **Behavioral Analysis** - Detect abnormal user behavior
3. **Time-Series Anomaly Detection** - Identify unusual metric patterns
4. **Ensemble Methods** - Combine multiple algorithms for higher accuracy
5. **False Positive Reduction** - Minimize operational noise
6. **Explainability** - Provide context for detected anomalies

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Log Ingestion Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Security  │  │   API    │  │  Database │  │  Access   │      │
│  │  Logs    │  │   Logs   │  │    Logs   │  │   Logs    │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │             │             │             │               │
│       └─────────────┴─────────────┴─────────────┘               │
└─────────────────────────┼────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Feature Engineering                               │
│                    ┌─────────────┐                                │
│                    │  Feature    │                                │
│                    │  Extractor  │                                │
│                    │             │                                │
│                    │  - Temporal│                                │
│                    │  - Frequency│                                │
│                    │  - Sequence │                                │
│                    │  - Behavioral│                               │
│                    └──────┬──────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                    │                        │
        ▼                    ▼                        ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   Unsupervised     │  │   Supervised       │  │   Time-Series      │
│   Learning        │  │   Learning        │  │   Analysis         │
│                   │  │                   │  │                    │
│  - Isolation       │  │  - Classification │  │  - STL Decompose   │
│  - Clustering      │  │  - Random Forest   │  │  - ARIMA          │
│  - Autoencoder     │  │  - XGBoost        │  │  - Prophet        │
└────────┬──────────┘  └────────┬──────────┘  └────────┬──────────┘
         │                     │                       │
         └─────────────────────┴───────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Ensemble Layer                                   │
│                   ┌─────────────┐                                │
│                   │  Ensemble   │                                │
│                   │  Model      │                                │
│                   │             │                                │
│                   │  - Voting    │                                │
│                   │  - Weighting │                                │
│                   │  - Stacking │                                │
│                   └──────┬──────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Alerting & Response                               │
│                   ┌─────────────┐                                │
│                   │  Alert      │                                │
│                   │  Manager    │                                │
│                   │             │                                │
│                   │  - Scoring   │                                │
│                   │  - Routing  │                                │
│                   │  - Context   │                                │
│                   └──────┬──────┘                                │
└─────────────────────────────────┼──────────────────────────────────────┘
                                 │
                    ┌──────────┴──────────┐
                    │                    │
                    ▼                    ▼
            ┌─────────────┐     ┌─────────────┐
            │   Ops Team  │     │   Security  │
            │   Channel   │     │   Team      │
            └─────────────┘     └─────────────┘
```

---

## Component Specifications

### 1. Feature Engineering Pipeline

**File:** `monitoring/ml_anomaly/feature_extractor.py`

```python
"""
Feature Engineering for Anomaly Detection
Extracts features from security logs for ML models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter


class FeatureExtractor:
    """Extract features from security log events"""

    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes
        self.event_history = defaultdict(list)
        self.user_profiles = defaultdict(dict)
        self.ip_profiles = defaultdict(dict)

    def extract_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all features from a single event

        Returns:
            Dictionary of features for ML model
        """
        features = {}

        # 1. Temporal Features
        features.update(self._extract_temporal_features(event))

        # 2. Frequency Features
        features.update(self._extract_frequency_features(event))

        # 3. Sequence Features
        features.update(self._extract_sequence_features(event))

        # 4. Behavioral Features
        features.update(self._extract_behavioral_features(event))

        # 5. Contextual Features
        features.update(self._extract_contextual_features(event))

        return features

    def _extract_temporal_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract time-based features"""
        features = {}
        timestamp = datetime.fromisoformat(event.get('timestamp', datetime.now().isoformat()))

        features['hour'] = timestamp.hour
        features['day_of_week'] = timestamp.weekday()
        features['is_weekend'] = 1 if timestamp.weekday() >= 5 else 0
        features['is_business_hours'] = 1 if 9 <= timestamp.hour < 17 else 0

        return features

    def _extract_frequency_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract frequency-based features"""
        features = {}

        user_id = event.get('actor_user_id')
        ip_address = event.get('actor_ip_address')
        event_type = event.get('event_type')

        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)

        # Count events in time window
        recent_events = [
            e for e in self.event_history.get('all', [])
            if datetime.fromisoformat(e.get('timestamp', now.isoformat())) > window_start
        ]

        features['events_in_window'] = len(recent_events)

        # User-specific frequency
        if user_id:
            user_events = [
                e for e in recent_events
                if e.get('actor_user_id') == user_id
            ]
            features['user_events_in_window'] = len(user_events)

        # IP-specific frequency
        if ip_address:
            ip_events = [
                e for e in recent_events
                if e.get('actor_ip_address') == ip_address
            ]
            features['ip_events_in_window'] = len(ip_events)

        # Event-type frequency
        if event_type:
            type_events = [
                e for e in recent_events
                if e.get('event_type') == event_type
            ]
            features['event_type_frequency'] = len(type_events) / max(len(recent_events), 1)

        return features

    def _extract_sequence_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract sequence-based features"""
        features = {}

        user_id = event.get('actor_user_id')
        if not user_id:
            return features

        # Get user's recent events
        user_history = [
            e for e in self.event_history.get(user_id, [])[-10:]
        ]

        if len(user_history) < 2:
            return features

        # Calculate time between events
        timestamps = [
            datetime.fromisoformat(e.get('timestamp', datetime.now().isoformat()))
            for e in user_history
        ]

        time_diffs = [
            (timestamps[i+1] - timestamps[i]).total_seconds()
            for i in range(len(timestamps) - 1)
        ]

        features['avg_time_between_events'] = np.mean(time_diffs)
        features['std_time_between_events'] = np.std(time_diffs)
        features['max_time_between_events'] = np.max(time_diffs)
        features['min_time_between_events'] = np.min(time_diffs)

        # Event sequence patterns
        recent_types = [e.get('event_type') for e in user_history[-5:]]
        event_counts = Counter(recent_types)

        features['unique_event_types_in_sequence'] = len(event_counts)
        features['dominant_event_type_ratio'] = max(event_counts.values()) / len(recent_types)

        return features

    def _extract_behavioral_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral features"""
        features = {}

        user_id = event.get('actor_user_id')
        ip_address = event.get('actor_ip_address')
        event_type = event.get('event_type')

        # Update user profile
        if user_id:
            profile = self.user_profiles.get(user_id, {})
            user_events = self.event_history.get(user_id, [])

            # Typical IPs for user
            ips = [e.get('actor_ip_address') for e in user_events]
            ip_counts = Counter(ips)
            typical_ips = [ip for ip, count in ip_counts.most_common(3)]

            features['is_typical_ip'] = 1 if ip_address in typical_ips else 0

            # Typical event types
            types = [e.get('event_type') for e in user_events]
            type_counts = Counter(types)
            typical_types = [t for t, count in type_counts.most_common(5)]

            features['is_typical_event_type'] = 1 if event_type in typical_types else 0

            # Session metrics
            features['total_user_events'] = len(user_events)
            features['user_unique_ips'] = len(set(ips))
            features['user_unique_event_types'] = len(set(types))

            # Success rate
            success_events = [e for e in user_events if e.get('success', True)]
            features['user_success_rate'] = len(success_events) / max(len(user_events), 1)

        # IP profile
        if ip_address:
            ip_events = self.event_history.get(ip_address, [])
            users = [e.get('actor_user_id') for e in ip_events if e.get('actor_user_id')]

            features['ip_unique_users'] = len(set(users))
            features['ip_total_events'] = len(ip_events)

            # Failed login rate for IP
            failed_logins = [
                e for e in ip_events
                if e.get('event_type') == 'auth_login_failure'
            ]
            total_logins = [
                e for e in ip_events
                if 'login' in e.get('event_type', '').lower()
            ]
            features['ip_failure_rate'] = (
                len(failed_logins) / max(len(total_logins), 1)
                if len(total_logins) > 0 else 0
            )

        return features

    def _extract_contextual_features(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract contextual features"""
        features = {}

        # Event characteristics
        features['severity_critical'] = 1 if event.get('severity') == 'CRITICAL' else 0
        features['severity_high'] = 1 if event.get('severity') == 'HIGH' else 0
        features['severity_medium'] = 1 if event.get('severity') == 'MEDIUM' else 0

        # User agent analysis
        user_agent = event.get('actor_user_agent', '')
        features['has_user_agent'] = 1 if user_agent else 0

        if user_agent:
            features['ua_has_bot_string'] = 1 if 'bot' in user_agent.lower() else 0
            features['ua_has_crawler'] = 1 if 'crawler' in user_agent.lower() else 0

        # MFA status
        features['has_mfa'] = 1 if event.get('mfa_verified', False) else 0

        # Risk score from rule-based system
        features['rule_based_risk_score'] = event.get('risk_score', 0)

        # Is anomalous flag from rules
        features['rule_based_is_anomalous'] = 1 if event.get('is_anomalous', False) else 0

        return features

    def update_history(self, event: Dict[str, Any]):
        """Update event history with new event"""
        event_type = event.get('event_type', 'unknown')
        user_id = event.get('actor_user_id')
        ip_address = event.get('actor_ip_address')

        # Update global history
        self.event_history['all'].append(event)
        self.event_history[event_type].append(event)

        if user_id:
            self.event_history[user_id].append(event)

        if ip_address:
            self.event_history[ip_address].append(event)

        # Maintain window size
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)

        for key in list(self.event_history.keys()):
            self.event_history[key] = [
                e for e in self.event_history[key]
                if datetime.fromisoformat(e.get('timestamp', now.isoformat())) > window_start
            ]
```

### 2. Unsupervised Learning Models

**Isolation Forest for Anomaly Detection:**

```python
"""
Isolation Forest Anomaly Detector
Unsupervised learning for detecting outliers in high-dimensional data
"""

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import joblib
import os


class IsolationForestDetector:
    """Isolation Forest-based anomaly detection"""

    def __init__(
        self,
        contamination: float = 0.1,
        n_estimators: int = 100,
        max_samples: int = 256,
        model_path: str = "models/isolation_forest.pkl"
    ):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.model_path = model_path
        self.scaler = StandardScaler()
        self.model = None
        self.is_fitted = False

    def train(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the Isolation Forest model

        Args:
            X: Training features

        Returns:
            Training metrics
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Initialize model
        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            max_samples=self.max_samples,
            random_state=42,
            n_jobs=-1
        )

        # Fit model
        self.model.fit(X_scaled)
        self.is_fitted = True

        # Get predictions for training data
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)

        # Calculate metrics
        anomaly_count = sum(1 for p in predictions if p == -1)
        anomaly_rate = anomaly_count / len(predictions)

        metrics = {
            'total_samples': len(predictions),
            'anomaly_count': anomaly_count,
            'anomaly_rate': anomaly_rate,
            'mean_anomaly_score': scores[predictions == -1].mean() if anomaly_count > 0 else 0,
            'mean_normal_score': scores[predictions == 1].mean()
        }

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies

        Args:
            X: Features to predict

        Returns:
            Array of anomaly scores (-1 for anomaly, 1 for normal)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get anomaly probability

        Args:
            X: Features to predict

        Returns:
            Array of anomaly probabilities (0-1)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        X_scaled = self.scaler.transform(X)
        scores = self.model.score_samples(X_scaled)

        # Convert scores to probabilities (higher is more anomalous)
        # IsolationForest returns negative scores for anomalies
        probabilities = (scores - scores.min()) / (scores.max() - scores.min())
        probabilities = 1 - probabilities  # Invert so higher = more anomalous

        return probabilities

    def explain(self, X: pd.DataFrame, feature_names: List[str]) -> List[Dict[str, Any]]:
        """
        Explain predictions using feature importance

        Args:
            X: Features to explain
            feature_names: Names of features

        Returns:
            List of explanations
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        # Get feature importance from Isolation Forest
        # Note: IsolationForest doesn't have direct feature importance
        # We'll use permutation importance as approximation
        from sklearn.inspection import permutation_importance

        X_scaled = self.scaler.transform(X)
        result = permutation_importance(
            self.model, X_scaled, n_repeats=10, random_state=42, n_jobs=-1
        )

        explanations = []
        for idx, importance in enumerate(result.importances_mean):
            explanations.append({
                'feature': feature_names[idx],
                'importance': importance,
                'std': result.importances_std[idx]
            })

        # Sort by importance
        explanations.sort(key=lambda x: x['importance'], reverse=True)

        return explanations

    def save(self):
        """Save model and scaler"""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Cannot save.")

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'params': {
                'contamination': self.contamination,
                'n_estimators': self.n_estimators,
                'max_samples': self.max_samples
            }
        }

        joblib.dump(model_data, self.model_path)
        print(f"Model saved to {self.model_path}")

    def load(self):
        """Load model and scaler"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.contamination = model_data['params']['contamination']
        self.n_estimators = model_data['params']['n_estimators']
        self.max_samples = model_data['params']['max_samples']
        self.is_fitted = True

        print(f"Model loaded from {self.model_path}")
```

**Autoencoder for Anomaly Detection:**

```python
"""
Autoencoder Anomaly Detector
Deep learning approach for detecting anomalies in complex patterns
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from typing import Dict, Tuple
from sklearn.preprocessing import MinMaxScaler
import os


class Autoencoder(nn.Module):
    """Autoencoder neural network"""

    def __init__(self, input_dim: int, encoding_dim: int = 8):
        super().__init__()

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, encoding_dim),
            nn.ReLU()
        )

        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim),
            nn.Sigmoid()  # Normalize to [0, 1]
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AutoencoderDetector:
    """Autoencoder-based anomaly detection"""

    def __init__(
        self,
        input_dim: int,
        encoding_dim: int = 8,
        learning_rate: float = 0.001,
        batch_size: int = 32,
        epochs: int = 100,
        model_path: str = "models/autoencoder.pth"
    ):
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.model_path = model_path

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.scaler = MinMaxScaler()
        self.model = Autoencoder(input_dim, encoding_dim).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        self.threshold = None
        self.is_fitted = False

    def train(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Train the autoencoder

        Args:
            X: Training features

        Returns:
            Training metrics
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Convert to tensors
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)

        # Create data loader
        dataset = TensorDataset(X_tensor, X_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        # Training loop
        self.model.train()
        losses = []

        for epoch in range(self.epochs):
            epoch_loss = 0
            for batch_x, _ in dataloader:
                self.optimizer.zero_grad()

                # Forward pass
                outputs = self.model(batch_x)
                loss = self.criterion(outputs, batch_x)

                # Backward pass
                loss.backward()
                self.optimizer.step()

                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)

            if epoch % 10 == 0:
                print(f'Epoch [{epoch}/{self.epochs}], Loss: {avg_loss:.6f}')

        # Calculate anomaly threshold based on reconstruction error
        self.model.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_scaled).to(self.device)
            reconstructed = self.model(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1).cpu().numpy()

        # Use 95th percentile as threshold
        self.threshold = np.percentile(reconstruction_errors, 95)
        self.is_fitted = True

        metrics = {
            'final_loss': losses[-1],
            'reconstruction_threshold': self.threshold,
            'mean_reconstruction_error': np.mean(reconstruction_errors),
            'max_reconstruction_error': np.max(reconstruction_errors)
        }

        return metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict anomalies

        Args:
            X: Features to predict

        Returns:
            Array of anomaly flags (1 for anomaly, 0 for normal)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        X_scaled = self.scaler.transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)

        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1).cpu().numpy()

        # Anomaly if reconstruction error > threshold
        anomalies = (reconstruction_errors > self.threshold).astype(int)

        return anomalies

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Get anomaly probability

        Args:
            X: Features to predict

        Returns:
            Array of anomaly probabilities (0-1)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        X_scaled = self.scaler.transform(X)
        X_tensor = torch.FloatTensor(X_scaled).to(self.device)

        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            reconstruction_errors = torch.mean((X_tensor - reconstructed) ** 2, dim=1).cpu().numpy()

        # Normalize to [0, 1]
        probabilities = (reconstruction_errors - reconstruction_errors.min()) / (reconstruction_errors.max() - reconstruction_errors.min())

        return probabilities

    def save(self):
        """Save model"""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Cannot save.")

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler': self.scaler,
            'threshold': self.threshold,
            'params': {
                'input_dim': self.input_dim,
                'encoding_dim': self.encoding_dim,
                'learning_rate': self.learning_rate
            }
        }, self.model_path)

        print(f"Model saved to {self.model_path}")

    def load(self):
        """Load model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        checkpoint = torch.load(self.model_path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.scaler = checkpoint['scaler']
        self.threshold = checkpoint['threshold']
        self.input_dim = checkpoint['params']['input_dim']
        self.encoding_dim = checkpoint['params']['encoding_dim']
        self.is_fitted = True

        print(f"Model loaded from {self.model_path}")
```

### 3. Supervised Learning Models

**XGBoost Classifier:**

```python
"""
XGBoost Anomaly Classifier
Supervised learning using historical anomaly labels
"""

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import numpy as np
import pandas as pd
from typing import Dict, Tuple
import joblib
import os


class XGBoostAnomalyClassifier:
    """XGBoost-based anomaly classification"""

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        scale_pos_weight: float = 10,
        model_path: str = "models/xgboost_anomaly.pkl"
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.scale_pos_weight = scale_pos_weight
        self.model_path = model_path
        self.model = None
        self.feature_importance = None
        self.is_fitted = False

    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train the XGBoost classifier

        Args:
            X: Training features
            y: Training labels (0=normal, 1=anomaly)

        Returns:
            Training metrics
        """
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Initialize model
        self.model = xgb.XGBClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            scale_pos_weight=self.scale_pos_weight,
            objective='binary:logistic',
            eval_metric='auc',
            random_state=42,
            n_jobs=-1
        )

        # Train model
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=10,
            verbose=False
        )

        self.is_fitted = True

        # Get predictions
        y_pred = self.model.predict(X_val)
        y_pred_proba = self.model.predict_proba(X_val)[:, 1]

        # Calculate metrics
        metrics = {
            'accuracy': (y_pred == y_val).mean(),
            'precision': (y_pred[y_val == 1] == 1).mean() if sum(y_val == 1) > 0 else 0,
            'recall': (y_val[y_pred == 1] == 1).mean() if sum(y_pred == 1) > 0 else 0,
            'f1': (2 * (y_pred[y_val == 1] == 1).mean() * (y_val[y_pred == 1] == 1).mean()) /
                    ((y_pred[y_val == 1] == 1).mean() + (y_val[y_pred == 1] == 1).mean())
                    if (y_pred[y_val == 1] == 1).mean() + (y_val[y_pred == 1] == 1).mean() > 0 else 0,
            'auc': roc_auc_score(y_val, y_pred_proba)
        }

        # Feature importance
        self.feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict anomalies

        Args:
            X: Features to predict

        Returns:
            Array of predictions (0=normal, 1=anomaly)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get anomaly probability

        Args:
            X: Features to predict

        Returns:
            Array of probabilities (0-1)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        return self.model.predict_proba(X)[:, 1]

    def explain(self, X: pd.DataFrame, top_n: int = 5) -> Dict[str, Any]:
        """
        Explain predictions using SHAP values

        Args:
            X: Features to explain
            top_n: Number of top features to return

        Returns:
            Explanation dictionary
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")

        import shap

        # Calculate SHAP values
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X)

        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'shap_value': np.abs(shap_values).mean(axis=0)
        }).sort_values('shap_value', ascending=False)

        top_features = feature_importance.head(top_n).to_dict('records')

        return {
            'top_features': top_features,
            'shap_values': shap_values
        }

    def save(self):
        """Save model"""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Cannot save.")

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        model_data = {
            'model': self.model,
            'feature_importance': self.feature_importance,
            'params': {
                'n_estimators': self.n_estimators,
                'max_depth': self.max_depth,
                'learning_rate': self.learning_rate,
                'scale_pos_weight': self.scale_pos_weight
            }
        }

        joblib.dump(model_data, self.model_path)
        print(f"Model saved to {self.model_path}")

    def load(self):
        """Load model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}")

        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.feature_importance = model_data['feature_importance']
        self.n_estimators = model_data['params']['n_estimators']
        self.max_depth = model_data['params']['max_depth']
        self.learning_rate = model_data['params']['learning_rate']
        self.scale_pos_weight = model_data['params']['scale_pos_weight']
        self.is_fitted = True

        print(f"Model loaded from {self.model_path}")
```

### 4. Ensemble Model

```python
"""
Ensemble Anomaly Detector
Combines multiple models for improved accuracy
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import joblib
import os


class EnsembleAnomalyDetector:
    """Ensemble of multiple anomaly detection models"""

    def __init__(
        self,
        models: List,
        weights: List[float] = None,
        voting: str = 'soft',
        model_path: str = "models/ensemble.pkl"
    ):
        self.models = models
        self.weights = weights or [1.0] * len(models)
        self.voting = voting  # 'hard' or 'soft'
        self.model_path = model_path
        self.is_fitted = False

    def train(self, X: pd.DataFrame, y: pd.Series = None) -> Dict[str, Any]:
        """
        Train all models in the ensemble

        Args:
            X: Training features
            y: Training labels (optional, for supervised models)

        Returns:
            Training metrics for all models
        """
        all_metrics = {}

        for i, model in enumerate(self.models):
            print(f"Training model {i+1}/{len(self.models)}...")

            try:
                if hasattr(model, 'train') and y is not None:
                    metrics = model.train(X, y)
                elif hasattr(model, 'train'):
                    metrics = model.train(X)
                else:
                    metrics = {}

                all_metrics[f'model_{i}'] = metrics
            except Exception as e:
                print(f"Error training model {i}: {e}")
                all_metrics[f'model_{i}'] = {'error': str(e)}

        self.is_fitted = True
        return all_metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict using ensemble voting

        Args:
            X: Features to predict

        Returns:
            Array of ensemble predictions
        """
        if not self.is_fitted:
            raise ValueError("Models not fitted. Call train() first.")

        # Get predictions from all models
        all_predictions = []
        all_probabilities = []

        for model in self.models:
            if hasattr(model, 'predict'):
                pred = model.predict(X)
                all_predictions.append(pred)

            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)
                all_probabilities.append(proba)

        # Soft voting (weighted average of probabilities)
        if self.voting == 'soft' and all_probabilities:
            weighted_proba = np.zeros(len(X))
            for proba, weight in zip(all_probabilities, self.weights):
                weighted_proba += proba * weight
            weighted_proba /= sum(self.weights)

            return (weighted_proba > 0.5).astype(int)

        # Hard voting (majority vote)
        if self.voting == 'hard' and all_predictions:
            predictions = np.array(all_predictions)
            # Weighted majority vote
            weighted_votes = np.zeros(len(X))
            for pred, weight in zip(predictions, self.weights):
                weighted_votes += pred * weight
            weighted_votes /= sum(self.weights)

            return (weighted_votes > 0.5).astype(int)

        raise ValueError(f"Voting method '{self.voting}' not supported with available models")

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get ensemble anomaly probability

        Args:
            X: Features to predict

        Returns:
            Array of probabilities (0-1)
        """
        if not self.is_fitted:
            raise ValueError("Models not fitted. Call train() first.")

        all_probabilities = []

        for model in self.models:
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(X)
                all_probabilities.append(proba)

        if not all_probabilities:
            raise ValueError("No models support probability prediction")

        # Weighted average
        weighted_proba = np.zeros(len(X))
        for proba, weight in zip(all_probabilities, self.weights):
            weighted_proba += proba * weight
        weighted_proba /= sum(self.weights)

        return weighted_proba

    def save(self):
        """Save ensemble"""
        if not self.is_fitted:
            raise ValueError("Models not fitted. Cannot save.")

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

        # Save each model
        model_paths = []
        for i, model in enumerate(self.models):
            if hasattr(model, 'save'):
                path = f"{self.model_path}_model_{i}"
                model.save()
                model_paths.append(path)

        # Save ensemble configuration
        ensemble_data = {
            'model_paths': model_paths,
            'weights': self.weights,
            'voting': self.voting
        }

        joblib.dump(ensemble_data, self.model_path)
        print(f"Ensemble saved to {self.model_path}")

    def load(self):
        """Load ensemble"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Ensemble not found at {self.model_path}")

        ensemble_data = joblib.load(self.model_path)
        self.weights = ensemble_data['weights']
        self.voting = ensemble_data['voting']

        # Load each model
        for i, path in enumerate(ensemble_data['model_paths']):
            if os.path.exists(path):
                self.models[i].load()

        self.is_fitted = True
        print(f"Ensemble loaded from {self.model_path}")
```

### 5. Alert Manager

```python
"""
Anomaly Alert Manager
Manages alert generation and routing for detected anomalies
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyAlert:
    """Anomaly alert object"""

    def __init__(
        self,
        alert_id: str,
        event: Dict[str, Any],
        anomaly_score: float,
        models_triggered: List[str],
        explanation: Dict[str, Any],
        severity: AlertSeverity,
        correlation_id: str,
        timestamp: datetime
    ):
        self.alert_id = alert_id
        self.event = event
        self.anomaly_score = anomaly_score
        self.models_triggered = models_triggered
        self.explanation = explanation
        self.severity = severity
        self.correlation_id = correlation_id
        self.timestamp = timestamp
        self.notified_channels = []


class AnomalyAlertManager:
    """Manage anomaly alerts and notifications"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_history = []
        self.alert_cooldown = timedelta(minutes=30)  # Prevent alert spamming

        # Notification channels
        self.notification_channels = self._initialize_channels()

    def _initialize_channels(self) -> Dict[str, Any]:
        """Initialize notification channels"""
        channels = {}

        if self.config.get('slack_webhook'):
            channels['slack'] = {
                'webhook_url': self.config['slack_webhook'],
                'enabled': True
            }

        if self.config.get('email_recipients'):
            channels['email'] = {
                'recipients': self.config['email_recipients'],
                'enabled': True
            }

        if self.config.get('pagerduty_key'):
            channels['pagerduty'] = {
                'integration_key': self.config['pagerduty_key'],
                'enabled': True
            }

        return channels

    async def process_anomaly(
        self,
        event: Dict[str, Any],
        anomaly_score: float,
        models_triggered: List[str],
        explanation: Dict[str, Any],
        correlation_id: str
    ) -> Optional[AnomalyAlert]:
        """
        Process detected anomaly and create alert if needed

        Args:
            event: Original event
            anomaly_score: Anomaly score (0-1)
            models_triggered: Models that detected anomaly
            explanation: Model explanation
            correlation_id: Correlation ID

        Returns:
            Alert object if alert should be sent, None otherwise
        """
        # Determine severity
        severity = self._determine_severity(anomaly_score, event, models_triggered)

        # Check cooldown for similar alerts
        if self._is_on_cooldown(event, severity):
            print(f"Alert on cooldown for event {event.get('event_type')}")
            return None

        # Create alert
        alert = AnomalyAlert(
            alert_id=self._generate_alert_id(),
            event=event,
            anomaly_score=anomaly_score,
            models_triggered=models_triggered,
            explanation=explanation,
            severity=severity,
            correlation_id=correlation_id,
            timestamp=datetime.now()
        )

        # Add to history
        self.alert_history.append(alert)

        # Send notifications
        await self._send_notifications(alert)

        return alert

    def _determine_severity(
        self,
        anomaly_score: float,
        event: Dict[str, Any],
        models_triggered: List[str]
    ) -> AlertSeverity:
        """Determine alert severity"""
        event_severity = event.get('severity', 'LOW')

        # Critical if multiple models agree on anomaly
        if len(models_triggered) >= 2 and anomaly_score > 0.8:
            return AlertSeverity.CRITICAL

        # High if event is already high severity
        if event_severity in ['HIGH', 'CRITICAL']:
            return AlertSeverity.HIGH

        # High if anomaly score is very high
        if anomaly_score > 0.9:
            return AlertSeverity.HIGH

        # Medium for moderate anomalies
        if anomaly_score > 0.7:
            return AlertSeverity.MEDIUM

        return AlertSeverity.LOW

    def _is_on_cooldown(self, event: Dict[str, Any], severity: AlertSeverity) -> bool:
        """Check if similar alert was recently sent"""
        user_id = event.get('actor_user_id')
        event_type = event.get('event_type')

        if not user_id or not event_type:
            return False

        now = datetime.now()
        recent_alerts = [
            a for a in self.alert_history
            if now - a.timestamp < self.alert_cooldown
        ]

        for alert in recent_alerts:
            if (alert.event.get('actor_user_id') == user_id and
                alert.event.get('event_type') == event_type and
                alert.severity == severity):
                return True

        return False

    async def _send_notifications(self, alert: AnomalyAlert):
        """Send alert to all configured channels"""
        tasks = []

        for channel_name, channel in self.notification_channels.items():
            if not channel.get('enabled'):
                continue

            if channel_name == 'slack':
                task = self._send_slack_alert(alert)
            elif channel_name == 'email':
                task = self._send_email_alert(alert)
            elif channel_name == 'pagerduty':
                task = self._send_pagerduty_alert(alert)
            else:
                continue

            tasks.append(task)

        # Send all notifications concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_slack_alert(self, alert: AnomalyAlert):
        """Send alert to Slack"""
        import aiohttp

        webhook_url = self.notification_channels['slack']['webhook_url']

        # Format message
        color = {
            AlertSeverity.LOW: '#36a64f',  # Green
            AlertSeverity.MEDIUM: '#ffaa00',  # Orange
            AlertSeverity.HIGH: '#ff4400',  # Red
            AlertSeverity.CRITICAL: '#880000'  # Dark red
        }[alert.severity]

        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"⚠️ Anomaly Detected: {alert.event.get('event_type', 'Unknown')}",
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Anomaly Score", "value": f"{alert.anomaly_score:.2%}", "short": True},
                        {"title": "User ID", "value": alert.event.get('actor_user_id', 'N/A'), "short": True},
                        {"title": "IP Address", "value": alert.event.get('actor_ip_address', 'N/A'), "short": True},
                        {"title": "Models Triggered", "value": ", ".join(alert.models_triggered), "short": False},
                        {"title": "Correlation ID", "value": alert.correlation_id, "short": False}
                    ],
                    "footer": f"PsychSync Security | {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=message) as response:
                if response.status == 200:
                    alert.notified_channels.append('slack')
                    print(f"Slack alert sent: {alert.alert_id}")
                else:
                    print(f"Failed to send Slack alert: {response.status}")

    async def _send_email_alert(self, alert: AnomalyAlert):
        """Send alert via email"""
        # Implementation would depend on email service
        # This is a placeholder
        print(f"Email alert would be sent: {alert.alert_id}")
        alert.notified_channels.append('email')

    async def _send_pagerDuty_alert(self, alert: AnomalyAlert):
        """Send alert to PagerDuty"""
        # Implementation would use PagerDuty API
        print(f"PagerDuty alert would be sent: {alert.alert_id}")
        alert.notified_channels.append('pagerduty')

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        import uuid
        return f"alert_{uuid.uuid4().hex[:12]}"
```

---

## Implementation Roadmap

### Phase 1: Data Collection & Labeling (Week 1-2)
- [ ] Collect historical security log data
- [ ] Manual labeling of known anomalies
- [ ] Split data into train/validation/test sets
- [ ] Set up feature extraction pipeline

### Phase 2: Model Development (Week 3-4)
- [ ] Implement Isolation Forest detector
- [ ] Implement Autoencoder detector
- [ ] Implement XGBoost classifier
- [ ] Train and validate each model
- [ ] Evaluate model performance

### Phase 3: Ensemble Building (Week 5)
- [ ] Implement ensemble voting mechanism
- [ ] Train ensemble on combined models
- [ ] Tune weights and voting strategy
- [ ] Evaluate ensemble performance vs individual models

### Phase 4: Alert System (Week 6)
- [ ] Implement alert manager
- [ ] Set up notification channels
- [ ] Configure alert severity thresholds
- [ ] Implement cooldown mechanisms
- [ ] Create alert dashboard

### Phase 5: Deployment (Week 7-8)
- [ ] Deploy models to production
- [ ] Set up model retraining pipeline
- [ ] Monitor false positive rate
- [ ] Adjust thresholds based on feedback
- [ ] Document operation procedures

---

## Performance Metrics

### Model Evaluation Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Precision | % of detected anomalies that are real | > 80% |
| Recall | % of real anomalies detected | > 90% |
| F1 Score | Harmonic mean of precision and recall | > 85% |
| AUC-ROC | Area under ROC curve | > 0.90 |
| False Positive Rate | % of normal events flagged as anomalous | < 5% |

### Operational Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Alert Response Time | Time from detection to notification | < 30s |
| False Positive/day | Number of false alerts per day | < 5 |
| Detection Latency | Time from event to anomaly detection | < 5s |
| Model Retraining Time | Time to retrain models | < 1 hour |

---

## Cost Estimate

| Component | Monthly Cost | Notes |
|-----------|--------------|--------|
| GPU Instance (ML training) | $200 | g4dn.xlarge for training |
| CPU Instance (inference) | $100 | m5.large for real-time inference |
| S3 Storage (model artifacts) | $10 | 50GB storage |
| **Total** | **$310/month** | Production estimate |

---

## Security Considerations

1. **Model Security**
   - Encrypt model artifacts at rest
   - Secure model API endpoints
   - Audit model access

2. **Data Privacy**
   - Anonymize features before training
   - Remove PII from training data
   - Comply with data retention policies

3. **Explainability**
   - Provide clear explanations for alerts
   - Log model decision process
   - Enable human review of alerts

4. **Adversarial Protection**
   - Monitor for model poisoning attempts
   - Validate model inputs
   - Regular model integrity checks

---

## Conclusion

Implementing ML-based anomaly detection will significantly enhance PsychSync's security monitoring capabilities by:

- ✅ Detecting zero-day threats not covered by rules
- ✅ Reducing false positives through ensemble methods
- ✅ Providing explainable alerts for faster response
- ✅ Adapting to new attack patterns automatically
- ✅ Enabling proactive rather than reactive security

The estimated implementation time is **8 weeks** with a monthly operational cost of **$310** for production deployment.

---

**Next Steps:**
1. Review design with security team
2. Obtain labeled historical data for training
3. Begin Phase 1: Data Collection & Labeling
4. Set up development environment with GPU support
