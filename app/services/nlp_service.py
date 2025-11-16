# ============================================================================
# FILE 1: app/services/nlp_service.py
# Core NLP service for sentiment analysis and text processing
# ============================================================================

from typing import Dict, List, Optional, Tuple
import re
from collections import Counter
from datetime import datetime
import numpy as np
from textblob import TextBlob
import spacy
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class NLPService:
    """Advanced NLP service for psychometric text analysis"""
    
    def __init__(self):
        self.nlp = None
        self.sentiment_analyzer = None
        self.emotion_classifier = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models lazily"""
        try:
            # Load spaCy model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Initialize sentiment analyzer
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # Initialize emotion classifier
            self.emotion_classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None
            )
            
            logger.info("NLP models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing NLP models: {e}")
            raise
    
    def analyze_text(self, text: str) -> Dict:
        """
        Comprehensive text analysis for psychometric insights
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict containing sentiment, emotions, linguistic features
        """
        if not text or not text.strip():
            return self._empty_analysis()
        
        try:
            # Basic sentiment
            sentiment = self._analyze_sentiment(text)
            
            # Emotion detection
            emotions = self._detect_emotions(text)
            
            # Linguistic features
            linguistic = self._extract_linguistic_features(text)
            
            # Psycholinguistic markers
            psycho_markers = self._extract_psycholinguistic_markers(text)
            
            # Named entities
            entities = self._extract_entities(text)
            
            return {
                "sentiment": sentiment,
                "emotions": emotions,
                "linguistic_features": linguistic,
                "psycholinguistic_markers": psycho_markers,
                "entities": entities,
                "metadata": {
                    "text_length": len(text),
                    "word_count": len(text.split()),
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error in text analysis: {e}")
            return self._empty_analysis()
    
    def _analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using multiple methods"""
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_sentiment = {
            "polarity": blob.sentiment.polarity,  # -1 to 1
            "subjectivity": blob.sentiment.subjectivity  # 0 to 1
        }
        
        # Transformer-based sentiment
        transformer_result = self.sentiment_analyzer(text[:512])[0]
        
        return {
            "overall_score": textblob_sentiment["polarity"],
            "label": transformer_result["label"],
            "confidence": transformer_result["score"],
            "subjectivity": textblob_sentiment["subjectivity"],
            "interpretation": self._interpret_sentiment(textblob_sentiment["polarity"])
        }
    
    def _detect_emotions(self, text: str) -> Dict:
        """Detect emotions in text"""
        try:
            results = self.emotion_classifier(text[:512])[0]
            
            emotions = {}
            for result in results:
                emotions[result["label"]] = result["score"]
            
            # Get dominant emotion
            dominant = max(results, key=lambda x: x["score"])
            
            return {
                "scores": emotions,
                "dominant_emotion": dominant["label"],
                "dominant_confidence": dominant["score"],
                "emotional_intensity": np.std(list(emotions.values()))
            }
        except Exception as e:
            logger.error(f"Emotion detection error: {e}")
            return {"scores": {}, "dominant_emotion": "neutral", "dominant_confidence": 0.5}
    
    def _extract_linguistic_features(self, text: str) -> Dict:
        """Extract linguistic features for personality insights"""
        doc = self.nlp(text)
        
        # Count different POS tags
        pos_counts = Counter([token.pos_ for token in doc])
        
        # Sentence complexity
        sentences = list(doc.sents)
        avg_sentence_length = np.mean([len(sent) for sent in sentences]) if sentences else 0
        
        # Vocabulary richness (Type-Token Ratio)
        words = [token.text.lower() for token in doc if token.is_alpha]
        ttr = len(set(words)) / len(words) if words else 0
        
        return {
            "sentence_count": len(sentences),
            "avg_sentence_length": float(avg_sentence_length),
            "type_token_ratio": float(ttr),
            "noun_count": pos_counts.get("NOUN", 0),
            "verb_count": pos_counts.get("VERB", 0),
            "adjective_count": pos_counts.get("ADJ", 0),
            "adverb_count": pos_counts.get("ADV", 0),
            "pronoun_count": pos_counts.get("PRON", 0),
            "complexity_score": self._calculate_complexity(doc)
        }
    
    def _extract_psycholinguistic_markers(self, text: str) -> Dict:
        """Extract LIWC-style psycholinguistic markers"""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        total_words = len(words)
        
        if total_words == 0:
            return {}
        
        # Define marker categories
        markers = {
            "first_person": ["i", "me", "my", "mine", "myself"],
            "first_person_plural": ["we", "us", "our", "ours", "ourselves"],
            "second_person": ["you", "your", "yours", "yourself"],
            "third_person": ["he", "she", "they", "him", "her", "them"],
            "positive_emotion": ["happy", "joy", "love", "good", "great", "excellent"],
            "negative_emotion": ["sad", "angry", "hate", "bad", "terrible", "awful"],
            "anxiety": ["worry", "fear", "nervous", "anxious", "scared", "afraid"],
            "cognitive": ["think", "know", "consider", "understand", "realize"],
            "tentative": ["maybe", "perhaps", "possibly", "probably", "might"],
            "certainty": ["always", "never", "definitely", "absolutely", "certainly"],
            "achievement": ["win", "success", "achieve", "goal", "accomplish"],
            "power": ["strong", "superior", "control", "dominant", "powerful"]
        }
        
        results = {}
        for category, word_list in markers.items():
            count = sum(1 for word in words if word in word_list)
            results[category] = {
                "count": count,
                "percentage": (count / total_words) * 100
            }
        
        return results
    
    def _extract_entities(self, text: str) -> List[Dict]:
        """Extract named entities"""
        doc = self.nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        return entities
    
    def _calculate_complexity(self, doc) -> float:
        """Calculate text complexity score"""
        # Average word length
        words = [token for token in doc if token.is_alpha]
        avg_word_length = np.mean([len(token.text) for token in words]) if words else 0
        
        # Sentence length variance
        sentences = list(doc.sents)
        sentence_lengths = [len(sent) for sent in sentences]
        length_variance = np.var(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        # Lexical diversity
        unique_ratio = len(set([t.lemma_ for t in words])) / len(words) if words else 0
        
        # Combine into complexity score (0-100)
        complexity = (
            (avg_word_length / 10) * 30 +
            (length_variance / 100) * 30 +
            unique_ratio * 40
        )
        
        return min(100, complexity)
    
    def _interpret_sentiment(self, polarity: float) -> str:
        """Interpret sentiment polarity score"""
        if polarity >= 0.5:
            return "very_positive"
        elif polarity >= 0.1:
            return "positive"
        elif polarity >= -0.1:
            return "neutral"
        elif polarity >= -0.5:
            return "negative"
        else:
            return "very_negative"
    
    def analyze_trend(self, texts: List[str], timestamps: List[datetime]) -> Dict:
        """Analyze sentiment trend over multiple texts"""
        if len(texts) != len(timestamps):
            raise ValueError("texts and timestamps must have same length")
        
        analyses = []
        for text, timestamp in zip(texts, timestamps):
            analysis = self.analyze_text(text)
            analysis["timestamp"] = timestamp.isoformat()
            analyses.append(analysis)
        
        # Calculate trend
        sentiments = [a["sentiment"]["overall_score"] for a in analyses]
        
        if len(sentiments) > 1:
            # Linear regression for trend
            x = np.arange(len(sentiments))
            z = np.polyfit(x, sentiments, 1)
            trend_direction = "improving" if z[0] > 0.05 else "declining" if z[0] < -0.05 else "stable"
            trend_strength = abs(z[0])
        else:
            trend_direction = "insufficient_data"
            trend_strength = 0.0
        
        return {
            "analyses": analyses,
            "trend": {
                "direction": trend_direction,
                "strength": float(trend_strength),
                "average_sentiment": float(np.mean(sentiments)),
                "sentiment_variance": float(np.var(sentiments))
            },
            "session_count": len(texts)
        }
    
    def generate_wordcloud_data(self, text: str, max_words: int = 100) -> List[Dict]:
        """Generate word frequency data for wordcloud"""
        doc = self.nlp(text)
        
        # Filter meaningful words (nouns, verbs, adjectives)
        meaningful_words = [
            token.lemma_.lower()
            for token in doc
            if token.pos_ in ["NOUN", "VERB", "ADJ"] and not token.is_stop
        ]
        
        # Count frequencies
        word_freq = Counter(meaningful_words)
        
        # Return top words
        return [
            {"word": word, "frequency": freq}
            for word, freq in word_freq.most_common(max_words)
        ]
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            "sentiment": {"overall_score": 0.0, "label": "neutral", "confidence": 0.0},
            "emotions": {"scores": {}, "dominant_emotion": "neutral"},
            "linguistic_features": {},
            "psycholinguistic_markers": {},
            "entities": []
        }


