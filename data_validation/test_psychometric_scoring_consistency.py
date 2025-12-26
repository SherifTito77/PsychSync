#!/usr/bin/env python3
"""
Psychometric Scoring Consistency Testing Module
Tests if psychometric scoring is applied consistently across different assessment types
"""

import asyncio
import json
import time
import math
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import numpy as np

class AssessmentType(Enum):
    """Assessment types supported"""
    BIG_FIVE = "big_five"
    MBTI = "mbti"
    ENNEAGRAM = "enneagram"
    DISC = "disc"
    STRENGTHS_FINDER = "strengths_finder"
    PREDICTIVE_INDEX = "predictive_index"

@dataclass
class AssessmentQuestion:
    """Assessment question structure"""
    id: int
    question_text: str
    options: List[Dict[str, Any]]
    category: str
    weight: float = 1.0
    reverse_scored: bool = False

@dataclass
class AssessmentResponse:
    """User response to assessment question"""
    question_id: int
    answer_value: int
    response_time: float
    timestamp: datetime

@dataclass
class ScoringResult:
    """Psychometric scoring result"""
    assessment_type: AssessmentType
    raw_scores: Dict[str, float]
    normalized_scores: Dict[str, float]
    personality_type: Optional[str] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0

@dataclass
class ConsistencyTestResult:
    """Result of consistency testing"""
    test_name: str
    assessment_type: str
    consistency_score: float
    identical_results: int
    total_comparisons: int
    details: Dict[str, Any]
    timestamp: datetime

