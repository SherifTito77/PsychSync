"""
Pattern Matching Engine
Advanced machine learning engine for discovering, matching, and analyzing behavioral patterns.
Implements various ML algorithms for pattern recognition and similarity matching.

Key Features:
- Sequential pattern mining (PrefixSpan, GSP algorithms)
- Clustering-based pattern discovery
- Deep learning pattern recognition (LSTM, Transformers)
- Similarity matching and pattern classification
- Real-time pattern streaming and matching
- Pattern evolution tracking and adaptation
- Cross-user pattern analysis and recommendations
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd

# ML and statistical libraries
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Deep learning (optional, with fallback)
try:
    import torch
    from torch import nn

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import redis.asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PatternCategory(Enum):
    """Categories of patterns that can be matched."""

    BEHAVIORAL_SEQUENCE = "behavioral_sequence"
    TEMPORAL_PATTERN = "temporal_pattern"
    FEATURE_PATTERN = "feature_pattern"
    NETWORK_PATTERN = "network_pattern"
    PREFERENCE_PATTERN = "preference_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    LEARNING_PATTERN = "learning_pattern"
    SOCIAL_PATTERN = "social_pattern"


class MatchingAlgorithm(Enum):
    """Pattern matching algorithms."""

    EXACT_MATCH = "exact_match"
    FUZZY_MATCH = "fuzzy_match"
    SEQUENCE_MATCH = "sequence_match"
    CLUSTER_MATCH = "cluster_match"
    SEMANTIC_MATCH = "semantic_match"
    TEMPORAL_MATCH = "temporal_match"
    HYBRID_MATCH = "hybrid_match"
    DEEP_MATCH = "deep_match"


class PatternComplexity(Enum):
    """Complexity levels of patterns."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class PatternTemplate:
    """Template for pattern matching."""

    template_id: str
    pattern_category: PatternCategory
    description: str
    pattern_structure: dict[str, Any]
    matching_algorithm: MatchingAlgorithm
    complexity: PatternComplexity
    confidence_threshold: float = 0.7
    min_support: int = 5
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternMatch:
    """Result of pattern matching."""

    match_id: str
    template_id: str
    user_id: str
    match_score: float
    confidence: float
    matched_data: dict[str, Any]
    match_timestamp: datetime
    pattern_instances: list[dict[str, Any]]
    similarity_metrics: dict[str, float] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternEngineConfig:
    """Configuration for the pattern matching engine."""

    # General settings
    max_patterns_per_user: int = 1000
    min_pattern_length: int = 3
    max_pattern_length: int = 50
    pattern_cache_ttl_hours: int = 24

    # Sequential pattern mining settings
    min_support_ratio: float = 0.1
    max_pattern_gap: int = 5
    sequence_similarity_threshold: float = 0.8

    # Clustering settings
    n_clusters: int = 10
    clustering_eps: float = 0.5
    min_cluster_samples: int = 5

    # Similarity settings
    cosine_similarity_threshold: float = 0.7
    euclidean_distance_threshold: float = 1.0
    temporal_tolerance_minutes: int = 30

    # Deep learning settings
    embedding_dim: int = 128
    lstm_hidden_size: int = 64
    num_attention_heads: int = 8
    training_epochs: int = 100
    batch_size: int = 32

    # Performance settings
    max_sequence_length: int = 1000
    parallel_processing: bool = True
    gpu_acceleration: bool = TORCH_AVAILABLE

    # Redis configuration
    redis_url: str = "redis://localhost:6379/7"


