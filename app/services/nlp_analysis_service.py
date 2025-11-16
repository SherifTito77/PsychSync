# app/services/nlp_analysis_service.py
"""
NLP Analysis Service for Email-Based Behavioral Analysis
Privacy-first analysis that works with metadata-only approach
"""

import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import hashlib
import logging
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import DBSCAN
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
from collections import defaultdict, Counter

from app.db.models.email_metadata import EmailMetadata
from app.db.models.communication_analysis import CommunicationAnalysis
from app.db.models.communication_patterns import CommunicationPatterns
from app.db.models.user import User
from app.core.config import settings
from app.core.logging_config import logger

@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    score: float  # -1 to 1 (negative to positive)
    confidence: float  # 0 to 1
    label: str  # 'positive', 'negative', 'neutral'

@dataclass
class EmotionResult:
    """Emotion analysis result"""
    emotions: Dict[str, float]  # emotion name -> score
    dominant_emotion: str
    emotional_intensity: float

@dataclass
class BehavioralIndicators:
    """Behavioral pattern indicators"""
    communication_style: str  # 'assertive', 'passive', 'aggressive', 'passive_aggressive'
    response_pattern: str  # 'prompt', 'delayed', 'inconsistent'
    leadership_indicators: float  # 0 to 1
    collaboration_score: float  # 0 to 1
    conflict_tendency: float  # 0 to 1
    burnout_risk: float  # 0 to 1

@dataclass
class PsychologicalSafetyIndicators:
    """Psychological safety metrics"""
    speaking_up_propensity: float  # 0 to 1
    feedback_receptivity: float  # 0 to 1
    vulnerability_sharing: float  # 0 to 1
    psychological_safety_score: float  # 0 to 1

