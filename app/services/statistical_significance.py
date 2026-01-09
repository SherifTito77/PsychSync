"""
Statistical Significance Testing Framework

Comprehensive framework for statistical significance testing including
multiple comparison corrections, power analysis, and Bayesian inference
for intervention effectiveness evaluation.
"""

from dataclasses import dataclass
from enum import Enum
import logging
import math

import numpy as np
from scipy import stats
from scipy.stats import norm, t

logger = logging.getLogger(__name__)


class MultipleComparisonCorrection(Enum):
    """Methods for multiple comparison correction"""

    BONFERRONI = "bonferroni"
    HOLM_BONFERRONI = "holm_bonferroni"
    BENJAMINI_HOCHBERG = "benjamini_hochberg"
    BENJAMINI_YEKUTIELI = "benjamini_yekutieli"
    FALSE_DISCOVERY_RATE = "false_discovery_rate"
    PERMUTATION = "permutation"


class BayesianMethod(Enum):
    """Bayesian inference methods"""

    BAYES_FACTOR = "bayes_factor"
    POSTERIOR_PROBABILITY = "posterior_probability"
    CREDIBLE_INTERVAL = "credible_interval"
    ROPE_ANALYSIS = "rope_analysis"  # Region of Practical Equivalence


class TestDirection(Enum):
    """Direction of hypothesis testing"""

    TWO_TAILED = "two_tailed"
    LEFT_TAILED = "left_tailed"
    RIGHT_TAILED = "right_tailed"


@dataclass
class TestResult:
    """Result of a statistical test"""

    test_name: str
    statistic: float
    p_value: float
    degrees_of_freedom: int | None
    confidence_interval: tuple[float, float] | None
    effect_size: float | None
    test_direction: TestDirection
    assumptions: dict[str, bool]
    notes: str | None


@dataclass
class CorrectedResult:
    """Result after multiple comparison correction"""

    original_result: TestResult
    corrected_p_value: float
    correction_method: MultipleComparisonCorrection
    is_significant: bool
    correction_factor: float


@dataclass
class BayesianResult:
    """Bayesian analysis result"""

    method: BayesianMethod
    bayes_factor: float | None = None
    posterior_probability: float | None = None
    credible_interval: tuple[float, float] | None = None
    rope_probability: float | None = None
    interpretation: str
    strength_of_evidence: str


@dataclass
class PowerAnalysis:
    """Statistical power analysis results"""

    observed_power: float
    required_sample_size: int | None
    minimum_detectable_effect: float
    alpha: float
    effect_size: float
    power_recommendation: str


@dataclass
class SignificanceTestSuite:
    """Complete significance testing suite"""

    primary_tests: list[TestResult]
    corrected_results: list[CorrectedResult]
    bayesian_results: list[BayesianResult]
    power_analysis: PowerAnalysis
    overall_significance: bool
    recommendations: list[str]
    limitations: list[str]


