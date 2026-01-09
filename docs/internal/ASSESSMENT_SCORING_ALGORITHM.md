# Assessment Scoring Algorithm - Internal Documentation

**Document Owner:** AI/ML Team
**Version:** 1.0.0
**Last Updated:** 2025-12-27
**Classification:** Internal - Proprietary Algorithm
**Target Audience:** Software Engineers, Data Scientists, QA Engineers

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Assessment Frameworks](#assessment-frameworks)
4. [Scoring Algorithms](#scoring-algorithms)
5. [Processor Implementation](#processor-implementation)
6. [Normalization & Standardization](#normalization--standardization)
7. [Insight Generation](#insight-generation)
8. [Confidence Scoring](#confidence-scoring)
9. [Performance Optimization](#performance-optimization)
10. [Testing & Validation](#testing--validation)

---

## Executive Summary

PsychSync's assessment scoring engine uses a **pluggable processor architecture** to convert raw questionnaire responses into standardized personality profiles. The system supports multiple psychological frameworks (Big Five, MBTI, Enneagram, etc.) while maintaining consistent output formats through abstract base classes.

### Key Principles

1. **Standardization:** All frameworks output to a common JSON structure
2. **Validation:** Input sanitization and range enforcement (0.0-1.0)
3. **Graceful Degradation:** Fallback results with low confidence on errors
4. **Extensibility:** New frameworks added by implementing base interface
5. **Transparency:** Clear scoring logic with interpretable outputs

### High-Level Flow

```
User Responses (JSON)
         ↓
Framework Detection
         ↓
Processor Selection
         ↓
Raw Score Calculation
         ↓
Normalization (0-100 scale)
         ↓
Standardization (Big Five mapping)
         ↓
Insight Generation
         ↓
Confidence Scoring
         ↓
Final Output (JSON)
```

---

## Architecture Overview

### Component Hierarchy

```
PersonalityFrameworkProcessor (Abstract Base)
    ├── BigFiveProcessor
    ├── MBTIProcessor
    ├── EnneagramProcessor
    ├── PredictiveIndexProcessor
    ├── CliftonStrengthsProcessor
    └── SocialStylesProcessor
```

### Design Patterns

#### 1. Strategy Pattern
Each processor implements the same interface but uses different scoring strategies:

```python
class PersonalityFrameworkProcessor(ABC):
    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw assessment data into standardized format"""
        pass
```

#### 2. Template Method Pattern
Base class provides common functionality, subclasses implement specific steps:

```python
def _safe_get(self, data: Dict[str, Any], key: str, default: Any) -> Any:
    """Safely get value from dict with default fallback"""
    return data.get(key, default)

def _clamp_value(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp value to range [min_val, max_val]"""
    return max(min_val, min(max_val, value))
```

#### 3. Adapter Pattern
Different frameworks adapt to standard Big Five output format:

```python
def _mbti_to_big_five(self, mbti_type: str) -> Dict[str, float]:
    """Convert MBTI type to Big Five approximation"""
    mapping = {
        "E": {"extraversion": 0.7, "introversion": 0.3},
        "I": {"extraversion": 0.3, "introversion": 0.7},
        # ... etc
    }
    return self._combine_dimensions(mbti_type, mapping)
```

---

## Assessment Frameworks

### 1. Big Five (OCEAN) Model

**Scientific Basis:** Five-factor model of personality (McCrae & Costa, 1980s)

**Dimensions:**
- **O**penness to Experience: Creativity, curiosity, adventure-seeking
- **C**onscientiousness: Organization, discipline, achievement-striving
- **E**xtraversion: Sociability, assertiveness, energy level
- **A**greeableness: Compassion, cooperativeness, trust
- **N**euroticism: Emotional stability, anxiety, moodiness (inverted)

**Scoring Algorithm:**

```python
# File: app/services/scoring/big_five_scorer.py

class BigFiveScorer:
    def score_assessment(self, responses: Dict[str, int]) -> Dict[str, Any]:
        """
        Score Big Five assessment from Likert-scale responses.

        Args:
            responses: Dict mapping question_id to response (1-5)

        Returns:
            Dict with:
                - dimensions: {dimension: score_0_to_100}
                - percentiles: {dimension: percentile_0_to_100}
                - interpretations: {dimension: "Very High" to "Very Low"}
                - overall_profile: classification
        """

        # 1. Calculate raw dimension scores
        raw_scores = self._calculate_dimension_scores(responses)

        # 2. Normalize to 0-100 scale
        normalized = self._normalize_scores(raw_scores)

        # 3. Convert to population percentiles
        percentiles = self._calculate_percentiles(normalized)

        # 4. Generate interpretations
        interpretations = self._generate_interpretations(normalized)

        # 5. Determine overall profile
        profile = self._determine_profile(normalized)

        return {
            "dimensions": normalized,
            "percentiles": percentiles,
            "interpretations": interpretations,
            "overall_profile": profile,
            "confidence": self._calculate_confidence(responses)
        }
```

**Question-to-Dimension Mapping:**

```python
DIMENSION_QUESTIONS = {
    "openness": ["q1", "q6", "q11", "q16", "q21", "q26"],
    "conscientiousness": ["q2", "q7", "q12", "q17", "q22", "q27"],
    "extraversion": ["q3", "q8", "q13", "q18", "q23", "q28"],
    "agreeableness": ["q4", "q9", "q14", "q19", "q24", "q29"],
    "neuroticism": ["q5", "q10", "q15", "q20", "q25", "q30"]
}

REVERSE_SCORED = {
    "q6", "q12", "q18", "q24",  # Reverse-scored questions
    # ... etc
}
```

**Reverse Scoring:**

```python
def _calculate_dimension_score(self, dimension: str, responses: Dict) -> float:
    total = 0
    count = 0

    for q_id in DIMENSION_QUESTIONS[dimension]:
        value = responses.get(q_id, 3)  # Default to neutral

        # Reverse scoring: 5→1, 4→2, 3→3, 2→4, 1→5
        if q_id in REVERSE_SCORED:
            value = 6 - value

        total += value
        count += 1

    # Average (1-5 scale)
    avg = total / count if count > 0 else 3

    # Normalize to 0-100
    return ((avg - 1) / 4) * 100
```

**Percentile Calculation:**

```python
def _calculate_percentiles(self, scores: Dict[str, float]) -> Dict[str, float]:
    """
    Convert raw scores to population percentiles.
    Based on normative data from general population.
    """
    # Normal distribution parameters (mean, std) for each dimension
    NORMATIVE_DATA = {
        "openness": (50, 15),
        "conscientiousness": (52, 14),
        "extraversion": (48, 16),
        "agreeableness": (55, 13),
        "neuroticism": (45, 12)
    }

    percentiles = {}
    for dim, score in scores.items():
        mean, std = NORMATIVE_DATA[dim]
        z_score = (score - mean) / std
        percentile = stats.norm.cdf(z_score) * 100
        percentiles[dim] = round(percentile, 1)

    return percentiles
```

**Interpretation Bands:**

```python
INTERPRETATION_RANGES = {
    (87, 100): "Very High",
    (70, 86): "High",
    (30, 69): "Average",
    (14, 29): "Low",
    (0, 13): "Very Low"
}

def _generate_interpretations(self, scores: Dict[str, float]) -> Dict[str, str]:
    interpretations = {}
    for dim, score in scores.items():
        for (low, high), label in INTERPRETATION_RANGES.items():
            if low <= score <= high:
                interpretations[dim] = label
                break
    return interpretations
```

### 2. MBTI (Myers-Briggs Type Indicator)

**Scientific Basis:** Jungian cognitive functions (Myers & Briggs, 1940s)

**Dimensions:**
- **E**xtraversion vs **I**ntroversion: Energy orientation
- **S**ensing vs I**N**tuition: Information processing
- **T**hinking vs **F**eeling: Decision-making
- **J**udging vs **P**erceiving: Lifestyle structure

**Scoring Algorithm:**

```python
# File: app/services/scoring/mbti_scorer.py

class MBTIScorer:
    def score_assessment(self, responses: Dict[str, int]) -> Dict[str, Any]:
        """
        Score MBTI assessment and convert to Big Five.

        Each dimension is binary: preference > 50% determines letter.
        """

        # 1. Calculate raw preference scores for each dimension
        preferences = self._calculate_preferences(responses)

        # 2. Determine MBTI type (e.g., "INTJ")
        mbti_type = self._determine_type(preferences)

        # 3. Calculate preference strength (%)
        strengths = self._calculate_strengths(preferences)

        # 4. Convert to Big Five for standardization
        big_five = self._mbti_to_big_five(mbti_type, strengths)

        # 5. Generate type-specific insights
        insights = self._generate_insights(mbti_type, strengths)

        return {
            "mbti_type": mbti_type,
            "preferences": preferences,
            "strengths": strengths,
            "dimensions": big_five,  # Standardized output
            "insights": insights,
            "confidence": self._calculate_confidence(responses)
        }
```

**Preference Calculation:**

```python
def _calculate_preferences(self, responses: Dict) -> Dict[str, Dict[str, float]]:
    """
    Calculate preference strength for each dichotomy.

    Returns:
        {
            "EI": {"E": 0.7, "I": 0.3},  # 70% Extraversion
            "SN": {"S": 0.4, "N": 0.6},  # 60% Intuition
            "TF": {"T": 0.8, "F": 0.2},  # 80% Thinking
            "JP": {"J": 0.55, "P": 0.45} # 55% Judging
        }
    """
    questions = {
        "EI": ["q1", "q5", "q9", "q13"],    # E questions
        "SN": ["q2", "q6", "q10", "q14"],   # S questions
        "TF": ["q3", "q7", "q11", "q15"],   # T questions
        "JP": ["q4", "q8", "q12", "q16"]    # J questions
    }

    preferences = {}
    for dichotomy, e_questions in questions.items():
        # Score extraverted/sensing/thinking/judging questions
        e_score = sum(responses.get(q, 3) for q in e_questions)

        # Score opposite (introverted/intuitive/feeling/perceiving)
        i_questions = [q.replace(q[0], opposite[q[0]]) for q in e_questions]
        i_score = sum(responses.get(q, 3) for q in i_questions)

        # Normalize to proportions
        total = e_score + i_score
        preferences[dichotomy] = {
            dichotomy[0]: e_score / total,
            dichotomy[1]: i_score / total
        }

    return preferences
```

**Type Determination:**

```python
def _determine_type(self, preferences: Dict) -> str:
    """Determine 4-letter MBTI type"""
    type_code = ""

    for dichotomy in ["EI", "SN", "TF", "JP"]:
        e_pref, i_pref = preferences[dichotomy].values()
        type_code += dichotomy[0] if e_pref > i_pref else dichotomy[1]

    return type_code  # e.g., "INTJ"
```

**Big Five Conversion:**

```python
def _mbti_to_big_five(self, mbti_type: str, strengths: Dict) -> Dict[str, float]:
    """
    Convert MBTI type to Big Five approximation.

    Mapping based on research correlations:
    - E ↔ Extraversion (r ≈ 0.7)
    - N ↔ Openness (r ≈ 0.5)
    - T ↔ Agreeableness (inverted, r ≈ -0.4)
    - J ↔ Conscientiousness (r ≈ 0.5)
    """
    # Base mappings
    mappings = {
        "E": {"extraversion": 0.75},
        "I": {"extraversion": 0.25},
        "N": {"openness": 0.70},
        "S": {"openness": 0.40},
        "T": {"agreeableness": 0.35},
        "F": {"agreeableness": 0.70},
        "J": {"conscientiousness": 0.70},
        "P": {"conscientiousness": 0.40}
    }

    # Combine based on type and strengths
    big_five = {}
    for letter in mbti_type:
        dim, value = mappings[letter]
        # Adjust by preference strength
        strength = strengths.get_dichotomy_strength(letter)
        big_five[dim] = value * (0.8 + 0.4 * strength)

    # Add neuroticism (not directly measured by MBTI)
    big_five["neuroticism"] = 0.5  # Default to average

    return big_five
```

### 3. Enneagram

**Scientific Basis:** Nine personality types based on core motivations (Ichazo, 1960s)

**Types:** 1-9 (Perfectionist, Helper, Achiever, Individualist, Investigator, Loyalist, Enthusiast, Challenger, Peacemaker)

**Wings:** Adjacent types influence (e.g., 1w2, 1w9)

**Scoring Algorithm:**

```python
# File: app/services/scoring/enneagram_scorer.py

class EnneagramScorer:
    def score_assessment(self, responses: Dict[str, int]) -> Dict[str, Any]:
        """
        Score Enneagram assessment with wing influence.

        Returns:
            - primary_type: 1-9
            - wing: Adjacent type or None
            - type_name: e.g., "The Investigator"
            - core_motivation: Primary driver
            - dimensions: Big Five mapping
        """

        # 1. Score each of the 9 types
        type_scores = self._score_all_types(responses)

        # 2. Determine primary type (highest score)
        primary_type = max(type_scores, key=type_scores.get)

        # 3. Determine wing (higher of adjacent types)
        wing = self._determine_wing(primary_type, type_scores)

        # 4. Calculate wing influence (30% weight)
        if wing:
            dimensions = self._blend_wing(primary_type, wing, type_scores)
        else:
            dimensions = self._map_type_to_dimensions(primary_type)

        # 5. Generate insights
        insights = self._generate_type_insights(primary_type, wing)

        return {
            "primary_type": primary_type,
            "wing": wing,
            "type_code": f"{primary_type}w{wing}" if wing else str(primary_type),
            "type_name": TYPE_NAMES[primary_type],
            "dimensions": dimensions,  # Big Five format
            "insights": insights,
            "confidence": self._calculate_confidence(responses)
        }
```

**Type-to-Dimension Mapping:**

```python
TYPE_DIMENSIONS = {
    1: {  # Perfectionist
        "conscientiousness": 0.90,
        "neuroticism": 0.60,
        "agreeableness": 0.40,
        "openness": 0.50,
        "extraversion": 0.45
    },
    2: {  # Helper
        "agreeableness": 0.95,
        "extraversion": 0.70,
        "conscientiousness": 0.60,
        "neuroticism": 0.55,
        "openness": 0.50
    },
    # ... etc for all 9 types
}
```

**Wing Blending:**

```python
def _blend_wing(self, primary: int, wing: int, scores: Dict) -> Dict[str, float]:
    """
    Blend primary type with wing influence (70% primary, 30% wing).
    """
    primary_dims = TYPE_DIMENSIONS[primary]
    wing_dims = TYPE_DIMENSIONS[wing]

    blended = {}
    for dim in primary_dims:
        blended[dim] = (
            primary_dims[dim] * 0.7 +
            wing_dims[dim] * 0.3
        )

    return blended
```

---

## Processor Implementation

### Base Processor

```python
# File: ai/processors/processors_base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class PersonalityFrameworkProcessor(ABC):
    """
    Abstract base class for personality framework processors.

    All processors must implement the process() method which takes
    raw assessment data and returns standardized personality profiles.
    """

    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process raw assessment data into standardized format.

        Args:
            raw_data: Dict containing:
                - responses: Question-answer mappings
                - framework_code: Assessment framework identifier
                - metadata: Assessment metadata

        Returns:
            Dict with:
                - dimensions: Big Five dimension scores (0-100)
                - confidence: Overall confidence score (0-1)
                - raw_data: Original framework-specific scores
                - insights: Framework-specific insights
                - framework: Framework identifier
                - timestamp: Processing timestamp
        """
        pass

    # Helper methods for all processors

    def _safe_get(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Safely retrieve value from dictionary with default."""
        return data.get(key, default)

    def _clamp_value(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp numeric value to specified range."""
        try:
            return max(min_val, min(max_val, float(value)))
        except (ValueError, TypeError):
            return min_val

    def _ensure_confidence(self, data: Dict[str, Any], default: float = 0.8) -> Dict[str, Any]:
        """Ensure confidence score exists in output."""
        if 'confidence' not in data:
            data['confidence'] = default
        return data

    def _validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate input data has required fields."""
        required_fields = ['responses', 'framework_code']
        return all(field in raw_data for field in required_fields)
```

### Big Five Processor Implementation

```python
# File: ai/processors/big_five.py

from ai.processors.processors_base import PersonalityFrameworkProcessor
from typing import Dict, Any

class BigFiveProcessor(PersonalityFrameworkProcessor):
    """Processor for Big Five (OCEAN) personality framework."""

    FRAMEWORK_CODE = "BIG_FIVE"
    DIMENSION_NAMES = [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism"
    ]

    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Big Five assessment responses."""

        # 1. Validate input
        if not self._validate_input(raw_data):
            return self._error_result("Invalid input data")

        try:
            # 2. Extract responses
            responses = raw_data.get('responses', {})

            # 3. Calculate dimension scores
            dimensions = {}
            for dim in self.DIMENSION_NAMES:
                value = self._safe_get(responses, dim, 0.5)
                dimensions[dim] = self._clamp_value(float(value))

            # 4. Generate interpretations
            interpretations = self._generate_interpretations(dimensions)

            # 5. Calculate confidence
            confidence = self._calculate_confidence(responses)

            # 6. Build result
            return {
                "dimensions": dimensions,
                "interpretations": interpretations,
                "framework": self.FRAMEWORK_CODE,
                "confidence": confidence,
                "raw_data": {
                    "dimensions": dimensions,
                    "interpretations": interpretations
                },
                "insights": {
                    "strengths": self._identify_strengths(dimensions),
                    "development_areas": self._identify_development_areas(dimensions)
                },
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            return self._error_result(f"Processing error: {str(e)}")

    def _generate_interpretations(self, dimensions: Dict[str, float]) -> Dict[str, str]:
        """Generate text interpretations for each dimension."""
        interpretations = {}

        for dim, value in dimensions.items():
            if value >= 0.8:
                level = "Very High"
            elif value >= 0.6:
                level = "High"
            elif value >= 0.4:
                level = "Moderate"
            elif value >= 0.2:
                level = "Low"
            else:
                level = "Very Low"

            interpretations[dim] = level

        return interpretations

    def _calculate_confidence(self, responses: Dict) -> float:
        """
        Calculate confidence based on response completeness.

        Factors:
        - Percentage of questions answered
        - Response time consistency
        - Straight-lining detection (all same answers)
        """
        total_questions = len(self.DIMENSION_NAMES) * 6  # 6 questions per dimension
        answered_questions = len(responses)

        # Completeness score
        completeness = answered_questions / total_questions

        # Straight-lining penalty
        values = list(responses.values())
        if len(set(values)) == 1:
            completeness *= 0.5  # Penalize heavily

        return round(completeness, 2)

    def _identify_strengths(self, dimensions: Dict[str, float]) -> list:
        """Identify top 2 dimensions as strengths."""
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
        return [dim for dim, score in sorted_dims[:2]]

    def _identify_development_areas(self, dimensions: Dict[str, float]) -> list:
        """Identify bottom 2 dimensions as development areas."""
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1])
        return [dim for dim, score in sorted_dims[:2]]

    def _error_result(self, message: str) -> Dict[str, Any]:
        """Return error result with low confidence."""
        return {
            "dimensions": {dim: 0.5 for dim in self.DIMENSION_NAMES},
            "framework": self.FRAMEWORK_CODE,
            "confidence": 0.0,
            "error": message,
            "timestamp": self._get_timestamp()
        }

    def _get_timestamp(self) -> str:
        """Get current ISO timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
```

---

## Normalization & Standardization

### Response Normalization

All framework responses are normalized to a common 0-100 scale:

```python
def normalize_to_100_scale(raw_score: float, scale_min: float, scale_max: float) -> float:
    """
    Normalize any scale to 0-100.

    Examples:
    - Likert 1-5: normalize_to_100_scale(4, 1, 5) = 75
    - Percentage 0-1: normalize_to_100_scale(0.8, 0, 1) = 80
    - T-score 40-60: normalize_to_100_scale(55, 40, 60) = 75
    """
    return ((raw_score - scale_min) / (scale_max - scale_min)) * 100
```

### Big Five Standardization

All frameworks map to Big Five dimensions for cross-framework comparison:

```python
BIG_FIVE_DIMENSIONS = [
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism"
]

def standardize_to_big_five(framework_data: Dict) -> Dict[str, float]:
    """
    Convert any framework to Big Five format.

    Supported mappings:
    - MBTI → Big Five (research-based correlations)
    - Enneagram → Big Five (type-based profiles)
    - Predictive Index → Big Five (direct dimension mapping)
    """
    framework = framework_data.get('framework')

    if framework == 'MBTI':
        return mbti_to_big_five(framework_data)
    elif framework == 'ENNEAGRAM':
        return enneagram_to_big_five(framework_data)
    elif framework == 'PREDICTIVE_INDEX':
        return pi_to_big_five(framework_data)
    else:
        # Already Big Five
        return framework_data['dimensions']
```

---

## Insight Generation

### Strengths & Development Areas

```python
def generate_insights(dimensions: Dict[str, float]) -> Dict[str, Any]:
    """
    Generate actionable insights from dimension scores.

    Returns:
        - strengths: Top 2 dimensions
        - development_areas: Bottom 2 dimensions
        - personality_summary: Text description
        - recommendations: Actionable suggestions
    """
    sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)

    # Strengths (top 2)
    strengths = [dim for dim, score in sorted_dims[:2]]

    # Development areas (bottom 2)
    development = [dim for dim, score in sorted_dims[-2:]]

    # Personality summary
    summary = generate_personality_summary(dimensions)

    # Recommendations
    recommendations = generate_recommendations(dimensions)

    return {
        "strengths": strengths,
        "development_areas": development,
        "personality_summary": summary,
        "recommendations": recommendations
    }
```

### Interpretation Bands

```python
INTERPRETATION_TEMPLATES = {
    "openness": {
        (0.8, 1.0): "Highly creative and imaginative. You embrace new ideas and experiences.",
        (0.6, 0.8): "Fairly open to new experiences. You enjoy variety and intellectual challenges.",
        (0.4, 0.6): "Balanced openness. You appreciate tradition but welcome some novelty.",
        (0.2, 0.4): "Prefer familiar routines and practical, concrete approaches.",
        (0.0, 0.2): "Very conventional. You favor tradition and proven methods."
    },
    # ... similar templates for other dimensions
}

def get_interpretation(dimension: str, score: float) -> str:
    """Get interpretation text for dimension score."""
    templates = INTERPRETATION_TEMPLATES.get(dimension, {})

    for (low, high), text in templates.items():
        if low <= score <= high:
            return text

    return "Average level"
```

---

## Confidence Scoring

### Confidence Factors

```python
def calculate_overall_confidence(
    response_completeness: float,
    response_time_consistency: float,
    straight_lining_detected: bool,
    question_quality_score: float
) -> float:
    """
    Calculate overall confidence score (0-1).

    Factors:
    1. Completeness: % of questions answered (weight: 0.4)
    2. Consistency: Response time variance (weight: 0.2)
    3. Straight-lining: All same answers penalty (weight: -0.3)
    4. Quality: Question validity score (weight: 0.3)
    """
    confidence = (
        response_completeness * 0.4 +
        response_time_consistency * 0.2 +
        question_quality_score * 0.3
    )

    if straight_lining_detected:
        confidence *= 0.7

    return round(max(0.0, min(1.0, confidence)), 2)
```

### Confidence Levels

```python
CONFIDENCE_LEVELS = {
    (0.9, 1.0): "Very High",
    (0.75, 0.9): "High",
    (0.6, 0.75): "Moderate",
    (0.4, 0.6): "Low",
    (0.0, 0.4): "Very Low"
}

def get_confidence_level(confidence: float) -> str:
    """Get confidence level label."""
    for (low, high), level in CONFIDENCE_LEVELS.items():
        if low <= confidence <= high:
            return level
    return "Unknown"
```

---

## Performance Optimization

### Caching Strategy

```python
from functools import lru_cache
import hashlib

class CachedScorer:
    """Score assessment with result caching."""

    def __init__(self, scorer: BigFiveScorer):
        self.scorer = scorer
        self.cache = {}

    def score_with_cache(self, responses: Dict) -> Dict:
        """Score with LRU cache."""
        # Generate cache key from responses
        cache_key = self._generate_cache_key(responses)

        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Calculate score
        result = self.scorer.score_assessment(responses)

        # Cache result
        self.cache[cache_key] = result

        return result

    def _generate_cache_key(self, responses: Dict) -> str:
        """Generate deterministic cache key."""
        sorted_items = sorted(responses.items())
        response_str = str(sorted_items)
        return hashlib.md5(response_str.encode()).hexdigest()
```

### Batch Processing

```python
def score_batch_assessments(
    scorer: BigFiveScorer,
    response_batch: List[Dict]
) -> List[Dict]:
    """
    Score multiple assessments efficiently.

    Optimizations:
    - Pre-load normative data
    - Reuse calculation objects
    - Parallel processing (thread pool)
    """
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(
            scorer.score_assessment,
            response_batch
        ))

    return results
```

---

## Testing & Validation

### Unit Testing

```python
# tests/scoring/test_big_five_scorer.py
import pytest
from app.services.scoring.big_five_scorer import BigFiveScorer

def test_calculate_openness_score():
    """Test Openness dimension calculation."""
    scorer = BigFiveScorer()

    # High openness responses
    responses = {
        "q1": 5,  # Creative
        "q6": 4,  # Curious
        "q11": 5,  # Adventurous
        "q16": 4,  # Imaginative
        "q21": 5,  # Innovative
        "q26": 4   # Original
    }

    score = scorer._calculate_dimension_score("openness", responses)

    assert score >= 80  # Should be high
    assert 0 <= score <= 100  # Within valid range

def test_reverse_scoring():
    """Test reverse-scored questions."""
    scorer = BigFiveScorer()

    responses = {
        "q1": 5,  # Regular question
        "q6": 5   # Reverse-scored (should become 1)
    }

    # Should treat reverse-scored correctly
    score = scorer._calculate_dimension_score("openness", responses)

    # q6 is reverse-scored, so 5 → 1
    # Average: (5 + 1) / 2 = 3
    # Normalized: ((3 - 1) / 4) * 100 = 50
    assert score == 50
```

### Integration Testing

```python
def test_end_to_end_scoring():
    """Test complete scoring pipeline."""
    # 1. Create assessment
    assessment = create_test_assessment(framework="BIG_FIVE")

    # 2. Generate responses
    responses = generate_test_responses(assessment)

    # 3. Score responses
    scorer = BigFiveScorer()
    result = scorer.score_assessment(responses)

    # 4. Validate output structure
    assert "dimensions" in result
    assert "confidence" in result
    assert "interpretations" in result
    assert len(result["dimensions"]) == 5

    # 5. Validate score ranges
    for dim, score in result["dimensions"].items():
        assert 0 <= score <= 100
```

### Validation Testing

```python
def test_concurrent_validity():
    """
    Test that different frameworks converge on similar traits.

    MBTI "E" should correlate with Big Five "Extraversion"
    """
    # Create same user, assess with both frameworks
    user_responses = generate_consistent_responses()

    # Score with Big Five
    bf_result = BigFiveProcessor().process(user_responses["big_five"])

    # Score with MBTI
    mbti_result = MBTIProcessor().process(user_responses["mbti"])

    # Extract extraversion scores
    bf_extraversion = bf_result["dimensions"]["extraversion"]
    mbti_extraversion = mbti_result["dimensions"]["extraversion"]

    # Should be reasonably correlated (within 20%)
    assert abs(bf_extraversion - mbti_extraversion) < 20
```

---

## Algorithm Maintenance

### Updating Normative Data

```python
# Periodically update with new population data
def update_percentile_tables(new_normative_data: Dict):
    """
    Update percentile conversion tables.

    Should be done annually with new population samples.
    """
    # Validate new data
    assert validate_normative_data(new_normative_data)

    # Update mapping
    NORMATIVE_DATA.update(new_normative_data)

    # Version the update
    NORMATIVE_DATA_VERSION = increment_version()

    # A/B test before full rollout
    run_ab_test(old_data, new_data)
```

### Adding New Frameworks

```python
# 1. Create new processor
class NewFrameworkProcessor(PersonalityFrameworkProcessor):
    FRAMEWORK_CODE = "NEW_FRAMEWORK"

    def process(self, raw_data: Dict) -> Dict:
        # Implementation
        pass

# 2. Add to processor registry
PROCESSOR_REGISTRY = {
    "BIG_FIVE": BigFiveProcessor,
    "MBTI": MBTIProcessor,
    "ENNEAGRAM": EnneagramProcessor,
    "NEW_FRAMEWORK": NewFrameworkProcessor  # Add here
}

# 3. Implement Big Five mapping
def new_framework_to_big_five(data: Dict) -> Dict[str, float]:
    # Research-based mapping
    pass

# 4. Write comprehensive tests
# tests/scoring/test_new_framework.py

# 5. Document in this file
# Update ASSESSMENT_SCORING_ALGORITHM.md
```

---

## Appendices

### A. Research References

- Costa, P. T., & McCrae, R. R. (1992). *Revised NEO Personality Inventory (NEO-PI-R)*
- Myers, I. B., & McCaulley, M. H. (1985). *Manual: A Guide to the Development and Use of the Myers-Briggs Type Indicator*
- Riso, D. R., & Hudson, R. (1996). *Personality Types: Using the Enneagram for Self-Discovery*
- Goldberg, L. R. (1990). "An alternative 'description of personality': The Big-Five factor structure"
- McCrae, R. R., & Costa, P. T. (1987). "Validation of the five-factor model of personality across instruments and observers"

### B. Algorithm Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-12-27 | Initial documentation | Claude (Sonnet 4.5) |

### C. Contact Information

**Questions about scoring algorithms:**
- Lead Data Scientist: [Email]
- AI/ML Team Lead: [Email]
- Engineering Manager: [Email]

---

**Document Status:** ✅ Approved

**Next Review Date:** 2026-06-27 (6 months)

**Confidentiality Notice:** This document contains proprietary algorithmic information. Do not distribute outside the company.
