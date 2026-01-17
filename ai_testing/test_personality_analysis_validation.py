#!/usr/bin/env python3
"""
Personality Analysis Validation Framework
Validates correctness of personality analysis output against assessment data
"""

import asyncio
import json
import time
import statistics
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import random
from collections import defaultdict

class AssessmentType(Enum):
    """Different personality assessment types"""
    BIG_FIVE = "big_five"
    MBTI = "mbti"
    ENNEAGRAM = "enneagram"
    DISC = "disc"
    PREDICTIVE_INDEX = "predictive_index"
    STRENGTHSFINDER = "strengthsfinder"

class ValidationLevel(Enum):
    """Validation result levels"""
    CORRECT = "correct"
    PARTIALLY_CORRECT = "partially_correct"
    INCORRECT = "incorrect"
    INSUFFICIENT_DATA = "insufficient_data"

@dataclass
class AssessmentData:
    """Standardized assessment data structure"""
    user_id: str
    assessment_type: AssessmentType
    raw_scores: Dict[str, float]
    normalized_scores: Dict[str, float]
    responses: List[Dict[str, Any]]
    personality_type: Optional[str] = None
    confidence_score: float = 0.0

@dataclass
class PersonalityAnalysis:
    """AI-generated personality analysis"""
    analysis_id: str
    user_id: str
    assessment_type: AssessmentType
    personality_type: Optional[str]
    traits_identified: List[str]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    confidence_score: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ValidationCheck:
    """Individual validation check result"""
    check_id: str
    check_type: str  # 'type_matching', 'trait_accuracy', 'strength_relevance', etc.
    expected: Any
    actual: Any
    passed: bool
    confidence: float
    details: str

