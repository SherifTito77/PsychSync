
# ============================================================================
# FILE 7: /ai/pattern_recognition.py  
# Behavioral pattern recognition and anomaly detection
# ============================================================================

from typing import Dict, List, Tuple, Optional
import numpy as np
from scipy import stats, signal
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PatternDetector:
    """Detect behavioral patterns in time-series data"""
    
    def detect_cyclical_patterns(
        self,
        data: List[float],
        timestamps: List[datetime],
        min_cycle_length: int = 3
    ) -> Dict:
        """
        Detect cyclical patterns in behavioral data
        
        Args:
            data: Time-series values (e.g., mood scores)
            timestamps: Corresponding timestamps
            min_cycle_length: Minimum cycle length to detect
            
        Returns:
            Dict with detected cycles and their characteristics
        """
        if len(data) < min_cycle_length * 2:
            return {"cycles_detected": False, "reason": "insufficient_data"}
        
        # Detrend data
        detrended = signal.detrend(data)
        
        # Find peaks and troughs
        peaks, _ = signal.find_peaks(detrended, distance=min_cycle_length)
        troughs, _ = signal.find_peaks(-detrended, distance=min_cycle_length)
        
        if len(peaks) < 2 or len(troughs) < 2:
            return {"cycles_detected": False, "reason": "no_clear_cycles"}
        
        # Calculate cycle characteristics
        peak_intervals = np.diff(peaks)
        avg_cycle_length = float(np.mean(peak_intervals))
        cycle_regularity = 1.0 - (np.std(peak_intervals) / np.mean(peak_intervals)) if np.mean(peak_intervals) > 0 else 0
        
        # Calculate amplitude
        amplitude = float(np.mean([data[p] - data[t] for p, t in zip(peaks[:len(troughs)], troughs[:len(peaks)])]))
        
        return {
            "cycles_detected": True,
            "cycle_count": len(peaks),
            "avg_cycle_length_days": avg_cycle_length,
            "cycle_regularity": float(np.clip(cycle_regularity, 0, 1)),
            "amplitude": amplitude,
            "peaks": peaks.tolist(),
            "troughs": troughs.tolist(),
            "pattern_strength": self._calculate_pattern_strength(detrended)
        }
    
    def analyze_trend(
        self,
        data: List[float],
        timestamps: List[datetime]
    ) -> Dict:
        """
        Analyze trend in time-series data
        
        Args:
            data: Time-series values
            timestamps: Corresponding timestamps
            
        Returns:
            Dict with trend analysis
        """
        if len(data) < 2:
            return {"trend": "insufficient_data"}
        
        # Linear regression
        x = np.arange(len(data))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)
        
        # Determine trend direction
        if p_value < 0.05:  # Statistically significant
            if slope > 0.05:
                direction = "improving"
            elif slope < -0.05:
                direction = "declining"
            else:
                direction = "stable"
        else:
            direction = "stable"
        
        # Calculate trend strength (R-squared)
        trend_strength = float(r_value ** 2)
        
        return {
            "trend_direction": direction,
            "slope": float(slope),
            "trend_strength": trend_strength,
            "p_value": float(p_value),
            "statistically_significant": p_value < 0.05,
            "predicted_change": float(slope * len(data)),
            "interpretation": self._interpret_trend(direction, trend_strength)
        }
    
    def detect_intervention_effect(
        self,
        pre_intervention: List[float],
        post_intervention: List[float]
    ) -> Dict:
        """
        Detect effect of an intervention (e.g., therapy start)
        
        Args:
            pre_intervention: Data before intervention
            post_intervention: Data after intervention
            
        Returns:
            Dict with effect analysis
        """
        if len(pre_intervention) < 3 or len(post_intervention) < 3:
            return {"sufficient_data": False}
        
        # T-test
        t_stat, p_value = stats.ttest_ind(pre_intervention, post_intervention)
        
        # Effect size (Cohen's d)
        cohens_d = self._calculate_cohens_d(pre_intervention, post_intervention)
        
        # Mean difference
        mean_diff = float(np.mean(post_intervention) - np.mean(pre_intervention))
        
        # Determine significance
        significant = p_value < 0.05
        
        return {
            "sufficient_data": True,
            "statistically_significant": significant,
            "p_value": float(p_value),
            "effect_size": float(cohens_d),
            "effect_interpretation": self._interpret_effect_size(cohens_d),
            "mean_difference": mean_diff,
            "improvement_detected": mean_diff > 0 and significant,
            "pre_mean": float(np.mean(pre_intervention)),
            "post_mean": float(np.mean(post_intervention))
        }
    
    def cluster_clients(
        self,
        client_profiles: List[Dict],
        n_clusters: int = 5
    ) -> Dict:
        """
        Cluster clients based on behavioral profiles
        
        Args:
            client_profiles: List of client feature vectors
            n_clusters: Number of clusters
            
        Returns:
            Dict with cluster assignments and characteristics
        """
        if len(client_profiles) < n_clusters:
            return {"error": "insufficient_clients"}
        
        # Extract features
        features = self._extract_clustering_features(client_profiles)
        
        # Normalize
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(features_scaled)
        
        # Analyze clusters
        clusters = {}
        for i in range(n_clusters):
            cluster_members = [j for j, label in enumerate(cluster_labels) if label == i]
            cluster_profiles = [client_profiles[j] for j in cluster_members]
            
            clusters[f"cluster_{i}"] = {
                "size": len(cluster_members),
                "member_ids": cluster_members,
                "characteristics": self._characterize_cluster(cluster_profiles),
                "centroid": kmeans.cluster_centers_[i].tolist()
            }
        
        return {
            "n_clusters": n_clusters,
            "clusters": clusters,
            "silhouette_score": self._calculate_silhouette(features_scaled, cluster_labels)
        }
    
    def _calculate_pattern_strength(self, detrended_data: np.ndarray) -> float:
        """Calculate strength of cyclical pattern"""
        # Use autocorrelation
        autocorr = np.correlate(detrended_data, detrended_data, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr / autocorr[0]  # Normalize
        
        # Find first significant peak after lag 0
        peaks, _ = signal.find_peaks(autocorr[1:], height=0.3)
        
        if len(peaks) > 0:
            return float(autocorr[peaks[0] + 1])
        return 0.0
    
    def _interpret_trend(self, direction: str, strength: float) -> str:
        """Interpret trend analysis"""
        if direction == "stable":
            return "No significant trend detected"
        elif direction == "improving":
            if strength > 0.7:
                return "Strong improvement trend"
            elif strength > 0.4:
                return "Moderate improvement trend"
            else:
                return "Slight improvement trend"
        else:  # declining
            if strength > 0.7:
                return "Strong decline trend - intervention may be needed"
            elif strength > 0.4:
                return "Moderate decline trend"
            else:
                return "Slight decline trend"
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """Calculate Cohen's d effect size"""
        n1, n2 = len(group1), len(group2)
        var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
        pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
        
        if pooled_std == 0:
            return 0.0
        
        return (np.mean(group2) - np.mean(group1)) / pooled_std
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def _extract_clustering_features(self, profiles: List[Dict]) -> np.ndarray:
        """Extract features for clustering"""
        features = []
        for profile in profiles:
            feature_vec = [
                profile.get("avg_sentiment", 0),
                profile.get("sentiment_variance", 0),
                profile.get("session_frequency", 0),
                profile.get("engagement_score", 0),
                profile.get("symptom_severity", 0)
            ]
            features.append(feature_vec)
        return np.array(features)
    
    def _characterize_cluster(self, profiles: List[Dict]) -> Dict:
        """Characterize a cluster"""
        return {
            "avg_sentiment": float(np.mean([p.get("avg_sentiment", 0) for p in profiles])),
            "avg_engagement": float(np.mean([p.get("engagement_score", 0) for p in profiles])),
            "avg_severity": float(np.mean([p.get("symptom_severity", 0) for p in profiles]))
        }
    
    def _calculate_silhouette(self, features: np.ndarray, labels: np.ndarray) -> float:
        """Calculate silhouette score"""
        from sklearn.metrics import silhouette_score
        try:
            return float(silhouette_score(features, labels))
        except:
            return 0.0
          
            
# ============================================================================
# FILE 7 CONTINUED: app/ai/pattern_recognition.py
# Behavioral pattern recognition and anomaly detection (CONTINUED)
# ============================================================================

class AnomalyDetector:
    """Detect anomalous patterns in client behavior"""
    
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
    
    def detect_anomalies(
        self,
        data_points: List[Dict],
        feature_keys: List[str]
    ) -> Dict:
        """
        Detect anomalies in behavioral data
        
        Args:
            data_points: List of data points with features
            feature_keys: Keys to extract as features
            
        Returns:
            Dict with anomaly detection results
        """
        if len(data_points) < 10:
            return {"sufficient_data": False, "reason": "need_at_least_10_points"}
        
        # Extract features
        features = []
        for point in data_points:
            feature_vec = [point.get(key, 0) for key in feature_keys]
            features.append(feature_vec)
        
        features = np.array(features)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Detect anomalies
        predictions = self.model.fit_predict(features_scaled)
        anomaly_scores = self.model.score_samples(features_scaled)
        
        # Identify anomalies (prediction = -1)
        anomaly_indices = [i for i, pred in enumerate(predictions) if pred == -1]
        
        # Analyze anomalies
        anomalies = []
        for idx in anomaly_indices:
            anomalies.append({
                "index": idx,
                "timestamp": data_points[idx].get("timestamp"),
                "anomaly_score": float(anomaly_scores[idx]),
                "severity": self._calculate_severity(anomaly_scores[idx], anomaly_scores),
                "features": {key: data_points[idx].get(key) for key in feature_keys},
                "description": self._describe_anomaly(data_points[idx], feature_keys)
            })
        
        return {
            "sufficient_data": True,
            "total_points": len(data_points),
            "anomalies_detected": len(anomalies),
            "anomaly_rate": len(anomalies) / len(data_points),
            "anomalies": anomalies,
            "risk_level": self._assess_risk_level(len(anomalies), len(data_points))
        }
    
    def detect_sudden_changes(
        self,
        time_series: List[float],
        timestamps: List[datetime],
        threshold: float = 2.0
    ) -> Dict:
        """
        Detect sudden changes in time-series data
        
        Args:
            time_series: Time-series values
            timestamps: Corresponding timestamps
            threshold: Number of standard deviations for change detection
            
        Returns:
            Dict with detected changes
        """
        if len(time_series) < 5:
            return {"sufficient_data": False}
        
        # Calculate differences
        diffs = np.diff(time_series)
        
        # Find outlier changes
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        
        sudden_changes = []
        for i, diff in enumerate(diffs):
            z_score = abs((diff - mean_diff) / std_diff) if std_diff > 0 else 0
            
            if z_score > threshold:
                sudden_changes.append({
                    "index": i + 1,
                    "timestamp": timestamps[i + 1].isoformat(),
                    "change_magnitude": float(diff),
                    "z_score": float(z_score),
                    "direction": "increase" if diff > 0 else "decrease",
                    "severity": "high" if z_score > 3 else "moderate"
                })
        
        return {
            "sufficient_data": True,
            "changes_detected": len(sudden_changes),
            "changes": sudden_changes,
            "mean_change": float(mean_diff),
            "change_volatility": float(std_diff)
        }
    
    def _calculate_severity(self, score: float, all_scores: np.ndarray) -> str:
        """Calculate anomaly severity"""
        percentile = stats.percentileofscore(all_scores, score)
        
        if percentile < 5:
            return "critical"
        elif percentile < 15:
            return "high"
        elif percentile < 30:
            return "moderate"
        else:
            return "low"
    
    def _describe_anomaly(self, data_point: Dict, feature_keys: List[str]) -> str:
        """Generate description of anomaly"""
        # Find which feature(s) are most anomalous
        unusual_features = []
        for key in feature_keys:
            value = data_point.get(key, 0)
            if abs(value) > 2:  # Simple threshold
                unusual_features.append(key)
        
        if unusual_features:
            return f"Unusual patterns in: {', '.join(unusual_features)}"
        return "Anomalous behavioral pattern detected"
    
    def _assess_risk_level(self, anomaly_count: int, total_points: int) -> str:
        """Assess overall risk level"""
        rate = anomaly_count / total_points if total_points > 0 else 0
        
        if rate > 0.3:
            return "high"
        elif rate > 0.15:
            return "moderate"
        else:
            return "low"

