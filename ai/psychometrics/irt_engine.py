"""
Item Response Theory (IRT) and Adaptive Testing Engine for PsychSync
Implements 1PL, 2PL, and 3PL IRT models for psychometric assessment.

Requirements:
    pip install numpy scipy pandas
"""

import numpy as np
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
import json
from dataclasses import dataclass, asdict
from enum import Enum


class IRTModel(Enum):
    """IRT model types."""
    RASCH = "1PL"  # One Parameter Logistic (difficulty only)
    TWO_PL = "2PL"  # Two Parameter Logistic (difficulty + discrimination)
    THREE_PL = "3PL"  # Three Parameter Logistic (difficulty + discrimination + guessing)


@dataclass
class ItemParameters:
    """IRT item parameters."""
    item_id: str
    difficulty: float  # b parameter (location on ability scale)
    discrimination: float = 1.0  # a parameter (slope)
    guessing: float = 0.0  # c parameter (lower asymptote)
    model: str = "2PL"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ItemParameters':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AssessmentResult:
    """Results from an adaptive assessment."""
    estimated_theta: float  # Estimated ability level
    standard_error: float  # Standard error of estimate
    items_administered: List[str]  # Item IDs administered
    responses: List[int]  # Responses (0 or 1)
    theta_trajectory: List[float]  # Ability estimates over time
    stopping_reason: str  # Why assessment stopped
    total_items: int
    reliability: float  # Estimated reliability


class IRTEngine:
    """
    Item Response Theory engine for psychometric assessment.
    Supports 1PL, 2PL, and 3PL models.
    """
    
    def __init__(self, item_bank: List[ItemParameters], model: IRTModel = IRTModel.TWO_PL):
        """
        Initialize IRT engine.
        
        Args:
            item_bank: List of calibrated items with parameters
            model: IRT model to use (1PL, 2PL, or 3PL)
        """
        self.item_bank = item_bank
        self.model = model
        self.item_dict = {item.item_id: item for item in item_bank}
    
    def probability(self, theta: float, item: ItemParameters) -> float:
        """
        Calculate probability of correct response using IRT model.
        
        P(θ) = c + (1 - c) / (1 + exp(-a(θ - b)))
        
        Args:
            theta: Ability level
            item: Item parameters
            
        Returns:
            Probability of correct response (0 to 1)
        """
        a = item.discrimination
        b = item.difficulty
        c = item.guessing
        
        if self.model == IRTModel.RASCH:
            # 1PL: All items have same discrimination (a=1)
            return 1 / (1 + np.exp(-(theta - b)))
        
        elif self.model == IRTModel.TWO_PL:
            # 2PL: Include discrimination
            return 1 / (1 + np.exp(-a * (theta - b)))
        
        elif self.model == IRTModel.THREE_PL:
            # 3PL: Include guessing parameter
            return c + (1 - c) / (1 + np.exp(-a * (theta - b)))
        
        else:
            raise ValueError(f"Unknown IRT model: {self.model}")
    
    def information(self, theta: float, item: ItemParameters) -> float:
        """
        Calculate item information at given ability level.
        Fisher Information quantifies precision of ability estimate.
        
        Args:
            theta: Ability level
            item: Item parameters
            
        Returns:
            Item information value
        """
        p = self.probability(theta, item)
        q = 1 - p
        a = item.discrimination
        c = item.guessing
        
        if self.model == IRTModel.RASCH:
            return p * q
        
        elif self.model == IRTModel.TWO_PL:
            return a**2 * p * q
        
        elif self.model == IRTModel.THREE_PL:
            return a**2 * ((p - c)**2) / ((1 - c)**2 * p * q)
        
        else:
            return 0
    
    def test_information(self, theta: float, items: List[ItemParameters]) -> float:
        """
        Calculate total test information (sum of item information).
        
        Args:
            theta: Ability level
            items: List of items
            
        Returns:
            Total information
        """
        return sum(self.information(theta, item) for item in items)
    
    def standard_error(self, theta: float, items: List[ItemParameters]) -> float:
        """
        Calculate standard error of ability estimate.
        SE(θ) = 1 / sqrt(Information)
        
        Args:
            theta: Ability level
            items: Items administered
            
        Returns:
            Standard error
        """
        info = self.test_information(theta, items)
        if info <= 0:
            return float('inf')
        return 1 / np.sqrt(info)
    
    def estimate_ability_mle(
        self,
        responses: List[int],
        items: List[ItemParameters],
        initial_theta: float = 0.0
    ) -> Tuple[float, float]:
        """
        Estimate ability using Maximum Likelihood Estimation.
        
        Args:
            responses: List of responses (0 or 1)
            items: Corresponding items
            initial_theta: Starting theta estimate
            
        Returns:
            Tuple of (estimated_theta, standard_error)
        """
        if len(responses) != len(items):
            raise ValueError("Number of responses must match number of items")
        
        # Handle edge cases
        if all(r == 1 for r in responses):
            # All correct: theta is high
            max_difficulty = max(item.difficulty for item in items)
            return max_difficulty + 2.0, 1.0
        
        if all(r == 0 for r in responses):
            # All incorrect: theta is low
            min_difficulty = min(item.difficulty for item in items)
            return min_difficulty - 2.0, 1.0
        
        # Likelihood function to minimize (negative log-likelihood)
        def neg_log_likelihood(theta):
            ll = 0
            for response, item in zip(responses, items):
                p = self.probability(theta, item)
                # Avoid log(0)
                p = np.clip(p, 1e-10, 1 - 1e-10)
                
                if response == 1:
                    ll += np.log(p)
                else:
                    ll += np.log(1 - p)
            
            return -ll
        
        # Optimize
        result = minimize(
            neg_log_likelihood,
            x0=initial_theta,
            method='BFGS',
            bounds=[(-4, 4)]
        )
        
        theta_est = result.x[0]
        se = self.standard_error(theta_est, items)
        
        return theta_est, se
    
    def estimate_ability_eap(
        self,
        responses: List[int],
        items: List[ItemParameters],
        prior_mean: float = 0.0,
        prior_sd: float = 1.0
    ) -> Tuple[float, float]:
        """
        Estimate ability using Expected A Posteriori (EAP) method.
        More stable than MLE for short tests.
        
        Args:
            responses: List of responses
            items: Corresponding items
            prior_mean: Mean of prior distribution
            prior_sd: Standard deviation of prior
            
        Returns:
            Tuple of (estimated_theta, standard_error)
        """
        # Quadrature points for integration
        theta_values = np.linspace(-4, 4, 41)
        
        # Prior probabilities (normal distribution)
        prior = np.exp(-0.5 * ((theta_values - prior_mean) / prior_sd)**2)
        prior = prior / np.sum(prior)
        
        # Likelihood for each theta value
        likelihood = np.ones(len(theta_values))
        for response, item in zip(responses, items):
            for i, theta in enumerate(theta_values):
                p = self.probability(theta, item)
                if response == 1:
                    likelihood[i] *= p
                else:
                    likelihood[i] *= (1 - p)
        
        # Posterior distribution
        posterior = likelihood * prior
        posterior = posterior / np.sum(posterior)
        
        # Expected value (mean of posterior)
        theta_est = np.sum(theta_values * posterior)
        
        # Standard error (SD of posterior)
        se = np.sqrt(np.sum(((theta_values - theta_est)**2) * posterior))
        
        return theta_est, se


