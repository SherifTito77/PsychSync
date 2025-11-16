
# ============================================================================
# FILE 4: ai/psychometrics/emotion_detection.py
# Emotion detection and psychological state analysis
# ============================================================================

from typing import Dict, List
import numpy as np
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class EmotionDetector:
    """Detect and track emotional states over time"""
    
    def __init__(self):
        self.emotion_categories = [
            "joy", "sadness", "anger", "fear", "surprise", "disgust", "neutral"
        ]
        self.psychological_states = self._define_psychological_states()
    
    def _define_psychological_states(self) -> Dict:
        """Define mappings from emotions to psychological states"""
        return {
            "depression_risk": {
                "primary_emotions": ["sadness", "neutral"],
                "secondary_emotions": ["fear", "disgust"],
                "threshold": 0.6
            },
            "anxiety_risk": {
                "primary_emotions": ["fear", "surprise"],
                "secondary_emotions": ["sadness", "anger"],
                "threshold": 0.5
            },
            "stress_indicators": {
                "primary_emotions": ["anger", "fear"],
                "secondary_emotions": ["sadness"],
                "threshold": 0.55
            },
            "positive_wellbeing": {
                "primary_emotions": ["joy"],
                "secondary_emotions": ["surprise"],
                "threshold": 0.6
            }
        }
    
    def analyze_emotional_state(self, emotion_history: List[Dict]) -> Dict:
        """
        Analyze emotional state from history of emotion detections
        
        Args:
            emotion_history: List of emotion detection results over time
            
        Returns:
            Dict with psychological state assessment
        """
        if not emotion_history:
            return self._empty_state()
        
        # Calculate emotion frequencies
        emotion_freq = self._calculate_emotion_frequencies(emotion_history)
        
        # Assess psychological states
        psych_states = self._assess_psychological_states(emotion_freq)
        
        # Calculate emotional stability
        stability = self._calculate_emotional_stability(emotion_history)
        
        # Detect patterns
        patterns = self._detect_emotional_patterns(emotion_history)
        
        return {
            "emotion_distribution": emotion_freq,
            "psychological_states": psych_states,
            "emotional_stability": stability,
            "patterns": patterns,
            "dominant_emotion": max(emotion_freq, key=emotion_freq.get),
            "sample_count": len(emotion_history)
        }
    
    def _calculate_emotion_frequencies(self, history: List[Dict]) -> Dict[str, float]:
        """Calculate normalized emotion frequencies"""
        all_emotions = [h["dominant_emotion"] for h in history]
        counts = Counter(all_emotions)
        total = len(all_emotions)
        
        return {emotion: counts.get(emotion, 0) / total for emotion in self.emotion_categories}
    
    def _assess_psychological_states(self, emotion_freq: Dict[str, float]) -> Dict:
        """Assess psychological state risks"""
        states = {}
        
        for state_name, criteria in self.psychological_states.items():
            # Calculate weighted score
            primary_score = sum(emotion_freq.get(e, 0) for e in criteria["primary_emotions"])
            secondary_score = sum(emotion_freq.get(e, 0) for e in criteria["secondary_emotions"]) * 0.5
            
            total_score = primary_score + secondary_score
            risk_level = "high" if total_score >= criteria["threshold"] else "moderate" if total_score >= criteria["threshold"] * 0.7 else "low"
            
            states[state_name] = {
                "score": float(total_score),
                "risk_level": risk_level,
                "meets_threshold": total_score >= criteria["threshold"]
            }
        
        return states
    
    def _calculate_emotional_stability(self, history: List[Dict]) -> Dict:
        """Calculate emotional stability metrics"""
        if len(history) < 2:
            return {"score": 0.5, "level": "insufficient_data"}
        
        # Calculate emotion change frequency
        changes = 0
        for i in range(1, len(history)):
            if history[i]["dominant_emotion"] != history[i-1]["dominant_emotion"]:
                changes += 1
        
        change_rate = changes / (len(history) - 1)
        
        # Stability score (inverse of change rate)
        stability_score = 1.0 - change_rate
        
        level = "stable" if stability_score >= 0.7 else "moderate" if stability_score >= 0.4 else "unstable"
        
        return {
            "score": float(stability_score),
            "level": level,
            "change_rate": float(change_rate)
        }
    
    def _detect_emotional_patterns(self, history: List[Dict]) -> List[Dict]:
        """Detect recurring emotional patterns"""
        if len(history) < 3:
            return []
        
        patterns = []
        
        # Detect cycling patterns (e.g., joy -> sadness -> joy)
        for i in range(len(history) - 2):
            sequence = [h["dominant_emotion"] for h in history[i:i+3]]
            if sequence[0] == sequence[2] and sequence[0] != sequence[1]:
                patterns.append({
                    "type": "cycling",
                    "emotions": sequence,
                    "position": i
                })
        
        # Detect prolonged states
        current_emotion = history[0]["dominant_emotion"]
        duration = 1
        
        for i in range(1, len(history)):
            if history[i]["dominant_emotion"] == current_emotion:
                duration += 1
            else:
                if duration >= 3:
                    patterns.append({
                        "type": "prolonged",
                        "emotion": current_emotion,
                        "duration": duration
                    })
                current_emotion = history[i]["dominant_emotion"]
                duration = 1
        
        return patterns
    
    def _empty_state(self) -> Dict:
        """Return empty state"""
        return {
            "emotion_distribution": {e: 0.0 for e in self.emotion_categories},
            "psychological_states": {},
            "emotional_stability": {"score": 0.5, "level": "unknown"},
            "patterns": [],
            "dominant_emotion": "neutral",
            "sample_count": 0
        }


