
# ============================================================================
# FILE 9: app/services/psychometric_service.py
# Integrated psychometric service layer
# ============================================================================

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from ai.psychometrics.sentiment_analysis import PsychometricSentimentAnalyzer
from ai.psychometrics.emotion_detection import EmotionDetector
from ai.psychometrics.personality_insights import PersonalityInsightEngine
from ai.psychometrics.psychometric_scorer import PsychometricScorer
from ai.pattern_recognition import PatternDetector, AnomalyDetector
from app.services.nlp_service import NLPService

logger = logging.getLogger(__name__)

class PsychometricService:
    """
    Integrated service for all psychometric analysis
    Combines NLP, sentiment analysis, pattern detection, etc.
    """
    
    def __init__(self):
        self.nlp_service = NLPService()
        self.sentiment_analyzer = PsychometricSentimentAnalyzer()
        self.emotion_detector = EmotionDetector()
        self.personality_engine = PersonalityInsightEngine()
        self.scorer = PsychometricScorer()
        self.pattern_detector = PatternDetector()
        self.anomaly_detector = AnomalyDetector()
    
    async def analyze_client_session(
        self,
        session_text: str,
        client_id: str,
        session_id: str,
        session_date: datetime
    ) -> Dict:
        """
        Comprehensive analysis of a therapy/coaching session
        
        Args:
            session_text: Transcript or notes from session
            client_id: Client identifier
            session_id: Session identifier
            session_date: Date of session
            
        Returns:
            Comprehensive analysis results
        """
        try:
            # NLP analysis
            nlp_results = self.nlp_service.analyze_text(session_text)
            
            # Extract sentiment and emotion
            sentiment = nlp_results["sentiment"]
            emotions = nlp_results["emotions"]
            
            # Psycholinguistic markers
            psycho_markers = nlp_results["psycholinguistic_markers"]
            
            # Package results
            analysis = {
                "client_id": client_id,
                "session_id": session_id,
                "session_date": session_date.isoformat(),
                "sentiment_analysis": sentiment,
                "emotion_analysis": emotions,
                "psycholinguistic_markers": psycho_markers,
                "linguistic_features": nlp_results["linguistic_features"],
                "key_insights": self._generate_session_insights(
                    sentiment, emotions, psycho_markers
                ),
                "red_flags": self._identify_red_flags(
                    sentiment, emotions, psycho_markers
                ),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Session analysis failed: {e}")
            raise
    
    async def generate_client_progress_report(
        self,
        client_id: str,
        session_analyses: List[Dict],
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Generate comprehensive progress report for a client
        
        Args:
            client_id: Client identifier
            session_analyses: List of previous session analyses
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Comprehensive progress report
        """
        try:
            # Extract time-series data
            sentiment_scores = [s["sentiment_analysis"]["overall_score"] for s in session_analyses]
            timestamps = [datetime.fromisoformat(s["session_date"]) for s in session_analyses]
            
            # Trend analysis
            trend = self.pattern_detector.analyze_trend(sentiment_scores, timestamps)
            
            # Cyclical patterns
            cycles = self.pattern_detector.detect_cyclical_patterns(
                sentiment_scores, timestamps
            )
            
            # Emotion patterns
            emotion_history = [s["emotion_analysis"] for s in session_analyses]
            emotional_state = self.emotion_detector.analyze_emotional_state(emotion_history)
            
            # Anomaly detection
            data_points = [
                {
                    "timestamp": s["session_date"],
                    "sentiment": s["sentiment_analysis"]["overall_score"],
                    "dominant_emotion": s["emotion_analysis"]["dominant_emotion"]
                }
                for s in session_analyses
            ]
            anomalies = self.anomaly_detector.detect_anomalies(
                data_points,
                ["sentiment"]
            )
            
            # Overall assessment
            progress_level = self._assess_progress_level(trend, emotional_state)
            
            report = {
                "client_id": client_id,
                "report_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "session_count": len(session_analyses),
                "trend_analysis": trend,
                "cyclical_patterns": cycles,
                "emotional_state": emotional_state,
                "anomalies": anomalies,
                "progress_level": progress_level,
                "recommendations": self._generate_recommendations(
                    trend, emotional_state, anomalies
                ),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Progress report generation failed: {e}")
            raise
    
    async def score_and_interpret_assessment(
        self,
        assessment_type: str,
        responses: List[Dict],
        client_id: str
    ) -> Dict:
        """
        Score assessment and provide interpretation
        
        Args:
            assessment_type: Type of assessment
            responses: Assessment responses
            client_id: Client identifier
            
        Returns:
            Scored results with interpretation
        """
        try:
            # Get framework config (would typically come from database)
            framework_config = self._get_framework_config(assessment_type)
            
            # Score assessment
            scores = self.scorer.score_assessment(
                assessment_type,
                responses,
                framework_config
            )
            
            # Add client info
            scores["client_id"] = client_id
            scores["completed_at"] = datetime.utcnow().isoformat()
            
            # Generate insights
            scores["insights"] = self._generate_assessment_insights(
                assessment_type,
                scores
            )
            
            return scores
            
        except Exception as e:
            logger.error(f"Assessment scoring failed: {e}")
            raise
    
    def _generate_session_insights(
        self,
        sentiment: Dict,
        emotions: Dict,
        psycho_markers: Dict
    ) -> List[str]:
        """Generate insights from session analysis"""
        insights = []
        
        # Sentiment insights
        if sentiment["overall_score"] < -0.5:
            insights.append("Session showed predominantly negative sentiment")
        elif sentiment["overall_score"] > 0.5:
            insights.append("Session showed predominantly positive sentiment")
        
        # Emotion insights
        dominant_emotion = emotions["dominant_emotion"]
        if dominant_emotion in ["sadness", "fear", "anger"]:
            insights.append(f"Primary emotion: {dominant_emotion} - may require attention")
        
        # First-person pronoun usage
        first_person = psycho_markers.get("first_person", {})
        if first_person.get("percentage", 0) > 10:
            insights.append("High self-focus detected")
        
        return insights
    
    def _identify_red_flags(
        self,
        sentiment: Dict,
        emotions: Dict,
        psycho_markers: Dict
    ) -> List[Dict]:
        """Identify potential red flags"""
        red_flags = []
        
        # Severe negative sentiment
        if sentiment["overall_score"] < -0.7:
            red_flags.append({
                "severity": "high",
                "type": "extreme_negative_sentiment",
                "description": "Extremely negative sentiment detected"
            })
        
        # High anxiety markers
        anxiety_markers = psycho_markers.get("anxiety", {})
        if anxiety_markers.get("percentage", 0) > 5:
            red_flags.append({
                "severity": "moderate",
                "type": "anxiety_indicators",
                "description": "Elevated anxiety language detected"
            })
        
        # Sustained negative emotions
        if emotions["dominant_emotion"] in ["sadness", "fear"] and \
           emotions["dominant_confidence"] > 0.8:
            red_flags.append({
                "severity": "moderate",
                "type": "persistent_negative_emotion",
                "description": f"Strong {emotions['dominant_emotion']} detected"
            })
        
        return red_flags
    
    def _assess_progress_level(
        self,
        trend: Dict,
        emotional_state: Dict
    ) -> str:
        """Assess overall progress level"""
        if trend["trend_direction"] == "improving" and \
           trend["trend_strength"] > 0.5:
            return "strong_improvement"
        elif trend["trend_direction"] == "improving":
            return "moderate_improvement"
        elif trend["trend_direction"] == "declining":
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendations(
        self,
        trend: Dict,
        emotional_state: Dict,
        anomalies: Dict
    ) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = []
        
        # Trend-based recommendations
        if trend["trend_direction"] == "declining":
            recommendations.append(
                "Consider adjusting treatment plan - declining trend detected"
            )
        
        # Emotional state recommendations
        psych_states = emotional_state.get("psychological_states", {})
        if psych_states.get("depression_risk", {}).get("risk_level") == "high":
            recommendations.append(
                "Screen for depression - elevated risk indicators present"
            )
        
        if psych_states.get("anxiety_risk", {}).get("risk_level") == "high":
            recommendations.append(
                "Implement anxiety management interventions"
            )
        
        # Anomaly-based recommendations
        if anomalies.get("anomaly_rate", 0) > 0.2:
            recommendations.append(
                "High volatility detected - increase session frequency"
            )
        
        return recommendations if recommendations else [
            "Continue current treatment approach"
        ]
    
    def _generate_assessment_insights(
        self,
        assessment_type: str,
        scores: Dict
    ) -> List[str]:
        """Generate insights from assessment scores"""
        insights = []
        
        if assessment_type == "big_five":
            dimensions = scores.get("dimensions", {})
            
            for dim, data in dimensions.items():
                if data["score"] > 0.7:
                    insights.append(
                        f"High {dim}: {data['interpretation']}"
                    )
                elif data["score"] < 0.3:
                    insights.append(
                        f"Low {dim}: {data['interpretation']}"
                    )
        
        elif assessment_type == "mbti":
            insights.append(
                f"Type: {scores['type']} - {scores['description']}"
            )
        
        elif assessment_type == "enneagram":
            insights.append(
                f"Type {scores['primary_type']} with {scores['wing']} wing"
            )
        
        return insights
    
    def _get_framework_config(self, assessment_type: str) -> Dict:
        """Get framework configuration (simplified)"""
        configs = {
            "big_five": {
                "min_value": 1,
                "max_value": 5,
                "questions": {},  # Would be populated from database
                "required_questions": []
            },
            "mbti": {
                "min_value": 1,
                "max_value": 5,
                "questions": {},
                "required_questions": []
            },
            "enneagram": {
                "min_value": 1,
                "max_value": 5,
                "questions": {},
                "required_questions": []
            },
            "disc": {
                "min_value": 1,
                "max_value": 4,
                "questions": {},
                "required_questions": []
            }
        }
        
        return configs.get(assessment_type, {})