# api/optimizer_endpoints.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date

from team_optimizer import (
    TeamOptimizationEngine,
    Player,
    LineupConstraints,
    OptimizationObjective,
    OptimizedLineup
)

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])

# =================================================================
# PYDANTIC MODELS
# =================================================================

class PlayerInput(BaseModel):
    """Player input for optimization"""
    id: int
    name: str
    position: str
    eligible_positions: List[str]
    team: str
    opponent: str
    game_date: date
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
    injury_status: str = "healthy"
    usage_rate: float
    salary: int = 0
    ownership_projection: float = 0.0
    is_locked: bool = False
    is_excluded: bool = False

class OptimizationRequest(BaseModel):
    """Request for lineup optimization"""
    players: List[PlayerInput]
    objective: str = "maximize_score"  # maximize_score, balance_categories, maximize_ceiling, minimize_risk
    num_lineups: int = Field(1, ge=1, le=20)
    max_players_per_team: int = Field(4, ge=1, le=5)
    max_salary: Optional[int] = None
    locked_player_ids: Optional[List[int]] = None
    excluded_player_ids: Optional[List[int]] = None

class LineupResponse(BaseModel):
    """Optimized lineup response"""
    lineup_id: int
    players: List[PlayerInput]
    total_score: float
    projected_points: float
    total_salary: int
    expected_value: float
    risk_score: float
    category_balance: dict
    team_stacks: dict
    game_stacks: dict
    metadata: dict

class OptimizationResponse(BaseModel):
    """Multiple lineups response"""
    lineups: List[LineupResponse]
    request_summary: dict
    optimization_time: float