class AdaptiveTestEngine:
    """
    Computerized Adaptive Testing (CAT) engine.
    Selects optimal items based on current ability estimate.
    """
    
    def __init__(
        self,
        irt_engine: IRTEngine,
        min_items: int = 5,
        max_items: int = 30,
        se_threshold: float = 0.3,
        starting_theta: float = 0.0
    ):
        """
        Initialize adaptive testing engine.
        
        Args:
            irt_engine: IRT engine with calibrated item bank
            min_items: Minimum items to administer
            max_items: Maximum items to administer
            se_threshold: Stop when SE below this value
            starting_theta: Initial ability estimate
        """
        self.irt = irt_engine
        self.min_items = min_items
        self.max_items = max_items
        self.se_threshold = se_threshold
        self.starting_theta = starting_theta
    
    def select_next_item(
        self,
        current_theta: float,
        administered_items: List[str],
        method: str = 'max_info'
    ) -> Optional[ItemParameters]:
        """
        Select the next best item to administer.
        
        Args:
            current_theta: Current ability estimate
            administered_items: Items already given
            method: Selection method ('max_info', 'random', 'difficulty_match')
            
        Returns:
            Next item to administer or None if no items available
        """
        # Available items (not yet administered)
        available = [
            item for item in self.irt.item_bank
            if item.item_id not in administered_items
        ]
        
        if not available:
            return None
        
        if method == 'max_info':
            # Select item with maximum information at current theta
            info_scores = [
                self.irt.information(current_theta, item)
                for item in available
            ]
            best_idx = np.argmax(info_scores)
            return available[best_idx]
        
        elif method == 'difficulty_match':
            # Select item closest in difficulty to current theta
            difficulties = [abs(item.difficulty - current_theta) for item in available]
            best_idx = np.argmin(difficulties)
            return available[best_idx]
        
        elif method == 'random':
            # Random selection (for comparison/testing)
            return np.random.choice(available)
        
        else:
            raise ValueError(f"Unknown selection method: {method}")
    
    def administer_test(
        self,
        response_function: callable,
        selection_method: str = 'max_info',
        verbose: bool = False
    ) -> AssessmentResult:
        """
        Administer full adaptive test.
        
        Args:
            response_function: Function that takes item_id and returns response (0 or 1)
            selection_method: Item selection strategy
            verbose: Print progress
            
        Returns:
            AssessmentResult with final estimates and test statistics
        """
        # Initialize
        theta_est = self.starting_theta
        se_est = float('inf')
        administered = []
        responses = []
        theta_trajectory = [theta_est]
        
        # Administer items
        for item_num in range(self.max_items):
            # Select next item
            next_item = self.select_next_item(
                theta_est,
                administered,
                method=selection_method
            )
            
            if next_item is None:
                stopping_reason = "item_bank_exhausted"
                break
            
            # Get response
            response = response_function(next_item.item_id)
            
            # Record
            administered.append(next_item.item_id)
            responses.append(response)
            
            # Update ability estimate
            items_given = [self.irt.item_dict[iid] for iid in administered]
            theta_est, se_est = self.irt.estimate_ability_eap(responses, items_given)
            theta_trajectory.append(theta_est)
            
            if verbose:
                print(f"Item {item_num + 1}: {next_item.item_id}")
                print(f"  Response: {response}")
                print(f"  Theta: {theta_est:.3f} (SE: {se_est:.3f})")
            
            # Check stopping criteria
            if item_num + 1 >= self.min_items:
                if se_est < self.se_threshold:
                    stopping_reason = "se_threshold_reached"
                    break
        else:
            stopping_reason = "max_items_reached"
        
        # Calculate reliability
        reliability = 1 - (se_est ** 2)
        
        return AssessmentResult(
            estimated_theta=theta_est,
            standard_error=se_est,
            items_administered=administered,
            responses=responses,
            theta_trajectory=theta_trajectory,
            stopping_reason=stopping_reason,
            total_items=len(administered),
            reliability=reliability
        )
    
    def simulate_test(
        self,
        true_theta: float,
        selection_method: str = 'max_info',
        verbose: bool = False
    ) -> AssessmentResult:
        """
        Simulate an adaptive test for a person with known ability.
        Useful for testing and validation.
        
        Args:
            true_theta: True ability level
            selection_method: Item selection method
            verbose: Print progress
            
        Returns:
            AssessmentResult
        """
        def simulated_response(item_id: str) -> int:
            """Simulate response based on true ability."""
            item = self.irt.item_dict[item_id]
            p = self.irt.probability(true_theta, item)
            return 1 if np.random.random() < p else 0
        
        result = self.administer_test(
            simulated_response,
            selection_method=selection_method,
            verbose=verbose
        )
        
        if verbose:
            print(f"\nTrue theta: {true_theta:.3f}")
            print(f"Estimated theta: {result.estimated_theta:.3f}")
            print(f"Estimation error: {abs(true_theta - result.estimated_theta):.3f}")
        
        return result


