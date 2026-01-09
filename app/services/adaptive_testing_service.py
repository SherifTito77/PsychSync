"""
Computerized Adaptive Testing (CAT) Service
Advanced adaptive testing engine using Item Response Theory (IRT)
"""

from dataclasses import dataclass
from enum import Enum
import logging
import math
from typing import Any
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class StoppingRule(Enum):
    """Types of stopping rules for adaptive tests"""
    FIXED_LENGTH = "fixed_length"
    STANDARD_ERROR = "standard_error"
    INFORMATION = "information"
    CONFIDENCE_INTERVAL = "confidence_interval"


class EstimationMethod(Enum):
    """Ability estimation methods"""
    MAXIMUM_LIKELIHOOD = "maximum_likelihood"
    BAYESIAN = "bayesian"
    EXPECTED_A_POSTERIORI = "expected_a_posteriori"


@dataclass
class TestItem:
    """Represents a test item with IRT parameters"""
    id: str
    question_text: str
    item_type: str
    difficulty: float  # b parameter
    discrimination: float  # a parameter
    guessing: float  # c parameter
    content_domain: str
    position: int | None = None
    response_time_estimate: float | None = None


@dataclass
class AbilityEstimate:
    """Ability estimate with confidence intervals"""
    theta: float  # Ability estimate
    standard_error: float
    confidence_interval: tuple[float, float]
    information: float


@dataclass
class AdaptiveTestSession:
    """Active adaptive testing session"""
    session_id: UUID
    user_id: UUID
    assessment_id: UUID
    items_administered: list[TestItem]
    responses: list[int]
    current_ability: AbilityEstimate
    stopping_rule: StoppingRule
    max_items: int
    min_items: int
    target_se: float
    is_complete: bool
    start_time: float
    response_times: list[float]


