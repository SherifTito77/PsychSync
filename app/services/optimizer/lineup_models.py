from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LineupConstraints:
    max_players_per_team: int
    max_salary: Optional[int] = None
    locked_players: Optional[List[int]] = None
    excluded_players: Optional[List[int]] = None


@dataclass
class OptimizationObjective:
    MAXIMIZE_SCORE = "maximize_score"
    MAXIMIZE_POINTS = "maximize_points"
    BALANCE_CATEGORIES = "balance_categories"
    MAXIMIZE_CEILING = "maximize_ceiling"
    MINIMIZE_RISK = "minimize_risk"


@dataclass
class OptimizedLineup:
    players: List
    total_score: float
    projected_points: float
    total_salary: int
    expected_value: float
    risk_score: float
    category_balance: dict
    optimization_metadata: dict


@dataclass
class Player:
    id: int
    name: str
    position: str
    eligible_positions: List[str]
    team: str
    opponent: str
    game_date: str
    projected_points: float
    overall_score: float
    scoring_score: float
    efficiency_score: float
    playmaking_score: float
    defense_score: float
    rebounding_score: float
    floor: float
    ceiling: float
    variance: float
    consistency_score: float
    minutes_projection: float
    injury_status: str
    usage_rate: float
    salary: int
    ownership_projection: float
    is_locked: bool
    is_excluded: bool
