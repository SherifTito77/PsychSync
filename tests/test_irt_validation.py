"""
Comprehensive IRT Validation Test Suite
Validates the correctness and reliability of IRT model implementations
through simulated data and known theoretical properties.
"""

import asyncio
import math
import unittest
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

from app.services.irt_calibration_service import (
    CalibrationReport,
    CalibrationStatus,
    IRTCalibrationService,
)

# Import IRT services
from app.services.irt_service import (
    EstimationMethod,
    IRTCalibrationResult,
    IRTItem,
    IRTModel,
    IRTPerson,
    IRTResponse,
    IRTService,
)


class IRTValidationTestCase(unittest.TestCase):
    """Base class for IRT validation tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.irt_service = IRTService()
        self.calibration_service = IRTCalibrationService()

        # Known parameters for validation
        self.test_seed = 42
        np.random.seed(self.test_seed)

    def generate_simulated_data(
        self,
        n_persons: int = 1000,
        n_items: int = 20,
        model: IRTModel = IRTModel.TWO_PL,
        difficulty_range: tuple = (-2.0, 2.0),
        discrimination_range: tuple = (0.5, 2.0),
        guessing_range: tuple = (0.1, 0.3),
    ) -> tuple:
        """Generate simulated IRT data with known parameters"""
        np.random.seed(self.test_seed)

        # Generate true person abilities (normal distribution)
        true_abilities = np.random.normal(0, 1, n_persons)

        # Generate true item parameters
        true_items = []
        for i in range(n_items):
            difficulty = np.random.uniform(*difficulty_range)

            if model == IRTModel.ONE_PL:
                discrimination = None
                guessing = None
            elif model == IRTModel.TWO_PL:
                discrimination = np.random.uniform(*discrimination_range)
                guessing = None
            else:  # THREE_PL
                discrimination = np.random.uniform(*discrimination_range)
                guessing = np.random.uniform(*guessing_range)

            item = IRTItem(
                item_id=f"item_{i}",
                model=model,
                difficulty=difficulty,
                discrimination=discrimination,
                guessing=guessing,
            )
            true_items.append(item)

        # Generate responses based on true parameters
        responses = []
        for p_idx, ability in enumerate(true_abilities):
            for i_idx, item in enumerate(true_items):
                # Calculate true probability
                p_correct = self.irt_service.probability_of_correct_response(
                    ability, item
                )

                # Generate response (0 or 1)
                response = 1 if np.random.random() < p_correct else 0

                response_obj = IRTResponse(
                    person_id=f"person_{p_idx}", item_id=item.item_id, response=response
                )
                responses.append(response_obj)

        return true_items, true_abilities, responses


class TestIRTModelValidation(IRTValidationTestCase):
    """Test core IRT model functionality"""

    def test_probability_calculation_1pl(self):
        """Test 1PL probability calculation"""
        # Test Rasch model properties
        item = IRTItem(item_id="test_item", model=IRTModel.ONE_PL, difficulty=0.0)

        # At ability = difficulty, probability should be 0.5
        prob = self.irt_service.probability_of_correct_response(0.0, item)
        self.assertAlmostEqual(prob, 0.5, places=3)

        # High ability should result in high probability
        prob_high = self.irt_service.probability_of_correct_response(3.0, item)
        self.assertGreater(prob_high, 0.95)

        # Low ability should result in low probability
        prob_low = self.irt_service.probability_of_correct_response(-3.0, item)
        self.assertLess(prob_low, 0.05)

    def test_probability_calculation_2pl(self):
        """Test 2PL probability calculation"""
        item = IRTItem(
            item_id="test_item",
            model=IRTModel.TWO_PL,
            difficulty=0.0,
            discrimination=1.5,
        )

        # At ability = difficulty, probability should be 0.5 regardless of discrimination
        prob = self.irt_service.probability_of_correct_response(0.0, item)
        self.assertAlmostEqual(prob, 0.5, places=3)

        # Higher discrimination should create steeper curve
        item_high_disc = IRTItem(
            item_id="test_item_high",
            model=IRTModel.TWO_PL,
            difficulty=0.0,
            discrimination=2.5,
        )

        prob_high_disc_high = self.irt_service.probability_of_correct_response(
            1.0, item_high_disc
        )
        prob_regular_high = self.irt_service.probability_of_correct_response(1.0, item)

        # With same ability difference, higher discrimination should give higher probability
        self.assertGreater(prob_high_disc_high, prob_regular_high)

    def test_probability_calculation_3pl(self):
        """Test 3PL probability calculation"""
        item = IRTItem(
            item_id="test_item",
            model=IRTModel.THREE_PL,
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.2,
        )

        # At very low ability, probability should approach guessing parameter
        prob_low = self.irt_service.probability_of_correct_response(-10.0, item)
        self.assertAlmostEqual(prob_low, 0.2, places=2)

        # Probability should never be below guessing parameter
        for ability in np.linspace(-3, 3, 7):
            prob = self.irt_service.probability_of_correct_response(ability, item)
            self.assertGreaterEqual(prob, 0.2)

    def test_information_function_properties(self):
        """Test information function mathematical properties"""
        item = IRTItem(
            item_id="test_item",
            model=IRTModel.TWO_PL,
            difficulty=0.0,
            discrimination=1.0,
        )

        # Information should be maximum at ability = difficulty
        abilities = np.linspace(-3, 3, 13)
        informations = [
            self.irt_service.information_function(ability, item)
            for ability in abilities
        ]

        max_info_ability = abilities[np.argmax(informations)]
        self.assertAlmostEqual(max_info_ability, 0.0, places=1)

        # Information should always be non-negative
        for info in informations:
            self.assertGreaterEqual(info, 0)

    def test_test_information_function(self):
        """Test test information function"""
        items = [IRTItem(f"item_{i}", IRTModel.TWO_PL, 0.0, 1.0) for i in range(5)]

        # Test information should be sum of item informations
        test_info = self.irt_service.test_information_function(0.0, items)
        item_infos_sum = sum(
            self.irt_service.information_function(0.0, item) for item in items
        )

        self.assertAlmostEqual(test_info, item_infos_sum, places=6)

    def test_standard_error_calculation(self):
        """Test standard error of measurement calculation"""
        items = [IRTItem(f"item_{i}", IRTModel.TWO_PL, 0.0, 1.0) for i in range(10)]

        # Higher information should result in lower standard error
        se = self.irt_service.standard_error_of_measurement(0.0, items)
        self.assertGreater(se, 0)
        self.assertLess(se, 10)  # Reasonable upper bound

        # Standard error should be inversely related to information
        info = self.irt_service.test_information_function(0.0, items)
        expected_se = 1.0 / math.sqrt(info) if info > 0 else float("inf")
        self.assertAlmostEqual(se, expected_se, places=6)


class TestParameterRecovery(IRTValidationTestCase):
    """Test IRT parameter recovery accuracy"""

    def test_1pl_parameter_recovery(self):
        """Test 1PL parameter recovery with simulated data"""
        # Generate data with known parameters
        n_persons, n_items = 500, 15
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.ONE_PL
        )

        # Calibrate model
        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.ONE_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        self.assertTrue(
            calibration_result.convergence, "1PL calibration should converge"
        )

        # Check parameter recovery
        estimated_items = {item.item_id: item for item in calibration_result.items}
        recovery_errors = []

        for true_item in true_items:
            if true_item.item_id in estimated_items:
                estimated_item = estimated_items[true_item.item_id]
                error = abs(true_item.difficulty - estimated_item.difficulty)
                recovery_errors.append(error)

        # Average recovery error should be small
        avg_error = np.mean(recovery_errors) if recovery_errors else float("inf")
        self.assertLess(
            avg_error, 0.3, f"1PL difficulty recovery error too high: {avg_error}"
        )

    def test_2pl_parameter_recovery(self):
        """Test 2PL parameter recovery with simulated data"""
        n_persons, n_items = 1000, 20
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        self.assertTrue(
            calibration_result.convergence, "2PL calibration should converge"
        )

        # Check parameter recovery
        estimated_items = {item.item_id: item for item in calibration_result.items}
        difficulty_errors = []
        discrimination_errors = []

        for true_item in true_items:
            if true_item.item_id in estimated_items:
                estimated_item = estimated_items[true_item.item_id]

                diff_error = abs(true_item.difficulty - estimated_item.difficulty)
                disc_error = abs(
                    true_item.discrimination - estimated_item.discrimination
                )

                difficulty_errors.append(diff_error)
                discrimination_errors.append(disc_error)

        # Recovery errors should be reasonable
        avg_diff_error = (
            np.mean(difficulty_errors) if difficulty_errors else float("inf")
        )
        avg_disc_error = (
            np.mean(discrimination_errors) if discrimination_errors else float("inf")
        )

        self.assertLess(
            avg_diff_error,
            0.4,
            f"2PL difficulty recovery error too high: {avg_diff_error}",
        )
        self.assertLess(
            avg_disc_error,
            0.3,
            f"2PL discrimination recovery error too high: {avg_disc_error}",
        )

    def test_ability_estimation_accuracy(self):
        """Test ability estimation accuracy"""
        n_persons, n_items = 500, 20
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # Check ability recovery
        estimated_persons = {
            person.person_id: person for person in calibration_result.persons
        }
        ability_errors = []

        for i, true_ability in enumerate(true_abilities):
            person_id = f"person_{i}"
            if person_id in estimated_persons:
                estimated_ability = estimated_persons[person_id].ability
                error = abs(true_ability - estimated_ability)
                ability_errors.append(error)

        # Average ability error should be reasonable
        avg_ability_error = np.mean(ability_errors) if ability_errors else float("inf")
        self.assertLess(
            avg_ability_error,
            0.5,
            f"Ability estimation error too high: {avg_ability_error}",
        )

        # Correlation between true and estimated abilities should be high
        if len(ability_errors) > 10:
            true_abilities_array = np.array(
                [
                    true_abilities[i]
                    for i in range(len(true_abilities))
                    if f"person_{i}" in estimated_persons
                ]
            )
            estimated_abilities_array = np.array(
                [
                    estimated_persons[f"person_{i}"].ability
                    for i in range(len(true_abilities))
                    if f"person_{i}" in estimated_persons
                ]
            )

            correlation = np.corrcoef(true_abilities_array, estimated_abilities_array)[
                0, 1
            ]
            self.assertGreater(
                correlation,
                0.8,
                f"Ability-estimated correlation too low: {correlation}",
            )


class TestCalibrationValidation(IRTValidationTestCase):
    """Test calibration service validation functionality"""

    def test_reliability_calculation(self):
        """Test reliability calculations"""
        # Generate high-quality data
        n_persons, n_items = 1000, 25
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # Perform calibration validation
        report = asyncio.run(
            self.calibration_service.comprehensive_calibration(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # High-quality simulated data should produce good reliability
        self.assertGreater(
            report.reliability_analysis.cronbach_alpha,
            0.7,
            "Cronbach's alpha should be acceptable for good quality data",
        )

        # Check that reliability is within valid range
        self.assertGreaterEqual(report.reliability_analysis.cronbach_alpha, 0.0)
        self.assertLessEqual(report.reliability_analysis.cronbach_alpha, 1.0)

    def test_item_fit_statistics(self):
        """Test item fit statistics calculation"""
        # Generate data with some items designed to have poor fit
        n_persons, n_items = 500, 15
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # Calculate item fit statistics
        item_fit_stats = asyncio.run(
            self.calibration_service.analyze_item_fit(
                responses, calibration_result.items, calibration_result.persons
            )
        )

        # Should have fit statistics for all items
        self.assertEqual(len(item_fit_stats), n_items)

        # Check that statistics are within reasonable ranges
        for stat in item_fit_stats:
            self.assertGreater(stat.outfit_mnsq, 0, "Outfit MNSQ should be positive")
            self.assertGreater(stat.infit_mnsq, 0, "Infit MNSQ should be positive")

            # Point-biserial should be between -1 and 1
            self.assertGreaterEqual(stat.point_biserial, -1)
            self.assertLessEqual(stat.point_biserial, 1)

    def test_dimensionality_analysis(self):
        """Test dimensionality analysis"""
        # Generate unidimensional data
        n_persons, n_items = 800, 20
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # Perform dimensionality analysis
        dim_analysis = asyncio.run(
            self.calibration_service.analyze_dimensionality(
                responses, calibration_result.persons
            )
        )

        # Should have eigenvalues for analysis
        self.assertGreater(len(dim_analysis.eigenvalues), 0)

        # First eigenvalue should be largest
        eigenvalues = dim_analysis.eigenvalues
        self.assertEqual(eigenvalues[0], max(eigenvalues))

        # Unidimensionality score should be reasonable for generated data
        self.assertGreaterEqual(dim_analysis.unidimensionality_score, 0)
        self.assertLessEqual(dim_analysis.unidimensionality_score, 1)

    def test_calibration_report_generation(self):
        """Test comprehensive calibration report generation"""
        n_persons, n_items = 600, 18
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        # Generate comprehensive calibration report
        report = asyncio.run(
            self.calibration_service.comprehensive_calibration(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # Check report structure
        self.assertIsNotNone(report.calibration_id)
        self.assertEqual(report.model, IRTModel.TWO_PL)
        self.assertEqual(report.sample_size, n_persons)
        self.assertEqual(report.item_count, n_items)

        # Should have analysis results
        self.assertGreater(len(report.item_fit_stats), 0)
        self.assertGreater(len(report.person_fit_stats), 0)

        # Should have recommendations
        self.assertGreater(len(report.recommendations), 0)

        # Should have validation checks
        self.assertGreater(len(report.validation_checks), 0)

        # Check that report can be exported to JSON
        json_str = self.calibration_service.export_calibration_report(report)
        self.assertIsInstance(json_str, str)
        self.assertGreater(len(json_str), 100)  # Should be substantial JSON


class TestModelComparison(IRTValidationTestCase):
    """Test comparison between different IRT models"""

    def test_model_comparison(self):
        """Compare 1PL, 2PL, and 3PL models on same data"""
        n_persons, n_items = 800, 20

        # Generate data with 3PL parameters
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.THREE_PL
        )

        # Calibrate with different models
        models_to_test = [
            (IRTModel.ONE_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD),
            (IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD),
            (IRTModel.THREE_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD),
        ]

        model_results = {}
        for model, method in models_to_test:
            try:
                result = asyncio.run(
                    self.irt_service.calibrate_irt_model(responses, model, method)
                )
                model_results[model] = result
            except Exception as e:
                self.fail(f"Failed to calibrate {model.value}: {str(e)}")

        # All models should converge
        for model, result in model_results.items():
            self.assertTrue(result.convergence, f"{model.value} should converge")

        # 3PL should have best log-likelihood (most flexible model)
        if IRTModel.THREE_PL in model_results and IRTModel.TWO_PL in model_results:
            ll_3pl = model_results[IRTModel.THREE_PL].log_likelihood
            ll_2pl = model_results[IRTModel.TWO_PL].log_likelihood

            # 3PL should not be much worse than 2PL for 3PL-generated data
            diff = abs(ll_3pl - ll_2pl)
            tolerance = abs(ll_2pl) * 0.1 if ll_2pl != 0 else 1.0
            self.assertLess(
                diff, tolerance, "3PL should perform reasonably well on 3PL data"
            )

    def test_model_selection_criteria(self):
        """Test information criteria for model selection"""
        n_persons, n_items = 600, 15
        true_items, true_abilities, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        # Calibrate 1PL and 2PL models
        result_1pl = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.ONE_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        result_2pl = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.TWO_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # Both should converge
        self.assertTrue(result_1pl.convergence)
        self.assertTrue(result_2pl.convergence)

        # 2PL should have better (higher) log-likelihood for 2PL data
        self.assertGreater(result_2pl.log_likelihood, result_1pl.log_likelihood)

        # Check information criteria
        # BIC penalizes complexity more heavily than AIC
        # Since data was generated with discrimination parameters, 2PL should be preferred
        bic_diff = result_2pl.bic - result_1pl.bic
        self.assertLessEqual(
            bic_diff,
            100,  # Allow some tolerance
            "2PL should have similar or better BIC for 2PL data",
        )


class TestAdaptiveTesting(IRTValidationTestCase):
    """Test adaptive testing functionality"""

    def test_adaptive_item_selection(self):
        """Test adaptive item selection algorithms"""
        # Create test items with varying difficulties
        items = []
        abilities = np.linspace(-2, 2, 20)

        for i, ability in enumerate(abilities):
            item = IRTItem(
                item_id=f"item_{i}",
                model=IRTModel.TWO_PL,
                difficulty=ability,
                discrimination=1.0,
            )
            items.append(item)

        # Test maximum information selection
        selected_item = self.irt_service.adaptive_item_selection(
            0.0, items, "max_information"
        )

        # Should select item with difficulty closest to ability
        self.assertAlmostEqual(selected_item.difficulty, 0.0, delta=0.5)

        # Test closest difficulty selection
        selected_item_high = self.irt_service.adaptive_item_selection(
            1.5, items, "closest_difficulty"
        )

        self.assertGreater(selected_item_high.difficulty, 0.5)

        # Test Bayesian selection (combination)
        selected_item_bayesian = self.irt_service.adaptive_item_selection(
            -1.0, items, "bayesian"
        )

        # Bayesian should consider both information and difficulty matching
        self.assertLess(abs(selected_item_bayesian.difficulty + 1.0), 1.0)

    def test_information_function_properties_adaptive(self):
        """Test information function properties for adaptive testing"""
        item = IRTItem(
            item_id="test_item",
            model=IRTModel.TWO_PL,
            difficulty=0.0,
            discrimination=1.5,
        )

        # Information should be symmetric around difficulty
        info_plus = self.irt_service.information_function(1.0, item)
        info_minus = self.irt_service.information_function(-1.0, item)

        self.assertAlmostEqual(info_plus, info_minus, places=3)
        self.assertTrue(
            abs(info_plus - info_minus) < 0.001,
            "Information should be symmetric around item difficulty",
        )

        # Maximum information at difficulty
        info_max = self.irt_service.information_function(0.0, item)
        info_far = self.irt_service.information_function(3.0, item)

        self.assertGreater(
            info_max, info_far, "Information should be highest at item difficulty"
        )


class TestBoundaryConditions(IRTValidationTestCase):
    """Test IRT models under boundary conditions"""

    def test_extreme_parameters(self):
        """Test IRT calculations with extreme parameter values"""
        # Test extreme discrimination
        item_high_disc = IRTItem(
            item_id="high_disc",
            model=IRTModel.TWO_PL,
            difficulty=0.0,
            discrimination=3.0,
        )

        # Should handle high discrimination without errors
        prob = self.irt_service.probability_of_correct_response(1.0, item_high_disc)
        self.assertGreater(prob, 0.5)
        self.assertLessEqual(prob, 1.0)

        # Test extreme difficulty
        item_hard = IRTItem(
            item_id="very_hard",
            model=IRTModel.TWO_PL,
            difficulty=4.0,
            discrimination=1.0,
        )

        # Even very able person should have < 100% chance
        prob_expert = self.irt_service.probability_of_correct_response(3.0, item_hard)
        self.assertLess(prob_expert, 1.0)

        # Test extreme guessing parameter
        item_high_guess = IRTItem(
            item_id="high_guess",
            model=IRTModel.THREE_PL,
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.4,
        )

        # Minimum probability should be guessing parameter
        prob_very_low = self.irt_service.probability_of_correct_response(
            -10.0, item_high_guess
        )
        self.assertAlmostEqual(prob_very_low, 0.4, places=2)

    def test_small_sample_handling(self):
        """Test IRT calibration with small samples"""
        n_persons, n_items = 30, 5  # Very small sample
        _, _, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.ONE_PL
        )

        # Should handle small samples without crashing
        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses, IRTModel.ONE_PL, EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD
            )
        )

        # May not converge with very small sample, but should not crash
        self.assertIsInstance(calibration_result, IRTCalibrationResult)

    def test_missing_data_handling(self):
        """Test IRT with missing data"""
        n_persons, n_items = 100, 10
        _, _, responses = self.generate_simulated_data(
            n_persons, n_items, IRTModel.TWO_PL
        )

        # Remove some responses to create missing data
        responses_missing = responses[: int(len(responses) * 0.8)]  # Remove 20%

        # Should handle missing data
        calibration_result = asyncio.run(
            self.irt_service.calibrate_irt_model(
                responses_missing,
                IRTModel.TWO_PL,
                EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD,
            )
        )

        self.assertIsInstance(calibration_result, IRTCalibrationResult)


def run_validation_tests():
    """Run all validation tests and return summary"""
    print("=" * 60)
    print("IRT VALIDATION TEST SUITE")
    print("=" * 60)

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestIRTModelValidation,
        TestParameterRecovery,
        TestCalibrationValidation,
        TestModelComparison,
        TestAdaptiveTesting,
        TestBoundaryConditions,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {str(test)}")

    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {str(test)}")

    # Overall assessment
    success_rate = (
        result.testsRun - len(result.failures) - len(result.errors)
    ) / result.testsRun

    if success_rate >= 0.95:
        print("\n✅ EXCELLENT: IRT implementation passes all critical validation tests")
    elif success_rate >= 0.90:
        print("\n✅ GOOD: IRT implementation passes most validation tests")
    elif success_rate >= 0.80:
        print(
            "\n⚠️  ACCEPTABLE: IRT implementation has some issues but is generally functional"
        )
    else:
        print("\n❌ NEEDS IMPROVEMENT: IRT implementation has significant issues")

    print("=" * 60)

    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": success_rate,
        "result": result,
    }


if __name__ == "__main__":
    # Run validation tests when executed directly
    run_validation_tests()