# =================================================================
# API ENDPOINTS
# =================================================================

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_lineups(request: OptimizationRequest):
    """
    Optimize fantasy lineups based on player pool and constraints
    
    - **players**: Available player pool with projections
    - **objective**: Optimization objective (maximize_score, balance_categories, etc.)
    - **num_lineups**: Number of unique lineups to generate (1-20)
    - **max_players_per_team**: Maximum players from same team
    - **max_salary**: Maximum total salary (for DFS)
    - **locked_player_ids**: Players that must be in lineup
    - **excluded_player_ids**: Players that must not be in lineup
    """
    import time
    start_time = time.time()
    
    try:
        # Convert pydantic models to dataclass
        players = [
            Player(
                id=p.id,
                name=p.name,
                position=p.position,
                eligible_positions=p.eligible_positions,
                team=p.team,
                opponent=p.opponent,
                game_date=p.game_date,
                projected_points=p.projected_points,
                overall_score=p.overall_score,
                scoring_score=p.scoring_score,
                efficiency_score=p.efficiency_score,
                playmaking_score=p.playmaking_score,
                defense_score=p.defense_score,
                rebounding_score=p.rebounding_score,
                floor=p.floor,
                ceiling=p.ceiling,
                variance=p.variance,
                consistency_score=p.consistency_score,
                minutes_projection=p.minutes_projection,
                injury_status=p.injury_status,
                usage_rate=p.usage_rate,
                salary=p.salary,
                ownership_projection=p.ownership_projection,
                is_locked=p.is_locked,
                is_excluded=p.is_excluded
            )
            for p in request.players
        ]
        
        # Create constraints
        constraints = LineupConstraints(
            max_players_per_team=request.max_players_per_team,
            max_salary=request.max_salary,
            locked_players=request.locked_player_ids,
            excluded_players=request.excluded_player_ids
        )
        
        # Map objective string to enum
        objective_map = {
            'maximize_score': OptimizationObjective.MAXIMIZE_SCORE,
            'maximize_points': OptimizationObjective.MAXIMIZE_POINTS,
            'balance_categories': OptimizationObjective.BALANCE_CATEGORIES,
            'maximize_ceiling': OptimizationObjective.MAXIMIZE_CEILING,
            'minimize_risk': OptimizationObjective.MINIMIZE_RISK
        }
        objective = objective_map.get(request.objective, OptimizationObjective.MAXIMIZE_SCORE)
        
        # Optimize
        optimizer = TeamOptimizationEngine()
        optimized_lineups = optimizer.optimize_lineup(
            players,
            objective=objective,
            constraints=constraints,
            num_lineups=request.num_lineups
        )
        
        # Convert to response format
        lineup_responses = []
        for idx, lineup in enumerate(optimized_lineups, 1):
            # Get correlations
            correlations = optimizer.analyze_lineup_correlations(lineup)
            
            lineup_response = LineupResponse(
                lineup_id=idx,
                players=[
                    PlayerInput(
                        id=p.id,
                        name=p.name,
                        position=p.position,
                        eligible_positions=p.eligible_positions,
                        team=p.team,
                        opponent=p.opponent,
                        game_date=p.game_date,
                        projected_points=p.projected_points,
                        overall_score=p.overall_score,
                        scoring_score=p.scoring_score,
                        efficiency_score=p.efficiency_score,
                        playmaking_score=p.playmaking_score,
                        defense_score=p.defense_score,
                        rebounding_score=p.rebounding_score,
                        floor=p.floor,
                        ceiling=p.ceiling,
                        variance=p.variance,
                        consistency_score=p.consistency_score,
                        minutes_projection=p.minutes_projection,
                        injury_status=p.injury_status,
                        usage_rate=p.usage_rate,
                        salary=p.salary,
                        ownership_projection=p.ownership_projection
                    )
                    for p in lineup.players
                ],
                total_score=lineup.total_score,
                projected_points=lineup.projected_points,
                total_salary=lineup.total_salary,
                expected_value=lineup.expected_value,
                risk_score=lineup.risk_score,
                category_balance=lineup.category_balance,
                team_stacks=correlations.get('team_stacks', {}),
                game_stacks=correlations.get('game_stacks', {}),
                metadata=lineup.optimization_metadata
            )
            lineup_responses.append(lineup_response)
        
        optimization_time = time.time() - start_time
        
        return OptimizationResponse(
            lineups=lineup_responses,
            request_summary={
                'num_players_evaluated': len(request.players),
                'num_lineups_requested': request.num_lineups,
                'num_lineups_generated': len(lineup_responses),
                'objective': request.objective,
                'max_salary': request.max_salary,
                'locked_players': len(request.locked_player_ids or []),
                'excluded_players': len(request.excluded_player_ids or [])
            },
            optimization_time=round(optimization_time, 3)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.post("/analyze-player-pool")
async def analyze_player_pool(players: List[PlayerInput]):
    """
    Analyze player pool and provide recommendations
    
    Returns insights about player distribution, value opportunities, etc.
    """
    try:
        import numpy as np
        
        # Convert to Player objects
        player_objs = [
            Player(
                id=p.id, name=p.name, position=p.position,
                eligible_positions=p.eligible_positions,
                team=p.team, opponent=p.opponent, game_date=p.game_date,
                projected_points=p.projected_points, overall_score=p.overall_score,
                scoring_score=p.scoring_score, efficiency_score=p.efficiency_score,
                playmaking_score=p.playmaking_score, defense_score=p.defense_score,
                rebounding_score=p.rebounding_score,
                floor=p.floor, ceiling=p.ceiling, variance=p.variance,
                consistency_score=p.consistency_score,
                minutes_projection=p.minutes_projection,
                injury_status=p.injury_status, usage_rate=p.usage_rate,
                salary=p.salary, ownership_projection=p.ownership_projection
            )
            for p in players
        ]
        
        # Calculate value metrics
        values = []
        for p in player_objs:
            if p.salary > 0:
                value = p.projected_points / (p.salary / 1000)
                values.append({
                    'player_id': p.id,
                    'player_name': p.name,
                    'value': round(value, 3),
                    'projected_points': p.projected_points,
                    'salary': p.salary,
                    'ownership': p.ownership_projection
                })
        
        # Sort by value
        values.sort(key=lambda x: x['value'], reverse=True)
        
        # Position distribution
        position_dist = {}
        for p in player_objs:
            position_dist[p.position] = position_dist.get(p.position, 0) + 1
        
        # Team distribution
        team_dist = {}
        for p in player_objs:
            team_dist[p.team] = team_dist.get(p.team, 0) + 1
        
        # Score distribution
        scores = [p.overall_score for p in player_objs]
        
        # Injury concerns
        injury_concerns = [
            {'id': p.id, 'name': p.name, 'status': p.injury_status}
            for p in player_objs
            if p.injury_status not in ['healthy', '']
        ]
        
        # Value picks (high value, low ownership)
        value_picks = [
            v for v in values[:20]
            if v['ownership'] < 0.20  # Less than 20% owned
        ]
        
        # Contrarian plays (low ownership, high ceiling)
        contrarian = [
            {
                'player_id': p.id,
                'player_name': p.name,
                'ceiling': p.ceiling,
                'ownership': p.ownership_projection,
                'upside': round(p.ceiling - p.projected_points, 2)
            }
            for p in player_objs
            if p.ownership_projection < 0.15 and p.ceiling > p.projected_points * 1.3
        ]
        contrarian.sort(key=lambda x: x['upside'], reverse=True)
        
        return {
            'pool_summary': {
                'total_players': len(player_objs),
                'avg_projected_points': round(np.mean([p.projected_points for p in player_objs]), 2),
                'avg_score': round(np.mean([p.overall_score for p in player_objs]), 2),
                'avg_salary': round(np.mean([p.salary for p in player_objs if p.salary > 0]), 0),
                'position_distribution': position_dist,
                'team_distribution': team_dist
            },
            'top_values': values[:10],
            'value_picks': value_picks[:10],
            'contrarian_plays': contrarian[:10],
            'injury_concerns': injury_concerns,
            'score_distribution': {
                'mean': round(np.mean(scores), 2),
                'median': round(np.median(scores), 2),
                'std': round(np.std(scores), 2),
                'min': round(min(scores), 2),
                'max': round(max(scores), 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/compare-lineups")
async def compare_lineups(lineups: List[List[int]], player_pool: List[PlayerInput]):
    """
    Compare multiple lineups side by side
    
    - **lineups**: List of lineups (each is list of player IDs)
    - **player_pool**: Full player pool with projections
    """
    try:
        # Create player lookup
        player_lookup = {p.id: p for p in player_pool}
        
        comparisons = []
        
        for idx, lineup_ids in enumerate(lineups, 1):
            lineup_players = [player_lookup[pid] for pid in lineup_ids if pid in player_lookup]
            
            if not lineup_players:
                continue
            
            # Calculate lineup metrics
            total_score = sum(p.overall_score for p in lineup_players)
            projected_points = sum(p.projected_points for p in lineup_players)
            total_salary = sum(p.salary for p in lineup_players)
            avg_ownership = sum(p.ownership_projection for p in lineup_players) / len(lineup_players)
            
            # Category averages
            category_avg = {
                'scoring': sum(p.scoring_score for p in lineup_players) / len(lineup_players),
                'efficiency': sum(p.efficiency_score for p in lineup_players) / len(lineup_players),
                'playmaking': sum(p.playmaking_score for p in lineup_players) / len(lineup_players),
                'defense': sum(p.defense_score for p in lineup_players) / len(lineup_players),
                'rebounding': sum(p.rebounding_score for p in lineup_players) / len(lineup_players)
            }
            
            # Risk metrics
            floor_total = sum(p.floor for p in lineup_players)
            ceiling_total = sum(p.ceiling for p in lineup_players)
            variance_avg = sum(p.variance for p in lineup_players) / len(lineup_players)
            
            # Team stacks
            team_counts = {}
            for p in lineup_players:
                team_counts[p.team] = team_counts.get(p.team, 0) + 1
            
            comparisons.append({
                'lineup_number': idx,
                'players': [p.name for p in lineup_players],
                'total_score': round(total_score, 2),
                'projected_points': round(projected_points, 2),
                'floor': round(floor_total, 2),
                'ceiling': round(ceiling_total, 2),
                'total_salary': total_salary,
                'avg_ownership': round(avg_ownership, 3),
                'variance': round(variance_avg, 2),
                'category_averages': {k: round(v, 2) for k, v in category_avg.items()},
                'team_stacks': {t: c for t, c in team_counts.items() if c >= 2}
            })
        
        # Find best in each category
        best_score = max(comparisons, key=lambda x: x['total_score'])
        best_ceiling = max(comparisons, key=lambda x: x['ceiling'])
        safest = max(comparisons, key=lambda x: x['floor'])
        most_contrarian = min(comparisons, key=lambda x: x['avg_ownership'])
        
        return {
            'lineups': comparisons,
            'recommendations': {
                'highest_score': best_score['lineup_number'],
                'highest_ceiling': best_ceiling['lineup_number'],
                'safest_floor': safest['lineup_number'],
                'most_contrarian': most_contrarian['lineup_number']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/player-projections/{player_id}")
async def get_player_projections(
    player_id: int,
    date: Optional[date] = None
):
    """
    Get detailed projections for a specific player
    """
    # This would fetch from database
    # Placeholder implementation
    return {
        'player_id': player_id,
        'date': date or date.today(),
        'projections': {
            'points': 28.5,
            'rebounds': 8.5,
            'assists': 9.2,
            'overall_score': 94.2
        },
        'range': {
            'floor': 22.0,
            'projection': 28.5,
            'ceiling': 38.0
        },
        'historical_performance': {
            'last_5_games': [27.5, 31.2, 25.8, 29.3, 28.1],
            'vs_opponent_avg': 30.2,
            'home_vs_away': {'home': 29.5, 'away': 27.3}
        }
    }


@router.post("/lineup-builder/suggestions")
async def get_lineup_suggestions(
    current_lineup: List[int],
    player_pool: List[PlayerInput],
    position_needed: str
):
    """
    Get player suggestions to complete a lineup
    
    Suggests players that complement existing lineup
    """
    try:
        # Get current lineup players
        player_lookup = {p.id: p for p in player_pool}
        current_players = [player_lookup[pid] for pid in current_lineup if pid in player_lookup]
        
        # Calculate current lineup stats
        current_categories = {
            'scoring': sum(p.scoring_score for p in current_players) / max(len(current_players), 1),
            'efficiency': sum(p.efficiency_score for p in current_players) / max(len(current_players), 1),
            'playmaking': sum(p.playmaking_score for p in current_players) / max(len(current_players), 1),
            'defense': sum(p.defense_score for p in current_players) / max(len(current_players), 1),
            'rebounding': sum(p.rebounding_score for p in current_players) / max(len(current_players), 1)
        }
        
        # Find weakest category
        weakest_cat = min(current_categories, key=current_categories.get)
        
        # Get available players for position
        available = [
            p for p in player_pool
            if p.id not in current_lineup
            and position_needed in p.eligible_positions
        ]
        
        # Score players based on filling needs
        scored_players = []
        for p in available:
            # Base score
            base_score = p.overall_score
            
            # Bonus for filling weak category
            weak_cat_score = getattr(p, f'{weakest_cat}_score', 0)
            bonus = (weak_cat_score - current_categories[weakest_cat]) * 0.2
            
            final_score = base_score + bonus
            
            scored_players.append({
                'player_id': p.id,
                'player_name': p.name,
                'score': round(final_score, 2),
                'fills_need': weakest_cat,
                'category_score': weak_cat_score,
                'projected_points': p.projected_points,
                'salary': p.salary
            })
        
        # Sort by score
        scored_players.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'position_needed': position_needed,
            'current_lineup_size': len(current_players),
            'weakest_category': weakest_cat,
            'current_category_avg': round(current_categories[weakest_cat], 2),
            'suggestions': scored_players[:15]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Suggestions failed: {str(e)}")


@router.post("/export-lineup")
async def export_lineup(
    lineup: List[PlayerInput],
    format: str = Query("csv", regex="^(csv|json|dfs)$")
):
    """
    Export lineup in various formats
    
    - **csv**: CSV format for import
    - **json**: JSON format
    - **dfs**: DraftKings/FanDuel format
    """
    try:
        if format == "json":
            return {
                'format': 'json',
                'lineup': [
                    {
                        'name': p.name,
                        'position': p.position,
                        'team': p.team,
                        'opponent': p.opponent,
                        'salary': p.salary,
                        'projected_points': p.projected_points,
                        'overall_score': p.overall_score
                    }
                    for p in lineup
                ]
            }
        
        elif format == "csv":
            csv_lines = ["Name,Position,Team,Opponent,Salary,Projected Points,Score"]
            for p in lineup:
                csv_lines.append(
                    f"{p.name},{p.position},{p.team},{p.opponent},"
                    f"{p.salary},{p.projected_points},{p.overall_score}"
                )
            return {
                'format': 'csv',
                'content': '\n'.join(csv_lines)
            }
        
        elif format == "dfs":
            # DraftKings format
            return {
                'format': 'draftkings',
                'lineup': [
                    {
                        'roster_position': idx + 1,
                        'player_name': p.name,
                        'player_id': p.id,
                        'position': p.position,
                        'team': p.team
                    }
                    for idx, p in enumerate(lineup)
                ]
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/optimization-presets")
async def get_optimization_presets():
    """
    Get predefined optimization presets for different scenarios
    """
    return {
        'presets': [
            {
                'name': 'Cash Game Safe',
                'objective': 'minimize_risk',
                'description': 'High floor players with consistent performance',
                'settings': {
                    'objective': 'minimize_risk',
                    'max_players_per_team': 3,
                    'prefer_high_consistency': True
                }
            },
            {
                'name': 'Tournament GPP',
                'objective': 'maximize_ceiling',
                'description': 'High upside players with tournament leverage',
                'settings': {
                    'objective': 'maximize_ceiling',
                    'max_players_per_team': 4,
                    'prefer_low_ownership': True
                }
            },
            {
                'name': 'Balanced Build',
                'objective': 'balance_categories',
                'description': 'Well-rounded lineup across all categories',
                'settings': {
                    'objective': 'balance_categories',
                    'max_players_per_team': 4
                }
            },
            {
                'name': 'Stars and Scrubs',
                'objective': 'maximize_score',
                'description': 'Load up on superstars, fill with value',
                'settings': {
                    'objective': 'maximize_score',
                    'max_players_per_team': 4,
                    'salary_strategy': 'top_heavy'
                }
            },
            {
                'name': 'Game Stack',
                'objective': 'maximize_ceiling',
                'description': 'Stack players from high-scoring games',
                'settings': {
                    'objective': 'maximize_ceiling',
                    'max_players_per_team': 5,
                    'min_different_games': 1
                }
            }
        ]
    }


# Health check
@router.get("/health")
async def optimizer_health():
    """Health check for optimizer service"""
    try:
        # Test optimizer instantiation
        optimizer = TeamOptimizationEngine()
        
        return {
            'status': 'healthy',
            'service': 'team_optimizer',
            'version': '1.0.0'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
                