class StatisticalSignificanceTester:
    """Advanced statistical significance testing framework"""

    def __init__(self, db_session, alpha: float = 0.05, power: float = 0.8):
        self.db = db_session
        self.alpha = alpha
        self.power = power
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def comprehensive_significance_test(
        self,
        intervention_id: str,
        pre_values: list[float],
        post_values: list[float],
        test_direction: TestDirection = TestDirection.TWO_TAILED,
        correction_methods: list[MultipleComparisonCorrection] | None = None,
        bayesian_methods: list[BayesianMethod] | None = None,
    ) -> SignificanceTestSuite:
        """Perform comprehensive significance testing"""

        if not correction_methods:
            correction_methods = [
                MultipleComparisonCorrection.BONFERRONI,
                MultipleComparisonCorrection.BENJAMINI_HOCHBERG,
            ]

        if not bayesian_methods:
            bayesian_methods = [BayesianMethod.BAYES_FACTOR]

        # Primary statistical tests
        primary_tests = await self._perform_primary_tests(pre_values, post_values, test_direction)

        # Multiple comparison corrections
        corrected_results = []
        for correction_method in correction_methods:
            corrected = await self._apply_multiple_comparison_correction(
                primary_tests, correction_method
            )
            corrected_results.extend(corrected)

        # Bayesian analysis
        bayesian_results = []
        for method in bayesian_methods:
            bayesian = await self._perform_bayesian_analysis(pre_values, post_values, method)
            if bayesian:
                bayesian_results.append(bayesian)

        # Power analysis
        power_analysis = await self._perform_comprehensive_power_analysis(
            pre_values, post_values, primary_tests
        )

        # Overall significance assessment
        overall_significance = self._assess_overall_significance(
            corrected_results, bayesian_results
        )

        # Generate recommendations
        recommendations = self._generate_evidence_recommendations(
            primary_tests, corrected_results, bayesian_results, power_analysis
        )

        # Identify limitations
        limitations = self._identify_statistical_limitations(
            primary_tests, corrected_results, power_analysis
        )

        return SignificanceTestSuite(
            primary_tests=primary_tests,
            corrected_results=corrected_results,
            bayesian_results=bayesian_results,
            power_analysis=power_analysis,
            overall_significance=overall_significance,
            recommendations=recommendations,
            limitations=limitations,
        )

    async def _perform_primary_tests(
        self, pre_values: list[float], post_values: list[float], test_direction: TestDirection
    ) -> list[TestResult]:
        """Perform primary statistical tests"""

        results = []

        try:
            # Paired samples t-test
            t_stat, t_p_value = stats.ttest_rel(pre_values, post_values)

            # Adjust for one-tailed test if needed
            if test_direction == TestDirection.RIGHT_TAILED:
                t_p_value = t_p_value / 2 if t_stat > 0 else 1 - t_p_value / 2
            elif test_direction == TestDirection.LEFT_TAILED:
                t_p_value = t_p_value / 2 if t_stat < 0 else 1 - t_p_value / 2

            # Calculate confidence interval
            diff = np.array(post_values) - np.array(pre_values)
            mean_diff = np.mean(diff)
            sem_diff = stats.sem(diff)
            df = len(pre_values) - 1

            ci_lower, ci_upper = t.interval(0.95, df, loc=mean_diff, scale=sem_diff)

            # Effect size (Cohen's d)
            pooled_sd = np.sqrt((np.var(pre_values, ddof=1) + np.var(post_values, ddof=1)) / 2)
            cohens_d = mean_diff / pooled_sd if pooled_sd > 0 else 0

            t_test_result = TestResult(
                test_name="Paired t-test",
                statistic=float(t_stat),
                p_value=float(t_p_value),
                degrees_of_freedom=df,
                confidence_interval=(float(ci_lower), float(ci_upper)),
                effect_size=float(cohens_d),
                test_direction=test_direction,
                assumptions=self._check_t_test_assumptions(pre_values, post_values),
                notes="Parametric test assuming normal distribution of differences",
            )
            results.append(t_test_result)

        except Exception as e:
            self.logger.warning(f"Paired t-test failed: {e}")

        try:
            # Wilcoxon signed-rank test
            wilcoxon_stat, wilcoxon_p_value = stats.wilcoxon(
                pre_values, post_values, zero_method="wilcox"
            )

            # Adjust for one-tailed test
            if test_direction != TestDirection.TWO_TAILED:
                # Approximation for one-tailed Wilcoxon
                if test_direction == TestDirection.RIGHT_TAILED:
                    wilcoxon_p_value = wilcoxon_p_value / 2
                else:
                    wilcoxon_p_value = wilcoxon_p_value / 2

            wilcoxon_result = TestResult(
                test_name="Wilcoxon Signed-Rank Test",
                statistic=float(wilcoxon_stat),
                p_value=float(wilcoxon_p_value),
                degrees_of_freedom=None,
                confidence_interval=None,
                effect_size=None,
                test_direction=test_direction,
                assumptions=self._check_wilcoxon_assumptions(pre_values, post_values),
                notes="Non-parametric test for paired data",
            )
            results.append(wilcoxon_result)

        except Exception as e:
            self.logger.warning(f"Wilcoxon test failed: {e}")

        try:
            # Sign test (most conservative)
            signs = np.sign(np.array(post_values) - np.array(pre_values))
            positive_signs = np.sum(signs > 0)
            total_signs = len(signs[signs != 0])

            if total_signs > 0:
                if test_direction == TestDirection.TWO_TAILED:
                    sign_p_value = stats.binom_test(
                        positive_signs, total_signs, p=0.5, alternative="two-sided"
                    )
                elif test_direction == TestDirection.RIGHT_TAILED:
                    sign_p_value = stats.binom_test(
                        positive_signs, total_signs, p=0.5, alternative="greater"
                    )
                else:
                    sign_p_value = stats.binom_test(
                        positive_signs, total_signs, p=0.5, alternative="less"
                    )

                sign_test_result = TestResult(
                    test_name="Sign Test",
                    statistic=float(positive_signs),
                    p_value=float(sign_p_value),
                    degrees_of_freedom=None,
                    confidence_interval=None,
                    effect_size=None,
                    test_direction=test_direction,
                    assumptions={"independent_observations": True},
                    notes="Most conservative non-parametric test",
                )
                results.append(sign_test_result)

        except Exception as e:
            self.logger.warning(f"Sign test failed: {e}")

        try:
            # Bootstrap confidence interval for mean difference
            bootstrap_ci = await self._bootstrap_confidence_interval(
                pre_values, post_values, n_bootstrap=10000
            )

            bootstrap_result = TestResult(
                test_name="Bootstrap Analysis",
                statistic=np.mean(np.array(post_values) - np.array(pre_values)),
                p_value=None,  # Bootstrap typically provides CI, not p-value
                degrees_of_freedom=None,
                confidence_interval=bootstrap_ci,
                effect_size=None,
                test_direction=test_direction,
                assumptions={"resampling_valid": True},
                notes="Non-parametric bootstrap analysis",
            )
            results.append(bootstrap_result)

        except Exception as e:
            self.logger.warning(f"Bootstrap analysis failed: {e}")

        return results

    async def _apply_multiple_comparison_correction(
        self, test_results: list[TestResult], correction_method: MultipleComparisonCorrection
    ) -> list[CorrectedResult]:
        """Apply multiple comparison corrections to p-values"""

        corrected_results = []

        if not test_results:
            return corrected_results

        p_values = [test.p_value for test in test_results if test.p_value is not None]

        if not p_values:
            return corrected_results

        try:
            if correction_method == MultipleComparisonCorrection.BONFERRONI:
                corrected_p_values = [min(p * len(p_values), 1.0) for p in p_values]
                correction_factor = len(p_values)

            elif correction_method == MultipleComparisonCorrection.HOLM_BONFERRONI:
                # Holm-Bonferroni step-down procedure
                indexed_p_values = list(enumerate(p_values))
                indexed_p_values.sort(key=lambda x: x[1])

                corrected_p_values = [p for _, p in indexed_p_values]
                n = len(p_values)

                for i, (idx, p) in enumerate(indexed_p_values):
                    corrected_p_values[i] = min(p * (n - i), 1.0)

                # Restore original order
                corrected_p_values = [0] * len(p_values)
                for i, (idx, _) in enumerate(indexed_p_values):
                    corrected_p_values[idx] = corrected_p_values[i]

                correction_factor = "Holm step-down"

            elif correction_method == MultipleComparisonCorrection.BENJAMINI_HOCHBERG:
                # Benjamini-Hochberg FDR procedure
                indexed_p_values = list(enumerate(p_values))
                indexed_p_values.sort(key=lambda x: x[1])

                corrected_p_values = []
                n = len(p_values)

                for i, (idx, p) in enumerate(indexed_p_values):
                    bh_p = p * n / (i + 1)
                    corrected_p_values.append(min(bh_p, 1.0))

                # Ensure monotonicity
                for i in range(len(corrected_p_values) - 2, -1, -1):
                    corrected_p_values[i] = min(corrected_p_values[i], corrected_p_values[i + 1])

                # Restore original order
                final_corrected = [0] * len(p_values)
                for i, (idx, _) in enumerate(indexed_p_values):
                    final_corrected[idx] = corrected_p_values[i]

                corrected_p_values = final_corrected
                correction_factor = "FDR procedure"

            elif correction_method == MultipleComparisonCorrection.BENJAMINI_YEKUTIELI:
                # Benjamini-Yekutieli procedure (more conservative)
                indexed_p_values = list(enumerate(p_values))
                indexed_p_values.sort(key=lambda x: x[1])

                n = len(p_values)
                harmonic_sum = sum(1 / (i + 1) for i in range(n))

                corrected_p_values = []
                for i, (idx, p) in enumerate(indexed_p_values):
                    by_p = p * n * harmonic_sum / (i + 1)
                    corrected_p_values.append(min(by_p, 1.0))

                # Ensure monotonicity
                for i in range(len(corrected_p_values) - 2, -1, -1):
                    corrected_p_values[i] = min(corrected_p_values[i], corrected_p_values[i + 1])

                # Restore original order
                final_corrected = [0] * len(p_values)
                for i, (idx, _) in enumerate(indexed_p_values):
                    final_corrected[idx] = corrected_p_values[i]

                corrected_p_values = final_corrected
                correction_factor = "BY procedure"

            else:
                corrected_p_values = p_values
                correction_factor = 1.0

            # Create corrected results
            test_index = 0
            for test in test_results:
                if test.p_value is not None and test_index < len(corrected_p_values):
                    corrected = CorrectedResult(
                        original_result=test,
                        corrected_p_value=corrected_p_values[test_index],
                        correction_method=correction_method,
                        is_significant=corrected_p_values[test_index] < self.alpha,
                        correction_factor=correction_factor,
                    )
                    corrected_results.append(corrected)
                    test_index += 1

        except Exception as e:
            self.logger.warning(f"Multiple comparison correction failed: {e}")

        return corrected_results

    async def _perform_bayesian_analysis(
        self, pre_values: list[float], post_values: list[float], method: BayesianMethod
    ) -> BayesianResult | None:
        """Perform Bayesian analysis of intervention effects"""

        try:
            if method == BayesianMethod.BAYES_FACTOR:
                bayes_factor = await self._calculate_bayes_factor(pre_values, post_values)
                interpretation = self._interpret_bayes_factor(bayes_factor)
                strength = self._classify_bayes_evidence(bayes_factor)

                return BayesianResult(
                    method=method,
                    bayes_factor=bayes_factor,
                    interpretation=interpretation,
                    strength_of_evidence=strength,
                )

            if method == BayesianMethod.POSTERIOR_PROBABILITY:
                post_prob = await self._calculate_posterior_probability(pre_values, post_values)
                interpretation = f"Posterior probability of effect: {post_prob:.3f}"
                strength = (
                    "Strong" if post_prob > 0.95 else "Moderate" if post_prob > 0.8 else "Weak"
                )

                return BayesianResult(
                    method=method,
                    posterior_probability=post_prob,
                    interpretation=interpretation,
                    strength_of_evidence=strength,
                )

            if method == BayesianMethod.CREDIBLE_INTERVAL:
                ci = await self._calculate_credible_interval(pre_values, post_values)
                interpretation = f"95% credible interval: ({ci[0]:.3f}, {ci[1]:.3f})"
                strength = "Strong" if 0 not in ci else "Weak"

                return BayesianResult(
                    method=method,
                    credible_interval=ci,
                    interpretation=interpretation,
                    strength_of_evidence=strength,
                )

            if method == BayesianMethod.ROPE_ANALYSIS:
                rope_prob = await self._calculate_rope_probability(pre_values, post_values)
                interpretation = f"Probability of negligible effect: {rope_prob:.3f}"
                strength = (
                    "Strong" if rope_prob > 0.95 else "Moderate" if rope_prob > 0.8 else "Weak"
                )

                return BayesianResult(
                    method=method,
                    rope_probability=rope_prob,
                    interpretation=interpretation,
                    strength_of_evidence=strength,
                )

        except Exception as e:
            self.logger.warning(f"Bayesian analysis failed for {method}: {e}")

        return None

    async def _calculate_bayes_factor(
        self, pre_values: list[float], post_values: list[float]
    ) -> float:
        """Calculate Bayes factor for paired t-test using BIC approximation"""

        n = len(pre_values)
        diff = np.array(post_values) - np.array(pre_values)
        mean_diff = np.mean(diff)
        std_diff = np.std(diff, ddof=1)

        # BIC approximation for Bayes factor
        # BF10 = exp((BIC_null - BIC_alternative) / 2)

        # Null model (no effect)
        bic_null = n * np.log(2 * np.pi * std_diff**2) + n

        # Alternative model (with effect)
        residual_sum_squares = np.sum((diff - mean_diff) ** 2)
        bic_alternative = n * np.log(residual_sum_squares / n) + n + np.log(n)

        bayes_factor = math.exp((bic_null - bic_alternative) / 2)

        return bayes_factor

    async def _calculate_posterior_probability(
        self, pre_values: list[float], post_values: list[float]
    ) -> float:
        """Calculate posterior probability of effect using conjugate priors"""

        diff = np.array(post_values) - np.array(pre_values)
        n = len(diff)

        # Using normal conjugate prior with non-informative prior
        sample_mean = np.mean(diff)
        sample_std = np.std(diff, ddof=1)

        # Posterior distribution parameters (assuming non-informative prior)
        posterior_mean = sample_mean
        posterior_std = sample_std / math.sqrt(n)

        # Probability that effect > 0
        if posterior_std > 0:
            prob_positive = 1 - norm.cdf(0, loc=posterior_mean, scale=posterior_std)
        else:
            prob_positive = 0.5 if posterior_mean == 0 else (1.0 if posterior_mean > 0 else 0.0)

        return prob_positive

    async def _calculate_credible_interval(
        self, pre_values: list[float], post_values: list[float]
    ) -> tuple[float, float]:
        """Calculate 95% credible interval for effect size"""

        diff = np.array(post_values) - np.array(pre_values)
        n = len(diff)

        sample_mean = np.mean(diff)
        sample_std = np.std(diff, ddof=1)

        # Using t-distribution for credible interval (conjugate prior approach)
        df = n - 1
        margin = t.ppf(0.975, df) * (sample_std / math.sqrt(n))

        ci_lower = sample_mean - margin
        ci_upper = sample_mean + margin

        return (float(ci_lower), float(ci_upper))

    async def _calculate_rope_probability(
        self,
        pre_values: list[float],
        post_values: list[float],
        rope_range: tuple[float, float] = (-0.1, 0.1),
    ) -> float:
        """Calculate probability that effect falls in Region of Practical Equivalence"""

        diff = np.array(post_values) - np.array(pre_values)
        n = len(diff)

        sample_mean = np.mean(diff)
        sample_std = np.std(diff, ddof=1)

        # Using posterior distribution (normal approximation)
        df = n - 1
        posterior_std = sample_std / math.sqrt(n)

        # Probability of being within ROPE
        if posterior_std > 0:
            prob_lower = norm.cdf(rope_range[0], loc=sample_mean, scale=posterior_std)
            prob_upper = norm.cdf(rope_range[1], loc=sample_mean, scale=posterior_std)
            rope_prob = prob_upper - prob_lower
        else:
            rope_prob = 1.0 if rope_range[0] <= sample_mean <= rope_range[1] else 0.0

        return rope_prob

    async def _bootstrap_confidence_interval(
        self,
        pre_values: list[float],
        post_values: list[float],
        n_bootstrap: int = 10000,
        confidence_level: float = 0.95,
    ) -> tuple[float, float]:
        """Calculate bootstrap confidence interval for mean difference"""

        n = len(pre_values)
        bootstrap_means = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            indices = np.secrets.choice(n, n, replace=True)
            bootstrap_pre = [pre_values[i] for i in indices]
            bootstrap_post = [post_values[i] for i in indices]

            bootstrap_diff = np.array(bootstrap_post) - np.array(bootstrap_pre)
            bootstrap_means.append(np.mean(bootstrap_diff))

        # Calculate percentile-based confidence interval
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        ci_lower = np.percentile(bootstrap_means, lower_percentile)
        ci_upper = np.percentile(bootstrap_means, upper_percentile)

        return (float(ci_lower), float(ci_upper))

    async def _perform_comprehensive_power_analysis(
        self, pre_values: list[float], post_values: list[float], test_results: list[TestResult]
    ) -> PowerAnalysis:
        """Perform comprehensive power analysis"""

        n = len(pre_values)
        diff = np.array(post_values) - np.array(pre_values)
        mean_diff = np.mean(diff)
        pooled_sd = np.sqrt((np.var(pre_values, ddof=1) + np.var(post_values, ddof=1)) / 2)

        # Observed effect size
        effect_size = mean_diff / pooled_sd if pooled_sd > 0 else 0

        # Calculate observed power using non-central t-distribution
        critical_t = t.ppf(1 - self.alpha / 2, n - 1)
        non_central_param = effect_size * math.sqrt(n / 2)

        try:
            # Power calculation using non-central t-distribution
            observed_power = (
                1
                - t.cdf(critical_t, n - 1, non_central_param)
                + t.cdf(-critical_t, n - 1, non_central_param)
            )
            observed_power = max(0, min(1, observed_power))
        except:
            observed_power = 0.5  # Conservative estimate

        # Required sample size for 80% power
        required_n = self._calculate_required_sample_size(effect_size, self.alpha, self.power)

        # Minimum detectable effect with current sample size
        min_detectable_effect = self._calculate_minimum_detectable_effect(n, self.alpha, self.power)

        # Power recommendation
        if observed_power >= 0.8:
            power_recommendation = "Adequate power - study well-powered to detect effects"
        elif observed_power >= 0.6:
            power_recommendation = "Moderate power - consider larger sample for replication"
        elif observed_power >= 0.4:
            power_recommendation = "Low power - results should be interpreted with caution"
        else:
            power_recommendation = "Very low power - study severely underpowered"

        return PowerAnalysis(
            observed_power=observed_power,
            required_sample_size=required_n,
            minimum_detectable_effect=min_detectable_effect,
            alpha=self.alpha,
            effect_size=effect_size,
            power_recommendation=power_recommendation,
        )

    def _calculate_required_sample_size(
        self, effect_size: float, alpha: float, power: float
    ) -> int:
        """Calculate required sample size for given effect size and desired power"""

        if abs(effect_size) < 0.01:
            return None  # Effect size too small

        # Approximation using central limit theorem
        # In practice, use power analysis software or more precise calculations
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)

        required_n = 2 * ((z_alpha + z_beta) / effect_size) ** 2

        return math.ceil(required_n)

    def _calculate_minimum_detectable_effect(self, n: int, alpha: float, power: float) -> float:
        """Calculate minimum detectable effect size for given sample size"""

        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power)

        if n > 0:
            min_effect = (z_alpha + z_beta) * math.sqrt(2 / n)
        else:
            min_effect = float("inf")

        return min_effect

    def _interpret_bayes_factor(self, bayes_factor: float) -> str:
        """Interpret Bayes factor according to Jeffreys' scale"""

        if bayes_factor > 100:
            return "Extreme evidence for effect"
        if bayes_factor > 30:
            return "Very strong evidence for effect"
        if bayes_factor > 10:
            return "Strong evidence for effect"
        if bayes_factor > 3:
            return "Moderate evidence for effect"
        if bayes_factor > 1:
            return "Weak evidence for effect"
        if bayes_factor > 0.33:
            return "Weak evidence against effect"
        if bayes_factor > 0.1:
            return "Moderate evidence against effect"
        if bayes_factor > 0.03:
            return "Strong evidence against effect"
        if bayes_factor > 0.01:
            return "Very strong evidence against effect"
        return "Extreme evidence against effect"

    def _classify_bayes_evidence(self, bayes_factor: float) -> str:
        """Classify strength of Bayesian evidence"""

        if bayes_factor > 10 or bayes_factor < 0.1:
            return "Strong"
        if bayes_factor > 3 or bayes_factor < 0.33:
            return "Moderate"
        return "Weak"

    def _check_t_test_assumptions(
        self, pre_values: list[float], post_values: list[float]
    ) -> dict[str, bool]:
        """Check assumptions for paired t-test"""

        assumptions = {
            "normality_of_differences": False,
            "continuous_data": True,
            "independent_observations": True,
        }

        try:
            # Test normality of differences using Shapiro-Wilk
            diff = np.array(post_values) - np.array(pre_values)
            shapiro_stat, shapiro_p = stats.shapiro(diff)
            assumptions["normality_of_differences"] = shapiro_p > 0.05
        except Exception:
            pass

        return assumptions

    def _check_wilcoxon_assumptions(
        self, pre_values: list[float], post_values: list[float]
    ) -> dict[str, bool]:
        """Check assumptions for Wilcoxon signed-rank test"""

        return {
            "continuous_data": True,
            "symmetric_distribution": True,  # Assumed for interpretation
            "independent_observations": True,
        }

    def _assess_overall_significance(
        self, corrected_results: list[CorrectedResult], bayesian_results: list[BayesianResult]
    ) -> bool:
        """Assess overall statistical significance across all methods"""

        # Check corrected frequentist results
        significant_corrected = [result for result in corrected_results if result.is_significant]

        # Check Bayesian results
        strong_bayesian = [
            result
            for result in bayesian_results
            if result.strength_of_evidence in ["Strong", "Very strong", "Extreme"]
        ]

        # Overall significance if at least one method shows strong evidence
        return len(significant_corrected) > 0 or len(strong_bayesian) > 0

    def _generate_evidence_recommendations(
        self,
        primary_tests: list[TestResult],
        corrected_results: list[CorrectedResult],
        bayesian_results: list[BayesianResult],
        power_analysis: PowerAnalysis,
    ) -> list[str]:
        """Generate evidence-based recommendations"""

        recommendations = []

        # Frequentist evidence
        significant_corrected = [result for result in corrected_results if result.is_significant]

        if significant_corrected:
            recommendations.append(
                "Statistical significance maintained after multiple comparison corrections"
            )
        else:
            recommendations.append(
                "No statistically significant effects after correction for multiple testing"
            )

        # Bayesian evidence
        if bayesian_results:
            strong_bayesian = [
                result
                for result in bayesian_results
                if result.strength_of_evidence in ["Strong", "Very strong"]
            ]

            if strong_bayesian:
                recommendations.append(
                    "Bayesian analysis provides strong evidence for intervention effectiveness"
                )
            else:
                recommendations.append("Bayesian analysis suggests weak or inconclusive evidence")

        # Power considerations
        if power_analysis.observed_power >= 0.8:
            recommendations.append("Study adequately powered - results reliable")
        elif power_analysis.observed_power >= 0.6:
            recommendations.append(
                "Moderate statistical power - consider replication with larger sample"
            )
        else:
            recommendations.append("Low statistical power - interpret results with caution")

        # Consistency across methods
        significant_tests = [test for test in primary_tests if test.p_value and test.p_value < 0.05]

        if len(significant_tests) >= len(primary_tests) / 2:
            recommendations.append("Consistent evidence across multiple statistical tests")
        else:
            recommendations.append("Inconsistent results across different statistical methods")

        return recommendations

    def _identify_statistical_limitations(
        self,
        primary_tests: list[TestResult],
        corrected_results: list[CorrectedResult],
        power_analysis: PowerAnalysis,
    ) -> list[str]:
        """Identify statistical limitations of the analysis"""

        limitations = []

        # Sample size limitations
        if power_analysis.observed_power < 0.6:
            limitations.append("Low statistical power increases risk of Type II errors")

        # Assumption violations
        for test in primary_tests:
            if test.assumptions_met:
                violated_assumptions = [
                    assumption for assumption, met in test.assumptions_met.items() if not met
                ]
                if violated_assumptions:
                    limitations.append(
                        f"{test.test_name} assumptions violated: {', '.join(violated_assumptions)}"
                    )

        # Multiple testing concerns
        if len(primary_tests) > 3:
            limitations.append(
                "Multiple testing increases familywise error rate - correction methods applied"
            )

        # Study design limitations
        limitations.append(
            "Pre-post design without control group susceptible to confounding factors"
        )

        return limitations