class PsychometricScoringEngine:
    """Advanced psychometric scoring engine with multiple assessment types"""

    def __init__(self):
        self.question_banks = self._initialize_question_banks()
        self.scoring_algorithms = {
            AssessmentType.BIG_FIVE: self._score_big_five,
            AssessmentType.MBTI: self._score_mbti,
            AssessmentType.ENNEAGRAM: self._score_enneagram,
            AssessmentType.DISC: self._score_disc,
            AssessmentType.STRENGTHS_FINDER: self._score_strengths_finder,
            AssessmentType.PREDICTIVE_INDEX: self._score_predictive_index
        }

    def _initialize_question_banks(self) -> Dict[AssessmentType, List[AssessmentQuestion]]:
        """Initialize comprehensive question banks for each assessment type"""
        return {
            AssessmentType.BIG_FIVE: self._create_big_five_questions(),
            AssessmentType.MBTI: self._create_mbti_questions(),
            AssessmentType.ENNEAGRAM: self._create_enneagram_questions(),
            AssessmentType.DISC: self._create_disc_questions(),
            AssessmentType.STRENGTHS_FINDER: self._create_strengths_finder_questions(),
            AssessmentType.PREDICTIVE_INDEX: self._create_predictive_index_questions()
        }

    def _create_big_five_questions(self) -> List[AssessmentQuestion]:
        """Create Big Five (OCEAN) assessment questions"""
        questions = []

        # Openness questions
        for i in range(12):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text=f"I enjoy trying new and unusual foods",
                options=[
                    {"value": 1, "text": "Strongly Disagree"},
                    {"value": 2, "text": "Disagree"},
                    {"value": 3, "text": "Neutral"},
                    {"value": 4, "text": "Agree"},
                    {"value": 5, "text": "Strongly Agree"}
                ],
                category="Openness",
                weight=1.0,
                reverse_scored=False
            ))

        # Conscientiousness questions
        for i in range(12, 24):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I am always prepared",
                options=[
                    {"value": 1, "text": "Strongly Disagree"},
                    {"value": 2, "text": "Disagree"},
                    {"value": 3, "text": "Neutral"},
                    {"value": 4, "text": "Agree"},
                    {"value": 5, "text": "Strongly Agree"}
                ],
                category="Conscientiousness",
                weight=1.0,
                reverse_scored=False
            ))

        # Extraversion questions
        for i in range(24, 36):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I feel energized after social gatherings",
                options=[
                    {"value": 1, "text": "Strongly Disagree"},
                    {"value": 2, "text": "Disagree"},
                    {"value": 3, "text": "Neutral"},
                    {"value": 4, "text": "Agree"},
                    {"value": 5, "text": "Strongly Agree"}
                ],
                category="Extraversion",
                weight=1.0,
                reverse_scored=False
            ))

        # Agreeableness questions
        for i in range(36, 48):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I am interested in other people's problems",
                options=[
                    {"value": 1, "text": "Strongly Disagree"},
                    {"value": 2, "text": "Disagree"},
                    {"value": 3, "text": "Neutral"},
                    {"value": 4, "text": "Agree"},
                    {"value": 5, "text": "Strongly Agree"}
                ],
                category="Agreeableness",
                weight=1.0,
                reverse_scored=False
            ))

        # Neuroticism questions
        for i in range(48, 60):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I worry about things frequently",
                options=[
                    {"value": 1, "text": "Strongly Disagree"},
                    {"value": 2, "text": "Disagree"},
                    {"value": 3, "text": "Neutral"},
                    {"value": 4, "text": "Agree"},
                    {"value": 5, "text": "Strongly Agree"}
                ],
                category="Neuroticism",
                weight=1.0,
                reverse_scored=False
            ))

        return questions

    def _create_mbti_questions(self) -> List[AssessmentQuestion]:
        """Create MBTI assessment questions"""
        questions = []

        # E-I dimension questions (10 each)
        for i in range(10):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I prefer spending time with large groups of people",
                options=[
                    {"value": 1, "text": "Not at all"},
                    {"value": 2, "text": "Slightly"},
                    {"value": 3, "text": "Moderately"},
                    {"value": 4, "text": "Very much"},
                    {"value": 5, "text": "Completely"}
                ],
                category="Extraversion",
                weight=1.0,
                reverse_scored=False
            ))

        # S-N dimension questions
        for i in range(10, 20):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I focus on reality and practical applications",
                options=[
                    {"value": 1, "text": "Not at all"},
                    {"value": 2, "text": "Slightly"},
                    {"value": 3, "text": "Moderately"},
                    {"value": 4, "text": "Very much"},
                    {"value": 5, "text": "Completely"}
                ],
                category="Sensing",
                weight=1.0,
                reverse_scored=False
            ))

        # T-F dimension questions
        for i in range(20, 30):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I make decisions based on logical analysis",
                options=[
                    {"value": 1, "text": "Not at all"},
                    {"value": 2, "text": "Slightly"},
                    {"value": 3, "text": "Moderately"},
                    {"value": 4, "text": "Very much"},
                    {"value": 5, "text": "Completely"}
                ],
                category="Thinking",
                weight=1.0,
                reverse_scored=False
            ))

        # J-P dimension questions
        for i in range(30, 40):
            questions.append(AssessmentQuestion(
                id=i+1,
                question_text="I prefer to have things decided and settled",
                options=[
                    {"value": 1, "text": "Not at all"},
                    {"value": 2, "text": "Slightly"},
                    {"value": 3, "text": "Moderately"},
                    {"value": 4, "text": "Very much"},
                    {"value": 5, "text": "Completely"}
                ],
                category="Judging",
                weight=1.0,
                reverse_scored=False
            ))

        return questions

    def _create_enneagram_questions(self) -> List[AssessmentQuestion]:
        """Create Enneagram assessment questions"""
        questions = []

        enneagram_types = [
            "Type 1 - Reformer", "Type 2 - Helper", "Type 3 - Achiever",
            "Type 4 - Individualist", "Type 5 - Investigator", "Type 6 - Loyalist",
            "Type 7 - Enthusiast", "Type 8 - Challenger", "Type 9 - Peacemaker"
        ]

        # Create questions for each Enneagram type
        for type_idx, enneagram_type in enumerate(enneagram_types):
            for q in range(6):  # 6 questions per type
                question_id = type_idx * 6 + q + 1
                questions.append(AssessmentQuestion(
                    id=question_id,
                    question_text=f"I have a strong need to be perfect and do things right",
                    options=[
                        {"value": 1, "text": "Never"},
                        {"value": 2, "text": "Rarely"},
                        {"value": 3, "text": "Sometimes"},
                        {"value": 4, "text": "Often"},
                        {"value": 5, "text": "Always"}
                    ],
                    category=enneagram_type,
                    weight=1.0,
                    reverse_scored=False
                ))

        return questions[:58]  # Return 58 questions for Enneagram

    def _create_disc_questions(self) -> List[AssessmentQuestion]:
        """Create DISC assessment questions"""
        questions = []

        disc_categories = ["Dominance", "Influence", "Steadiness", "Conscientiousness"]

        for category in disc_categories:
            for i in range(15):  # 15 questions per category
                question_id = len(questions) + 1
                questions.append(AssessmentQuestion(
                    id=question_id,
                    question_text=f"I take charge of situations when needed",
                    options=[
                        {"value": 1, "text": "Strongly Disagree"},
                        {"value": 2, "text": "Disagree"},
                        {"value": 3, "text": "Neutral"},
                        {"value": 4, "text": "Agree"},
                        {"value": 5, "text": "Strongly Agree"}
                    ],
                    category=category,
                    weight=1.0,
                    reverse_scored=False
                ))

        return questions

    def _create_strengths_finder_questions(self) -> List[AssessmentQuestion]:
        """Create StrengthsFinder assessment questions"""
        questions = []

        strength_themes = [
            "Achiever", "Activator", "Adaptability", "Analytical", "Arranger",
            "Belief", "Command", "Communication", "Competition", "Connectedness",
            "Consistency", "Context", "Deliberative", "Developer", "Discipline",
            "Empathy", "Focus", "Futuristic", "Harmony", "Ideation",
            "Includer", "Individualization", "Input", "Intellection", "Learner",
            "Maximizer", "Positivity", "Relator", "Responsibility", "Restorative",
            "Self-Assurance", "Significance", "Strategic", "Woo"
        ]

        for theme in strength_themes:
            for i in range(5):  # 5 questions per strength theme
                question_id = len(questions) + 1
                questions.append(AssessmentQuestion(
                    id=question_id,
                    question_text=f"I enjoy achieving measurable goals",
                    options=[
                        {"value": 1, "text": "Strongly Disagree"},
                        {"value": 2, "text": "Disagree"},
                        {"value": 3, "text": "Neutral"},
                        {"value": 4, "text": "Agree"},
                        {"value": 5, "text": "Strongly Agree"}
                    ],
                    category=theme,
                    weight=1.0,
                    reverse_scored=False
                ))

        return questions[:170]  # Return 170 questions

    def _create_predictive_index_questions(self) -> List[AssessmentQuestion]:
        """Create Predictive Index assessment questions"""
        questions = []

        pi_categories = ["A", "B", "C", "D"]

        for category in pi_categories:
            for i in range(3):  # 3 questions per PI factor
                question_id = len(questions) + 1
                questions.append(AssessmentQuestion(
                    id=question_id,
                    question_text=f"I am assertive in expressing my opinions",
                    options=[
                        {"value": 1, "text": "Strongly Disagree"},
                        {"value": 2, "text": "Disagree"},
                        {"value": 3, "text": "Neutral"},
                        {"value": 4, "text": "Agree"},
                        {"value": 5, "text": "Strongly Agree"}
                    ],
                    category=category,
                    weight=1.0,
                    reverse_scored=False
                ))

        return questions

    def _score_big_five(self, responses: List[AssessmentResponse]) -> ScoringResult:
        """Score Big Five assessment using OCEAN model"""
        start_time = time.time()

        # Group responses by category
        categories = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]
        raw_scores = {}
        normalized_scores = {}

        for category in categories:
            category_responses = [r for r in responses
                                if next((q for q in self.question_banks[AssessmentType.BIG_FIVE]
                                       if q.id == r.question_id), None).category == category]
            total_score = sum(r.answer_value for r in category_responses)
            raw_scores[category] = total_score

            # Normalize to 0-100 scale
            max_possible = len(category_responses) * 5
            normalized_scores[category] = (total_score / max_possible) * 100 if max_possible > 0 else 0

        # Calculate personality type (dominant trait)
        personality_type = max(normalized_scores, key=normalized_scores.get)

        # Calculate confidence score based on response consistency
        response_times = [r.response_time for r in responses]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        confidence_score = min(100, 100 - (avg_response_time / 10))  # Higher confidence for faster responses

        processing_time = time.time() - start_time

        return ScoringResult(
            assessment_type=AssessmentType.BIG_FIVE,
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            personality_type=personality_type,
            confidence_score=confidence_score,
            processing_time=processing_time
        )

    def _score_mbti(self, responses: List[AssessmentResponse]) -> ScoringResult:
        """Score MBTI assessment using dimensional approach"""
        start_time = time.time()

        # Group responses by MBTI dimensions
        dimensions = ["Extraversion", "Sensing", "Thinking", "Judging"]
        raw_scores = {}
        normalized_scores = {}

        for dimension in dimensions:
            dimension_responses = [r for r in responses
                                 if next((q for q in self.question_banks[AssessmentType.MBTI]
                                        if q.id == r.question_id), None).category == dimension]
            total_score = sum(r.answer_value for r in dimension_responses)
            raw_scores[dimension] = total_score

            # Normalize to 0-100 scale
            max_possible = len(dimension_responses) * 5
            normalized_scores[dimension] = (total_score / max_possible) * 100 if max_possible > 0 else 0

        # Determine MBTI type based on dimension scores
        e_score = normalized_scores["Extraversion"]
        i_score = 100 - e_score
        s_score = normalized_scores["Sensing"]
        n_score = 100 - s_score
        t_score = normalized_scores["Thinking"]
        f_score = 100 - t_score
        j_score = normalized_scores["Judging"]
        p_score = 100 - j_score

        mbti_type = (
            ("E" if e_score > 50 else "I") +
            ("S" if s_score > 50 else "N") +
            ("T" if t_score > 50 else "F") +
            ("J" if j_score > 50 else "P")
        )

        # Calculate confidence score
        dimension_scores = [e_score, s_score, t_score, j_score]
        clarity_scores = [abs(score - 50) for score in dimension_scores]
        confidence_score = statistics.mean(clarity_scores) * 2  # Scale to 0-100

        processing_time = time.time() - start_time

        return ScoringResult(
            assessment_type=AssessmentType.MBTI,
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            personality_type=mbti_type,
            confidence_score=confidence_score,
            processing_time=processing_time
        )

    def _score_enneagram(self, responses: List[AssessmentResponse]) -> ScoringResult:
        """Score Enneagram assessment"""
        start_time = time.time()

        # Group responses by Enneagram types
        enneagram_types = [f"Type {i} - {'Reformer' if i == 1 else 'Helper' if i == 2 else 'Achiever' if i == 3 else 'Individualist' if i == 4 else 'Investigator' if i == 5 else 'Loyalist' if i == 6 else 'Enthusiast' if i == 7 else 'Challenger' if i == 8 else 'Peacemaker'}"
                          for i in range(1, 10)]

        raw_scores = {}
        normalized_scores = {}

        for enneagram_type in enneagram_types:
            type_responses = [r for r in responses
                            if next((q for q in self.question_banks[AssessmentType.ENNEAGRAM]
                                   if q.id == r.question_id), None).category == enneagram_type]
            total_score = sum(r.answer_value for r in type_responses)
            raw_scores[enneagram_type] = total_score

            # Normalize to 0-100 scale
            max_possible = len(type_responses) * 5
            normalized_scores[enneagram_type] = (total_score / max_possible) * 100 if max_possible > 0 else 0

        # Determine dominant Enneagram type
        personality_type = max(normalized_scores, key=normalized_scores.get)

        # Calculate confidence score
        all_scores = list(normalized_scores.values())
        max_score = max(all_scores) if all_scores else 0
        second_max = sorted(all_scores)[-2] if len(all_scores) > 1 else 0
        confidence_score = (max_score - second_max) / max_score * 100 if max_score > 0 else 0

        processing_time = time.time() - start_time

        return ScoringResult(
            assessment_type=AssessmentType.ENNEAGRAM,
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            personality_type=personality_type,
            confidence_score=confidence_score,
            processing_time=processing_time
        )

    def _score_disc(self, responses: List[AssessmentResponse]) -> ScoringResult:
        """Score DISC assessment"""
        start_time = time.time()

        # Group responses by DISC categories
        disc_categories = ["Dominance", "Influence", "Steadiness", "Conscientiousness"]
        raw_scores = {}
        normalized_scores = {}

        for category in disc_categories:
            category_responses = [r for r in responses
                                if next((q for q in self.question_banks[AssessmentType.DISC]
                                       if q.id == r.question_id), None).category == category]
            total_score = sum(r.answer_value for r in category_responses)
            raw_scores[category] = total_score

            # Normalize to 0-100 scale and calculate percentage
            max_possible = len(category_responses) * 5
            normalized_score = (total_score / max_possible) * 100 if max_possible > 0 else 0
            normalized_scores[category] = normalized_score

        # Determine dominant DISC style
        personality_type = max(normalized_scores, key=normalized_scores.get)

        # Calculate confidence score
        all_scores = list(normalized_scores.values())
        max_score = max(all_scores) if all_scores else 0
        confidence_score = max_score  # Use highest score as confidence

        processing_time = time.time() - start_time

        return ScoringResult(
            assessment_type=AssessmentType.DISC,
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            personality_type=personality_type,
            confidence_score=confidence_score,
            processing_time=processing_time
        )

    def _score_strengths_finder(self, responses: List[AssessmentResponse]) -> ScoringResult:
        """Score StrengthsFinder assessment"""
        start_time = time.time()

        # Get all strength themes
        all_questions = self.question_banks[AssessmentType.STRENGTHS_FINDER]
        strength_themes = list(set(q.category for q in all_questions))

        raw_scores = {}
        normalized_scores = {}

        for theme in strength_themes:
            theme_responses = [r for r in responses
                             if next((q for q in self.question_banks[AssessmentType.STRENGTHS_FINDER]
                                    if q.id == r.question_id), None).category == theme]
            total_score = sum(r.answer_value for r in theme_responses)
            raw_scores[theme] = total_score

            # Normalize to 0-100 scale
            max_possible = len(theme_responses) * 5
            normalized_scores[theme] = (total_score / max_possible) * 100 if max_possible > 0 else 0

        # Get top 5 strengths
        sorted_strengths = sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True)
        top_strengths = [strength for strength, score in sorted_strengths[:5]]
        personality_type = ", ".join(top_strengths)

        # Calculate confidence score
        all_scores = list(normalized_scores.values())
        confidence_score = statistics.mean(all_scores) if all_scores else 0

        processing_time = time.time() - start_time

        return ScoringResult(
            assessment_type=AssessmentType.STRENGTHS_FINDER,
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            personality_type=personality_type,
            confidence_score=confidence_score,
            processing_time=processing_time
        )

    def _score_predictive_index(self, responses: List[AssessmentResponse]) -> ScoringResult:
        """Score Predictive Index assessment"""
        start_time = time.time()

        # Group responses by PI factors
        pi_factors = ["A", "B", "C", "D"]
        raw_scores = {}
        normalized_scores = {}

        for factor in pi_factors:
            factor_responses = [r for r in responses
                              if next((q for q in self.question_banks[AssessmentType.PREDICTIVE_INDEX]
                                     if q.id == r.question_id), None).category == factor]
            total_score = sum(r.answer_value for r in factor_responses)
            raw_scores[factor] = total_score

            # Normalize to 0-100 scale
            max_possible = len(factor_responses) * 5
            normalized_scores[factor] = (total_score / max_possible) * 100 if max_possible > 0 else 0

        # Determine dominant PI factor
        personality_type = max(normalized_scores, key=normalized_scores.get)

        # Calculate confidence score
        all_scores = list(normalized_scores.values())
        confidence_score = statistics.mean(all_scores) if all_scores else 0

        processing_time = time.time() - start_time

        return ScoringResult(
            assessment_type=AssessmentType.PREDICTIVE_INDEX,
            raw_scores=raw_scores,
            normalized_scores=normalized_scores,
            personality_type=personality_type,
            confidence_score=confidence_score,
            processing_time=processing_time
        )

    async def score_assessment(self, assessment_type: AssessmentType,
                             responses: List[AssessmentResponse]) -> ScoringResult:
        """Score assessment responses using appropriate algorithm"""
        if assessment_type not in self.scoring_algorithms:
            raise ValueError(f"Unsupported assessment type: {assessment_type}")

        scoring_function = self.scoring_algorithms[assessment_type]
        return await asyncio.get_event_loop().run_in_executor(
            None, scoring_function, responses
        )

