#!/usr/bin/env python3
"""
Rounding Error Validation Module
Tests rounding errors in scores across different precision levels and calculation methods
"""

import asyncio
import json
import time
import statistics
import math
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_DOWN, ROUND_HALF_EVEN, ROUND_UP, ROUND_DOWN, ROUND_CEILING, ROUND_FLOOR
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random

# Import the scoring engine from previous tests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_psychometric_scoring_consistency import (
    AssessmentType, AssessmentQuestion, AssessmentResponse, ScoringResult,
    PsychometricScoringEngine
)

class RoundingMethod(Enum):
    """Different rounding methods to test"""
    ROUND_HALF_UP = "round_half_up"
    ROUND_HALF_DOWN = "round_half_down"
    ROUND_HALF_EVEN = "round_half_even"
    ROUND_UP = "round_up"
    ROUND_DOWN = "round_down"
    ROUND_CEILING = "round_ceiling"
    ROUND_FLOOR = "round_floor"

class PrecisionLevel(Enum):
    """Different precision levels to test"""
    LOW = 0      # 0 decimal places
    MEDIUM = 1    # 1 decimal place
    HIGH = 2      # 2 decimal places
    VERY_HIGH = 3 # 3 decimal places
    MAX = 6       # 6 decimal places (full precision)

@dataclass
class RoundingTestResult:
    """Result of rounding error testing"""
    rounding_method: RoundingMethod
    precision_level: PrecisionLevel
    original_scores: Dict[str, float]
    rounded_scores: Dict[str, float]
    rounding_errors: Dict[str, float]
    max_error: float
    avg_error: float
    cumulative_error: float
    processing_time: float

@dataclass
class ErrorClassification:
    """Classification of rounding errors"""
    error_level: str  # "negligible", "minor", "moderate", "significant", "critical"
    threshold_exceeded: bool
    impact_assessment: str
    recommended_action: str

@dataclass
class PrecisionAnalysisResult:
    """Analysis of precision impact on scores"""
    precision_level: PrecisionLevel
    score_variations: Dict[str, List[float]]
    variance_analysis: Dict[str, float]
    coefficient_of_variation: Dict[str, float]
    stability_rating: str
    recommended_precision: int

@dataclass
class CumulativeErrorAnalysis:
    """Analysis of cumulative rounding errors"""
    calculation_steps: List[str]
    step_errors: List[float]
    cumulative_error: float
    error_magnification_factor: float
    critical_threshold_exceeded: bool

@dataclass
class RoundingValidationResult:
    """Overall rounding validation result"""
    test_name: str
    assessment_type: str
    rounding_methods: List[RoundingMethod]
    precision_levels: List[PrecisionLevel]
    rounding_results: List[RoundingTestResult]
    precision_analysis: List[PrecisionAnalysisResult]
    cumulative_error_analysis: List[CumulativeErrorAnalysis]
    overall_accuracy: float
    error_classifications: Dict[str, ErrorClassification]
    recommendations: List[str]
    timestamp: datetime

