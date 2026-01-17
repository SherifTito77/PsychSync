#!/usr/bin/env python3
"""
AI Hallucination Detection Framework
Detects hallucination in AI-generated team recommendations and analyses
"""

import asyncio
import json
import time
import re
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import random
from collections import defaultdict, Counter

class HallucinationType(Enum):
    """Types of AI hallucinations to detect"""
    FACTUAL_INCORRECTNESS = "factual_incorrectness"
    IMPOSSIBLE_METRICS = "impossible_metrics"
    CONTRADICTORY_STATEMENTS = "contradictory_statements"
    INVENTED_DATA = "invented_data"
    INVALID_REFERENCES = "invalid_references"
    LOGICAL_INCONSISTENCIES = "logical_inconsistencies"
    IMPOSSIBLE_CORRELATIONS = "impossible_correlations"

class SeverityLevel(Enum):
    """Severity levels for detected hallucinations"""
    CRITICAL = "critical"  # Completely fabricated information
    HIGH = "high"          # Major factual errors
    MEDIUM = "medium"      # Minor inaccuracies
    LOW = "low"           # Minor inconsistencies

@dataclass
class FactReference:
    """Reference to a verifiable fact"""
    fact_id: str
    source_type: str  # 'assessment_data', 'user_profile', 'team_metrics'
    source_data: Dict[str, Any]
    verification_status: str
    confidence: float

@dataclass
class HallucinationDetection:
    """Detected hallucination instance"""
    detection_id: str
    hallucination_type: HallucinationType
    severity: SeverityLevel
    description: str
    evidence: str
    confidence_score: float
    location_in_text: str
    expected_correct_value: Optional[str] = None