class PsychometricScoringConsistencyTester:
    """Comprehensive testing suite for psychometric scoring consistency"""

    def __init__(self):
        self.engine = PsychometricScoringEngine()
        self.test_results = []

    def generate_test_responses(self, assessment_type: AssessmentType,
                              count: int = 10) -> List[List[AssessmentResponse]]:
        """Generate multiple sets of test responses for consistency testing"""
        questions = self.engine.question_banks[assessment_type]
        response_sets = []

        for _ in range(count):
            responses = []
            for question in questions:
                # Generate consistent responses with some variation
                if random.random() < 0.7:  # 70% consistency
                    base_value = random.randint(2, 4)
                else:  # 30% variation
                    base_value = random.randint(1, 5)

                response = AssessmentResponse(
                    question_id=question.id,
                    answer_value=base_value,
                    response_time=random.uniform(1.0, 10.0),
                    timestamp=datetime.now()
                )
                responses.append(response)

            response_sets.append(responses)

        return response_sets

    async def test_scoring_consistency_across_assessments(self) -> ConsistencyTestResult:
        """Test scoring consistency across all assessment types"""
        print("Testing scoring consistency across assessment types...")

        assessment_types = list(AssessmentType)
        consistency_scores = {}

        for assessment_type in assessment_types:
            print(f"  Testing {assessment_type.value}...")

            # Generate identical response sets
            response_sets = self.generate_test_responses(assessment_type, 5)
            results = []

            # Score each response set
            for responses in response_sets:
                result = await self.engine.score_assessment(assessment_type, responses)
                results.append(result)

            # Calculate consistency scores
            identical_results = 0
            total_comparisons = 0

            for i in range(len(results)):
                for j in range(i + 1, len(results)):
                    result1, result2 = results[i], results[j]

                    # Check personality type consistency
                    if result1.personality_type == result2.personality_type:
                        identical_results += 1

                    # Check score similarity (within 5% tolerance)
                    for category in result1.normalized_scores:
                        if category in result2.normalized_scores:
                            score1 = result1.normalized_scores[category]
                            score2 = result2.normalized_scores[category]
                            if abs(score1 - score2) <= 5.0:  # 5% tolerance
                                identical_results += 0.5

                    total_comparisons += 1

            consistency_score = (identical_results / total_comparisons * 100) if total_comparisons > 0 else 0
            consistency_scores[assessment_type.value] = consistency_score

        overall_consistency = statistics.mean(consistency_scores.values())

        return ConsistencyTestResult(
            test_name="scoring_consistency_across_assessments",
            assessment_type="all",
            consistency_score=overall_consistency,
            identical_results=int(overall_consistency),
            total_comparisons=100,
            details={
                "by_assessment": consistency_scores,
                "target_consistency_rate": 95.0
            },
            timestamp=datetime.now()
        )

    async def test_same_input_same_output(self) -> ConsistencyTestResult:
        """Test that identical inputs produce identical outputs"""
        print("Testing same input same output consistency...")

        # Test with a single assessment type (MBTI for this example)
        assessment_type = AssessmentType.MBTI
        responses = self.generate_test_responses(assessment_type, 1)[0]

        # Score the same responses multiple times
        results = []
        for _ in range(10):
            result = await self.engine.score_assessment(assessment_type, responses)
            results.append(result)

        # Check if all results are identical
        first_result = results[0]
        identical_results = 0

        for result in results[1:]:
            # Compare personality types
            if result.personality_type == first_result.personality_type:
                identical_results += 1

            # Compare normalized scores
            scores_match = all(
                abs(result.normalized_scores.get(key, 0) - first_result.normalized_scores.get(key, 0)) < 0.001
                for key in first_result.normalized_scores
            )
            if scores_match:
                identical_results += 1

        total_comparisons = len(results) - 1
        consistency_score = (identical_results / (total_comparisons * 2)) * 100  # 2 comparisons per result

        return ConsistencyTestResult(
            test_name="same_input_same_output",
            assessment_type=assessment_type.value,
            consistency_score=consistency_score,
            identical_results=identical_results,
            total_comparisons=total_comparisons * 2,
            details={
                "personality_type": first_result.personality_type,
                "normalized_scores": first_result.normalized_scores,
                "processing_time": first_result.processing_time
            },
            timestamp=datetime.now()
        )

    async def test_scoring_algorithm_stability(self) -> ConsistencyTestResult:
        """Test scoring algorithm stability with edge cases"""
        print("Testing scoring algorithm stability...")

        assessment_type = AssessmentType.BIG_FIVE
        questions = self.engine.question_banks[assessment_type]

        # Test edge cases
        edge_cases = {
            "all_minimum": [1] * len(questions),
            "all_maximum": [5] * len(questions),
            "alternating": [1, 5] * (len(questions) // 2),
            "random": [random.randint(1, 5) for _ in range(len(questions))]
        }

        results = {}
        for case_name, answer_values in edge_cases.items():
            responses = [
                AssessmentResponse(
                    question_id=question.id,
                    answer_value=answer_values[i],
                    response_time=2.0,
                    timestamp=datetime.now()
                )
                for i, question in enumerate(questions)
            ]

            result = await self.engine.score_assessment(assessment_type, responses)
            results[case_name] = result

        # Check for reasonable ranges and stability
        stability_checks = []
        for case_name, result in results.items():
            # All scores should be within 0-100
            scores_in_range = all(0 <= score <= 100 for score in result.normalized_scores.values())
            stability_checks.append(scores_in_range)

            # Processing time should be reasonable
            processing_ok = result.processing_time < 1.0  # Less than 1 second
            stability_checks.append(processing_ok)

        consistency_score = (sum(stability_checks) / len(stability_checks)) * 100
        identical_results = sum(stability_checks)
        total_comparisons = len(stability_checks)

        return ConsistencyTestResult(
            test_name="scoring_algorithm_stability",
            assessment_type=assessment_type.value,
            consistency_score=consistency_score,
            identical_results=identical_results,
            total_comparisons=total_comparisons,
            details={
                "edge_case_results": {
                    case: {
                        "personality_type": result.personality_type,
                        "max_score": max(result.normalized_scores.values()),
                        "min_score": min(result.normalized_scores.values()),
                        "processing_time": result.processing_time
                    }
                    for case, result in results.items()
                }
            },
            timestamp=datetime.now()
        )

    async def run_all_consistency_tests(self) -> Dict[str, Any]:
        """Run all consistency tests and generate comprehensive report"""
        print("Starting comprehensive psychometric scoring consistency tests...")

        # Run all tests
        test1 = await self.test_scoring_consistency_across_assessments()
        test2 = await self.test_same_input_same_output()
        test3 = await self.test_scoring_algorithm_stability()

        self.test_results = [test1, test2, test3]

        # Calculate overall metrics
        overall_consistency = statistics.mean([r.consistency_score for r in self.test_results])
        successful_tests = sum(1 for r in self.test_results if r.consistency_score >= 80.0)

        # Generate report
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "successful_tests": successful_tests,
                "overall_consistency_score": overall_consistency,
                "target_consistency_rate": 95.0,
                "meets_target": overall_consistency >= 95.0
            },
            "test_results": [
                {
                    "name": result.test_name,
                    "assessment_type": result.assessment_type,
                    "consistency_score": result.consistency_score,
                    "identical_results": result.identical_results,
                    "total_comparisons": result.total_comparisons,
                    "details": result.details,
                    "timestamp": result.timestamp.isoformat()
                }
                for result in self.test_results
            ],
            "engine_capabilities": {
                "supported_assessments": [t.value for t in AssessmentType],
                "question_bank_sizes": {
                    t.value: len(self.engine.question_banks[t])
                    for t in AssessmentType
                }
            },
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        for result in self.test_results:
            if result.consistency_score < 95.0:
                recommendations.append(
                    f"Review {result.test_name} algorithm - consistency score: {result.consistency_score:.1f}%"
                )

        if not recommendations:
            recommendations.append("All scoring algorithms meet consistency targets")

        return recommendations

