"""
Reliability and Validity Analysis Service

Comprehensive psychometric analysis service for assessing the reliability and validity
of psychological assessments. This service implements industry-standard statistical methods
for evaluating measurement quality.

Key Features:
- Internal consistency reliability (Cronbach's Alpha, McDonald's Omega)
- Test-retest reliability analysis
- Factor analysis for construct validity
- Convergent and discriminant validity
- Criterion-related validity coefficients
- Item analysis and statistics
- Reliability generalization studies
- Validity dashboard and reporting
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")


from app.services.irt_service import IRTService

logger = logging.getLogger(__name__)


class ReliabilityType(Enum):
    """Types of reliability analysis."""

    INTERNAL_CONSISTENCY = "internal_consistency"
    TEST_RETEST = "test_retest"
    INTER_RATER = "inter_rater"
    PARALLEL_FORMS = "parallel_forms"


class ValidityType(Enum):
    """Types of validity analysis."""

    CONSTRUCT = "construct"
    CRITERION = "criterion"
    CONVERGENT = "convergent"
    DISCRIMINANT = "discriminant"
    CONTENT = "content"
    FACE = "face"


class FactorAnalysisMethod(Enum):
    """Factor analysis extraction methods."""

    PCA = "pca"
    PRINCIPAL_AXIS = "principal_axis"
    MAXIMUM_LIKELIHOOD = "maximum_likelihood"
    MINIMUM_RESIDUAL = "minimum_residual"


class RotationMethod(Enum):
    """Factor rotation methods."""

    VARIMAX = "varimax"
    EQUAMAX = "equamax"
    QUARTIMAX = "quartimax"
    PROMAX = "promax"
    OBLIMIN = "oblimin"
    NO_ROTATION = "none"


@dataclass
class ReliabilityResult:
    """Results from reliability analysis."""

    reliability_type: ReliabilityType
    coefficient: float
    confidence_interval: tuple[float, float] | None = None
    standard_error: float | None = None
    sample_size: int = 0
    interpretation: str = ""
    item_statistics: dict[str, dict[str, float]] | None = None
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ValidityResult:
    """Results from validity analysis."""

    validity_type: ValidityType
    coefficient: float
    significance_level: float
    confidence_interval: tuple[float, float] | None = None
    sample_size: int = 0
    interpretation: str = ""
    methodology: str = ""
    criterion_description: str | None = None
    recommendations: list[str] = field(default_factory=list)


@dataclass
class FactorAnalysisResult:
    """Results from factor analysis."""

    extraction_method: FactorAnalysisMethod
    rotation_method: RotationMethod
    eigenvalues: np.ndarray
    factor_loadings: pd.DataFrame
    communalities: np.ndarray
    uniqueness: np.ndarray
    variance_explained: np.ndarray
    cumulative_variance: np.ndarray
    factor_correlations: np.ndarray | None = None
    kaiser_criterion: int = 0
    parallel_analysis: int = 0
    scree_plot_data: dict[str, list[float]] | None = None
    factor_interpretation: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class ItemAnalysisResult:
    """Results from item analysis."""

    item_id: str
    difficulty: float  # p-value
    discrimination: float  # point-biserial correlation
    item_total_correlation: float
    item_reliability: float
    item_validity: float
    skewness: float
    kurtosis: float
    option_frequencies: dict[str, int] | None = None
    distractor_analysis: dict[str, dict[str, float]] | None = None


class ReliabilityValidityService:
    """
    Comprehensive reliability and validity analysis service.
    """

    def __init__(self):
        self.irt_service = IRTService()
        self.reliability_thresholds = self._initialize_reliability_thresholds()
        self.validity_thresholds = self._initialize_validity_thresholds()

    def _initialize_reliability_thresholds(self) -> dict[str, dict[str, float]]:
        """Initialize reliability interpretation thresholds."""
        return {
            "cronbach_alpha": {
                "excellent": 0.90,
                "good": 0.80,
                "acceptable": 0.70,
                "questionable": 0.60,
                "poor": 0.50,
            },
            "test_retest": {
                "excellent": 0.80,
                "good": 0.70,
                "acceptable": 0.60,
                "questionable": 0.50,
                "poor": 0.40,
            },
            "mcdonald_omega": {
                "excellent": 0.90,
                "good": 0.80,
                "acceptable": 0.70,
                "questionable": 0.60,
                "poor": 0.50,
            },
        }

    def _initialize_validity_thresholds(self) -> dict[str, dict[str, float]]:
        """Initialize validity interpretation thresholds."""
        return {
            "convergent": {
                "excellent": 0.70,
                "good": 0.60,
                "acceptable": 0.50,
                "questionable": 0.40,
                "poor": 0.30,
            },
            "criterion": {
                "excellent": 0.70,
                "good": 0.60,
                "acceptable": 0.50,
                "questionable": 0.40,
                "poor": 0.30,
            },
            "discriminant": {
                "excellent": 0.30,  # Lower is better for discriminant
                "good": 0.40,
                "acceptable": 0.50,
                "questionable": 0.60,
                "poor": 0.70,
            },
        }

    async def calculate_cronbach_alpha(
        self,
        response_matrix: pd.DataFrame,
        item_ids: list[str] | None = None,
        confidence_level: float = 0.95,
    ) -> ReliabilityResult:
        """
        Calculate Cronbach's Alpha for internal consistency reliability.

        Args:
            response_matrix: DataFrame with items as columns and respondents as rows
            item_ids: List of item IDs to include (if None, use all columns)
            confidence_level: Confidence level for confidence interval

        Returns:
            ReliabilityResult with Cronbach's Alpha statistics
        """
        try:
            if item_ids:
                item_data = response_matrix[item_ids]
            else:
                item_data = response_matrix

            # Remove rows with missing data
            item_data = item_data.dropna()

            if len(item_data) < 2 or item_data.shape[1] < 2:
                return ReliabilityResult(
                    reliability_type=ReliabilityType.INTERNAL_CONSISTENCY,
                    coefficient=0.0,
                    sample_size=len(item_data),
                    interpretation="Insufficient data for reliability analysis",
                )

            # Calculate Cronbach's Alpha
            n_items = item_data.shape[1]
            item_variances = item_data.var(axis=0, ddof=1)
            total_score = item_data.sum(axis=1)
            total_variance = total_score.var(ddof=1)

            if n_items == 0:
                alpha = 0.0
            else:
                alpha = (n_items / (n_items - 1)) * (1 - (item_variances.sum() / total_variance))
                alpha = max(0.0, min(1.0, alpha))  # Ensure alpha is between 0 and 1

            # Calculate confidence interval using Feldt's method
            alpha_ci = self._calculate_alpha_confidence_interval(
                alpha, n_items, len(item_data), confidence_level
            )

            # Item-total correlations and item statistics
            item_statistics = {}
            for item_id in item_data.columns:
                item_scores = item_data[item_id]
                other_items_total = item_data.drop(columns=[item_id]).sum(axis=1)

                # Item-total correlation (corrected)
                item_total_corr = stats.pearsonr(item_scores, other_items_total)[0]

                # Alpha if item deleted
                item_data_without = item_data.drop(columns=[item_id])
                if item_data_without.shape[1] > 1:
                    n_items_without = item_data_without.shape[1]
                    item_variances_without = item_data_without.var(axis=0, ddof=1)
                    total_score_without = item_data_without.sum(axis=1)
                    total_variance_without = total_score_without.var(ddof=1)

                    alpha_without = (n_items_without / (n_items_without - 1)) * (
                        1 - (item_variances_without.sum() / total_variance_without)
                    )
                    alpha_without = max(0.0, min(1.0, alpha_without))
                else:
                    alpha_without = 0.0

                item_statistics[item_id] = {
                    "item_total_correlation": item_total_corr,
                    "alpha_if_deleted": alpha_without,
                    "item_mean": item_scores.mean(),
                    "item_std": item_scores.std(),
                    "item_variance": item_scores.var(ddof=1),
                }

            # Interpretation
            interpretation = self._interpret_reliability_coefficient(alpha, "cronbach_alpha")

            # Recommendations
            recommendations = self._generate_reliability_recommendations(
                alpha, item_statistics, n_items
            )

            return ReliabilityResult(
                reliability_type=ReliabilityType.INTERNAL_CONSISTENCY,
                coefficient=alpha,
                confidence_interval=alpha_ci,
                sample_size=len(item_data),
                interpretation=interpretation,
                item_statistics=item_statistics,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating Cronbach's Alpha: {e!s}")
            return ReliabilityResult(
                reliability_type=ReliabilityType.INTERNAL_CONSISTENCY,
                coefficient=0.0,
                interpretation=f"Error in calculation: {e!s}",
            )

    async def calculate_mcdonald_omega(
        self, response_matrix: pd.DataFrame, item_ids: list[str] | None = None
    ) -> ReliabilityResult:
        """
        Calculate McDonald's Omega for internal consistency reliability.
        This is often preferred over Cronbach's Alpha when items don't meet tau-equivalence.

        Args:
            response_matrix: DataFrame with items as columns and respondents as rows
            item_ids: List of item IDs to include

        Returns:
            ReliabilityResult with McDonald's Omega statistics
        """
        try:
            if item_ids:
                item_data = response_matrix[item_ids]
            else:
                item_data = response_matrix

            item_data = item_data.dropna()

            if len(item_data) < 2 or item_data.shape[1] < 2:
                return ReliabilityResult(
                    reliability_type=ReliabilityType.INTERNAL_CONSISTENCY,
                    coefficient=0.0,
                    sample_size=len(item_data),
                    interpretation="Insufficient data for reliability analysis",
                )

            # Standardize the data
            scaler = StandardScaler()
            standardized_data = pd.DataFrame(
                scaler.fit_transform(item_data), columns=item_data.columns
            )

            # Calculate correlation matrix
            correlation_matrix = standardized_data.corr()

            # Factor analysis to extract general factor
            n_items = item_data.shape[1]
            fa = FactorAnalysis(n_components=1, random_state=42)
            factor_loadings = fa.fit_transform(standardized_data)

            # Calculate omega
            loading_matrix = fa.components_.T
            squared_loadings = loading_matrix**2
            error_variances = 1 - squared_loadings.flatten()

            omega = (squared_loadings.sum()) / (squared_loadings.sum() + error_variances.sum())
            omega = max(0.0, min(1.0, omega))

            # Interpretation
            interpretation = self._interpret_reliability_coefficient(omega, "mcdonald_omega")

            return ReliabilityResult(
                reliability_type=ReliabilityType.INTERNAL_CONSISTENCY,
                coefficient=omega,
                sample_size=len(item_data),
                interpretation=interpretation,
                recommendations=[
                    "Consider using omega over alpha when items are not tau-equivalent"
                ],
            )

        except Exception as e:
            logger.error(f"Error calculating McDonald's Omega: {e!s}")
            return ReliabilityResult(
                reliability_type=ReliabilityType.INTERNAL_CONSISTENCY,
                coefficient=0.0,
                interpretation=f"Error in calculation: {e!s}",
            )

    async def calculate_test_retest_reliability(
        self,
        time1_responses: pd.DataFrame,
        time2_responses: pd.DataFrame,
        test_retest_interval: int,
        time_point_matching: str = "respondent_id",
    ) -> ReliabilityResult:
        """
        Calculate test-retest reliability using correlation between two time points.

        Args:
            time1_responses: DataFrame with responses at time 1
            time2_responses: DataFrame with responses at time 2
            test_retest_interval: Number of days between test administrations
            time_point_matching: Column name for matching respondents across time points

        Returns:
            ReliabilityResult with test-retest reliability statistics
        """
        try:
            # Merge the two time point datasets
            merged_data = pd.merge(
                time1_responses, time2_responses, on=time_point_matching, suffixes=("_t1", "_t2")
            )

            if len(merged_data) < 30:  # Minimum sample size recommendation
                return ReliabilityResult(
                    reliability_type=ReliabilityType.TEST_RETEST,
                    coefficient=0.0,
                    sample_size=len(merged_data),
                    interpretation="Insufficient sample size for test-retest reliability (n < 30)",
                )

            # Calculate total scores at each time point
            time1_columns = [col for col in merged_data.columns if col.endswith("_t1")]
            time2_columns = [col for col in merged_data.columns if col.endswith("_t2")]

            # Match items across time points
            score_pairs = []
            for col in time1_columns:
                item_name = col.replace("_t1", "")
                t2_col = f"{item_name}_t2"
                if t2_col in merged_data.columns:
                    score_pairs.append((col, t2_col))

            # Calculate correlations for each item and total score
            item_correlations = {}
            total_scores_t1 = []
            total_scores_t2 = []

            for t1_col, t2_col in score_pairs:
                # Remove rows with missing data
                valid_pairs = merged_data[[t1_col, t2_col]].dropna()

                if len(valid_pairs) >= 10:  # Minimum for correlation
                    correlation, p_value = stats.pearsonr(valid_pairs[t1_col], valid_pairs[t2_col])
                    item_correlations[t1_col.replace("_t1", "")] = {
                        "correlation": correlation,
                        "p_value": p_value,
                        "n": len(valid_pairs),
                    }

                # Add to total scores
                if len(valid_pairs) >= 10:
                    total_scores_t1.extend(valid_pairs[t1_col].tolist())
                    total_scores_t2.extend(valid_pairs[t2_col].tolist())

            # Calculate overall test-retest reliability
            if len(total_scores_t1) >= 30:
                overall_correlation, overall_p = stats.pearsonr(total_scores_t1, total_scores_t2)

                # Calculate confidence interval
                se = np.sqrt((1 - overall_correlation**2) / (len(total_scores_t1) - 2))
                z = stats.norm.ppf(1 - (1 - 0.95) / 2)
                ci_lower = np.tanh(np.arctanh(overall_correlation) - z * se)
                ci_upper = np.tanh(np.arctanh(overall_correlation) + z * se)
                confidence_interval = (ci_lower, ci_upper)
            else:
                overall_correlation = 0.0
                confidence_interval = None

            # Interpretation considering test-retest interval
            interpretation = self._interpret_test_retest_reliability(
                overall_correlation, test_retest_interval
            )

            # Generate recommendations
            recommendations = self._generate_test_retest_recommendations(
                overall_correlation, test_retest_interval, len(merged_data)
            )

            return ReliabilityResult(
                reliability_type=ReliabilityType.TEST_RETEST,
                coefficient=overall_correlation,
                confidence_interval=confidence_interval,
                sample_size=len(merged_data),
                interpretation=interpretation,
                item_statistics=item_correlations,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating test-retest reliability: {e!s}")
            return ReliabilityResult(
                reliability_type=ReliabilityType.TEST_RETEST,
                coefficient=0.0,
                interpretation=f"Error in calculation: {e!s}",
            )

    async def conduct_factor_analysis(
        self,
        response_matrix: pd.DataFrame,
        extraction_method: FactorAnalysisMethod = FactorAnalysisMethod.PRINCIPAL_AXIS,
        rotation_method: RotationMethod = RotationMethod.VARIMAX,
        n_factors: int | None = None,
        parallel_analysis_samples: int = 100,
    ) -> FactorAnalysisResult:
        """
        Conduct exploratory factor analysis to assess construct validity.

        Args:
            response_matrix: DataFrame with items as columns and respondents as rows
            extraction_method: Method for factor extraction
            rotation_method: Method for factor rotation
            n_factors: Number of factors to extract (if None, use eigenvalue > 1)
            parallel_analysis_samples: Number of samples for parallel analysis

        Returns:
            FactorAnalysisResult with comprehensive factor analysis statistics
        """
        try:
            # Clean data
            item_data = response_matrix.dropna()

            if len(item_data) < 100 or item_data.shape[1] < 3:
                raise ValueError(
                    "Insufficient data for factor analysis (need n >= 100 and items >= 3)"
                )

            # Standardize the data
            scaler = StandardScaler()
            standardized_data = scaler.fit_transform(item_data)

            # Calculate correlation matrix
            correlation_matrix = np.corrcoef(standardized_data.T)

            # Check suitability for factor analysis
            kmo_result = self._calculate_kmo(correlation_matrix)
            bartlett_result = self._calculate_bartlett_test(correlation_matrix, len(item_data))

            # Eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eig(correlation_matrix)
            eigenvalues = np.real(eigenvalues)  # Remove imaginary parts
            eigenvalues = np.sort(eigenvalues)[::-1]  # Sort in descending order

            # Determine number of factors if not specified
            if n_factors is None:
                # Kaiser criterion (eigenvalue > 1)
                n_factors_kaiser = np.sum(eigenvalues > 1.0)

                # Parallel analysis
                n_factors_parallel = await self._parallel_analysis(
                    standardized_data, parallel_analysis_samples
                )

                # Use the more conservative estimate
                n_factors = min(n_factors_kaiser, n_factors_parallel)

            n_factors = max(1, min(n_factors, len(item_data.columns) - 1))

            # Perform factor analysis based on extraction method
            if extraction_method == FactorAnalysisMethod.PCA:
                fa = PCA(n_components=n_factors, random_state=42)
                factor_scores = fa.fit_transform(standardized_data)
                factor_loadings = fa.components_.T
                communalities = fa.explained_variance_
                uniqueness = 1 - fa.explained_variance_ratio_
            else:
                # Use scikit-learn FactorAnalysis for other methods
                fa = FactorAnalysis(n_components=n_factors, random_state=42)
                factor_scores = fa.fit_transform(standardized_data)
                factor_loadings = fa.components_.T
                communalities = np.sum(fa.components_.T**2, axis=1)
                uniqueness = 1 - communalities

            # Create factor loadings DataFrame
            factor_columns = [f"Factor_{i + 1}" for i in range(n_factors)]
            loadings_df = pd.DataFrame(
                factor_loadings, index=item_data.columns, columns=factor_columns
            )

            # Calculate variance explained
            variance_explained = eigenvalues[:n_factors] / np.sum(eigenvalues)
            cumulative_variance = np.cumsum(variance_explained)

            # Factor correlations (for oblique rotations)
            factor_correlations = None
            if rotation_method in [RotationMethod.PROMAX, RotationMethod.OBLIMIN]:
                # For oblique rotations, factor correlations should be calculated
                # This is a simplified approach
                factor_correlations = np.corrcoef(factor_scores.T)

            # Generate scree plot data
            scree_plot_data = {
                "factor_numbers": list(range(1, len(eigenvalues) + 1)),
                "eigenvalues": eigenvalues.tolist(),
                "parallel_analysis": [],  # Would be filled with parallel analysis results
            }

            # Interpret factors
            factor_interpretation = self._interpret_factors(loadings_df, item_data.columns)

            return FactorAnalysisResult(
                extraction_method=extraction_method,
                rotation_method=rotation_method,
                eigenvalues=eigenvalues,
                factor_loadings=loadings_df,
                communalities=communalities,
                uniqueness=uniqueness,
                variance_explained=variance_explained,
                cumulative_variance=cumulative_variance,
                factor_correlations=factor_correlations,
                kaiser_criterion=np.sum(eigenvalues > 1.0),
                parallel_analysis=n_factors,
                scree_plot_data=scree_plot_data,
                factor_interpretation=factor_interpretation,
            )

        except Exception as e:
            logger.error(f"Error in factor analysis: {e!s}")
            raise

    async def calculate_convergent_validity(
        self,
        assessment_scores: pd.Series,
        criterion_scores: pd.Series,
        criterion_description: str = "",
    ) -> ValidityResult:
        """
        Calculate convergent validity by correlating assessment with similar measures.

        Args:
            assessment_scores: Scores from the assessment being validated
            criterion_scores: Scores from a similar, established measure
            criterion_description: Description of the criterion measure

        Returns:
            ValidityResult with convergent validity statistics
        """
        try:
            # Remove missing data
            valid_data = pd.DataFrame(
                {"assessment": assessment_scores, "criterion": criterion_scores}
            ).dropna()

            if len(valid_data) < 50:  # Minimum sample size recommendation
                return ValidityResult(
                    validity_type=ValidityType.CONVERGENT,
                    coefficient=0.0,
                    significance_level=1.0,
                    sample_size=len(valid_data),
                    interpretation="Insufficient sample size for validity analysis (n < 50)",
                )

            # Calculate Pearson correlation
            correlation, p_value = stats.pearsonr(valid_data["assessment"], valid_data["criterion"])

            # Calculate confidence interval
            n = len(valid_data)
            se = np.sqrt((1 - correlation**2) / (n - 2))
            z = stats.norm.ppf(1 - (1 - 0.95) / 2)
            ci_lower = np.tanh(np.arctanh(correlation) - z * se)
            ci_upper = np.tanh(np.arctanh(correlation) + z * se)
            confidence_interval = (ci_lower, ci_upper)

            # Interpretation
            interpretation = self._interpret_validity_coefficient(abs(correlation), "convergent")

            # Recommendations
            recommendations = self._generate_convergent_validity_recommendations(
                abs(correlation), p_value, criterion_description
            )

            return ValidityResult(
                validity_type=ValidityType.CONVERGENT,
                coefficient=correlation,
                significance_level=p_value,
                confidence_interval=confidence_interval,
                sample_size=len(valid_data),
                interpretation=interpretation,
                methodology="Pearson correlation coefficient",
                criterion_description=criterion_description,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating convergent validity: {e!s}")
            return ValidityResult(
                validity_type=ValidityType.CONVERGENT,
                coefficient=0.0,
                significance_level=1.0,
                interpretation=f"Error in calculation: {e!s}",
            )

    async def calculate_discriminant_validity(
        self,
        assessment_scores: pd.Series,
        unrelated_scores: pd.Series,
        unrelated_construct_description: str = "",
    ) -> ValidityResult:
        """
        Calculate discriminant validity by showing low correlation with unrelated constructs.

        Args:
            assessment_scores: Scores from the assessment being validated
            unrelated_scores: Scores from theoretically unrelated constructs
            unrelated_construct_description: Description of the unrelated construct

        Returns:
            ValidityResult with discriminant validity statistics
        """
        try:
            # Remove missing data
            valid_data = pd.DataFrame(
                {"assessment": assessment_scores, "unrelated": unrelated_scores}
            ).dropna()

            if len(valid_data) < 50:
                return ValidityResult(
                    validity_type=ValidityType.DISCRIMINANT,
                    coefficient=0.0,
                    significance_level=1.0,
                    sample_size=len(valid_data),
                    interpretation="Insufficient sample size for validity analysis (n < 50)",
                )

            # Calculate correlation
            correlation, p_value = stats.pearsonr(valid_data["assessment"], valid_data["unrelated"])

            # For discriminant validity, we're interested in absolute correlation
            abs_correlation = abs(correlation)

            # Calculate confidence interval
            n = len(valid_data)
            se = np.sqrt((1 - correlation**2) / (n - 2))
            z = stats.norm.ppf(1 - (1 - 0.95) / 2)
            ci_lower = np.tanh(np.arctanh(correlation) - z * se)
            ci_upper = np.tanh(np.arctanh(correlation) + z * se)
            confidence_interval = (ci_lower, ci_upper)

            # Interpretation (lower is better for discriminant validity)
            interpretation = self._interpret_validity_coefficient(abs_correlation, "discriminant")

            # Recommendations
            recommendations = self._generate_discriminant_validity_recommendations(
                abs_correlation, p_value, unrelated_construct_description
            )

            return ValidityResult(
                validity_type=ValidityType.DISCRIMINANT,
                coefficient=correlation,
                significance_level=p_value,
                confidence_interval=confidence_interval,
                sample_size=len(valid_data),
                interpretation=interpretation,
                methodology="Pearson correlation coefficient",
                criterion_description=unrelated_construct_description,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error calculating discriminant validity: {e!s}")
            return ValidityResult(
                validity_type=ValidityType.DISCRIMINANT,
                coefficient=0.0,
                significance_level=1.0,
                interpretation=f"Error in calculation: {e!s}",
            )

    async def conduct_item_analysis(
        self,
        response_matrix: pd.DataFrame,
        total_scores: pd.Series,
        item_answer_keys: dict[str, str] | None = None,
    ) -> dict[str, ItemAnalysisResult]:
        """
        Conduct comprehensive item analysis including difficulty, discrimination, and validity.

        Args:
            response_matrix: DataFrame with items as columns and respondents as rows
            total_scores: Total assessment scores for item-total correlations
            item_answer_keys: Dictionary of correct answers for cognitive tests

        Returns:
            Dictionary of item analysis results indexed by item ID
        """
        try:
            item_results = {}

            for item_id in response_matrix.columns:
                item_responses = response_matrix[item_id].dropna()

                if len(item_responses) < 10:
                    continue

                # Item difficulty (p-value)
                difficulty = item_responses.mean()

                # Item discrimination (point-biserial correlation)
                item_total_corr = stats.pointbiserialr(item_responses, total_scores).correlation

                # Item validity (correlation with external criterion if available)
                # This would require external criterion data

                # Distribution statistics
                skewness = stats.skew(item_responses)
                kurtosis = stats.kurtosis(item_responses)

                # Item reliability (squared item-total correlation)
                item_reliability = item_total_corr**2

                # Option frequencies (for multiple-choice items)
                option_frequencies = None
                distractor_analysis = None

                if item_answer_keys and item_id in item_answer_keys:
                    # Analyze multiple-choice options
                    value_counts = item_responses.value_counts().to_dict()
                    option_frequencies = {str(k): v for k, v in value_counts.items()}

                    # Distractor analysis
                    correct_answer = item_answer_keys[item_id]
                    distractor_analysis = {}

                    for option, frequency in value_counts.items():
                        if str(option) != str(correct_answer):
                            # Calculate discrimination for this distractor
                            option_binary = (item_responses == option).astype(int)
                            if option_binary.sum() > 0:
                                distractor_corr = stats.pointbiserialr(
                                    option_binary, total_scores
                                ).correlation
                                distractor_analysis[str(option)] = {
                                    "frequency": frequency,
                                    "discrimination": distractor_corr,
                                    "is_effective": distractor_corr
                                    < 0,  # Good distractors have negative discrimination
                                }

                item_results[item_id] = ItemAnalysisResult(
                    item_id=item_id,
                    difficulty=difficulty,
                    discrimination=item_total_corr,
                    item_total_correlation=item_total_corr,
                    item_reliability=item_reliability,
                    item_validity=0.0,  # Would be calculated with external criterion
                    skewness=skewness,
                    kurtosis=kurtosis,
                    option_frequencies=option_frequencies,
                    distractor_analysis=distractor_analysis,
                )

            return item_results

        except Exception as e:
            logger.error(f"Error in item analysis: {e!s}")
            return {}

    # Helper methods
    def _calculate_alpha_confidence_interval(
        self, alpha: float, n_items: int, n_respondents: int, confidence_level: float
    ) -> tuple[float, float]:
        """Calculate confidence interval for Cronbach's Alpha using Feldt's method."""
        try:
            if alpha <= 0 or alpha >= 1 or n_respondents <= 1:
                return (0.0, 1.0)

            alpha_transformed = 1 - alpha
            df = n_respondents - 1

            # F-statistic approximation for confidence interval
            from scipy.stats import f

            lower_crit = f.ppf(1 - confidence_level, df, df)
            upper_crit = f.ppf(confidence_level, df, df)

            alpha_lower = 1 - (alpha_transformed * lower_crit)
            alpha_upper = 1 - (alpha_transformed * upper_crit)

            # Ensure bounds are within [0, 1]
            alpha_lower = max(0.0, min(1.0, alpha_lower))
            alpha_upper = max(0.0, min(1.0, alpha_upper))

            return (alpha_lower, alpha_upper)

        except Exception:
            return (0.0, 1.0)

    def _interpret_reliability_coefficient(self, coefficient: float, reliability_type: str) -> str:
        """Interpret reliability coefficient based on established thresholds."""
        thresholds = self.reliability_thresholds.get(reliability_type, {})

        if coefficient >= thresholds.get("excellent", 0.90):
            return f"Excellent reliability ({coefficient:.3f}). The assessment demonstrates strong internal consistency."
        if coefficient >= thresholds.get("good", 0.80):
            return f"Good reliability ({coefficient:.3f}). The assessment has acceptable internal consistency."
        if coefficient >= thresholds.get("acceptable", 0.70):
            return f"Acceptable reliability ({coefficient:.3f}). The assessment meets minimum standards for reliability."
        if coefficient >= thresholds.get("questionable", 0.60):
            return f"Questionable reliability ({coefficient:.3f}). Consider item analysis and revision."
        return (
            f"Poor reliability ({coefficient:.3f}). The assessment requires substantial revision."
        )

    def _interpret_test_retest_reliability(self, coefficient: float, interval_days: int) -> str:
        """Interpret test-retest reliability considering the time interval."""
        thresholds = self.reliability_thresholds["test_retest"]

        # Adjust expectations based on interval
        if interval_days <= 7:  # Short interval
            expected_min = 0.80
        elif interval_days <= 30:  # Medium interval
            expected_min = 0.70
        else:  # Long interval
            expected_min = 0.60

        if coefficient >= thresholds.get("excellent", 0.80):
            return (
                f"Excellent test-retest reliability ({coefficient:.3f}) over {interval_days} days."
            )
        if coefficient >= expected_min:
            return f"Good test-retest reliability ({coefficient:.3f}) over {interval_days} days."
        return f"Low test-retest reliability ({coefficient:.3f}) over {interval_days} days. Consider construct instability or measurement error."

    def _interpret_validity_coefficient(self, coefficient: float, validity_type: str) -> str:
        """Interpret validity coefficient."""
        thresholds = self.validity_thresholds.get(validity_type, {})

        if validity_type == "discriminant":
            # For discriminant validity, lower is better
            if coefficient <= thresholds.get("excellent", 0.30):
                return f"Excellent discriminant validity ({coefficient:.3f}). Low correlation with unrelated constructs."
            if coefficient <= thresholds.get("good", 0.40):
                return f"Good discriminant validity ({coefficient:.3f})."
            return f"Poor discriminant validity ({coefficient:.3f}). High correlation suggests construct overlap."
        # For convergent and criterion validity, higher is better
        if coefficient >= thresholds.get("excellent", 0.70):
            return f"Excellent validity ({coefficient:.3f}). Strong relationship with criterion."
        if coefficient >= thresholds.get("good", 0.60):
            return f"Good validity ({coefficient:.3f}). Adequate relationship with criterion."
        if coefficient >= thresholds.get("acceptable", 0.50):
            return f"Acceptable validity ({coefficient:.3f}). Meets minimum standards."
        return f"Poor validity ({coefficient:.3f}). Weak relationship with criterion."

    async def _parallel_analysis(self, data: np.ndarray, n_samples: int = 100) -> int:
        """Conduct parallel analysis to determine optimal number of factors."""
        try:
            n_items = data.shape[1]
            n_respondents = data.shape[0]

            # Generate random data and calculate eigenvalues
            random_eigenvalues = []

            for _ in range(n_samples):
                random_data = np.random.normal(0, 1, (n_respondents, n_items))
                correlation_matrix = np.corrcoef(random_data.T)
                eigenvalues = np.linalg.eigvals(correlation_matrix)
                random_eigenvalues.extend(np.real(eigenvalues))

            # Calculate 95th percentile for each eigenvalue position
            random_eigenvalues = np.array(random_eigenvalues).reshape(n_samples, n_items)
            percentile_95 = np.percentile(random_eigenvalues, 95, axis=0)

            # Calculate actual eigenvalues
            actual_correlation = np.corrcoef(data.T)
            actual_eigenvalues = np.linalg.eigvals(actual_correlation)
            actual_eigenvalues = np.sort(np.real(actual_eigenvalues))[::-1]

            # Determine number of factors where actual eigenvalue > 95th percentile
            n_factors = np.sum(actual_eigenvalues > percentile_95)

            return max(1, n_factors)

        except Exception as e:
            logger.error(f"Error in parallel analysis: {e!s}")
            return 1

    def _calculate_kmo(self, correlation_matrix: np.ndarray) -> dict[str, float]:
        """Calculate Kaiser-Meyer-Olkin measure of sampling adequacy."""
        try:
            # Calculate inverse of correlation matrix
            try:
                inverse_corr = np.linalg.inv(correlation_matrix)
            except np.linalg.LinAlgError:
                return {"kmo_overall": 0.0, "kmo_individual": []}

            # Calculate partial correlations
            n_items = correlation_matrix.shape[0]
            partial_corr = -inverse_corr / np.sqrt(
                np.outer(np.diag(inverse_corr), np.diag(inverse_corr))
            )
            np.fill_diagonal(partial_corr, 0)

            # Calculate KMO statistics
            correlation_sq = correlation_matrix**2
            partial_corr_sq = partial_corr**2

            kmo_overall = np.sum(correlation_sq) - np.sum(np.diag(correlation_sq))
            kmo_overall /= kmo_overall + 2 * np.sum(partial_corr_sq - np.diag(partial_corr_sq))

            kmo_individual = []
            for i in range(n_items):
                kmo_i = np.sum(correlation_sq[i, :]) - correlation_sq[i, i]
                kmo_i /= kmo_i + 2 * np.sum(partial_corr_sq[i, :])
                kmo_individual.append(kmo_i)

            return {"kmo_overall": kmo_overall, "kmo_individual": kmo_individual}

        except Exception as e:
            logger.error(f"Error calculating KMO: {e!s}")
            return {"kmo_overall": 0.0, "kmo_individual": []}

    def _calculate_bartlett_test(
        self, correlation_matrix: np.ndarray, n_samples: int
    ) -> dict[str, Any]:
        """Calculate Bartlett's test of sphericity."""
        try:
            n_items = correlation_matrix.shape[0]

            # Calculate determinant of correlation matrix
            det = np.linalg.det(correlation_matrix)

            if det <= 0:
                return {"chi_square": 0.0, "df": 0, "p_value": 1.0}

            # Calculate Bartlett's chi-square statistic
            chi_square = -(n_samples - 1 - (2 * n_items + 5) / 6) * np.log(det)
            df = n_items * (n_items - 1) / 2
            p_value = 1 - stats.chi2.cdf(chi_square, df)

            return {"chi_square": chi_square, "df": df, "p_value": p_value}

        except Exception as e:
            logger.error(f"Error calculating Bartlett's test: {e!s}")
            return {"chi_square": 0.0, "df": 0, "p_value": 1.0}

    def _interpret_factors(
        self, loadings_df: pd.DataFrame, item_ids: list[str]
    ) -> dict[str, list[str]]:
        """Interpret factors based on factor loadings."""
        try:
            factor_interpretation = {}

            for factor_col in loadings_df.columns:
                # Get items with high loadings (> 0.4 or <-0.4)
                high_loadings = loadings_df[abs(loadings_df[factor_col]) > 0.4]
                high_loadings = high_loadings.sort_values(by=factor_col, key=abs, ascending=False)

                factor_items = high_loadings.index.tolist()
                factor_interpretation[factor_col] = factor_items

            return factor_interpretation

        except Exception as e:
            logger.error(f"Error interpreting factors: {e!s}")
            return {}

    def _generate_reliability_recommendations(
        self, alpha: float, item_statistics: dict[str, dict[str, float]], n_items: int
    ) -> list[str]:
        """Generate recommendations based on reliability analysis."""
        recommendations = []

        if alpha < 0.70:
            recommendations.append(
                "Consider increasing the number of items to improve reliability."
            )
            recommendations.append("Review items with low item-total correlations (< 0.30).")

        # Check items that would improve reliability if deleted
        items_to_review = []
        for item_id, stats in item_statistics.items():
            if stats.get("alpha_if_deleted", 0) > alpha:
                items_to_review.append(item_id)

        if items_to_review:
            recommendations.append(
                f"Consider revising or removing items: {', '.join(items_to_review[:5])}"
            )

        if n_items < 10:
            recommendations.append("Consider adding more items to improve measurement precision.")

        return recommendations

    def _generate_test_retest_recommendations(
        self, correlation: float, interval_days: int, sample_size: int
    ) -> list[str]:
        """Generate recommendations for test-retest reliability."""
        recommendations = []

        if correlation < 0.70:
            if interval_days > 30:
                recommendations.append(
                    "Consider that low reliability may be due to genuine change over time."
                )
            else:
                recommendations.append("Review item clarity and scoring consistency.")
                recommendations.append("Consider providing clearer instructions to respondents.")

        if sample_size < 50:
            recommendations.append("Increase sample size for more reliable test-retest estimates.")

        return recommendations

    def _generate_convergent_validity_recommendations(
        self, correlation: float, p_value: float, criterion_description: str
    ) -> list[str]:
        """Generate recommendations for convergent validity."""
        recommendations = []

        if abs(correlation) < 0.50:
            if criterion_description:
                recommendations.append(
                    f"Review conceptual overlap between your assessment and {criterion_description}."
                )
            recommendations.append(
                "Consider whether the criterion measure is appropriate for validation."
            )
            recommendations.append(
                "Examine whether the assessment measures the intended construct."
            )

        if p_value > 0.05:
            recommendations.append(
                "The correlation is not statistically significant. Consider increasing sample size."
            )

        return recommendations

    def _generate_discriminant_validity_recommendations(
        self, correlation: float, p_value: float, construct_description: str
    ) -> list[str]:
        """Generate recommendations for discriminant validity."""
        recommendations = []

        if abs(correlation) > 0.50:
            if construct_description:
                recommendations.append(
                    f"High correlation with {construct_description} suggests construct overlap."
                )
            recommendations.append("Consider whether these constructs are truly distinct.")
            recommendations.append("Review item content to ensure construct differentiation.")

        return recommendations