class NLPAnalysisService:
    """Privacy-first NLP analysis service for behavioral insights"""

    def __init__(self):
        self.logger = logger
        self._sentiment_pipeline = None
        self._emotion_pipeline = None
        self._tokenizer = None

        # Check for required dependencies
        if not HAS_TRANSFORMERS or not HAS_SKLEARN:
            self.logger.warning("ML dependencies not available. NLP features will be limited.")
            self.device = "cpu"
            self._models_loaded = True  # Skip loading
        else:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self._models_loaded = False

    async def initialize_models(self):
        """Initialize NLP models lazily"""
        if self._models_loaded:
            return

        if not HAS_TRANSFORMERS or not HAS_SKLEARN:
            self.logger.info("ML dependencies not available, skipping model initialization")
            return

        try:
            self.logger.info("Initializing NLP models...")

            # Initialize sentiment analysis pipeline
            self._sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )

            # Initialize emotion analysis pipeline
            self._emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                device=0 if self.device == "cuda" else -1,
                return_all_scores=True
            )

            self._tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-sentiment-latest")
            self._models_loaded = True

            self.logger.info(f"NLP models loaded successfully on {self.device}")

        except Exception as e:
            self.logger.error(f"Failed to initialize NLP models: {e}")
            # Fallback to basic rule-based analysis
            self._models_loaded = False

    def _hash_text_for_analysis(self, text: str) -> str:
        """Create hash of text for consistent analysis without storing content"""
        if not text:
            return ""
        # Use SHA-256 for consistent hashing
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

    def _extract_subject_features(self, subject: str) -> Dict[str, Any]:
        """Extract linguistic features from email subject"""
        if not subject:
            return {
                'length': 0,
                'word_count': 0,
                'exclamation_count': 0,
                'question_count': 0,
                'urgency_words': 0,
                'politeness_words': 0,
                'has_re_prefix': False
            }

        # Basic counts
        word_count = len(subject.split())
        exclamation_count = subject.count('!')
        question_count = subject.count('?')

        # Linguistic patterns
        urgency_words = len(re.findall(r'\b(urgent|asap|immediate|critical|important|stat)\b', subject, re.IGNORECASE))
        politeness_words = len(re.findall(r'\b(please|thank|thanks|appreciate|kindly|could you|would you)\b', subject, re.IGNORECASE))
        has_re_prefix = subject.lower().startswith('re:')

        return {
            'length': len(subject),
            'word_count': word_count,
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            'urgency_words': urgency_words,
            'politeness_words': politeness_words,
            'has_re_prefix': has_re_prefix
        }

    async def analyze_sentiment_from_subject(self, subject: str) -> SentimentResult:
        """Analyze sentiment from email subject line"""
        if not subject:
            return SentimentResult(score=0.0, confidence=0.0, label="neutral")

        try:
            await self.initialize_models()

            if self._sentiment_pipeline:
                # Use transformer model
                result = self._sentiment_pipeline(subject[:512])  # Truncate for model
                label = result[0]['label'].lower()
                score = result[0]['score']

                # Convert to -1 to 1 scale
                if label == 'positive':
                    sentiment_score = score
                elif label == 'negative':
                    sentiment_score = -score
                else:
                    sentiment_score = 0.0

                return SentimentResult(
                    score=sentiment_score,
                    confidence=score,
                    label=label
                )
            else:
                # Fallback to rule-based sentiment
                return self._rule_based_sentiment(subject)

        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return self._rule_based_sentiment(subject)

    def _rule_based_sentiment(self, text: str) -> SentimentResult:
        """Rule-based sentiment analysis as fallback"""
        positive_words = ['great', 'excellent', 'good', 'happy', 'pleased', 'thank', 'thanks', 'awesome', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'angry', 'frustrated', 'disappointed', 'issue', 'problem', 'urgent', 'critical']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            score = min(0.8, positive_count / max(1, len(text.split())) * 2)
            label = "positive"
        elif negative_count > positive_count:
            score = max(-0.8, -negative_count / max(1, len(text.split())) * 2)
            label = "negative"
        else:
            score = 0.0
            label = "neutral"

        confidence = min(0.7, abs(score) + 0.3)
        return SentimentResult(score=score, confidence=confidence, label=label)

    async def analyze_emotions_from_subject(self, subject: str) -> EmotionResult:
        """Analyze emotions from email subject line"""
        if not subject:
            return EmotionResult(
                emotions={'neutral': 1.0},
                dominant_emotion='neutral',
                emotional_intensity=0.0
            )

        try:
            await self.initialize_models()

            if self._emotion_pipeline:
                # Use transformer model
                results = self._emotion_pipeline(subject[:512])
                emotions = {result['label']: result['score'] for result in results[0]}
                dominant_emotion = max(emotions, key=emotions.get)
                emotional_intensity = max(emotions.values())

                return EmotionResult(
                    emotions=emotions,
                    dominant_emotion=dominant_emotion,
                    emotional_intensity=emotional_intensity
                )
            else:
                # Fallback to basic emotion detection
                return self._rule_based_emotions(subject)

        except Exception as e:
            self.logger.error(f"Error analyzing emotions: {e}")
            return self._rule_based_emotions(subject)

    def _rule_based_emotions(self, text: str) -> EmotionResult:
        """Rule-based emotion detection as fallback"""
        emotion_keywords = {
            'joy': ['happy', 'excited', 'great', 'excellent', 'wonderful', 'fantastic'],
            'anger': ['angry', 'frustrated', 'annoyed', 'upset', 'furious', 'irritated'],
            'fear': ['worried', 'concerned', 'anxious', 'scared', 'nervous', 'afraid'],
            'sadness': ['sad', 'disappointed', 'upset', 'depressed', 'unhappy'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished'],
            'neutral': []  # default
        }

        text_lower = text.lower()
        emotion_scores = {}

        for emotion, keywords in emotion_keywords.items():
            if keywords:
                score = sum(1 for keyword in keywords if keyword in text_lower)
                emotion_scores[emotion] = score / len(text.split()) if text.split() else 0
            else:
                emotion_scores[emotion] = 0.1  # baseline for neutral

        # Normalize scores
        total_score = sum(emotion_scores.values())
        if total_score > 0:
            emotion_scores = {k: v/total_score for k, v in emotion_scores.items()}

        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        emotional_intensity = max(emotion_scores.values())

        return EmotionResult(
            emotions=emotion_scores,
            dominant_emotion=dominant_emotion,
            emotional_intensity=emotional_intensity
        )

    def analyze_communication_patterns(self, email_metadata_list: List[EmailMetadata]) -> BehavioralIndicators:
        """Analyze communication patterns from email metadata"""
        if not email_metadata_list:
            return BehavioralIndicators(
                communication_style='neutral',
                response_pattern='inconsistent',
                leadership_indicators=0.5,
                collaboration_score=0.5,
                conflict_tendency=0.5,
                burnout_risk=0.5
            )

        # Response time analysis
        response_times = [email.response_time_minutes for email in email_metadata_list if email.response_time_minutes]

        if response_times:
            avg_response_time = np.mean(response_times)
            response_time_std = np.std(response_times)

            # Determine response pattern
            if avg_response_time < 60:  # less than 1 hour
                response_pattern = 'prompt'
            elif avg_response_time > 1440:  # more than 1 day
                response_pattern = 'delayed'
            else:
                response_pattern = 'inconsistent' if response_time_std > avg_response_time * 0.5 else 'moderate'
        else:
            response_pattern = 'unknown'
            avg_response_time = 0

        # Subject line analysis for communication style
        subjects = [email.subject_clean for email in email_metadata_list if email.subject_clean]

        if subjects:
            # Analyze linguistic patterns
            urgency_indicators = sum(len(re.findall(r'\b(urgent|asap|immediate|critical)\b', s, re.IGNORECASE)) for s in subjects)
            politeness_indicators = sum(len(re.findall(r'\b(please|thank|appreciate)\b', s, re.IGNORECASE)) for s in subjects)
            question_indicators = sum(s.count('?') for s in subjects)
            exclamation_indicators = sum(s.count('!') for s in subjects)

            # Determine communication style
            if urgency_indicators > politeness_indicators * 2:
                communication_style = 'aggressive'
            elif politeness_indicators > urgency_indicators * 2:
                communication_style = 'passive'
            elif exclamation_indicators > len(subjects) * 0.3:
                communication_style = 'passive_aggressive'
            else:
                communication_style = 'assertive'
        else:
            communication_style = 'neutral'
            urgency_indicators = politeness_indicators = question_indicators = exclamation_indicators = 0

        # Calculate behavioral scores
        total_emails = len(email_metadata_list)

        # Leadership indicators: initiating threads, asking questions, providing guidance
        leadership_score = min(1.0, (
            sum(email.is_thread_initiator for email in email_metadata_list if email.is_thread_initiator) / max(1, total_emails) +
            question_indicators / max(1, total_emails) * 0.3
        ))

        # Collaboration score: participation in threads, balanced communication
        collaboration_score = min(1.0, (
            (total_emails - sum(email.is_thread_initiator for email in email_metadata_list if email.is_thread_initiator)) / max(1, total_emails) +
            politeness_indicators / max(1, total_emails) * 0.5
        ))

        # Conflict tendency: urgency, negative sentiment patterns
        conflict_tendency = min(1.0, urgency_indicators / max(1, total_emails) + exclamation_indicators / max(1, total_emails))

        # Burnout risk: response times, email volume patterns
        burnout_risk = min(1.0, (
            (avg_response_time / (24 * 60)) if avg_response_time > 0 else 0 +  # convert to days
            min(1.0, total_emails / 100)  # volume indicator
        ) / 2)

        return BehavioralIndicators(
            communication_style=communication_style,
            response_pattern=response_pattern,
            leadership_indicators=leadership_score,
            collaboration_score=collaboration_score,
            conflict_tendency=conflict_tendency,
            burnout_risk=burnout_risk
        )

    def calculate_psychological_safety(self, user_patterns: Dict[str, Any], team_patterns: Dict[str, Any]) -> PsychologicalSafetyIndicators:
        """Calculate psychological safety indicators from communication patterns"""

        # Speaking up propensity: initiating threads, asking questions
        speaking_up = min(1.0, (
            user_patterns.get('thread_initiation_rate', 0) +
            user_patterns.get('question_asking_rate', 0)
        ) / 2)

        # Feedback receptivity: response patterns, acknowledgment behaviors
        feedback_receptivity = 1.0 - min(1.0, user_patterns.get('avoidance_rate', 0))

        # Vulnerability sharing: appropriate self-disclosure patterns
        vulnerability_sharing = min(1.0, user_patterns.get('appropriate_sharing_rate', 0))

        # Overall psychological safety (weighted average)
        psychological_safety = (
            speaking_up * 0.3 +
            feedback_receptivity * 0.3 +
            vulnerability_sharing * 0.2 +
            team_patterns.get('team_safety climate', 0.5) * 0.2
        )

        return PsychologicalSafetyIndicators(
            speaking_up_propensity=speaking_up,
            feedback_receptivity=feedback_receptivity,
            vulnerability_sharing=vulnerability_sharing,
            psychological_safety_score=psychological_safety
        )

    async def analyze_email_batch(self, db: Session, email_metadata_list: List[EmailMetadata]) -> List[CommunicationAnalysis]:
        """Analyze a batch of emails and create communication analysis records"""
        analyses = []

        for email_meta in email_metadata_list:
            try:
                # Analyze sentiment from subject
                sentiment_result = await self.analyze_sentiment_from_subject(email_meta.subject_clean)

                # Analyze emotions from subject
                emotion_result = await self.analyze_emotions_from_subject(email_meta.subject_clean)

                # Extract linguistic features
                subject_features = self._extract_subject_features(email_meta.subject_clean)

                # Calculate conflict probability
                conflict_probability = self._calculate_conflict_probability(email_meta, sentiment_result, subject_features)

                # Create communication analysis record
                analysis = CommunicationAnalysis(
                    email_id=email_meta.message_id,
                    user_id=email_meta.user_id,
                    sentiment_score=sentiment_result.score,
                    sentiment_confidence=sentiment_result.confidence,
                    emotion_scores=emotion_result.emotions,
                    dominant_emotion=emotion_result.dominant_emotion,
                    emotional_intensity=emotion_result.emotional_intensity,
                    linguistic_features=subject_features,
                    conflict_probability=conflict_probability,
                    analysis_timestamp=datetime.utcnow(),
                    analysis_model_version="1.0"
                )

                analyses.append(analysis)

            except Exception as e:
                self.logger.error(f"Error analyzing email {email_meta.message_id}: {e}")
                continue

        return analyses

    def _calculate_conflict_probability(self, email: EmailMetadata, sentiment: SentimentResult, features: Dict[str, Any]) -> float:
        """Calculate probability of conflict based on email characteristics"""

        # Base probability from sentiment
        base_conflict = max(0, -sentiment.score) * 0.5  # Negative sentiment increases conflict probability

        # Urgency indicators
        urgency_factor = min(1.0, features.get('urgency_words', 0) * 0.2)

        # Exclamation marks (agitation indicator)
        exclamation_factor = min(1.0, features.get('exclamation_count', 0) * 0.1)

        # Response time patterns (very quick or very slow responses can indicate conflict)
        if email.response_time_minutes:
            if email.response_time_minutes < 5:  # Very quick response
                response_factor = 0.2
            elif email.response_time_minutes > 2880:  # >48 hours
                response_factor = 0.3
            else:
                response_factor = 0.0
        else:
            response_factor = 0.0

        # Thread length (long threads can indicate unresolved issues)
        thread_factor = min(1.0, (email.thread_position or 1) * 0.05)

        # Combine factors
        conflict_probability = min(1.0, base_conflict + urgency_factor + exclamation_factor + response_factor + thread_factor)

        return conflict_probability

    async def generate_insights_summary(self, db: Session, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Generate comprehensive insights summary for a user"""

        # Get recent analyses
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        recent_analyses = result = await db.execute(query)
        return result.scalars().all()

        if not recent_analyses:
            return {"message": "No recent communication data available"}

        # Aggregate metrics
        sentiment_scores = [float(a.sentiment_score) for a in recent_analyses if a.sentiment_score]
        conflict_probabilities = [float(a.conflict_probability) for a in recent_analyses if a.conflict_probability]

        insights = {
            "analysis_period_days": days_back,
            "total_emails_analyzed": len(recent_analyses),
            "sentiment_analysis": {
                "average_sentiment": np.mean(sentiment_scores) if sentiment_scores else 0,
                "sentiment_trend": "improving" if len(sentiment_scores) > 1 and np.mean(sentiment_scores[-10:]) > np.mean(sentiment_scores[:10]) else "stable",
                "positive_ratio": len([s for s in sentiment_scores if s > 0.1]) / len(sentiment_scores) if sentiment_scores else 0
            },
            "conflict_analysis": {
                "average_conflict_probability": np.mean(conflict_probabilities) if conflict_probabilities else 0,
                "high_conflict_emails": len([p for p in conflict_probabilities if p > 0.7]),
                "conflict_trend": "increasing" if len(conflict_probabilities) > 1 and np.mean(conflict_probabilities[-10:]) > np.mean(conflict_probabilities[:10]) else "stable"
            },
            "behavioral_patterns": {
                "communication_frequency": len(recent_analyses) / days_back,
                "emotional_intensity": np.mean([float(a.emotional_intensity) for a in recent_analyses if a.emotional_intensity]) if recent_analyses else 0
            }
        }

        return insights

# Singleton instance
nlp_analysis_service = NLPAnalysisService()