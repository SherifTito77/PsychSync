"""
IRT Calibration and Validation Service
Provides comprehensive tools for IRT model calibration, validation,
quality assessment, and diagnostic reporting.
"""

import json
import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from scipy import stats

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

from app.services.irt_service import (
    EstimationMethod,
    IRTCalibrationResult,
    IRTItem,
    IRTModel,
    IRTPerson,
    IRTResponse,
    IRTService,
)

logger = logging.getLogger(__name__)


class ValidationMetric(Enum):
    """Types of validation metrics"""

    ITEM_FIT = "item_fit"
    PERSON_FIT = "person_fit"
    UNIDIMENSIONALITY = "unidimensionality"
    LOCAL_INDEPENDENCE = "local_independence"
    DIFFERENTIAL_ITEM_FUNCTIONING = "dif"
    RELIABILITY = "reliability"
    STANDARD_ERRORS = "standard_errors"


class CalibrationStatus(Enum):
    """Calibration status levels"""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    QUESTIONABLE = "questionable"
    POOR = "poor"
    FAILED = "failed"


@dataclass
class ItemFitStatistics:
    """Item fit statistics"""

    item_id: str
    outfit_mnsq: float  # Outfit mean square
    infit_mnsq: float  # Infit mean square
    outfit_zstd: float  # Outfit z-standardized
    infit_zstd: float  # Infit z-standardized
    point_biserial: float  # Point-biserial correlation
    biserial: float  # Biserial correlation
    item_total_correlation: float
    status: CalibrationStatus
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "outfit_mnsq": self.outfit_mnsq,
            "infit_mnsq": self.infit_mnsq,
            "outfit_zstd": self.outfit_zstd,
            "infit_zstd": self.infit_zstd,
            "point_biserial": self.point_biserial,
            "biserial": self.biserial,
            "item_total_correlation": self.item_total_correlation,
            "status": self.status.value,
            "interpretation": self.interpretation,
        }


@dataclass
class PersonFitStatistics:
    """Person fit statistics"""

    person_id: str
    outfit_mnsq: float
    infit_mnsq: float
    outfit_zstd: float
    infit_zstd: float
    pattern_score: int
    ability: float
    standard_error: float
    status: CalibrationStatus
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "outfit_mnsq": self.outfit_mnsq,
            "infit_mnsq": self.infit_mnsq,
            "outfit_zstd": self.outfit_zstd,
            "infit_zstd": self.infit_zstd,
            "pattern_score": self.pattern_score,
            "ability": self.ability,
            "standard_error": self.standard_error,
            "status": self.status.value,
            "interpretation": self.interpretation,
        }


@dataclass
class ReliabilityAnalysis:
    """Reliability analysis results"""

    cronbach_alpha: float
    mcdonalds_omega: float
    test_reliability: float
    split_half_reliability: float
    stratified_alpha: float
    sem: float  # Standard Error of Measurement
    interpretation: str
    status: CalibrationStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "cronbach_alpha": self.cronbach_alpha,
            "mcdonalds_omega": self.mcdonalds_omega,
            "test_reliability": self.test_reliability,
            "split_half_reliability": self.split_half_reliability,
            "stratified_alpha": self.stratified_alpha,
            "sem": self.sem,
            "interpretation": self.interpretation,
            "status": self.status.value,
        }


@dataclass
class DimensionalityAnalysis:
    """Dimensionality analysis results"""

    eigenvalues: list[float]
    variance_explained: list[float]
    parallel_analysis: list[float]
    Kaiser_criterion: int
    scree_plot: str  # Base64 encoded plot
    factor_structure: list[list[float]]
    unidimensionality_score: float
    status: CalibrationStatus
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "eigenvalues": self.eigenvalues,
            "variance_explained": self.variance_explained,
            "parallel_analysis": self.parallel_analysis,
            "kaiser_criterion": self.kaiser_criterion,
            "scree_plot": self.scree_plot,
            "factor_structure": self.factor_structure,
            "unidimensionality_score": self.unidimensionality_score,
            "status": self.status.value,
            "interpretation": self.interpretation,
        }


@dataclass
class DIFAnalysis:
    """Differential Item Functioning analysis"""

    item_id: str
    group_type: str  # e.g., "gender", "age_group"
    group1_name: str
    group2_name: str
    effect_size: float
    p_value: float
    delta_difficulty: float  # Difference in difficulty between groups
    delta_discrimination: float  # Difference in discrimination between groups
    mantel_haenszel_chi2: float
    mantel_haenszel_p: float
    status: CalibrationStatus
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "group_type": self.group_type,
            "group1_name": self.group1_name,
            "group2_name": self.group2_name,
            "effect_size": self.effect_size,
            "p_value": self.p_value,
            "delta_difficulty": self.delta_difficulty,
            "delta_discrimination": self.delta_discrimination,
            "mantel_haenszel_chi2": self.mantel_haenszel_chi2,
            "mantel_haenszel_p": self.mantel_haenszel_p,
            "status": self.status.value,
            "interpretation": self.interpretation,
        }


@dataclass
class CalibrationReport:
    """Comprehensive calibration report"""

    calibration_id: str
    timestamp: datetime
    model: IRTModel
    sample_size: int
    item_count: int
    item_fit_stats: list[ItemFitStatistics]
    person_fit_stats: list[PersonFitStatistics]
    reliability_analysis: ReliabilityAnalysis
    dimensionality_analysis: DimensionalityAnalysis
    dif_analyses: list[DIFAnalysis]
    overall_status: CalibrationStatus
    recommendations: list[str]
    summary_metrics: dict[str, float]
    validation_checks: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibration_id": self.calibration_id,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model.value,
            "sample_size": self.sample_size,
            "item_count": self.item_count,
            "item_fit_stats": [stat.to_dict() for stat in self.item_fit_stats],
            "person_fit_stats": [stat.to_dict() for stat in self.person_fit_stats],
            "reliability_analysis": self.reliability_analysis.to_dict(),
            "dimensionality_analysis": self.dimensionality_analysis.to_dict(),
            "dif_analyses": [dif.to_dict() for dif in self.dif_analyses],
            "overall_status": self.overall_status.value,
            "recommendations": self.recommendations,
            "summary_metrics": self.summary_metrics,
            "validation_checks": self.validation_checks,
        }


