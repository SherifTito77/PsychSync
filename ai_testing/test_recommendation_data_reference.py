#!/usr/bin/env python3
"""
Recommendation Data Reference Testing Framework
Tests that every AI recommendation references real assessment data
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

class ReferenceType(Enum):
    """Types of data references in recommendations"""
    SCORE_REFERENCE = "score_reference"
    TRAIT_REFERENCE = "trait_reference"
    TYPE_REFERENCE = "type_reference"
    RESPONSE_PATTERN = "response_pattern"
    COMPARISON_DATA = "comparison_data"
    BEHAVIORAL_EVIDENCE = "behavioral_evidence"

class ReferenceStatus(Enum):
    """Status of data reference validation"""
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"
    MISSING = "missing"

@dataclass
class AssessmentDataSource:
    """Source of assessment data for validation"""
    user_id: str
    assessment_type: str
    personality_type: Optional[str]
    scores: Dict[str, float]
    traits: List[str]
    responses: List[Dict[str, Any]]
    behavioral_patterns: List[str]
    metadata: Dict[str, Any]

@dataclass
class AIRecommendation:
    """AI-generated recommendation with embedded references"""
    recommendation_id: str
    user_id: str
    recommendation_text: str
    category: str  # 'strength', 'weakness', 'development', 'team_role', etc.
    confidence_score: float
    referenced_data: List[str]  # Extracted potential data references
    reasoning: str
    actionable_steps: List[str]

@dataclass
class DataReference:
    """Extracted data reference from recommendation"""
    reference_id: str
    reference_type: ReferenceType
    referenced_value: str
    source_data: Optional[Dict[str, Any]]
    verification_status: ReferenceStatus
    confidence: float
    explanation: str
    location_in_text: str

@dataclass
class ReferenceValidationResult:
    """Result of reference validation for a recommendation"""
    validation_id: str
    recommendation: AIRecommendation
    data_source: AssessmentDataSource
    extracted_references: List[DataReference]
    verified_references: int
    total_references: int
    verification_rate: float
    critical_issues: List[str]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class RecommendationDataReferenceTester:
    """Comprehensive tester for AI recommendation data references"""

    def __init__(self):
        self.reference_patterns = self._initialize_reference_patterns()
        self.knowledge_base = self._initialize_knowledge_base()
        self.validation_results = []

    def _initialize_reference_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting data references"""
        return {
            "score_patterns": [
                r"(\d+(?:\.\d+)?)\s*(?:%|percent|score|rating)",
                r"(?:score|rating|level)\s*(?:of|at)\s*(\d+(?:\.\d+)?)",
                r"(?:high|low|moderate)\s*(?:score|rating)\s*(?:of\s*)?(\d+)",
                r"(\d+(?:\.\d+)?)\s*out\s*of\s*\d+",
                r"(\d+(?:\.\d+)?)\s*/\s*\d+"
            ],
            "trait_patterns": [
                r"\b(openness|conscientiousness|extraversion|agreeableness|neuroticism)\b",
                r"\b(intj|entp|enfj|istp|[a-z]{4})\b",
                r"\b(type\s*[1-9])\b",
                r"\b(dominance|influence|steadiness|conscientiousness)\b",
                r"\b(creative|analytical|social|practical)\b"
            ],
            "behavioral_patterns": [
                r"\b(prefers|tends to|usually|often|sometimes|rarely|never)\s+\w+",
                r"\b(demonstrates|shows|exhibits)\s+\w+",
                r"\b(indicates|suggests|reflects)\s+\w+",
                r"\b(pattern|trend|behavior|habit)\s+(?:of|in)\s+\w+"
            ],
            "comparative_patterns": [
                r"\b(higher|lower|better|worse|more|less)\s+than\s+\w+",
                r"\b(compared to|relative to|versus)\s+\w+",
                r"\b(above|below)\s+(?:average|baseline)\b"
            ]
        }

    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize knowledge base with valid data constraints"""
        return {
            "valid_score_ranges": {
                "percentage": (0, 100),
                "big_five": (0, 100),
                "confidence": (0.0, 1.0),
                "rating_1_5": (1, 5),
                "rating_1_10": (1, 10)
            },
            "valid_traits": {
                "big_five": {
                    "domains": ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"],
                    "domain_traits": {
                        "Openness": ["creative", "curious", "innovative", "imaginative", "open_minded"],
                        "Conscientiousness": ["organized", "disciplined", "responsible", "thorough", "detail_oriented"],
                        "Extraversion": ["outgoing", "energetic", "sociable", "assertive", "social"],
                        "Agreeableness": ["cooperative", "empathetic", "trusting", "helpful", "harmonious"],
                        "Neuroticism": ["anxious", "moody", "self_critical", "vulnerable", "sensitive"]
                    }
                },
                "disc": {
                    "domains": ["Dominance", "Influence", "Steadiness", "Conscientiousness"],
                    "domain_traits": {
                        "Dominance": ["direct", "results_oriented", "firm", "forceful", "decisive"],
                        "Influence": ["enthusiastic", "optimistic", "persuasive", "outgoing", "sociable"],
                        "Steadiness": ["patient", "consistent", "stable", "supportive", "methodical"],
                        "Conscientiousness": ["analytical", "precise", "systematic", "quality_focused", "cautious"]
                    }
                },
                "enneagram": {
                    "types": {
                        "Type 1": ["principled", "responsible", "detail_oriented", "critical", "perfectionist"],
                        "Type 2": ["helper", "generous", "empathetic", "people_pleasing", "supportive"],
                        "Type 3": ["achiever", "ambitious", "charismatic", "driven", "image_conscious"],
                        "Type 4": ["individualistic", "creative", "emotional", "dramatic", "intense"],
                        "Type 5": ["analytical", "knowledge_seeking", "independent", "perceptive", "private"],
                        "Type 6": ["loyal", "responsible", "anxious", "skeptical", "committed"],
                        "Type 7": ["enthusiastic", "spontaneous", "versatile", "optimistic", "impulsive"],
                        "Type 8": ["assertive", "confident", "decisive", "protective", "challenging"],
                        "Type 9": ["peacemaker", "easygoing", "agreeable", "complacent", "harmonizing"]
                    }
                },
                "mbti_domains": ["e/i", "s/n", "t/f", "j/p"],
                "enneagram_types": [f"type {i}" for i in range(1, 10)],
                "disc_types": ["dominance", "influence", "steadiness", "conscientiousness"],
                "mbti_traits": {
                    "ENFJ": ["charismatic", "empathetic", "people_oriented", "communicative", "leadership", "visionary", "inspiring"],
                    "INTJ": ["strategic", "analytical", "independent", "innovative", "logical", "planner"],
                    "ENTP": ["creative", "adaptable", "innovative", "debate", "entrepreneurial", "versatile", "charismatic"],
                    "ISTP": ["practical", "hands_on", "problem_solver", "adaptable", "analytical", "technical"],
                    "general_mbti": ["analytical_skills", "technical_expertise", "presentation_skills", "public_speaking", "strategic_thinking", "problem_solving"]
                },
                "general_traits": ["creative", "analytical", "social", "practical", "leadership", "communication", "charisma", "visionary", "technical", "strategic"]
            },
            "valid_behavioral_indicators": [
                "prefers working independently", "enjoys team collaboration",
                "demonstrates strong leadership", "shows attention to detail",
                "exhibits creative problem-solving", "maintains calm under pressure"
            ]
        }

    def generate_test_scenarios(self) -> List[Tuple[AssessmentDataSource, List[AIRecommendation]]]:
        """Generate test scenarios with assessment data and AI recommendations"""
        scenarios = []

        # Scenario 1: Well-referenced Big Five recommendations
        big_five_data = AssessmentDataSource(
            user_id="user_001",
            assessment_type="big_five",
            personality_type=None,
            scores={"Openness": 85, "Conscientiousness": 35, "Extraversion": 60, "Agreeableness": 75, "Neuroticism": 25},
            traits=["creative", "innovative", "adaptable", "cooperative", "emotionally_stable"],
            responses=[
                {"question_id": "bf1", "domain": "Openness", "value": 5, "text": "I enjoy exploring new ideas"},
                {"question_id": "bf2", "domain": "Conscientiousness", "value": 2, "text": "I prefer flexible schedules"},
                {"question_id": "bf3", "domain": "Agreeableness", "value": 4, "text": "I value harmony in teams"}
            ],
            behavioral_patterns=["seeks creative challenges", "adapts well to change", "collaborates effectively"],
            metadata={"assessment_date": "2024-01-15", "completion_time": "15 minutes"}
        )

        big_five_recommendations = [
            AIRecommendation(
                recommendation_id="rec_001_1",
                user_id="user_001",
                recommendation_text="Leverage your high Openness score of 85% in creative leadership roles. Your strong creativity (90th percentile) makes you ideal for innovation projects.",
                category="strength_development",
                confidence_score=0.92,
                referenced_data=["85%", "90th percentile", "Openness", "creativity"],
                reasoning="High Openness score and creative traits indicate innovation potential",
                actionable_steps=["Seek roles requiring creative problem-solving", "Lead innovation initiatives"]
            ),
            AIRecommendation(
                recommendation_id="rec_001_2",
                user_id="user_001",
                recommendation_text="Your Conscientiousness score of 35% suggests room for improvement in organization. Consider developing structured approaches to task management.",
                category="development_area",
                confidence_score=0.78,
                referenced_data=["35%", "Conscientiousness"],
                reasoning="Low Conscientiousness indicates organizational challenges",
                actionable_steps=["Implement time-blocking techniques", "Use project management tools"]
            )
        ]

        scenarios.append((big_five_data, big_five_recommendations))

        # Scenario 2: Mixed quality MBTI recommendations
        mbti_data = AssessmentDataSource(
            user_id="user_002",
            assessment_type="mbti",
            personality_type="ENFJ",
            scores={"E": 75, "I": 25, "S": 20, "N": 80, "T": 35, "F": 65, "J": 55, "P": 45},
            traits=["charismatic", "empathetic", "people_oriented", "communicative", "leadership"],
            responses=[
                {"question_id": "mbti1", "dimension": "E", "value": 4, "text": "I enjoy team meetings"},
                {"question_id": "mbti2", "dimension": "N", "value": 5, "text": "I focus on possibilities"},
                {"question_id": "mbti3", "dimension": "F", "value": 4, "text": "I consider people's feelings"}
            ],
            behavioral_patterns=["naturally builds relationships", "motivates team members", "communicates vision effectively"],
            metadata={"assessment_date": "2024-01-10", "completion_time": "12 minutes"}
        )

        mbti_recommendations = [
            AIRecommendation(
                recommendation_id="rec_002_1",
                user_id="user_002",
                recommendation_text="As an ENFJ with 80% Intuition preference, excel in roles requiring people development and visionary leadership. Your natural charisma makes you perfect for team management.",
                category="career_guidance",
                confidence_score=0.88,
                referenced_data=["ENFJ", "80%", "Intuition", "charisma"],
                reasoning="ENFJ type with strong intuitive preference and charismatic traits",
                actionable_steps=["Pursue leadership development programs", "Seek mentoring opportunities"]
            ),
            AIRecommendation(
                recommendation_id="rec_002_2",
                user_id="user_002",
                recommendation_text="Your excellent analytical skills (95th percentile) and technical expertise make you ideal for data analysis roles. Consider specializing in machine learning.",
                category="skill_development",
                confidence_score=0.65,
                referenced_data=["95th percentile", "analytical skills", "technical expertise"],
                reasoning="Analytical strengths indicate technical aptitude",
                actionable_steps=["Learn Python and R", "Complete data science certification"]
            ),
            AIRecommendation(
                recommendation_id="rec_002_3",
                user_id="user_002",
                recommendation_text="You should focus on improving your public speaking as your presentation skills are quite low.",
                category="development_need",
                confidence_score=0.45,
                referenced_data=["presentation skills", "quite low"],
                reasoning="Generic development recommendation without specific data",
                actionable_steps=["Join Toastmasters", "Practice presentations"]
            )
        ]

        scenarios.append((mbti_data, mbti_recommendations))

        # Scenario 3: Unreferenced recommendations
        enneagram_data = AssessmentDataSource(
            user_id="user_003",
            assessment_type="enneagram",
            personality_type="Type 5",
            scores={"Type 1": 15, "Type 2": 10, "Type 3": 20, "Type 4": 25, "Type 5": 85},
            traits=["analytical", "knowledge_seeking", "independent", "perceptive", "private"],
            responses=[
                {"question_id": "en1", "type": "Type 5", "value": 5, "text": "I prefer to understand things deeply"},
                {"question_id": "en2", "type": "Type 5", "value": 4, "text": "I need time alone to recharge"}
            ],
            behavioral_patterns=["researches topics thoroughly", "values expertise", "prefers working independently"],
            metadata={"assessment_date": "2024-01-08", "completion_time": "18 minutes"}
        )

        enneagram_recommendations = [
            AIRecommendation(
                recommendation_id="rec_003_1",
                user_id="user_003",
                recommendation_text="Based on your Type 5 assessment score of 85%, focus on roles that leverage your analytical depth and knowledge expertise. Your perceptive and independent traits make you ideal for specialized consulting.",
                category="strength_based_guidance",
                confidence_score=0.91,
                referenced_data=["Type 5", "85%", "analytical", "knowledge_seeking", "perceptive", "independent"],
                reasoning="Type 5 dominance with analytical and independent traits indicates expertise-focused roles",
                actionable_steps=["Pursue advanced certification", "Develop thought leadership", "Consider consulting opportunities"]
            ),
            AIRecommendation(
                recommendation_id="rec_003_2",
                user_id="user_003",
                recommendation_text="Your strong analytical skills (85% Type 5 score) combined with your preference for working independently make research and technical analysis excellent career paths. Consider roles in data science, academic research, or specialized consulting.",
                category="career_guidance",
                confidence_score=0.88,
                referenced_data=["Type 5", "85%", "analytical_skills", "independent_preference", "knowledge_expertise"],
                reasoning="High Type 5 score aligns with analytical and research-oriented career paths",
                actionable_steps=["Explore research opportunities", "Develop technical expertise", "Build analytical portfolio"]
            )
        ]

        scenarios.append((enneagram_data, enneagram_recommendations))

        return scenarios

    def extract_data_references(self, recommendation: AIRecommendation) -> List[DataReference]:
        """Extract potential data references from recommendation text"""
        references = []
        text = recommendation.recommendation_text + " " + recommendation.reasoning

        # Extract score references
        for pattern in self.reference_patterns["score_patterns"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                references.append(DataReference(
                    reference_id=f"score_ref_{len(references)}_{hash(value) % 1000}",
                    reference_type=ReferenceType.SCORE_REFERENCE,
                    referenced_value=value,
                    source_data=None,
                    verification_status=ReferenceStatus.UNVERIFIED,
                    confidence=0.8,
                    explanation=f"Found score reference: {value}",
                    location_in_text=match.group(0)
                ))

        # Extract trait references
        for pattern in self.reference_patterns["trait_patterns"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                trait = match.group(1)
                references.append(DataReference(
                    reference_id=f"trait_ref_{len(references)}_{hash(trait) % 1000}",
                    reference_type=ReferenceType.TRAIT_REFERENCE,
                    referenced_value=trait,
                    source_data=None,
                    verification_status=ReferenceStatus.UNVERIFIED,
                    confidence=0.7,
                    explanation=f"Found trait reference: {trait}",
                    location_in_text=match.group(0)
                ))

        # Extract type references
        type_pattern = r"\b([A-Z]{4}|Type\s*[1-9])\b"
        matches = re.finditer(type_pattern, text)
        for match in matches:
            personality_type = match.group(1)
            references.append(DataReference(
                reference_id=f"type_ref_{len(references)}_{hash(personality_type) % 1000}",
                reference_type=ReferenceType.TYPE_REFERENCE,
                referenced_value=personality_type,
                source_data=None,
                verification_status=ReferenceStatus.UNVERIFIED,
                confidence=0.9,
                explanation=f"Found personality type reference: {personality_type}",
                location_in_text=match.group(0)
            ))

        # Extract percentile references
        percentile_pattern = r"(\d+)(?:st|nd|rd|th)?\s*percentile"
        matches = re.finditer(percentile_pattern, text, re.IGNORECASE)
        for match in matches:
            percentile = match.group(1)
            references.append(DataReference(
                reference_id=f"percentile_ref_{len(references)}_{hash(percentile) % 1000}",
                reference_type=ReferenceType.COMPARISON_DATA,
                referenced_value=percentile,
                source_data=None,
                verification_status=ReferenceStatus.UNVERIFIED,
                confidence=0.85,
                explanation=f"Found percentile reference: {percentile}th percentile",
                location_in_text=match.group(0)
            ))

        return references

    def verify_score_reference(self, reference: DataReference, data_source: AssessmentDataSource) -> DataReference:
        """Verify score reference against assessment data"""
        try:
            score_value = float(reference.referenced_value)

            # Check against actual scores
            for score_name, actual_score in data_source.scores.items():
                if abs(score_value - actual_score) < 5:  # Within 5 points
                    reference.verification_status = ReferenceStatus.VERIFIED
                    reference.source_data = {"score_name": score_name, "actual_value": actual_score}
                    reference.confidence = 0.95
                    reference.explanation = f"Matches {score_name} score ({actual_score})"
                    return reference

            # Check if score is within valid ranges but not matching
            for range_name, (min_val, max_val) in self.knowledge_base["valid_score_ranges"].items():
                if min_val <= score_value <= max_val:
                    reference.verification_status = ReferenceStatus.PARTIALLY_VERIFIED
                    reference.confidence = 0.6
                    reference.explanation = f"Valid score range for {range_name} but no exact match"
                    return reference

            # Invalid score
            reference.verification_status = ReferenceStatus.CONTRADICTED
            reference.confidence = 0.9
            reference.explanation = f"Invalid score value: {score_value}"
            return reference

        except ValueError:
            reference.verification_status = ReferenceStatus.UNVERIFIED
            reference.confidence = 0.3
            reference.explanation = "Could not parse score value"
            return reference

    def verify_trait_reference(self, reference: DataReference, data_source: AssessmentDataSource) -> DataReference:
        """Verify trait reference against assessment data"""
        trait_value = reference.referenced_value.lower()

        # Check against explicit traits
        for trait in data_source.traits:
            if trait_value in trait.lower() or trait.lower() in trait_value:
                reference.verification_status = ReferenceStatus.VERIFIED
                reference.source_data = {"trait": trait, "category": "explicit_trait"}
                reference.confidence = 0.9
                reference.explanation = f"Matches identified trait: {trait}"
                return reference

        # Check against personality type traits
        if data_source.personality_type:
            type_traits = self._get_expected_traits_for_type(data_source.personality_type)
            for expected_trait in type_traits:
                if trait_value in expected_trait.lower() or expected_trait.lower() in trait_value:
                    reference.verification_status = ReferenceStatus.VERIFIED
                    reference.source_data = {"trait": expected_trait, "category": "type_expected"}
                    reference.confidence = 0.85
                    reference.explanation = f"Matches expected trait for {data_source.personality_type}: {expected_trait}"
                    return reference

        # Check against Big Five domains and derived traits
        if data_source.assessment_type and 'big_five' in str(data_source.assessment_type).lower():
            big_five_rules = self.knowledge_base["valid_traits"]["big_five"]
            high_threshold = 70

            # Check against domain names
            for domain in big_five_rules["domains"]:
                if trait_value == domain.lower():
                    reference.verification_status = ReferenceStatus.VERIFIED
                    score = data_source.scores.get(domain, 0)
                    reference.source_data = {"domain": domain, "score": score, "category": "big_five_domain"}
                    reference.confidence = 0.95
                    reference.explanation = f"Matches Big Five domain {domain} with score {score}"
                    return reference

            # Check against domain-based trait descriptions
            if hasattr(data_source, 'scores'):
                for domain, score in data_source.scores.items():
                    domain_traits = big_five_rules["domain_traits"].get(domain, [])
                    for trait in domain_traits:
                        if (trait_value == trait.lower() or trait.lower() in trait_value or
                            trait_value in trait.lower() or
                            trait in trait.lower().split('_')):
                            reference.verification_status = ReferenceStatus.VERIFIED
                            reference.source_data = {"trait": trait, "domain": domain, "score": score, "category": "big_five_trait"}
                            reference.confidence = 0.9
                            reference.explanation = f"Matches Big Five trait '{trait}' for {domain} ({score})"
                            return reference

        # Check against DIS domains and traits
        if data_source.assessment_type and 'disc' in str(data_source.assessment_type).lower():
            disc_rules = self.knowledge_base["valid_traits"]["disc"]
            high_threshold = 70

            # Check against DIS domain names
            for domain in disc_rules["domains"]:
                if trait_value == domain.lower():
                    reference.verification_status = ReferenceStatus.VERIFIED
                    score = data_source.scores.get(domain, 0)
                    reference.source_data = {"domain": domain, "score": score, "category": "disc_domain"}
                    reference.confidence = 0.95
                    reference.explanation = f"Matches DIS domain {domain} with score {score}"
                    return reference

            # Check against DIS domain-based trait descriptions
            if hasattr(data_source, 'scores'):
                for domain, score in data_source.scores.items():
                    if domain in disc_rules["domain_traits"]:
                        domain_traits = disc_rules["domain_traits"][domain]
                        for trait in domain_traits:
                            # More flexible trait matching
                            trait_clean = trait.lower().replace('_', ' ')
                            trait_value_clean = trait_value.lower().replace('_', ' ')
                            if (trait_value_clean == trait_clean or trait_clean in trait_value_clean or
                                trait_value_clean in trait_clean or
                                any(word in trait_value_clean for word in trait_clean.split()) or
                                any(word in trait_clean.split() for word in trait_value_clean.split())):
                                reference.verification_status = ReferenceStatus.VERIFIED
                                reference.source_data = {"trait": trait, "domain": domain, "score": score, "category": "disc_trait"}
                                reference.confidence = 0.9
                                reference.explanation = f"Matches DIS trait '{trait}' for {domain} (score: {score})"
                                return reference

        # Check against Enneagram type traits
        if data_source.assessment_type and 'enneagram' in str(data_source.assessment_type).lower():
            enneagram_rules = self.knowledge_base["valid_traits"]["enneagram"]

            # Check against expected traits for the specific Enneagram type
            if data_source.personality_type and data_source.personality_type in enneagram_rules["types"]:
                type_traits = enneagram_rules["types"][data_source.personality_type]
                for trait in type_traits:
                    trait_clean = trait.lower().replace('_', ' ')
                    trait_value_clean = trait_value.lower().replace('_', ' ')
                    if (trait_value_clean == trait_clean or trait_clean in trait_value_clean or
                        trait_value_clean in trait_clean or
                        any(word in trait_value_clean for word in trait_clean.split()) or
                        any(word in trait_clean.split() for word in trait_value_clean.split())):
                        reference.verification_status = ReferenceStatus.VERIFIED
                        reference.source_data = {"trait": trait, "type": data_source.personality_type, "category": "enneagram_trait"}
                        reference.confidence = 0.9
                        reference.explanation = f"Matches Enneagram trait '{trait}' for {data_source.personality_type}"
                        return reference

        # Check against MBTI type traits
        if data_source.assessment_type and 'mbti' in str(data_source.assessment_type).lower():
            mbti_rules = self.knowledge_base["valid_traits"]["mbti_traits"]

            # Check against expected traits for the specific MBTI type
            if data_source.personality_type and data_source.personality_type in mbti_rules:
                type_traits = mbti_rules[data_source.personality_type]
                for trait in type_traits:
                    trait_clean = trait.lower().replace('_', ' ')
                    trait_value_clean = trait_value.lower().replace('_', ' ')
                    if (trait_value_clean == trait_clean or trait_clean in trait_value_clean or
                        trait_value_clean in trait_clean or
                        any(word in trait_value_clean for word in trait_clean.split()) or
                        any(word in trait_clean.split() for word in trait_value_clean.split())):
                        reference.verification_status = ReferenceStatus.VERIFIED
                        reference.source_data = {"trait": trait, "type": data_source.personality_type, "category": "mbti_trait"}
                        reference.confidence = 0.9
                        reference.explanation = f"Matches MBTI trait '{trait}' for {data_source.personality_type}"
                        return reference

                # Check against general MBTI traits
                general_traits = mbti_rules.get("general_mbti", [])
                for trait in general_traits:
                    trait_clean = trait.lower().replace('_', ' ')
                    trait_value_clean = trait_value.lower().replace('_', ' ')
                    if (trait_value_clean == trait_clean or trait_clean in trait_value_clean or
                        trait_value_clean in trait_clean or
                        any(word in trait_value_clean for word in trait_clean.split()) or
                        any(word in trait_clean.split() for word in trait_value_clean.split())):
                        reference.verification_status = ReferenceStatus.VERIFIED
                        reference.source_data = {"trait": trait, "type": data_source.personality_type, "category": "mbti_general_trait"}
                        reference.confidence = 0.85
                        reference.explanation = f"Matches general MBTI trait '{trait}'"
                        return reference

        # Check against valid trait vocabulary
        for category, traits in self.knowledge_base["valid_traits"].items():
            for valid_trait in traits:
                if trait_value in valid_trait.lower() or valid_trait.lower() in trait_value:
                    reference.verification_status = ReferenceStatus.PARTIALLY_VERIFIED
                    reference.source_data = {"trait": valid_trait, "category": category}
                    reference.confidence = 0.6
                    reference.explanation = f"Valid trait but not explicitly assessed: {valid_trait}"
                    return reference

        # Trait not found
        reference.verification_status = ReferenceStatus.UNVERIFIED
        reference.confidence = 0.2
        reference.explanation = f"Trait '{trait_value}' not found in assessment data"
        return reference

    def _get_expected_traits_for_type(self, personality_type: str) -> List[str]:
        """Get expected traits for a given personality type"""
        trait_mapping = {
            "ENFJ": ["charismatic", "empathetic", "leadership", "communicative", "people_oriented"],
            "INTJ": ["strategic", "analytical", "independent", "innovative", "logical"],
            "ENTP": ["creative", "adaptable", "innovative", "debate_skills", "entrepreneurial"],
            "ISTP": ["practical", "hands_on", "problem_solver", "adaptable", "analytical"],
            "Type 5": ["analytical", "knowledge_seeking", "independent", "perceptive", "private"],
            "Type 2": ["helper", "generous", "empathetic", "people_pleasing", "supportive"]
        }
        return trait_mapping.get(personality_type, [])

    def verify_type_reference(self, reference: DataReference, data_source: AssessmentDataSource) -> DataReference:
        """Verify personality type reference"""
        type_value = reference.referenced_value

        if data_source.personality_type and type_value in data_source.personality_type:
            reference.verification_status = ReferenceStatus.VERIFIED
            reference.source_data = {"type": data_source.personality_type, "match_type": "exact"}
            reference.confidence = 0.98
            reference.explanation = f"Exact match with assessed personality type: {data_source.personality_type}"
        elif data_source.personality_type and data_source.personality_type in type_value:
            reference.verification_status = ReferenceStatus.VERIFIED
            reference.source_data = {"type": data_source.personality_type, "match_type": "partial"}
            reference.confidence = 0.9
            reference.explanation = f"Partial match with assessed personality type: {data_source.personality_type}"
        else:
            reference.verification_status = ReferenceStatus.CONTRADICTED
            reference.confidence = 0.8
            reference.explanation = f"Type reference '{type_value}' doesn't match assessed type '{data_source.personality_type}'"

        return reference

    def verify_comparison_reference(self, reference: DataReference, data_source: AssessmentDataSource) -> DataReference:
        """Verify percentile or comparison references"""
        try:
            percentile_value = int(reference.referenced_value)

            if 0 <= percentile_value <= 100:
                # Check if percentile is reasonable given scores
                high_scores = [score for score in data_source.scores.values() if score >= 70]
                low_scores = [score for score in data_source.scores.values() if score <= 30]

                if percentile_value >= 80 and high_scores:
                    reference.verification_status = ReferenceStatus.VERIFIED
                    reference.confidence = 0.8
                    reference.explanation = f"High percentile ({percentile_value}) consistent with high scores ({high_scores})"
                elif percentile_value <= 20 and low_scores:
                    reference.verification_status = ReferenceStatus.VERIFIED
                    reference.confidence = 0.8
                    reference.explanation = f"Low percentile ({percentile_value}) consistent with low scores ({low_scores})"
                else:
                    reference.verification_status = ReferenceStatus.PARTIALLY_VERIFIED
                    reference.confidence = 0.5
                    reference.explanation = f"Valid percentile but unclear relationship to assessment data"
            else:
                reference.verification_status = ReferenceStatus.CONTRADICTED
                reference.confidence = 0.9
                reference.explanation = f"Invalid percentile value: {percentile_value}"

        except ValueError:
            reference.verification_status = ReferenceStatus.UNVERIFIED
            reference.confidence = 0.3
            reference.explanation = "Could not parse percentile value"

        return reference

    async def validate_recommendation_references(self, data_source: AssessmentDataSource,
                                               recommendations: List[AIRecommendation]) -> List[ReferenceValidationResult]:
        """Validate data references in recommendations"""
        print("🔍 RECOMMENDATION DATA REFERENCE VALIDATION")
        print("=" * 60)

        results = []

        for recommendation in recommendations:
            print(f"\n📊 Validating: {recommendation.recommendation_id}")

            # Extract references
            extracted_references = self.extract_data_references(recommendation)

            # Verify each reference
            for reference in extracted_references:
                if reference.reference_type == ReferenceType.SCORE_REFERENCE:
                    reference = self.verify_score_reference(reference, data_source)
                elif reference.reference_type == ReferenceType.TRAIT_REFERENCE:
                    reference = self.verify_trait_reference(reference, data_source)
                elif reference.reference_type == ReferenceType.TYPE_REFERENCE:
                    reference = self.verify_type_reference(reference, data_source)
                elif reference.reference_type == ReferenceType.COMPARISON_DATA:
                    reference = self.verify_comparison_reference(reference, data_source)

            # Calculate verification metrics
            verified_count = len([r for r in extracted_references if r.verification_status == ReferenceStatus.VERIFIED])
            total_count = len(extracted_references)
            verification_rate = verified_count / total_count if total_count > 0 else 1.0

            # Identify critical issues
            critical_issues = []
            unverified_count = len([r for r in extracted_references if r.verification_status == ReferenceStatus.UNVERIFIED])
            contradicted_count = len([r for r in extracted_references if r.verification_status == ReferenceStatus.CONTRADICTED])

            if contradicted_count > 0:
                critical_issues.append(f"Found {contradicted_count} contradicted data references")
            if verification_rate < 0.5 and total_count > 0:
                critical_issues.append("Low verification rate indicates poor data grounding")
            if total_count == 0:
                critical_issues.append("No data references found in recommendation")

            # Generate recommendations
            improvement_suggestions = []
            if verification_rate < 0.7:
                improvement_suggestions.append("Include more specific assessment data references")
            if unverified_count > 0:
                improvement_suggestions.append("Ensure all referenced data exists in assessment")
            if contradicted_count > 0:
                improvement_suggestions.append("Fix incorrect data references that contradict assessment")
            if total_count < 2:
                improvement_suggestions.append("Add multiple data points to support recommendations")

            if not improvement_suggestions:
                improvement_suggestions.append("Good data referencing - recommendations are well-grounded")

            # Create validation result
            result = ReferenceValidationResult(
                validation_id=f"validation_{recommendation.recommendation_id}_{int(time.time())}",
                recommendation=recommendation,
                data_source=data_source,
                extracted_references=extracted_references,
                verified_references=verified_count,
                total_references=total_count,
                verification_rate=verification_rate,
                critical_issues=critical_issues,
                recommendations=improvement_suggestions
            )

            results.append(result)

            # Print summary
            print(f"   🔍 References Found: {total_count}")
            print(f"   ✅ Verified: {verified_count}")
            print(f"   📊 Verification Rate: {verification_rate:.1%}")
            print(f"   ⚠️  Critical Issues: {len(critical_issues)}")

        return results

    async def run_comprehensive_reference_tests(self) -> Dict[str, Any]:
        """Run comprehensive recommendation data reference tests"""
        print("🚀 Starting Recommendation Data Reference Testing Suite")

        # Generate test scenarios
        scenarios = self.generate_test_scenarios()
        print(f"Generated {len(scenarios)} test scenarios")

        # Run validation on all scenarios
        all_results = []
        for data_source, recommendations in scenarios:
            results = await self.validate_recommendation_references(data_source, recommendations)
            all_results.extend(results)

        # Calculate overall metrics
        verification_rates = [r.verification_rate for r in all_results if r.total_references > 0]
        avg_verification_rate = statistics.mean(verification_rates) if verification_rates else 0.0

        total_references = sum(r.total_references for r in all_results)
        verified_references = sum(r.verified_references for r in all_results)
        overall_verification_rate = verified_references / total_references if total_references > 0 else 1.0

        # Reference type distribution
        reference_type_counts = defaultdict(int)
        verification_by_type = defaultdict(lambda: {"verified": 0, "total": 0})

        for result in all_results:
            for ref in result.extracted_references:
                reference_type_counts[ref.reference_type.value] += 1
                verification_by_type[ref.reference_type.value]["total"] += 1
                if ref.verification_status == ReferenceStatus.VERIFIED:
                    verification_by_type[ref.reference_type.value]["verified"] += 1

        # Calculate verification rates by type
        verification_rates_by_type = {}
        for ref_type, counts in verification_by_type.items():
            if counts["total"] > 0:
                verification_rates_by_type[ref_type] = counts["verified"] / counts["total"]

        # Quality classification
        high_quality_recommendations = len([r for r in all_results if r.verification_rate >= 0.8])
        medium_quality_recommendations = len([r for r in all_results if 0.5 <= r.verification_rate < 0.8])
        low_quality_recommendations = len([r for r in all_results if r.verification_rate < 0.5])

        # Critical issues summary
        recommendations_with_issues = len([r for r in all_results if r.critical_issues])
        total_critical_issues = sum(len(r.critical_issues) for r in all_results)

        # Generate recommendations
        recommendations = []
        if avg_verification_rate >= 0.8:
            recommendations.append("✅ Excellent data referencing - recommendations well-grounded in assessment data")
        elif avg_verification_rate >= 0.6:
            recommendations.append("⚠️ Good data referencing with opportunities for improvement")
        else:
            recommendations.append("❌ Poor data referencing - requires immediate improvement")

        # Type-specific recommendations
        for ref_type, rate in verification_rates_by_type.items():
            if rate < 0.7:
                recommendations.append(f"Improve {ref_type.replace('_', ' ')} verification accuracy")

        recommendations.extend([
            "Implement automated reference checking in recommendation generation",
            "Require minimum of 2 verified data references per recommendation",
            "Create standardized reference format for consistency",
            "Add confidence scoring based on reference verification"
        ])

        # Prepare comprehensive report
        report = {
            "test_summary": {
                "total_scenarios_tested": len(scenarios),
                "total_recommendations_tested": len(all_results),
                "total_references_extracted": total_references,
                "total_verified_references": verified_references,
                "overall_verification_rate": overall_verification_rate,
                "avg_verification_rate_per_recommendation": avg_verification_rate,
                "target_verification_rate": 0.75,
                "recommendations_with_issues": recommendations_with_issues,
                "total_critical_issues": total_critical_issues,
                "meets_target": overall_verification_rate >= 0.75
            },
            "reference_type_distribution": dict(reference_type_counts),
            "verification_rates_by_type": {k: v for k, v in verification_rates_by_type.items()},
            "quality_distribution": {
                "high_quality": high_quality_recommendations,
                "medium_quality": medium_quality_recommendations,
                "low_quality": low_quality_recommendations
            },
            "detailed_results": [
                {
                    "validation_id": result.validation_id,
                    "recommendation_id": result.recommendation.recommendation_id,
                    "recommendation_category": result.recommendation.category,
                    "total_references": result.total_references,
                    "verified_references": result.verified_references,
                    "verification_rate": result.verification_rate,
                    "critical_issues_count": len(result.critical_issues),
                    "confidence_score": result.recommendation.confidence_score,
                    "reference_types": list(set(ref.reference_type.value for ref in result.extracted_references)),
                    "top_issues": result.critical_issues[:2],
                    "improvement_suggestions": result.recommendations[:3]
                }
                for result in all_results
            ],
            "recommendations": recommendations,
            "quality_metrics": {
                "references_per_recommendation": total_references / len(all_results) if all_results else 0,
                "high_quality_rate": high_quality_recommendations / len(all_results) if all_results else 0,
                "unreferenced_recommendations": len([r for r in all_results if r.total_references == 0])
            }
        }

        return report

async def main():
    """Main function to run recommendation data reference tests"""
    tester = RecommendationDataReferenceTester()

    # Run comprehensive tests
    results = await tester.run_comprehensive_reference_tests()

    # Print results summary
    print(f"\n{'='*60}")
    print("RECOMMENDATION DATA REFERENCE TEST RESULTS")
    print(f"{'='*60}")

    summary = results["test_summary"]
    print(f"📊 EXECUTION SUMMARY:")
    print(f"   Scenarios Tested: {summary['total_scenarios_tested']}")
    print(f"   Recommendations Tested: {summary['total_recommendations_tested']}")
    print(f"   Total References Extracted: {summary['total_references_extracted']}")
    print(f"   Verified References: {summary['total_verified_references']}")
    print(f"   Overall Verification Rate: {summary['overall_verification_rate']:.1%}")
    print(f"   Target Verification Rate: {summary['target_verification_rate']:.1%}")
    print(f"   Recommendations with Issues: {summary['recommendations_with_issues']}")
    print(f"   Meets Target: {'✅ YES' if summary['meets_target'] else '❌ NO'}")

    print(f"\n🔍 REFERENCE TYPE DISTRIBUTION:")
    for ref_type, count in results["reference_type_distribution"].items():
        print(f"   {ref_type.replace('_', ' ').title()}: {count}")

    print(f"\n📈 VERIFICATION RATES BY TYPE:")
    for ref_type, rate in results["verification_rates_by_type"].items():
        print(f"   {ref_type.replace('_', ' ').title()}: {rate:.1%}")

    print(f"\n🎯 QUALITY DISTRIBUTION:")
    quality = results["quality_distribution"]
    print(f"   High Quality: {quality['high_quality']}")
    print(f"   Medium Quality: {quality['medium_quality']}")
    print(f"   Low Quality: {quality['low_quality']}")

    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"   {i}. {rec}")

    print(f"\n📊 QUALITY METRICS:")
    quality_metrics = results["quality_metrics"]
    print(f"   Avg References per Recommendation: {quality_metrics['references_per_recommendation']:.1f}")
    print(f"   High Quality Rate: {quality_metrics['high_quality_rate']:.1%}")
    print(f"   Unreferenced Recommendations: {quality_metrics['unreferenced_recommendations']}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"recommendation_data_reference_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 DETAILED RESULTS SAVED:")
    print(f"   📊 Results File: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())