class ComputerizedAdaptiveTestingService:
    """Advanced Computerized Adaptive Testing service using IRT"""

    def __init__(self, db: Session):
        self.db = db

        # CAT configuration defaults
        self.default_config = {
            "max_items": 30,
            "min_items": 10,
            "target_standard_error": 0.3,
            "stopping_rule": StoppingRule.STANDARD_ERROR,
            "estimation_method": EstimationMethod.MAXIMUM_LIKELIHOOD,
            "initial_ability": 0.0,
            "item_exposure_rate": 0.2,  # Maximum exposure rate for items
            "content_balancing": True,
            "shadow_testing": True
        }

        # IRT model parameters
        self.irt_model = "3PL"  # 3-parameter logistic model

    async def start_adaptive_test(
        self,
        user_id: UUID,
        assessment_id: UUID,
        config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Start a new adaptive testing session"""
        try:
            # Merge with default config
            test_config = {**self.default_config, **(config or {})}

            # Get item bank for the assessment
            item_bank = await self._get_item_bank(assessment_id)
            if not item_bank:
                raise ValueError("No items available for this assessment")

            # Create session
            session_id = UUID()
            initial_ability = AbilityEstimate(
                theta=test_config["initial_ability"],
                standard_error=2.0,  # High uncertainty initially
                confidence_interval=(-2.0, 2.0),
                information=0.0
            )

            session = AdaptiveTestSession(
                session_id=session_id,
                user_id=user_id,
                assessment_id=assessment_id,
                items_administered=[],
                responses=[],
                current_ability=initial_ability,
                stopping_rule=test_config["stopping_rule"],
                max_items=test_config["max_items"],
                min_items=test_config["min_items"],
                target_se=test_config["target_standard_error"],
                is_complete=False,
                start_time=self._get_current_timestamp(),
                response_times=[]
            )

            # Select first item (typically medium difficulty)
            first_item = await self._select_next_item(session, item_bank)
            session.items_administered.append(first_item)

            return {
                "success": True,
                "session_id": str(session_id),
                "first_item": {
                    "id": first_item.id,
                    "text": first_item.question_text,
                    "type": first_item.item_type
                },
                "estimated_time_remaining": len(item_bank) * 30,  # Rough estimate
                "progress": {
                    "items_administered": 0,
                    "max_items": session.max_items
                }
            }

        except Exception as e:
            logger.error(f"Error starting adaptive test: {e!s}")
            return {"success": False, "error": str(e)}

    async def submit_response(
        self,
        session_id: UUID,
        item_id: str,
        response: int,
        response_time: float | None = None
    ) -> dict[str, Any]:
        """Submit response and get next item"""
        try:
            # Get session (in production, store in Redis/database)
            session = await self._get_session(session_id)
            if not session:
                return {"success": False, "error": "Invalid session ID"}

            if session.is_complete:
                return {"success": False, "error": "Test is already complete"}

            # Record response
            session.responses.append(response)
            if response_time:
                session.response_times.append(response_time)

            # Update ability estimate
            await self._update_ability_estimate(session)

            # Check stopping criteria
            should_stop = await self._check_stopping_criteria(session)

            if should_stop:
                session.is_complete = True
                final_results = await self._calculate_final_results(session)

                return {
                    "success": True,
                    "test_complete": True,
                    "results": final_results,
                    "session_id": str(session_id)
                }
            # Select next item
            item_bank = await self._get_item_bank(session.assessment_id)
            next_item = await self._select_next_item(session, item_bank)
            session.items_administered.append(next_item)

            return {
                "success": True,
                "test_complete": False,
                "next_item": {
                    "id": next_item.id,
                    "text": next_item.question_text,
                    "type": next_item.item_type
                },
                "progress": {
                    "items_administered": len(session.items_administered) - 1,
                    "max_items": session.max_items,
                    "ability_estimate": session.current_ability.theta,
                    "standard_error": session.current_ability.standard_error
                }
            }

        except Exception as e:
            logger.error(f"Error submitting response: {e!s}")
            return {"success": False, "error": str(e)}

    async def get_test_status(self, session_id: UUID) -> dict[str, Any]:
        """Get current status of adaptive test"""
        try:
            session = await self._get_session(session_id)
            if not session:
                return {"success": False, "error": "Invalid session ID"}

            return {
                "success": True,
                "session_id": str(session_id),
                "is_complete": session.is_complete,
                "items_administered": len(session.items_administered),
                "max_items": session.max_items,
                "current_ability": session.current_ability.theta,
                "standard_error": session.current_ability.standard_error,
                "estimated_time_remaining": (session.max_items - len(session.items_administered)) * 30
            }

        except Exception as e:
            logger.error(f"Error getting test status: {e!s}")
            return {"success": False, "error": str(e)}

    async def _get_item_bank(self, assessment_id: UUID) -> list[TestItem]:
        """Retrieve and calibrate item bank for assessment"""
        try:
            # In production, this would query the database for calibrated items
            # For now, generate sample items with IRT parameters

            sample_items = [
                TestItem(
                    id="item_001",
                    question_text="How comfortable are you with taking on new challenges?",
                    item_type="likert",
                    difficulty=-0.5,
                    discrimination=1.2,
                    guessing=0.0,
                    content_domain="adventurousness"
                ),
                TestItem(
                    id="item_002",
                    question_text="Do you prefer working independently or in teams?",
                    item_type="multiple_choice",
                    difficulty=0.0,
                    discrimination=1.0,
                    guessing=0.25,
                    content_domain="teamwork"
                ),
                TestItem(
                    id="item_003",
                    question_text="How often do you seek feedback on your performance?",
                    item_type="scale",
                    difficulty=0.3,
                    discrimination=1.5,
                    guessing=0.0,
                    content_domain="growth_mindset"
                ),
                TestItem(
                    id="item_004",
                    question_text="Do you enjoy analyzing complex problems?",
                    item_type="likert",
                    difficulty=-0.2,
                    discrimination=1.3,
                    guessing=0.0,
                    content_domain="analytical_thinking"
                ),
                TestItem(
                    id="item_005",
                    question_text="How do you handle unexpected changes in plans?",
                    item_type="multiple_choice",
                    difficulty=0.1,
                    discrimination=1.1,
                    guessing=0.2,
                    content_domain="adaptability"
                )
            ]

            # Generate more items to simulate a real item bank
            additional_items = []
            for i in range(6, 50):  # 45 more items
                difficulty = np.random.normal(0, 1)
                discrimination = np.random.gamma(2, 0.5)
                guessing = 0.0 if i % 3 != 0 else np.random.uniform(0.1, 0.3)

                additional_items.append(TestItem(
                    id=f"item_{i:03d}",
                    question_text=f"Sample question {i} for adaptive testing",
                    item_type="likert",
                    difficulty=difficulty,
                    discrimination=discrimination,
                    guessing=guessing,
                    content_domain="personality"
                ))

            return sample_items + additional_items

        except Exception as e:
            logger.error(f"Error getting item bank: {e!s}")
            return []

    async def _select_next_item(
        self,
        session: AdaptiveTestSession,
        item_bank: list[TestItem]
    ) -> TestItem:
        """Select next item using optimal item selection"""
        try:
            # Filter out already administered items
            available_items = [
                item for item in item_bank
                if item.id not in [administered.id for administered in session.items_administered]
            ]

            if not available_items:
                raise ValueError("No more items available")

            current_theta = session.current_ability.theta

            # Calculate information for each available item
            item_informations = []
            for item in available_items:
                information = await self._calculate_item_information(item, current_theta)
                item_informations.append((item, information))

            # Sort by information (highest first)
            item_informations.sort(key=lambda x: x[1], reverse=True)

            # Apply content balancing if enabled
            if self.default_config["content_balancing"]:
                selected_item = await self._apply_content_balancing(
                    item_informations, session
                )
            else:
                # Select highest information item
                selected_item = item_informations[0][0]

            return selected_item

        except Exception as e:
            logger.error(f"Error selecting next item: {e!s}")
            # Fallback: return first available item
            return available_items[0]

    async def _calculate_item_information(self, item: TestItem, theta: float) -> float:
        """Calculate Fisher information for an item at given ability level"""
        try:
            a = item.discrimination
            b = item.difficulty
            c = item.guessing

            if self.irt_model == "3PL":
                # 3PL model information function
                p = await self._irt_probability(theta, a, b, c)
                q = 1 - p
                p_c = p - c

                if p_c <= 0:
                    return 0.0

                information = (a ** 2) * ((q / p) ** 2) * ((p_c / (1 - c)) ** 2)
            else:
                # 2PL model (simplified)
                p = await self._irt_probability_2pl(theta, a, b)
                q = 1 - p
                information = (a ** 2) * p * q

            return information

        except Exception as e:
            logger.error(f"Error calculating item information: {e!s}")
            return 0.0

    async def _irt_probability(self, theta: float, a: float, b: float, c: float) -> float:
        """Calculate probability of correct response using 3PL model"""
        try:
            exp_term = math.exp(a * (theta - b))
            return c + (1 - c) * (exp_term / (1 + exp_term))
        except Exception as e:
            logger.error(f"Error in IRT probability calculation: {e!s}")
            return 0.5

    async def _irt_probability_2pl(self, theta: float, a: float, b: float) -> float:
        """Calculate probability of correct response using 2PL model"""
        try:
            exp_term = math.exp(a * (theta - b))
            return exp_term / (1 + exp_term)
        except Exception as e:
            logger.error(f"Error in 2PL IRT probability calculation: {e!s}")
            return 0.5

    async def _update_ability_estimate(self, session: AdaptiveTestSession):
        """Update ability estimate based on responses"""
        try:
            method = self.default_config["estimation_method"]

            if method == EstimationMethod.MAXIMUM_LIKELIHOOD:
                new_estimate = await self._maximum_likelihood_estimation(session)
            elif method == EstimationMethod.BAYESIAN:
                new_estimate = await self._bayesian_estimation(session)
            else:
                new_estimate = await self._expected_a_posteriori(session)

            session.current_ability = new_estimate

        except Exception as e:
            logger.error(f"Error updating ability estimate: {e!s}")

    async def _maximum_likelihood_estimation(self, session: AdaptiveTestSession) -> AbilityEstimate:
        """Maximum likelihood ability estimation"""
        try:
            if not session.responses:
                return session.current_ability

            # Newton-Raphson iteration
            theta = session.current_ability.theta
            max_iterations = 50
            convergence_threshold = 0.001

            for iteration in range(max_iterations):
                # Calculate first and second derivatives
                first_derivative = 0.0
                second_derivative = 0.0

                for i, item in enumerate(session.items_administered):
                    response = session.responses[i]
                    a = item.discrimination
                    b = item.difficulty
                    c = item.guessing

                    p = await self._irt_probability(theta, a, b, c)
                    q = 1 - p

                    if self.irt_model == "3PL":
                        w = (p - c) / (1 - c)
                        first_derivative += (a * (response - p) * w / (p * q))
                        second_derivative -= (a ** 2 * w * ((response * q) - (p * c)) / (p ** 2 * q ** 2))

                # Update theta
                if abs(second_derivative) > 1e-10:
                    delta = first_derivative / second_derivative
                    theta = theta - delta

                    if abs(delta) < convergence_threshold:
                        break

            # Calculate standard error
            fisher_information = 0.0
            for i, item in enumerate(session.items_administered):
                info = await self._calculate_item_information(item, theta)
                fisher_information += info

            standard_error = 1.0 / math.sqrt(max(fisher_information, 0.01))
            confidence_interval = (
                theta - 1.96 * standard_error,
                theta + 1.96 * standard_error
            )

            return AbilityEstimate(
                theta=theta,
                standard_error=standard_error,
                confidence_interval=confidence_interval,
                information=fisher_information
            )

        except Exception as e:
            logger.error(f"Error in MLE estimation: {e!s}")
            return session.current_ability

    async def _bayesian_estimation(self, session: AdaptiveTestSession) -> AbilityEstimate:
        """Bayesian ability estimation"""
        try:
            # Simplified Bayesian estimation using normal prior
            prior_mean = 0.0
            prior_std = 1.0

            # Use MLE as MAP estimate with normal prior
            mle_estimate = await self._maximum_likelihood_estimation(session)

            # Apply Bayesian shrinkage
            n_items = len(session.responses)
            weight = n_items / (n_items + (prior_std ** 2 / (mle_estimate.standard_error ** 2)))

            bayesian_theta = weight * mle_estimate.theta + (1 - weight) * prior_mean
            bayesian_se = math.sqrt(weight * (mle_estimate.standard_error ** 2))

            confidence_interval = (
                bayesian_theta - 1.96 * bayesian_se,
                bayesian_theta + 1.96 * bayesian_se
            )

            return AbilityEstimate(
                theta=bayesian_theta,
                standard_error=bayesian_se,
                confidence_interval=confidence_interval,
                information=1.0 / (bayesian_se ** 2)
            )

        except Exception as e:
            logger.error(f"Error in Bayesian estimation: {e!s}")
            return session.current_ability

    async def _expected_a_posteriori(self, session: AdaptiveTestSession) -> AbilityEstimate:
        """Expected a posteriori estimation"""
        # For now, use Bayesian estimation as proxy
        return await self._bayesian_estimation(session)

    async def _check_stopping_criteria(self, session: AdaptiveTestSession) -> bool:
        """Check if test should stop based on stopping rule"""
        try:
            # Check minimum items requirement
            if len(session.responses) < session.min_items:
                return False

            # Check maximum items limit
            if len(session.responses) >= session.max_items:
                return True

            stopping_rule = session.stopping_rule

            if stopping_rule == StoppingRule.FIXED_LENGTH:
                return len(session.responses) >= session.max_items

            if stopping_rule == StoppingRule.STANDARD_ERROR:
                return session.current_ability.standard_error <= session.target_se

            if stopping_rule == StoppingRule.INFORMATION:
                return session.current_ability.information >= 10.0  # Threshold

            if stopping_rule == StoppingRule.CONFIDENCE_INTERVAL:
                ci_width = (session.current_ability.confidence_interval[1] -
                          session.current_ability.confidence_interval[0])
                return ci_width <= 0.5  # Width threshold

            return False

        except Exception as e:
            logger.error(f"Error checking stopping criteria: {e!s}")
            return False

    async def _apply_content_balancing(
        self,
        item_informations: list[tuple[TestItem, float]],
        session: AdaptiveTestSession
    ) -> TestItem:
        """Apply content balancing constraints"""
        try:
            # Count content domains already administered
            domain_counts = {}
            for item in session.items_administered:
                domain = item.content_domain
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

            # Select item from domain with least coverage
            for item, information in item_informations[:10]:  # Consider top 10 items
                domain = item.content_domain
                if domain_counts.get(domain, 0) <= len(session.responses) // 4:  # Balanced distribution
                    return item

            # Fallback to highest information item
            return item_informations[0][0]

        except Exception as e:
            logger.error(f"Error applying content balancing: {e!s}")
            return item_informations[0][0]

    async def _calculate_final_results(self, session: AdaptiveTestSession) -> dict[str, Any]:
        """Calculate final test results and report"""
        try:
            ability_estimate = session.current_ability

            # Convert ability to standard scores
            z_score = ability_estimate.theta
            percentile = await self._theta_to_percentile(z_score)
            t_score = 50 + z_score * 10  # T-score (mean=50, sd=10)

            # Calculate domain-level scores if available
            domain_scores = await self._calculate_domain_scores(session)

            # Generate interpretation
            interpretation = await self._generate_ability_interpretation(z_score)

            return {
                "final_ability": ability_estimate.theta,
                "standard_error": ability_estimate.standard_error,
                "confidence_interval": ability_estimate.confidence_interval,
                "standard_scores": {
                    "z_score": z_score,
                    "percentile": percentile,
                    "t_score": t_score
                },
                "domain_scores": domain_scores,
                "interpretation": interpretation,
                "test_statistics": {
                    "items_administered": len(session.items_administered),
                    "response_times": session.response_times,
                    "total_time": self._get_current_timestamp() - session.start_time,
                    "reliability": await self._calculate_reliability(ability_estimate.standard_error)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating final results: {e!s}")
            return {"error": str(e)}

    async def _theta_to_percentile(self, theta: float) -> float:
        """Convert theta estimate to percentile rank"""
        try:
            # Standard normal CDF approximation
            if theta == 0:
                return 50.0
            if theta > 0:
                return 50.0 + 50.0 * math.erf(theta / math.sqrt(2))
            return 50.0 - 50.0 * math.erf(abs(theta) / math.sqrt(2))
        except Exception:
            return 50.0

    async def _calculate_domain_scores(self, session: AdaptiveTestSession) -> dict[str, float]:
        """Calculate scores by content domain"""
        try:
            domain_responses = {}
            domain_items = {}

            # Group responses by domain
            for i, item in enumerate(session.items_administered):
                domain = item.content_domain
                if domain not in domain_responses:
                    domain_responses[domain] = []
                    domain_items[domain] = []
                domain_responses[domain].append(session.responses[i])
                domain_items[domain].append(item)

            # Calculate domain-specific ability estimates
            domain_scores = {}
            for domain, responses in domain_responses.items():
                # Simplified domain scoring
                avg_response = sum(responses) / len(responses)
                domain_scores[domain] = avg_response

            return domain_scores

        except Exception as e:
            logger.error(f"Error calculating domain scores: {e!s}")
            return {}

    async def _generate_ability_interpretation(self, theta: float) -> str:
        """Generate human-readable interpretation of ability level"""
        try:
            if theta > 1.5:
                return "Very High: Demonstrates exceptional ability in this domain."
            if theta > 0.5:
                return "High: Shows strong ability above average."
            if theta > -0.5:
                return "Average: Demonstrates typical ability levels."
            if theta > -1.5:
                return "Below Average: Shows room for development."
            return "Low: May need significant support in this area."

        except Exception:
            return "Interpretation not available."

    async def _calculate_reliability(self, standard_error: float) -> float:
        """Calculate test reliability from standard error"""
        try:
            # Reliability = 1 - (measurement error variance / true score variance)
            # Assuming true score variance = 1 for standard normal
            measurement_error_variance = standard_error ** 2
            reliability = 1 - measurement_error_variance
            return max(0.0, min(1.0, reliability))
        except Exception:
            return 0.0

    async def _get_session(self, session_id: UUID) -> AdaptiveTestSession | None:
        """Get test session (in production, would use Redis/database)"""
        # Placeholder implementation
        return None

    def _get_current_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()

    async def calibrate_items(self, response_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Calibrate IRT parameters for new items using response data"""
        try:
            # This is a complex operation that would use specialized IRT calibration software
            # For now, return placeholder results
            return {
                "success": True,
                "message": "Item calibration completed",
                "calibrated_items": len(response_data),
                "note": "This is a placeholder. Real calibration requires specialized algorithms."
            }

        except Exception as e:
            logger.error(f"Error calibrating items: {e!s}")
            return {"success": False, "error": str(e)}
