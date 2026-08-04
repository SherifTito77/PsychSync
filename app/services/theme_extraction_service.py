"""
Theme Extraction Service
Specialized service for extracting and analyzing key themes from text data
using advanced NLP techniques and statistical analysis.
"""

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from app.services.nlp_service import NLPService, Theme

logger = logging.getLogger(__name__)


class ThemeExtractionMethod(Enum):
    """Methods for theme extraction"""

    FREQUENCY = "frequency"
    TFIDF = "tfidf"
    TOPIC_MODELING = "topic_modeling"
    CLUSTERING = "clustering"
    HYBRID = "hybrid"


class ThemeType(Enum):
    """Types of themes"""

    CONCEPT = "concept"  # Abstract concepts and ideas
    EMOTION = "emotion"  # Emotional themes
    ACTION = "action"  # Action-oriented themes
    ENTITY = "entity"  # Named entities and people
    TOPIC = "topic"  # General topics
    BEHAVIOR = "behavior"  # Behavioral patterns


@dataclass
class ThemeCluster:
    """Cluster of related themes"""

    cluster_id: str
    name: str
    themes: list[Theme]
    centrality_score: float
    coherence_score: float
    dominant_sentiment: str
    time_trend: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "name": self.name,
            "themes": [theme.to_dict() for theme in self.themes],
            "centrality_score": self.centrality_score,
            "coherence_score": self.coherence_score,
            "dominant_sentiment": self.dominant_sentiment,
            "time_trend": self.time_trend,
        }


@dataclass
class ThemeTrend:
    """Temporal analysis of theme evolution"""

    theme_id: str
    theme_name: str
    time_points: list[datetime]
    frequency_values: list[float]
    sentiment_values: list[float]
    trend_direction: str  # increasing, decreasing, stable, volatile
    trend_strength: float
    seasonal_pattern: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme_id": self.theme_id,
            "theme_name": self.theme_name,
            "time_points": [tp.isoformat() for tp in self.time_points],
            "frequency_values": self.frequency_values,
            "sentiment_values": self.sentiment_values,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "seasonal_pattern": self.seasonal_pattern,
        }


@dataclass
class ThemeRelationship:
    """Relationship between themes"""

    theme1_id: str
    theme2_id: str
    relationship_type: str  # co_occurrence, semantic, temporal
    strength: float
    confidence: float
    context_examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme1_id": self.theme1_id,
            "theme2_id": self.theme2_id,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "confidence": self.confidence,
            "context_examples": self.context_examples[:5],
        }


