"""
Word Cloud Visualization Service
Generates word cloud data and visualizations for text analysis,
including interactive and theme-based word clouds.
"""

import colorsys
import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.services.nlp_service import NLPService, WordFrequency
from app.services.theme_extraction_service import Theme, ThemeExtractionService

logger = logging.getLogger(__name__)


class WordCloudType(Enum):
    """Types of word clouds"""

    FREQUENCY = "frequency"  # Basic frequency-based word cloud
    TFIDF = "tfidf"  # TF-IDF weighted word cloud
    THEMATIC = "thematic"  # Theme-based word cloud
    SENTIMENT = "sentiment"  # Sentiment-colored word cloud
    TEMPORAL = "temporal"  # Time-evolving word cloud
    COMPARATIVE = "comparative"  # Comparison word cloud
    HIERARCHICAL = "hierarchical"  # Hierarchical word cloud


class ColorScheme(Enum):
    """Color schemes for word clouds"""

    RAINBOW = "rainbow"
    GRADIENT = "gradient"
    SENTIMENT = "sentiment"
    THEME = "theme"
    MONOCHROME = "monochrome"
    CUSTOM = "custom"


class LayoutAlgorithm(Enum):
    """Layout algorithms for word cloud positioning"""

    SPIRAL = "spiral"
    ARCHIMEDEAN = "archimedean"
    RECTANGULAR = "rectangular"
    CIRCULAR = "circular"
    RANDOM = "random"


@dataclass
class WordCloudWord:
    """Individual word in word cloud"""

    text: str
    size: float
    color: str
    x: float | None = None
    y: float | None = None
    rotation: float | None = None
    weight: float = 1.0
    category: str | None = None
    sentiment: str | None = None
    theme_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "size": self.size,
            "color": self.color,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "weight": self.weight,
            "category": self.category,
            "sentiment": self.sentiment,
            "theme_id": self.theme_id,
        }


@dataclass
class WordCloudConfig:
    """Configuration for word cloud generation"""

    width: int = 800
    height: int = 600
    max_words: int = 100
    min_font_size: int = 12
    max_font_size: int = 60
    background_color: str = "#ffffff"
    color_scheme: ColorScheme = ColorScheme.RAINBOW
    layout_algorithm: LayoutAlgorithm = LayoutAlgorithm.SPIRAL
    padding: int = 2
    prefer_horizontal: float = 0.9
    scale: float = 1.0
    relative_scaling: float = 0.5
    min_rotation: int = -45
    max_rotation: int = 45
    random_state: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "max_words": self.max_words,
            "min_font_size": self.min_font_size,
            "max_font_size": self.max_font_size,
            "background_color": self.background_color,
            "color_scheme": self.color_scheme.value,
            "layout_algorithm": self.layout_algorithm.value,
            "padding": self.padding,
            "prefer_horizontal": self.prefer_horizontal,
            "scale": self.scale,
            "relative_scaling": self.relative_scaling,
            "min_rotation": self.min_rotation,
            "max_rotation": self.max_rotation,
            "random_state": self.random_state,
        }


@dataclass
class WordCloudData:
    """Complete word cloud data"""

    words: list[WordCloudWord]
    config: WordCloudConfig
    metadata: dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "words": [word.to_dict() for word in self.words],
            "config": self.config.to_dict(),
            "metadata": self.metadata,
            "generated_at": self.generated_at.isoformat(),
        }


