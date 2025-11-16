"""
NLP Sentiment Analysis Service for PsychSync
Analyzes clinical notes, session summaries, and client feedback for sentiment and key themes.

Requirements:
    pip install spacy textblob vaderSentiment
    python -m spacy download en_core_web_sm
"""

import spacy
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime


class SentimentService:
    """
    Sentiment analysis service for clinical text analysis.
    Uses multiple NLP approaches for robust sentiment detection.
    """
    
    def __init__(self):
        """Initialize NLP models and analyzers."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy model not found. Please run: python -m spacy download en_core_web_sm"
            )
        
        self.vader = SentimentIntensityAnalyzer()
        
        # Clinical terms that may skew general sentiment but are neutral in clinical context
        self.clinical_neutral_terms = {
            'depression', 'anxiety', 'ptsd', 'trauma', 'disorder', 'symptoms',
            'diagnosis', 'treatment', 'therapy', 'medication', 'suicidal', 'death'
        }
        
        # Positive progress indicators
        self.progress_indicators = {
            'improved', 'better', 'progress', 'reduction', 'decreased', 'relief',
            'coping', 'managed', 'successful', 'achieved', 'motivated', 'engaged',
            'compliant', 'responsive', 'insight', 'understanding', 'stable'
        }
        
        # Negative progress indicators
        self.concern_indicators = {
            'worsened', 'deteriorated', 'increased', 'escalated', 'crisis',
            'relapse', 'withdrawn', 'non-compliant', 'resistant', 'declined',
            'struggle', 'difficulty', 'unable', 'failed', 'setback'
        }
    
    def analyze_text(self, text: str) -> Dict:
        """
        Comprehensive sentiment analysis of clinical text.
        
        Args:
            text: Clinical note or text to analyze
            
        Returns:
            Dictionary containing sentiment scores, themes, and keywords
        """
        if not text or not text.strip():
            return self._empty_analysis()
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Get sentiment scores
        textblob_sentiment = self._textblob_sentiment(text)
        vader_sentiment = self._vader_sentiment(text)
        clinical_sentiment = self._clinical_sentiment(doc)
        
        # Extract key information
        keywords = self._extract_keywords(doc)
        themes = self._extract_themes(doc)
        entities = self._extract_entities(doc)
        
        # Progress indicators
        progress_score = self._calculate_progress_score(text.lower())
        
        # Combine scores with clinical weighting
        combined_sentiment = self._combine_sentiments(
            textblob_sentiment,
            vader_sentiment,
            clinical_sentiment,
            progress_score
        )
        
        return {
            'overall_sentiment': combined_sentiment['label'],
            'sentiment_score': combined_sentiment['score'],
            'confidence': combined_sentiment['confidence'],
            'detailed_scores': {
                'textblob': textblob_sentiment,
                'vader': vader_sentiment,
                'clinical': clinical_sentiment,
                'progress': progress_score
            },
            'keywords': keywords[:20],  # Top 20 keywords
            'themes': themes,
            'entities': entities,
            'word_count': len(doc),
            'sentence_count': len(list(doc.sents)),
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def _textblob_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using TextBlob."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        return {
            'polarity': round(polarity, 3),  # -1 to 1
            'subjectivity': round(subjectivity, 3),  # 0 to 1
            'label': self._polarity_to_label(polarity)
        }
    
    def _vader_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using VADER (optimized for social media but useful)."""
        scores = self.vader.polarity_scores(text)
        
        return {
            'negative': round(scores['neg'], 3),
            'neutral': round(scores['neu'], 3),
            'positive': round(scores['pos'], 3),
            'compound': round(scores['compound'], 3),
            'label': self._vader_label(scores['compound'])
        }
    
    def _clinical_sentiment(self, doc) -> Dict:
        """
        Clinical-specific sentiment analysis.
        Focuses on progress indicators rather than general sentiment.
        """
        text_lower = doc.text.lower()
        
        # Count progress indicators
        positive_count = sum(1 for term in self.progress_indicators if term in text_lower)
        negative_count = sum(1 for term in self.concern_indicators if term in text_lower)
        
        # Calculate clinical score
        total = positive_count + negative_count
        if total == 0:
            clinical_score = 0
        else:
            clinical_score = (positive_count - negative_count) / total
        
        return {
            'score': round(clinical_score, 3),
            'positive_indicators': positive_count,
            'negative_indicators': negative_count,
            'label': self._polarity_to_label(clinical_score)
        }
    
    def _calculate_progress_score(self, text: str) -> Dict:
        """Calculate client progress based on indicator terms."""
        progress_count = sum(1 for term in self.progress_indicators if term in text)
        concern_count = sum(1 for term in self.concern_indicators if term in text)
        
        if progress_count + concern_count == 0:
            return {
                'score': 0,
                'interpretation': 'neutral',
                'progress_indicators': 0,
                'concern_indicators': 0
            }
        
        score = (progress_count - concern_count) / (progress_count + concern_count)
        
        return {
            'score': round(score, 3),
            'interpretation': 'improving' if score > 0.2 else 'declining' if score < -0.2 else 'stable',
            'progress_indicators': progress_count,
            'concern_indicators': concern_count
        }
    
    def _extract_keywords(self, doc) -> List[Dict]:
        """Extract significant keywords using TF-IDF-like approach."""
        # Filter for meaningful words
        keywords = [
            token.lemma_.lower() 
            for token in doc 
            if not token.is_stop 
            and not token.is_punct 
            and token.is_alpha
            and len(token.text) > 2
            and token.lemma_.lower() not in self.clinical_neutral_terms
        ]
        
        # Count frequency
        keyword_freq = Counter(keywords)
        
        # Return top keywords with frequency
        return [
            {'word': word, 'frequency': freq}
            for word, freq in keyword_freq.most_common(30)
        ]
    
    def _extract_themes(self, doc) -> List[str]:
        """Extract main themes from text using noun chunks."""
        themes = []
        
        # Extract noun phrases as potential themes
        for chunk in doc.noun_chunks:
            # Filter meaningful chunks
            if len(chunk.text.split()) >= 2 and not any(
                token.is_stop for token in chunk
            ):
                themes.append(chunk.text.lower())
        
        # Get most common themes
        theme_counts = Counter(themes)
        return [theme for theme, count in theme_counts.most_common(10)]
    
    def _extract_entities(self, doc) -> Dict[str, List[str]]:
        """Extract named entities (while protecting PHI)."""
        # Note: In production, this should be carefully filtered to avoid PHI exposure
        entities = {
            'symptoms': [],
            'treatments': [],
            'conditions': [],
            'temporal': [],
            'other': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'DATE' or ent.label_ == 'TIME':
                entities['temporal'].append(ent.text)
            elif ent.label_ == 'ORG':
                # Could be treatment programs, facilities
                entities['treatments'].append(ent.text)
            else:
                entities['other'].append(ent.text)
        
        return entities
    
    def _combine_sentiments(self, textblob, vader, clinical, progress) -> Dict:
        """
        Combine multiple sentiment scores with clinical weighting.
        Clinical indicators weighted more heavily than general sentiment.
        """
        # Weights for different analyses
        weights = {
            'textblob': 0.2,
            'vader': 0.2,
            'clinical': 0.4,
            'progress': 0.2
        }
        
        # Normalize all scores to -1 to 1 range
        scores = {
            'textblob': textblob['polarity'],
            'vader': vader['compound'],
            'clinical': clinical['score'],
            'progress': progress['score']
        }
        
        # Weighted average
        combined_score = sum(scores[k] * weights[k] for k in scores)
        
        # Calculate confidence based on agreement
        score_values = list(scores.values())
        variance = sum((x - combined_score) ** 2 for x in score_values) / len(score_values)
        confidence = max(0, 1 - variance)  # Lower variance = higher confidence
        
        return {
            'score': round(combined_score, 3),
            'label': self._polarity_to_label(combined_score),
            'confidence': round(confidence, 3)
        }
    
    def _polarity_to_label(self, score: float) -> str:
        """Convert polarity score to label."""
        if score >= 0.3:
            return 'positive'
        elif score <= -0.3:
            return 'negative'
        else:
            return 'neutral'
    
    def _vader_label(self, compound: float) -> str:
        """Convert VADER compound score to label."""
        if compound >= 0.05:
            return 'positive'
        elif compound <= -0.05:
            return 'negative'
        else:
            return 'neutral'
    
    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure."""
        return {
            'overall_sentiment': 'neutral',
            'sentiment_score': 0,
            'confidence': 0,
            'detailed_scores': {},
            'keywords': [],
            'themes': [],
            'entities': {},
            'word_count': 0,
            'sentence_count': 0,
            'analyzed_at': datetime.utcnow().isoformat()
        }
    
    def analyze_session_notes(self, notes: List[str]) -> Dict:
        """
        Analyze multiple session notes to track sentiment trends.
        
        Args:
            notes: List of session note texts (chronologically ordered)
            
        Returns:
            Trend analysis with aggregated statistics
        """
        if not notes:
            return {'error': 'No notes provided'}
        
        analyses = [self.analyze_text(note) for note in notes]
        
        # Extract sentiment scores over time
        sentiment_trend = [a['sentiment_score'] for a in analyses]
        
        # Calculate trend direction
        if len(sentiment_trend) >= 2:
            recent_avg = sum(sentiment_trend[-3:]) / min(3, len(sentiment_trend))
            early_avg = sum(sentiment_trend[:3]) / min(3, len(sentiment_trend))
            trend_direction = 'improving' if recent_avg > early_avg else 'declining' if recent_avg < early_avg else 'stable'
        else:
            trend_direction = 'insufficient_data'
        
        # Aggregate keywords across all notes
        all_keywords = {}
        for analysis in analyses:
            for kw in analysis['keywords']:
                word = kw['word']
                all_keywords[word] = all_keywords.get(word, 0) + kw['frequency']
        
        top_keywords = sorted(
            [{'word': w, 'frequency': f} for w, f in all_keywords.items()],
            key=lambda x: x['frequency'],
            reverse=True
        )[:20]
        
        return {
            'total_notes': len(notes),
            'sentiment_trend': sentiment_trend,
            'trend_direction': trend_direction,
            'average_sentiment': round(sum(sentiment_trend) / len(sentiment_trend), 3),
            'latest_sentiment': sentiment_trend[-1] if sentiment_trend else 0,
            'top_keywords': top_keywords,
            'analyses': analyses  # Individual analyses
        }
    
    def get_word_cloud_data(self, text: str, max_words: int = 50) -> List[Dict]:
        """
        Prepare data for word cloud visualization.
        
        Args:
            text: Text to analyze
            max_words: Maximum number of words to return
            
        Returns:
            List of word-frequency pairs suitable for word cloud
        """
        doc = self.nlp(text)
        keywords = self._extract_keywords(doc)
        
        # Format for frontend word cloud library
        return keywords[:max_words]


# Example usage and testing
if __name__ == "__main__":
    service = SentimentService()
    
    # Test with sample clinical note
    sample_note = """
    Client reported improved mood this week. She has been consistently 
    practicing mindfulness techniques and reports better sleep quality.
    Anxiety symptoms have decreased significantly since our last session.
    Client demonstrated good insight into her thought patterns and was 
    able to challenge negative automatic thoughts effectively. She completed
    all homework assignments and expressed motivation to continue treatment.
    No suicidal ideation reported. Plan: Continue with CBT techniques,
    schedule follow-up in one week.
    """
    
    print("Single Note Analysis:")
    print("-" * 50)
    result = service.analyze_text(sample_note)
    print(f"Overall Sentiment: {result['overall_sentiment']}")
    print(f"Sentiment Score: {result['sentiment_score']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Progress Interpretation: {result['detailed_scores']['progress']['interpretation']}")
    print(f"\nTop Keywords:")
    for kw in result['keywords'][:10]:
        print(f"  - {kw['word']}: {kw['frequency']}")
    
    print("\n" + "=" * 50)
    print("Multiple Notes Trend Analysis:")
    print("-" * 50)
    
    # Test with multiple session notes
    session_notes = [
        "Client appears withdrawn and reports increased anxiety. Sleep disturbances continue.",
        "Some improvement noted. Client engaged in session and completed homework partially.",
        "Significant progress this week. Client reports feeling more hopeful and anxiety levels decreased.",
        "Client maintaining gains. Coping skills being used effectively in daily life."
    ]
    
    trend_result = service.analyze_session_notes(session_notes)
    print(f"Total Notes Analyzed: {trend_result['total_notes']}")
    print(f"Trend Direction: {trend_result['trend_direction']}")
    print(f"Average Sentiment: {trend_result['average_sentiment']}")
    print(f"Sentiment Trend: {trend_result['sentiment_trend']}")
    
    print("\n" + "=" * 50)
    print("Word Cloud Data:")
    print("-" * 50)
    word_cloud_data = service.get_word_cloud_data(sample_note, max_words=15)
    for item in word_cloud_data:
        print(f"  {item['word']}: {item['frequency']}")