"""
Intervention Analysis Service

Provides comprehensive pre/post intervention analysis with statistical testing,
effect size calculations, and significance testing for organizational interventions.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
from scipy import stats
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.intervention_effectiveness import (
    Intervention,
    PostInterventionMeasurement,
    PreInterventionMeasurement,
)

logger = logging.getLogger(__name__)


class StatisticalTest(Enum):
    """Available statistical tests"""

    PAIRED_T_TEST = "paired_t_test"
    WILCOXON_SIGNED_RANK = "wilcoxon_signed_rank"
    SIGN_TEST = "sign_test"
    MCNEMAR_TEST = "mcnemar_test"
    REPEATED_MEASURES_ANOVA = "repeated_measures_anova"
    FRIEDMAN_TEST = "friedman_test"
    COCHRAN_Q = "cochran_q"


class EffectSizeMetric(Enum):
    """Effect size metrics"""

    COHENS_D = "cohens_d"
    GLASS_DELTA = "glass_delta"
    HEDGES_G = "hedges_g"
    CLIFFS_DELTA = "cliffs_delta"
    ETA_SQUARED = "eta_squared"
    OMEGA_SQUARED = "omega_squared"


class SignificanceLevel(Enum):
    """Statistical significance levels"""

    ALPHA_001 = 0.001
    ALPHA_01 = 0.01
    ALPHA_05 = 0.05
    ALPHA_10 = 0.10


@dataclass
class PrePostData:
    """Pre and post intervention measurements for analysis"""

    pre_values: list[float]
    post_values: list[float]
    participant_ids: list[str]
    metric_name: str
    measurement_dates: list[datetime]
    metadata: dict[str, Any]


@dataclass
class StatisticalTestResult:
    """Result of statistical test"""

    test_name: StatisticalTest
    statistic: float
    p_value: float
    degrees_of_freedom: int | None = None
    confidence_interval: tuple[float, float] | None = None
    effect_size: float | None = None
    interpretation: str | None = None
    assumptions_met: dict[str, bool] = None


@dataclass
class EffectSizeResult:
    """Effect size calculation result"""

    metric: EffectSizeMetric
    effect_size: float
    confidence_interval: tuple[float, float] | None = None
    interpretation: str
    magnitude: str  # trivial, small, medium, large, very_large


@dataclass
class InterventionAnalysisResult:
    """Complete intervention analysis result"""

    intervention_id: str
    metric_name: str
    pre_post_data: PrePostData
    statistical_tests: list[StatisticalTestResult]
    effect_sizes: list[EffectSizeResult]
    clinical_significance: str | None = None
    practical_significance: bool | None = None
    recommendations: list[str] = None
    limitations: list[str] = None
    sample_size: int = 0
    power_analysis: dict[str, Any] = None


class InterventionAnalyzer:
    """Advanced intervention effectiveness analyzer"""

    def __init__(self, db_session: Session, significance_level: float = 0.05):
        self.db = db_session
        self.significance_level = significance_level
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def analyze_intervention_effectiveness(
        self,
        intervention_id: str,
        metrics: list[str] | None = None,
        control_group_id: str | None = None,
        follow_up_days: int | None = None,
    ) -> list[InterventionAnalysisResult]:
        """Comprehensive analysis of intervention effectiveness"""

        self.logger.info(f"Analyzing intervention effectiveness for {intervention_id}")

        # Get intervention details
        intervention = (
            self.db.query(Intervention)
            .filter(Intervention.id == intervention_id)
            .first()
        )

        if not intervention:
            raise ValueError(f"Intervention {intervention_id} not found")

        # Get metrics to analyze
        if not metrics:
            metrics = await self._get_intervention_metrics(intervention_id)

        results = []

        for metric in metrics:
            try:
                result = await self._analyze_single_metric(
                    intervention_id, metric, control_group_id, follow_up_days
                )
                if result:
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to analyze metric {metric}: {e}")
                continue

        return results

    async def _analyze_single_metric(
        self,
        intervention_id: str,
        metric_name: str,
        control_group_id: str | None,
        follow_up_days: int | None,
    ) -> InterventionAnalysisResult | None:
        """Analyze a single metric for effectiveness"""

        # Get pre/post measurements
        pre_post_data = await self._get_pre_post_measurements(
            intervention_id, metric_name, follow_up_days
        )

        if not pre_post_data or len(pre_post_data.pre_values) < 2:
            self.logger.warning(f"Insufficient data for metric {metric_name}")
            return None

        # Perform statistical tests
        statistical_tests = await self._perform_statistical_tests(pre_post_data)

        # Calculate effect sizes
        effect_sizes = await self._calculate_effect_sizes(pre_post_data)

        # Determine clinical and practical significance
        clinical_significance = self._determine_clinical_significance(effect_sizes)
        practical_significance = self._determine_practical_significance(
            pre_post_data, effect_sizes
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            pre_post_data, statistical_tests, effect_sizes
        )

        # Identify limitations
        limitations = self._identify_limitations(pre_post_data, statistical_tests)

        # Power analysis
        power_analysis = self._perform_power_analysis(pre_post_data, statistical_tests)

        return InterventionAnalysisResult(
            intervention_id=intervention_id,
            metric_name=metric_name,
            pre_post_data=pre_post_data,
            statistical_tests=statistical_tests,
            effect_sizes=effect_sizes,
            clinical_significance=clinical_significance,
            practical_significance=practical_significance,
            recommendations=recommendations,
            limitations=limitations,
            sample_size=len(pre_post_data.pre_values),
            power_analysis=power_analysis,
        )

    async def _get_intervention_metrics(self, intervention_id: str) -> list[str]:
        """Get all metrics measured for an intervention"""

        # Get unique metrics from pre measurements
        pre_metrics = (
            self.db.query(PreInterventionMeasurement.metric_name)
            .filter(PreInterventionMeasurement.intervention_id == intervention_id)
            .distinct()
            .all()
        )

        # Get unique metrics from post measurements
        post_metrics = (
            self.db.query(PostInterventionMeasurement.metric_name)
            .filter(PostInterventionMeasurement.intervention_id == intervention_id)
            .distinct()
            .all()
        )

        # Combine and return unique metrics
        all_metrics = set([m[0] for m in pre_metrics] + [m[0] for m in post_metrics])
        return list(all_metrics)

    async def _get_pre_post_measurements(
        self, intervention_id: str, metric_name: str, follow_up_days: int | None
    ) -> PrePostData | None:
        """Get paired pre and post measurements for analysis"""

        # Get participants with both pre and post measurements
        participants_with_both = (
            self.db.query(
                PreInterventionMeasurement.user_id,
                func.avg(PreInterventionMeasurement.metric_value).label("pre_value"),
                func.min(PreInterventionMeasurement.measurement_date).label("pre_date"),
            )
            .filter(
                PreInterventionMeasurement.intervention_id == intervention_id,
                PreInterventionMeasurement.metric_name == metric_name,
            )
            .group_by(PreInterventionMeasurement.user_id)
            .subquery()
        )

        post_query = self.db.query(
            PostInterventionMeasurement.user_id,
            func.avg(PostInterventionMeasurement.metric_value).label("post_value"),
            func.min(PostInterventionMeasurement.measurement_date).label("post_date"),
        ).filter(
            PostInterventionMeasurement.intervention_id == intervention_id,
            PostInterventionMeasurement.metric_name == metric_name,
        )

        if follow_up_days:
            intervention = (
                self.db.query(Intervention)
                .filter(Intervention.id == intervention_id)
                .first()
            )
            if intervention and intervention.end_date:
                cutoff_date = intervention.end_date + timedelta(days=follow_up_days)
                post_query = post_query.filter(
                    PostInterventionMeasurement.measurement_date <= cutoff_date
                )

        post_measurements = post_query.group_by(
            PostInterventionMeasurement.user_id
        ).subquery()

        # Join pre and post measurements
        paired_data = (
            self.db.query(
                participants_with_both.c.user_id,
                participants_with_both.c.pre_value,
                participants_with_both.c.pre_date,
                post_measurements.c.post_value,
                post_measurements.c.post_date,
            )
            .join(
                post_measurements,
                participants_with_both.c.user_id == post_measurements.c.user_id,
            )
            .all()
        )

        if not paired_data:
            return None

        pre_values = [float(row.pre_value) for row in paired_data]
        post_values = [float(row.post_value) for row in paired_data]
        participant_ids = [str(row.user_id) for row in paired_data]
        measurement_dates = [row.pre_date for row in paired_data]

        # Get additional metadata
        metadata = {
            "intervention_id": intervention_id,
            "metric_name": metric_name,
            "follow_up_days": follow_up_days,
            "sample_size": len(paired_data),
            "data_collection_dates": {
                "earliest_pre": (
                    min(measurement_dates).isoformat() if measurement_dates else None
                ),
                "latest_post": (
                    max([row.post_date for row in paired_data]).isoformat()
                    if paired_data
                    else None
                ),
            },
        }

        return PrePostData(
            pre_values=pre_values,
            post_values=post_values,
            participant_ids=participant_ids,
            metric_name=metric_name,
            measurement_dates=measurement_dates,
            metadata=metadata,
        )

    async def _perform_statistical_tests(
        self, data: PrePostData
    ) -> list[StatisticalTestResult]:
        """Perform appropriate statistical tests based on data characteristics"""

        results = []

        try:
            # Paired t-test (parametric)
            t_stat, t_p_value = stats.ttest_rel(data.pre_values, data.post_values)

            # Calculate confidence interval for mean difference
            diff = np.array(data.post_values) - np.array(data.pre_values)
            mean_diff = np.mean(diff)
            sem_diff = stats.sem(diff)
            ci_lower, ci_upper = stats.t.interval(
                0.95, len(diff) - 1, loc=mean_diff, scale=sem_diff
            )

            t_result = StatisticalTestResult(
                test_name=StatisticalTest.PAIRED_T_TEST,
                statistic=float(t_stat),
                p_value=float(t_p_value),
                degrees_of_freedom=len(data.pre_values) - 1,
                confidence_interval=(float(ci_lower), float(ci_upper)),
                interpretation=self._interpret_p_value(float(t_p_value)),
                assumptions_met=self._check_t_test_assumptions(data),
            )
            results.append(t_result)

        except Exception as e:
            self.logger.warning(f"Paired t-test failed: {e}")

        try:
            # Wilcoxon signed-rank test (non-parametric)
            wilcoxon_stat, wilcoxon_p_value = stats.wilcoxon(
                data.pre_values, data.post_values, zero_method="wilcox"
            )

            wilcoxon_result = StatisticalTestResult(
                test_name=StatisticalTest.WILCOXON_SIGNED_RANK,
                statistic=float(wilcoxon_stat),
                p_value=float(wilcoxon_p_value),
                interpretation=self._interpret_p_value(float(wilcoxon_p_value)),
                assumptions_met=self._check_wilcoxon_assumptions(data),
            )
            results.append(wilcoxon_result)

        except Exception as e:
            self.logger.warning(f"Wilcoxon test failed: {e}")

        # Sign test (very conservative non-parametric)
        try:
            signs = np.sign(np.array(data.post_values) - np.array(data.pre_values))
            positive_signs = np.sum(signs > 0)
            total_signs = len(signs[signs != 0])

            if total_signs > 0:
                # Binomial test
                sign_p_value = stats.binom_test(positive_signs, total_signs, p=0.5)

                sign_result = StatisticalTestResult(
                    test_name=StatisticalTest.SIGN_TEST,
                    statistic=float(positive_signs),
                    p_value=float(sign_p_value),
                    interpretation=self._interpret_p_value(float(sign_p_value)),
                    assumptions_met={"independent_observations": True},
                )
                results.append(sign_result)

        except Exception as e:
            self.logger.warning(f"Sign test failed: {e}")

        return results

    async def _calculate_effect_sizes(
        self, data: PrePostData
    ) -> list[EffectSizeResult]:
        """Calculate various effect size metrics"""

        results = []

        try:
            # Cohen's d
            diff = np.array(data.post_values) - np.array(data.pre_values)
            mean_diff = np.mean(diff)
            pre_std = np.std(data.pre_values, ddof=1)

            if pre_std > 0:
                cohens_d = mean_diff / pre_std
                hedges_g = self._hedges_g_correction(cohens_d, len(data.pre_values))

                # Confidence interval for Cohen's d
                se_d = math.sqrt(
                    (len(data.pre_values) / len(data.post_values))
                    + (cohens_d**2 / (2 * len(data.pre_values)))
                )
                ci_lower = cohens_d - 1.96 * se_d
                ci_upper = cohens_d + 1.96 * se_d

                results.append(
                    EffectSizeResult(
                        metric=EffectSizeMetric.COHENS_D,
                        effect_size=cohens_d,
                        confidence_interval=(ci_lower, ci_upper),
                        interpretation=self._interpret_effect_size(cohens_d),
                        magnitude=self._categorize_effect_magnitude(cohens_d),
                    )
                )

                results.append(
                    EffectSizeResult(
                        metric=EffectSizeMetric.HEDGES_G,
                        effect_size=hedges_g,
                        interpretation=self._interpret_effect_size(hedges_g),
                        magnitude=self._categorize_effect_magnitude(hedges_g),
                    )
                )

        except Exception as e:
            self.logger.warning(f"Effect size calculation failed: {e}")

        try:
            # Glass's Delta (using pre-intervention SD)
            diff = np.array(data.post_values) - np.array(data.pre_values)
            mean_diff = np.mean(diff)
            pre_std = np.std(data.pre_values, ddof=1)

            if pre_std > 0:
                glass_delta = mean_diff / pre_std

                results.append(
                    EffectSizeResult(
                        metric=EffectSizeMetric.GLASS_DELTA,
                        effect_size=glass_delta,
                        interpretation=self._interpret_effect_size(glass_delta),
                        magnitude=self._categorize_effect_magnitude(glass_delta),
                    )
                )

        except Exception as e:
            self.logger.warning(f"Glass's Delta calculation failed: {e}")

        try:
            # Cliff's Delta (non-parametric effect size)
            cliffs_delta = self._calculate_cliffs_delta(
                data.pre_values, data.post_values
            )

            results.append(
                EffectSizeResult(
                    metric=EffectSizeMetric.CLIFFS_DELTA,
                    effect_size=cliffs_delta,
                    interpretation=self._interpret_cliffs_delta(cliffs_delta),
                    magnitude=self._categorize_cliffs_delta(cliffs_delta),
                )
            )

        except Exception as e:
            self.logger.warning(f"Cliff's Delta calculation failed: {e}")

        return results

    def _hedges_g_correction(self, cohens_d: float, n: int) -> float:
        """Apply Hedges' g correction for small sample bias"""
        correction_factor = 1 - (3 / (4 * (2 * n) - 1))
        return cohens_d * correction_factor

    def _calculate_cliffs_delta(
        self, group1: list[float], group2: list[float]
    ) -> float:
        """Calculate Cliff's Delta for non-parametric effect size"""
        n1, n2 = len(group1), len(group2)
        dominance_count = 0

        for x in group1:
            for y in group2:
                if x > y:
                    dominance_count += 1
                elif x < y:
                    dominance_count -= 1

        return dominance_count / (n1 * n2)

    def _interpret_p_value(self, p_value: float) -> str:
        """Interpret statistical significance of p-value"""
        if p_value < 0.001:
            return "Highly significant (p < 0.001)"
        if p_value < 0.01:
            return "Very significant (p < 0.01)"
        if p_value < 0.05:
            return "Significant (p < 0.05)"
        if p_value < 0.10:
            return "Marginally significant (p < 0.10)"
        return "Not statistically significant"

    def _interpret_effect_size(self, effect_size: float) -> str:
        """Provide interpretation of effect size magnitude"""
        abs_effect = abs(effect_size)
        if abs_effect >= 0.8:
            return f"Large effect ({effect_size:.3f})"
        if abs_effect >= 0.5:
            return f"Medium effect ({effect_size:.3f})"
        if abs_effect >= 0.2:
            return f"Small effect ({effect_size:.3f})"
        return f"Trivial effect ({effect_size:.3f})"

    def _interpret_cliffs_delta(self, cliffs_delta: float) -> str:
        """Interpret Cliff's Delta effect size"""
        abs_delta = abs(cliffs_delta)
        if abs_delta >= 0.474:
            return f"Large effect ({cliffs_delta:.3f})"
        if abs_delta >= 0.33:
            return f"Medium effect ({cliffs_delta:.3f})"
        if abs_delta >= 0.147:
            return f"Small effect ({cliffs_delta:.3f})"
        return f"Negligible effect ({cliffs_delta:.3f})"

    def _categorize_effect_magnitude(self, effect_size: float) -> str:
        """Categorize effect size into magnitude categories"""
        abs_effect = abs(effect_size)
        if abs_effect >= 1.0:
            return "very_large"
        if abs_effect >= 0.8:
            return "large"
        if abs_effect >= 0.5:
            return "medium"
        if abs_effect >= 0.2:
            return "small"
        return "trivial"

    def _categorize_cliffs_delta(self, cliffs_delta: float) -> str:
        """Categorize Cliff's Delta magnitude"""
        abs_delta = abs(cliffs_delta)
        if abs_delta >= 0.474:
            return "large"
        if abs_delta >= 0.33:
            return "medium"
        if abs_delta >= 0.147:
            return "small"
        return "trivial"

    def _check_t_test_assumptions(self, data: PrePostData) -> dict[str, bool]:
        """Check assumptions for paired t-test"""
        assumptions = {
            "normality_of_differences": False,
            "continuous_data": True,
            "independent_observations": True,
        }

        try:
            # Test normality of differences using Shapiro-Wilk
            diff = np.array(data.post_values) - np.array(data.pre_values)
            shapiro_stat, shapiro_p = stats.shapiro(diff)
            assumptions["normality_of_differences"] = shapiro_p > 0.05
        except Exception:
            pass

        return assumptions

    def _check_wilcoxon_assumptions(self, data: PrePostData) -> dict[str, bool]:
        """Check assumptions for Wilcoxon signed-rank test"""
        return {
            "continuous_data": True,
            "symmetric_distribution": True,  # Assumed for interpretation
            "independent_observations": True,
        }

    def _determine_clinical_significance(
        self, effect_sizes: list[EffectSizeResult]
    ) -> str | None:
        """Determine clinical significance based on effect sizes"""
        if not effect_sizes:
            return None

        # Use Cohen's d or Hedges' g if available
        for es in effect_sizes:
            if es.metric in [EffectSizeMetric.COHENS_D, EffectSizeMetric.HEDGES_G]:
                abs_effect = abs(es.effect_size)
                if abs_effect >= 0.8:
                    return "very_large"
                if abs_effect >= 0.5:
                    return "large"
                if abs_effect >= 0.2:
                    return "medium"
                return "small"

        return None

    def _determine_practical_significance(
        self, data: PrePostData, effect_sizes: list[EffectSizeResult]
    ) -> bool | None:
        """Determine practical significance based on context and effect sizes"""
        if not effect_sizes:
            return None

        # Consider both effect size and percentage change
        pre_mean = np.mean(data.pre_values)
        post_mean = np.mean(data.post_values)

        if pre_mean != 0:
            percent_change = ((post_mean - pre_mean) / abs(pre_mean)) * 100
        else:
            percent_change = 0

        # Practical significance if effect size >= 0.2 AND percent change >= 10%
        significant_effect_sizes = [
            es
            for es in effect_sizes
            if es.metric in [EffectSizeMetric.COHENS_D, EffectSizeMetric.HEDGES_G]
            and abs(es.effect_size) >= 0.2
        ]

        return len(significant_effect_sizes) > 0 and abs(percent_change) >= 10

    def _generate_recommendations(
        self,
        data: PrePostData,
        statistical_tests: list[StatisticalTestResult],
        effect_sizes: list[EffectSizeResult],
    ) -> list[str]:
        """Generate evidence-based recommendations"""
        recommendations = []

        # Check for statistical significance
        significant_tests = [
            test for test in statistical_tests if test.p_value < self.significance_level
        ]

        if significant_tests:
            if len(significant_tests) >= 2:  # Multiple significant tests
                recommendations.append(
                    "Strong evidence of intervention effectiveness - consider scaling"
                )
            else:
                recommendations.append(
                    "Moderate evidence of effectiveness - consider replication with larger sample"
                )
        else:
            recommendations.append(
                "No statistically significant effects detected - reconsider intervention approach"
            )

        # Check effect sizes
        large_effects = [
            es for es in effect_sizes if es.magnitude in ["large", "very_large"]
        ]

        if large_effects:
            recommendations.append(
                "Large practical effects observed - high potential for organizational impact"
            )
        elif effect_sizes:
            medium_effects = [es for es in effect_sizes if es.magnitude == "medium"]
            if medium_effects:
                recommendations.append(
                    "Medium effects observed - valuable but may need optimization"
                )

        # Sample size considerations
        if len(data.pre_values) < 20:
            recommendations.append(
                "Small sample size - interpret results with caution, consider larger scale implementation"
            )
        elif len(data.pre_values) < 50:
            recommendations.append(
                "Moderate sample size - results promising but would benefit from larger scale validation"
            )

        return recommendations[:5]  # Top 5 recommendations

    def _identify_limitations(
        self, data: PrePostData, statistical_tests: list[StatisticalTestResult]
    ) -> list[str]:
        """Identify study limitations"""
        limitations = []

        # Sample size limitations
        if len(data.pre_values) < 20:
            limitations.append(
                "Small sample size limits statistical power and generalizability"
            )

        # Test assumption violations
        for test in statistical_tests:
            if test.assumptions_met:
                violated_assumptions = [
                    assumption
                    for assumption, met in test.assumptions_met.items()
                    if not met
                ]
                if violated_assumptions:
                    limitations.append(
                        f"{test.test_name.value} assumptions violated: {', '.join(violated_assumptions)}"
                    )

        # Study design limitations
        limitations.append(
            "Pre-post design without control group - results may be influenced by confounding factors"
        )

        # Measurement limitations
        if len(set(data.measurement_dates)) == 1:
            limitations.append(
                "All measurements taken on same date - may limit temporal generalizability"
            )

        return limitations

    def _perform_power_analysis(
        self, data: PrePostData, statistical_tests: list[StatisticalTestResult]
    ) -> dict[str, Any]:
        """Perform statistical power analysis"""

        n = len(data.pre_values)
        alpha = self.significance_level

        # Calculate observed effect size
        diff = np.array(data.post_values) - np.array(data.pre_values)
        mean_diff = np.mean(diff)
        pooled_sd = np.sqrt(
            (np.var(data.pre_values, ddof=1) + np.var(data.post_values, ddof=1)) / 2
        )

        if pooled_sd > 0:
            observed_effect_size = mean_diff / pooled_sd
        else:
            observed_effect_size = 0

        # Approximate power calculation (simplified)
        # In practice, you'd use power analysis libraries
        critical_t = stats.t.ppf(1 - alpha / 2, n - 1)
        noncentral_t = observed_effect_size * math.sqrt(n / 2)

        try:
            # Approximate power using non-central t-distribution
            power = (
                1
                - stats.nct.cdf(critical_t, n - 1, noncentral_t)
                + stats.nct.cdf(-critical_t, n - 1, noncentral_t)
            )
            power = max(0, min(1, power))  # Ensure power is between 0 and 1
        except Exception as e:
            power = None

        return {
            "sample_size": n,
            "observed_effect_size": observed_effect_size,
            "alpha": alpha,
            "power": power,
            "adequate_power": power >= 0.8 if power is not None else None,
            "minimum_detectable_effect": self._calculate_minimum_detectable_effect(
                n, alpha
            ),
        }

    def _calculate_minimum_detectable_effect(self, n: int, alpha: float) -> float:
        """Calculate minimum detectable effect size with 80% power"""
        # Simplified calculation - in practice use power analysis libraries
        power = 0.8
        critical_t = stats.t.ppf(1 - alpha / 2, n - 1)

        # Approximate minimum effect size for 80% power
        min_effect = critical_t * math.sqrt(2 / n)

        return min_effect
