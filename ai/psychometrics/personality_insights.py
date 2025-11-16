
# ============================================================================
# FILE 5: /ai/psychometrics/personality_insights.py
# Personality insights from combined data sources
# ============================================================================

from typing import Dict, List
import numpy as np

class PersonalityInsightEngine:
    """Generate comprehensive personality insights"""
    
    def generate_comprehensive_profile(
        self,
        sentiment_data: Dict,
        emotion_data: Dict,
        linguistic_data: Dict
    ) -> Dict:
        """
        Generate comprehensive personality profile
        
        Args:
            sentiment_data: Sentiment analysis results
            emotion_data: Emotion detection results
            linguistic_data: Linguistic feature analysis
            
        Returns:
            Comprehensive personality profile with insights
        """
        # Extract Big Five from sentiment
        big_five = sentiment_data.get("personality_estimates", {})
        
        # Extract emotional patterns
        emotional_state = emotion_data.get("psychological_states", {})
        
        # Generate insights
        insights = self._generate_insights(big_five, emotional_state, linguistic_data)
        
        # Calculate overall wellbeing score
        wellbeing = self._calculate_wellbeing(sentiment_data, emotion_data)
        
        # Identify strengths and areas for growth
        strengths = self._identify_strengths(big_five, emotional_state)
        growth_areas = self._identify_growth_areas(big_five, emotional_state)
        
        return {
            "big_five_profile": big_five,
            "emotional_profile": emotional_state,
            "wellbeing_score": wellbeing,
            "insights": insights,
            "strengths": strengths,
            "growth_areas": growth_areas,
            "confidence_level": sentiment_data.get("confidence", 0.5)
        }
    
    def _generate_insights(self, big_five: Dict, emotional_state: Dict, linguistic: Dict) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Openness insights
        if big_five.get("openness", 0.5) > 0.7:
            insights.append("High creativity and openness to new experiences detected. Consider exploring novel approaches to challenges.")
        elif big_five.get("openness", 0.5) < 0.3:
            insights.append("Preference for familiar approaches detected. May benefit from gradually expanding comfort zone.")
        
        # Conscientiousness insights
        if big_five.get("conscientiousness", 0.5) > 0.7:
            insights.append("Strong organizational skills and attention to detail evident. Natural planner and executor.")
        elif big_five.get("conscientiousness", 0.5) < 0.3:
            insights.append("Flexible and spontaneous approach detected. Consider implementing light structure for important goals.")
        
        # Extraversion insights
        if big_five.get("extraversion", 0.5) > 0.7:
            insights.append("High social energy and enthusiasm. Thrives in collaborative environments.")
        elif big_five.get("extraversion", 0.5) < 0.3:
            insights.append("Reflective and introspective nature. Values deep thinking and focused work.")
        
        # Emotional state insights
        if emotional_state.get("depression_risk", {}).get("risk_level") == "high":
            insights.append("⚠️ Elevated indicators of low mood detected. Consider reaching out to a mental health professional.")
        
        if emotional_state.get("anxiety_risk", {}).get("risk_level") == "high":
            insights.append("⚠️ Anxiety indicators present. Mindfulness and stress management techniques may be beneficial.")
        
        return insights
    
    def _calculate_wellbeing(self, sentiment_data: Dict, emotion_data: Dict) -> Dict:
        """Calculate overall wellbeing score"""
        # Sentiment contribution (40%)
        sentiment_score = (sentiment_data.get("sentiment_statistics", {}).get("mean", 0) + 1) / 2
        
        # Positive emotions contribution (30%)
        emotion_dist = emotion_data.get("emotion_distribution", {})
        positive_score = emotion_dist.get("joy", 0) + emotion_dist.get("surprise", 0) * 0.5
        
        # Stability contribution (30%)
        stability_score = emotion_data.get("emotional_stability", {}).get("score", 0.5)
        
        overall_score = (
            sentiment_score * 0.4 +
            positive_score * 0.3 +
            stability_score * 0.3
        )
        
        level = "excellent" if overall_score >= 0.8 else \
                "good" if overall_score >= 0.6 else \
                "fair" if overall_score >= 0.4 else "needs_attention"
        
        return {
            "score": float(overall_score),
            "level": level,
            "components": {
                "sentiment": float(sentiment_score),
                "positive_emotions": float(positive_score),
                "stability": float(stability_score)
            }
        }
    
    def _identify_strengths(self, big_five: Dict, emotional_state: Dict) -> List[str]:
        """Identify personality strengths"""
        strengths = []
        
        for trait, score in big_five.items():
            if score > 0.7:
                strength_map = {
                    "openness": "Creative thinking and adaptability",
                    "conscientiousness": "Reliability and goal achievement",
                    "extraversion": "Social confidence and communication",
                    "agreeableness": "Empathy and cooperation",
                    "neuroticism": None  # High neuroticism isn't typically a strength
                }
                if trait != "neuroticism" and strength_map[trait]:
                    strengths.append(strength_map[trait])
        
        # Low neuroticism is a strength
        if big_five.get("neuroticism", 0.5) < 0.3:
            strengths.append("Emotional resilience and stress tolerance")
        
        return strengths
    
    def _identify_growth_areas(self, big_five: Dict, emotional_state: Dict) -> List[str]:
        """Identify areas for personal growth"""
        growth_areas = []
        
        # Low scores suggest growth opportunities
        if big_five.get("openness", 0.5) < 0.3:
            growth_areas.append("Exploring new perspectives and experiences")
        
        if big_five.get("conscientiousness", 0.5) < 0.3:
            growth_areas.append("Developing organizational and planning skills")
        
        if big_five.get("agreeableness", 0.5) < 0.3:
            growth_areas.append("Building collaborative relationships")
        
        # High neuroticism suggests growth opportunity
        if big_five.get("neuroticism", 0.5) > 0.7:
            growth_areas.append("Developing emotional regulation strategies")
        
        # Check psychological states
        for state, data in emotional_state.items():
            if isinstance(data, dict) and data.get("risk_level") in ["high", "moderate"]:
                if state == "depression_risk":
                    growth_areas.append("Enhancing mood and emotional positivity")
                elif state == "anxiety_risk":
                    growth_areas.append("Stress management and anxiety reduction")
        
        return growth_areas

