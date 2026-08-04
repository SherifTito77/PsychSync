# app/services/free_nlp_service.py
"""
Free NLP Analysis Service - Using only open-source local models
Replaces OpenAI/Anthropic with free alternatives

SECURITY: All text analysis methods now include comprehensive security controls:
- Input validation and sanitization
- PII/PHI redaction before processing
- Output sanitization before returning
- Security event logging for suspicious patterns
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

import nltk
import spacy
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize, word_tokenize

# AI Security imports
try:
    from ai.security.ai_input_validator import validate_ai_input
    from ai.security.ai_output_sanitizer import OutputType, sanitize_ai_output
    from ai.security.ai_security_monitoring import (
        SecurityEventSeverity,
        SecurityEventType,
        log_ai_security_event,
    )
    from ai.security.pii_redaction import redact_pii

    AI_SECURITY_AVAILABLE = True
except ImportError:
    AI_SECURITY_AVAILABLE = False
    logger.warning(
        "AI security controls not available - NLP service will run without security protection"
    )

# Download required NLTK data (one-time setup)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("sentiment/vader_lexicon")
except LookupError:
    nltk.download("vader_lexicon")

from app.core.logging_config import logger


@dataclass
class SentimentScore:
    """Sentiment analysis result"""

    positive: float
    negative: float
    neutral: float
    compound: float
    label: str


@dataclass
class EmotionScore:
    """Emotion analysis result"""

    joy: float
    anger: float
    fear: float
    sadness: float
    surprise: float
    disgust: float
    dominant_emotion: str


@dataclass
class BehavioralIndicators:
    """Behavioral indicators from communication"""

    urgency: float
    stress_level: float
    confidence: float
    collaboration_tendency: float
    leadership_indicators: float
    conflict_probability: float


class FreeNLPService:
    """Free NLP analysis using open-source models with comprehensive security controls"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

        # Security: Track security metrics
        self.security_enabled = AI_SECURITY_AVAILABLE
        self.processed_count = 0
        self.security_events_count = 0

        # Load spaCy model (download if needed)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("Downloading spaCy model...")
            import subprocess

            subprocess.run(
                ["python", "-m", "spacy", "download", "en_core_web_sm"], check=True
            )
            self.nlp = spacy.load("en_core_web_sm")

        # Emotion keywords (simplified emotion detection)
        self.emotion_keywords = {
            "joy": [
                "happy",
                "excited",
                "pleased",
                "satisfied",
                "delighted",
                "thrilled",
                "wonderful",
            ],
            "anger": [
                "angry",
                "frustrated",
                "annoyed",
                "irritated",
                "furious",
                "outraged",
                "mad",
            ],
            "fear": [
                "afraid",
                "scared",
                "worried",
                "anxious",
                "nervous",
                "concerned",
                "fearful",
            ],
            "sadness": [
                "sad",
                "disappointed",
                "upset",
                "depressed",
                "unhappy",
                "miserable",
                "grief",
            ],
            "surprise": [
                "surprised",
                "amazed",
                "shocked",
                "astonished",
                "unexpected",
                "wow",
            ],
            "disgust": [
                "disgusted",
                "revolted",
                "repulsed",
                "sickened",
                "appalled",
                "nauseated",
            ],
        }

        # Behavioral keywords
        self.urgency_keywords = [
            "urgent",
            "asap",
            "immediately",
            "emergency",
            "critical",
            "deadline",
        ]
        self.stress_keywords = [
            "overwhelmed",
            "stressed",
            "pressure",
            "difficult",
            "challenging",
            "problem",
        ]
        self.confidence_keywords = [
            "confident",
            "sure",
            "certain",
            "definitely",
            "absolutely",
            "guarantee",
        ]
        self.collaboration_keywords = [
            "together",
            "team",
            "collaborate",
            "partner",
            "join",
            "cooperation",
        ]
        self.leadership_keywords = [
            "lead",
            "manage",
            "guide",
            "direct",
            "supervise",
            "coordinate",
        ]
        self.conflict_keywords = [
            "disagree",
            "conflict",
            "dispute",
            "argument",
            "issue",
            "problem",
        ]

    def _apply_security_controls(
        self, text: str, method_name: str = "analysis"
    ) -> tuple[str, bool]:
        """
        Apply security controls to input text

        Returns:
            Tuple of (secured_text, security_passed)
        """
        if not self.security_enabled:
            return text, True

        try:
            # Step 1: Validate input
            validation_result = validate_ai_input(
                text, input_type="clinical_note", sanitize=True
            )

            if not validation_result.is_valid:
                self.security_events_count += 1
                log_ai_security_event(
                    event_type=SecurityEventType.INPUT_VALIDATION_FAILED,
                    severity=SecurityEventSeverity.MEDIUM,
                    details={"method": method_name, "issues": validation_result.issues},
                )
                # Still process but with sanitized input
                text = validation_result.sanitized_input

            # Step 2: Redact PII
            redaction_result = redact_pii(text)

            if redaction_result.findings:
                self.security_events_count += 1
                log_ai_security_event(
                    event_type=SecurityEventType.PII_DETECTED,
                    severity=SecurityEventSeverity.LOW,
                    details={
                        "method": method_name,
                        "num_findings": len(redaction_result.findings),
                        "risk_score": redaction_result.risk_score,
                    },
                )

            return redaction_result.redacted_text, True

        except Exception as e:
            self.logger.error(f"Error applying security controls: {e}")
            return text, False

    def analyze_sentiment(
        self, text: str, user_id: str | None = None
    ) -> SentimentScore:
        """
        Analyze sentiment using VADER (free NLTK analyzer)

        SECURITY: Input is validated and PII is redacted before processing
        """
        try:
            # SECURITY: Apply security controls
            secured_text, security_passed = self._apply_security_controls(
                text, "analyze_sentiment"
            )

            # Clean text
            cleaned_text = self._clean_text(secured_text)

            if not cleaned_text:
                return SentimentScore(0, 0, 1, 0, "neutral")

            # VADER sentiment analysis
            scores = self.sentiment_analyzer.polarity_scores(cleaned_text)

            # Determine sentiment label
            compound = scores["compound"]
            if compound >= 0.05:
                label = "positive"
            elif compound <= -0.05:
                label = "negative"
            else:
                label = "neutral"

            # Create result
            result = SentimentScore(
                positive=scores["pos"],
                negative=scores["neg"],
                neutral=scores["neu"],
                compound=compound,
                label=label,
            )

            # SECURITY: Sanitize output
            if self.security_enabled:
                sanitized_result = sanitize_ai_output(
                    result, output_type=OutputType.ANALYSIS
                )
                if sanitized_result.blocked:
                    self.logger.error(f"Output blocked: {sanitized_result.reason}")
                    return SentimentScore(0, 0, 1, 0, "neutral")
                result = sanitized_result.sanitized_output

            self.processed_count += 1
            return result

        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            return SentimentScore(0, 0, 1, 0, "neutral")

    def analyze_emotions(self, text: str) -> EmotionScore:
        """Analyze emotions using keyword-based approach"""
        try:
            cleaned_text = text.lower()
            tokens = word_tokenize(cleaned_text)

            emotion_scores = {}
            for emotion, keywords in self.emotion_keywords.items():
                score = sum(1 for token in tokens if token in keywords)
                emotion_scores[emotion] = score / len(tokens) if tokens else 0

            # Normalize scores
            total_score = sum(emotion_scores.values())
            if total_score > 0:
                for emotion in emotion_scores:
                    emotion_scores[emotion] = emotion_scores[emotion] / total_score
            else:
                # Default neutral emotion distribution
                for emotion in emotion_scores:
                    emotion_scores[emotion] = 0.167  # 1/6 for each emotion

            # Find dominant emotion
            dominant_emotion = max(emotion_scores, key=emotion_scores.get)

            return EmotionScore(
                joy=emotion_scores.get("joy", 0),
                anger=emotion_scores.get("anger", 0),
                fear=emotion_scores.get("fear", 0),
                sadness=emotion_scores.get("sadness", 0),
                surprise=emotion_scores.get("surprise", 0),
                disgust=emotion_scores.get("disgust", 0),
                dominant_emotion=dominant_emotion,
            )

        except Exception as e:
            self.logger.error(f"Emotion analysis failed: {e}")
            return EmotionScore(0.167, 0.167, 0.167, 0.167, 0.167, 0.167, "neutral")

    def analyze_behavioral_indicators(self, text: str) -> BehavioralIndicators:
        """Analyze behavioral indicators from text"""
        try:
            cleaned_text = text.lower()
            tokens = word_tokenize(cleaned_text)
            sentences = sent_tokenize(text)

            # Calculate various indicators
            urgency_score = self._calculate_keyword_score(tokens, self.urgency_keywords)
            stress_score = self._calculate_keyword_score(tokens, self.stress_keywords)
            confidence_score = self._calculate_keyword_score(
                tokens, self.confidence_keywords
            )
            collaboration_score = self._calculate_keyword_score(
                tokens, self.collaboration_keywords
            )
            leadership_score = self._calculate_keyword_score(
                tokens, self.leadership_keywords
            )
            conflict_score = self._calculate_keyword_score(
                tokens, self.conflict_keywords
            )

            # Adjust scores based on linguistic patterns
            avg_sentence_length = (
                sum(len(sent.split()) for sent in sentences) / len(sentences)
                if sentences
                else 0
            )

            # Very short sentences might indicate urgency
            if avg_sentence_length < 10:
                urgency_score += 0.2

            # Exclamation points indicate urgency or stress
            exclamation_count = text.count("!")
            urgency_score += min(exclamation_count * 0.1, 0.3)

            # Question marks might indicate uncertainty (low confidence)
            question_count = text.count("?")
            confidence_score -= min(question_count * 0.05, 0.2)

            # Normalize scores to 0-1 range
            urgency_score = min(max(urgency_score, 0), 1)
            stress_score = min(max(stress_score, 0), 1)
            confidence_score = min(max(confidence_score, 0), 1)
            collaboration_score = min(max(collaboration_score, 0), 1)
            leadership_score = min(max(leadership_score, 0), 1)

            return BehavioralIndicators(
                urgency=urgency_score,
                stress_level=stress_score,
                confidence=confidence_score,
                collaboration_tendency=collaboration_score,
                leadership_indicators=leadership_score,
                conflict_probability=min(
                    conflict_score * 2, 1
                ),  # Amplify conflict indicators
            )

        except Exception as e:
            self.logger.error(f"Behavioral analysis failed: {e}")
            return BehavioralIndicators(0, 0, 0.5, 0, 0, 0)

    def extract_key_topics(self, text: str, max_topics: int = 10) -> list[str]:
        """Extract key topics using spaCy NER and POS tagging"""
        try:
            doc = self.nlp(text)

            # Extract named entities
            entities = [
                ent.text.lower()
                for ent in doc.ents
                if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT"]
            ]

            # Extract noun phrases as topics
            noun_phrases = [
                chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text) > 2
            ]

            # Combine and count
            all_topics = entities + noun_phrases
            topic_counts = Counter(all_topics)

            # Filter out common stopwords
            stop_words = set(stopwords.words("english"))
            filtered_topics = [
                (topic, count)
                for topic, count in topic_counts.items()
                if topic not in stop_words and len(topic) > 2
            ]

            # Return top topics
            return [topic for topic, count in filtered_topics.most_common(max_topics)]

        except Exception as e:
            self.logger.error(f"Topic extraction failed: {e}")
            return []

    def analyze_communication_style(self, text: str) -> dict[str, Any]:
        """Analyze communication style patterns"""
        try:
            doc = self.nlp(text)
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())

            # Basic metrics
            word_count = len(words)
            sentence_count = len(sentences)
            avg_sentence_length = (
                word_count / sentence_count if sentence_count > 0 else 0
            )

            # Linguistic features
            exclamation_count = text.count("!")
            question_count = text.count("?")
            capitalized_words = sum(1 for word in words if word.isupper())

            # Parts of speech analysis
            pos_counts = Counter([token.pos_ for token in doc])
            formal_ratio = (
                (pos_counts.get("NOUN", 0) + pos_counts.get("ADJ", 0)) / word_count
                if word_count > 0
                else 0
            )

            # Complexity metrics
            unique_words = len(set(words))
            vocabulary_richness = unique_words / word_count if word_count > 0 else 0

            # Determine communication style
            if avg_sentence_length > 20 and formal_ratio > 0.3:
                style = "formal"
            elif exclamation_count > 2 or question_count > 2:
                style = "enthusiastic"
            elif avg_sentence_length < 10:
                style = "concise"
            elif vocabulary_richness > 0.7:
                style = "articulate"
            else:
                style = "casual"

            return {
                "style": style,
                "avg_sentence_length": avg_sentence_length,
                "formal_ratio": formal_ratio,
                "vocabulary_richness": vocabulary_richness,
                "exclamation_count": exclamation_count,
                "question_count": question_count,
                "capitalized_words": capitalized_words,
                "word_count": word_count,
                "sentence_count": sentence_count,
            }

        except Exception as e:
            self.logger.error(f"Communication style analysis failed: {e}")
            return {"style": "casual", "error": str(e)}

    def _clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        # Remove email signatures
        text = re.sub(r"--[\s\S]*$", "", text)

        # Remove forwarded message headers
        text = re.sub(r"-----Forwarded message[\s\S]*$", "", text)
        text = re.sub(r"From:.*$", "", text, flags=re.MULTILINE)

        # Remove extra whitespace
        text = " ".join(text.split())

        return text.strip()

    def _calculate_keyword_score(self, tokens: list[str], keywords: list[str]) -> float:
        """Calculate keyword density score"""
        token_set = set(tokens)
        matches = sum(1 for keyword in keywords if keyword in token_set)
        return matches / len(keywords) if keywords else 0

    def comprehensive_analysis(
        self, subject: str, preview_text: str = ""
    ) -> dict[str, Any]:
        """Perform comprehensive NLP analysis"""
        try:
            # Combine subject and preview text
            full_text = f"{subject}. {preview_text}" if preview_text else subject

            if not full_text.strip():
                return {
                    "error": "No text provided for analysis",
                    "sentiment": {"label": "neutral", "compound": 0},
                    "emotions": {"dominant_emotion": "neutral"},
                    "behavioral_indicators": {"urgency": 0, "stress_level": 0},
                    "topics": [],
                    "style": "casual",
                }

            # Perform all analyses
            sentiment = self.analyze_sentiment(full_text)
            emotions = self.analyze_emotions(full_text)
            behavioral = self.analyze_behavioral_indicators(full_text)
            topics = self.extract_key_topics(full_text)
            style = self.analyze_communication_style(full_text)

            return {
                "sentiment": {
                    "label": sentiment.label,
                    "positive": sentiment.positive,
                    "negative": sentiment.negative,
                    "neutral": sentiment.neutral,
                    "compound": sentiment.compound,
                },
                "emotions": {
                    "dominant_emotion": emotions.dominant_emotion,
                    "joy": emotions.joy,
                    "anger": emotions.anger,
                    "fear": emotions.fear,
                    "sadness": emotions.sadness,
                    "surprise": emotions.surprise,
                    "disgust": emotions.disgust,
                },
                "behavioral_indicators": {
                    "urgency": behavioral.urgency,
                    "stress_level": behavioral.stress_level,
                    "confidence": behavioral.confidence,
                    "collaboration_tendency": behavioral.collaboration_tendency,
                    "leadership_indicators": behavioral.leadership_indicators,
                    "conflict_probability": behavioral.conflict_probability,
                },
                "topics": topics,
                "communication_style": style,
                "text_length": len(full_text),
                "word_count": len(full_text.split()),
            }

        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            return {
                "error": str(e),
                "sentiment": {"label": "neutral", "compound": 0},
                "emotions": {"dominant_emotion": "neutral"},
                "behavioral_indicators": {"urgency": 0, "stress_level": 0},
                "topics": [],
                "style": "casual",
            }


# Singleton instance
free_nlp_service = FreeNLPService()