@dataclass
class HallucinationTestResult:
    """Result of hallucination detection test"""
    test_id: str
    input_data: Dict[str, Any]
    ai_output: str
    hallucinations_detected: List[HallucinationDetection]
    hallucination_count: int
    severity_distribution: Dict[str, int]
    overall_hallucination_score: float
    factual_accuracy_score: float
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class AIHallucinationDetector:
    """Comprehensive hallucination detection system for AI outputs"""

    def __init__(self):
        self.knowledge_base = self._initialize_knowledge_base()
        self.detection_patterns = self._initialize_detection_patterns()
        self.test_results = []

    def _initialize_knowledge_base(self) -> Dict[str, Any]:
        """Initialize knowledge base with valid facts and constraints"""
        return {
            "valid_personality_types": {
                "mbti": ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                        "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"],
                "enneagram": [f"Type {i}" for i in range(1, 10)],
                "big_five": ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"],
                "disc": ["D", "I", "S", "C"],
                "predictive_index": ["A", "B", "C", "D"]
            },
            "score_constraints": {
                "percentage": {"min": 0, "max": 100},
                "confidence": {"min": 0.0, "max": 1.0},
                "correlation": {"min": -1.0, "max": 1.0},
                "big_five_scores": {"min": 0, "max": 100}
            },
            "team_constraints": {
                "team_size": {"min": 1, "max": 50},
                "diversity_score": {"min": 0.0, "max": 1.0},
                "satisfaction_rating": {"min": 1, "max": 10}
            },
            "valid_metrics": [
                "productivity", "satisfaction", "innovation", "collaboration",
                "communication", "efficiency", "engagement", "performance"
            ],
            "valid_timeframes": [
                "days", "weeks", "months", "quarters", "years",
                "1 week", "2 weeks", "1 month", "3 months", "6 months"
            ]
        }

    def _initialize_detection_patterns(self) -> Dict[str, List[str]]:
        """Initialize enhanced regex patterns for detecting potential hallucinations"""
        return {
            "impossible_percentages": [
                r"(\d{3,})\s*%",  # Percentages over 100
                r"(-\d+)\s*%",     # Negative percentages
                r"\b([1-9]\d{2,})%\b",  # Three-digit percentages
                r"\b(-\d+)%\b",    # Explicit negative percentages
            ],
            "impossible_correlations": [
                r"correlation.*?(-?\d+\.?\d*)",  # Any correlation value
                r"\b(-?\d+\.?\d*)\s*between",  # "1.8 between"
                r"correlation.*?of\s*(-?\d+\.?\d*)",  # "correlation of 1.8"
                r"\br\s*=\s*(-?\d+\.?\d*)",  # r = 1.8
                r"coefficient.*?(-?\d+\.?\d*)",  # coefficient values
            ],
            "invalid_personality_types": [
                r"\b[A-Z]{4}\b",  # Four-letter codes that aren't valid MBTI
                r"\bType\s*[1-9][0-9]+\b",  # Enneagram types > 9
                r"\bType\s*0\b",  # Type 0 (invalid)
                r"Big\s+Five.*?(?!Openness|Conscientiousness|Extraversion|Agreeableness|Neuroticism)",
            ],
            "impossible_scores": [
                r"score.*?(-?\d{3,})",  # Impossible scores
                r"rating.*?([1-9]\d+)",  # Ratings > 10
                r"\b(-\d+)\s*(?:points|score|rating)\b",  # Negative scores/ratings
            ],
            "made_up_statistics": [
                r"\d+\.\d+%.*?improvement.*?guaranteed",
                r"exact.*?\d+\.?\d*%.*?always",
                r"\b\d+%\s*.*?(certain|guaranteed|always|never)\b",
                r"\b(statistically|research).*?proves?\b",
                r"\b(study|research).*?shows?\b.*?\d+%",
            ],
            "contradictions": [
                r"(high.*?low|low.*?high)",
                r"(excellent.*?poor|poor.*?excellent)",
                r"(always.*?never|never.*?always)",
                r"(increase.*?decrease|decrease.*?increase)\s+simultaneously",
                r"(improved.*?worsened|worsened.*?improved)",
                r"(perfect.*?flawed|flawed.*?perfect)",
            ],
            "temporal_impossibilities": [
                r"\d+%\s*improvement\s*in\s*\d+\s*(?:seconds?|minutes?)",
                r"complete.*?transformation\s*in\s*\d+\s*(?:hours?|days?)",
                r"overnight.*?\d+%.*?change",
            ],
            "causality_fallacies": [
                r"correlation.*?implies.*?causation",
                r"because.*?therefore.*?always",
                r"post\s+hoc.*?ergo\s+propter\s+hoc",
            ],
            "assessment_specific_issues": [
                r"MBTI.*?(?!INTJ|INTP|ENTJ|ENTP|INFJ|INFP|ENFJ|ENFP|ISTJ|ISFJ|ESTJ|ESFJ|ISTP|ISFP|ESTP|ESFP)[A-Z]{4}",
                r"Big\s+Five.*?(?!Openness|Conscientiousness|Extraversion|Agreeableness|Neuroticism)\w+",
                r"Enneagram.*?Type\s*(?!Type\s+[1-9])\w+",
            ]
        }

    def generate_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate test scenarios with known ground truth"""
        scenarios = []

        # Scenario 1: Valid team analysis (should pass)
        scenarios.append({
            "scenario_id": "valid_team_001",
            "ground_truth": {
                "team_members": [
                    {"id": "user1", "personality": "ENFJ", "productivity": 8.2},
                    {"id": "user2", "personality": "ISTP", "productivity": 7.8}
                ],
                "team_size": 2,
                "avg_satisfaction": 8.0
            },
            "ai_output": """
            Team Analysis Report

            Your team of 2 members shows strong potential. The ENFJ member brings excellent
            communication skills (productivity: 8.2), while the ISTP contributes strong
            analytical capabilities (productivity: 7.8). Team satisfaction is averaging 8.0/10.

            Recommendations:
            - Leverage the complementary strengths of both personality types
            - Focus on structured communication protocols
            Expected improvement: 20-30% in team efficiency
            """,
            "expected_hallucinations": 0
        })

        # Scenario 2: AI with impossible percentages
        scenarios.append({
            "scenario_id": "impossible_metrics_001",
            "ground_truth": {
                "team_performance": 85,
                "improvement_potential": 15
            },
            "ai_output": """
            Performance Analysis

            Your team shows exceptional performance with 150% productivity improvement.
            Team collaboration has increased by 250% in the past month.
            Individual performance scores range from 120% to 180% of baseline.

            This represents a -50% reduction in project completion time.
            """,
            "expected_hallucinations": 4  # 150%, 250%, 120%-180%, -50%
        })

        # Scenario 3: AI with invalid personality types
        scenarios.append({
            "scenario_id": "invalid_types_001",
            "ground_truth": {
                "team_members": ["INTJ", "ENFP"]
            },
            "ai_output": """
            Personality Analysis

            Your team includes XXFJ and ENTP personality types, which creates an interesting dynamic.
            The XXFJ member brings warmth and empathy, while the ENTP contributes innovation.

            We also have a ZZZQ member who provides unique perspectives.
            Consider also adding a YYYY member for better balance.
            """,
            "expected_hallucinations": 3  # XXFJ, ZZZQ, YYYY
        })

        # Scenario 4: AI with contradictory statements
        scenarios.append({
            "scenario_id": "contradictions_001",
            "ground_truth": {
                "team_cohesion": "high"
            },
            "ai_output": """
            Team Dynamics Assessment

            Your team demonstrates excellent cohesion and collaboration. However, there are
            significant communication barriers preventing effective teamwork.

            Team morale is consistently high, though team members report low satisfaction.
            The leadership style is both autocratic and highly collaborative.

            Team always meets deadlines but never completes projects on time.
            """,
            "expected_hallucinations": 4  # Multiple contradictions
        })

        # Scenario 5: AI with invented data
        scenarios.append({
            "scenario_id": "invented_data_001",
            "ground_truth": {
                "assessment_data": ["big_five", "mbti"],
                "completed_assessments": 12
            },
            "ai_output": """
            Assessment Insights

            Based on the 47 completed assessments in your Advanced Leadership Competency
            framework, we can see clear patterns. The Quantum Intelligence Quotient (QIQ)
            averages 87.3% across the team.

            The Emotional Synergy Index (ESI) shows a remarkable 94% improvement after
            implementing the Neuro-Linguistic Programming protocols.

            Your team's Collective Intelligence Score (CIS) of 156.7 is in the 99th percentile.
            """,
            "expected_hallucinations": 6  # 47 assessments, QIQ, ESI, NLP protocols, CIS score, 99th percentile
        })

        # Scenario 6: AI with impossible correlations
        scenarios.append({
            "scenario_id": "impossible_correlations_001",
            "ground_truth": {
                "variables": ["personality", "performance"]
            },
            "ai_output": """
            Statistical Analysis

            Our analysis reveals a correlation of 1.8 between personality type and performance,
            which is exceptionally strong. The inverse correlation between team size and
            efficiency is -2.3, showing perfect inverse relationship.

            The correlation between satisfaction and productivity is +1.5, indicating
            that every satisfaction point directly contributes to performance.
            """,
            "expected_hallucinations": 3  # 1.8, -2.3, +1.5 correlations
        })

        return scenarios

    def detect_factual_hallucinations(self, ai_output: str,
                                    ground_truth: Dict[str, Any]) -> List[HallucinationDetection]:
        """Enhanced detection of factual hallucinations by comparing against ground truth"""
        hallucinations = []

        # Enhanced impossible percentage detection
        for pattern in self.detection_patterns["impossible_percentages"]:
            matches = re.finditer(pattern, ai_output, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.group(1))
                    if value > 100 or value < 0:
                        hallucinations.append(HallucinationDetection(
                            detection_id=f"impossible_percentage_{hash(match.group(0)) % 10000}",
                            hallucination_type=HallucinationType.IMPOSSIBLE_METRICS,
                            severity=SeverityLevel.CRITICAL if value > 150 or value < 0 else SeverityLevel.HIGH,
                            description=f"Impossible percentage value: {value}%",
                            evidence=f"Found '{match.group(0)}' in text",
                            confidence_score=0.98,
                            location_in_text=match.group(0),
                            expected_correct_value="Percentage should be between 0-100%"
                        ))
                except (ValueError, IndexError):
                    hallucinations.append(HallucinationDetection(
                        detection_id=f"invalid_percentage_format_{hash(match.group(0)) % 10000}",
                        hallucination_type=HallucinationType.IMPOSSIBLE_METRICS,
                        severity=SeverityLevel.HIGH,
                        description=f"Invalid percentage format: {match.group(0)}",
                        evidence=f"Found malformed percentage",
                        confidence_score=0.85,
                        location_in_text=match.group(0),
                        expected_correct_value="Valid percentage format: 0-100%"
                    ))

        # Enhanced invalid personality type detection
        valid_mbti = set(self.knowledge_base["valid_personality_types"]["mbti"])
        valid_enneagram = set(self.knowledge_base["valid_personality_types"]["enneagram"])

        # Check MBTI types
        personality_matches = re.finditer(r"\b[A-Z]{4}\b", ai_output)
        for match in personality_matches:
            personality_type = match.group(0)
            if personality_type not in valid_mbti:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"invalid_mbti_{hash(personality_type) % 10000}",
                    hallucination_type=HallucinationType.FACTUAL_INCORRECTNESS,
                    severity=SeverityLevel.HIGH,
                    description=f"Invalid MBTI personality type: {personality_type}",
                    evidence=f"Found invalid MBTI type '{personality_type}'",
                    confidence_score=0.95,
                    location_in_text=match.group(0),
                    expected_correct_value=f"Valid MBTI types: {', '.join(list(valid_mbti)[:8])}..."
                ))

        # Check Enneagram types
        enneagram_matches = re.finditer(r"\bType\s*([1-9][0-9]*|[0])\b", ai_output, re.IGNORECASE)
        for match in enneagram_matches:
            type_num = int(match.group(1))
            if type_num < 1 or type_num > 9:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"invalid_enneagram_{type_num}",
                    hallucination_type=HallucinationType.FACTUAL_INCORRECTNESS,
                    severity=SeverityLevel.HIGH,
                    description=f"Invalid Enneagram type: Type {type_num}",
                    evidence=f"Found invalid Enneagram '{match.group(0)}'",
                    confidence_score=0.95,
                    location_in_text=match.group(0),
                    expected_correct_value="Valid Enneagram types: Type 1 through Type 9"
                ))

        # Enhanced impossible correlation detection
        for pattern in self.detection_patterns["impossible_correlations"]:
            matches = re.finditer(pattern, ai_output, re.IGNORECASE)
            for match in matches:
                try:
                    # Extract the correlation value
                    correlation_text = match.group(0)
                    # Look for numeric values in the match
                    numeric_matches = re.findall(r"(-?\d+\.?\d*)", correlation_text)
                    for num_str in numeric_matches:
                        correlation_value = float(num_str)
                        if abs(correlation_value) > 1.0:
                            hallucinations.append(HallucinationDetection(
                                detection_id=f"impossible_correlation_{abs(hash(correlation_text)) % 10000}",
                                hallucination_type=HallucinationType.IMPOSSIBLE_CORRELATIONS,
                                severity=SeverityLevel.CRITICAL,
                                description=f"Impossible correlation coefficient: {correlation_value}",
                                evidence=f"Found invalid correlation: {correlation_text}",
                                confidence_score=0.99,
                                location_in_text=match.group(0),
                                expected_correct_value="Correlations must be between -1.0 and 1.0"
                            ))
                except (ValueError, IndexError):
                    hallucinations.append(HallucinationDetection(
                        detection_id=f"correlation_format_error_{hash(match.group(0)) % 10000}",
                        hallucination_type=HallucinationType.FACTUAL_INCORRECTNESS,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Malformed correlation statement: {match.group(0)}",
                        evidence="Invalid correlation format detected",
                        confidence_score=0.80,
                        location_in_text=match.group(0),
                        expected_correct_value="Valid correlation: r = X.Y where -1.0 ≤ X.Y ≤ 1.0"
                    ))

        # Detect made-up statistics and guarantees
        for pattern in self.detection_patterns["made_up_statistics"]:
            matches = re.finditer(pattern, ai_output, re.IGNORECASE)
            for match in matches:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"made_up_stats_{hash(match.group(0)) % 10000}",
                    hallucination_type=HallucinationType.INVENTED_DATA,
                    severity=SeverityLevel.HIGH,
                    description=f"Suspicious statistical claim or guarantee: {match.group(0)}",
                    evidence=f"Found potentially fabricated statistics",
                    confidence_score=0.85,
                    location_in_text=match.group(0),
                    expected_correct_value="Avoid absolute guarantees in psychological assessments"
                ))

        # Detect temporal impossibilities
        for pattern in self.detection_patterns["temporal_impossibilities"]:
            matches = re.finditer(pattern, ai_output, re.IGNORECASE)
            for match in matches:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"temporal_impossibility_{hash(match.group(0)) % 10000}",
                    hallucination_type=HallucinationType.LOGICAL_INCONSISTENCIES,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Temporal impossibility: {match.group(0)}",
                    evidence=f"Found unrealistic timeframe claim",
                    confidence_score=0.80,
                    location_in_text=match.group(0),
                    expected_correct_value="Psychological changes require reasonable timeframes"
                ))

        return hallucinations

    def detect_contradictions(self, ai_output: str) -> List[HallucinationDetection]:
        """Detect contradictory statements in AI output"""
        hallucinations = []
        sentences = re.split(r'[.!?]+', ai_output)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Look for contradictory patterns
        for pattern in self.detection_patterns["contradictions"]:
            matches = re.finditer(pattern, ai_output, re.IGNORECASE)
            for match in matches:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"contradiction_{hash(match.group(0)) % 10000}",
                    hallucination_type=HallucinationType.CONTRADICTORY_STATEMENTS,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Contradictory statement detected",
                    evidence=f"Found contradiction: {match.group(0)}",
                    confidence_score=0.75,
                    location_in_text=match.group(0)
                ))

        # Check sentence-level contradictions
        positive_words = {"excellent", "high", "strong", "good", "effective", "successful", "always"}
        negative_words = {"poor", "low", "weak", "bad", "ineffective", "failed", "never"}

        for i, sentence in enumerate(sentences):
            pos_count = len([w for w in positive_words if w in sentence.lower()])
            neg_count = len([w for w in negative_words if w in sentence.lower()])

            if pos_count > 0 and neg_count > 0:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"sentence_contradiction_{i}",
                    hallucination_type=HallucinationType.CONTRADICTORY_STATEMENTS,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Sentence contains contradictory sentiment",
                    evidence=f"Sentence: {sentence[:100]}...",
                    confidence_score=0.60,
                    location_in_text=sentence[:50]
                ))

        return hallucinations

    def detect_invented_data(self, ai_output: str,
                           ground_truth: Dict[str, Any]) -> List[HallucinationDetection]:
        """Detect invented or fabricated data"""
        hallucinations = []

        # Check for made-up assessment frameworks
        known_frameworks = {"mbti", "big_five", "enneagram", "disc", "predictive_index", "strengthsfinder"}
        framework_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:framework|assessment|test|index)"

        matches = re.finditer(framework_pattern, ai_output)
        for match in matches:
            framework_name = match.group(1).lower()
            if framework_name not in known_frameworks:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"unknown_framework_{hash(framework_name) % 10000}",
                    hallucination_type=HallucinationType.INVENTED_DATA,
                    severity=SeverityLevel.HIGH,
                    description=f"Unknown assessment framework mentioned",
                    evidence=f"Unknown framework: {match.group(0)}",
                    confidence_score=0.85,
                    location_in_text=match.group(0),
                    expected_correct_value="Use only recognized assessment frameworks"
                ))

        # Check for unrealistic improvement claims
        improvement_pattern = r"(\d{2,3})%\s*(?:improvement|increase|boost|gain)"
        matches = re.finditer(improvement_pattern, ai_output, re.IGNORECASE)
        for match in matches:
            percentage = int(match.group(1))
            if percentage > 50:  # Unrealistic improvement claims
                hallucinations.append(HallucinationDetection(
                    detection_id=f"unrealistic_improvement_{hash(match.group(0)) % 10000}",
                    hallucination_type=HallucinationType.FACTUAL_INCORRECTNESS,
                    severity=SeverityLevel.MEDIUM,
                    description=f"Unrealistic improvement claim: {percentage}%",
                    evidence=f"Claim: {match.group(0)}",
                    confidence_score=0.70,
                    location_in_text=match.group(0),
                    expected_correct_value="Realistic improvements are typically 5-30%"
                ))

        return hallucinations

    def detect_logical_inconsistencies(self, ai_output: str) -> List[HallucinationDetection]:
        """Detect logical inconsistencies in the reasoning"""
        hallucinations = []

        # Check for circular reasoning
        if "because" in ai_output.lower() and ai_output.lower().count("because") > 2:
            hallucinations.append(HallucinationDetection(
                detection_id="circular_reasoning",
                hallucination_type=HallucinationType.LOGICAL_INCONSISTENCIES,
                severity=SeverityLevel.LOW,
                description="Potential circular reasoning detected",
                evidence="Multiple 'because' clauses may indicate circular logic",
                confidence_score=0.60,
                location_in_text="text contains multiple causal claims"
            ))

        # Check for overconfident claims
        overconfidence_patterns = [
            r"\b100%\s*(?:certain|guaranteed|always|never)\b",
            r"\b(always|never)\b.*?\b(every|all|none)\b"
        ]

        for pattern in overconfidence_patterns:
            matches = re.finditer(pattern, ai_output, re.IGNORECASE)
            for match in matches:
                hallucinations.append(HallucinationDetection(
                    detection_id=f"overconfidence_{hash(match.group(0)) % 10000}",
                    hallucination_type=HallucinationType.LOGICAL_INCONSISTENCIES,
                    severity=SeverityLevel.LOW,
                    description="Overconfident absolute claim",
                    evidence=f"Absolute claim: {match.group(0)}",
                    confidence_score=0.65,
                    location_in_text=match.group(0),
                    expected_correct_value="Use more qualified language"
                ))

        return hallucinations

    def calculate_hallucination_score(self, hallucinations: List[HallucinationDetection]) -> float:
        """Calculate overall hallucination severity score"""
        if not hallucinations:
            return 0.0

        severity_weights = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.75,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.LOW: 0.25
        }

        weighted_score = sum(
            severity_weights[h.severity] * h.confidence_score
            for h in hallucinations
        ) / len(hallucinations)

        return min(1.0, weighted_score)

    def calculate_factual_accuracy_score(self, hallucinations: List[HallucinationDetection]) -> float:
        """Calculate factual accuracy score (inverse of hallucination score)"""
        hallucination_score = self.calculate_hallucination_score(hallucinations)
        return max(0.0, 1.0 - hallucination_score)

    async def test_hallucination_detection(self, scenarios: List[Dict[str, Any]]) -> List[HallucinationTestResult]:
        """Run hallucination detection on test scenarios"""
        print("🔍 AI HALLUCINATION DETECTION TESTING")
        print("=" * 60)

        results = []

        for scenario in scenarios:
            print(f"\n📊 Testing: {scenario['scenario_id']}")

            ai_output = scenario["ai_output"]
            ground_truth = scenario["ground_truth"]

            # Run all detection methods
            factual_hallucinations = self.detect_factual_hallucinations(ai_output, ground_truth)
            contradictions = self.detect_contradictions(ai_output)
            invented_data = self.detect_invented_data(ai_output, ground_truth)
            logical_issues = self.detect_logical_inconsistencies(ai_output)

            # Combine all hallucinations
            all_hallucinations = (
                factual_hallucinations + contradictions +
                invented_data + logical_issues
            )

            # Remove duplicates (same detection_id)
            seen_ids = set()
            unique_hallucinations = []
            for h in all_hallucinations:
                if h.detection_id not in seen_ids:
                    seen_ids.add(h.detection_id)
                    unique_hallucinations.append(h)

            # Calculate severity distribution
            severity_distribution = defaultdict(int)
            for h in unique_hallucinations:
                severity_distribution[h.severity.value] += 1

            # Calculate scores
            hallucination_score = self.calculate_hallucination_score(unique_hallucinations)
            factual_accuracy_score = self.calculate_factual_accuracy_score(unique_hallucinations)

            # Generate recommendations
            recommendations = []
            if hallucination_score > 0.7:
                recommendations.append("Critical hallucination issues detected - review model training data")
            elif hallucination_score > 0.4:
                recommendations.append("Moderate hallucination risk - implement output validation")
            elif hallucination_score > 0.2:
                recommendations.append("Minor hallucination risk - enhance fact-checking mechanisms")
            else:
                recommendations.append("Low hallucination risk - current safeguards are effective")

            # Specific recommendations based on detected issues
            if any(h.hallucination_type == HallucinationType.IMPOSSIBLE_METRICS for h in unique_hallucinations):
                recommendations.append("Implement metric validation constraints")

            if any(h.hallucination_type == HallucinationType.FACTUAL_INCORRECTNESS for h in unique_hallucinations):
                recommendations.append("Enhance knowledge base with verified facts")

            if any(h.hallucination_type == HallucinationType.CONTRADICTORY_STATEMENTS for h in unique_hallucinations):
                recommendations.append("Add consistency checking for output coherence")

            # Create result
            result = HallucinationTestResult(
                test_id=f"hallucination_test_{scenario['scenario_id']}",
                input_data=ground_truth,
                ai_output=ai_output,
                hallucinations_detected=unique_hallucinations,
                hallucination_count=len(unique_hallucinations),
                severity_distribution=dict(severity_distribution),
                overall_hallucination_score=hallucination_score,
                factual_accuracy_score=factual_accuracy_score,
                recommendations=recommendations
            )

            results.append(result)

            # Print summary
            print(f"   🔍 Hallucinations Found: {len(unique_hallucinations)}")
            print(f"   📈 Hallucination Score: {hallucination_score:.3f}")
            print(f"   ✅ Factual Accuracy: {factual_accuracy_score:.3f}")
            print(f"   ⚠️  Expected vs Actual: {scenario['expected_hallucinations']} vs {len(unique_hallucinations)}")

        return results

    async def run_comprehensive_hallucination_tests(self) -> Dict[str, Any]:
        """Run comprehensive hallucination detection testing"""
        print("🚀 Starting AI Hallucination Detection Testing Suite")

        # Generate test scenarios
        scenarios = self.generate_test_scenarios()
        print(f"Generated {len(scenarios)} test scenarios")

        # Run tests
        results = await self.test_hallucination_detection(scenarios)

        # Calculate overall metrics
        total_hallucinations = sum(r.hallucination_count for r in results)
        avg_hallucination_score = statistics.mean([r.overall_hallucination_score for r in results])
        avg_factual_accuracy = statistics.mean([r.factual_accuracy_score for r in results])

        # Severity distribution across all tests
        total_severity_distribution = defaultdict(int)
        for result in results:
            for severity, count in result.severity_distribution.items():
                total_severity_distribution[severity] += count

        # Detection effectiveness
        expected_total = sum(s["expected_hallucinations"] for s in scenarios)
        detection_accuracy = min(1.0, total_hallucinations / max(1, expected_total))

        # Hallucination type distribution
        type_distribution = defaultdict(int)
        for result in results:
            for h in result.hallucinations_detected:
                type_distribution[h.hallucination_type.value] += 1

        # Critical issues identification
        critical_results = [r for r in results if r.overall_hallucination_score > 0.7]
        high_risk_results = [r for r in results if 0.4 < r.overall_hallucination_score <= 0.7]

        # Generate recommendations
        recommendations = []
        if avg_factual_accuracy >= 0.8:
            recommendations.append("✅ Excellent factual accuracy - AI outputs are reliable")
        elif avg_factual_accuracy >= 0.6:
            recommendations.append("⚠️ Good factual accuracy with room for improvement")
        else:
            recommendations.append("❌ Significant factual accuracy issues - immediate action required")

        recommendations.extend([
            "Implement real-time hallucination detection in production",
            "Create comprehensive fact-checking knowledge base",
            "Add output validation constraints for metrics and percentages",
            "Develop contradiction detection algorithms",
            "Establish regular model audit procedures"
        ])

        # Prepare comprehensive report
        report = {
            "test_summary": {
                "total_scenarios_tested": len(scenarios),
                "total_hallucinations_detected": total_hallucinations,
                "expected_hallucinations": expected_total,
                "detection_accuracy_rate": detection_accuracy,
                "avg_hallucination_score": avg_hallucination_score,
                "avg_factual_accuracy": avg_factual_accuracy,
                "target_accuracy": 0.80,
                "meets_target": avg_factual_accuracy >= 0.80
            },
            "severity_distribution": dict(total_severity_distribution),
            "hallucination_type_distribution": dict(type_distribution),
            "risk_assessment": {
                "critical_risk_scenarios": len(critical_results),
                "high_risk_scenarios": len(high_risk_results),
                "low_risk_scenarios": len(results) - len(critical_results) - len(high_risk_results)
            },
            "detailed_results": [
                {
                    "test_id": result.test_id,
                    "scenario_id": result.test_id.replace("hallucination_test_", ""),
                    "hallucinations_found": result.hallucination_count,
                    "hallucination_score": result.overall_hallucination_score,
                    "factual_accuracy": result.factual_accuracy_score,
                    "severity_breakdown": result.severity_distribution,
                    "recommendations": result.recommendations[:3],  # Top 3 recommendations
                    "hallucination_types": list(set(h.hallucination_type.value for h in result.hallucinations_detected))
                }
                for result in results
            ],
            "recommendations": recommendations,
            "quality_metrics": {
                "detection_precision": detection_accuracy,
                "high_severity_rate": total_severity_distribution.get("critical", 0) / max(1, total_hallucinations),
                "consistency_issues": total_severity_distribution.get("low", 0) + total_severity_distribution.get("medium", 0)
            }
        }

        return report

async def main():
    """Main function to run hallucination detection tests"""
    detector = AIHallucinationDetector()

    # Run comprehensive tests
    results = await detector.run_comprehensive_hallucination_tests()

    # Print results summary
    print(f"\n{'='*60}")
    print("AI HALLUCINATION DETECTION TEST RESULTS")
    print(f"{'='*60}")

    summary = results["test_summary"]
    print(f"📊 EXECUTION SUMMARY:")
    print(f"   Scenarios Tested: {summary['total_scenarios_tested']}")
    print(f"   Hallucinations Detected: {summary['total_hallucinations_detected']}")
    print(f"   Expected Hallucinations: {summary['expected_hallucinations']}")
    print(f"   Detection Accuracy: {summary['detection_accuracy_rate']:.1%}")
    print(f"   Avg Hallucination Score: {summary['avg_hallucination_score']:.3f}")
    print(f"   Avg Factual Accuracy: {summary['avg_factual_accuracy']:.1%}")
    print(f"   Target Accuracy: {summary['target_accuracy']:.1%}")
    print(f"   Meets Target: {'✅ YES' if summary['meets_target'] else '❌ NO'}")

    print(f"\n🔍 SEVERITY DISTRIBUTION:")
    for severity, count in results["severity_distribution"].items():
        print(f"   {severity.replace('_', ' ').title()}: {count}")

    print(f"\n⚠️ RISK ASSESSMENT:")
    risk = results["risk_assessment"]
    print(f"   Critical Risk Scenarios: {risk['critical_risk_scenarios']}")
    print(f"   High Risk Scenarios: {risk['high_risk_scenarios']}")
    print(f"   Low Risk Scenarios: {risk['low_risk_scenarios']}")

    print(f"\n🎯 HALLUCINATION TYPES FOUND:")
    for h_type, count in results["hallucination_type_distribution"].items():
        print(f"   {h_type.replace('_', ' ').title()}: {count}")

    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"   {i}. {rec}")

    print(f"\n📈 QUALITY METRICS:")
    quality = results["quality_metrics"]
    print(f"   Detection Precision: {quality['detection_precision']:.1%}")
    print(f"   High Severity Rate: {quality['high_severity_rate']:.1%}")
    print(f"   Consistency Issues: {quality['consistency_issues']}")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"ai_hallucination_detection_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 DETAILED RESULTS SAVED:")
    print(f"   📊 Results File: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())
