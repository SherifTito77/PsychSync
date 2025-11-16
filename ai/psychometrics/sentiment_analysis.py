
# ============================================================================
# FILE 3: ai/psychometrics/sentiment_analysis.py
# Advanced sentiment analysis for psychometric assessments
# ============================================================================

import numpy as np
from typing import Dict, List, Tuple
from textblob import TextBlob
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class PsychometricSentimentAnalyzer:
    """
    Advanced sentiment analysis for psychometric profiling
    Maps sentiment patterns to personality traits
    """
    
    def __init__(self):
        self.personality_mappings = self._load_personality_mappings()
    
    def _load_personality_mappings(self) -> Dict:
        """Load sentiment-to-personality trait mappings"""
        return {
            "big_five": {
                "openness": {
                    "indicators": ["creative", "imaginative", "curious", "novel"],
                    "sentiment_pattern": "varied"  # High variance in sentiment
                },
                "conscientiousness": {
                    "indicators": ["organized", "planned", "structured", "careful"],
                    "sentiment_pattern": "stable"  # Low variance
                },
                "extraversion": {
                    "indicators": ["social", "energetic", "talkative", "outgoing"],
                    "sentiment_pattern": "positive"  # Generally positive
                },
                "agreeableness": {
                    "indicators": ["kind", "cooperative", "helpful", "compassionate"],
                    "sentiment_pattern": "positive_stable"
                },
                "neuroticism": {
                    "indicators": ["anxious", "worried", "stressed", "nervous"],
                    "sentiment_pattern": "negative_variable"
                }
            }
        }
    
    def analyze_personality_from_text(self, texts: List[str]) -> Dict:
        """
        Analyze personality traits from multiple text samples
        
        Args:
            texts: List of text samples from user
            
        Returns:
            Dict with Big Five personality estimates
        """
        if not texts:
            return self._empty_personality_profile()
        
        # Analyze each text
        analyses = [self._analyze_single_text(text) for text in texts]
        
        # Calculate sentiment statistics
        sentiments = [a["sentiment"] for a in analyses]
        sentiment_stats = {
            "mean": np.mean(sentiments),
            "std": np.std(sentiments),
            "min": np.min(sentiments),
            "max": np.max(sentiments)
        }
        
        # Estimate personality traits
        personality = self._estimate_big_five(analyses, sentiment_stats)
        
        return {
            "personality_estimates": personality,
            "sentiment_statistics": sentiment_stats,
            "sample_count": len(texts),
            "confidence": self._calculate_confidence(len(texts))
        }
    
    def _analyze_single_text(self, text: str) -> Dict:
        """Analyze single text sample"""
        blob = TextBlob(text)
        
        return {
            "sentiment": blob.sentiment.polarity,
            "subjectivity": blob.sentiment.subjectivity,
            "word_count": len(text.split()),
            "sentence_count": len(blob.sentences)
        }
    
    def _estimate_big_five(self, analyses: List[Dict], stats: Dict) -> Dict:
        """Estimate Big Five traits from analyses"""
        
        # Openness: Correlates with sentiment variance and subjectivity
        openness = min(1.0, (stats["std"] * 2 + np.mean([a["subjectivity"] for a in analyses])) / 2)
        
        # Conscientiousness: Inverse of sentiment variance
        conscientiousness = max(0.0, 1.0 - (stats["std"] * 1.5))
        
        # Extraversion: Correlates with positive sentiment
        extraversion = (stats["mean"] + 1) / 2  # Normalize -1,1 to 0,1
        
        # Agreeableness: High positive sentiment, low variance
        agreeableness = max(0.0, (stats["mean"] + 1) / 2 - stats["std"] * 0.5)
        
        # Neuroticism: Correlates with negative sentiment and high variance
        neuroticism = max(0.0, (1 - stats["mean"]) / 2 + stats["std"] * 0.5)
        
        return {
            "openness": float(np.clip(openness, 0, 1)),
            "conscientiousness": float(np.clip(conscientiousness, 0, 1)),
            "extraversion": float(np.clip(extraversion, 0, 1)),
            "agreeableness": float(np.clip(agreeableness, 0, 1)),
            "neuroticism": float(np.clip(neuroticism, 0, 1))
        }
    
    def _calculate_confidence(self, sample_count: int) -> float:
        """Calculate confidence based on sample size"""
        # Confidence increases with samples, asymptotes at 0.9
        return min(0.9, 0.3 + (sample_count / 20) * 0.6)
    
    def _empty_personality_profile(self) -> Dict:
        """Return empty profile"""
        return {
            "personality_estimates": {trait: 0.5 for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]},
            "sentiment_statistics": {},
            "sample_count": 0,
            "confidence": 0.0
        }

