#!/usr/bin/env python3
"""
Report Accuracy Testing Module with Answer Changes
Tests report accuracy if a user changes answers midway through assessment
"""

import asyncio
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

# Import the scoring engine from the first test
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_psychometric_scoring_consistency import (
    AssessmentType, AssessmentQuestion, AssessmentResponse, ScoringResult,
    PsychometricScoringEngine
)

class ChangeScenario(Enum):
    """Different change scenarios to test"""
    SINGLE_ANSWER = "single_answer_change"
    MULTIPLE_ANSWERS = "multiple_answer_changes"
    SECTION_CHANGE = "section_based_change"
    PROGRESSIVE_CHANGES = "progressive_changes"
    CONFIDENCE_IMPACT = "confidence_score_impact"

@dataclass
class AssessmentSnapshot:
    """Snapshot of assessment state at a point in time"""
    timestamp: datetime
    responses: List[AssessmentResponse]
    current_score: ScoringResult
    completion_percentage: float
    changed_answers: List[int] = field(default_factory=list)

@dataclass
class ChangeImpactResult:
    """Result of change impact analysis"""
    scenario: ChangeScenario
    initial_result: ScoringResult
    final_result: ScoringResult
    snapshots: List[AssessmentSnapshot]
    change_magnitude: float
    direction: str  # "positive", "negative", "neutral"
    personality_type_changed: bool
    confidence_change: float
    processing_times: List[float]

@dataclass
class AccuracyTestResult:
    """Overall accuracy test result"""
    test_name: str
    assessment_type: str
    success_rate: float
    change_scenarios: Dict[str, ChangeImpactResult]
    overall_accuracy: float
    recommendations: List[str]
    timestamp: datetime

