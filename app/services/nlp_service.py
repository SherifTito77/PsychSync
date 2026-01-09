"""
Natural Language Processing Service
Provides comprehensive NLP capabilities including text processing,
sentiment analysis, theme extraction, and language understanding.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import re
import string
from typing import Any

# Try to import NLP libraries, provide fallbacks if not available
# SPACY may have compatibility issues with pydantic 2.x
SPACY_AVAILABLE = False
try:
    # Suppress the import error - spacy 3.8+ has pydantic v1 incompatibility
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        import spacy

        SPACY_AVAILABLE = True
except (ImportError, Exception):
    # Spacy not available or has compatibility issues
    SPACY_AVAILABLE = False
    # Silently fail - will use fallback implementations

try:
    import nltk
    from nltk import ngrams
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import sent_tokenize, word_tokenize

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not available. Install with: pip install nltk")

try:
    from textblob import TextBlob

    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logging.warning("TextBlob not available. Install with: pip install textblob")

try:
    import gensim
    from gensim import corpora, models
    from gensim.models import CoherenceModel, LdaModel

    GENSIM_AVAILABLE = True
except ImportError:
    GENSIM_AVAILABLE = False
    logging.warning("Gensim not available. Install with: pip install gensim")


logger = logging.getLogger(__name__)


class SentimentLabel(Enum):
    """Sentiment classification labels"""

    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class TextComplexity(Enum):
    """Text complexity levels"""

    VERY_SIMPLE = "very_simple"
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class NLPModel(Enum):
    """Available NLP models"""

    SPACY = "spacy"
    NLTK = "nltk"
    TEXTBLOB = "textblob"
    CUSTOM = "custom"


@dataclass
class SentimentScore:
    """Sentiment analysis results"""

    polarity: float  # -1.0 to 1.0
    subjectivity: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    label: SentimentLabel
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "polarity": self.polarity,
            "subjectivity": self.subjectivity,
            "confidence": self.confidence,
            "label": self.label.value,
            "details": self.details,
        }


@dataclass
class Theme:
    """Identified theme from text analysis"""

    id: str
    name: str
    keywords: list[str]
    frequency: int
    relevance_score: float
    examples: list[str] = field(default_factory=list)
    sentiment_distribution: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "keywords": self.keywords,
            "frequency": self.frequency,
            "relevance_score": self.relevance_score,
            "examples": self.examples[:3],  # Limit examples
            "sentiment_distribution": self.sentiment_distribution,
        }


@dataclass
class TextAnalysis:
    """Complete text analysis results"""

    text_id: str
    original_text: str
    word_count: int
    sentence_count: int
    readability_score: float
    complexity: TextComplexity
    sentiment: SentimentScore
    themes: list[Theme] = field(default_factory=list)
    key_entities: list[str] = field(default_factory=list)
    key_phrases: list[str] = field(default_factory=list)
    language: str = "en"
    processed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "text_id": self.text_id,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "readability_score": self.readability_score,
            "complexity": self.complexity.value,
            "sentiment": self.sentiment.to_dict(),
            "themes": [theme.to_dict() for theme in self.themes],
            "key_entities": self.key_entities,
            "key_phrases": self.key_phrases,
            "language": self.language,
            "processed_at": self.processed_at.isoformat(),
        }


@dataclass
class WordFrequency:
    """Word frequency analysis"""

    word: str
    frequency: int
    normalized_frequency: float
    context_words: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "frequency": self.frequency,
            "normalized_frequency": self.normalized_frequency,
            "context_words": self.context_words[:10],
        }


class NLPService:
    """Comprehensive NLP service with multiple model support"""

    def __init__(self, preferred_model: NLPModel = NLPModel.SPACY):
        self.preferred_model = preferred_model
        self.models_loaded = False
        self.nlp_models = {}

        # Text processing resources
        self.stop_words = set()
        self.lemmatizer = None
        self.word_freq_cache = {}

        # Topic modeling components
        self.lda_models = {}
        self.topic_dictionaries = {}

        # Initialize services
        self._initialize_nlp_models()
        self._initialize_resources()

        logger.info(f"NLP Service initialized with preferred model: {preferred_model.value}")

    def _initialize_nlp_models(self) -> None:
        """Initialize available NLP models"""
        try:
            # Initialize spaCy
            if SPACY_AVAILABLE:
                try:
                    self.nlp_models["spacy"] = spacy.load("en_core_web_sm")
                    logger.info("spaCy model loaded successfully")
                except OSError:
                    logger.warning(
                        "spaCy model not found. Run: python -m spacy download en_core_web_sm"
                    )
                    self.nlp_models["spacy"] = None

            # Initialize NLTK resources
            if NLTK_AVAILABLE:
                try:
                    # Configure SSL for NLTK downloads if needed
                    try:
                        import ssl

                        try:
                            _create_unverified_https_context = ssl._create_unverified_context
                        except AttributeError:
                            pass
                        else:
                            ssl._create_default_https_context = _create_unverified_https_context
                    except ImportError:
                        pass

                    # Ensure nltk is accessible in this scope
                    import nltk

                    # Download required NLTK data with error handling
                    required_data = ["punkt", "stopwords", "wordnet", "averaged_perceptron_tagger"]
                    downloaded_data = []

                    for data_name in required_data:
                        try:
                            nltk.download(data_name, quiet=True)
                            downloaded_data.append(data_name)
                        except Exception as download_error:
                            logger.warning(
                                f"Failed to download NLTK data '{data_name}': {download_error!s}"
                            )

                    # Verify data is actually available
                    available_data = []
                    for data_name in downloaded_data:
                        try:
                            if (
                                data_name == "punkt"
                                or data_name == "stopwords"
                                or data_name == "wordnet"
                            ):
                                available_data.append(data_name)
                            elif data_name == "averaged_perceptron_tagger":
                                import nltk

                                nltk.data.load("taggers/averaged_perceptron_tagger.pickle")
                                available_data.append(data_name)
                        except Exception as verify_error:
                            logger.warning(
                                f"NLTK data '{data_name}' verification failed: {verify_error!s}"
                            )

                    if len(available_data) >= 2:  # At least basic functionality
                        self.nlp_models["nltk"] = True
                        if "wordnet" in available_data:
                            self.lemmatizer = WordNetLemmatizer()
                        logger.info(f"NLTK resources loaded successfully: {available_data}")
                    else:
                        self.nlp_models["nltk"] = None
                        logger.warning(
                            "Insufficient NLTK data available, falling back to basic functionality"
                        )

                except Exception as e:
                    logger.error(f"Failed to initialize NLTK resources: {e!s}")
                    self.nlp_models["nltk"] = None

            # Initialize TextBlob
            if TEXTBLOB_AVAILABLE:
                self.nlp_models["textblob"] = True
                logger.info("TextBlob initialized successfully")

            # Initialize Gensim for topic modeling
            if GENSIM_AVAILABLE:
                self.nlp_models["gensim"] = True
                logger.info("Gensim initialized successfully")

            self.models_loaded = True

        except Exception as e:
            logger.error(f"Failed to initialize NLP models: {e!s}")
            self.models_loaded = False

    def _initialize_resources(self) -> None:
        """Initialize text processing resources"""
        try:
            # Load stop words
            if NLTK_AVAILABLE and self.nlp_models.get("nltk") and "stopwords" in dir():
                try:
                    self.stop_words = set(stopwords.words("english"))
                except Exception as stopwords_error:
                    logger.warning(f"Failed to load NLTK stopwords: {stopwords_error!s}")
                    self.stop_words = self._get_basic_stopwords()
            else:
                # Basic stop words list
                self.stop_words = self._get_basic_stopwords()

            logger.info(
                f"NLP resources initialized successfully with {len(self.stop_words)} stopwords"
            )

        except Exception as e:
            logger.error(f"Failed to initialize NLP resources: {e!s}")
            # Fallback to basic stopwords
            self.stop_words = self._get_basic_stopwords()

    def _get_basic_stopwords(self) -> set:
        """Get basic stop words list as fallback"""
        return {
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "your",
            "yours",
            "yourself",
            "yourselves",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "am",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "having",
            "do",
            "does",
            "did",
            "doing",
            "a",
            "an",
            "the",
            "and",
            "but",
            "if",
            "or",
            "because",
            "as",
            "until",
            "while",
            "of",
            "at",
            "by",
            "for",
            "with",
            "about",
            "against",
            "between",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "to",
            "from",
            "up",
            "down",
            "in",
            "out",
            "on",
            "off",
            "over",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "s",
            "t",
            "can",
            "will",
            "just",
            "don",
            "should",
            "now",
        }

    async def analyze_text(
        self,
        text: str,
        text_id: str | None = None,
        include_sentiment: bool = True,
        include_themes: bool = True,
        include_entities: bool = True,
        include_phrases: bool = True,
    ) -> TextAnalysis:
        """Perform comprehensive text analysis"""
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")

            text_id = text_id or f"text_{datetime.utcnow().timestamp()}"

            # Basic text statistics
            word_count = len(text.split())
            sentence_count = self._count_sentences(text)
            readability_score = self._calculate_readability(text)
            complexity = self._determine_complexity(readability_score, word_count, sentence_count)

            # Sentiment analysis
            sentiment = SentimentScore(0.0, 0.0, 0.0, SentimentLabel.NEUTRAL)
            if include_sentiment:
                sentiment = await self.analyze_sentiment(text)

            # Theme extraction
            themes = []
            if include_themes:
                themes = await self.extract_themes(text)

            # Entity recognition
            entities = []
            if include_entities:
                entities = await self.extract_entities(text)

            # Key phrase extraction
            phrases = []
            if include_phrases:
                phrases = await self.extract_key_phrases(text)

            analysis = TextAnalysis(
                text_id=text_id,
                original_text=text,
                word_count=word_count,
                sentence_count=sentence_count,
                readability_score=readability_score,
                complexity=complexity,
                sentiment=sentiment,
                themes=themes,
                key_entities=entities,
                key_phrases=phrases,
                language=self._detect_language(text),
            )

            logger.debug(f"Completed text analysis for {text_id}")
            return analysis

        except Exception as e:
            logger.error(f"Text analysis failed: {e!s}")
            raise

    async def analyze_sentiment(self, text: str, model: NLPModel | None = None) -> SentimentScore:
        """Analyze sentiment of text"""
        try:
            model = model or self.preferred_model

            if model == NLPModel.SPACY and self.nlp_models.get("spacy"):
                return await self._sentiment_analysis_spacy(text)
            if model == NLPModel.TEXTBLOB and TEXTBLOB_AVAILABLE:
                return await self._sentiment_analysis_textblob(text)
            if model == NLPModel.NLTK and NLTK_AVAILABLE:
                return await self._sentiment_analysis_nltk(text)
            # Fallback to simple rule-based sentiment
            return await self._sentiment_analysis_simple(text)

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e!s}")
            return SentimentScore(0.0, 0.0, 0.0, SentimentLabel.NEUTRAL)

    async def extract_themes(
        self, text: str, num_themes: int = 5, method: str = "frequency"
    ) -> list[Theme]:
        """Extract main themes from text"""
        try:
            if method == "frequency":
                return await self._extract_themes_frequency(text, num_themes)
            if method == "topic_modeling" and GENSIM_AVAILABLE:
                return await self._extract_themes_lda(text, num_themes)
            return await self._extract_themes_frequency(text, num_themes)

        except Exception as e:
            logger.error(f"Theme extraction failed: {e!s}")
            return []

    async def extract_entities(self, text: str) -> list[str]:
        """Extract named entities from text"""
        try:
            if self.nlp_models.get("spacy"):
                return await self._extract_entities_spacy(text)
            return await self._extract_entities_simple(text)

        except Exception as e:
            logger.error(f"Entity extraction failed: {e!s}")
            return []

    async def extract_key_phrases(
        self, text: str, num_phrases: int = 10, min_length: int = 2, max_length: int = 4
    ) -> list[str]:
        """Extract key phrases from text"""
        try:
            if self.nlp_models.get("spacy"):
                return await self._extract_key_phrases_spacy(
                    text, num_phrases, min_length, max_length
                )
            return await self._extract_key_phrases_ngrams(text, num_phrases, min_length, max_length)

        except Exception as e:
            logger.error(f"Key phrase extraction failed: {e!s}")
            return []

    async def analyze_word_frequency(
        self, texts: list[str], normalize: bool = True, min_frequency: int = 2
    ) -> list[WordFrequency]:
        """Analyze word frequency across multiple texts"""
        try:
            all_words = []
            word_contexts = defaultdict(list)

            for text in texts:
                words = self._preprocess_text(text)
                all_words.extend(words)

                # Track word contexts
                for i, word in enumerate(words):
                    context_start = max(0, i - 3)
                    context_end = min(len(words), i + 4)
                    context = [words[j] for j in range(context_start, context_end) if j != i]
                    word_contexts[word].extend(context)

            # Count frequencies
            word_counts = Counter(all_words)
            total_words = len(all_words)

            # Create WordFrequency objects
            frequencies = []
            for word, count in word_counts.items():
                if count >= min_frequency and word not in self.stop_words:
                    normalized_freq = (
                        count / total_words if normalize and total_words > 0 else count
                    )

                    # Get unique context words
                    unique_contexts = list(set(word_contexts[word]))

                    frequencies.append(
                        WordFrequency(
                            word=word,
                            frequency=count,
                            normalized_frequency=normalized_freq,
                            context_words=unique_contexts,
                        )
                    )

            # Sort by frequency
            frequencies.sort(key=lambda x: x.frequency, reverse=True)

            return frequencies

        except Exception as e:
            logger.error(f"Word frequency analysis failed: {e!s}")
            return []

    async def generate_word_cloud_data(
        self, texts: list[str], max_words: int = 100, exclude_stopwords: bool = True
    ) -> list[dict[str, Any]]:
        """Generate data for word cloud visualization"""
        try:
            frequencies = await self.analyze_word_frequency(texts, normalize=True, min_frequency=1)

            # Filter and format for word cloud
            word_cloud_data = []
            for freq in frequencies[:max_words]:
                if exclude_stopwords and freq.word.lower() in self.stop_words:
                    continue

                word_cloud_data.append(
                    {
                        "text": freq.word,
                        "value": freq.frequency,
                        "weight": freq.normalized_frequency * 100,  # Scale for visualization
                    }
                )

            return word_cloud_data

        except Exception as e:
            logger.error(f"Word cloud data generation failed: {e!s}")
            return []

    # Implementation methods for different NLP models

    async def _sentiment_analysis_spacy(self, text: str) -> SentimentScore:
        """Sentiment analysis using spaCy with custom rules"""
        try:
            nlp = self.nlp_models["spacy"]
            doc = nlp(text)

            # Simple sentiment based on word polarity
            positive_words = [
                "good",
                "great",
                "excellent",
                "amazing",
                "wonderful",
                "fantastic",
                "love",
                "like",
                "enjoy",
            ]
            negative_words = [
                "bad",
                "terrible",
                "awful",
                "horrible",
                "hate",
                "dislike",
                "poor",
                "worst",
            ]

            positive_count = sum(1 for token in doc if token.text.lower() in positive_words)
            negative_count = sum(1 for token in doc if token.text.lower() in negative_words)
            total_words = len(doc)

            polarity = (positive_count - negative_count) / max(total_words, 1)
            subjectivity = min(0.5, (positive_count + negative_count) / max(total_words, 1))

            # Determine sentiment label
            if polarity > 0.3:
                label = SentimentLabel.POSITIVE if polarity < 0.7 else SentimentLabel.VERY_POSITIVE
            elif polarity < -0.3:
                label = SentimentLabel.NEGATIVE if polarity > -0.7 else SentimentLabel.VERY_NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL

            confidence = abs(polarity)

            return SentimentScore(
                polarity=polarity, subjectivity=subjectivity, confidence=confidence, label=label
            )

        except Exception as e:
            logger.error(f"spaCy sentiment analysis failed: {e!s}")
            return await self._sentiment_analysis_simple(text)

    async def _sentiment_analysis_textblob(self, text: str) -> SentimentScore:
        """Sentiment analysis using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity

            # Determine sentiment label
            if polarity > 0.3:
                label = SentimentLabel.POSITIVE if polarity < 0.7 else SentimentLabel.VERY_POSITIVE
            elif polarity < -0.3:
                label = SentimentLabel.NEGATIVE if polarity > -0.7 else SentimentLabel.VERY_NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL

            confidence = abs(polarity)

            return SentimentScore(
                polarity=polarity,
                subjectivity=subjectivity,
                confidence=confidence,
                label=label,
                details={
                    "assessments": blob.sentiment_assessments.assessments
                    if hasattr(blob.sentiment_assessments, "assessments")
                    else []
                },
            )

        except Exception as e:
            logger.error(f"TextBlob sentiment analysis failed: {e!s}")
            return await self._sentiment_analysis_simple(text)

    async def _sentiment_analysis_nltk(self, text: str) -> SentimentScore:
        """Sentiment analysis using NLTK (requires VADER)"""
        try:
            # Try to use VADER sentiment analyzer
            from nltk.sentiment import SentimentIntensityAnalyzer

            sia = SentimentIntensityAnalyzer()

            scores = sia.polarity_scores(text)
            polarity = scores["compound"]
            subjectivity = 1 - scores["neu"]

            # Determine sentiment label
            if polarity > 0.05:
                label = SentimentLabel.POSITIVE if polarity < 0.5 else SentimentLabel.VERY_POSITIVE
            elif polarity < -0.05:
                label = SentimentLabel.NEGATIVE if polarity > -0.5 else SentimentLabel.VERY_NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL

            confidence = abs(polarity)

            return SentimentScore(
                polarity=polarity,
                subjectivity=subjectivity,
                confidence=confidence,
                label=label,
                details={"vader_scores": scores},
            )

        except ImportError:
            logger.warning(
                "VADER sentiment analyzer not available, falling back to simple analysis"
            )
            return await self._sentiment_analysis_simple(text)
        except Exception as e:
            logger.error(f"NLTK sentiment analysis failed: {e!s}")
            return await self._sentiment_analysis_simple(text)

    async def _sentiment_analysis_simple(self, text: str) -> SentimentScore:
        """Simple rule-based sentiment analysis"""
        try:
            positive_words = [
                "good",
                "great",
                "excellent",
                "amazing",
                "wonderful",
                "fantastic",
                "love",
                "like",
                "enjoy",
                "happy",
                "pleased",
                "satisfied",
                "awesome",
                "perfect",
            ]
            negative_words = [
                "bad",
                "terrible",
                "awful",
                "horrible",
                "hate",
                "dislike",
                "poor",
                "worst",
                "angry",
                "frustrated",
                "disappointed",
                "sad",
                "upset",
                "annoying",
            ]

            words = text.lower().split()
            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            total_words = len(words)

            polarity = (positive_count - negative_count) / max(total_words, 1)
            subjectivity = min(0.5, (positive_count + negative_count) / max(total_words, 1))

            # Determine sentiment label
            if polarity > 0.1:
                label = SentimentLabel.POSITIVE if polarity < 0.5 else SentimentLabel.VERY_POSITIVE
            elif polarity < -0.1:
                label = SentimentLabel.NEGATIVE if polarity > -0.5 else SentimentLabel.VERY_NEGATIVE
            else:
                label = SentimentLabel.NEUTRAL

            confidence = min(abs(polarity) * 2, 1.0)

            return SentimentScore(
                polarity=polarity, subjectivity=subjectivity, confidence=confidence, label=label
            )

        except Exception as e:
            logger.error(f"Simple sentiment analysis failed: {e!s}")
            return SentimentScore(0.0, 0.0, 0.0, SentimentLabel.NEUTRAL)

    async def _extract_themes_frequency(self, text: str, num_themes: int) -> list[Theme]:
        """Extract themes based on word frequency"""
        try:
            # Process text
            words = self._preprocess_text(text)
            word_freq = Counter(words)

            # Group related words into themes
            themes = []
            processed_words = set()

            for word, freq in word_freq.most_common(num_themes * 3):  # Get more to find themes
                if word in processed_words or word in self.stop_words:
                    continue

                # Find related words (simple approach)
                related_words = [word]
                for other_word, other_freq in word_freq.items():
                    if other_word not in processed_words and other_word != word:
                        # Check if words are similar (same starting letters or common patterns)
                        if (
                            other_word.startswith(word[:3]) or word.startswith(other_word[:3])
                        ) and other_freq >= 2:
                            related_words.append(other_word)
                            processed_words.add(other_word)

                total_freq = sum(word_freq[w] for w in related_words)
                relevance_score = total_freq / len(words)

                # Create theme
                theme_id = f"theme_{len(themes)}"
                theme_name = self._generate_theme_name(related_words)

                # Find examples containing these words
                sentences = self._split_into_sentences(text)
                examples = []
                for sentence in sentences[:10]:  # Check first 10 sentences
                    if any(word in sentence.lower() for word in related_words[:3]):
                        examples.append(sentence.strip())
                        if len(examples) >= 2:
                            break

                themes.append(
                    Theme(
                        id=theme_id,
                        name=theme_name,
                        keywords=related_words[:5],  # Top 5 keywords
                        frequency=total_freq,
                        relevance_score=relevance_score,
                        examples=examples,
                    )
                )

                processed_words.add(word)

                if len(themes) >= num_themes:
                    break

            return themes

        except Exception as e:
            logger.error(f"Frequency-based theme extraction failed: {e!s}")
            return []

    async def _extract_themes_lda(self, text: str, num_themes: int) -> list[Theme]:
        """Extract themes using Latent Dirichlet Allocation"""
        try:
            if not GENSIM_AVAILABLE:
                return await self._extract_themes_frequency(text, num_themes)

            # Prepare documents (split text into chunks)
            sentences = self._split_into_sentences(text)
            documents = [
                self._preprocess_text(sent) for sent in sentences if len(sent.strip()) > 10
            ]

            if len(documents) < num_themes:
                return await self._extract_themes_frequency(text, num_themes)

            # Create dictionary and corpus
            dictionary = corpora.Dictionary(documents)
            corpus = [dictionary.doc2bow(doc) for doc in documents]

            # Train LDA model
            lda_model = LdaModel(
                corpus=corpus,
                id2word=dictionary,
                num_topics=num_themes,
                random_state=42,
                passes=10,
                alpha="auto",
            )

            # Extract themes
            themes = []
            for idx, topic in lda_model.print_topics(num_words=5):
                # Parse topic words
                topic_words = []
                for word_prob in topic.split(" + "):
                    word = word_prob.split('"')[1]
                    topic_words.append(word)

                # Calculate theme frequency
                theme_freq = sum(1 for doc in documents if any(word in doc for word in topic_words))
                relevance_score = theme_freq / len(documents)

                # Find examples
                examples = []
                for sentence in sentences[:20]:
                    if any(word in sentence.lower() for word in topic_words[:3]):
                        examples.append(sentence.strip())
                        if len(examples) >= 2:
                            break

                themes.append(
                    Theme(
                        id=f"lda_topic_{idx}",
                        name=f"Topic {idx + 1}: {topic_words[0].title()} & {topic_words[1].title()}",
                        keywords=topic_words,
                        frequency=theme_freq,
                        relevance_score=relevance_score,
                        examples=examples,
                    )
                )

            return themes

        except Exception as e:
            logger.error(f"LDA theme extraction failed: {e!s}")
            return await self._extract_themes_frequency(text, num_themes)

    async def _extract_entities_spacy(self, text: str) -> list[str]:
        """Extract entities using spaCy"""
        try:
            nlp = self.nlp_models["spacy"]
            doc = nlp(text)

            entities = []
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "GPE", "PRODUCT", "EVENT", "WORK_OF_ART"]:
                    entities.append(ent.text)

            # Remove duplicates while preserving order
            seen = set()
            unique_entities = []
            for entity in entities:
                if entity not in seen:
                    seen.add(entity)
                    unique_entities.append(entity)

            return unique_entities[:20]  # Limit to top 20

        except Exception as e:
            logger.error(f"spaCy entity extraction failed: {e!s}")
            return []

    async def _extract_entities_simple(self, text: str) -> list[str]:
        """Simple entity extraction using capitalization patterns"""
        try:
            # Find capitalized words/phrases
            capitalized_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"
            entities = re.findall(capitalized_pattern, text)

            # Filter out common words
            common_words = {"This", "That", "The", "It", "He", "She", "They", "We", "You"}
            entities = [
                entity for entity in entities if entity not in common_words and len(entity) > 2
            ]

            # Remove duplicates
            return list(dict.fromkeys(entities))[:20]

        except Exception as e:
            logger.error(f"Simple entity extraction failed: {e!s}")
            return []

    async def _extract_key_phrases_spacy(
        self, text: str, num_phrases: int, min_length: int, max_length: int
    ) -> list[str]:
        """Extract key phrases using spaCy"""
        try:
            nlp = self.nlp_models["spacy"]
            doc = nlp(text)

            # Extract noun chunks and other phrases
            phrases = []

            # Noun chunks
            for chunk in doc.noun_chunks:
                if min_length <= len(chunk.text.split()) <= max_length:
                    phrases.append(chunk.text)

            # Additional phrases based on POS patterns
            for i in range(len(doc)):
                # Find adjective-noun patterns
                if i < len(doc) - 1 and doc[i].pos_ == "ADJ" and doc[i + 1].pos_ == "NOUN":
                    phrase = f"{doc[i].text} {doc[i + 1].text}"
                    if min_length <= len(phrase.split()) <= max_length:
                        phrases.append(phrase)

            # Filter and rank phrases
            filtered_phrases = []
            seen = set()

            for phrase in phrases:
                # Clean and normalize
                clean_phrase = phrase.strip().lower()
                if (
                    len(clean_phrase) > 5
                    and clean_phrase not in seen
                    and not all(word in self.stop_words for word in clean_phrase.split())
                ):
                    seen.add(clean_phrase)
                    filtered_phrases.append(phrase)

            return filtered_phrases[:num_phrases]

        except Exception as e:
            logger.error(f"spaCy key phrase extraction failed: {e!s}")
            return await self._extract_key_phrases_ngrams(text, num_phrases, min_length, max_length)

    async def _extract_key_phrases_ngrams(
        self, text: str, num_phrases: int, min_length: int, max_length: int
    ) -> list[str]:
        """Extract key phrases using n-grams"""
        try:
            words = self._preprocess_text(text)

            # Generate n-grams
            phrases = []
            for n in range(min_length, max_length + 1):
                if len(words) >= n:
                    for ngram in ngrams(words, n):
                        phrase = " ".join(ngram)
                        if not all(word in self.stop_words for word in phrase.split()):
                            phrases.append(phrase)

            # Count phrase frequencies
            phrase_freq = Counter(phrases)

            # Return most frequent phrases
            return [phrase for phrase, freq in phrase_freq.most_common(num_phrases)]

        except Exception as e:
            logger.error(f"N-gram key phrase extraction failed: {e!s}")
            return []

    # Helper methods

    def _preprocess_text(self, text: str) -> list[str]:
        """Preprocess text for analysis"""
        try:
            # Convert to lowercase
            text = text.lower()

            # Remove punctuation
            text = text.translate(str.maketrans("", "", string.punctuation))

            # Tokenize with fallback
            if NLTK_AVAILABLE and self.nlp_models.get("nltk") and "punkt" in str(nltk.data.path):
                try:
                    words = word_tokenize(text)
                except Exception as tokenize_error:
                    logger.warning(f"NLTK tokenization failed: {tokenize_error!s}")
                    words = text.split()
            else:
                words = text.split()

            # Remove stop words and short words
            words = [word for word in words if word not in self.stop_words and len(word) > 2]

            # Lemmatize if available
            if self.lemmatizer:
                try:
                    words = [self.lemmatizer.lemmatize(word) for word in words]
                except Exception as lemmatize_error:
                    logger.warning(f"Lemmatization failed: {lemmatize_error!s}")
                    # Continue with non-lemmatized words

            return words

        except Exception as e:
            logger.error(f"Text preprocessing failed: {e!s}")
            # Return basic tokenization as last resort
            try:
                text = text.lower().translate(str.maketrans("", "", string.punctuation))
                return [
                    word for word in text.split() if len(word) > 2 and word not in self.stop_words
                ]
            except Exception:
                return []

    def _count_sentences(self, text: str) -> int:
        """Count number of sentences in text"""
        try:
            # Try NLTK sentence tokenization first
            if NLTK_AVAILABLE and self.nlp_models.get("nltk") and "punkt" in str(nltk.data.path):
                try:
                    return len(sent_tokenize(text))
                except Exception as nltk_error:
                    logger.warning(f"NLTK sentence tokenization failed: {nltk_error!s}")

            # Fallback to regex-based sentence counting
            sentences = re.split(r"[.!?]+", text)
            return len([s.strip() for s in sentences if s.strip()])

        except Exception:
            return len(text.split("."))

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences with fallback methods"""
        try:
            # Try NLTK sentence tokenization first
            if NLTK_AVAILABLE and self.nlp_models.get("nltk") and "punkt" in str(nltk.data.path):
                try:
                    return sent_tokenize(text)
                except Exception as nltk_error:
                    logger.warning(f"NLTK sentence tokenization failed: {nltk_error!s}")

            # Fallback to regex-based sentence splitting
            sentences = re.split(r"[.!?]+", text)
            return [s.strip() for s in sentences if s.strip()]

        except Exception:
            # Last resort: split on periods
            return [s.strip() for s in text.split(".") if s.strip()]

    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)"""
        try:
            words = text.split()
            sentences = self._count_sentences(text)

            if sentences == 0:
                return 0

            avg_sentence_length = len(words) / sentences

            # Simplified readability score
            readability = 100 - (avg_sentence_length * 1.5)
            return max(0, min(100, readability))

        except Exception:
            return 50  # Default to moderate readability

    def _determine_complexity(
        self, readability: float, word_count: int, sentence_count: int
    ) -> TextComplexity:
        """Determine text complexity level"""
        if readability > 80:
            return TextComplexity.VERY_SIMPLE
        if readability > 65:
            return TextComplexity.SIMPLE
        if readability > 45:
            return TextComplexity.MODERATE
        if readability > 25:
            return TextComplexity.COMPLEX
        return TextComplexity.VERY_COMPLEX

    def _detect_language(self, text: str) -> str:
        """Detect text language (simplified)"""
        try:
            # Simple detection based on common words
            english_words = {
                "the",
                "and",
                "is",
                "in",
                "to",
                "of",
                "a",
                "that",
                "it",
                "with",
                "for",
                "as",
                "was",
                "on",
                "be",
                "are",
                "have",
            }
            words = text.lower().split()[:50]  # Check first 50 words

            english_count = sum(1 for word in words if word in english_words)

            if english_count > len(words) * 0.1:  # 10% threshold
                return "en"
            return "unknown"
        except Exception:
            return "en"  # Default to English

    def _generate_theme_name(self, keywords: list[str]) -> str:
        """Generate a readable theme name from keywords"""
        if not keywords:
            return "Unknown Theme"

        # Take the most frequent keyword
        main_keyword = keywords[0].replace("_", " ").title()

        if len(keywords) > 1:
            second_keyword = keywords[1].replace("_", " ").title()
            return f"{main_keyword} & {second_keyword}"

        return main_keyword

    # Utility methods

    def get_model_status(self) -> dict[str, Any]:
        """Get status of loaded NLP models"""
        return {
            "models_loaded": self.models_loaded,
            "preferred_model": self.preferred_model.value,
            "available_models": {
                name: (model is not None) for name, model in self.nlp_models.items()
            },
            "resources": {
                "stop_words_loaded": len(self.stop_words) > 0,
                "lemmatizer_available": self.lemmatizer is not None,
            },
        }

    async def batch_analyze_texts(
        self, texts: list[str], text_ids: list[str] | None = None, **kwargs
    ) -> list[TextAnalysis]:
        """Analyze multiple texts in batch"""
        try:
            if text_ids is None:
                text_ids = [f"batch_{i}_{datetime.utcnow().timestamp()}" for i in range(len(texts))]

            analyses = []
            for text, text_id in zip(texts, text_ids):
                try:
                    analysis = await self.analyze_text(text, text_id, **kwargs)
                    analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Failed to analyze text {text_id}: {e!s}")
                    continue

            return analyses

        except Exception as e:
            logger.error(f"Batch text analysis failed: {e!s}")
            return []


# Export the main service class
__all__ = [
    "NLPModel",
    "NLPService",
    "SentimentLabel",
    "SentimentScore",
    "TextAnalysis",
    "TextComplexity",
    "Theme",
    "WordFrequency",
]
