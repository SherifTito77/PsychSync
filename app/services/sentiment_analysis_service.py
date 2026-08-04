"""
Sentiment Analysis Service
Uses NLP to detect emotional tone in emails
"""

import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Tuple

# Emotion lexicons (simplified - in production, use NLP libraries like TextBlob, VADER, or transformers)
EMOTION_LEXICON = {
    "positive": {
        "strong": [
            "excellent",
            "outstanding",
            "fantastic",
            "amazing",
            "wonderful",
            "terrific",
            "love",
            "excited",
            "thrilled",
            "delighted",
            "ecstatic",
            "overjoyed",
            "brilliant",
            "superb",
            "perfect",
            "incredible",
            "phenomenal",
        ],
        "moderate": [
            "good",
            "great",
            "nice",
            "happy",
            "pleased",
            "satisfied",
            "content",
            "glad",
            "pleasure",
            "enjoy",
            "appreciate",
            "thank",
            "thanks",
            "helpful",
            "useful",
            "positive",
            "success",
            "successful",
        ],
        "weak": ["okay", "fine", "alright", "decent", "acceptable", "reasonable"],
    },
    "negative": {
        "strong": [
            "terrible",
            "horrible",
            "awful",
            "hate",
            "disgusted",
            "furious",
            "enraged",
            "devastated",
            "miserable",
            "appalled",
            "disgusting",
            "outraged",
            "catastrophic",
            "disastrous",
            "unbearable",
            "unacceptable",
        ],
        "moderate": [
            "bad",
            "poor",
            "disappointed",
            "frustrated",
            "annoyed",
            "upset",
            "unhappy",
            "dissatisfied",
            "concern",
            "worried",
            "anxious",
            "problem",
            "issue",
            "fail",
            "failed",
            "failure",
        ],
        "weak": ["sorry", "regret", "unfortunate", "dislike", "rather", "unpleasant"],
    },
    "neutral": [
        "regarding",
        "concerning",
        "about",
        "regarding",
        "reference",
        "please",
        "note",
        "information",
        "update",
        "notice",
        "reminder",
        "confirmation",
    ],
}

# Emotional tone indicators
EMOTIONAL_TONES = {
    "anger": ["angry", "furious", "irate", "mad", "outraged", "hostile"],
    "fear": ["afraid", "scared", "fearful", "anxious", "worried", "terrified", "panic"],
    "joy": ["joy", "joyful", "cheerful", "elated", "happy", "excited"],
    "sadness": ["sad", "unhappy", "depressed", "down", "miserable", "grief"],
    "surprise": ["surprised", "shocked", "amazed", "astonished", "stunned"],
    "stress": ["stressed", "overwhelmed", "pressured", "burdened", "exhausted"],
    "urgency": ["urgent", "immediately", "asap", "emergency", "critical", "priority"],
    "confusion": ["confused", "unclear", "uncertain", "puzzled", "don't understand"],
}

# Email stress indicators
STRESS_INDICATORS = {
    "exclamation_overload": re.compile(r"!{2,}"),
    "all_caps": re.compile(r"\b[A-Z]{2,}\b"),
    "urgency_words": [
        "urgent",
        "asap",
        "immediately",
        "right away",
        "emergency",
        "critical",
        "priority",
        "action required",
        "action needed",
    ],
    "deadline_pressure": [
        "deadline",
        "due",
        "overdue",
        "late",
        "extension needed",
        "by 5 pm",
        "by 5pm",
        "by noon",
        "by end of day",
        "eod",
        "eow",
        "end of week",
        "today",
        "tomorrow",
        "as soon as possible",
    ],
    "time_pressure": [
        "quickly",
        "hurry",
        "rush",
        "asap",
        "as soon as possible",
        "right now",
        "immediately",
    ],
    "overwhelmed": [
        "too much",
        "can't handle",
        "overwhelmed",
        "drowning",
        "buried",
        "swamped",
    ],
    "approval_needed": ["approval", "sign-off", "authorization", "approved", "approve"],
}

# Disappointment and negative pattern indicators
DISAPPOINTMENT_PATTERNS = {
    "questioning": [
        "why am i not",
        "why didn't you",
        "why haven't",
        "why can't",
        "how come",
    ],
    "exclusion": [
        "not cc'd",
        "not included",
        "left out",
        "didn't copy",
        "forgot to include",
    ],
    "broken_expectations": [
        "i thought",
        "we agreed",
        "supposed to",
        "you promised",
        "should have",
        "expected",
    ],
    "frustration": [
        "again",
        "still",
        "yet another",
        "why does it",
        "how many times",
        "tired of",
    ],
    "disappointment": [
        "disappointed",
        "unfortunate",
        "sad to see",
        "wish you had",
        "hoped for",
    ],
}