class RoundingErrorValidator:
    """Comprehensive rounding error validation system"""

    def __init__(self):
        self.engine = PsychometricScoringEngine()
        self.error_thresholds = self._initialize_error_thresholds()
        self.rounding_functions = {
            RoundingMethod.ROUND_HALF_UP: self._round_half_up,
            RoundingMethod.ROUND_HALF_DOWN: self._round_half_down,
            RoundingMethod.ROUND_HALF_EVEN: self._round_half_even,
            RoundingMethod.ROUND_UP: self._round_up,
            RoundingMethod.ROUND_DOWN: self._round_down,
            RoundingMethod.ROUND_CEILING: self._round_ceiling,
            RoundingMethod.ROUND_FLOOR: self._round_floor
        }

    def _initialize_error_thresholds(self) -> Dict[str, float]:
        """Initialize error thresholds for different precision levels"""
        return {
            "negligible": 0.01,    # 0.01% error
            "minor": 0.1,         # 0.1% error
            "moderate": 1.0,      # 1% error
            "significant": 5.0,   # 5% error
            "critical": 10.0      # 10% error
        }

    def _round_half_up(self, value: float, precision: int) -> float:
        """Round half up (standard rounding)"""
        factor = 10 ** precision
        return math.floor(value * factor + 0.5) / factor

    def _round_half_down(self, value: float, precision: int) -> float:
        """Round half down (banker's rounding opposite)"""
        factor = 10 ** precision
        return math.ceil(value * factor - 0.5) / factor

    def _round_half_even(self, value: float, precision: int) -> float:
        """Round half even (IEEE 754 standard)"""
        return round(value, precision)

    def _round_up(self, value: float, precision: int) -> float:
        """Always round up (ceil)"""
        factor = 10 ** precision
        return math.ceil(value * factor) / factor

    def _round_down(self, value: float, precision: int) -> float:
        """Always round down (floor)"""
        factor = 10 ** precision
        return math.floor(value * factor) / factor

    def _round_ceiling(self, value: float, precision: int) -> float:
        """Mathematical ceiling"""
        return math.ceil(value * (10 ** precision)) / (10 ** precision)

    def _round_floor(self, value: float, precision: int) -> float:
        """Mathematical floor"""
        return math.floor(value * (10 ** precision)) / (10 ** precision)

    def apply_rounding_method(self, scores: Dict[str, float],
                            rounding_method: RoundingMethod,
                            precision_level: PrecisionLevel) -> Dict[str, float]:
        """Apply specific rounding method to scores"""
        rounding_function = self.rounding_functions[rounding_method]
        precision = precision_level.value

        rounded_scores = {}
        for category, score in scores.items():
            rounded_scores[category] = rounding_function(score, precision)

        return rounded_scores

    def calculate_rounding_errors(self, original_scores: Dict[str, float],
                               rounded_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate rounding errors for each score category"""
        errors = {}
        for category in original_scores:
            if category in rounded_scores:
                original = original_scores[category]
                rounded = rounded_scores[category]
                # Calculate percentage error
                if original != 0:
                    error = abs((rounded - original) / original) * 100
                else:
                    error = abs(rounded) * 100  # For zero original values
                errors[category] = error
        return errors

    async def test_rounding_methods(self, assessment_type: AssessmentType,
                                  rounding_method: RoundingMethod,
                                  precision_level: PrecisionLevel) -> RoundingTestResult:
        """Test specific rounding method and precision combination"""

        # Generate test assessment data
        questions = self.engine.question_banks[assessment_type]
        responses = []

        for question in questions:
            response = AssessmentResponse(
                question_id=question.id,
                answer_value=random.randint(1, 5),
                response_time=random.uniform(1.0, 8.0),
                timestamp=datetime.now()
            )
            responses.append(response)

        # Get original scores with high precision
        start_time = time.time()
        original_result = await self.engine.score_assessment(assessment_type, responses)
        processing_time = time.time() - start_time

        # Apply rounding method
        rounded_scores = self.apply_rounding_method(
            original_result.normalized_scores,
            rounding_method,
            precision_level
        )

        # Calculate errors
        rounding_errors = self.calculate_rounding_errors(
            original_result.normalized_scores,
            rounded_scores
        )

        # Calculate error metrics
        max_error = max(rounding_errors.values()) if rounding_errors else 0
        avg_error = statistics.mean(rounding_errors.values()) if rounding_errors else 0
        cumulative_error = sum(rounding_errors.values())

        return RoundingTestResult(
            rounding_method=rounding_method,
            precision_level=precision_level,
            original_scores=original_result.normalized_scores,
            rounded_scores=rounded_scores,
            rounding_errors=rounding_errors,
            max_error=max_error,
            avg_error=avg_error,
            cumulative_error=cumulative_error,
            processing_time=processing_time
        )

    async def test_precision_levels(self, assessment_type: AssessmentType) -> List[PrecisionAnalysisResult]:
        """Test different precision levels for score stability"""

        # Generate multiple test results to analyze variance
        test_results = []
        num_iterations = 20

        for _ in range(num_iterations):
            questions = self.engine.question_banks[assessment_type]
            responses = []

            for question in questions:
                response = AssessmentResponse(
                    question_id=question.id,
                    answer_value=random.randint(1, 5),
                    response_time=random.uniform(1.0, 8.0),
                    timestamp=datetime.now()
                )
                responses.append(response)

            result = await self.engine.score_assessment(assessment_type, responses)
            test_results.append(result.normalized_scores)

        # Analyze precision levels
        precision_results = []

        for precision_level in PrecisionLevel:
            # Apply rounding to all results
            rounded_results = []
            for test_result in test_results:
                rounded = self.apply_rounding_method(
                    test_result,
                    RoundingMethod.ROUND_HALF_EVEN,  # Standard rounding
                    precision_level
                )
                rounded_results.append(rounded)

            # Calculate variance analysis
            score_variations = {}
            variance_analysis = {}
            coefficient_of_variation = {}

            for category in test_results[0].keys():
                values = [result[category] for result in rounded_results]
                score_variations[category] = values

                if values:
                    mean_val = statistics.mean(values)
                    variance = statistics.variance(values) if len(values) > 1 else 0
                    variance_analysis[category] = variance

                    # Coefficient of variation (CV)
                    if mean_val != 0:
                        cv = (statistics.stdev(values) / mean_val) * 100 if len(values) > 1 else 0
                        coefficient_of_variation[category] = cv
                    else:
                        coefficient_of_variation[category] = 0

            # Determine stability rating
            avg_cv = statistics.mean(coefficient_of_variation.values()) if coefficient_of_variation else 0

            if avg_cv < 1:
                stability_rating = "Excellent"
            elif avg_cv < 5:
                stability_rating = "Good"
            elif avg_cv < 10:
                stability_rating = "Fair"
            else:
                stability_rating = "Poor"

            # Recommended precision based on CV
            if avg_cv < 1:
                recommended_precision = 2  # 2 decimal places is sufficient
            elif avg_cv < 5:
                recommended_precision = 3  # 3 decimal places
            else:
                recommended_precision = 6  # Full precision

            precision_results.append(PrecisionAnalysisResult(
                precision_level=precision_level,
                score_variations=score_variations,
                variance_analysis=variance_analysis,
                coefficient_of_variation=coefficient_of_variation,
                stability_rating=stability_rating,
                recommended_precision=recommended_precision
            ))

        return precision_results

    async def test_cumulative_errors(self, assessment_type: AssessmentType) -> List[CumulativeErrorAnalysis]:
        """Test cumulative rounding errors in multi-step calculations"""

        # Generate test assessment
        questions = self.engine.question_banks[assessment_type]
        responses = []

        for question in questions:
            response = AssessmentResponse(
                question_id=question.id,
                answer_value=random.randint(1, 5),
                response_time=random.uniform(1.0, 8.0),
                timestamp=datetime.now()
            )
            responses.append(response)

        # Simulate multi-step calculation with rounding at each step
        original_result = await self.engine.score_assessment(assessment_type, responses)
        cumulative_analyses = []

        # Test different rounding at each calculation step
        for precision_level in [0, 1, 2]:  # Test key precision levels

            calculation_steps = [
                "Step 1: Raw response aggregation",
                "Step 2: Category scoring with rounding",
                "Step 3: Normalization with rounding",
                "Step 4: Final score calculation with rounding"
            ]

            step_errors = []
            current_scores = original_result.raw_scores.copy()

            # Simulate multi-step rounding
            for i, step_name in enumerate(calculation_steps):
                # Apply rounding at this step
                if i >= 1:  # Don't round the first step (raw aggregation)
                    current_scores = {
                        category: self._round_half_up(score, precision_level)
                        for category, score in current_scores.items()
                    }

                # Simulate next calculation step
                if i == 1:  # Category scoring
                    # Convert raw scores to normalized scores with rounding
                    max_possible = 100.0  # Simplified for testing
                    current_scores = {
                        category: min(100, (score / max_possible) * 100)
                        for category, score in current_scores.items()
                    }
                elif i == 2:  # Normalization
                    total = sum(current_scores.values())
                    if total > 0:
                        current_scores = {
                            category: (score / total) * 100
                            for category, score in current_scores.items()
                        }

                # Calculate error at this step compared to original
                if i >= 1:
                    original_normalized = original_result.normalized_scores
                    step_error = 0
                    for category in current_scores:
                        if category in original_normalized:
                            error = abs(current_scores[category] - original_normalized[category])
                            step_error += error
                    step_errors.append(step_error / len(current_scores))

            # Calculate cumulative error and magnification
            cumulative_error = sum(step_errors)
            error_magnification_factor = cumulative_error / max(step_errors) if step_errors else 1
            critical_threshold_exceeded = cumulative_error > 10.0  # 10% threshold

            cumulative_analyses.append(CumulativeErrorAnalysis(
                calculation_steps=calculation_steps,
                step_errors=step_errors,
                cumulative_error=cumulative_error,
                error_magnification_factor=error_magnification_factor,
                critical_threshold_exceeded=critical_threshold_exceeded
            ))

        return cumulative_analyses

    def classify_errors(self, rounding_results: List[RoundingTestResult]) -> Dict[str, ErrorClassification]:
        """Classify rounding errors by severity"""
        classifications = {}

        for result in rounding_results:
            method_name = f"{result.rounding_method.value}_{result.precision_level.value}"

            max_error = result.max_error
            avg_error = result.avg_error

            # Determine error level based on max error
            if max_error <= self.error_thresholds["negligible"]:
                error_level = "negligible"
            elif max_error <= self.error_thresholds["minor"]:
                error_level = "minor"
            elif max_error <= self.error_thresholds["moderate"]:
                error_level = "moderate"
            elif max_error <= self.error_thresholds["significant"]:
                error_level = "significant"
            else:
                error_level = "critical"

            threshold_exceeded = max_error > self.error_thresholds["moderate"]

            # Impact assessment
            if error_level in ["negligible", "minor"]:
                impact = "Minimal impact on assessment accuracy"
                recommended_action = "Current rounding method is acceptable"
            elif error_level == "moderate":
                impact = "May affect fine-grained comparisons"
                recommended_action = "Consider increasing precision"
            elif error_level == "significant":
                impact = "Could affect assessment decisions"
                recommended_action = "Increase precision or use different rounding method"
            else:
                impact = "Severe impact on assessment validity"
                recommended_action = "Immediate review of rounding strategy required"

            classifications[method_name] = ErrorClassification(
                error_level=error_level,
                threshold_exceeded=threshold_exceeded,
                impact_assessment=impact,
                recommended_action=recommended_action
            )

        return classifications

    async def validate_rounding_errors(self, assessment_type: AssessmentType) -> RoundingValidationResult:
        """Comprehensive rounding error validation"""
        print(f"Validating rounding errors for {assessment_type.value}...")

        rounding_results = []

        # Test all rounding method and precision combinations
        for rounding_method in RoundingMethod:
            for precision_level in PrecisionLevel:
                result = await self.test_rounding_methods(
                    assessment_type, rounding_method, precision_level
                )
                rounding_results.append(result)

        # Test precision levels
        precision_analysis = await self.test_precision_levels(assessment_type)

        # Test cumulative errors
        cumulative_error_analysis = await self.test_cumulative_errors(assessment_type)

        # Classify errors
        error_classifications = self.classify_errors(rounding_results)

        # Calculate overall accuracy
        acceptable_errors = sum(1 for r in rounding_results if r.max_error <= self.error_thresholds["moderate"])
        overall_accuracy = (acceptable_errors / len(rounding_results)) * 100

        # Generate recommendations
        recommendations = []

        if overall_accuracy < 70:
            recommendations.append("Overall rounding accuracy is low - review rounding strategy")

        # Check for critical errors
        critical_errors = [r for r in rounding_results if r.max_error > self.error_thresholds["critical"]]
        if critical_errors:
            recommendations.append(f"Found {len(critical_errors)} critical error cases - immediate attention needed")

        # Check cumulative errors
        high_cumulative = [a for a in cumulative_error_analysis if a.critical_threshold_exceeded]
        if high_cumulative:
            recommendations.append("High cumulative rounding errors detected - review calculation steps")

        # Precision recommendations
        best_precision = max(precision_analysis, key=lambda p: len([c for c in p.coefficient_of_variation.values() if c < 5]))
        recommendations.append(f"Recommended precision: {best_precision.recommended_precision} decimal places for {assessment_type.value}")

        if len(recommendations) == 0:
            recommendations.append("Rounding errors are within acceptable limits")

        return RoundingValidationResult(
            test_name="rounding_error_validation",
            assessment_type=assessment_type.value,
            rounding_methods=list(RoundingMethod),
            precision_levels=list(PrecisionLevel),
            rounding_results=rounding_results,
            precision_analysis=precision_analysis,
            cumulative_error_analysis=cumulative_error_analysis,
            overall_accuracy=overall_accuracy,
            error_classifications=error_classifications,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

    async def run_comprehensive_rounding_tests(self) -> Dict[str, Any]:
        """Run comprehensive rounding tests across assessment types"""
        print("🔢 ROUNDING ERROR VALIDATION")
        print("=" * 70)

        assessment_types = [AssessmentType.BIG_FIVE, AssessmentType.MBTI, AssessmentType.ENNEAGRAM]
        validation_results = []

        for assessment_type in assessment_types:
            print(f"\n📊 Testing {assessment_type.value} assessment...")
            result = await self.validate_rounding_errors(assessment_type)
            validation_results.append(result)

        # Calculate overall metrics
        overall_accuracy_rates = [r.overall_accuracy for r in validation_results]
        overall_accuracy = statistics.mean(overall_accuracy_rates)

        total_test_combinations = sum(len(r.rounding_results) for r in validation_results)
        total_precision_analyses = sum(len(r.precision_analysis) for r in validation_results)

        # Analyze error patterns
        error_patterns = self._analyze_error_patterns(validation_results)

        # Generate comprehensive report
        report = {
            "test_summary": {
                "total_assessments_tested": len(validation_results),
                "overall_rounding_accuracy": overall_accuracy,
                "target_accuracy": 90.0,
                "total_combinations_tested": total_test_combinations,
                "total_precision_analyses": total_precision_analyses,
                "meets_target": overall_accuracy >= 90.0
            },
            "assessment_results": [
                {
                    "assessment_type": result.assessment_type,
                    "rounding_accuracy": result.overall_accuracy,
                    "methods_tested": len(result.rounding_methods) * len(result.precision_levels),
                    "critical_errors": len([r for r in result.rounding_results if r.max_error > self.error_thresholds["critical"]]),
                    "recommendations": result.recommendations[:2]  # Top 2 recommendations
                }
                for result in validation_results
            ],
            "error_patterns": error_patterns,
            "recommendations": self._generate_rounding_recommendations(validation_results),
            "rounding_method_performance": self._analyze_rounding_method_performance(validation_results)
        }

        return report

    def _analyze_error_patterns(self, validation_results: List[RoundingValidationResult]) -> Dict[str, Any]:
        """Analyze error patterns across assessments and methods"""
        patterns = {
            "method_performance": {},
            "precision_impact": {},
            "common_error_sources": []
        }

        # Analyze rounding method performance
        for method in RoundingMethod:
            method_errors = []
            for result in validation_results:
                for test_result in result.rounding_results:
                    if test_result.rounding_method == method:
                        method_errors.append(test_result.max_error)

            if method_errors:
                patterns["method_performance"][method.value] = {
                    "avg_max_error": statistics.mean(method_errors),
                    "max_error": max(method_errors),
                    "error_std": statistics.stdev(method_errors) if len(method_errors) > 1 else 0
                }

        # Analyze precision impact
        for precision in PrecisionLevel:
            precision_errors = []
            for result in validation_results:
                for test_result in result.rounding_results:
                    if test_result.precision_level == precision:
                        precision_errors.append(test_result.avg_error)

            if precision_errors:
                patterns["precision_impact"][precision.value] = {
                    "avg_error": statistics.mean(precision_errors),
                    "error_range": min(precision_errors),
                    "error_reduction_factor": precision_errors[0] / precision_errors[-1] if len(precision_errors) > 1 else 1
                }

        # Identify common error sources
        all_errors = []
        for result in validation_results:
            for test_result in result.rounding_results:
                all_errors.extend(test_result.rounding_errors.values())

        if all_errors:
            patterns["common_error_sources"] = [
                "Score normalization calculations",
                "Multi-step aggregation with intermediate rounding",
                "Floating-point precision limitations",
                "Different category score magnitudes"
            ]

        return patterns

    def _analyze_rounding_method_performance(self, validation_results: List[RoundingValidationResult]) -> Dict[str, Any]:
        """Analyze performance of different rounding methods"""
        method_scores = {}

        for method in RoundingMethod:
            method_accuracies = []
            method_errors = []

            for result in validation_results:
                method_results = [r for r in result.rounding_results if r.rounding_method == method]
                if method_results:
                    avg_accuracy = sum(1 for r in method_results if r.max_error <= 1.0) / len(method_results) * 100
                    method_accuracies.append(avg_accuracy)
                    method_errors.extend([r.max_error for r in method_results])

            if method_accuracies:
                method_scores[method.value] = {
                    "avg_accuracy": statistics.mean(method_accuracies),
                    "avg_max_error": statistics.mean(method_errors),
                    "consistency": 100 - statistics.stdev(method_accuracies) if len(method_accuracies) > 1 else 100
                }

        # Rank methods by performance
        ranked_methods = sorted(
            method_scores.items(),
            key=lambda x: x[1]["avg_accuracy"],
            reverse=True
        )

        return {
            "method_scores": method_scores,
            "recommended_method": ranked_methods[0][0] if ranked_methods else "ROUND_HALF_EVEN",
            "method_ranking": ranked_methods
        }

    def _generate_rounding_recommendations(self, validation_results: List[RoundingValidationResult]) -> List[str]:
        """Generate comprehensive rounding recommendations"""
        recommendations = []

        # Overall accuracy recommendation
        avg_accuracy = statistics.mean([r.overall_accuracy for r in validation_results])
        if avg_accuracy < 80:
            recommendations.append("Overall rounding accuracy below acceptable - implement higher precision calculations")

        # Method-specific recommendations
        method_analysis = self._analyze_rounding_method_performance(validation_results)
        best_method = method_analysis["recommended_method"]
        recommendations.append(f"Use {best_method} as standard rounding method for consistent results")

        # Precision recommendations
        precision_errors = {}
        for result in validation_results:
            for test_result in result.rounding_results:
                precision = test_result.precision_level.value
                if precision not in precision_errors:
                    precision_errors[precision] = []
                precision_errors[precision].append(test_result.avg_error)

        for precision, errors in precision_errors.items():
            avg_error = statistics.mean(errors)
            if avg_error > 5.0:
                recommendations.append(f"Avoid {precision} decimal places - average error of {avg_error:.2f}%")

        recommendations.append("Use at least 2 decimal places for intermediate calculations")
        recommendations.append("Implement consistent rounding strategy across all assessment types")

        return recommendations

async def main():
    """Main function to run rounding error validation tests"""
    validator = RoundingErrorValidator()

    # Run comprehensive tests
    results = await validator.run_comprehensive_rounding_tests()

    # Print summary
    print(f"\n{'='*70}")
    print("ROUNDING ERROR VALIDATION RESULTS")
    print(f"{'='*70}")

    summary = results["test_summary"]
    print(f"Assessments Tested: {summary['total_assessments_tested']}")
    print(f"Overall Rounding Accuracy: {summary['overall_rounding_accuracy']:.1f}%")
    print(f"Target Accuracy: {summary['target_accuracy']}%")
    print(f"Total Combinations Tested: {summary['total_combinations_tested']}")
    print(f"Meets Target: {'✅ YES' if summary['meets_target'] else '❌ NO'}")

    print(f"\nPer Assessment Results:")
    for result in results["assessment_results"]:
        print(f"  📊 {result['assessment_type'].upper()}:")
        print(f"     Rounding Accuracy: {result['rounding_accuracy']:.1f}%")
        print(f"     Methods Tested: {result['methods_tested']}")
        print(f"     Critical Errors: {result['critical_errors']}")

    print(f"\nRounding Method Performance:")
    method_perf = results["rounding_method_performance"]
    print(f"  Recommended Method: {method_perf['recommended_method'].upper()}")
    print(f"  Method Ranking:")
    for i, (method, score) in enumerate(method_perf["method_ranking"], 1):
        print(f"    {i}. {method.upper()}: {score['avg_accuracy']:.1f}% accuracy")

    print(f"\nPrecision Impact Analysis:")
    precision_impact = results["error_patterns"]["precision_impact"]
    for precision, impact in precision_impact.items():
        print(f"  {precision} decimal places: {impact['avg_error']:.3f}% avg error")

    print(f"\nRecommendations:")
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"  {i}. {rec}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"rounding_error_validation_results_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    return results

if __name__ == "__main__":
    asyncio.run(main())