class WordCloudService:
    """Advanced word cloud generation service"""

    def __init__(self):
        self.nlp_service = NLPService()
        self.theme_service = ThemeExtractionService(self.nlp_service)

        # Color palettes
        self.color_palettes = {
            ColorScheme.RAINBOW: self._generate_rainbow_palette,
            ColorScheme.GRADIENT: self._generate_gradient_palette,
            ColorScheme.SENTIMENT: self._generate_sentiment_palette,
            ColorScheme.MONOCHROME: self._generate_monochrome_palette,
            ColorScheme.THEME: self._generate_theme_palette,
        }

        # Layout functions
        self.layout_functions = {
            LayoutAlgorithm.SPIRAL: self._spiral_layout,
            LayoutAlgorithm.ARCHIMEDEAN: self._archimedean_layout,
            LayoutAlgorithm.RECTANGULAR: self._rectangular_layout,
            LayoutAlgorithm.CIRCULAR: self._circular_layout,
            LayoutAlgorithm.RANDOM: self._random_layout,
        }

        logger.info("Word Cloud Service initialized")

    async def generate_word_cloud(
        self,
        texts: list[str],
        cloud_type: WordCloudType = WordCloudType.FREQUENCY,
        config: WordCloudConfig | None = None,
        themes: list[Theme] | None = None,
        sentiment_data: dict[str, float] | None = None,
        time_data: list[datetime] | None = None,
    ) -> WordCloudData:
        """Generate word cloud from text data"""
        try:
            start_time = datetime.utcnow()

            # Use default config if none provided
            if config is None:
                config = WordCloudConfig()

            # Process texts based on cloud type
            if cloud_type == WordCloudType.FREQUENCY:
                words = await self._generate_frequency_word_cloud(texts, config)
            elif cloud_type == WordCloudType.TFIDF:
                words = await self._generate_tfidf_word_cloud(texts, config)
            elif cloud_type == WordCloudType.THEMATIC:
                words = await self._generate_thematic_word_cloud(
                    texts, themes or [], config
                )
            elif cloud_type == WordCloudType.SENTIMENT:
                words = await self._generate_sentiment_word_cloud(
                    texts, sentiment_data or {}, config
                )
            elif cloud_type == WordCloudType.TEMPORAL:
                words = await self._generate_temporal_word_cloud(
                    texts, time_data or [], config
                )
            elif cloud_type == WordCloudType.HIERARCHICAL:
                words = await self._generate_hierarchical_word_cloud(texts, config)
            else:
                raise ValueError(f"Unsupported word cloud type: {cloud_type}")

            # Apply layout
            words = await self._apply_layout(words, config)

            # Apply colors
            words = await self._apply_colors(words, config)

            # Create metadata
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            metadata = {
                "cloud_type": cloud_type.value,
                "num_texts": len(texts),
                "num_words": len(words),
                "processing_time_seconds": processing_time,
                "total_word_count": sum(len(text.split()) for text in texts),
            }

            return WordCloudData(
                words=words,
                config=config,
                metadata=metadata,
                generated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Word cloud generation failed: {e!s}")
            return WordCloudData(
                words=[], config=config or WordCloudConfig(), metadata={"error": str(e)}
            )

    async def generate_comparative_word_cloud(
        self,
        texts1: list[str],
        texts2: list[str],
        label1: str = "Group 1",
        label2: str = "Group 2",
        config: WordCloudConfig | None = None,
    ) -> WordCloudData:
        """Generate comparative word cloud showing differences between two text groups"""
        try:
            if config is None:
                config = WordCloudConfig()

            # Analyze both groups
            freq1 = await self.nlp_service.analyze_word_frequency(
                texts1, normalize=True
            )
            freq2 = await self.nlp_service.analyze_word_frequency(
                texts2, normalize=True
            )

            # Create word maps for lookup
            freq1_map = {freq.word: freq.normalized_frequency for freq in freq1}
            freq2_map = {freq.word: freq.normalized_frequency for freq in freq2}

            # Find unique and shared words
            all_words = set(freq1_map.keys()) | set(freq2_map.keys())
            shared_words = set(freq1_map.keys()) & set(freq2_map.keys())
            unique1 = set(freq1_map.keys()) - set(freq2_map.keys())
            unique2 = set(freq2_map.keys()) - set(freq1_map.keys())

            # Create word list with categories
            words = []
            for word in all_words:
                freq1_val = freq1_map.get(word, 0)
                freq2_val = freq2_map.get(word, 0)

                # Determine size based on max frequency
                max_freq = max(freq1_val, freq2_val)
                size = self._calculate_word_size(max_freq, config)

                # Determine category and color
                if word in unique1:
                    category = label1
                    color = "#FF6B6B"  # Red for group 1
                elif word in unique2:
                    category = label2
                    color = "#4ECDC4"  # Teal for group 2
                else:
                    category = "shared"
                    # Color intensity based on frequency difference
                    diff = abs(freq1_val - freq2_val)
                    intensity = min(255, int(diff * 1000))
                    color = f"#{intensity:02x}{intensity:02x}{intensity:02x}"

                word_obj = WordCloudWord(
                    text=word,
                    size=size,
                    color=color,
                    category=category,
                    weight=max_freq,
                    rotation=0,  # No rotation for comparative clouds
                )

                words.append(word_obj)

            # Sort by size and limit
            words.sort(key=lambda w: w.size, reverse=True)
            words = words[: config.max_words]

            # Apply layout
            words = await self._apply_layout(words, config)

            # Create metadata
            metadata = {
                "cloud_type": WordCloudType.COMPARATIVE.value,
                "group1_label": label1,
                "group2_label": label2,
                "group1_count": len(texts1),
                "group2_count": len(texts2),
                "unique_words_group1": len(unique1),
                "unique_words_group2": len(unique2),
                "shared_words": len(shared_words),
                "total_words": len(words),
            }

            return WordCloudData(words=words, config=config, metadata=metadata)

        except Exception as e:
            logger.error(f"Comparative word cloud generation failed: {e!s}")
            return WordCloudData(
                words=[], config=config or WordCloudConfig(), metadata={"error": str(e)}
            )

    async def generate_animated_word_cloud(
        self,
        text_sequences: list[list[str]],
        timestamps: list[datetime],
        config: WordCloudConfig | None = None,
    ) -> list[WordCloudData]:
        """Generate animated word cloud showing evolution over time"""
        try:
            if config is None:
                config = WordCloudConfig()

            if len(text_sequences) != len(timestamps):
                raise ValueError("text_sequences and timestamps must have same length")

            frames = []

            for i, (texts, timestamp) in enumerate(zip(text_sequences, timestamps)):
                # Generate word cloud for this time point
                frame = await self.generate_word_cloud(
                    texts, WordCloudType.TEMPORAL, config, time_data=[timestamp]
                )

                # Add frame metadata
                frame.metadata.update(
                    {
                        "frame_number": i,
                        "timestamp": timestamp.isoformat(),
                        "total_frames": len(text_sequences),
                    }
                )

                frames.append(frame)

            return frames

        except Exception as e:
            logger.error(f"Animated word cloud generation failed: {e!s}")
            return []

    async def _generate_frequency_word_cloud(
        self, texts: list[str], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Generate frequency-based word cloud"""
        try:
            # Get word frequencies
            frequencies = await self.nlp_service.analyze_word_frequency(
                texts, normalize=True, min_frequency=1
            )

            # Convert to WordCloudWord objects
            words = []
            for freq in frequencies[: config.max_words]:
                size = self._calculate_word_size(freq.normalized_frequency, config)
                weight = freq.normalized_frequency

                word = WordCloudWord(
                    text=freq.word,
                    size=size,
                    color="",  # Will be set by color scheme
                    weight=weight,
                    category="frequency",
                )

                words.append(word)

            return words

        except Exception as e:
            logger.error(f"Frequency word cloud generation failed: {e!s}")
            return []

    async def _generate_tfidf_word_cloud(
        self, texts: list[str], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Generate TF-IDF weighted word cloud"""
        try:
            # Combine all texts for TF-IDF analysis
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer(
                max_features=config.max_words * 2,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8,
            )

            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            # Calculate average TF-IDF scores
            mean_scores = tfidf_matrix.mean(axis=0).A1

            # Get top terms
            top_indices = mean_scores.argsort()[::-1][: config.max_words]

            words = []
            for idx in top_indices:
                term = feature_names[idx]
                score = mean_scores[idx]

                if score > 0.01:  # Minimum threshold
                    size = self._calculate_word_size(score, config)
                    weight = float(score)

                    word = WordCloudWord(
                        text=term.replace("_", " "),
                        size=size,
                        color="",  # Will be set by color scheme
                        weight=weight,
                        category="tfidf",
                    )

                    words.append(word)

            return words

        except ImportError:
            # Fallback to frequency-based if sklearn not available
            logger.warning(
                "sklearn not available, falling back to frequency-based word cloud"
            )
            return await self._generate_frequency_word_cloud(texts, config)
        except Exception as e:
            logger.error(f"TF-IDF word cloud generation failed: {e!s}")
            return []

    async def _generate_thematic_word_cloud(
        self, texts: list[str], themes: list[Theme], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Generate theme-based word cloud"""
        try:
            if not themes:
                # Extract themes if not provided
                theme_result = await self.theme_service.extract_themes(texts)
                themes = [Theme(**theme_data) for theme_data in theme_result["themes"]]

            # Create theme color mapping
            theme_colors = self._generate_theme_colors(len(themes))

            words = []
            for i, theme in enumerate(themes):
                theme_color = theme_colors[i]

                # Add theme keywords to word cloud
                for keyword in theme.keywords:
                    size = self._calculate_word_size(theme.relevance_score, config)

                    word = WordCloudWord(
                        text=keyword,
                        size=size,
                        color=theme_color,
                        weight=theme.relevance_score,
                        category=theme.name,
                        theme_id=theme.id,
                    )

                    words.append(word)

            # Sort by size and limit
            words.sort(key=lambda w: w.size, reverse=True)
            return words[: config.max_words]

        except Exception as e:
            logger.error(f"Thematic word cloud generation failed: {e!s}")
            return []

    async def _generate_sentiment_word_cloud(
        self,
        texts: list[str],
        sentiment_data: dict[str, float],
        config: WordCloudConfig,
    ) -> list[WordCloudWord]:
        """Generate sentiment-colored word cloud"""
        try:
            # Get word frequencies
            frequencies = await self.nlp_service.analyze_word_frequency(
                texts, normalize=True
            )

            words = []
            for freq in frequencies[: config.max_words]:
                size = self._calculate_word_size(freq.normalized_frequency, config)

                # Determine sentiment from sentiment_data
                word_sentiment = sentiment_data.get(freq.word, "neutral")
                color = self._get_sentiment_color(word_sentiment)

                word = WordCloudWord(
                    text=freq.word,
                    size=size,
                    color=color,
                    weight=freq.normalized_frequency,
                    category="sentiment",
                    sentiment=word_sentiment,
                )

                words.append(word)

            return words

        except Exception as e:
            logger.error(f"Sentiment word cloud generation failed: {e!s}")
            return []

    async def _generate_temporal_word_cloud(
        self, texts: list[str], time_data: list[datetime], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Generate temporal word cloud with time-based coloring"""
        try:
            # Get word frequencies
            frequencies = await self.nlp_service.analyze_word_frequency(
                texts, normalize=True
            )

            # Calculate time weights (more recent words get higher weight)
            if time_data and len(time_data) == len(texts):
                now = datetime.utcnow()
                time_weights = []

                for timestamp in time_data:
                    # Weight based on recency (more recent = higher weight)
                    days_old = (now - timestamp).days
                    weight = max(0.1, 1.0 - days_old / 365.0)  # Decay over year
                    time_weights.append(weight)

                # Apply temporal weighting to word frequencies
                weighted_frequencies = []
                for freq in frequencies:
                    # Find texts containing this word and calculate temporal weight
                    temporal_weight = 0.0
                    for i, text in enumerate(texts):
                        if freq.word.lower() in text.lower():
                            temporal_weight += time_weights[i]

                    freq_copy = WordFrequency(
                        word=freq.word,
                        frequency=freq.frequency,
                        normalized_frequency=freq.normalized_frequency
                        * (1.0 + temporal_weight / len(texts)),
                        context_words=freq.context_words,
                    )
                    weighted_frequencies.append(freq_copy)

                frequencies = weighted_frequencies

            words = []
            for freq in frequencies[: config.max_words]:
                size = self._calculate_word_size(freq.normalized_frequency, config)

                # Color based on frequency (gradient from blue to red)
                color = self._get_gradient_color(freq.normalized_frequency, 0, 1)

                word = WordCloudWord(
                    text=freq.word,
                    size=size,
                    color=color,
                    weight=freq.normalized_frequency,
                    category="temporal",
                )

                words.append(word)

            return words

        except Exception as e:
            logger.error(f"Temporal word cloud generation failed: {e!s}")
            return []

    async def _generate_hierarchical_word_cloud(
        self, texts: list[str], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Generate hierarchical word cloud with parent-child relationships"""
        try:
            # Get word frequencies and extract themes
            frequencies = await self.nlp_service.analyze_word_frequency(
                texts, normalize=True
            )
            theme_result = await self.theme_service.extract_themes(texts)
            themes = [Theme(**theme_data) for theme_data in theme_result["themes"]]

            # Create hierarchy: themes as parents, keywords as children
            words = []
            theme_keywords_map = {}

            # Map keywords to themes
            for theme in themes:
                for keyword in theme.keywords:
                    theme_keywords_map[keyword.lower()] = theme

            # Add theme words (larger)
            for theme in themes[:10]:  # Limit number of main themes
                size = config.max_font_size * 0.8  # Themes are large
                color = self._get_theme_color(len(themes), themes.index(theme))

                word = WordCloudWord(
                    text=theme.name,
                    size=size,
                    color=color,
                    weight=theme.relevance_score,
                    category="theme",
                    theme_id=theme.id,
                )

                words.append(word)

            # Add keyword words (smaller, related to themes)
            for freq in frequencies[: config.max_words - len(themes)]:
                word_lower = freq.word.lower()

                # Check if this word belongs to a theme
                if word_lower in theme_keywords_map:
                    parent_theme = theme_keywords_map[word_lower]
                    size = config.min_font_size + (
                        config.max_font_size * 0.3 * freq.normalized_frequency
                    )
                    color = self._get_theme_color(
                        len(themes), themes.index(parent_theme)
                    )

                    word = WordCloudWord(
                        text=freq.word,
                        size=size,
                        color=color,
                        weight=freq.normalized_frequency,
                        category="keyword",
                        theme_id=parent_theme.id,
                    )

                    words.append(word)

            return words

        except Exception as e:
            logger.error(f"Hierarchical word cloud generation failed: {e!s}")
            return []

    async def _apply_layout(
        self, words: list[WordCloudWord], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Apply layout algorithm to position words"""
        try:
            layout_func = self.layout_functions.get(
                config.layout_algorithm, self._spiral_layout
            )
            return await layout_func(words, config)

        except Exception as e:
            logger.error(f"Layout application failed: {e!s}")
            # Fallback to spiral layout
            return await self._spiral_layout(words, config)

    async def _apply_colors(
        self, words: list[WordCloudWord], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Apply color scheme to words"""
        try:
            color_func = self.color_palettes.get(
                config.color_scheme, self._generate_rainbow_palette
            )

            for i, word in enumerate(words):
                if not word.color:  # Only apply if color not already set
                    word.color = color_func(i, len(words), word)

            return words

        except Exception as e:
            logger.error(f"Color application failed: {e!s}")
            return words

    # Layout algorithms

    async def _spiral_layout(
        self, words: list[WordCloudWord], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Apply spiral layout to words"""
        try:
            center_x = config.width / 2
            center_y = config.height / 2

            for i, word in enumerate(words):
                # Spiral parameters
                angle = i * 0.5  # radians
                radius = i * 3  # pixels per step

                word.x = center_x + radius * math.cos(angle)
                word.y = center_y + radius * math.sin(angle)

                # Random rotation within limits
                if np.secrets.SystemRandom().random() > config.prefer_horizontal:
                    word.rotation = np.random.uniform(
                        config.min_rotation, config.max_rotation
                    )
                else:
                    word.rotation = 0

            return words

        except Exception as e:
            logger.error(f"Spiral layout failed: {e!s}")
            # Fallback: place words in center
            for word in words:
                word.x = config.width / 2
                word.y = config.height / 2
                word.rotation = 0
            return words

    async def _archimedean_layout(
        self, words: list[WordCloudWord], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Apply Archimedean spiral layout"""
        try:
            center_x = config.width / 2
            center_y = config.height / 2

            for i, word in enumerate(words):
                # Archimedean spiral: r = a + b*θ
                theta = i * 0.3
                radius = 10 + 2 * theta

                word.x = center_x + radius * math.cos(theta)
                word.y = center_y + radius * math.sin(theta)

                # Rotation based on position
                word.rotation = np.random.uniform(
                    config.min_rotation, config.max_rotation
                )

            return words

        except Exception as e:
            logger.error(f"Archimedean layout failed: {e!s}")
            return await self._spiral_layout(words, config)

    async def _rectangular_layout(
        self, words: list[WordCloudWord], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Apply rectangular grid layout"""
        try:
            cols = int(math.sqrt(len(words) * config.width / config.height))
            rows = math.ceil(len(words) / cols)

            cell_width = config.width / cols
            cell_height = config.height / rows

            for i, word in enumerate(words):
                row = i // cols
                col = i % cols

                word.x = col * cell_width + cell_width / 2
                word.y = row * cell_height + cell_height / 2
                word.rotation = 0  # No rotation for rectangular layout

            return words

        except Exception as e:
            logger.error(f"Rectangular layout failed: {e!s}")
            return await self._spiral_layout(words, config)

    async def _circular_layout(
        self, words: list[WordCloudWord], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Apply circular layout"""
        try:
            center_x = config.width / 2
            center_y = config.height / 2
            max_radius = min(center_x, center_y) - 50

            for i, word in enumerate(words):
                # Position words in circles
                circle = i // 20  # 20 words per circle
                position = i % 20

                if circle == 0:
                    radius = 0  # Center word
                else:
                    radius = (circle / 10) * max_radius

                angle = (position / 20) * 2 * math.pi

                word.x = center_x + radius * math.cos(angle)
                word.y = center_y + radius * math.sin(angle)

                # Rotation based on position
                word.rotation = angle * 180 / math.pi

            return words

        except Exception as e:
            logger.error(f"Circular layout failed: {e!s}")
            return await self._spiral_layout(words, config)

    async def _random_layout(
        self, words: list[WordCloudWord], config: WordCloudConfig
    ) -> list[WordCloudWord]:
        """Apply random layout"""
        try:
            margin = 50

            for word in words:
                word.x = np.random.uniform(margin, config.width - margin)
                word.y = np.random.uniform(margin, config.height - margin)
                word.rotation = np.random.uniform(
                    config.min_rotation, config.max_rotation
                )

            return words

        except Exception as e:
            logger.error(f"Random layout failed: {e!s}")
            return await self._spiral_layout(words, config)

    # Color generation functions

    def _generate_rainbow_palette(
        self, index: int, total: int, word: WordCloudWord
    ) -> str:
        """Generate rainbow color"""
        hue = (index / total) * 0.8  # 0.8 to avoid red again
        rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"

    def _generate_gradient_palette(
        self, index: int, total: int, word: WordCloudWord
    ) -> str:
        """Generate gradient color (blue to red)"""
        ratio = index / total if total > 0 else 0
        red = int(255 * ratio)
        blue = int(255 * (1 - ratio))
        return f"#{red:02x}00{blue:02x}"

    def _generate_sentiment_palette(
        self, index: int, total: int, word: WordCloudWord
    ) -> str:
        """Generate sentiment-based color"""
        if hasattr(word, "sentiment") and word.sentiment:
            return self._get_sentiment_color(word.sentiment)
        return self._generate_rainbow_palette(index, total, word)

    def _generate_monochrome_palette(
        self, index: int, total: int, word: WordCloudWord
    ) -> str:
        """Generate monochrome color"""
        value = int(100 + (155 * word.weight))  # Range from dark to light gray
        return f"#{value:02x}{value:02x}{value:02x}"

    def _generate_theme_palette(
        self, index: int, total: int, word: WordCloudWord
    ) -> str:
        """Generate theme-based color"""
        if hasattr(word, "theme_id") and word.theme_id:
            # Use theme_id to generate consistent color
            hash_val = hash(word.theme_id) % 360
            rgb = colorsys.hsv_to_rgb(hash_val / 360, 0.7, 0.8)
            return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
        return self._generate_rainbow_palette(index, total, word)

    # Helper functions

    def _calculate_word_size(self, weight: float, config: WordCloudConfig) -> float:
        """Calculate word size based on weight"""
        # Normalize weight to 0-1 range (assuming weight is already normalized)
        normalized_weight = min(1.0, max(0.0, weight))

        # Apply relative scaling
        if config.relative_scaling < 1.0:
            # Non-linear scaling
            normalized_weight = normalized_weight ** (1.0 / config.relative_scaling)

        # Calculate size
        size_range = config.max_font_size - config.min_font_size
        size = config.min_font_size + (normalized_weight * size_range * config.scale)

        return size

    def _get_sentiment_color(self, sentiment: str) -> str:
        """Get color for sentiment"""
        sentiment_colors = {
            "positive": "#4CAF50",  # Green
            "negative": "#F44336",  # Red
            "neutral": "#9E9E9E",  # Gray
            "very_positive": "#2E7D32",  # Dark green
            "very_negative": "#C62828",  # Dark red
        }
        return sentiment_colors.get(sentiment, "#9E9E9E")

    def _get_gradient_color(self, value: float, min_val: float, max_val: float) -> str:
        """Get gradient color based on value"""
        if max_val <= min_val:
            return "#0000FF"

        # Normalize to 0-1
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))

        # Blue to red gradient
        red = int(255 * normalized)
        blue = int(255 * (1 - normalized))
        return f"#{red:02x}00{blue:02x}"

    def _generate_theme_colors(self, num_themes: int) -> list[str]:
        """Generate distinct colors for themes"""
        colors = []
        for i in range(num_themes):
            hue = (i / num_themes) * 0.8  # 0.8 to avoid red again
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.8)
            colors.append(
                f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"
            )
        return colors

    def _get_theme_color(self, total_themes: int, theme_index: int) -> str:
        """Get color for specific theme"""
        hue = (theme_index / total_themes) * 0.8 if total_themes > 0 else 0
        rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.8)
        return f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}"

    def export_to_svg(
        self, word_cloud_data: WordCloudData, filename: str | None = None
    ) -> str:
        """Export word cloud to SVG format"""
        try:
            svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{word_cloud_data.config.width}" height="{word_cloud_data.config.height}"
     xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="{word_cloud_data.config.background_color}"/>
"""

            for word in word_cloud_data.words:
                if word.x and word.y:
                    svg_content += f"""
<text x="{word.x}" y="{word.y}"
      font-family="Arial, sans-serif"
      font-size="{word.size}"
      fill="{word.color}"
      text-anchor="middle"
      transform="rotate({word.rotation or 0} {word.x} {word.y})">
{word.text}
</text>"""

            svg_content += "\n</svg>"

            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(svg_content)

            return svg_content

        except Exception as e:
            logger.error(f"SVG export failed: {e!s}")
            return ""

    def export_to_json(
        self, word_cloud_data: WordCloudData, filename: str | None = None
    ) -> str:
        """Export word cloud to JSON format"""
        try:
            json_data = word_cloud_data.to_dict()
            json_content = json.dumps(json_data, indent=2, ensure_ascii=False)

            if filename:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(json_content)

            return json_content

        except Exception as e:
            logger.error(f"JSON export failed: {e!s}")
            return ""


# Import numpy for random number generation
try:
    import numpy as np
except ImportError:
    # Fallback if numpy not available
    import random as np


# Export the main service class
__all__ = [
    "ColorScheme",
    "LayoutAlgorithm",
    "WordCloudConfig",
    "WordCloudData",
    "WordCloudService",
    "WordCloudType",
    "WordCloudWord",
]