class SentimentAnalyzer:
    """Analyze sentiment and emotional tone in emails"""

    def __init__(self):
        self.emotion_lexicon = EMOTION_LEXICON
        self.emotional_tones = EMOTIONAL_TONES
        self.stress_indicators = STRESS_INDICATORS

    def analyze_email(self, email_content: str, subject: str = "") -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis on email

        Args:
            email_content: Email body text
            subject: Email subject line

        Returns:
            Dict with sentiment scores and emotional analysis
        """
        # Combine subject and body
        full_text = f"{subject} {email_content}".lower()

        # Log for debugging
        from app.core.logging_config import logger

        logger.info(f"🔍 Analyzing email - Subject: {subject[:50]}...")
        logger.info(f"📧 Content preview: {email_content[:100]}...")

        # Tokenize
        words = self._tokenize(full_text)
        logger.info(f"📝 Tokenized to {len(words)} words")

        # Analyze sentiment
        sentiment = self._analyze_sentiment(words, full_text)
        logger.info(
            f"✨ Sentiment result: {sentiment['polarity']} (confidence: {sentiment['confidence']})"
        )

        # Analyze emotional tones
        emotional_tones = self._analyze_emotional_tones(words)

        # Detect stress levels
        stress_analysis = self._detect_stress(full_text, email_content)

        # Extract key phrases
        key_phrases = self._extract_key_phrases(words)

        # Generate insights
        insights = self._generate_insights(sentiment, emotional_tones, stress_analysis)

        return {
            "sentiment": sentiment,
            "emotional_tones": emotional_tones,
            "stress_analysis": stress_analysis,
            "key_phrases": key_phrases,
            "insights": insights,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove punctuation, convert to lowercase, split
        words = re.findall(r"\b[a-z]+\b", text.lower())
        return words

    def _analyze_sentiment(self, words: List[str], full_text: str) -> Dict[str, Any]:
        """Analyze overall sentiment"""
        word_counts = Counter(words)

        # Count positive/negative words by strength
        positive_strong = sum(
            word_counts.get(w, 0) for w in self.emotion_lexicon["positive"]["strong"]
        )
        positive_moderate = sum(
            word_counts.get(w, 0) for w in self.emotion_lexicon["positive"]["moderate"]
        )
        positive_weak = sum(
            word_counts.get(w, 0) for w in self.emotion_lexicon["positive"]["weak"]
        )

        negative_strong = sum(
            word_counts.get(w, 0) for w in self.emotion_lexicon["negative"]["strong"]
        )
        negative_moderate = sum(
            word_counts.get(w, 0) for w in self.emotion_lexicon["negative"]["moderate"]
        )
        negative_weak = sum(
            word_counts.get(w, 0) for w in self.emotion_lexicon["negative"]["weak"]
        )

        # Calculate weighted scores
        positive_score = (
            (positive_strong * 3) + (positive_moderate * 2) + (positive_weak * 1)
        )
        negative_score = (
            (negative_strong * 3) + (negative_moderate * 2) + (negative_weak * 1)
        )

        # Add urgency/stress as negative sentiment contributors
        urgency_count = sum(
            1 for word in self.stress_indicators["urgency_words"] if word in full_text
        )
        deadline_count = sum(
            1
            for phrase in self.stress_indicators["deadline_pressure"]
            if phrase in full_text
        )

        # Urgency and deadline pressure contribute to negative sentiment
        stress_contribution = (urgency_count * 2) + (deadline_count * 1)
        if stress_contribution > 0:
            negative_score += stress_contribution

        # Check for disappointment patterns (these are strongly negative)
        from app.core.logging_config import logger

        disappointment_score = 0
        full_lower = full_text.lower()

        for category, patterns in DISAPPOINTMENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in full_lower:
                    # Count occurrences
                    count = full_lower.count(pattern)
                    if category == "questioning":
                        disappointment_score += count * 3  # Strong negative
                    elif category == "exclusion":
                        disappointment_score += count * 4  # Very strong negative
                    elif category == "broken_expectations":
                        disappointment_score += count * 3  # Strong negative
                    elif category == "frustration":
                        disappointment_score += count * 2  # Moderate negative
                    elif category == "disappointment":
                        disappointment_score += count * 3  # Strong negative

        if disappointment_score > 0:
            negative_score += disappointment_score
            logger.info(
                f"Detected disappointment patterns: score={disappointment_score}"
            )

        total_score = positive_score + negative_score
        if total_score == 0:
            polarity = "neutral"
            confidence = 0.5
        else:
            polarity_ratio = positive_score / total_score
            if polarity_ratio > 0.6:
                polarity = "positive"
            elif polarity_ratio < 0.4:
                polarity = "negative"
            else:
                # If there's urgency/deadline pressure or disappointment, lean towards negative
                if stress_contribution > 0 or disappointment_score > 0:
                    polarity = "negative"
                else:
                    polarity = "neutral"

            # Confidence based on strength of sentiment words
            strength_count = (
                positive_strong
                + negative_strong
                + stress_contribution
                + (disappointment_score // 2)
            )
            confidence = min(0.5 + (strength_count * 0.1), 1.0)

        return {
            "polarity": polarity,  # positive, negative, neutral
            "confidence": round(confidence, 2),
            "positive_score": positive_score,
            "negative_score": negative_score,
            "breakdown": {
                "positive": {
                    "strong": positive_strong,
                    "moderate": positive_moderate,
                    "weak": positive_weak,
                },
                "negative": {
                    "strong": negative_strong,
                    "moderate": negative_moderate,
                    "weak": negative_weak,
                },
            },
        }

    def _analyze_emotional_tones(self, words: List[str]) -> Dict[str, Any]:
        """Analyze specific emotional tones"""
        word_counts = Counter(words)
        detected_tones = []

        for tone, tone_words in self.emotional_tones.items():
            count = sum(word_counts.get(w, 0) for w in tone_words)
            if count > 0:
                intensity = (
                    "high" if count >= 3 else "moderate" if count >= 2 else "low"
                )
                detected_tones.append(
                    {"tone": tone, "count": count, "intensity": intensity}
                )

        # Sort by count
        detected_tones.sort(key=lambda x: x["count"], reverse=True)

        return {
            "primary_tone": detected_tones[0]["tone"] if detected_tones else "neutral",
            "tones": detected_tones,
            "has_emotional_content": len(detected_tones) > 0,
        }

    def _detect_stress(self, full_text: str, original_content: str) -> Dict[str, Any]:
        """Detect stress indicators in email"""
        stress_signals = []

        # Check for exclamation overload
        exclamations = len(
            self.stress_indicators["exclamation_overload"].findall(original_content)
        )
        if exclamations > 2:
            stress_signals.append(
                {
                    "indicator": "exclamation_overload",
                    "count": exclamations,
                    "severity": "high" if exclamations > 5 else "moderate",
                }
            )

        # Check for ALL CAPS
        caps_matches = self.stress_indicators["all_caps"].findall(original_content)
        if len(caps_matches) > 3:
            stress_signals.append(
                {
                    "indicator": "all_caps",
                    "count": len(caps_matches),
                    "severity": "moderate",
                }
            )

        # Check for urgency words (including phrases)
        full_lower = full_text.lower()
        urgency_count = 0
        for urgency_word in self.stress_indicators["urgency_words"]:
            if urgency_word in full_lower:
                urgency_count += full_lower.count(urgency_word)

        if urgency_count > 0:
            stress_signals.append(
                {
                    "indicator": "urgency_language",
                    "count": urgency_count,
                    "severity": "high" if urgency_count >= 3 else "moderate",
                }
            )

        # Check for deadline pressure (including time phrases)
        deadline_count = 0
        for deadline_phrase in self.stress_indicators["deadline_pressure"]:
            if deadline_phrase in full_lower:
                deadline_count += full_lower.count(deadline_phrase)

        if deadline_count > 0:
            stress_signals.append(
                {
                    "indicator": "deadline_pressure",
                    "count": deadline_count,
                    "severity": "high" if deadline_count >= 2 else "moderate",
                }
            )

        # Check for time pressure
        time_pressure_count = 0
        for time_word in self.stress_indicators["time_pressure"]:
            if time_word in full_lower:
                time_pressure_count += full_lower.count(time_word)

        if time_pressure_count > 0:
            stress_signals.append(
                {
                    "indicator": "time_pressure",
                    "count": time_pressure_count,
                    "severity": "moderate",
                }
            )

        # Check for approval pressure
        approval_count = 0
        for approval_word in self.stress_indicators["approval_needed"]:
            if approval_word in full_lower:
                approval_count += full_lower.count(approval_word)

        if approval_count > 0:
            stress_signals.append(
                {
                    "indicator": "approval_pressure",
                    "count": approval_count,
                    "severity": "moderate",
                }
            )

        # Check for overwhelmed language
        overwhelmed_count = sum(
            1 for phrase in self.stress_indicators["overwhelmed"] if phrase in full_text
        )
        if overwhelmed_count > 0:
            stress_signals.append(
                {
                    "indicator": "overwhelmed_language",
                    "count": overwhelmed_count,
                    "severity": "high",
                }
            )

        # Check for disappointment patterns
        for category, patterns in DISAPPOINTMENT_PATTERNS.items():
            for pattern in patterns:
                if pattern in full_lower:
                    count = full_lower.count(pattern)
                    if count > 0:
                        severity = (
                            "high"
                            if category
                            in ["exclusion", "questioning", "broken_expectations"]
                            else "moderate"
                        )
                        stress_signals.append(
                            {
                                "indicator": category,
                                "count": count,
                                "severity": severity,
                            }
                        )

        # Calculate overall stress level
        if not stress_signals:
            stress_level = "low"
            stress_score = 0
        else:
            high_severity = sum(1 for s in stress_signals if s["severity"] == "high")
            stress_score = len(stress_signals) + high_severity

            if stress_score >= 4:
                stress_level = "very high"
            elif stress_score >= 3:
                stress_level = "high"
            elif stress_score >= 2:
                stress_level = "moderate"
            else:
                stress_level = "low"

        return {
            "stress_level": stress_level,
            "stress_score": stress_score,
            "indicators": stress_signals,
            "requires_attention": stress_level in ["high", "very high"],
        }

    def _extract_key_phrases(self, words: List[str]) -> List[str]:
        """Extract key phrases that carry sentiment"""
        # Find words from emotion lexicons
        key_words = []
        for category in ["positive", "negative"]:
            for strength in ["strong", "moderate", "weak"]:
                key_words.extend(self.emotion_lexicon[category][strength])

        # Find matches
        word_counts = Counter(words)
        key_phrases = [word for word in key_words if word_counts.get(word, 0) > 0]

        # Remove duplicates and limit
        return list(set(key_phrases))[:10]

    def _generate_insights(
        self, sentiment: Dict[str, Any], tones: Dict[str, Any], stress: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable insights from analysis"""
        insights = []

        # Sentiment insights
        if sentiment["polarity"] == "negative" and sentiment["confidence"] > 0.7:
            insights.append(
                "Email has strongly negative tone - may require careful response"
            )

        if sentiment["polarity"] == "positive" and sentiment["confidence"] > 0.7:
            insights.append("Email has positive tone - good relationship indicator")

        # Check for disappointment/exclusion patterns
        if sentiment["negative_score"] > 0:
            if sentiment["negative_score"] >= 6:
                # Check for specific patterns
                if "exclusion" in str(stress.get("indicators", [])):
                    insights.append(
                        "Sender feels excluded - address the exclusion directly"
                    )
                if "questioning" in str(stress.get("indicators", [])):
                    insights.append(
                        "Sender is questioning actions - provide clear explanation"
                    )
                if "broken_expectations" in str(stress.get("indicators", [])):
                    insights.append(
                        "Expectations were not met - acknowledge and address the gap"
                    )

        # Emotional tone insights
        if tones["has_emotional_content"]:
            primary = tones["primary_tone"]
            if primary == "anger":
                insights.append("Anger detected - consider de-escalation techniques")
            elif primary == "stress":
                insights.append(
                    "Stress indicators present - may need support or extension"
                )
            elif primary == "urgency":
                insights.append("Urgency detected - prioritize response")

        # Stress insights
        if stress["stress_level"] in ["high", "very high"]:
            insights.append(
                f"High stress level detected ({stress['stress_level']}) - sender may be overwhelmed"
            )

        if stress["requires_attention"]:
            insights.append(
                "Multiple stress indicators - recommend empathetic response"
            )

        # Default insight if neutral
        if not insights:
            insights.append("Email has neutral tone - straightforward communication")

        return insights

    def analyze_email_batch(self, emails: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analyze multiple emails and provide aggregate analysis

        Args:
            emails: List of email dicts with 'content' and 'subject' keys

        Returns:
            Aggregate sentiment analysis
        """
        individual_analyses = []

        for email in emails:
            analysis = self.analyze_email(
                email.get("content", ""), email.get("subject", "")
            )
            individual_analyses.append(analysis)

        # Calculate aggregates
        total = len(individual_analyses)
        sentiment_counts = Counter(
            a["sentiment"]["polarity"] for a in individual_analyses
        )

        stress_levels = Counter(
            a["stress_analysis"]["stress_level"] for a in individual_analyses
        )

        # Most common emotional tones
        all_tones = []
        for analysis in individual_analyses:
            all_tones.extend([t["tone"] for t in analysis["emotional_tones"]["tones"]])
        top_tones = Counter(all_tones).most_common(5)

        return {
            "total_emails_analyzed": total,
            "sentiment_distribution": {
                "positive": sentiment_counts.get("positive", 0),
                "neutral": sentiment_counts.get("neutral", 0),
                "negative": sentiment_counts.get("negative", 0),
            },
            "stress_level_distribution": dict(stress_levels),
            "top_emotional_tones": [
                {"tone": tone, "count": count} for tone, count in top_tones
            ],
            "high_stress_count": sum(
                1
                for a in individual_analyses
                if a["stress_analysis"]["requires_attention"]
            ),
            "average_confidence": (
                sum(a["sentiment"]["confidence"] for a in individual_analyses) / total
                if total > 0
                else 0
            ),
            "individual_analyses": individual_analyses,
        }


# Singleton instance
sentiment_analyzer = SentimentAnalyzer()