class ThemeExtractionService:
    """Advanced theme extraction and analysis service"""

    def __init__(self, nlp_service: NLPService | None = None):
        self.nlp_service = nlp_service or NLPService()

        # Configuration
        self.config = {
            "min_theme_frequency": 3,
            "max_num_themes": 20,
            "similarity_threshold": 0.7,
            "trend_window_days": 30,
            "sentiment_threshold": 0.1,
        }

        # Caches for performance
        self._theme_cache = {}
        self._similarity_cache = {}
        self._cache_ttl = 3600  # 1 hour

        # Statistical models
        self._tfidf_vectorizer = None
        self._theme_embeddings = {}

        logger.info("Theme Extraction Service initialized")

    async def extract_themes(
        self,
        texts: list[str],
        method: ThemeExtractionMethod = ThemeExtractionMethod.HYBRID,
        num_themes: int | None = None,
        time_metadata: list[datetime] | None = None,
        metadata: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Extract themes from a collection of texts"""
        try:
            start_time = datetime.utcnow()

            # Validate inputs
            if not texts:
                return {"themes": [], "metadata": {"error": "No texts provided"}}

            if time_metadata and len(time_metadata) != len(texts):
                raise ValueError("time_metadata must have same length as texts")

            # Preprocess texts
            processed_texts = await self._preprocess_texts(texts)

            # Extract themes using specified method
            if method == ThemeExtractionMethod.FREQUENCY:
                themes = await self._extract_themes_frequency(
                    processed_texts, num_themes
                )
            elif method == ThemeExtractionMethod.TFIDF:
                themes = await self._extract_themes_tfidf(processed_texts, num_themes)
            elif method == ThemeExtractionMethod.TOPIC_MODELING:
                themes = await self._extract_themes_topic_modeling(
                    processed_texts, num_themes
                )
            elif method == ThemeExtractionMethod.CLUSTERING:
                themes = await self._extract_themes_clustering(
                    processed_texts, num_themes
                )
            elif method == ThemeExtractionMethod.HYBRID:
                themes = await self._extract_themes_hybrid(processed_texts, num_themes)
            else:
                raise ValueError(f"Unsupported theme extraction method: {method}")

            # Analyze theme relationships
            relationships = await self._analyze_theme_relationships(
                themes, processed_texts
            )

            # Temporal analysis if time metadata provided
            trends = []
            if time_metadata:
                trends = await self._analyze_theme_trends(themes, texts, time_metadata)

            # Create theme clusters
            clusters = await self._cluster_themes(themes)

            # Calculate theme statistics
            theme_stats = await self._calculate_theme_statistics(themes, texts)

            # Classify themes by type
            classified_themes = await self._classify_themes(themes)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            return {
                "themes": [theme.to_dict() for theme in classified_themes],
                "relationships": [rel.to_dict() for rel in relationships],
                "trends": [trend.to_dict() for trend in trends],
                "clusters": [cluster.to_dict() for cluster in clusters],
                "statistics": theme_stats,
                "metadata": {
                    "method": method.value,
                    "num_texts": len(texts),
                    "num_themes": len(themes),
                    "processing_time_seconds": processing_time,
                    "extraction_timestamp": start_time.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Theme extraction failed: {e!s}")
            return {"themes": [], "metadata": {"error": str(e)}}

    async def _extract_themes_frequency(
        self, texts: list[str], num_themes: int | None = None
    ) -> list[Theme]:
        """Extract themes using frequency-based analysis"""
        try:
            # Analyze word frequency across all texts
            word_frequencies = await self.nlp_service.analyze_word_frequency(texts)

            # Group related words into themes
            themes = []
            theme_keywords = set()

            for freq in word_frequencies[: num_themes or self.config["max_num_themes"]]:
                if freq.word in theme_keywords:
                    continue

                # Find related words based on co-occurrence and similarity
                related_words = await self._find_related_words(
                    freq.word, word_frequencies, texts
                )

                if len(related_words) >= 2:  # Need at least 2 related words for a theme
                    theme_id = f"freq_theme_{len(themes)}"
                    theme_name = self._generate_theme_name_from_words(
                        [freq.word] + related_words[:3]
                    )

                    # Calculate sentiment distribution
                    sentiment_dist = await self._calculate_theme_sentiment(
                        [freq.word] + related_words, texts
                    )

                    # Find example sentences
                    examples = await self._find_theme_examples(
                        [freq.word] + related_words, texts
                    )

                    theme = Theme(
                        id=theme_id,
                        name=theme_name,
                        keywords=[freq.word] + related_words[:5],
                        frequency=freq.frequency
                        + sum(
                            f.frequency
                            for f in word_frequencies
                            if f.word in related_words
                        ),
                        relevance_score=freq.normalized_frequency,
                        examples=examples,
                        sentiment_distribution=sentiment_dist,
                    )

                    themes.append(theme)
                    theme_keywords.update([freq.word] + related_words)

            return themes

        except Exception as e:
            logger.error(f"Frequency-based theme extraction failed: {e!s}")
            return []

    async def _extract_themes_tfidf(
        self, texts: list[str], num_themes: int | None = None
    ) -> list[Theme]:
        """Extract themes using TF-IDF analysis"""
        try:
            # Initialize TF-IDF vectorizer
            if self._tfidf_vectorizer is None:
                self._tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words="english",
                    ngram_range=(1, 3),
                    min_df=2,
                    max_df=0.8,
                )

            # Fit and transform texts
            tfidf_matrix = self._tfidf_vectorizer.fit_transform(texts)
            feature_names = self._tfidf_vectorizer.get_feature_names_out()

            # Calculate average TF-IDF scores for each term
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)

            # Get top terms by TF-IDF score
            top_indices = np.argsort(mean_scores)[::-1][
                : num_themes or self.config["max_num_themes"]
            ]

            themes = []
            for idx in top_indices:
                term = feature_names[idx]
                score = mean_scores[idx]

                if score < self.config["similarity_threshold"]:
                    continue

                # Split compound terms
                keywords = term.split()

                # Find examples containing this term
                examples = await self._find_theme_examples(keywords, texts)

                # Calculate sentiment distribution
                sentiment_dist = await self._calculate_theme_sentiment(keywords, texts)

                theme_id = f"tfidf_theme_{len(themes)}"
                theme_name = term.replace("_", " ").title()

                theme = Theme(
                    id=theme_id,
                    name=theme_name,
                    keywords=keywords,
                    frequency=int(score * len(texts)),  # Approximate frequency
                    relevance_score=score,
                    examples=examples,
                    sentiment_distribution=sentiment_dist,
                )

                themes.append(theme)

            return themes

        except Exception as e:
            logger.error(f"TF-IDF theme extraction failed: {e!s}")
            return []

    async def _extract_themes_topic_modeling(
        self, texts: list[str], num_themes: int | None = None
    ) -> list[Theme]:
        """Extract themes using topic modeling (LDA)"""
        try:
            # Use NLP service for LDA-based theme extraction
            themes = []
            num_topics = num_themes or min(10, len(texts) // 3)

            for i, text in enumerate(
                texts[: num_topics * 5]
            ):  # Sample texts for processing
                try:
                    # Extract themes from individual text using LDA
                    text_themes = await self.nlp_service.extract_themes(
                        text, num_themes=3, method="topic_modeling"
                    )

                    for theme in text_themes:
                        # Check if similar theme already exists
                        existing_theme = await self._find_similar_theme(theme, themes)
                        if existing_theme:
                            # Merge with existing theme
                            existing_theme.frequency += theme.frequency
                            existing_theme.examples.extend(theme.examples[:2])
                        else:
                            # Add as new theme with unique ID
                            new_theme = Theme(
                                id=f"topic_theme_{len(themes)}_{i}",
                                name=theme.name,
                                keywords=theme.keywords,
                                frequency=theme.frequency,
                                relevance_score=theme.relevance_score,
                                examples=theme.examples,
                                sentiment_distribution=theme.sentiment_distribution,
                            )
                            themes.append(new_theme)

                except Exception as e:
                    logger.warning(
                        f"Failed to process text {i} for topic modeling: {e!s}"
                    )
                    continue

            # Sort by relevance and limit
            themes.sort(key=lambda t: t.relevance_score, reverse=True)
            return themes[: num_themes or self.config["max_num_themes"]]

        except Exception as e:
            logger.error(f"Topic modeling theme extraction failed: {e!s}")
            return []

    async def _extract_themes_clustering(
        self, texts: list[str], num_themes: int | None = None
    ) -> list[Theme]:
        """Extract themes using clustering analysis"""
        try:
            # Initialize TF-IDF for clustering
            vectorizer = TfidfVectorizer(
                max_features=500, stop_words="english", ngram_range=(1, 2), min_df=2
            )

            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            # Perform K-means clustering
            n_clusters = min(num_themes or 10, len(texts) // 2)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)

            # Extract themes from clusters
            themes = []
            for cluster_id in range(n_clusters):
                # Get texts in this cluster
                cluster_texts = [
                    texts[i]
                    for i in range(len(texts))
                    if cluster_labels[i] == cluster_id
                ]

                if len(cluster_texts) < 2:
                    continue

                # Combine cluster texts and extract key terms
                combined_text = " ".join(cluster_texts)

                # Get top terms for this cluster
                cluster_center = kmeans.cluster_centers_[cluster_id]
                top_indices = np.argsort(cluster_center)[::-1][:10]
                top_terms = [feature_names[i] for i in top_indices]

                if not top_terms:
                    continue

                # Create theme from cluster
                theme_name = self._generate_theme_name_from_words(top_terms[:3])
                keywords = [
                    term.replace("_", " ").split()[0] for term in top_terms[:5]
                ]  # First words only

                # Find examples
                examples = await self._find_theme_examples(keywords[:3], cluster_texts)

                # Calculate sentiment
                sentiment_dist = await self._calculate_theme_sentiment(
                    keywords, cluster_texts
                )

                theme = Theme(
                    id=f"cluster_theme_{cluster_id}",
                    name=theme_name,
                    keywords=keywords,
                    frequency=len(cluster_texts),
                    relevance_score=float(np.max(cluster_center)),
                    examples=examples,
                    sentiment_distribution=sentiment_dist,
                )

                themes.append(theme)

            # Sort by relevance
            themes.sort(key=lambda t: t.relevance_score, reverse=True)
            return themes[: num_themes or self.config["max_num_themes"]]

        except Exception as e:
            logger.error(f"Clustering theme extraction failed: {e!s}")
            return []

    async def _extract_themes_hybrid(
        self, texts: list[str], num_themes: int | None = None
    ) -> list[Theme]:
        """Extract themes using hybrid approach combining multiple methods"""
        try:
            # Extract themes using multiple methods
            frequency_themes = await self._extract_themes_frequency(texts, num_themes)
            tfidf_themes = await self._extract_themes_tfidf(texts, num_themes)
            clustering_themes = await self._extract_themes_clustering(texts, num_themes)

            # Combine and deduplicate themes
            all_themes = frequency_themes + tfidf_themes + clustering_themes

            # Group similar themes
            merged_themes = []
            for theme in all_themes:
                similar_theme = await self._find_similar_theme(theme, merged_themes)

                if similar_theme:
                    # Merge themes
                    await self._merge_themes(similar_theme, theme)
                else:
                    merged_themes.append(theme)

            # Calculate final relevance scores
            for theme in merged_themes:
                theme.relevance_score = await self._calculate_theme_relevance(
                    theme, texts
                )

            # Sort by relevance and limit
            merged_themes.sort(key=lambda t: t.relevance_score, reverse=True)
            return merged_themes[: num_themes or self.config["max_num_themes"]]

        except Exception as e:
            logger.error(f"Hybrid theme extraction failed: {e!s}")
            return []

    async def _analyze_theme_relationships(
        self, themes: list[Theme], texts: list[str]
    ) -> list[ThemeRelationship]:
        """Analyze relationships between themes"""
        try:
            relationships = []

            # Co-occurrence analysis
            co_occurrence_matrix = await self._calculate_co_occurrence_matrix(
                themes, texts
            )

            for i, theme1 in enumerate(themes):
                for j, theme2 in enumerate(themes[i + 1 :], i + 1):
                    co_occurrence = co_occurrence_matrix[i][j]

                    if co_occurrence > 0:
                        # Calculate relationship strength
                        strength = co_occurrence / len(texts)
                        confidence = min(1.0, strength * 2)  # Normalize confidence

                        if strength > 0.1:  # Threshold for meaningful relationship
                            # Find context examples
                            context_examples = await self._find_co_occurrence_examples(
                                theme1.keywords[:2], theme2.keywords[:2], texts
                            )

                            relationship = ThemeRelationship(
                                theme1_id=theme1.id,
                                theme2_id=theme2.id,
                                relationship_type="co_occurrence",
                                strength=strength,
                                confidence=confidence,
                                context_examples=context_examples,
                            )

                            relationships.append(relationship)

            return relationships

        except Exception as e:
            logger.error(f"Theme relationship analysis failed: {e!s}")
            return []

    async def _analyze_theme_trends(
        self, themes: list[Theme], texts: list[str], timestamps: list[datetime]
    ) -> list[ThemeTrend]:
        """Analyze temporal trends of themes"""
        try:
            trends = []

            # Create time buckets (daily)
            time_buckets = {}
            for text, timestamp in zip(texts, timestamps):
                date_key = timestamp.date()
                if date_key not in time_buckets:
                    time_buckets[date_key] = []
                time_buckets[date_key].append(text)

            # Analyze each theme over time
            for theme in themes:
                time_points = []
                frequency_values = []
                sentiment_values = []

                for date in sorted(time_buckets.keys()):
                    day_texts = time_buckets[date]

                    # Calculate theme frequency for this day
                    freq = await self._calculate_theme_frequency_in_texts(
                        theme, day_texts
                    )

                    # Calculate average sentiment for this day
                    sentiment = await self._calculate_theme_sentiment(
                        theme.keywords, day_texts
                    )
                    avg_sentiment = sentiment.get("positive", 0) - sentiment.get(
                        "negative", 0
                    )

                    time_points.append(datetime.combine(date, datetime.min.time()))
                    frequency_values.append(freq)
                    sentiment_values.append(avg_sentiment)

                if len(time_points) >= 3:  # Need at least 3 points for trend analysis
                    # Calculate trend direction and strength
                    trend_direction, trend_strength = self._calculate_trend(
                        frequency_values
                    )

                    # Check for seasonal patterns
                    seasonal_pattern = self._detect_seasonal_pattern(
                        time_points, frequency_values
                    )

                    trend = ThemeTrend(
                        theme_id=theme.id,
                        theme_name=theme.name,
                        time_points=time_points,
                        frequency_values=frequency_values,
                        sentiment_values=sentiment_values,
                        trend_direction=trend_direction,
                        trend_strength=trend_strength,
                        seasonal_pattern=seasonal_pattern,
                    )

                    trends.append(trend)

            return trends

        except Exception as e:
            logger.error(f"Theme trend analysis failed: {e!s}")
            return []

    async def _cluster_themes(self, themes: list[Theme]) -> list[ThemeCluster]:
        """Cluster related themes together"""
        try:
            if len(themes) < 2:
                return []

            # Create theme vectors based on keywords
            theme_vectors = []
            for theme in themes:
                # Simple keyword overlap vector
                vector = [0.0] * len(themes)
                for i, other_theme in enumerate(themes):
                    if theme.id == other_theme.id:
                        vector[i] = 1.0
                    else:
                        # Calculate keyword overlap
                        overlap = len(set(theme.keywords) & set(other_theme.keywords))
                        total = len(set(theme.keywords) | set(other_theme.keywords))
                        vector[i] = overlap / total if total > 0 else 0.0
                theme_vectors.append(vector)

            # Perform clustering
            n_clusters = min(5, len(themes) // 2)
            if n_clusters < 2:
                return []

            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(theme_vectors)

            # Create theme clusters
            clusters = []
            for cluster_id in range(n_clusters):
                cluster_themes = [
                    themes[i]
                    for i in range(len(themes))
                    if cluster_labels[i] == cluster_id
                ]

                if len(cluster_themes) < 2:
                    continue

                # Calculate cluster metrics
                centrality_score = self._calculate_cluster_centrality(
                    cluster_themes, kmeans.cluster_centers_[cluster_id]
                )
                coherence_score = self._calculate_cluster_coherence(cluster_themes)

                # Get dominant sentiment
                all_sentiments = []
                for theme in cluster_themes:
                    for sentiment, score in theme.sentiment_distribution.items():
                        all_sentiments.append((sentiment, score))

                dominant_sentiment = (
                    max(
                        Counter(
                            s
                            for s, score in all_sentiments
                            for _ in range(int(score * 10))
                        ),
                        key=Counter().get,
                    )
                    if all_sentiments
                    else "neutral"
                )

                cluster = ThemeCluster(
                    cluster_id=f"cluster_{cluster_id}",
                    name=self._generate_cluster_name(cluster_themes),
                    themes=cluster_themes,
                    centrality_score=centrality_score,
                    coherence_score=coherence_score,
                    dominant_sentiment=dominant_sentiment,
                )

                clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"Theme clustering failed: {e!s}")
            return []

    async def _classify_themes(self, themes: list[Theme]) -> list[Theme]:
        """Classify themes by type (concept, emotion, action, etc.)"""
        try:
            emotion_keywords = {
                "happy",
                "sad",
                "angry",
                "love",
                "hate",
                "fear",
                "joy",
                "excitement",
                "anxiety",
                "depression",
                "contentment",
                "frustration",
                "worry",
                "hope",
            }

            action_keywords = {
                "work",
                "play",
                "run",
                "jump",
                "sleep",
                "eat",
                "drink",
                "drive",
                "write",
                "read",
                "think",
                "create",
                "destroy",
                "build",
                "learn",
            }

            for theme in themes:
                theme_words = set(word.lower() for word in theme.keywords)

                # Classify based on keyword overlap
                emotion_overlap = (
                    len(theme_words & emotion_keywords) / len(theme_words)
                    if theme_words
                    else 0
                )
                action_overlap = (
                    len(theme_words & action_keywords) / len(theme_words)
                    if theme_words
                    else 0
                )

                # Add theme type as metadata (extend the Theme class if needed)
                if emotion_overlap > 0.3:
                    theme.metadata = getattr(theme, "metadata", {})
                    theme.metadata["type"] = "emotion"
                elif action_overlap > 0.3:
                    theme.metadata = getattr(theme, "metadata", {})
                    theme.metadata["type"] = "action"
                else:
                    theme.metadata = getattr(theme, "metadata", {})
                    theme.metadata["type"] = "concept"

            return themes

        except Exception as e:
            logger.error(f"Theme classification failed: {e!s}")
            return themes

    # Helper methods

    async def _preprocess_texts(self, texts: list[str]) -> list[str]:
        """Preprocess texts for theme extraction"""
        processed = []
        for text in texts:
            # Basic preprocessing
            text = re.sub(r"\s+", " ", text.strip())  # Normalize whitespace
            if len(text) > 10:  # Filter very short texts
                processed.append(text)
        return processed

    async def _find_related_words(
        self,
        target_word: str,
        word_frequencies: list,
        texts: list[str],
        max_related: int = 5,
    ) -> list[str]:
        """Find words related to target word"""
        try:
            target_word = target_word.lower()
            related_words = []

            # Find co-occurring words in texts
            co_occurrence_counts = Counter()

            for text in texts:
                words = set(text.lower().split())
                if target_word in words:
                    for word in words:
                        if word != target_word and len(word) > 2:
                            co_occurrence_counts[word] += 1

            # Get top co-occurring words
            for word, count in co_occurrence_counts.most_common(max_related):
                if count >= 2:  # Minimum co-occurrence threshold
                    related_words.append(word)

            return related_words

        except Exception as e:
            logger.error(f"Failed to find related words for {target_word}: {e!s}")
            return []

    async def _find_theme_examples(
        self, keywords: list[str], texts: list[str], max_examples: int = 3
    ) -> list[str]:
        """Find example sentences containing theme keywords"""
        try:
            examples = []
            keyword_set = set(kw.lower() for kw in keywords)

            for text in texts:
                # Split into sentences
                sentences = re.split(r"[.!?]+", text)

                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 20:  # Filter very short sentences
                        words = set(sentence.lower().split())
                        if keyword_set & words:  # Intersection not empty
                            examples.append(sentence)
                            if len(examples) >= max_examples:
                                return examples

            return examples

        except Exception as e:
            logger.error(f"Failed to find theme examples: {e!s}")
            return []

    async def _calculate_theme_sentiment(
        self, keywords: list[str], texts: list[str]
    ) -> dict[str, float]:
        """Calculate sentiment distribution for theme"""
        try:
            sentiment_scores = []

            for text in texts:
                # Check if text contains theme keywords
                text_lower = text.lower()
                if any(kw.lower() in text_lower for kw in keywords):
                    # Analyze sentiment
                    sentiment = await self.nlp_service.analyze_sentiment(text)
                    sentiment_scores.append(sentiment.polarity)

            if not sentiment_scores:
                return {"neutral": 1.0}

            # Calculate distribution
            positive = sum(1 for s in sentiment_scores if s > 0.1) / len(
                sentiment_scores
            )
            negative = sum(1 for s in sentiment_scores if s < -0.1) / len(
                sentiment_scores
            )
            neutral = 1.0 - positive - negative

            return {
                "positive": positive,
                "negative": negative,
                "neutral": max(0.0, neutral),
            }

        except Exception as e:
            logger.error(f"Failed to calculate theme sentiment: {e!s}")
            return {"neutral": 1.0}

    def _generate_theme_name_from_words(self, words: list[str]) -> str:
        """Generate a readable theme name from keywords"""
        if not words:
            return "Unknown Theme"

        # Clean and capitalize words
        clean_words = [word.replace("_", " ").title() for word in words[:3]]

        if len(clean_words) == 1:
            return clean_words[0]
        if len(clean_words) == 2:
            return f"{clean_words[0]} & {clean_words[1]}"
        return f"{clean_words[0]}, {clean_words[1]} & {clean_words[2]}"

    async def _find_similar_theme(
        self, theme: Theme, existing_themes: list[Theme]
    ) -> Theme | None:
        """Find existing theme similar to given theme"""
        try:
            for existing in existing_themes:
                # Calculate keyword overlap
                overlap = len(set(theme.keywords) & set(existing.keywords))
                total = len(set(theme.keywords) | set(existing.keywords))
                similarity = overlap / total if total > 0 else 0

                if similarity > self.config["similarity_threshold"]:
                    return existing

            return None

        except Exception as e:
            logger.error(f"Failed to find similar theme: {e!s}")
            return None

    async def _merge_themes(self, base_theme: Theme, new_theme: Theme) -> None:
        """Merge new_theme into base_theme"""
        try:
            # Combine keywords
            base_theme.keywords = list(set(base_theme.keywords + new_theme.keywords))

            # Update frequency
            base_theme.frequency += new_theme.frequency

            # Combine examples
            base_theme.examples.extend(new_theme.examples)
            base_theme.examples = base_theme.examples[:5]  # Limit examples

            # Update relevance score (average)
            base_theme.relevance_score = (
                base_theme.relevance_score + new_theme.relevance_score
            ) / 2

        except Exception as e:
            logger.error(f"Failed to merge themes: {e!s}")

    async def _calculate_theme_relevance(self, theme: Theme, texts: list[str]) -> float:
        """Calculate relevance score for theme"""
        try:
            # Factors: frequency, diversity, uniqueness
            frequency_score = theme.frequency / len(texts)

            # Diversity: how many different texts contain this theme
            text_count = sum(
                1 for text in texts if any(kw in text.lower() for kw in theme.keywords)
            )
            diversity_score = text_count / len(texts)

            # Uniqueness: based on keyword uniqueness
            avg_word_freq = (
                sum(len(text.split()) for text in texts) / len(texts) if texts else 1
            )
            uniqueness_score = min(1.0, theme.frequency / avg_word_freq)

            # Combined score
            relevance = (
                frequency_score * 0.4 + diversity_score * 0.4 + uniqueness_score * 0.2
            )

            return min(1.0, relevance)

        except Exception as e:
            logger.error(f"Failed to calculate theme relevance: {e!s}")
            return 0.0

    def _calculate_trend(self, values: list[float]) -> tuple[str, float]:
        """Calculate trend direction and strength"""
        try:
            if len(values) < 3:
                return "insufficient_data", 0.0

            # Simple linear regression
            x = list(range(len(values)))
            n = len(values)

            # Calculate slope
            sum_x = sum(x)
            sum_y = sum(values)
            sum_xy = sum(x[i] * values[i] for i in range(n))
            sum_x2 = sum(xi * xi for xi in x)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            # Determine direction
            if slope > 0.01:
                direction = "increasing"
            elif slope < -0.01:
                direction = "decreasing"
            else:
                direction = "stable"

            # Calculate strength (normalized slope)
            strength = min(1.0, abs(slope) * 10)

            return direction, strength

        except Exception as e:
            logger.error(f"Failed to calculate trend: {e!s}")
            return "unknown", 0.0

    def _detect_seasonal_pattern(
        self, time_points: list[datetime], values: list[float]
    ) -> bool:
        """Detect if there's a seasonal pattern in the data"""
        try:
            if len(time_points) < 7:  # Need at least a week of data
                return False

            # Simple check for periodicity
            # This is a simplified implementation
            # A more sophisticated approach would use FFT or autocorrelation

            # Check for weekly patterns
            weekly_averages = defaultdict(list)
            for tp, val in zip(time_points, values):
                weekly_averages[tp.weekday()].append(val)

            # Calculate variance between days of week
            day_averages = [np.mean(vals) for vals in weekly_averages.values()]
            day_variance = np.var(day_averages) if day_averages else 0

            # If variance is significant, consider it seasonal
            total_variance = np.var(values)
            seasonal_ratio = day_variance / total_variance if total_variance > 0 else 0

            return seasonal_ratio > 0.3

        except Exception as e:
            logger.error(f"Failed to detect seasonal pattern: {e!s}")
            return False

    def _generate_cluster_name(self, themes: list[Theme]) -> str:
        """Generate name for theme cluster"""
        if not themes:
            return "Empty Cluster"

        # Use the most relevant theme's name as base
        main_theme = max(themes, key=lambda t: t.relevance_score)
        return f"{main_theme.name} Group"

    def _calculate_cluster_centrality(self, themes: list[Theme], center) -> float:
        """Calculate centrality score for cluster"""
        try:
            # Simple centrality based on average relevance
            return float(np.mean([theme.relevance_score for theme in themes]))
        except Exception:
            return 0.0

    def _calculate_cluster_coherence(self, themes: list[Theme]) -> float:
        """Calculate coherence score for cluster"""
        try:
            if len(themes) < 2:
                return 1.0

            # Calculate average keyword overlap
            total_overlap = 0
            comparisons = 0

            for i, theme1 in enumerate(themes):
                for theme2 in themes[i + 1 :]:
                    overlap = len(set(theme1.keywords) & set(theme2.keywords))
                    total = len(set(theme1.keywords) | set(theme2.keywords))
                    if total > 0:
                        total_overlap += overlap / total
                        comparisons += 1

            return total_overlap / comparisons if comparisons > 0 else 0.0

        except Exception:
            return 0.0

    async def _calculate_theme_statistics(
        self, themes: list[Theme], texts: list[str]
    ) -> dict[str, Any]:
        """Calculate overall theme statistics"""
        try:
            return {
                "total_themes": len(themes),
                "average_frequency": (
                    np.mean([theme.frequency for theme in themes]) if themes else 0
                ),
                "average_relevance": (
                    np.mean([theme.relevance_score for theme in themes])
                    if themes
                    else 0
                ),
                "theme_diversity": len(
                    set(kw for theme in themes for kw in theme.keywords)
                ),
                "sentiment_distribution": self._calculate_overall_sentiment(themes),
                "theme_types": self._get_theme_type_distribution(themes),
            }

        except Exception as e:
            logger.error(f"Failed to calculate theme statistics: {e!s}")
            return {}

    def _calculate_overall_sentiment(self, themes: list[Theme]) -> dict[str, float]:
        """Calculate overall sentiment distribution across themes"""
        try:
            all_sentiments = defaultdict(float)
            total_weight = 0

            for theme in themes:
                weight = theme.relevance_score
                for sentiment, score in theme.sentiment_distribution.items():
                    all_sentiments[sentiment] += score * weight
                total_weight += weight

            if total_weight > 0:
                return {
                    sentiment: score / total_weight
                    for sentiment, score in all_sentiments.items()
                }
            return {"neutral": 1.0}

        except Exception:
            return {"neutral": 1.0}

    def _get_theme_type_distribution(self, themes: list[Theme]) -> dict[str, int]:
        """Get distribution of theme types"""
        try:
            type_counts = defaultdict(int)
            for theme in themes:
                theme_type = (
                    getattr(theme.metadata, "type", "unknown")
                    if hasattr(theme, "metadata")
                    else "unknown"
                )
                type_counts[theme_type] += 1
            return dict(type_counts)
        except Exception:
            return {"unknown": len(themes)}

    async def _calculate_co_occurrence_matrix(
        self, themes: list[Theme], texts: list[str]
    ) -> list[list[float]]:
        """Calculate co-occurrence matrix for themes"""
        try:
            n = len(themes)
            matrix = [[0.0 for _ in range(n)] for _ in range(n)]

            for text in texts:
                text_lower = text.lower()
                present_themes = []

                for i, theme in enumerate(themes):
                    if any(kw in text_lower for kw in theme.keywords):
                        present_themes.append(i)

                # Update co-occurrence counts
                for i in present_themes:
                    for j in present_themes:
                        if i != j:
                            matrix[i][j] += 1

            # Normalize by total number of texts
            for i in range(n):
                for j in range(n):
                    matrix[i][j] /= len(texts)

            return matrix

        except Exception as e:
            logger.error(f"Failed to calculate co-occurrence matrix: {e!s}")
            return [[0.0] * len(themes) for _ in range(len(themes))]

    async def _find_co_occurrence_examples(
        self,
        keywords1: list[str],
        keywords2: list[str],
        texts: list[str],
        max_examples: int = 2,
    ) -> list[str]:
        """Find examples where both sets of keywords co-occur"""
        try:
            examples = []
            words1_set = set(kw.lower() for kw in keywords1)
            words2_set = set(kw.lower() for kw in keywords2)

            for text in texts:
                text_lower = text.lower()
                text_words = set(text_lower.split())

                if (words1_set & text_words) and (words2_set & text_words):
                    # Found co-occurrence
                    examples.append(text[:200] + "..." if len(text) > 200 else text)
                    if len(examples) >= max_examples:
                        break

            return examples

        except Exception as e:
            logger.error(f"Failed to find co-occurrence examples: {e!s}")
            return []

    async def _calculate_theme_frequency_in_texts(
        self, theme: Theme, texts: list[str]
    ) -> float:
        """Calculate how often theme appears in given texts"""
        try:
            count = 0
            for text in texts:
                text_lower = text.lower()
                if any(kw in text_lower for kw in theme.keywords):
                    count += 1

            return count / len(texts) if texts else 0.0

        except Exception as e:
            logger.error(f"Failed to calculate theme frequency: {e!s}")
            return 0.0


# Export the main service class
__all__ = [
    "ThemeCluster",
    "ThemeExtractionMethod",
    "ThemeExtractionService",
    "ThemeRelationship",
    "ThemeTrend",
    "ThemeType",
]