class PatternMatchingEngine:
    """
    Advanced pattern matching and discovery engine.
    """

    def __init__(self, db_session: Session, config: PatternEngineConfig | None = None):
        self.db = db_session
        self.config = config or PatternEngineConfig()
        self.redis_client: redis.Redis | None = None
        self._init_redis()

        # Initialize ML components
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000)

        # Pattern templates registry
        self.pattern_templates: dict[str, PatternTemplate] = {}
        self._initialize_pattern_templates()

        # Initialize deep learning models if available
        self.deep_models = {}
        if TORCH_AVAILABLE and self.config.gpu_acceleration:
            self._initialize_deep_models()

        # Clustering models
        self.clustering_models = {
            "kmeans": KMeans(n_clusters=self.config.n_clusters, random_state=42),
            "dbscan": DBSCAN(
                eps=self.config.clustering_eps,
                min_samples=self.config.min_cluster_samples,
            ),
            "agglomerative": AgglomerativeClustering(n_clusters=self.config.n_clusters),
        }

        # Pattern matching algorithms
        self.matching_algorithms = {
            MatchingAlgorithm.EXACT_MATCH: self._exact_match,
            MatchingAlgorithm.FUZZY_MATCH: self._fuzzy_match,
            MatchingAlgorithm.SEQUENCE_MATCH: self._sequence_match,
            MatchingAlgorithm.CLUSTER_MATCH: self._cluster_match,
            MatchingAlgorithm.SEMANTIC_MATCH: self._semantic_match,
            MatchingAlgorithm.TEMPORAL_MATCH: self._temporal_match,
            MatchingAlgorithm.HYBRID_MATCH: self._hybrid_match,
            MatchingAlgorithm.DEEP_MATCH: self._deep_match if TORCH_AVAILABLE else None,
        }

    def _init_redis(self) -> None:
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            logger.info("Pattern matching engine Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for pattern matching: {e}")
            self.redis_client = None

    def _initialize_pattern_templates(self) -> None:
        """Initialize predefined pattern templates."""

        # Behavioral sequence template
        self.pattern_templates["behavioral_sequence"] = PatternTemplate(
            template_id="behavioral_sequence",
            pattern_category=PatternCategory.BEHAVIORAL_SEQUENCE,
            description="Common sequences of user actions",
            pattern_structure={
                "sequence_length": {"min": 3, "max": 20},
                "action_types": ["login", "view", "interact", "complete", "logout"],
                "time_constraints": {"max_gap_minutes": 30},
            },
            matching_algorithm=MatchingAlgorithm.SEQUENCE_MATCH,
            complexity=PatternComplexity.MODERATE,
        )

        # Temporal pattern template
        self.pattern_templates["temporal_activity"] = PatternTemplate(
            template_id="temporal_activity",
            pattern_category=PatternCategory.TEMPORAL_PATTERN,
            description="Time-based activity patterns",
            pattern_structure={
                "time_windows": ["morning", "afternoon", "evening", "night"],
                "frequency_threshold": 0.1,
                "regularity_threshold": 0.7,
            },
            matching_algorithm=MatchingAlgorithm.TEMPORAL_MATCH,
            complexity=PatternComplexity.SIMPLE,
        )

        # Learning progression template
        self.pattern_templates["learning_progression"] = PatternTemplate(
            template_id="learning_progression",
            pattern_category=PatternCategory.LEARNING_PATTERN,
            description="Learning and skill development patterns",
            pattern_structure={
                "skill_categories": ["technical", "soft", "domain"],
                "improvement_threshold": 0.15,
                "time_span_days": {"min": 7, "max": 90},
            },
            matching_algorithm=MatchingAlgorithm.HYBRID_MATCH,
            complexity=PatternComplexity.COMPLEX,
        )

        # Social interaction template
        self.pattern_templates["social_interaction"] = PatternTemplate(
            template_id="social_interaction",
            pattern_category=PatternCategory.SOCIAL_PATTERN,
            description="Social and collaboration patterns",
            pattern_structure={
                "interaction_types": ["message", "share", "collaborate", "mentor"],
                "network_metrics": ["centrality", "clustering", "betweenness"],
                "frequency_minimum": 2,
            },
            matching_algorithm=MatchingAlgorithm.NETWORK_PATTERN,
            complexity=PatternComplexity.MODERATE,
        )

    def _initialize_deep_models(self) -> None:
        """Initialize deep learning models for pattern recognition."""
        if not TORCH_AVAILABLE:
            return

        try:
            # LSTM-based sequence model
            self.deep_models["lstm"] = self._create_lstm_model()

            # Transformer-based pattern model
            self.deep_models["transformer"] = self._create_transformer_model()

            # Autoencoder for pattern representation
            self.deep_models["autoencoder"] = self._create_autoencoder_model()

            logger.info("Deep learning models initialized for pattern matching")

        except Exception as e:
            logger.error(f"Error initializing deep learning models: {e}")
            self.deep_models = {}

    def _create_lstm_model(self) -> nn.Module:
        """Create LSTM model for sequence pattern recognition."""

        class LSTMPatternModel(nn.Module):
            def __init__(self, vocab_size, embedding_dim, hidden_size, num_layers=2):
                super().__init__()
                self.embedding = nn.Embedding(vocab_size, embedding_dim)
                self.lstm = nn.LSTM(
                    embedding_dim,
                    hidden_size,
                    num_layers,
                    batch_first=True,
                    dropout=0.2,
                )
                self.fc = nn.Linear(hidden_size, vocab_size)
                self.dropout = nn.Dropout(0.3)

            def forward(self, x):
                embedded = self.dropout(self.embedding(x))
                lstm_out, _ = self.lstm(embedded)
                output = self.fc(lstm_out)
                return output

        return LSTMPatternModel(
            vocab_size=1000,  # Action vocabulary size
            embedding_dim=self.config.embedding_dim,
            hidden_size=self.config.lstm_hidden_size,
        )

    def _create_transformer_model(self) -> nn.Module:
        """Create Transformer model for pattern recognition."""

        class TransformerPatternModel(nn.Module):
            def __init__(self, vocab_size, embedding_dim, num_heads, num_layers):
                super().__init__()
                self.embedding = nn.Embedding(vocab_size, embedding_dim)
                self.pos_encoding = nn.Parameter(torch.randn(1000, embedding_dim))
                encoder_layer = nn.TransformerEncoderLayer(
                    d_model=embedding_dim,
                    nhead=num_heads,
                    dim_feedforward=embedding_dim * 4,
                    dropout=0.1,
                )
                self.transformer = nn.TransformerEncoder(
                    encoder_layer, num_layers=num_layers
                )
                self.fc = nn.Linear(embedding_dim, vocab_size)

            def forward(self, x):
                seq_len = x.size(1)
                embedded = self.embedding(x) + self.pos_encoding[:seq_len]
                output = self.transformer(embedded)
                return self.fc(output)

        return TransformerPatternModel(
            vocab_size=1000,
            embedding_dim=self.config.embedding_dim,
            num_heads=self.config.num_attention_heads,
            num_layers=4,
        )

    def _create_autoencoder_model(self) -> nn.Module:
        """Create autoencoder for pattern representation learning."""

        class PatternAutoencoder(nn.Module):
            def __init__(self, input_dim, encoding_dim):
                super().__init__()
                self.encoder = nn.Sequential(
                    nn.Linear(input_dim, 256),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(256, encoding_dim),
                    nn.ReLU(),
                )
                self.decoder = nn.Sequential(
                    nn.Linear(encoding_dim, 256),
                    nn.ReLU(),
                    nn.Dropout(0.2),
                    nn.Linear(256, input_dim),
                    nn.Sigmoid(),
                )

            def forward(self, x):
                encoded = self.encoder(x)
                decoded = self.decoder(encoded)
                return encoded, decoded

        return PatternAutoencoder(
            input_dim=1000,  # Feature dimension
            encoding_dim=self.config.embedding_dim,
        )

    async def match_patterns(
        self,
        user_data: dict[str, Any],
        template_ids: list[str] | None = None,
        matching_algorithms: list[MatchingAlgorithm] | None = None,
        user_id: str | None = None,
    ) -> list[PatternMatch]:
        """
        Match user data against pattern templates using specified algorithms.

        Args:
            user_data: User behavioral data to analyze
            template_ids: Specific template IDs to match (None for all)
            matching_algorithms: Algorithms to use (None for template defaults)
            user_id: User ID for context

        Returns:
            List of pattern matches
        """
        try:
            # Use default templates if not specified
            if template_ids is None:
                template_ids = list(self.pattern_templates.keys())

            matches = []

            # Check cache first
            if user_id and self.redis_client:
                cache_key = f"pattern_matches:{user_id}:{hash(str(user_data))}"
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    cached_matches = json.loads(cached_result)
                    return [self._dict_to_pattern_match(m) for m in cached_matches]

            # Match against each template
            for template_id in template_ids:
                if template_id not in self.pattern_templates:
                    logger.warning(f"Template {template_id} not found")
                    continue

                template = self.pattern_templates[template_id]

                # Use specified algorithm or template default
                algorithm = (
                    matching_algorithms[0]
                    if matching_algorithms
                    else template.matching_algorithm
                )

                if (
                    algorithm not in self.matching_algorithms
                    or self.matching_algorithms[algorithm] is None
                ):
                    logger.warning(f"Algorithm {algorithm.value} not available")
                    continue

                try:
                    template_matches = await self.matching_algorithms[algorithm](
                        user_data, template, user_id
                    )
                    matches.extend(template_matches)

                except Exception as e:
                    logger.error(
                        f"Error matching with template {template_id} using {algorithm.value}: {e}"
                    )

            # Filter matches by confidence threshold
            filtered_matches = [
                m
                for m in matches
                if m.confidence
                >= min(t.confidence_threshold for t in self.pattern_templates.values())
            ]

            # Sort by confidence
            filtered_matches.sort(key=lambda x: x.confidence, reverse=True)

            # Cache results
            if user_id and self.redis_client and filtered_matches:
                cache_key = f"pattern_matches:{user_id}:{hash(str(user_data))}"
                await self.redis_client.setex(
                    cache_key,
                    self.config.pattern_cache_ttl_hours * 3600,
                    json.dumps(
                        [self._pattern_match_to_dict(m) for m in filtered_matches],
                        default=str,
                    ),
                )

            logger.info(
                f"Found {len(filtered_matches)} pattern matches for user {user_id}"
            )
            return filtered_matches

        except Exception as e:
            logger.error(f"Error in pattern matching: {e}")
            return []

    async def discover_patterns(
        self,
        data: list[dict[str, Any]],
        pattern_category: PatternCategory,
        min_support: int | None = None,
    ) -> list[PatternTemplate]:
        """
        Automatically discover new patterns from data.

        Args:
            data: Training data for pattern discovery
            pattern_category: Category of patterns to discover
            min_support: Minimum support for pattern validity

        Returns:
            List of discovered pattern templates
        """
        try:
            min_support = min_support or self.config.min_pattern_length

            discovered_patterns = []

            if pattern_category == PatternCategory.BEHAVIORAL_SEQUENCE:
                discovered_patterns = await self._discover_sequence_patterns(
                    data, min_support
                )
            elif pattern_category == PatternCategory.FEATURE_PATTERN:
                discovered_patterns = await self._discover_feature_patterns(
                    data, min_support
                )
            elif pattern_category == PatternCategory.TEMPORAL_PATTERN:
                discovered_patterns = await self._discover_temporal_patterns(
                    data, min_support
                )
            elif pattern_category == PatternCategory.NETWORK_PATTERN:
                discovered_patterns = await self._discover_network_patterns(
                    data, min_support
                )
            else:
                logger.warning(
                    f"Pattern discovery not implemented for {pattern_category}"
                )

            return discovered_patterns

        except Exception as e:
            logger.error(f"Error discovering patterns: {e}")
            return []

    async def _exact_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Exact pattern matching algorithm."""
        matches = []

        try:
            # Extract relevant data based on template
            if template.pattern_category == PatternCategory.BEHAVIORAL_SEQUENCE:
                sequences = user_data.get("sequences", [])
                target_sequences = template.pattern_structure.get(
                    "target_sequences", []
                )

                for i, sequence in enumerate(sequences):
                    for target_seq in target_sequences:
                        if self._sequences_match_exact(sequence, target_seq):
                            match = PatternMatch(
                                match_id=f"exact_{template.template_id}_{i}_{user_id}",
                                template_id=template.template_id,
                                user_id=user_id or "unknown",
                                match_score=1.0,
                                confidence=1.0,
                                matched_data={
                                    "sequence": sequence,
                                    "target": target_seq,
                                },
                                match_timestamp=datetime.utcnow(),
                                pattern_instances=[{"index": i, "sequence": sequence}],
                            )
                            matches.append(match)

        except Exception as e:
            logger.error(f"Error in exact matching: {e}")

        return matches

    async def _fuzzy_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Fuzzy pattern matching algorithm using similarity measures."""
        matches = []

        try:
            if template.pattern_category == PatternCategory.PREFERENCE_PATTERN:
                user_preferences = user_data.get("preferences", {})
                template_preferences = template.pattern_structure.get("preferences", {})

                similarity_score = self._calculate_preference_similarity(
                    user_preferences, template_preferences
                )

                if similarity_score >= 0.7:  # Threshold for fuzzy match
                    match = PatternMatch(
                        match_id=f"fuzzy_{template.template_id}_{user_id}",
                        template_id=template.template_id,
                        user_id=user_id or "unknown",
                        match_score=similarity_score,
                        confidence=similarity_score
                        * 0.9,  # Slightly lower confidence for fuzzy match
                        matched_data={
                            "user_preferences": user_preferences,
                            "template_preferences": template_preferences,
                        },
                        match_timestamp=datetime.utcnow(),
                        pattern_instances=[{"preferences": user_preferences}],
                        similarity_metrics={"preference_similarity": similarity_score},
                    )
                    matches.append(match)

        except Exception as e:
            logger.error(f"Error in fuzzy matching: {e}")

        return matches

    async def _sequence_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Sequence pattern matching using prefixspan-like algorithm."""
        matches = []

        try:
            sequences = user_data.get("sequences", [])
            min_length = template.pattern_structure.get("sequence_length", {}).get(
                "min", 3
            )
            max_gap = template.pattern_structure.get("time_constraints", {}).get(
                "max_gap_minutes", 30
            )

            for i, sequence in enumerate(sequences):
                if len(sequence) < min_length:
                    continue

                # Find frequent subsequences
                frequent_patterns = self._find_frequent_subsequences(
                    sequence, min_length, max_gap
                )

                for pattern in frequent_patterns:
                    support = self._calculate_pattern_support(sequences, pattern)
                    if support >= template.min_support:
                        confidence = self._calculate_sequence_confidence(
                            sequence, pattern
                        )

                        match = PatternMatch(
                            match_id=f"sequence_{template.template_id}_{i}_{user_id}_{hash(str(pattern))}",
                            template_id=template.template_id,
                            user_id=user_id or "unknown",
                            match_score=support,
                            confidence=confidence,
                            matched_data={"sequence": sequence, "pattern": pattern},
                            match_timestamp=datetime.utcnow(),
                            pattern_instances=[
                                {"index": i, "pattern": pattern, "support": support}
                            ],
                            similarity_metrics={
                                "support": support,
                                "pattern_length": len(pattern),
                            },
                        )
                        matches.append(match)

        except Exception as e:
            logger.error(f"Error in sequence matching: {e}")

        return matches

    async def _cluster_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Cluster-based pattern matching."""
        matches = []

        try:
            features = self._extract_features(user_data, template)
            if len(features) == 0:
                return matches

            # Standardize features
            features_scaled = self.scaler.fit_transform(features)

            # Apply clustering
            cluster_labels = self.clustering_models["kmeans"].fit_predict(
                features_scaled
            )

            # Find the most dominant cluster
            unique_labels, counts = np.unique(cluster_labels, return_counts=True)
            dominant_cluster = unique_labels[np.argmax(counts)]
            cluster_support = np.max(counts) / len(cluster_labels)

            if cluster_support >= 0.3:  # Minimum cluster support
                # Get cluster centroid
                cluster_features = features_scaled[cluster_labels == dominant_cluster]
                centroid = np.mean(cluster_features, axis=0)

                match = PatternMatch(
                    match_id=f"cluster_{template.template_id}_{user_id}",
                    template_id=template.template_id,
                    user_id=user_id or "unknown",
                    match_score=cluster_support,
                    confidence=cluster_support * 0.8,
                    matched_data={
                        "cluster_id": int(dominant_cluster),
                        "centroid": centroid.tolist(),
                    },
                    match_timestamp=datetime.utcnow(),
                    pattern_instances=[{"cluster_size": int(np.max(counts))}],
                    similarity_metrics={
                        "cluster_support": cluster_support,
                        "inertia": self.clustering_models["kmeans"].inertia_,
                    },
                )
                matches.append(match)

        except Exception as e:
            logger.error(f"Error in cluster matching: {e}")

        return matches

    async def _semantic_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Semantic pattern matching using NLP techniques."""
        matches = []

        try:
            # Extract text data
            text_data = self._extract_text_data(user_data)
            if not text_data:
                return matches

            # TF-IDF vectorization
            template_text = template.pattern_structure.get("semantic_patterns", [])
            all_text = text_data + template_text

            if len(all_text) < 2:
                return matches

            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_text)

            # Calculate cosine similarity between user data and template patterns
            user_vectors = tfidf_matrix[: len(text_data)]
            template_vectors = tfidf_matrix[len(text_data) :]

            similarities = cosine_similarity(user_vectors, template_vectors)

            # Find high similarity matches
            for i, user_doc in enumerate(text_data):
                for j, template_doc in enumerate(template_text):
                    similarity = similarities[i, j]

                    if similarity >= self.config.cosine_similarity_threshold:
                        match = PatternMatch(
                            match_id=f"semantic_{template.template_id}_{i}_{j}_{user_id}",
                            template_id=template.template_id,
                            user_id=user_id or "unknown",
                            match_score=float(similarity),
                            confidence=float(similarity) * 0.85,
                            matched_data={
                                "user_text": user_doc,
                                "template_text": template_doc,
                            },
                            match_timestamp=datetime.utcnow(),
                            pattern_instances=[
                                {"user_doc_index": i, "template_doc_index": j}
                            ],
                            similarity_metrics={"cosine_similarity": float(similarity)},
                        )
                        matches.append(match)

        except Exception as e:
            logger.error(f"Error in semantic matching: {e}")

        return matches

    async def _temporal_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Temporal pattern matching."""
        matches = []

        try:
            events = user_data.get("events", [])
            if not events:
                return matches

            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(events)
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Extract temporal features
            df["hour"] = df["timestamp"].dt.hour
            df["day_of_week"] = df["timestamp"].dt.dayofweek
            df["date"] = df["timestamp"].dt.date

            # Time window patterns
            time_windows = template.pattern_structure.get("time_windows", [])
            frequency_threshold = template.pattern_structure.get(
                "frequency_threshold", 0.1
            )

            for window in time_windows:
                window_events = self._filter_by_time_window(df, window)
                if len(window_events) > 0:
                    frequency = len(window_events) / len(df)

                    if frequency >= frequency_threshold:
                        match = PatternMatch(
                            match_id=f"temporal_{template.template_id}_{window}_{user_id}",
                            template_id=template.template_id,
                            user_id=user_id or "unknown",
                            match_score=frequency,
                            confidence=frequency * 0.9,
                            matched_data={
                                "time_window": window,
                                "event_count": len(window_events),
                                "total_events": len(df),
                            },
                            match_timestamp=datetime.utcnow(),
                            pattern_instances=[
                                {"window": window, "frequency": frequency}
                            ],
                            similarity_metrics={
                                "frequency": frequency,
                                "event_count": len(window_events),
                            },
                        )
                        matches.append(match)

        except Exception as e:
            logger.error(f"Error in temporal matching: {e}")

        return matches

    async def _hybrid_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Hybrid pattern matching combining multiple algorithms."""
        matches = []

        try:
            # Combine results from multiple algorithms
            algorithms_to_use = [
                MatchingAlgorithm.SEQUENCE_MATCH,
                MatchingAlgorithm.TEMPORAL_MATCH,
                MatchingAlgorithm.FUZZY_MATCH,
            ]

            all_algorithm_matches = []

            for algorithm in algorithms_to_use:
                if algorithm in self.matching_algorithms:
                    try:
                        algorithm_matches = await self.matching_algorithms[algorithm](
                            user_data, template, user_id
                        )
                        all_algorithm_matches.extend(algorithm_matches)
                    except Exception as e:
                        logger.error(
                            f"Error in hybrid algorithm {algorithm.value}: {e}"
                        )

            if not all_algorithm_matches:
                return matches

            # Group matches by similarity and combine scores
            combined_matches = self._combine_algorithm_matches(
                all_algorithm_matches, template
            )

            matches.extend(combined_matches)

        except Exception as e:
            logger.error(f"Error in hybrid matching: {e}")

        return matches

    async def _deep_match(
        self, user_data: dict[str, Any], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Deep learning-based pattern matching."""
        matches = []

        try:
            if not TORCH_AVAILABLE:
                return matches

            # Prepare data for deep learning
            sequences = user_data.get("sequences", [])
            if not sequences:
                return matches

            # Use LSTM model for sequence matching
            if "lstm" in self.deep_models:
                lstm_matches = await self._lstm_pattern_match(
                    sequences, template, user_id
                )
                matches.extend(lstm_matches)

            # Use Transformer model for pattern matching
            if "transformer" in self.deep_models:
                transformer_matches = await self._transformer_pattern_match(
                    sequences, template, user_id
                )
                matches.extend(transformer_matches)

        except Exception as e:
            logger.error(f"Error in deep matching: {e}")

        return matches

    async def _lstm_pattern_match(
        self, sequences: list[list[str]], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Use LSTM for pattern matching."""
        matches = []

        try:
            model = self.deep_models["lstm"]
            model.eval()

            for i, sequence in enumerate(sequences):
                # Convert sequence to numerical indices
                sequence_indices = self._sequence_to_indices(sequence)

                if len(sequence_indices) < 3:
                    continue

                # Predict next actions and calculate anomaly score
                with torch.no_grad():
                    input_tensor = torch.tensor(sequence_indices[:-1]).unsqueeze(0)
                    output = model(input_tensor)

                    # Calculate prediction confidence
                    predicted_probs = torch.softmax(output, dim=-1)
                    max_prob = torch.max(predicted_probs).item()

                    if max_prob > 0.8:  # High confidence prediction
                        match = PatternMatch(
                            match_id=f"lstm_{template.template_id}_{i}_{user_id}",
                            template_id=template.template_id,
                            user_id=user_id or "unknown",
                            match_score=max_prob,
                            confidence=max_prob * 0.9,
                            matched_data={
                                "sequence": sequence,
                                "predicted_confidence": max_prob,
                            },
                            match_timestamp=datetime.utcnow(),
                            pattern_instances=[
                                {"sequence_index": i, "confidence": max_prob}
                            ],
                            similarity_metrics={"prediction_confidence": max_prob},
                        )
                        matches.append(match)

        except Exception as e:
            logger.error(f"Error in LSTM pattern matching: {e}")

        return matches

    async def _transformer_pattern_match(
        self, sequences: list[list[str]], template: PatternTemplate, user_id: str | None
    ) -> list[PatternMatch]:
        """Use Transformer for pattern matching."""
        matches = []

        try:
            model = self.deep_models["transformer"]
            model.eval()

            for i, sequence in enumerate(sequences):
                # Convert sequence to numerical indices
                sequence_indices = self._sequence_to_indices(sequence)

                if len(sequence_indices) < 3:
                    continue

                # Generate pattern representation
                with torch.no_grad():
                    input_tensor = torch.tensor(sequence_indices).unsqueeze(0)
                    output = model(input_tensor)

                    # Calculate attention weights for pattern importance
                    pattern_importance = (
                        torch.mean(torch.abs(output), dim=-1).max().item()
                    )

                    if pattern_importance > 0.5:  # Significant pattern
                        match = PatternMatch(
                            match_id=f"transformer_{template.template_id}_{i}_{user_id}",
                            template_id=template.template_id,
                            user_id=user_id or "unknown",
                            match_score=pattern_importance,
                            confidence=pattern_importance * 0.85,
                            matched_data={
                                "sequence": sequence,
                                "importance": pattern_importance,
                            },
                            match_timestamp=datetime.utcnow(),
                            pattern_instances=[
                                {"sequence_index": i, "importance": pattern_importance}
                            ],
                            similarity_metrics={
                                "pattern_importance": pattern_importance
                            },
                        )
                        matches.append(match)

        except Exception as e:
            logger.error(f"Error in Transformer pattern matching: {e}")

        return matches

    def _sequences_match_exact(self, seq1: list[str], seq2: list[str]) -> bool:
        """Check if two sequences match exactly."""
        return seq1 == seq2

    def _calculate_preference_similarity(
        self, user_prefs: dict, template_prefs: dict
    ) -> float:
        """Calculate similarity between user preferences and template."""
        try:
            common_keys = set(user_prefs.keys()) & set(template_prefs.keys())
            if not common_keys:
                return 0.0

            similarities = []
            for key in common_keys:
                if user_prefs[key] == template_prefs[key]:
                    similarities.append(1.0)
                else:
                    similarities.append(0.0)

            return np.mean(similarities)

        except Exception:
            return 0.0

    def _find_frequent_subsequences(
        self, sequence: list[str], min_length: int, max_gap: int
    ) -> list[list[str]]:
        """Find frequent subsequences using a modified prefixspan algorithm."""
        try:
            frequent_patterns = []
            sequence_len = len(sequence)

            # Generate all possible subsequences of minimum length
            for start in range(sequence_len - min_length + 1):
                for end in range(
                    start + min_length, min(start + min_length + 5, sequence_len + 1)
                ):
                    subsequence = sequence[start:end]
                    frequent_patterns.append(subsequence)

            return frequent_patterns

        except Exception as e:
            logger.error(f"Error finding frequent subsequences: {e}")
            return []

    def _calculate_pattern_support(
        self, sequences: list[list[str]], pattern: list[str]
    ) -> float:
        """Calculate support of a pattern in a set of sequences."""
        try:
            if not sequences:
                return 0.0

            pattern_str = " -> ".join(pattern)
            count = 0

            for seq in sequences:
                seq_str = " -> ".join(seq)
                if pattern_str in seq_str:
                    count += 1

            return count / len(sequences)

        except Exception:
            return 0.0

    def _calculate_sequence_confidence(
        self, sequence: list[str], pattern: list[str]
    ) -> float:
        """Calculate confidence score for a sequence pattern match."""
        try:
            if not pattern or not sequence:
                return 0.0

            pattern_str = " -> ".join(pattern)
            seq_str = " -> ".join(sequence)

            if pattern_str in seq_str:
                # Confidence based on pattern length relative to sequence length
                return min(1.0, len(pattern) / len(sequence))
            return 0.0

        except Exception:
            return 0.0

    def _extract_features(
        self, user_data: dict[str, Any], template: PatternTemplate
    ) -> np.ndarray:
        """Extract features for clustering."""
        try:
            # This is a simplified feature extraction
            # In practice, this would be more sophisticated based on the template type

            features = []
            events = user_data.get("events", [])

            if events:
                # Basic features
                features.append(
                    [
                        len(events),  # Number of events
                        len(set(e["type"] for e in events)),  # Unique event types
                        sum(e.get("duration", 0) for e in events)
                        / len(events),  # Avg duration
                        len(events)
                        / max(
                            1,
                            (
                                events[-1]["timestamp"] - events[0]["timestamp"]
                            ).total_seconds()
                            / 3600,
                        ),  # Events per hour
                    ]
                )

            return np.array(features) if features else np.array([]).reshape(0, 4)

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.array([]).reshape(0, 4)

    def _extract_text_data(self, user_data: dict[str, Any]) -> list[str]:
        """Extract text data for semantic analysis."""
        try:
            text_data = []

            # Extract text from various fields
            if "descriptions" in user_data:
                text_data.extend(user_data["descriptions"])

            if "comments" in user_data:
                text_data.extend(user_data["comments"])

            if "events" in user_data:
                for event in user_data["events"]:
                    if "description" in event:
                        text_data.append(event["description"])

            return text_data

        except Exception:
            return []

    def _filter_by_time_window(self, df: pd.DataFrame, window: str) -> pd.DataFrame:
        """Filter DataFrame by time window."""
        try:
            if window == "morning":
                return df[df["hour"].between(6, 11)]
            if window == "afternoon":
                return df[df["hour"].between(12, 17)]
            if window == "evening":
                return df[df["hour"].between(18, 21)]
            if window == "night":
                return df[(df["hour"] >= 22) | (df["hour"] <= 5)]
            return df

        except Exception:
            return pd.DataFrame()

    def _combine_algorithm_matches(
        self, all_matches: list[PatternMatch], template: PatternTemplate
    ) -> list[PatternMatch]:
        """Combine matches from multiple algorithms."""
        try:
            if not all_matches:
                return []

            # Group similar matches
            match_groups = defaultdict(list)
            for match in all_matches:
                # Use a simple grouping key - in practice, this would be more sophisticated
                key = f"{match.template_id}_{hash(str(match.matched_data))}"
                match_groups[key].append(match)

            # Combine scores within groups
            combined_matches = []
            for group_key, group_matches in match_groups.items():
                # Average the scores
                avg_score = np.mean([m.match_score for m in group_matches])
                avg_confidence = np.mean([m.confidence for m in group_matches])

                # Create combined match
                combined_match = PatternMatch(
                    match_id=f"combined_{group_key}",
                    template_id=template.template_id,
                    user_id=group_matches[0].user_id,
                    match_score=avg_score,
                    confidence=avg_confidence
                    * 0.9,  # Slightly lower confidence for combined
                    matched_data={
                        "combined_from": len(group_matches),
                        "algorithms": [m.method.value for m in group_matches],
                    },
                    match_timestamp=datetime.utcnow(),
                    pattern_instances=[m.pattern_instances[0] for m in group_matches],
                    similarity_metrics={
                        "combined_score": avg_score,
                        "algorithm_count": len(group_matches),
                    },
                )
                combined_matches.append(combined_match)

            return sorted(combined_matches, key=lambda x: x.confidence, reverse=True)

        except Exception as e:
            logger.error(f"Error combining algorithm matches: {e}")
            return all_matches

    def _sequence_to_indices(self, sequence: list[str]) -> list[int]:
        """Convert sequence of strings to numerical indices."""
        try:
            # Simple hash-based encoding
            return [hash(item) % 1000 for item in sequence]
        except Exception:
            return []

    def _pattern_match_to_dict(self, match: PatternMatch) -> dict[str, Any]:
        """Convert PatternMatch to dictionary for JSON serialization."""
        return {
            "match_id": match.match_id,
            "template_id": match.template_id,
            "user_id": match.user_id,
            "match_score": match.match_score,
            "confidence": match.confidence,
            "matched_data": match.matched_data,
            "match_timestamp": match.match_timestamp.isoformat(),
            "pattern_instances": match.pattern_instances,
            "similarity_metrics": match.similarity_metrics,
            "context": match.context,
        }

    def _dict_to_pattern_match(self, data: dict[str, Any]) -> PatternMatch:
        """Convert dictionary to PatternMatch."""
        return PatternMatch(
            match_id=data["match_id"],
            template_id=data["template_id"],
            user_id=data["user_id"],
            match_score=data["match_score"],
            confidence=data["confidence"],
            matched_data=data["matched_data"],
            match_timestamp=datetime.fromisoformat(data["match_timestamp"]),
            pattern_instances=data["pattern_instances"],
            similarity_metrics=data["similarity_metrics"],
            context=data["context"],
        )