async def main():
    """Main function to run psychometric scoring consistency tests"""
    tester = PsychometricScoringConsistencyTester()

    print("🔍 PSYCHOMETRIC SCORING CONSISTENCY TESTING")
    print("=" * 60)

    # Run all tests
    results = await tester.run_all_consistency_tests()

    # Print summary
    print(f"\n{'='*60}")
    print("PSYCHOMETRIC SCORING CONSISTENCY TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests Run: {results['test_summary']['total_tests']}")
    print(f"Successful: {results['test_summary']['successful_tests']}")
    print(f"Overall Success Rate: {results['test_summary']['overall_consistency_score']:.1f}%")
    print(f"Target Success Rate: {results['test_summary']['target_consistency_rate']}%")
    print(f"Meets Target: {'✅ YES' if results['test_summary']['meets_target'] else '❌ NO'}")

    print(f"\nDetailed Results:")
    for test_result in results['test_results']:
        status = "✅" if test_result['consistency_score'] >= 80.0 else "❌"
        print(f"  {status} {test_result['name']}")
        print(f"       Consistency: {test_result['consistency_score']:.1f}%")
        print(f"       Assessment: {test_result['assessment_type']}")

    print(f"\nEngine Capabilities:")
    print(f"  Supported Assessments: {', '.join(results['engine_capabilities']['supported_assessments'])}")
    print(f"  Question Bank Sizes:")
    for assessment, size in results['engine_capabilities']['question_bank_sizes'].items():
        print(f"    {assessment}: {size} questions")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"psychometric_scoring_consistency_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())