class IRTCalibrationService:
    """Comprehensive IRT calibration and validation service"""

    def __init__(self):
        self.irt_service = IRTService()

        # Validation thresholds
        self.thresholds = {
            "outfit_mnsq_acceptable": (0.5, 1.5),
            "infit_mnsq_acceptable": (0.5, 1.5),
            "outfit_zstd_acceptable": (-2.0, 2.0),
            "infit_zstd_acceptable": (-2.0, 2.0),
            "point_biserial_min": 0.2,
            "reliability_excellent": 0.9,
            "reliability_good": 0.8,
            "reliability_acceptable": 0.7,
            "unidimensionality_min": 0.8,
            "dif_effect_size_min": 0.05,
            "dif_p_threshold": 0.01,
        }

        logger.info("IRT Calibration Service initialized")

    async def comprehensive_calibration(
        self,
        responses: list[IRTResponse],
        model: IRTModel,
        estimation_method: EstimationMethod = EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD,
        item_metadata: list[dict[str, Any]] | None = None,
        person_metadata: list[dict[str, Any]] | None = None,
        perform_dif: bool = True,
        dif_grouping_variables: list[str] | None = None,
    ) -> CalibrationReport:
        """Perform comprehensive IRT calibration with full validation"""
        try:
            start_time = datetime.utcnow()
            calibration_id = f"cal_{start_time.strftime('%Y%m%d_%H%M%S')}"

            logger.info(f"Starting comprehensive calibration {calibration_id}")

            # Step 1: Calibrate IRT model
            calibration_result = await self.irt_service.calibrate_irt_model(
                responses, model, estimation_method
            )

            if not calibration_result.convergence:
                logger.warning(f"Calibration did not converge for {calibration_id}")

            # Step 2: Item fit analysis
            item_fit_stats = await self.analyze_item_fit(
                responses, calibration_result.items, calibration_result.persons
            )

            # Step 3: Person fit analysis
            person_fit_stats = await self.analyze_person_fit(
                responses, calibration_result.items, calibration_result.persons
            )

            # Step 4: Reliability analysis
            reliability_analysis = await self.analyze_reliability(
                responses, calibration_result.items, calibration_result.persons
            )

            # Step 5: Dimensionality analysis
            dimensionality_analysis = await self.analyze_dimensionality(
                responses, calibration_result.persons
            )

            # Step 6: DIF analysis (if requested)
            dif_analyses = []
            if perform_dif and person_metadata and dif_grouping_variables:
                for grouping_var in dif_grouping_variables:
                    dif_results = await self.analyze_differential_item_functioning(
                        responses,
                        calibration_result.items,
                        calibration_result.persons,
                        person_metadata,
                        grouping_var,
                    )
                    dif_analyses.extend(dif_results)

            # Step 7: Generate overall assessment and recommendations
            overall_status, recommendations = await self.generate_overall_assessment(
                item_fit_stats,
                person_fit_stats,
                reliability_analysis,
                dimensionality_analysis,
                dif_analyses,
            )

            # Step 8: Create summary metrics
            summary_metrics = await self.create_summary_metrics(
                calibration_result,
                item_fit_stats,
                person_fit_stats,
                reliability_analysis,
                dimensionality_analysis,
            )

            # Step 9: Perform validation checks
            validation_checks = await self.perform_validation_checks(
                item_fit_stats,
                person_fit_stats,
                reliability_analysis,
                dimensionality_analysis,
                dif_analyses,
            )

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            report = CalibrationReport(
                calibration_id=calibration_id,
                timestamp=start_time,
                model=model,
                sample_size=len(calibration_result.persons),
                item_count=len(calibration_result.items),
                item_fit_stats=item_fit_stats,
                person_fit_stats=person_fit_stats,
                reliability_analysis=reliability_analysis,
                dimensionality_analysis=dimensionality_analysis,
                dif_analyses=dif_analyses,
                overall_status=overall_status,
                recommendations=recommendations,
                summary_metrics=summary_metrics,
                validation_checks=validation_checks,
            )

            logger.info(
                f"Comprehensive calibration {calibration_id} completed in {processing_time:.2f}s"
            )
            return report

        except Exception as e:
            logger.error(f"Comprehensive calibration failed: {e!s}")
            raise

    async def analyze_item_fit(
        self,
        responses: list[IRTResponse],
        items: list[IRTItem],
        persons: list[IRTPerson],
    ) -> list[ItemFitStatistics]:
        """Analyze item fit statistics"""
        try:
            item_fit_stats = []

            # Create response matrix and mapping
            person_ids = [p.person_id for p in persons]
            item_ids = [i.item_id for i in items]
            person_idx = {pid: i for i, pid in enumerate(person_ids)}
            item_idx = {iid: i for i, iid in enumerate(item_ids)}

            response_matrix = np.full((len(persons), len(items)), np.nan)
            for response in responses:
                if response.person_id in person_idx and response.item_id in item_idx:
                    p_idx = person_idx[response.person_id]
                    i_idx = item_idx[response.item_id]
                    response_matrix[p_idx, i_idx] = response.response

            # Calculate fit statistics for each item
            for i, item in enumerate(items):
                # Get valid responses for this item
                valid_mask = ~np.isnan(response_matrix[:, i])
                if not valid_mask.any():
                    continue

                item_responses = response_matrix[valid_mask, i]
                item_abilities = [
                    persons[p_idx].ability for p_idx in np.where(valid_mask)[0]
                ]

                # Calculate expected values and residuals
                expected_values = []
                standardized_residuals = []

                for ability in item_abilities:
                    p_expected = self.irt_service.probability_of_correct_response(
                        ability, item
                    )
                    expected_values.append(p_expected)

                # Calculate fit statistics
                outfit_mnsq, infit_mnsq = self._calculate_item_fit_statistics(
                    item_responses, expected_values
                )

                outfit_zstd, infit_zstd = self._calculate_item_fit_z_scores(
                    outfit_mnsq, infit_mnsq, len(item_responses)
                )

                # Calculate correlation statistics
                point_biserial = self._calculate_point_biserial(
                    item_responses, item_abilities
                )
                biserial = self._calculate_biserial_correlation(
                    point_biserial, item_responses
                )
                item_total_correlation = self._calculate_item_total_correlation(
                    item_responses, response_matrix[valid_mask, :]
                )

                # Determine status and interpretation
                status, interpretation = self._evaluate_item_fit(
                    outfit_mnsq,
                    infit_mnsq,
                    outfit_zstd,
                    infit_zstd,
                    point_biserial,
                    item_total_correlation,
                )

                item_stat = ItemFitStatistics(
                    item_id=item.item_id,
                    outfit_mnsq=outfit_mnsq,
                    infit_mnsq=infit_mnsq,
                    outfit_zstd=outfit_zstd,
                    infit_zstd=infit_zstd,
                    point_biserial=point_biserial,
                    biserial=biserial,
                    item_total_correlation=item_total_correlation,
                    status=status,
                    interpretation=interpretation,
                )

                item_fit_stats.append(item_stat)

            return item_fit_stats

        except Exception as e:
            logger.error(f"Item fit analysis failed: {e!s}")
            return []

    async def analyze_person_fit(
        self,
        responses: list[IRTResponse],
        items: list[IRTItem],
        persons: list[IRTPerson],
    ) -> list[PersonFitStatistics]:
        """Analyze person fit statistics"""
        try:
            person_fit_stats = []

            # Create response matrix
            person_ids = [p.person_id for p in persons]
            item_ids = [i.item_id for i in items]
            person_idx = {pid: i for i, pid in enumerate(person_ids)}
            item_idx = {iid: i for i, iid in enumerate(item_ids)}

            response_matrix = np.full((len(persons), len(items)), np.nan)
            for response in responses:
                if response.person_id in person_idx and response.item_id in item_idx:
                    p_idx = person_idx[response.person_id]
                    i_idx = item_idx[response.item_id]
                    response_matrix[p_idx, i_idx] = response.response

            # Calculate fit statistics for each person
            for person in persons:
                p_idx = person_idx[person.person_id]
                person_responses = response_matrix[p_idx, :]
                valid_mask = ~np.isnan(person_responses)

                if not valid_mask.any() or np.sum(valid_mask) < 3:
                    continue

                valid_responses = person_responses[valid_mask]
                valid_items = [items[i] for i in np.where(valid_mask)[0]]

                # Calculate expected values
                expected_values = []
                for item in valid_items:
                    p_expected = self.irt_service.probability_of_correct_response(
                        person.ability, item
                    )
                    expected_values.append(p_expected)

                # Calculate fit statistics
                outfit_mnsq, infit_mnsq = self._calculate_person_fit_statistics(
                    valid_responses, expected_values
                )

                outfit_zstd, infit_zstd = self._calculate_person_fit_z_scores(
                    outfit_mnsq, infit_mnsq, len(valid_responses)
                )

                # Determine status and interpretation
                status, interpretation = self._evaluate_person_fit(
                    outfit_mnsq, infit_mnsq, outfit_zstd, infit_zstd
                )

                person_stat = PersonFitStatistics(
                    person_id=person.person_id,
                    outfit_mnsq=outfit_mnsq,
                    infit_mnsq=infit_mnsq,
                    outfit_zstd=outfit_zstd,
                    infit_zstd=infit_zstd,
                    pattern_score=int(np.nansum(person_responses)),
                    ability=person.ability,
                    standard_error=person.standard_error,
                    status=status,
                    interpretation=interpretation,
                )

                person_fit_stats.append(person_stat)

            return person_fit_stats

        except Exception as e:
            logger.error(f"Person fit analysis failed: {e!s}")
            return []

    async def analyze_reliability(
        self,
        responses: list[IRTResponse],
        items: list[IRTItem],
        persons: list[IRTPerson],
    ) -> ReliabilityAnalysis:
        """Analyze test reliability"""
        try:
            # Create response matrix
            person_ids = [p.person_id for p in persons]
            item_ids = [i.item_id for i in items]
            person_idx = {pid: i for i, pid in enumerate(person_ids)}
            item_idx = {iid: i for i, iid in enumerate(item_ids)}

            response_matrix = np.full((len(persons), len(items)), np.nan)
            for response in responses:
                if response.person_id in person_idx and response.item_id in item_idx:
                    p_idx = person_idx[response.person_id]
                    i_idx = item_idx[response.item_id]
                    response_matrix[p_idx, i_idx] = response.response

            # Remove persons with missing data
            valid_person_mask = ~np.isnan(response_matrix).any(axis=1)
            valid_responses = response_matrix[valid_person_mask, :]

            if len(valid_responses) < 30:  # Need sufficient sample for reliability
                return ReliabilityAnalysis(
                    cronbach_alpha=0.0,
                    mcdonalds_omega=0.0,
                    test_reliability=0.0,
                    split_half_reliability=0.0,
                    stratified_alpha=0.0,
                    sem=float("inf"),
                    interpretation="Insufficient sample for reliability analysis",
                    status=CalibrationStatus.FAILED,
                )

            # Calculate Cronbach's Alpha
            cronbach_alpha = self._calculate_cronbach_alpha(valid_responses)

            # Calculate McDonald's Omega
            mcdonalds_omega = self._calculate_mcdonalds_omega(valid_responses)

            # Calculate test reliability from IRT
            test_reliability = self._calculate_irt_reliability(items, persons)

            # Calculate split-half reliability
            split_half_reliability = self._calculate_split_half_reliability(
                valid_responses
            )

            # Calculate stratified alpha (if we have item groupings)
            stratified_alpha = self._calculate_stratified_alpha(valid_responses)

            # Calculate Standard Error of Measurement
            sem = self._calculate_sem(test_reliability)

            # Determine interpretation and status
            interpretation, status = self._interpret_reliability(cronbach_alpha)

            return ReliabilityAnalysis(
                cronbach_alpha=cronbach_alpha,
                mcdonalds_omega=mcdonalds_omega,
                test_reliability=test_reliability,
                split_half_reliability=split_half_reliability,
                stratified_alpha=stratified_alpha,
                sem=sem,
                interpretation=interpretation,
                status=status,
            )

        except Exception as e:
            logger.error(f"Reliability analysis failed: {e!s}")
            return ReliabilityAnalysis(
                cronbach_alpha=0.0,
                mcdonalds_omega=0.0,
                test_reliability=0.0,
                split_half_reliability=0.0,
                stratified_alpha=0.0,
                sem=float("inf"),
                interpretation=f"Error: {e!s}",
                status=CalibrationStatus.FAILED,
            )

    async def analyze_dimensionality(
        self, responses: list[IRTResponse], persons: list[IRTPerson]
    ) -> DimensionalityAnalysis:
        """Analyze test dimensionality"""
        try:
            # Create response matrix
            person_ids = [p.person_id for p in persons]
            item_ids = list(set(r.item_id for r in responses))
            person_idx = {pid: i for i, pid in enumerate(person_ids)}
            item_idx = {iid: i for i, iid in enumerate(item_ids)}

            response_matrix = np.full((len(persons), len(item_ids)), 0.0)
            for response in responses:
                if response.person_id in person_idx and response.item_id in item_idx:
                    p_idx = person_idx[response.person_id]
                    i_idx = item_idx[response.item_id]
                    response_matrix[p_idx, i_idx] = response.response

            # Remove persons with all zeros or all ones
            person_sums = response_matrix.sum(axis=1)
            valid_mask = (person_sums > 0) & (person_sums < len(item_ids))
            valid_responses = response_matrix[valid_mask, :]

            if len(valid_responses) < 30:
                return DimensionalityAnalysis(
                    eigenvalues=[],
                    variance_explained=[],
                    parallel_analysis=[],
                    kaiser_criterion=0,
                    scree_plot="",
                    factor_structure=[],
                    unidimensionality_score=0.0,
                    interpretation="Insufficient sample for dimensionality analysis",
                    status=CalibrationStatus.FAILED,
                )

            # Perform factor analysis
            eigenvalues = self._calculate_eigenvalues(valid_responses)
            variance_explained = self._calculate_variance_explained(eigenvalues)
            parallel_analysis = self._perform_parallel_analysis(valid_responses)

            # Determine number of factors (Kaiser criterion)
            kaiser_criterion = sum(1 for eigenval in eigenvalues if eigenval > 1.0)

            # Create scree plot
            scree_plot = self._create_scree_plot(eigenvalues, parallel_analysis)

            # Calculate factor structure
            factor_structure = self._calculate_factor_structure(
                valid_responses, kaiser_criterion
            )

            # Calculate unidimensionality score
            unidimensionality_score = self._calculate_unidimensionality_score(
                eigenvalues, variance_explained, kaiser_criterion
            )

            # Determine interpretation and status
            interpretation, status = self._interpret_dimensionality(
                unidimensionality_score, kaiser_criterion, eigenvalues
            )

            return DimensionalityAnalysis(
                eigenvalues=eigenvalues.tolist(),
                variance_explained=variance_explained,
                parallel_analysis=parallel_analysis,
                kaiser_criterion=kaiser_criterion,
                scree_plot=scree_plot,
                factor_structure=factor_structure,
                unidimensionality_score=unidimensionality_score,
                interpretation=interpretation,
                status=status,
            )

        except Exception as e:
            logger.error(f"Dimensionality analysis failed: {e!s}")
            return DimensionalityAnalysis(
                eigenvalues=[],
                variance_explained=[],
                parallel_analysis=[],
                kaiser_criterion=0,
                scree_plot="",
                factor_structure=[],
                unidimensionality_score=0.0,
                interpretation=f"Error: {e!s}",
                status=CalibrationStatus.FAILED,
            )

    async def analyze_differential_item_functioning(
        self,
        responses: list[IRTResponse],
        items: list[IRTItem],
        persons: list[IRTPerson],
        person_metadata: list[dict[str, Any]],
        grouping_variable: str,
    ) -> list[DIFAnalysis]:
        """Analyze Differential Item Functioning"""
        try:
            dif_analyses = []

            # Create person metadata mapping
            person_metadata_map = {p.person_id: p for p in person_metadata}

            # Group persons by the grouping variable
            groups = defaultdict(list)
            for person in persons:
                if person.person_id in person_metadata_map:
                    metadata = person_metadata_map[person.person_id]
                    if grouping_variable in metadata:
                        groups[metadata[grouping_variable]].append(person)

            if len(groups) != 2:
                logger.warning(
                    f"DIF analysis requires exactly 2 groups for {grouping_variable}"
                )
                return []

            group_names = list(groups.keys())
            group1 = groups[group_names[0]]
            group2 = groups[group_names[1]]

            # Analyze DIF for each item
            for item in items:
                try:
                    dif_result = await self._analyze_item_dif(
                        item,
                        responses,
                        group1,
                        group2,
                        group_names[0],
                        group_names[1],
                        grouping_variable,
                    )
                    if dif_result:
                        dif_analyses.append(dif_result)
                except Exception as e:
                    logger.error(f"DIF analysis failed for item {item.item_id}: {e!s}")
                    continue

            return dif_analyses

        except Exception as e:
            logger.error(f"DIF analysis failed: {e!s}")
            return []

    async def _analyze_item_dif(
        self,
        item: IRTItem,
        responses: list[IRTResponse],
        group1: list[IRTPerson],
        group2: list[IRTPerson],
        group1_name: str,
        group2_name: str,
        grouping_variable: str,
    ) -> DIFAnalysis | None:
        """Analyze DIF for a specific item"""
        try:
            # Get responses for this item by group
            group1_person_ids = {p.person_id for p in group1}
            group2_person_ids = {p.person_id for p in group2}

            group1_responses = [
                r.response
                for r in responses
                if r.item_id == item.item_id and r.person_id in group1_person_ids
            ]
            group2_responses = [
                r.response
                for r in responses
                if r.item_id == item.item_id and r.person_id in group2_person_ids
            ]

            if len(group1_responses) < 10 or len(group2_responses) < 10:
                return None  # Insufficient sample size

            # Calculate proportions
            p1 = np.mean(group1_responses)
            p2 = np.mean(group2_responses)

            # Calculate effect size (Cohen's h)
            effect_size = 2 * (math.asin(math.sqrt(p1)) - math.asin(math.sqrt(p2)))

            # Perform Mantel-Haenszel chi-square test
            mh_chi2, mh_p = self._mantel_haenszel_test(
                group1_responses, group2_responses
            )

            # Calculate Delta statistics
            delta_difficulty = p2 - p1
            delta_discrimination = (
                0.0  # Would need calibration for each group to calculate
            )

            # Determine significance and interpretation
            is_significant = mh_p < self.thresholds["dif_p_threshold"]
            is_large_effect = abs(effect_size) > self.thresholds["dif_effect_size_min"]

            if is_significant and is_large_effect:
                status = CalibrationStatus.QUESTIONABLE
                interpretation = f"Significant DIF detected: {group1_name} ({p1:.3f}) vs {group2_name} ({p2:.3f})"
            else:
                status = CalibrationStatus.ACCEPTABLE
                interpretation = "No significant DIF detected"

            return DIFAnalysis(
                item_id=item.item_id,
                group_type=grouping_variable,
                group1_name=group1_name,
                group2_name=group2_name,
                effect_size=effect_size,
                p_value=mh_p,
                delta_difficulty=delta_difficulty,
                delta_discrimination=delta_discrimination,
                mantel_haenszel_chi2=mh_chi2,
                mantel_haenszel_p=mh_p,
                status=status,
                interpretation=interpretation,
            )

        except Exception as e:
            logger.error(f"Item DIF analysis failed: {e!s}")
            return None

    # Helper methods for fit statistics

    def _calculate_item_fit_statistics(
        self, observed_responses: np.ndarray, expected_probabilities: list[float]
    ) -> tuple[float, float]:
        """Calculate outfit and infit mean square statistics"""
        try:
            outfit_sum = 0.0
            infit_sum = 0.0
            weight_sum = 0.0

            for i, (observed, expected) in enumerate(
                zip(observed_responses, expected_probabilities)
            ):
                if 0 < expected < 1:  # Avoid division by zero
                    standardized_residual = (observed - expected) / math.sqrt(
                        expected * (1 - expected)
                    )
                    outfit_sum += standardized_residual**2
                    infit_sum += expected * standardized_residual**2
                    weight_sum += expected

            outfit_mnsq = outfit_sum / len(observed_responses)
            infit_mnsq = infit_sum / weight_sum if weight_sum > 0 else float("inf")

            return outfit_mnsq, infit_mnsq

        except Exception as e:
            logger.error(f"Item fit statistics calculation failed: {e!s}")
            return 1.0, 1.0

    def _calculate_person_fit_statistics(
        self, observed_responses: np.ndarray, expected_probabilities: list[float]
    ) -> tuple[float, float]:
        """Calculate outfit and infit mean square for person"""
        return self._calculate_item_fit_statistics(
            observed_responses, expected_probabilities
        )

    def _calculate_item_fit_z_scores(
        self, outfit_mnsq: float, infit_mnsq: float, sample_size: int
    ) -> tuple[float, float]:
        """Calculate z-scores for fit statistics"""
        try:
            # Approximate standard errors (simplified)
            outfit_se = math.sqrt(2 / sample_size)
            infit_se = math.sqrt(2 / sample_size)

            outfit_zstd = (outfit_mnsq - 1.0) / outfit_se
            infit_zstd = (infit_mnsq - 1.0) / infit_se

            return outfit_zstd, infit_zstd

        except Exception:
            return 0.0, 0.0

    def _calculate_person_fit_z_scores(
        self, outfit_mnsq: float, infit_mnsq: float, item_count: int
    ) -> tuple[float, float]:
        """Calculate z-scores for person fit statistics"""
        return self._calculate_item_fit_z_scores(outfit_mnsq, infit_mnsq, item_count)

    def _calculate_point_biserial(
        self, item_responses: np.ndarray, abilities: list[float]
    ) -> float:
        """Calculate point-biserial correlation"""
        try:
            if len(set(item_responses)) < 2:
                return 0.0

            item_corr = np.corrcoef(item_responses, abilities)[0, 1]
            return item_corr if not np.isnan(item_corr) else 0.0

        except Exception:
            return 0.0

    def _calculate_biserial_correlation(
        self, point_biserial: float, item_responses: np.ndarray
    ) -> float:
        """Convert point-biserial to biserial correlation"""
        try:
            p = np.mean(item_responses)
            if 0 < p < 1:
                y = stats.norm.ppf(p)  # Inverse normal CDF
                biserial = point_biserial * math.sqrt(p * (1 - p)) / stats.norm.pdf(y)
                return biserial if not np.isnan(biserial) else 0.0
            return 0.0

        except Exception:
            return 0.0

    def _calculate_item_total_correlation(
        self, item_responses: np.ndarray, person_responses: np.ndarray
    ) -> float:
        """Calculate item-total correlation"""
        try:
            total_scores = np.nansum(person_responses, axis=1)
            if len(set(item_responses)) < 2 or len(set(total_scores)) < 2:
                return 0.0

            correlation = np.corrcoef(item_responses, total_scores)[0, 1]
            return correlation if not np.isnan(correlation) else 0.0

        except Exception:
            return 0.0

    def _evaluate_item_fit(
        self,
        outfit_mnsq: float,
        infit_mnsq: float,
        outfit_zstd: float,
        infit_zstd: float,
        point_biserial: float,
        item_total_correlation: float,
    ) -> tuple[CalibrationStatus, str]:
        """Evaluate item fit and determine status"""
        try:
            issues = []

            # Check fit statistics
            outfit_low, outfit_high = self.thresholds["outfit_mnsq_acceptable"]
            infit_low, infit_high = self.thresholds["infit_mnsq_acceptable"]

            if outfit_mnsq < outfit_low or outfit_mnsq > outfit_high:
                issues.append("Outfit MNSQ outside acceptable range")
            if infit_mnsq < infit_low or infit_mnsq > infit_high:
                issues.append("Infit MNSQ outside acceptable range")

            # Check z-scores
            zstd_low, zstd_high = self.thresholds["outfit_zstd_acceptable"]
            if abs(outfit_zstd) > zstd_high:
                issues.append("Outfit Z-score extreme")
            if abs(infit_zstd) > zstd_high:
                issues.append("Infit Z-score extreme")

            # Check correlations
            if point_biserial < self.thresholds["point_biserial_min"]:
                issues.append("Low point-biserial correlation")

            if item_total_correlation < self.thresholds["point_biserial_min"]:
                issues.append("Low item-total correlation")

            # Determine status
            if not issues:
                status = CalibrationStatus.EXCELLENT
                interpretation = "Item shows excellent fit"
            elif len(issues) <= 2:
                status = CalibrationStatus.ACCEPTABLE
                interpretation = f"Item shows acceptable fit: {', '.join(issues)}"
            elif len(issues) <= 4:
                status = CalibrationStatus.QUESTIONABLE
                interpretation = f"Item shows questionable fit: {', '.join(issues)}"
            else:
                status = CalibrationStatus.POOR
                interpretation = f"Item shows poor fit: {', '.join(issues)}"

            return status, interpretation

        except Exception as e:
            logger.error(f"Item fit evaluation failed: {e!s}")
            return CalibrationStatus.FAILED, f"Error evaluating fit: {e!s}"

    def _evaluate_person_fit(
        self,
        outfit_mnsq: float,
        infit_mnsq: float,
        outfit_zstd: float,
        infit_zstd: float,
    ) -> tuple[CalibrationStatus, str]:
        """Evaluate person fit and determine status"""
        try:
            issues = []

            # Check fit statistics
            outfit_low, outfit_high = self.thresholds["outfit_mnsq_acceptable"]
            infit_low, infit_high = self.thresholds["infit_mnsq_acceptable"]

            if outfit_mnsq < outfit_low or outfit_mnsq > outfit_high:
                issues.append("Outfit MNSQ outside acceptable range")
            if infit_mnsq < infit_low or infit_mnsq > infit_high:
                issues.append("Infit MNSQ outside acceptable range")

            # Check z-scores
            zstd_low, zstd_high = self.thresholds["outfit_zstd_acceptable"]
            if abs(outfit_zstd) > zstd_high:
                issues.append("Outfit Z-score extreme")
            if abs(infit_zstd) > zstd_high:
                issues.append("Infit Z-score extreme")

            # Determine status
            if not issues:
                status = CalibrationStatus.EXCELLENT
                interpretation = "Response pattern shows excellent fit"
            elif len(issues) <= 1:
                status = CalibrationStatus.ACCEPTABLE
                interpretation = (
                    f"Response pattern shows acceptable fit: {', '.join(issues)}"
                )
            elif len(issues) <= 2:
                status = CalibrationStatus.QUESTIONABLE
                interpretation = (
                    f"Response pattern shows questionable fit: {', '.join(issues)}"
                )
            else:
                status = CalibrationStatus.POOR
                interpretation = f"Response pattern shows poor fit: {', '.join(issues)}"

            return status, interpretation

        except Exception as e:
            logger.error(f"Person fit evaluation failed: {e!s}")
            return CalibrationStatus.FAILED, f"Error evaluating fit: {e!s}"

    # Reliability calculation methods

    def _calculate_cronbach_alpha(self, response_matrix: np.ndarray) -> float:
        """Calculate Cronbach's Alpha"""
        try:
            n_items = response_matrix.shape[1]
            item_variances = np.var(response_matrix, axis=0, ddof=1)
            total_scores = np.sum(response_matrix, axis=1)
            total_variance = np.var(total_scores, ddof=1)

            if total_variance == 0:
                return 0.0

            alpha = (n_items / (n_items - 1)) * (
                1 - np.sum(item_variances) / total_variance
            )
            return max(0.0, min(1.0, alpha))

        except Exception:
            return 0.0

    def _calculate_mcdonalds_omega(self, response_matrix: np.ndarray) -> float:
        """Calculate McDonald's Omega (simplified)"""
        try:
            # For simplified implementation, use Cronbach's alpha as approximation
            # Full implementation requires factor analysis
            return self._calculate_cronbach_alpha(response_matrix)

        except Exception:
            return 0.0

    def _calculate_irt_reliability(
        self, items: list[IRTItem], persons: list[IRTPerson]
    ) -> float:
        """Calculate reliability from IRT parameters"""
        try:
            # Calculate average information across ability range
            ability_range = np.linspace(-2, 2, 21)
            information_values = [
                self.irt_service.test_information_function(theta, items)
                for theta in ability_range
            ]

            avg_information = np.mean(information_values)
            reliability = avg_information / (avg_information + 1)

            return max(0.0, min(1.0, reliability))

        except Exception:
            return 0.0

    def _calculate_split_half_reliability(self, response_matrix: np.ndarray) -> float:
        """Calculate split-half reliability"""
        try:
            n_items = response_matrix.shape[1]
            if n_items < 2:
                return 0.0

            # Split items into two halves
            mid = n_items // 2
            half1 = response_matrix[:, :mid]
            half2 = response_matrix[:, mid:]

            # Calculate scores for each half
            scores1 = np.nansum(half1, axis=1)
            scores2 = np.nansum(half2, axis=1)

            # Calculate correlation
            correlation = np.corrcoef(scores1, scores2)[0, 1]

            if np.isnan(correlation):
                return 0.0

            # Spearman-Brown prophecy formula
            spearman_brown = (2 * correlation) / (1 + correlation)
            return max(0.0, min(1.0, spearman_brown))

        except Exception:
            return 0.0

    def _calculate_stratified_alpha(self, response_matrix: np.ndarray) -> float:
        """Calculate stratified alpha (simplified)"""
        # For now, return Cronbach's alpha
        return self._calculate_cronbach_alpha(response_matrix)

    def _calculate_sem(self, reliability: float) -> float:
        """Calculate Standard Error of Measurement"""
        try:
            if reliability <= 0:
                return float("inf")
            return math.sqrt(1 - reliability)

        except Exception:
            return float("inf")

    def _interpret_reliability(
        self, cronbach_alpha: float
    ) -> tuple[str, CalibrationStatus]:
        """Interpret reliability coefficient"""
        if cronbach_alpha >= self.thresholds["reliability_excellent"]:
            return "Excellent internal consistency", CalibrationStatus.EXCELLENT
        if cronbach_alpha >= self.thresholds["reliability_good"]:
            return "Good internal consistency", CalibrationStatus.GOOD
        if cronbach_alpha >= self.thresholds["reliability_acceptable"]:
            return "Acceptable internal consistency", CalibrationStatus.ACCEPTABLE
        return (
            "Poor internal consistency - review test items",
            CalibrationStatus.QUESTIONABLE,
        )

    # Dimensionality analysis methods

    def _calculate_eigenvalues(self, response_matrix: np.ndarray) -> np.ndarray:
        """Calculate eigenvalues from correlation matrix"""
        try:
            # Calculate correlation matrix
            corr_matrix = np.corrcoef(response_matrix.T)

            # Handle NaN values
            corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

            # Calculate eigenvalues
            eigenvalues = np.linalg.eigvals(corr_matrix)

            # Sort in descending order
            eigenvalues = np.sort(eigenvalues)[::-1]

            return eigenvalues

        except Exception:
            return np.array([])

    def _calculate_variance_explained(self, eigenvalues: np.ndarray) -> np.ndarray:
        """Calculate variance explained by each factor"""
        try:
            total_variance = np.sum(eigenvalues)
            if total_variance == 0:
                return np.zeros_like(eigenvalues)
            return eigenvalues / total_variance

        except Exception:
            return np.array([])

    def _perform_parallel_analysis(self, response_matrix: np.ndarray) -> list[float]:
        """Perform parallel analysis for factor retention"""
        try:
            n_persons, n_items = response_matrix.shape

            # Generate random data with same dimensions
            random_data = np.random.random((n_persons, n_items))

            # Calculate eigenvalues for random data
            random_eigenvalues = self._calculate_eigenvalues(random_data)

            return random_eigenvalues.tolist()

        except Exception:
            return []

    def _create_scree_plot(
        self, eigenvalues: np.ndarray, parallel_analysis: list[float]
    ) -> str:
        """Create scree plot (simplified - return base64 string)"""
        try:
            # For now, return empty string - in production, this would create an actual plot
            return ""

        except Exception:
            return ""

    def _calculate_factor_structure(
        self, response_matrix: np.ndarray, n_factors: int
    ) -> list[list[float]]:
        """Calculate factor structure matrix"""
        try:
            if n_factors == 0:
                return []

            # Simplified factor analysis - in production, use proper factor analysis
            corr_matrix = np.corrcoef(response_matrix.T)
            eigenvalues, eigenvectors = np.linalg.eigh(corr_matrix)

            # Sort by eigenvalue magnitude
            idx = np.argsort(np.abs(eigenvalues))[::-1]
            eigenvalues = eigenvalues[idx]
            eigenvectors = eigenvectors[:, idx]

            # Get factor loadings for top factors
            factor_loadings = eigenvectors[:, :n_factors]

            return factor_loadings.tolist()

        except Exception:
            return [[]]

    def _calculate_unidimensionality_score(
        self,
        eigenvalues: np.ndarray,
        variance_explained: np.ndarray,
        kaiser_criterion: int,
    ) -> float:
        """Calculate unidimensionality score"""
        try:
            # Multiple indicators of unidimensionality

            # 1. First eigenvalue ratio
            if len(eigenvalues) > 1:
                eigenvalue_ratio = eigenvalues[0] / eigenvalues[1]
            else:
                eigenvalue_ratio = 1.0

            # 2. Variance explained by first factor
            first_factor_variance = (
                variance_explained[0] if len(variance_explained) > 0 else 0.0
            )

            # 3. Kaiser criterion (should be 1 for unidimensional)
            kaiser_score = (
                1.0
                if kaiser_criterion == 1
                else max(0.0, 1.0 - (kaiser_criterion - 1) * 0.2)
            )

            # Combine scores (weighted average)
            unidimensionality_score = (
                eigenvalue_ratio * 0.3
                + first_factor_variance * 0.4
                + kaiser_score * 0.3
            )

            return max(0.0, min(1.0, unidimensionality_score))

        except Exception:
            return 0.0

    def _interpret_dimensionality(
        self,
        unidimensionality_score: float,
        kaiser_criterion: int,
        eigenvalues: np.ndarray,
    ) -> tuple[str, CalibrationStatus]:
        """Interpret dimensionality analysis results"""
        try:
            if unidimensionality_score >= self.thresholds["unidimensionality_min"]:
                if kaiser_criterion == 1:
                    return (
                        "Strong evidence of unidimensionality",
                        CalibrationStatus.EXCELLENT,
                    )
                return "Moderate evidence of unidimensionality", CalibrationStatus.GOOD
            if kaiser_criterion <= 2:
                return "Some multidimensionality detected", CalibrationStatus.ACCEPTABLE
            return (
                "Significant multidimensionality detected - consider test restructuring",
                CalibrationStatus.QUESTIONABLE,
            )

        except Exception:
            return "Error interpreting dimensionality", CalibrationStatus.FAILED

    # DIF analysis helper methods

    def _mantel_haenszel_test(
        self, group1_responses: list[int], group2_responses: list[int]
    ) -> tuple[float, float]:
        """Perform Mantel-Haenszel test for DIF"""
        try:
            # Create 2x2 table
            a = sum(group1_responses)  # Group 1 correct
            b = len(group1_responses) - a  # Group 1 incorrect
            c = sum(group2_responses)  # Group 2 correct
            d = len(group2_responses) - c  # Group 2 incorrect

            # Mantel-Haenszel chi-square statistic
            numerator = (a * d - b * c) ** 2
            denominator = (a + b) * (c + d) * (a + c) * (b + d)

            if denominator == 0:
                return 0.0, 1.0

            mh_chi2 = numerator / denominator
            mh_p = 1.0 - stats.chi2.cdf(mh_chi2, 1)

            return mh_chi2, mh_p

        except Exception:
            return 0.0, 1.0

    # Overall assessment methods

    async def generate_overall_assessment(
        self,
        item_fit_stats: list[ItemFitStatistics],
        person_fit_stats: list[PersonFitStatistics],
        reliability_analysis: ReliabilityAnalysis,
        dimensionality_analysis: DimensionalityAnalysis,
        dif_analyses: list[DIFAnalysis],
    ) -> tuple[CalibrationStatus, list[str]]:
        """Generate overall assessment and recommendations"""
        try:
            recommendations = []
            status_scores = []

            # Evaluate item fit
            problematic_items = sum(
                1
                for stat in item_fit_stats
                if stat.status
                in [CalibrationStatus.QUESTIONABLE, CalibrationStatus.POOR]
            )
            if problematic_items > 0:
                recommendations.append(
                    f"Review {problematic_items} items with poor fit statistics"
                )
                status_scores.append(
                    0.7 if problematic_items / len(item_fit_stats) < 0.1 else 0.3
                )
            else:
                status_scores.append(0.9)

            # Evaluate person fit
            problematic_persons = sum(
                1
                for stat in person_fit_stats
                if stat.status
                in [CalibrationStatus.QUESTIONABLE, CalibrationStatus.POOR]
            )
            if problematic_persons > len(person_fit_stats) * 0.1:
                recommendations.append(
                    f"Consider review of {problematic_persons} respondents with unusual response patterns"
                )
                status_scores.append(0.6)
            else:
                status_scores.append(0.9)

            # Evaluate reliability
            if reliability_analysis.status == CalibrationStatus.EXCELLENT:
                status_scores.append(0.9)
            elif reliability_analysis.status == CalibrationStatus.GOOD:
                status_scores.append(0.8)
            elif reliability_analysis.status == CalibrationStatus.ACCEPTABLE:
                recommendations.append(
                    "Test reliability is acceptable but could be improved"
                )
                status_scores.append(0.7)
            else:
                recommendations.append(
                    "Test reliability is poor - consider item review"
                )
                status_scores.append(0.3)

            # Evaluate dimensionality
            if dimensionality_analysis.status == CalibrationStatus.EXCELLENT:
                status_scores.append(0.9)
            elif dimensionality_analysis.status == CalibrationStatus.GOOD:
                status_scores.append(0.8)
            elif dimensionality_analysis.status == CalibrationStatus.ACCEPTABLE:
                recommendations.append(
                    "Test appears mostly unidimensional but some secondary dimensions exist"
                )
                status_scores.append(0.7)
            else:
                recommendations.append(
                    "Test shows significant multidimensionality - consider factor analysis or test restructuring"
                )
                status_scores.append(0.3)

            # Evaluate DIF
            significant_dif = sum(
                1
                for dif in dif_analyses
                if dif.status
                in [CalibrationStatus.QUESTIONABLE, CalibrationStatus.POOR]
            )
            if significant_dif > 0:
                recommendations.append(
                    f"{significant_dif} items show significant differential item functioning"
                )
                status_scores.append(0.6)
            else:
                status_scores.append(0.9)

            # Determine overall status
            avg_score = np.mean(status_scores) if status_scores else 0.5

            if avg_score >= 0.85:
                overall_status = CalibrationStatus.EXCELLENT
                recommendations.insert(
                    0, "Excellent model calibration - test is ready for use"
                )
            elif avg_score >= 0.75:
                overall_status = CalibrationStatus.GOOD
                recommendations.insert(
                    0, "Good model calibration - minor improvements recommended"
                )
            elif avg_score >= 0.65:
                overall_status = CalibrationStatus.ACCEPTABLE
                recommendations.insert(
                    0, "Acceptable model calibration - several improvements needed"
                )
            else:
                overall_status = CalibrationStatus.QUESTIONABLE
                recommendations.insert(
                    0, "Questionable model calibration - significant revisions needed"
                )

            return overall_status, recommendations

        except Exception as e:
            logger.error(f"Overall assessment generation failed: {e!s}")
            return CalibrationStatus.FAILED, [f"Error generating assessment: {e!s}"]

    async def create_summary_metrics(
        self,
        calibration_result: IRTCalibrationResult,
        item_fit_stats: list[ItemFitStatistics],
        person_fit_stats: list[PersonFitStatistics],
        reliability_analysis: ReliabilityAnalysis,
        dimensionality_analysis: DimensionalityAnalysis,
    ) -> dict[str, float]:
        """Create summary metrics for the calibration"""
        try:
            metrics = {
                "convergence": 1.0 if calibration_result.convergence else 0.0,
                "log_likelihood": calibration_result.log_likelihood,
                "aic": calibration_result.aic,
                "bic": calibration_result.bic,
                "item_count": len(calibration_result.items),
                "person_count": len(calibration_result.persons),
                "sample_size": len(calibration_result.persons),
                "avg_item_discrimination": (
                    np.mean(
                        [
                            item.discrimination
                            for item in calibration_result.items
                            if item.discrimination is not None
                        ]
                    )
                    if any(item.discrimination for item in calibration_result.items)
                    else 0.0
                ),
                "avg_item_difficulty": np.mean(
                    [item.difficulty for item in calibration_result.items]
                ),
                "reliability_cronbach_alpha": reliability_analysis.cronbach_alpha,
                "reliability_mcdonalds_omega": reliability_analysis.mcdonalds_omega,
                "unidimensionality_score": dimensionality_analysis.unidimensionality_score,
                "percent_problematic_items": (
                    sum(
                        1
                        for stat in item_fit_stats
                        if stat.status
                        in [CalibrationStatus.QUESTIONABLE, CalibrationStatus.POOR]
                    )
                    / len(item_fit_stats)
                    if item_fit_stats
                    else 0.0
                ),
                "percent_problematic_persons": (
                    sum(
                        1
                        for stat in person_fit_stats
                        if stat.status
                        in [CalibrationStatus.QUESTIONABLE, CalibrationStatus.POOR]
                    )
                    / len(person_fit_stats)
                    if person_fit_stats
                    else 0.0
                ),
            }

            return metrics

        except Exception as e:
            logger.error(f"Summary metrics creation failed: {e!s}")
            return {}

    async def perform_validation_checks(
        self,
        item_fit_stats: list[ItemFitStatistics],
        person_fit_stats: list[PersonFitStatistics],
        reliability_analysis: ReliabilityAnalysis,
        dimensionality_analysis: DimensionalityAnalysis,
        dif_analyses: list[DIFAnalysis],
    ) -> dict[str, bool]:
        """Perform standard validation checks"""
        try:
            checks = {}

            # Item fit checks
            checks["item_fit_acceptable"] = (
                all(
                    stat.status
                    in [
                        CalibrationStatus.EXCELLENT,
                        CalibrationStatus.GOOD,
                        CalibrationStatus.ACCEPTABLE,
                    ]
                    for stat in item_fit_stats
                )
                if item_fit_stats
                else False
            )

            # Person fit checks
            checks["person_fit_acceptable"] = (
                all(
                    stat.status
                    in [
                        CalibrationStatus.EXCELLENT,
                        CalibrationStatus.GOOD,
                        CalibrationStatus.ACCEPTABLE,
                    ]
                    for stat in person_fit_stats
                )
                if person_fit_stats
                else False
            )

            # Reliability checks
            checks["reliability_acceptable"] = (
                reliability_analysis.cronbach_alpha
                >= self.thresholds["reliability_acceptable"]
            )

            # Dimensionality checks
            checks["unidimensionality_acceptable"] = (
                dimensionality_analysis.unidimensionality_score
                >= self.thresholds["unidimensionality_min"]
            )

            # DIF checks
            checks["no_significant_dif"] = (
                all(
                    dif.status
                    not in [CalibrationStatus.QUESTIONABLE, CalibrationStatus.POOR]
                    for dif in dif_analyses
                )
                if dif_analyses
                else True
            )

            return checks

        except Exception as e:
            logger.error(f"Validation checks failed: {e!s}")
            return {}

    def export_calibration_report(
        self, report: CalibrationReport, format: str = "json"
    ) -> str:
        """Export calibration report"""
        try:
            if format == "json":
                return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
            raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Report export failed: {e!s}")
            return ""


# Export the main service class
__all__ = [
    "CalibrationReport",
    "CalibrationStatus",
    "DIFAnalysis",
    "DimensionalityAnalysis",
    "IRTCalibrationService",
    "ItemFitStatistics",
    "PersonFitStatistics",
    "ReliabilityAnalysis",
    "ValidationMetric",
]
