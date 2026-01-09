"""
Item Response Theory (IRT) Service
Comprehensive implementation of IRT models for advanced psychometric analysis
including 1PL, 2PL, and 3PL models with parameter estimation and calibration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
import math
from typing import Any

import numpy as np
from scipy import optimize

logger = logging.getLogger(__name__)


class IRTModel(Enum):
    """Types of IRT models"""

    ONE_PL = "1PL"  # Rasch model - difficulty only
    TWO_PL = "2PL"  # Difficulty and discrimination
    THREE_PL = "3PL"  # Difficulty, discrimination, and guessing


class EstimationMethod(Enum):
    """Parameter estimation methods"""

    JOINT_MAXIMUM_LIKELIHOOD = "joint_ml"
    MARGINAL_MAXIMUM_LIKELIHOOD = "marginal_ml"
    BAYESIAN = "bayesian"
    EXPECTATION_MAXIMIZATION = "em"


@dataclass
class IRTItem:
    """IRT item parameters"""

    item_id: str
    model: IRTModel
    difficulty: float  # b parameter
    discrimination: float | None = None  # a parameter (2PL/3PL)
    guessing: float | None = None  # c parameter (3PL)
    standard_errors: dict[str, float] = field(default_factory=dict)
    fit_statistics: dict[str, float] = field(default_factory=dict)
    item_info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {
            "item_id": self.item_id,
            "model": self.model.value,
            "difficulty": self.difficulty,
            "standard_errors": self.standard_errors,
            "fit_statistics": self.fit_statistics,
            "item_info": self.item_info,
        }
        if self.discrimination is not None:
            result["discrimination"] = self.discrimination
        if self.guessing is not None:
            result["guessing"] = self.guessing
        return result


@dataclass
class IRTPerson:
    """Person ability parameters"""

    person_id: str
    ability: float  # theta parameter
    standard_error: float = 0.0
    pattern_score: int = 0  # Raw score
    reliability: float = 0.0
    response_pattern: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "ability": self.ability,
            "standard_error": self.standard_error,
            "pattern_score": self.pattern_score,
            "reliability": self.reliability,
            "response_pattern": self.response_pattern,
        }


@dataclass
class IRTResponse:
    """Individual response data"""

    person_id: str
    item_id: str
    response: int  # 0 or 1 for dichotomous items
    response_time: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "person_id": self.person_id,
            "item_id": self.item_id,
            "response": self.response,
            "response_time": self.response_time,
            "metadata": self.metadata,
        }


@dataclass
class IRTCalibrationResult:
    """Results of IRT calibration"""

    model: IRTModel
    items: list[IRTItem]
    persons: list[IRTPerson]
    log_likelihood: float
    aic: float  # Akaike Information Criterion
    bic: float  # Bayesian Information Criterion
    convergence: bool
    iterations: int
    calibration_time: float
    quality_metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model.value,
            "items": [item.to_dict() for item in self.items],
            "persons": [person.to_dict() for person in self.persons],
            "log_likelihood": self.log_likelihood,
            "aic": self.aic,
            "bic": self.bic,
            "convergence": self.convergence,
            "iterations": self.iterations,
            "calibration_time": self.calibration_time,
            "quality_metrics": self.quality_metrics,
        }


class IRTService:
    """Comprehensive IRT analysis service"""

    def __init__(self):
        # Configuration for estimation
        self.config = {
            "max_iterations": 1000,
            "tolerance": 1e-6,
            "min_discrimination": 0.1,
            "max_discrimination": 3.0,
            "min_difficulty": -4.0,
            "max_difficulty": 4.0,
            "min_guessing": 0.0,
            "max_guessing": 0.5,
            "ability_range": (-4.0, 4.0),
            "quadrature_points": 41,
        }

        # Cache for computed values
        self._likelihood_cache = {}
        self._information_cache = {}

        logger.info("IRT Service initialized")

    def probability_of_correct_response(self, ability: float, item: IRTItem) -> float:
        """Calculate probability of correct response given ability and item parameters"""
        try:
            if item.model == IRTModel.ONE_PL:
                # Rasch model: P(θ) = 1 / (1 + exp(-(θ - b)))
                exponent = ability - item.difficulty
                return 1.0 / (1.0 + math.exp(-exponent))

            if item.model == IRTModel.TWO_PL:
                # 2PL model: P(θ) = 1 / (1 + exp(-a(θ - b)))
                a = item.discrimination or 1.0
                exponent = a * (ability - item.difficulty)
                return 1.0 / (1.0 + math.exp(-exponent))

            if item.model == IRTModel.THREE_PL:
                # 3PL model: P(θ) = c + (1 - c) / (1 + exp(-a(θ - b)))
                a = item.discrimination or 1.0
                c = item.guessing or 0.0
                exponent = a * (ability - item.difficulty)
                return c + (1.0 - c) / (1.0 + math.exp(-exponent))

            raise ValueError(f"Unsupported IRT model: {item.model}")

        except Exception as e:
            logger.error(f"Probability calculation failed: {e!s}")
            return 0.5  # Default to 0.5 on error

    def information_function(self, ability: float, item: IRTItem) -> float:
        """Calculate information function for item at given ability"""
        try:
            p = self.probability_of_correct_response(ability, item)
            q = 1.0 - p

            if item.model == IRTModel.ONE_PL:
                return p * q

            if item.model == IRTModel.TWO_PL:
                a = item.discrimination or 1.0
                return (a**2) * p * q

            if item.model == IRTModel.THREE_PL:
                a = item.discrimination or 1.0
                c = item.guessing or 0.0
                p_star = (p - c) / (1.0 - c)  # Probability without guessing
                q_star = 1.0 - p_star
                return (a**2) * ((1.0 - c) ** 2) * p_star * q_star / (p**2)

            raise ValueError(f"Unsupported IRT model: {item.model}")

        except Exception as e:
            logger.error(f"Information function calculation failed: {e!s}")
            return 0.0

    def test_information_function(self, ability: float, items: list[IRTItem]) -> float:
        """Calculate total test information at given ability"""
        return sum(self.information_function(ability, item) for item in items)

    def standard_error_of_measurement(self, ability: float, items: list[IRTItem]) -> float:
        """Calculate standard error of measurement at given ability"""
        info = self.test_information_function(ability, items)
        return 1.0 / math.sqrt(info) if info > 0 else float("inf")

    async def calibrate_irt_model(
        self,
        responses: list[IRTResponse],
        model: IRTModel,
        method: EstimationMethod = EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD,
        initial_item_params: list[dict[str, float]] | None = None,
    ) -> IRTCalibrationResult:
        """Calibrate IRT model parameters"""
        try:
            start_time = datetime.utcnow()

            # Prepare data
            person_ids = list(set(r.person_id for r in responses))
            item_ids = list(set(r.item_id for r in responses))

            # Create response matrix
            response_matrix = self._create_response_matrix(responses, person_ids, item_ids)

            # Initialize item parameters
            items = self._initialize_items(item_ids, model, initial_item_params)

            # Estimate parameters based on method
            if method == EstimationMethod.MARGINAL_MAXIMUM_LIKELIHOOD:
                result = await self._estimate_mml(response_matrix, items, model)
            elif method == EstimationMethod.JOINT_MAXIMUM_LIKELIHOOD:
                result = await self._estimate_jml(response_matrix, items, model)
            elif method == EstimationMethod.EXPECTATION_MAXIMIZATION:
                result = await self._estimate_em(response_matrix, items, model)
            else:
                raise ValueError(f"Unsupported estimation method: {method}")

            # Estimate person abilities
            persons = await self._estimate_abilities(response_matrix, result.items)

            # Calculate model fit statistics
            log_likelihood = self._calculate_log_likelihood(response_matrix, result.items, persons)
            aic, bic = self._calculate_information_criteria(log_likelihood, result.items, persons)

            # Calculate quality metrics
            quality_metrics = await self._calculate_quality_metrics(
                response_matrix, result.items, persons
            )

            calibration_time = (datetime.utcnow() - start_time).total_seconds()

            calibration_result = IRTCalibrationResult(
                model=model,
                items=result.items,
                persons=persons,
                log_likelihood=log_likelihood,
                aic=aic,
                bic=bic,
                convergence=result.convergence,
                iterations=result.iterations,
                calibration_time=calibration_time,
                quality_metrics=quality_metrics,
            )

            logger.info(
                f"IRT calibration completed in {calibration_time:.2f}s for {len(persons)} persons, {len(items)} items"
            )
            return calibration_result

        except Exception as e:
            logger.error(f"IRT calibration failed: {e!s}")
            raise

    def _create_response_matrix(
        self, responses: list[IRTResponse], person_ids: list[str], item_ids: list[str]
    ) -> np.ndarray:
        """Create response matrix from response data"""
        try:
            # Create mapping dictionaries
            person_idx = {pid: i for i, pid in enumerate(person_ids)}
            item_idx = {iid: i for i, iid in enumerate(item_ids)}

            # Initialize matrix
            matrix = np.full((len(person_ids), len(item_ids)), np.nan)

            # Fill matrix with responses
            for response in responses:
                p_idx = person_idx[response.person_id]
                i_idx = item_idx[response.item_id]
                matrix[p_idx, i_idx] = response.response

            return matrix

        except Exception as e:
            logger.error(f"Response matrix creation failed: {e!s}")
            return np.array([])

    def _initialize_items(
        self,
        item_ids: list[str],
        model: IRTModel,
        initial_params: list[dict[str, float]] | None = None,
    ) -> list[IRTItem]:
        """Initialize item parameters"""
        try:
            items = []

            for i, item_id in enumerate(item_ids):
                # Use provided initial parameters or defaults
                if initial_params and i < len(initial_params):
                    params = initial_params[i]
                    difficulty = params.get("difficulty", 0.0)
                    discrimination = params.get("discrimination")
                    guessing = params.get("guessing")
                else:
                    difficulty = 0.0
                    discrimination = 1.0 if model in [IRTModel.TWO_PL, IRTModel.THREE_PL] else None
                    guessing = 0.0 if model == IRTModel.THREE_PL else None

                item = IRTItem(
                    item_id=item_id,
                    model=model,
                    difficulty=difficulty,
                    discrimination=discrimination,
                    guessing=guessing,
                )
                items.append(item)

            return items

        except Exception as e:
            logger.error(f"Item initialization failed: {e!s}")
            return []

    async def _estimate_mml(
        self, response_matrix: np.ndarray, items: list[IRTItem], model: IRTModel
    ) -> dict[str, Any]:
        """Marginal Maximum Likelihood estimation using EM algorithm"""
        try:
            n_persons, n_items = response_matrix.shape
            theta_points = np.linspace(
                *self.config["ability_range"], self.config["quadrature_points"]
            )
            theta_weights = np.exp(-0.5 * theta_points**2) / np.sqrt(2 * np.pi)
            theta_weights /= theta_weights.sum()  # Normalize

            iterations = 0
            prev_log_likelihood = -float("inf")
            convergence = False

            while iterations < self.config["max_iterations"] and not convergence:
                # E-step: Calculate posterior probabilities
                posterior_probs = np.zeros((n_persons, len(theta_points)))

                for p in range(n_persons):
                    for t, theta in enumerate(theta_points):
                        log_likelihood = 0.0
                        for i in range(n_items):
                            if not np.isnan(response_matrix[p, i]):
                                p_correct = self.probability_of_correct_response(theta, items[i])
                                if response_matrix[p, i] == 1:
                                    log_likelihood += np.log(p_correct)
                                else:
                                    log_likelihood += np.log(1.0 - p_correct)

                        posterior_probs[p, t] = np.exp(log_likelihood) * theta_weights[t]

                    # Normalize
                    posterior_probs[p, :] /= posterior_probs[p, :].sum() + 1e-10

                # M-step: Update item parameters
                for i in range(n_items):
                    # Get responses for this item
                    item_responses = response_matrix[:, i]
                    valid_indices = ~np.isnan(item_responses)

                    if not valid_indices.any():
                        continue

                    valid_responses = item_responses[valid_indices]
                    valid_posteriors = posterior_probs[valid_indices, :]

                    # Update parameters using numerical optimization
                    def negative_log_likelihood(params):
                        if model == IRTModel.ONE_PL:
                            b = params[0]
                            a, c = 1.0, 0.0
                        elif model == IRTModel.TWO_PL:
                            a, b = params
                            c = 0.0
                        else:  # THREE_PL
                            a, b, c = params

                        # Apply constraints
                        a = max(
                            self.config["min_discrimination"],
                            min(self.config["max_discrimination"], a),
                        )
                        b = max(
                            self.config["min_difficulty"], min(self.config["max_difficulty"], b)
                        )
                        c = max(self.config["min_guessing"], min(self.config["max_guessing"], c))

                        temp_item = IRTItem(
                            item_id=items[i].item_id,
                            model=model,
                            difficulty=b,
                            discrimination=a,
                            guessing=c,
                        )

                        nll = 0.0
                        for p_idx in range(len(valid_responses)):
                            for t_idx, theta in enumerate(theta_points):
                                p_correct = self.probability_of_correct_response(theta, temp_item)
                                response_prob = (
                                    p_correct if valid_responses[p_idx] == 1 else (1.0 - p_correct)
                                )
                                nll -= valid_posteriors[p_idx, t_idx] * np.log(
                                    response_prob + 1e-10
                                )

                        return nll

                    # Initial parameter guess
                    if model == IRTModel.ONE_PL:
                        initial_params = [items[i].difficulty]
                        bounds = [(self.config["min_difficulty"], self.config["max_difficulty"])]
                    elif model == IRTModel.TWO_PL:
                        initial_params = [items[i].discrimination or 1.0, items[i].difficulty]
                        bounds = [
                            (self.config["min_discrimination"], self.config["max_discrimination"]),
                            (self.config["min_difficulty"], self.config["max_difficulty"]),
                        ]
                    else:  # THREE_PL
                        initial_params = [
                            items[i].discrimination or 1.0,
                            items[i].difficulty,
                            items[i].guessing or 0.0,
                        ]
                        bounds = [
                            (self.config["min_discrimination"], self.config["max_discrimination"]),
                            (self.config["min_difficulty"], self.config["max_difficulty"]),
                            (self.config["min_guessing"], self.config["max_guessing"]),
                        ]

                    # Optimize parameters
                    result = optimize.minimize(
                        negative_log_likelihood, initial_params, method="L-BFGS-B", bounds=bounds
                    )

                    # Update item parameters
                    if model == IRTModel.ONE_PL:
                        items[i].difficulty = result.x[0]
                    elif model == IRTModel.TWO_PL:
                        items[i].discrimination = result.x[0]
                        items[i].difficulty = result.x[1]
                    else:  # THREE_PL
                        items[i].discrimination = result.x[0]
                        items[i].difficulty = result.x[1]
                        items[i].guessing = result.x[2]

                # Check convergence
                current_log_likelihood = self._calculate_marginal_log_likelihood(
                    response_matrix, items, theta_points, theta_weights
                )

                if abs(current_log_likelihood - prev_log_likelihood) < self.config["tolerance"]:
                    convergence = True

                prev_log_likelihood = current_log_likelihood
                iterations += 1

                if iterations % 10 == 0:
                    logger.debug(
                        f"MML iteration {iterations}: log_likelihood = {current_log_likelihood:.4f}"
                    )

            return {"items": items, "convergence": convergence, "iterations": iterations}

        except Exception as e:
            logger.error(f"MML estimation failed: {e!s}")
            return {"items": items, "convergence": False, "iterations": 0}

    async def _estimate_jml(
        self, response_matrix: np.ndarray, items: list[IRTItem], model: IRTModel
    ) -> dict[str, Any]:
        """Joint Maximum Likelihood estimation"""
        try:
            n_persons, n_items = response_matrix.shape

            # Initialize person abilities
            abilities = np.zeros(n_persons)

            iterations = 0
            convergence = False

            while iterations < self.config["max_iterations"] and not convergence:
                prev_params = self._extract_item_parameters(items)

                # Step 1: Update person abilities given item parameters
                for p in range(n_persons):

                    def negative_log_likelihood(theta):
                        nll = 0.0
                        for i in range(n_items):
                            if not np.isnan(response_matrix[p, i]):
                                p_correct = self.probability_of_correct_response(theta[0], items[i])
                                if response_matrix[p, i] == 1:
                                    nll -= np.log(p_correct)
                                else:
                                    nll -= np.log(1.0 - p_correct)
                        return nll

                    result = optimize.minimize(
                        negative_log_likelihood,
                        [abilities[p]],
                        method="L-BFGS-B",
                        bounds=[self.config["ability_range"]],
                    )
                    abilities[p] = result.x[0]

                # Step 2: Update item parameters given person abilities
                for i in range(n_items):
                    item_responses = response_matrix[:, i]
                    valid_indices = ~np.isnan(item_responses)

                    if not valid_indices.any():
                        continue

                    valid_responses = item_responses[valid_indices]
                    valid_abilities = abilities[valid_indices]

                    def negative_log_likelihood(params):
                        if model == IRTModel.ONE_PL:
                            b = params[0]
                            a, c = 1.0, 0.0
                        elif model == IRTModel.TWO_PL:
                            a, b = params
                            c = 0.0
                        else:  # THREE_PL
                            a, b, c = params

                        # Apply constraints
                        a = max(
                            self.config["min_discrimination"],
                            min(self.config["max_discrimination"], a),
                        )
                        b = max(
                            self.config["min_difficulty"], min(self.config["max_difficulty"], b)
                        )
                        c = max(self.config["min_guessing"], min(self.config["max_guessing"], c))

                        temp_item = IRTItem(
                            item_id=items[i].item_id,
                            model=model,
                            difficulty=b,
                            discrimination=a,
                            guessing=c,
                        )

                        nll = 0.0
                        for j, response in enumerate(valid_responses):
                            theta = valid_abilities[j]
                            p_correct = self.probability_of_correct_response(theta, temp_item)
                            response_prob = p_correct if response == 1 else (1.0 - p_correct)
                            nll -= np.log(response_prob + 1e-10)

                        return nll

                    # Initial parameter guess and bounds
                    if model == IRTModel.ONE_PL:
                        initial_params = [items[i].difficulty]
                        bounds = [(self.config["min_difficulty"], self.config["max_difficulty"])]
                    elif model == IRTModel.TWO_PL:
                        initial_params = [items[i].discrimination or 1.0, items[i].difficulty]
                        bounds = [
                            (self.config["min_discrimination"], self.config["max_discrimination"]),
                            (self.config["min_difficulty"], self.config["max_difficulty"]),
                        ]
                    else:  # THREE_PL
                        initial_params = [
                            items[i].discrimination or 1.0,
                            items[i].difficulty,
                            items[i].guessing or 0.0,
                        ]
                        bounds = [
                            (self.config["min_discrimination"], self.config["max_discrimination"]),
                            (self.config["min_difficulty"], self.config["max_difficulty"]),
                            (self.config["min_guessing"], self.config["max_guessing"]),
                        ]

                    result = optimize.minimize(
                        negative_log_likelihood, initial_params, method="L-BFGS-B", bounds=bounds
                    )

                    # Update item parameters
                    if model == IRTModel.ONE_PL:
                        items[i].difficulty = result.x[0]
                    elif model == IRTModel.TWO_PL:
                        items[i].discrimination = result.x[0]
                        items[i].difficulty = result.x[1]
                    else:  # THREE_PL
                        items[i].discrimination = result.x[0]
                        items[i].difficulty = result.x[1]
                        items[i].guessing = result.x[2]

                # Check convergence
                current_params = self._extract_item_parameters(items)
                param_change = np.mean(
                    [
                        abs(current_params[i][j] - prev_params[i][j])
                        for i in range(len(current_params))
                        for j in range(len(current_params[i]))
                    ]
                )

                if param_change < self.config["tolerance"]:
                    convergence = True

                iterations += 1

                if iterations % 10 == 0:
                    logger.debug(
                        f"JML iteration {iterations}: parameter change = {param_change:.6f}"
                    )

            return {"items": items, "convergence": convergence, "iterations": iterations}

        except Exception as e:
            logger.error(f"JML estimation failed: {e!s}")
            return {"items": items, "convergence": False, "iterations": 0}

    async def _estimate_em(
        self, response_matrix: np.ndarray, items: list[IRTItem], model: IRTModel
    ) -> dict[str, Any]:
        """Expectation-Maximization estimation"""
        # For now, delegate to MML (EM is a specific case of MML)
        return await self._estimate_mml(response_matrix, items, model)

    def _extract_item_parameters(self, items: list[IRTItem]) -> list[list[float]]:
        """Extract item parameters as list for comparison"""
        params = []
        for item in items:
            if item.model == IRTModel.ONE_PL:
                params.append([item.difficulty])
            elif item.model == IRTModel.TWO_PL:
                params.append([item.discrimination or 1.0, item.difficulty])
            else:  # THREE_PL
                params.append([item.discrimination or 1.0, item.difficulty, item.guessing or 0.0])
        return params

    async def _estimate_abilities(
        self, response_matrix: np.ndarray, items: list[IRTItem]
    ) -> list[IRTPerson]:
        """Estimate person abilities using Maximum Likelihood"""
        try:
            n_persons = response_matrix.shape[0]
            persons = []

            for p in range(n_persons):
                person_responses = response_matrix[p, :]
                valid_indices = ~np.isnan(person_responses)

                if not valid_indices.any():
                    # No valid responses, set ability to 0
                    person = IRTPerson(
                        person_id=f"person_{p}",
                        ability=0.0,
                        standard_error=float("inf"),
                        pattern_score=0,
                    )
                else:
                    # Estimate ability using MLE
                    def negative_log_likelihood(theta):
                        nll = 0.0
                        for i in valid_indices:
                            p_correct = self.probability_of_correct_response(theta[0], items[i])
                            if person_responses[i] == 1:
                                nll -= np.log(p_correct)
                            else:
                                nll -= np.log(1.0 - p_correct)
                        return nll

                    result = optimize.minimize(
                        negative_log_likelihood,
                        [0.0],  # Start at 0
                        method="L-BFGS-B",
                        bounds=[self.config["ability_range"]],
                    )

                    ability = result.x[0]

                    # Calculate standard error
                    information = self.test_information_function(
                        ability, [items[i] for i in valid_indices]
                    )
                    se = 1.0 / math.sqrt(information) if information > 0 else float("inf")

                    # Calculate pattern score
                    pattern_score = int(np.nansum(person_responses))

                    person = IRTPerson(
                        person_id=f"person_{p}",
                        ability=ability,
                        standard_error=se,
                        pattern_score=pattern_score,
                        response_pattern=[
                            int(r) if not np.isnan(r) else None for r in person_responses
                        ],
                    )

                persons.append(person)

            return persons

        except Exception as e:
            logger.error(f"Ability estimation failed: {e!s}")
            return []

    def _calculate_marginal_log_likelihood(
        self,
        response_matrix: np.ndarray,
        items: list[IRTItem],
        theta_points: np.ndarray,
        theta_weights: np.ndarray,
    ) -> float:
        """Calculate marginal log likelihood"""
        try:
            n_persons = response_matrix.shape[0]
            total_log_likelihood = 0.0

            for p in range(n_persons):
                person_likelihood = 0.0
                for t_idx, theta in enumerate(theta_points):
                    log_likelihood = 0.0
                    for i in range(response_matrix.shape[1]):
                        if not np.isnan(response_matrix[p, i]):
                            p_correct = self.probability_of_correct_response(theta, items[i])
                            if response_matrix[p, i] == 1:
                                log_likelihood += np.log(p_correct)
                            else:
                                log_likelihood += np.log(1.0 - p_correct)

                    person_likelihood += np.exp(log_likelihood) * theta_weights[t_idx]

                total_log_likelihood += np.log(person_likelihood + 1e-10)

            return total_log_likelihood

        except Exception as e:
            logger.error(f"Marginal log likelihood calculation failed: {e!s}")
            return -float("inf")

    def _calculate_log_likelihood(
        self, response_matrix: np.ndarray, items: list[IRTItem], persons: list[IRTPerson]
    ) -> float:
        """Calculate joint log likelihood"""
        try:
            total_log_likelihood = 0.0

            for p, person in enumerate(persons):
                for i, item in enumerate(items):
                    if not np.isnan(response_matrix[p, i]):
                        p_correct = self.probability_of_correct_response(person.ability, item)
                        if response_matrix[p, i] == 1:
                            total_log_likelihood += np.log(p_correct)
                        else:
                            total_log_likelihood += np.log(1.0 - p_correct)

            return total_log_likelihood

        except Exception as e:
            logger.error(f"Log likelihood calculation failed: {e!s}")
            return -float("inf")

    def _calculate_information_criteria(
        self, log_likelihood: float, items: list[IRTItem], persons: list[IRTPerson]
    ) -> tuple[float, float]:
        """Calculate AIC and BIC"""
        try:
            # Count parameters
            n_params = 0
            for item in items:
                if item.model == IRTModel.ONE_PL:
                    n_params += 1
                elif item.model == IRTModel.TWO_PL:
                    n_params += 2
                else:  # THREE_PL
                    n_params += 3

            n_observations = len(persons) * len(items)

            # AIC = 2k - 2ln(L)
            aic = 2 * n_params - 2 * log_likelihood

            # BIC = k*ln(n) - 2ln(L)
            bic = n_params * np.log(n_observations) - 2 * log_likelihood

            return aic, bic

        except Exception as e:
            logger.error(f"Information criteria calculation failed: {e!s}")
            return float("inf"), float("inf")

    async def _calculate_quality_metrics(
        self, response_matrix: np.ndarray, items: list[IRTItem], persons: list[IRTPerson]
    ) -> dict[str, float]:
        """Calculate model quality metrics"""
        try:
            metrics = {}

            # Item-level metrics
            item_discriminations = []
            item_difficulties = []
            for item in items:
                if item.discrimination is not None:
                    item_discriminations.append(item.discrimination)
                item_difficulties.append(item.difficulty)

            if item_discriminations:
                metrics["avg_discrimination"] = np.mean(item_discriminations)
                metrics["discrimination_std"] = np.std(item_discriminations)

            if item_difficulties:
                metrics["avg_difficulty"] = np.mean(item_difficulties)
                metrics["difficulty_std"] = np.std(item_difficulties)

            # Person-level metrics
            abilities = [p.ability for p in persons]
            if abilities:
                metrics["avg_ability"] = np.mean(abilities)
                metrics["ability_std"] = np.std(abilities)

            # Reliability metrics
            test_reliabilities = []
            for person in persons:
                if person.standard_error != float("inf"):
                    reliability = 1.0 - (person.standard_error**2)
                    test_reliabilities.append(max(0.0, min(1.0, reliability)))

            if test_reliabilities:
                metrics["avg_reliability"] = np.mean(test_reliabilities)

            # Information metrics
            abilities_range = np.linspace(-2, 2, 21)
            information_values = [
                self.test_information_function(theta, items) for theta in abilities_range
            ]
            metrics["max_information"] = max(information_values)
            metrics["min_information"] = min(information_values)
            metrics["avg_information"] = np.mean(information_values)

            return metrics

        except Exception as e:
            logger.error(f"Quality metrics calculation failed: {e!s}")
            return {}

    def adaptive_item_selection(
        self,
        current_ability: float,
        remaining_items: list[IRTItem],
        selection_method: str = "max_information",
    ) -> IRTItem:
        """Select next item for adaptive testing"""
        try:
            if not remaining_items:
                raise ValueError("No remaining items to select from")

            if selection_method == "max_information":
                # Select item with maximum information at current ability
                information_values = [
                    (item, self.information_function(current_ability, item))
                    for item in remaining_items
                ]
                return max(information_values, key=lambda x: x[1])[0]

            if selection_method == "closest_difficulty":
                # Select item with difficulty closest to current ability
                difficulty_diffs = [
                    (item, abs(item.difficulty - current_ability)) for item in remaining_items
                ]
                return min(difficulty_diffs, key=lambda x: x[1])[0]

            if selection_method == "bayesian":
                # Select item that maximizes expected information gain
                # Simplified: use combination of information and difficulty
                scores = []
                for item in remaining_items:
                    info = self.information_function(current_ability, item)
                    diff_penalty = abs(item.difficulty - current_ability) * 0.1
                    score = info - diff_penalty
                    scores.append((item, score))
                return max(scores, key=lambda x: x[1])[0]

            # Default to random selection
            return np.secrets.choice(remaining_items)

        except Exception as e:
            logger.error(f"Adaptive item selection failed: {e!s}")
            return remaining_items[0]  # Fallback to first item

    def calculate_standard_errors(
        self, items: list[IRTItem], abilities: list[float]
    ) -> list[float]:
        """Calculate standard errors for ability estimates"""
        try:
            standard_errors = []
            for ability in abilities:
                information = self.test_information_function(ability, items)
                se = 1.0 / math.sqrt(information) if information > 0 else float("inf")
                standard_errors.append(se)
            return standard_errors

        except Exception as e:
            logger.error(f"Standard error calculation failed: {e!s}")
            return [float("inf")] * len(abilities)

    def export_calibration_results(
        self, results: IRTCalibrationResult, format: str = "json"
    ) -> str:
        """Export calibration results"""
        try:
            if format == "json":
                return json.dumps(results.to_dict(), indent=2, ensure_ascii=False)
            raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Export failed: {e!s}")
            return ""


# Export the main service class
__all__ = [
    "EstimationMethod",
    "IRTCalibrationResult",
    "IRTItem",
    "IRTModel",
    "IRTPerson",
    "IRTResponse",
    "IRTService",
]