@dataclass
class ValidationResult:
    """Overall validation result for a personality analysis"""
    validation_id: str
    user_id: str
    assessment_type: AssessmentType
    analysis: PersonalityAnalysis
    assessment_data: AssessmentData
    validation_checks: List[ValidationCheck]
    overall_accuracy: float
    validation_level: ValidationLevel
    critical_issues: List[str]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class PersonalityAnalysisValidator:
    """Comprehensive validator for AI personality analysis outputs"""

    def __init__(self):
        self.validation_rules = self._initialize_validation_rules()
        self.expected_patterns = self._initialize_expected_patterns()
        self.validation_results = []

    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for different assessment types"""
        return {
            "mbti": {
                "valid_types": [
                    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"
                ],
                "type_determination_rules": {
                    "E/I": "extraversion_dimension",
                    "S/N": "intuition_dimension",
                    "T/F": "thinking_dimension",
                    "J/P": "judging_dimension"
                },
                "trait_mappings": {
                    "INTJ": ["strategic", "analytical", "independent", "innovative"],
                    "ENFJ": ["charismatic", "empathetic", "leadership", "communicative"],
                    "ISTP": ["practical", "hands_on", "problem_solver", "adaptable"],
                    "ESFP": ["enthusiastic", "social", "spontaneous", "people_oriented"],
                    "ENTP": ["innovative", "adaptable", "logical", "entrepreneurial", "creative", "versatile"]
                }
            },
            "big_five": {
                "domains": ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"],
                "score_ranges": {"min": 0, "max": 100},
                "high_threshold": 70,
                "low_threshold": 30,
                "trait_descriptions": {
                    "high_openness": ["creative", "curious", "innovative", "imaginative"],
                    "high_conscientiousness": ["organized", "disciplined", "responsible", "thorough"],
                    "high_extraversion": ["outgoing", "energetic", "sociable", "assertive"],
                    "high_agreeableness": ["cooperative", "empathetic", "trusting", "helpful"],
                    "high_neuroticism": ["anxious", "moody", "self_critical", "vulnerable"]
                }
            },
            "enneagram": {
                "valid_types": [f"Type {i}" for i in range(1, 10)],
                "type_descriptions": {
                    "Type 1": ["perfectionist", "responsible", "critical", "controlled"],
                    "Type 2": ["helper", "generous", "people_pleasing", "possessive"],
                    "Type 3": ["achiever", "competitive", "image_conscious", "workaholic"],
                    "Type 4": ["individualist", "creative", "emotional", "dramatic"],
                    "Type 5": ["investigator", "analytical", "detached", "private"],
                    "Type 6": ["loyalist", "committed", "anxious", "skeptical"],
                    "Type 7": ["enthusiast", "optimistic", "impulsive", "variety_seeking"],
                    "Type 8": ["challenger", "confident", "confrontational", "protective"],
                    "Type 9": ["peacemaker", "easy_going", "compliant", "stubborn"]
                }
            }
        }

    def _initialize_expected_patterns(self) -> Dict[str, Any]:
        """Initialize expected patterns and relationships"""
        return {
            "mbti_dimension_correlations": {
                "E": ["social", "outgoing", "energetic", "talkative"],
                "I": ["reserved", "thoughtful", "solitary", "reflective"],
                "S": ["practical", "realistic", "observant", "concrete"],
                "N": ["imaginative", "abstract", "innovative", "theoretical"],
                "T": ["logical", "objective", "analytical", "critical"],
                "F": ["empathetic", "subjective", "harmonious", "values_driven"],
                "J": ["organized", "decisive", "structured", "planned"],
                "P": ["flexible", "spontaneous", "adaptable", "open_ended"]
            },
            "strength_weakness_patterns": {
                "leadership_strengths": ["delegation", "vision", "motivation", "decision_making"],
                "analytical_strengths": ["problem_solving", "critical_thinking", "research", "analysis"],
                "creative_strengths": ["innovation", "ideation", "design", "brainstorming"],
                "social_strengths": ["communication", "empathy", "collaboration", "networking"]
            }
        }

    def generate_test_assessment_data(self) -> List[AssessmentData]:
        """Generate realistic test assessment data"""
        assessments = []

        # MBTI Assessment Data
        mbti_responses = [
            {"question_id": "q1", "dimension": "E", "value": 4},
            {"question_id": "q2", "dimension": "N", "value": 5},
            {"question_id": "q3", "dimension": "T", "value": 4},
            {"question_id": "q4", "dimension": "J", "value": 3},
            {"question_id": "q5", "dimension": "E", "value": 3},
            {"question_id": "q6", "dimension": "I", "value": 2},
            {"question_id": "q7", "dimension": "N", "value": 4},
            {"question_id": "q8", "dimension": "T", "value": 5}
        ]

        assessments.append(AssessmentData(
            user_id="mbti_user_001",
            assessment_type=AssessmentType.MBTI,
            raw_scores={"E": 7, "I": 2, "S": 1, "N": 9, "T": 9, "F": 1, "J": 3, "P": 7},
            normalized_scores={"E": 78, "N": 90, "T": 90, "P": 70},
            responses=mbti_responses,
            personality_type="ENTP",
            confidence_score=0.85
        ))

        # Big Five Assessment Data
        big_five_responses = [
            {"question_id": "bf1", "domain": "Openness", "value": 4},
            {"question_id": "bf2", "domain": "Openness", "value": 5},
            {"question_id": "bf3", "domain": "Conscientiousness", "value": 2},
            {"question_id": "bf4", "domain": "Extraversion", "value": 3},
            {"question_id": "bf5", "domain": "Agreeableness", "value": 4},
            {"question_id": "bf6", "domain": "Neuroticism", "value": 1}
        ]

        assessments.append(AssessmentData(
            user_id="bigfive_user_001",
            assessment_type=AssessmentType.BIG_FIVE,
            raw_scores={"Openness": 4.5, "Conscientiousness": 2.0, "Extraversion": 3.0,
                       "Agreeableness": 4.0, "Neuroticism": 1.5},
            normalized_scores={"Openness": 85, "Conscientiousness": 35, "Extraversion": 60,
                               "Agreeableness": 75, "Neuroticism": 25},
            responses=big_five_responses,
            confidence_score=0.78
        ))

        # Enneagram Assessment Data
        enneagram_responses = [
            {"question_id": "en1", "type": "Type 5", "value": 5},
            {"question_id": "en2", "type": "Type 5", "value": 4},
            {"question_id": "en3", "type": "Type 3", "value": 3},
            {"question_id": "en4", "type": "Type 5", "value": 4},
            {"question_id": "en5", "type": "Type 1", "value": 2}
        ]

        assessments.append(AssessmentData(
            user_id="enneagram_user_001",
            assessment_type=AssessmentType.ENNEAGRAM,
            raw_scores={"Type 1": 2, "Type 2": 1, "Type 3": 3, "Type 4": 2, "Type 5": 13},
            normalized_scores={"Type 5": 87, "Type 3": 20, "Type 1": 13},
            responses=enneagram_responses,
            personality_type="Type 5",
            confidence_score=0.82
        ))

        return assessments

    def simulate_ai_personality_analysis(self, assessment_data: AssessmentData) -> PersonalityAnalysis:
        """Simulate AI personality analysis with varying quality"""

        if assessment_data.assessment_type == AssessmentType.MBTI:
            # High quality analysis for MBTI
            if assessment_data.personality_type == "ENTP":
                analysis = PersonalityAnalysis(
                    analysis_id=f"analysis_{assessment_data.user_id}_{int(time.time())}",
                    user_id=assessment_data.user_id,
                    assessment_type=AssessmentType.MBTI,
                    personality_type="ENTP",
                    traits_identified=["innovative", "adaptable", "logical", "entrepreneurial"],
                    strengths=["creative_problem_solving", "strategic_thinking", "debate_skills", "versatility"],
                    weaknesses=["difficulty_following_through", "resistance_to_structure", "argumentative", "impatient"],
                    recommendations=[
                        "Focus on developing project completion skills",
                        "Create systems to maintain organization",
                        "Practice active listening over debating",
                        "Set realistic timelines for innovation projects"
                    ],
                    confidence_score=0.88,
                    reasoning="Strong preference for Intuition (90%) and Thinking (90%) with moderate Extraversion (78%) indicates ENTP type. High adaptability suggests Perceiving preference."
                )
            else:
                # Lower quality analysis for other types
                analysis = PersonalityAnalysis(
                    analysis_id=f"analysis_{assessment_data.user_id}_{int(time.time())}",
                    user_id=assessment_data.user_id,
                    assessment_type=AssessmentType.MBTI,
                    personality_type="INTJ",  # Incorrect type
                    traits_identified=["logical", "strategic"],  # Incomplete
                    strengths=["planning"],  # Minimal
                    weaknesses=["social_skills"],  # Generic
                    recommendations=["improve communication"],  # Single generic recommendation
                    confidence_score=0.65,  # Lower confidence
                    reasoning="Based on assessment responses"  # Vague reasoning
                )

        elif assessment_data.assessment_type == AssessmentType.BIG_FIVE:
            # Mixed quality Big Five analysis
            scores = assessment_data.normalized_scores
            rules = self.validation_rules["big_five"]
            high_threshold = rules["high_threshold"]

            # Generate proper trait names based on scores
            traits_identified = []
            for domain, score in scores.items():
                if score >= high_threshold:
                    trait_key = f"high_{domain.lower()}"
                    traits_from_rules = rules["trait_descriptions"].get(trait_key, [])
                    traits_identified.extend(traits_from_rules[:2])  # Take top 2 traits

            analysis = PersonalityAnalysis(
                analysis_id=f"analysis_{assessment_data.user_id}_{int(time.time())}",
                user_id=assessment_data.user_id,
                assessment_type=AssessmentType.BIG_FIVE,
                personality_type=None,  # Big Five doesn't use single type
                traits_identified=traits_identified,
                strengths=[
                    "creative_thinking" if scores.get("Openness", 0) > 70 else "emotional_stability"
                ],
                weaknesses=[
                    "organizational_skills" if scores.get("Conscientiousness", 0) < 40 else "social_anxiety"
                ],
                recommendations=[
                    "Leverage your creative strengths in innovative projects",
                    "Develop structured approaches to improve organization"
                ],
                confidence_score=0.75,
                reasoning=f"Analysis based on Big Five domain scores: Openness ({scores.get('Openness', 0)}), Conscientiousness ({scores.get('Conscientiousness', 0)})"
            )

        elif assessment_data.assessment_type == AssessmentType.ENNEAGRAM:
            # Accurate Enneagram analysis for Type 5
            if assessment_data.personality_type == "Type 5":
                analysis = PersonalityAnalysis(
                    analysis_id=f"analysis_{assessment_data.user_id}_{int(time.time())}",
                    user_id=assessment_data.user_id,
                    assessment_type=AssessmentType.ENNEAGRAM,
                    personality_type="Type 5 - The Investigator",
                    traits_identified=["analytical", "perceptive", "independent", "intense"],
                    strengths=["deep_thinking", "expertise_development", "problem_solving", "objectivity"],
                    weaknesses=["emotional_detachment", "social_withdrawal", "resistance_to_pressure", "resource_hoarding"],
                    recommendations=[
                        "Practice sharing knowledge with others",
                        "Develop emotional intelligence skills",
                        "Create healthy social boundaries",
                        "Balance thinking with feeling in decisions"
                    ],
                    confidence_score=0.91,
                    reasoning="Strongest scores in Type 5 (87%) with clear preference for analytical, knowledge-seeking behaviors typical of Investigator type."
                )
            else:
                # Incorrect Enneagram analysis
                analysis = PersonalityAnalysis(
                    analysis_id=f"analysis_{assessment_data.user_id}_{int(time.time())}",
                    user_id=assessment_data.user_id,
                    assessment_type=AssessmentType.ENNEAGRAM,
                    personality_type="Type 2 - The Helper",  # Wrong type
                    traits_identified=["supportive", "caring"],  # Inaccurate traits
                    strengths=["helping_others"],  # Mismatched strengths
                    weaknesses=["overextending"],  # Not based on data
                    recommendations=["set_boundaries"],  # Irrelevant
                    confidence_score=0.55,  # Low confidence for wrong analysis
                    reasoning="General personality assessment"  # No specific reasoning
                )

        else:
            # Generic analysis for other types
            analysis = PersonalityAnalysis(
                analysis_id=f"analysis_{assessment_data.user_id}_{int(time.time())}",
                user_id=assessment_data.user_id,
                assessment_type=assessment_data.assessment_type,
                personality_type="Unknown",
                traits_identified=["adaptable"],
                strengths=["flexible"],
                weaknesses=["indecisive"],
                recommendations=["be_more_decisive"],
                confidence_score=0.60,
                reasoning="Limited data available"
            )

        return analysis

    def validate_personality_type_matching(self, assessment_data: AssessmentData,
                                         analysis: PersonalityAnalysis) -> ValidationCheck:
        """Validate that AI correctly identifies personality type"""

        if assessment_data.assessment_type == AssessmentType.MBTI:
            expected_type = assessment_data.personality_type
            actual_type = analysis.personality_type

            # Check for exact match
            if expected_type and actual_type:
                passed = expected_type == actual_type
                confidence = 0.95 if passed else 0.10
                details = f"Expected: {expected_type}, Actual: {actual_type}"
            else:
                passed = False
                confidence = 0.0
                details = "Missing personality type in analysis or data"

        elif assessment_data.assessment_type == AssessmentType.ENNEAGRAM:
            expected_type = assessment_data.personality_type
            actual_type = analysis.personality_type

            if expected_type and actual_type:
                # Check for type match (allowing for descriptions like "Type 5 - The Investigator")
                passed = expected_type in actual_type or actual_type in expected_type
                confidence = 0.95 if passed else 0.15
                details = f"Expected: {expected_type}, Actual: {actual_type}"
            else:
                passed = False
                confidence = 0.0
                details = "Missing Enneagram type in analysis"

        else:
            # Big Five and others don't use single personality types
            passed = analysis.personality_type is None
            confidence = 0.90 if passed else 0.20
            details = "Should not assign single personality type for this assessment"

        return ValidationCheck(
            check_id="type_matching",
            check_type="personality_type_validation",
            expected=assessment_data.personality_type,
            actual=analysis.personality_type,
            passed=passed,
            confidence=confidence,
            details=details
        )

    def validate_trait_accuracy(self, assessment_data: AssessmentData,
                              analysis: PersonalityAnalysis) -> ValidationCheck:
        """Validate that identified traits match assessment data"""

        expected_traits = []

        # Derive expected traits from assessment data
        if assessment_data.assessment_type == AssessmentType.MBTI:
            if assessment_data.personality_type:
                type_traits = self.validation_rules["mbti"]["trait_mappings"].get(
                    assessment_data.personality_type, []
                )
                expected_traits.extend(type_traits)

        elif assessment_data.assessment_type == AssessmentType.BIG_FIVE:
            scores = assessment_data.normalized_scores
            rules = self.validation_rules["big_five"]

            # Add high-score traits
            for domain, score in scores.items():
                if score >= rules["high_threshold"]:
                    trait_key = f"high_{domain.lower()}"
                    expected_traits.extend(
                        rules["trait_descriptions"].get(trait_key, [])
                    )

        elif assessment_data.assessment_type == AssessmentType.ENNEAGRAM:
            if assessment_data.personality_type:
                type_traits = self.validation_rules["enneagram"]["type_descriptions"].get(
                    assessment_data.personality_type, []
                )
                expected_traits.extend(type_traits)

        # Check for overlap between expected and actual traits
        actual_traits = [trait.lower() for trait in analysis.traits_identified]
        expected_traits_lower = [trait.lower() for trait in expected_traits]

        # Calculate trait overlap
        if expected_traits_lower and actual_traits:
            overlap = len(set(expected_traits_lower) & set(actual_traits))
            coverage = overlap / len(expected_traits_lower)
            passed = coverage >= 0.5  # At least 50% coverage
            confidence = min(1.0, coverage + 0.3)  # Boost confidence based on coverage
        else:
            passed = False
            confidence = 0.0
            coverage = 0.0

        details = f"Expected traits: {expected_traits[:3]}, Actual traits: {analysis.traits_identified[:3]}, Coverage: {coverage:.1%}"

        return ValidationCheck(
            check_id="trait_accuracy",
            check_type="trait_validation",
            expected=expected_traits[:5],  # Top 5 expected traits
            actual=analysis.traits_identified,
            passed=passed,
            confidence=confidence,
            details=details
        )

    def validate_strength_relevance(self, assessment_data: AssessmentData,
                                  analysis: PersonalityAnalysis) -> ValidationCheck:
        """Validate that strengths are relevant to assessment results"""

        # Determine expected strengths based on assessment data
        expected_strengths = []

        if assessment_data.assessment_type == AssessmentType.BIG_FIVE:
            scores = assessment_data.normalized_scores

            # High Openness -> Creative strengths
            if scores.get("Openness", 0) >= 70:
                expected_strengths.extend(["creativity", "innovation", "problem_solving"])

            # High Conscientiousness -> Organizational strengths
            if scores.get("Conscientiousness", 0) >= 70:
                expected_strengths.extend(["organization", "planning", "reliability"])

            # High Agreeableness -> Social strengths
            if scores.get("Agreeableness", 0) >= 70:
                expected_strengths.extend(["teamwork", "collaboration", "empathy"])

        elif assessment_data.assessment_type == AssessmentType.MBTI:
            # MBTI-based strengths
            if assessment_data.personality_type:
                type_rules = self.validation_rules["mbti"]["trait_mappings"]
                traits = type_rules.get(assessment_data.personality_type, [])

                # Convert traits to strengths
                for trait in traits:
                    if trait in ["leadership", "communicative"]:
                        expected_strengths.append("communication")
                    elif trait in ["analytical", "strategic"]:
                        expected_strengths.append("problem_solving")
                    elif trait in ["innovative", "creative"]:
                        expected_strengths.append("creativity")

        # Check relevance of actual strengths
        actual_strengths = [s.lower() for s in analysis.strengths]
        expected_strengths_lower = [s.lower() for s in expected_strengths]

        if expected_strengths_lower and actual_strengths:
            # Check for semantic similarity
            relevance_count = 0
            for actual_strength in actual_strengths:
                for expected_strength in expected_strengths_lower:
                    # Simple substring check for relevance
                    if (expected_strength in actual_strength or
                        actual_strength in expected_strength or
                        self._check_concept_similarity(actual_strength, expected_strength)):
                        relevance_count += 1
                        break

            relevance_rate = relevance_count / len(actual_strengths) if actual_strengths else 0
            passed = relevance_rate >= 0.4  # At least 40% relevance
            confidence = min(1.0, relevance_rate + 0.4)
        else:
            passed = False
            confidence = 0.0
            relevance_rate = 0.0

        details = f"Expected strength categories: {expected_strengths[:3]}, Actual: {analysis.strengths[:3]}, Relevance: {relevance_rate:.1%}"

        return ValidationCheck(
            check_id="strength_relevance",
            check_type="strength_validation",
            expected=expected_strengths[:5],
            actual=analysis.strengths,
            passed=passed,
            confidence=confidence,
            details=details
        )

    def _check_concept_similarity(self, concept1: str, concept2: str) -> bool:
        """Check if two concepts are semantically similar"""
        # Simple similarity checking based on common synonyms
        similarity_groups = {
            "problem_solving": ["analytical", "analysis", "critical_thinking", "solving"],
            "communication": ["social", "interpersonal", "relational", "teamwork"],
            "creativity": ["innovative", "creative", "ideation", "innovation"],
            "leadership": ["leading", "managing", "guiding", "direction"],
            "organization": ["planning", "structured", "systematic", "methodical"]
        }

        for group, synonyms in similarity_groups.items():
            if concept1 in synonyms and concept2 in synonyms:
                return True
            if group in concept1 or group in concept2:
                return True

        return False

    def validate_recommendation_quality(self, assessment_data: AssessmentData,
                                      analysis: PersonalityAnalysis) -> ValidationCheck:
        """Validate quality and relevance of recommendations"""

        # Check for generic vs specific recommendations
        generic_recommendations = {
            "improve communication", "be more organized", "develop leadership",
            "work on teamwork", "be more confident", "manage time better"
        }

        actual_recommendations = [r.lower().strip() for r in analysis.recommendations]
        generic_count = sum(1 for rec in actual_recommendations
                           if any(gen in rec for gen in generic_recommendations))

        specific_count = len(actual_recommendations) - generic_count

        # Specificity check
        specificity_score = specific_count / len(actual_recommendations) if actual_recommendations else 0
        passed_specificity = specificity_score >= 0.5  # At least 50% specific

        # Actionability check (recommendations should be actionable)
        actionable_patterns = [
            r"\b(develop|practice|implement|create|establish|focus|learn|improve)\b",
            r"\b(skills|abilities|approach|strategy|technique|method)\b"
        ]

        actionable_count = 0
        for rec in actual_recommendations:
            if any(re.search(pattern, rec) for pattern in actionable_patterns):
                actionable_count += 1

        actionability_score = actionable_count / len(actual_recommendations) if actual_recommendations else 0
        passed_actionability = actionability_score >= 0.6  # At least 60% actionable

        # Overall quality score
        overall_quality = (specificity_score + actionability_score) / 2
        passed = overall_quality >= 0.5
        confidence = min(1.0, overall_quality + 0.3)

        details = f"Specificity: {specificity_score:.1%}, Actionability: {actionability_score:.1%}, Generic: {generic_count}/{len(actual_recommendations)}"

        return ValidationCheck(
            check_id="recommendation_quality",
            check_type="recommendation_validation",
            expected=["specific", "actionable", "personalized"],
            actual=analysis.recommendations,
            passed=passed,
            confidence=confidence,
            details=details
        )

    def validate_confidence_score_reasonableness(self, assessment_data: AssessmentData,
                                               analysis: PersonalityAnalysis) -> ValidationCheck:
        """Validate that confidence scores are reasonable given the data"""

        data_completeness = len(assessment_data.responses)
        base_confidence = assessment_data.confidence_score
        ai_confidence = analysis.confidence_score

        # Confidence should be reasonable based on data quality
        if data_completeness >= 8:  # Good data
            reasonable_range = (0.7, 1.0)
        elif data_completeness >= 5:  # Moderate data
            reasonable_range = (0.5, 0.9)
        else:  # Limited data
            reasonable_range = (0.3, 0.7)

        passed = reasonable_range[0] <= ai_confidence <= reasonable_range[1]

        # Check if AI confidence is dramatically different from base confidence
        confidence_diff = abs(ai_confidence - base_confidence)
        passed_consistency = confidence_diff <= 0.2  # Within 20%

        # Overall pass requires both conditions
        final_passed = passed and passed_consistency
        confidence = 0.8 if final_passed else 0.4

        details = f"AI confidence: {ai_confidence:.2f}, Base confidence: {base_confidence:.2f}, Reasonable range: {reasonable_range}"

        return ValidationCheck(
            check_id="confidence_reasonableness",
            check_type="confidence_validation",
            expected=reasonable_range,
            actual=ai_confidence,
            passed=final_passed,
            confidence=confidence,
            details=details
        )

    def calculate_overall_validation_accuracy(self, validation_checks: List[ValidationCheck]) -> float:
        """Calculate overall validation accuracy score"""
        if not validation_checks:
            return 0.0

        # Weight different checks differently
        weights = {
            "type_matching": 0.3,
            "trait_accuracy": 0.25,
            "strength_relevance": 0.2,
            "recommendation_quality": 0.15,
            "confidence_reasonableness": 0.1
        }

        weighted_score = 0.0
        total_weight = 0.0

        for check in validation_checks:
            weight = weights.get(check.check_type, 0.1)
            check_score = 1.0 if check.passed else 0.0

            # Adjust based on confidence
            adjusted_score = check_score * check.confidence
            weighted_score += adjusted_score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def determine_validation_level(self, accuracy_score: float) -> ValidationLevel:
        """Determine overall validation level"""
        if accuracy_score >= 0.85:
            return ValidationLevel.CORRECT
        elif accuracy_score >= 0.65:
            return ValidationLevel.PARTIALLY_CORRECT
        elif accuracy_score >= 0.40:
            return ValidationLevel.INCORRECT
        else:
            return ValidationLevel.INSUFFICIENT_DATA

    async def validate_personality_analysis(self, assessments: List[AssessmentData]) -> List[ValidationResult]:
        """Validate personality analyses against assessment data"""
        print("🧠 PERSONALITY ANALYSIS VALIDATION TESTING")
        print("=" * 60)

        results = []

        for assessment in assessments:
            print(f"\n📊 Validating: {assessment.user_id} - {assessment.assessment_type.value}")

            # Generate AI analysis
            analysis = self.simulate_ai_personality_analysis(assessment)

            # Run validation checks
            validation_checks = [
                self.validate_personality_type_matching(assessment, analysis),
                self.validate_trait_accuracy(assessment, analysis),
                self.validate_strength_relevance(assessment, analysis),
                self.validate_recommendation_quality(assessment, analysis),
                self.validate_confidence_score_reasonableness(assessment, analysis)
            ]

            # Calculate overall metrics
            overall_accuracy = self.calculate_overall_validation_accuracy(validation_checks)
            validation_level = self.determine_validation_level(overall_accuracy)

            # Identify critical issues
            critical_issues = []
            for check in validation_checks:
                if not check.passed and check.confidence > 0.8:
                    critical_issues.append(f"Critical failure in {check.check_type}: {check.details}")

            # Generate recommendations
            recommendations = []
            if overall_accuracy < 0.7:
                recommendations.append("Significant accuracy issues detected - review analysis algorithms")
            elif overall_accuracy < 0.85:
                recommendations.append("Moderate accuracy improvements needed")
            else:
                recommendations.append("Good accuracy achieved with minor optimization opportunities")

            # Specific recommendations based on failed checks
            for check in validation_checks:
                if not check.passed:
                    if check.check_type == "type_matching":
                        recommendations.append("Improve personality type determination algorithms")
                    elif check.check_type == "trait_accuracy":
                        recommendations.append("Enhance trait extraction from assessment data")
                    elif check.check_type == "strength_relevance":
                        recommendations.append("Improve strength relevance to actual assessment results")
                    elif check.check_type == "recommendation_quality":
                        recommendations.append("Generate more specific and actionable recommendations")
                    elif check.check_type == "confidence_validation":
                        recommendations.append("Calibrate confidence scoring to reflect data quality")

            # Create validation result
            result = ValidationResult(
                validation_id=f"validation_{assessment.user_id}_{int(time.time())}",
                user_id=assessment.user_id,
                assessment_type=assessment.assessment_type,
                analysis=analysis,
                assessment_data=assessment,
                validation_checks=validation_checks,
                overall_accuracy=overall_accuracy,
                validation_level=validation_level,
                critical_issues=critical_issues,
                recommendations=recommendations
            )

            results.append(result)

            # Print summary
            print(f"   ✅ Overall Accuracy: {overall_accuracy:.1%}")
            print(f"   🎯 Validation Level: {validation_level.value}")
            print(f"   ⚠️  Critical Issues: {len(critical_issues)}")
            print(f"   🔍 Checks Passed: {sum(1 for c in validation_checks if c.passed)}/{len(validation_checks)}")

        return results

    async def run_comprehensive_validation_tests(self) -> Dict[str, Any]:
        """Run comprehensive personality analysis validation tests"""
        print("🚀 Starting Personality Analysis Validation Testing Suite")

        # Generate test assessment data
        assessments = self.generate_test_assessment_data()
        print(f"Generated {len(assessments)} assessment scenarios")

        # Run validations
        results = await self.validate_personality_analysis(assessments)

        # Calculate overall metrics
        accuracy_scores = [r.overall_accuracy for r in results]
        avg_accuracy = statistics.mean(accuracy_scores)
        min_accuracy = min(accuracy_scores)
        max_accuracy = max(accuracy_scores)

        # Validation level distribution
        level_distribution = defaultdict(int)
        for result in results:
            level_distribution[result.validation_level.value] += 1

        # Check pass/fail rates by type
        check_type_results = defaultdict(lambda: {"passed": 0, "total": 0})
        for result in results:
            for check in result.validation_checks:
                check_type_results[check.check_type]["total"] += 1
                if check.passed:
                    check_type_results[check.check_type]["passed"] += 1

        # Calculate check success rates
        check_success_rates = {}
        for check_type, check_results in check_type_results.items():
            success_rate = check_results["passed"] / check_results["total"] if check_results["total"] > 0 else 0
            check_success_rates[check_type] = success_rate

        # Critical issues summary
        total_critical_issues = sum(len(r.critical_issues) for r in results)
        assessments_with_critical = len([r for r in results if r.critical_issues])

        # Generate recommendations
        recommendations = []
        if avg_accuracy >= 0.85:
            recommendations.append("✅ Excellent personality analysis accuracy - production ready")
        elif avg_accuracy >= 0.70:
            recommendations.append("⚠️ Good accuracy with targeted improvements needed")
        else:
            recommendations.append("❌ Significant accuracy issues require immediate attention")

        # Add specific recommendations based on check performance
        low_performing_checks = [check_type for check_type, rate in check_success_rates.items() if rate < 0.7]
        if low_performing_checks:
            recommendations.append(f"Priority improvements needed in: {', '.join(low_performing_checks)}")

        recommendations.extend([
            "Implement cross-validation with multiple analysis methods",
            "Enhance training data with verified personality assessments",
            "Add confidence interval reporting for all personality insights",
            "Create feedback loops from user validation of results"
        ])

        # Prepare comprehensive report
        report = {
            "test_summary": {
                "total_assessments_tested": len(assessments),
                "validation_checks_performed": sum(len(r.validation_checks) for r in results),
                "avg_validation_accuracy": avg_accuracy,
                "min_accuracy_score": min_accuracy,
                "max_accuracy_score": max_accuracy,
                "target_accuracy": 0.80,
                "critical_issues_found": total_critical_issues,
                "assessments_with_critical_issues": assessments_with_critical,
                "meets_target": avg_accuracy >= 0.80
            },
            "validation_level_distribution": dict(level_distribution),
            "check_performance_rates": check_success_rates,
            "detailed_results": [
                {
                    "validation_id": result.validation_id,
                    "user_id": result.user_id,
                    "assessment_type": result.assessment_type.value,
                    "predicted_type": result.analysis.personality_type,
                    "actual_type": result.assessment_data.personality_type,
                    "accuracy_score": result.overall_accuracy,
                    "validation_level": result.validation_level.value,
                    "checks_passed": sum(1 for c in result.validation_checks if c.passed),
                    "total_checks": len(result.validation_checks),
                    "critical_issues_count": len(result.critical_issues),
                    "confidence_score": result.analysis.confidence_score,
                    "recommendations": result.recommendations[:3]  # Top 3
                }
                for result in results
            ],
            "critical_issues_summary": {
                "total_critical_issues": total_critical_issues,
                "affected_assessments": assessments_with_critical,
                "most_common_failures": [
                    check_type for check_type, rate in check_success_rates.items()
                    if rate < 0.8
                ]
            },
            "recommendations": recommendations,
            "quality_metrics": {
                "high_accuracy_validations": len([r for r in results if r.overall_accuracy >= 0.85]),
                "low_accuracy_validations": len([r for r in results if r.overall_accuracy < 0.65]),
                "average_confidence": statistics.mean([r.analysis.confidence_score for r in results]),
                "type_matching_accuracy": check_success_rates.get("type_matching", 0)
            }
        }

        return report

async def main():
    """Main function to run personality analysis validation tests"""
    validator = PersonalityAnalysisValidator()

    # Run comprehensive tests
    results = await validator.run_comprehensive_validation_tests()

    # Print results summary
    print(f"\n{'='*60}")
    print("PERSONALITY ANALYSIS VALIDATION TEST RESULTS")
    print(f"{'='*60}")

    summary = results["test_summary"]
    print(f"📊 EXECUTION SUMMARY:")
    print(f"   Assessments Tested: {summary['total_assessments_tested']}")
    print(f"   Validation Checks: {summary['validation_checks_performed']}")
    print(f"   Avg Accuracy: {summary['avg_validation_accuracy']:.1%}")
    print(f"   Accuracy Range: {summary['min_accuracy_score']:.1%} - {summary['max_accuracy_score']:.1%}")
    print(f"   Target Accuracy: {summary['target_accuracy']:.1%}")
    print(f"   Critical Issues: {summary['critical_issues_found']}")
    print(f"   Meets Target: {'✅ YES' if summary['meets_target'] else '❌ NO'}")

    print(f"\n🎯 VALIDATION LEVEL DISTRIBUTION:")
    for level, count in results["validation_level_distribution"].items():
        print(f"   {level.replace('_', ' ').title()}: {count}")

    print(f"\n📈 CHECK PERFORMANCE RATES:")
    for check_type, rate in results["check_performance_rates"].items():
        print(f"   {check_type.replace('_', ' ').title()}: {rate:.1%}")

    print(f"\n⚠️ CRITICAL ISSUES SUMMARY:")
    critical = results["critical_issues_summary"]
    print(f"   Total Critical Issues: {critical['total_critical_issues']}")
    print(f"   Affected Assessments: {critical['affected_assessments']}")
    if critical['most_common_failures']:
        print(f"   Most Common Failures: {', '.join(critical['most_common_failures'])}")

    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"   {i}. {rec}")

    print(f"\n📊 QUALITY METRICS:")
    quality = results["quality_metrics"]
    print(f"   High Accuracy Validations: {quality['high_accuracy_validations']}")
    print(f"   Low Accuracy Validations: {quality['low_accuracy_validations']}")
    print(f"   Average Confidence: {quality['average_confidence']:.2f}")
    print(f"   Type Matching Accuracy: {quality['type_matching_accuracy']:.1%}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"personality_analysis_validation_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 DETAILED RESULTS SAVED:")
    print(f"   📊 Results File: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())