def load_item_bank_from_json(filepath: str) -> List[ItemParameters]:
    """Load item bank from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return [ItemParameters.from_dict(item) for item in data]


def save_item_bank_to_json(items: List[ItemParameters], filepath: str):
    """Save item bank to JSON file."""
    data = [item.to_dict() for item in items]
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


# Example usage
if __name__ == "__main__":
    print("IRT & Adaptive Testing Demo")
    print("=" * 50)
    
    # Create sample item bank (Depression screening items)
    sample_items = [
        ItemParameters("dep_001", difficulty=-2.0, discrimination=1.5, model="2PL"),
        ItemParameters("dep_002", difficulty=-1.5, discrimination=1.2, model="2PL"),
        ItemParameters("dep_003", difficulty=-1.0, discrimination=1.8, model="2PL"),
        ItemParameters("dep_004", difficulty=-0.5, discrimination=1.3, model="2PL"),
        ItemParameters("dep_005", difficulty=0.0, discrimination=1.6, model="2PL"),
        ItemParameters("dep_006", difficulty=0.5, discrimination=1.4, model="2PL"),
        ItemParameters("dep_007", difficulty=1.0, discrimination=1.7, model="2PL"),
        ItemParameters("dep_008", difficulty=1.5, discrimination=1.1, model="2PL"),
        ItemParameters("dep_009", difficulty=2.0, discrimination=1.5, model="2PL"),
        ItemParameters("dep_010", difficulty=2.5, discrimination=1.3, model="2PL"),
    ]
    
    # Initialize engines
    irt = IRTEngine(sample_items, model=IRTModel.TWO_PL)
    cat = AdaptiveTestEngine(
        irt,
        min_items=5,
        max_items=10,
        se_threshold=0.4
    )
    
    # Simulate adaptive test
    print("\nSimulating adaptive test for person with theta = 1.0")
    print("-" * 50)
    result = cat.simulate_test(true_theta=1.0, verbose=True)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Items administered: {result.total_items}")
    print(f"Final theta estimate: {result.estimated_theta:.3f}")
    print(f"Standard error: {result.standard_error:.3f}")
    print(f"Reliability: {result.reliability:.3f}")
    print(f"Stopping reason: {result.stopping_reason}")
    print(f"Theta trajectory: {[f'{t:.2f}' for t in result.theta_trajectory]}")