class ReportAccuracyMidwayTester:
    """Comprehensive testing suite for report accuracy with answer changes"""

    def __init__(self):
        self.engine = PsychometricScoringEngine()
        self.test_results = []

    async def test_single_answer_change(self, assessment_type: AssessmentType) -> ChangeImpactResult:
        """Test impact of changing a single answer"""
        questions = self.engine.question_banks[assessment_type]
        total_questions = min(len(questions), 20)  # Use subset for testing

        # Generate initial responses
        initial_responses = []
        for i in range(total_questions):
            question = questions[i]
            response = AssessmentResponse(
                question_id=question.id,
                answer_value=random.randint(2, 4),
                response_time=random.uniform(1.0, 8.0),
                timestamp=datetime.now()
            )
            initial_responses.append(response)

        # Get initial score
        initial_result = await self.engine.score_assessment(assessment_type, initial_responses)

        # Change one random answer
        question_to_change = random.choice(initial_responses)
        original_answer = question_to_change.answer_value
        new_answer = 1 if original_answer > 3 else 5  # Change to opposite extreme
        question_to_change.answer_value = new_answer
        question_to_change.timestamp = datetime.now()

        # Get final score
        final_result = await self.engine.score_assessment(assessment_type, initial_responses)

        # Calculate change metrics
        score_change = self._calculate_score_change(initial_result, final_result)
        change_magnitude = abs(score_change["overall_change"])
        direction = score_change["direction"]
        personality_type_changed = initial_result.personality_type != final_result.personality_type
        confidence_change = final_result.confidence_score - initial_result.confidence_score

        return ChangeImpactResult(
            scenario=ChangeScenario.SINGLE_ANSWER,
            initial_result=initial_result,
            final_result=final_result,
            snapshots=[],
            change_magnitude=change_magnitude,
            direction=direction,
            personality_type_changed=personality_type_changed,
            confidence_change=confidence_change,
            processing_times=[initial_result.processing_time, final_result.processing_time]
        )

    async def test_multiple_answer_changes(self, assessment_type: AssessmentType) -> ChangeImpactResult:
        """Test impact of changing multiple answers"""
        questions = self.engine.question_banks[assessment_type]
        total_questions = min(len(questions), 30)

        # Generate initial responses
        initial_responses = []
        for i in range(total_questions):
            question = questions[i]
            response = AssessmentResponse(
                question_id=question.id,
                answer_value=random.randint(2, 4),
                response_time=random.uniform(1.0, 8.0),
                timestamp=datetime.now()
            )
            initial_responses.append(response)

        # Get initial score
        initial_result = await self.engine.score_assessment(assessment_type, initial_responses)

        # Change multiple answers (10-20% of total)
        num_changes = max(2, total_questions // 10)
        questions_to_change = random.sample(initial_responses, num_changes)

        for question in questions_to_change:
            original_answer = question.answer_value
            new_answer = random.randint(1, 5)
            while new_answer == original_answer:
                new_answer = random.randint(1, 5)
            question.answer_value = new_answer
            question.timestamp = datetime.now()

        # Get final score
        final_result = await self.engine.score_assessment(assessment_type, initial_responses)

        # Calculate change metrics
        score_change = self._calculate_score_change(initial_result, final_result)
        change_magnitude = abs(score_change["overall_change"])
        direction = score_change["direction"]
        personality_type_changed = initial_result.personality_type != final_result.personality_type
        confidence_change = final_result.confidence_score - initial_result.confidence_score

        return ChangeImpactResult(
            scenario=ChangeScenario.MULTIPLE_ANSWERS,
            initial_result=initial_result,
            final_result=final_result,
            snapshots=[],
            change_magnitude=change_magnitude,
            direction=direction,
            personality_type_changed=personality_type_changed,
            confidence_change=confidence_change,
            processing_times=[initial_result.processing_time, final_result.processing_time]
        )

    async def test_progressive_changes(self, assessment_type: AssessmentType) -> ChangeImpactResult:
        """Test impact of progressive changes throughout assessment"""
        questions = self.engine.question_banks[assessment_type]
        total_questions = min(len(questions), 50)

        # Simulate progressive assessment with snapshots
        change_points = [10, 20, 30, 40]  # Points where changes occur
        snapshots = []

        initial_responses = []
        processing_times = []

        for i in range(total_questions):
            question = questions[i]

            # Generate response
            if i < 20:
                # First half: consistent moderate answers
                answer_value = random.randint(2, 4)
            else:
                # Second half: more extreme answers
                answer_value = random.choice([1, 1, 5, 5, 3])  # Bias towards extremes

            response = AssessmentResponse(
                question_id=question.id,
                answer_value=answer_value,
                response_time=random.uniform(1.0, 8.0),
                timestamp=datetime.now() + timedelta(seconds=i * 30)
            )
            initial_responses.append(response)

            # Take snapshot at change points
            if i + 1 in change_points:
                current_result = await self.engine.score_assessment(assessment_type, initial_responses[:i+1])
                processing_times.append(current_result.processing_time)

                snapshot = AssessmentSnapshot(
                    timestamp=response.timestamp,
                    responses=initial_responses[:i+1].copy(),
                    current_score=current_result,
                    completion_percentage=(i + 1) / total_questions * 100
                )
                snapshots.append(snapshot)

        # Get final result
        final_result = await self.engine.score_assessment(assessment_type, initial_responses)
        processing_times.append(final_result.processing_time)

        # Calculate change metrics
        if snapshots:
            initial_result = snapshots[0].current_score
            score_change = self._calculate_score_change(initial_result, final_result)
        else:
            initial_result = final_result
            score_change = {"overall_change": 0, "direction": "neutral"}

        change_magnitude = abs(score_change["overall_change"])
        direction = score_change["direction"]
        personality_type_changed = initial_result.personality_type != final_result.personality_type
        confidence_change = final_result.confidence_score - initial_result.confidence_score

        return ChangeImpactResult(
            scenario=ChangeScenario.PROGRESSIVE_CHANGES,
            initial_result=initial_result,
            final_result=final_result,
            snapshots=snapshots,
            change_magnitude=change_magnitude,
            direction=direction,
            personality_type_changed=personality_type_changed,
            confidence_change=confidence_change,
            processing_times=processing_times
        )

    def _calculate_score_change(self, initial: ScoringResult, final: ScoringResult) -> Dict[str, Any]:
        """Calculate change metrics between two scoring results"""
        if not initial.normalized_scores or not final.normalized_scores:
            return {"overall_change": 0, "direction": "neutral"}

        # Calculate average score change
        common_categories = set(initial.normalized_scores.keys()) & set(final.normalized_scores.keys())
        if not common_categories:
            return {"overall_change": 0, "direction": "neutral"}

        score_changes = []
        for category in common_categories:
            initial_score = initial.normalized_scores[category]
            final_score = final.normalized_scores[category]
            change = final_score - initial_score
            score_changes.append(change)

        overall_change = statistics.mean(score_changes) if score_changes else 0

        if abs(overall_change) < 1:
            direction = "neutral"
        elif overall_change > 0:
            direction = "positive"
        else:
            direction = "negative"

        return {
            "overall_change": overall_change,
            "direction": direction,
            "category_changes": dict(zip(common_categories, score_changes))
        }

    async def run_accuracy_tests(self, assessment_type: AssessmentType) -> AccuracyTestResult:
        """Run all accuracy tests for a specific assessment type"""
        print(f"Testing report accuracy with answer changes for {assessment_type.value}...")

        # Run all change scenarios
        scenarios = {}
        scenarios["single_answer"] = await self.test_single_answer_change(assessment_type)
        scenarios["multiple_answers"] = await self.test_multiple_answer_changes(assessment_type)
        scenarios["progressive_changes"] = await self.test_progressive_changes(assessment_type)

        # Calculate overall accuracy metrics
        successful_scenarios = 0
        total_scenarios = len(scenarios)
        personality_changes = 0
        avg_change_magnitude = 0

        for scenario_name, scenario_result in scenarios.items():
            # Consider a scenario successful if it produces reasonable changes
            if scenario_result.change_magnitude < 50:  # Less than 50% average change
                successful_scenarios += 1

            if scenario_result.personality_type_changed:
                personality_changes += 1

            avg_change_magnitude += scenario_result.change_magnitude

        avg_change_magnitude /= total_scenarios
        success_rate = (successful_scenarios / total_scenarios) * 100
        overall_accuracy = 100 - avg_change_magnitude if avg_change_magnitude < 100 else 0

        # Generate recommendations
        recommendations = []
        if avg_change_magnitude > 30:
            recommendations.append("High sensitivity to answer changes - review scoring algorithm stability")
        if personality_changes > total_scenarios * 0.5:
            recommendations.append("Frequent personality type changes - consider adding stability thresholds")
        if success_rate < 80:
            recommendations.append("Low success rate in change scenarios - review change impact handling")

        if not recommendations:
            recommendations.append("Report accuracy with answer changes is within acceptable ranges")

        return AccuracyTestResult(
            test_name="report_accuracy_with_answer_changes",
            assessment_type=assessment_type.value,
            success_rate=success_rate,
            change_scenarios=scenarios,
            overall_accuracy=overall_accuracy,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

async def main():
    """Main function to run report accuracy tests"""
    tester = ReportAccuracyMidwayTester()

    print("🔄 REPORT ACCURACY WITH ANSWER CHANGES TESTING")
    print("=" * 70)

    # Test with MBTI assessment
    assessment_type = AssessmentType.MBTI
    result = await tester.run_accuracy_tests(assessment_type)

    print(f"\n{'='*70}")
    print("REPORT ACCURACY WITH ANSWER CHANGES TEST RESULTS")
    print(f"{'='*70}")
    print(f"Assessment: {result.assessment_type}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Overall Accuracy: {result.overall_accuracy:.1f}%")

    print(f"\nChange Scenarios:")
    for scenario_name, scenario_result in result.change_scenarios.items():
        print(f"  📊 {scenario_name.replace('_', ' ').title()}:")
        print(f"     Change Magnitude: {scenario_result.change_magnitude:.2f}")
        print(f"     Direction: {scenario_result.direction}")
        print(f"     Personality Type Changed: {scenario_result.personality_type_changed}")
        print(f"     Confidence Change: {scenario_result.confidence_change:.2f}")

    print(f"\nRecommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")

    return result

if __name__ == "__main__":
    asyncio.run(main())
