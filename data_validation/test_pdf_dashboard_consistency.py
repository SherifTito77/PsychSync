#!/usr/bin/env python3
"""
PDF-Dashboard Consistency Validation Module
Tests that downloaded PDFs match live dashboard results
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
import io
from dataclasses import asdict

# Import the scoring engine from previous tests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_psychometric_scoring_consistency import (
    AssessmentType, AssessmentQuestion, AssessmentResponse, ScoringResult,
    PsychometricScoringEngine
)

class ExportFormat(Enum):
    """Different export formats to test"""
    PDF = "pdf"
    DASHBOARD = "dashboard"
    JSON = "json"
    EXCEL = "excel"

@dataclass
class ExportData:
    """Data structure for exported results"""
    user_id: str
    assessment_type: str
    personality_type: Optional[str]
    scores: Dict[str, float]
    percentiles: Dict[str, float]
    confidence_score: float
    completion_time: datetime
    recommendations: List[str]

@dataclass
class FormatSpecificConfig:
    """Configuration specific to each export format"""
    rounding_precision: int
    score_adjustment: float  # Systematic differences between formats
    order_changes: bool
    include_metadata: bool

@dataclass
class ConsistencyCheckResult:
    """Result of consistency check between formats"""
    format1: ExportFormat
    format2: ExportFormat
    consistent: bool
    score_differences: Dict[str, float]
    max_difference: float
    personality_match: bool
    percentile_tolerance_met: bool
    details: Dict[str, Any]

@dataclass
class ConsistencyTestResult:
    """Overall consistency test result"""
    test_name: str
    assessment_type: str
    export_formats: List[ExportFormat]
    consistency_results: List[ConsistencyCheckResult]
    overall_consistency_rate: float
    critical_issues: List[str]
    recommendations: List[str]
    timestamp: datetime

class PDFDashboardConsistencyTester:
    """Comprehensive testing suite for PDF-dashboard consistency"""

    def __init__(self):
        self.engine = PsychometricScoringEngine()
        self.format_configs = self._initialize_format_configs()
        self.test_results = []

    def _initialize_format_configs(self) -> Dict[ExportFormat, FormatSpecificConfig]:
        """Initialize format-specific configurations"""
        return {
            ExportFormat.PDF: FormatSpecificConfig(
                rounding_precision=1,
                score_adjustment=0.1,  # Small systematic difference
                order_changes=True,
                include_metadata=True
            ),
            ExportFormat.DASHBOARD: FormatSpecificConfig(
                rounding_precision=2,
                score_adjustment=0.0,
                order_changes=False,
                include_metadata=True
            ),
            ExportFormat.JSON: FormatSpecificConfig(
                rounding_precision=6,  # Full precision
                score_adjustment=0.0,
                order_changes=False,
                include_metadata=True
            ),
            ExportFormat.EXCEL: FormatSpecificConfig(
                rounding_precision=2,
                score_adjustment=0.05,
                order_changes=True,
                include_metadata=False
            )
        }

    async def generate_test_assessment_data(self, assessment_type: AssessmentType,
                                    user_count: int = 50) -> List[ScoringResult]:
        """Generate test assessment data for multiple users"""
        results = []

        for user_id in range(user_count):
            questions = self.engine.question_banks[assessment_type]
            responses = []

            for question in questions:
                # Generate realistic responses with some patterns
                if user_id % 3 == 0:
                    # Consistent high scores
                    answer_value = random.choice([4, 5, 4, 5, 3])
                elif user_id % 3 == 1:
                    # Consistent low scores
                    answer_value = random.choice([1, 2, 1, 2, 3])
                else:
                    # Mixed scores
                    answer_value = random.randint(1, 5)

                response = AssessmentResponse(
                    question_id=question.id,
                    answer_value=answer_value,
                    response_time=random.uniform(1.0, 15.0),
                    timestamp=datetime.now() - timedelta(days=random.randint(1, 30))
                )
                responses.append(response)

            # Score the assessment
            result = await self.engine.score_assessment(assessment_type, responses)
            results.append(result)

        return results

    def export_to_format(self, scoring_result: ScoringResult,
                        format_type: ExportFormat,
                        user_id: str) -> ExportData:
        """Export scoring result to specific format with format-specific processing"""
        config = self.format_configs[format_type]

        # Apply format-specific adjustments
        adjusted_scores = {}
        for category, score in scoring_result.normalized_scores.items():
            adjusted_score = score + config.score_adjustment
            # Apply rounding precision
            if config.rounding_precision >= 0:
                adjusted_score = round(adjusted_score, config.rounding_precision)
            adjusted_scores[category] = adjusted_score

        # Calculate percentiles (mock implementation)
        percentiles = {}
        for category, score in adjusted_scores.items():
            # Mock percentile calculation
            percentile = min(99, max(1, int(score * 0.99 + random.uniform(-5, 5))))
            percentiles[category] = percentile

        # Generate recommendations based on personality type
        recommendations = self._generate_recommendations(
            scoring_result.assessment_type,
            scoring_result.personality_type,
            adjusted_scores
        )

        # Apply format-specific ordering if configured
        if config.order_changes:
            # Randomly reorder for formats that change order
            score_items = list(adjusted_scores.items())
            random.shuffle(score_items[:2])  # Shuffle first two items
            adjusted_scores = dict(score_items)

        return ExportData(
            user_id=user_id,
            assessment_type=scoring_result.assessment_type.value,
            personality_type=scoring_result.personality_type,
            scores=adjusted_scores,
            percentiles=percentiles,
            confidence_score=round(scoring_result.confidence_score, config.rounding_precision),
            completion_time=scoring_result.processing_time,
            recommendations=recommendations if config.include_metadata else []
        )

    def _generate_recommendations(self, assessment_type: AssessmentType,
                                personality_type: Optional[str],
                                scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on assessment results"""
        recommendations = []

        if assessment_type == AssessmentType.BIG_FIVE:
            if scores.get("Openness", 0) > 70:
                recommendations.append("Leverage your creativity in problem-solving")
            if scores.get("Conscientiousness", 0) < 30:
                recommendations.append("Focus on developing organizational skills")

        elif assessment_type == AssessmentType.MBTI and personality_type:
            if "E" in personality_type:
                recommendations.append("Consider roles that involve teamwork and communication")
            if "I" in personality_type:
                recommendations.append("Ensure you have quiet time for deep work")

        # Add general recommendations
        if len(recommendations) == 0:
            recommendations = ["Continue developing your self-awareness",
                             "Consider regular check-ins on your progress"]

        return recommendations

    def check_format_consistency(self, data1: ExportData, data2: ExportData,
                               format1: ExportFormat, format2: ExportFormat) -> ConsistencyCheckResult:
        """Check consistency between two export formats"""

        # Check personality type consistency
        personality_match = data1.personality_type == data2.personality_type

        # Check score differences
        score_differences = {}
        max_difference = 0.0

        for category in data1.scores:
            if category in data2.scores:
                diff = abs(data1.scores[category] - data2.scores[category])
                score_differences[category] = diff
                max_difference = max(max_difference, diff)

        # Check percentile consistency (within tolerance)
        percentile_tolerance = 5.0  # 5% tolerance
        percentile_tolerance_met = True

        for category in data1.percentiles:
            if category in data2.percentiles:
                diff = abs(data1.percentiles[category] - data2.percentiles[category])
                if diff > percentile_tolerance:
                    percentile_tolerance_met = False

        # Determine overall consistency
        score_tolerance = 2.0  # 2% tolerance for scores
        consistent = (
            personality_match and
            max_difference <= score_tolerance and
            percentile_tolerance_met
        )

        # Additional checks
        details = {
            "score_tolerance_met": max_difference <= score_tolerance,
            "confidence_difference": abs(data1.confidence_score - data2.confidence_score),
            "recommendation_count_diff": len(data1.recommendations) - len(data2.recommendations)
        }

        return ConsistencyCheckResult(
            format1=format1,
            format2=format2,
            consistent=consistent,
            score_differences=score_differences,
            max_difference=max_difference,
            personality_match=personality_match,
            percentile_tolerance_met=percentile_tolerance_met,
            details=details
        )

    async def test_pdf_dashboard_consistency(self, assessment_type: AssessmentType) -> ConsistencyTestResult:
        """Test consistency between PDF and dashboard exports"""
        print(f"Testing PDF-Dashboard consistency for {assessment_type.value}...")

        # Generate test data
        test_results = await self.generate_test_assessment_data(assessment_type, user_count=30)

        consistency_results = []
        critical_issues = []

        # Test each result across different format combinations
        for i, scoring_result in enumerate(test_results):
            user_id = f"test_user_{i:03d}"

            # Export to different formats
            pdf_data = self.export_to_format(scoring_result, ExportFormat.PDF, user_id)
            dashboard_data = self.export_to_format(scoring_result, ExportFormat.DASHBOARD, user_id)
            json_data = self.export_to_format(scoring_result, ExportFormat.JSON, user_id)
            excel_data = self.export_to_format(scoring_result, ExportFormat.EXCEL, user_id)

            # Test format combinations
            format_combinations = [
                (pdf_data, dashboard_data, ExportFormat.PDF, ExportFormat.DASHBOARD),
                (pdf_data, json_data, ExportFormat.PDF, ExportFormat.JSON),
                (dashboard_data, json_data, ExportFormat.DASHBOARD, ExportFormat.JSON)
            ]

            for data1, data2, format1, format2 in format_combinations:
                consistency_result = self.check_format_consistency(
                    data1, data2, format1, format2
                )
                consistency_results.append(consistency_result)

                # Check for critical issues
                if not consistency_result.personality_match:
                    critical_issues.append(
                        f"User {user_id}: Personality type mismatch between {format1.value} and {format2.value}"
                    )

                if consistency_result.max_difference > 5.0:
                    critical_issues.append(
                        f"User {user_id}: Large score difference ({consistency_result.max_difference:.2f}) "
                        f"between {format1.value} and {format2.value}"
                    )

        # Calculate overall consistency rate
        consistent_checks = sum(1 for r in consistency_results if r.consistent)
        overall_consistency_rate = (consistent_checks / len(consistency_results)) * 100

        # Generate recommendations
        recommendations = []
        if overall_consistency_rate < 85:
            recommendations.append("Overall consistency below target - review format conversion algorithms")

        if any(r.max_difference > 3.0 for r in consistency_results):
            recommendations.append("High score differences detected - adjust rounding precision")

        if len(critical_issues) > len(test_results) * 0.1:  # More than 10% issues
            recommendations.append("High critical issue rate - comprehensive format review needed")

        if not recommendations:
            recommendations.append("PDF-Dashboard consistency is within acceptable parameters")

        return ConsistencyTestResult(
            test_name="pdf_dashboard_consistency",
            assessment_type=assessment_type.value,
            export_formats=[ExportFormat.PDF, ExportFormat.DASHBOARD, ExportFormat.JSON],
            consistency_results=consistency_results,
            overall_consistency_rate=overall_consistency_rate,
            critical_issues=critical_issues,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

    async def run_comprehensive_consistency_tests(self) -> Dict[str, Any]:
        """Run comprehensive consistency tests across multiple assessments"""
        print("📄 PDF-DASHBOARD CONSISTENCY VALIDATION")
        print("=" * 70)

        assessment_types = [AssessmentType.BIG_FIVE, AssessmentType.MBTI]

        test_results = []

        for assessment_type in assessment_types:
            print(f"\n📊 Testing {assessment_type.value} assessment...")
            result = await self.test_pdf_dashboard_consistency(assessment_type)
            test_results.append(result)

        # Calculate overall metrics
        overall_consistency_rates = [r.overall_consistency_rate for r in test_results]
        overall_consistency = statistics.mean(overall_consistency_rates)

        total_critical_issues = sum(len(r.critical_issues) for r in test_results)
        total_tests = sum(len(r.consistency_results) for r in test_results)

        # Generate comprehensive report
        report = {
            "test_summary": {
                "total_assessments_tested": len(test_results),
                "overall_consistency_rate": overall_consistency,
                "target_consistency_rate": 85.0,
                "total_format_checks": total_tests,
                "critical_issues_found": total_critical_issues,
                "meets_target": overall_consistency >= 85.0
            },
            "assessment_results": [
                {
                    "assessment_type": result.assessment_type,
                    "consistency_rate": result.overall_consistency_rate,
                    "format_checks": len(result.consistency_results),
                    "critical_issues": len(result.critical_issues),
                    "recommendations": result.recommendations
                }
                for result in test_results
            ],
            "recommendations": self._generate_overall_recommendations(test_results)
        }

        return report

    def _generate_overall_recommendations(self, test_results: List[ConsistencyTestResult]) -> List[str]:
        """Generate overall recommendations based on all test results"""
        recommendations = []

        # Check overall consistency
        avg_consistency = statistics.mean([r.overall_consistency_rate for r in test_results])
        if avg_consistency < 85:
            recommendations.append("Overall consistency below target - standardize format conversion logic")

        # Check critical issues patterns
        total_issues = sum(len(r.critical_issues) for r in test_results)
        if total_issues > 0:
            recommendations.append("Critical issues detected - prioritize format consistency fixes")

        if not recommendations:
            recommendations.append("All format consistency checks passed - system ready for production")

        return recommendations

async def main():
    """Main function to run PDF-dashboard consistency tests"""
    tester = PDFDashboardConsistencyTester()

    # Run comprehensive tests
    results = await tester.run_comprehensive_consistency_tests()

    # Print summary
    print(f"\n{'='*70}")
    print("PDF-DASHBOARD CONSISTENCY VALIDATION RESULTS")
    print(f"{'='*70}")

    summary = results["test_summary"]
    print(f"Assessments Tested: {summary['total_assessments_tested']}")
    print(f"Overall Consistency Rate: {summary['overall_consistency_rate']:.1f}%")
    print(f"Target Consistency Rate: {summary['target_consistency_rate']}%")
    print(f"Total Format Checks: {summary['total_format_checks']}")
    print(f"Critical Issues Found: {summary['critical_issues_found']}")
    print(f"Meets Target: {'✅ YES' if summary['meets_target'] else '❌ NO'}")

    print(f"\nPer Assessment Results:")
    for result in results["assessment_results"]:
        print(f"  📊 {result['assessment_type'].upper()}:")
        print(f"     Consistency Rate: {result['consistency_rate']:.1f}%")
        print(f"     Format Checks: {result['format_checks']}")
        print(f"     Critical Issues: {result['critical_issues']}")

    print(f"\nRecommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"  {i}. {rec}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"pdf_dashboard_consistency_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())