# scoring_service.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from scipy import stats

@dataclass
class PlayerMetrics:
    """Raw player statistics"""
    player_id: str
    games_played: int
    minutes: float
    points: float
    rebounds: float
    assists: float
    steals: float
    blocks: float
    turnovers: float
    fg_made: float
    fg_attempted: float
    fg3_made: float
    fg3_attempted: float
    ft_made: float
    ft_attempted: float
    plus_minus: float
    usage_rate: float
    
@dataclass
class ScoringResult:
    """Comprehensive scoring output"""
    player_id: str
    overall_score: float
    category_scores: Dict[str, float]
    percentile_ranks: Dict[str, float]
    trend_direction: str
    confidence_score: float
    alerts: List[str]
    timestamp: datetime

class PlayerScoringEngine:
    """
    Advanced player scoring system with multiple weighted categories
    """
    
    # Category weights (must sum to 1.0)
    WEIGHTS = {
        'scoring': 0.25,
        'efficiency': 0.20,
        'playmaking': 0.15,
        'defense': 0.15,
        'rebounding': 0.10,
        'consistency': 0.15
    }
    
    # League average baselines (would come from database)
    LEAGUE_AVERAGES = {
        'points': 15.0,
        'rebounds': 5.0,
        'assists': 4.0,
        'steals': 0.8,
        'blocks': 0.6,
        'fg_pct': 0.46,
        'fg3_pct': 0.36,
        'ft_pct': 0.78,
        'usage_rate': 22.0,
        'plus_minus': 0.0
    }
    
    def __init__(self):
        self.position_adjustments = self._init_position_adjustments()
        
    def _init_position_adjustments(self) -> Dict[str, Dict[str, float]]:
        """Position-specific scoring adjustments"""
        return {
            'PG': {'playmaking': 1.2, 'scoring': 0.9, 'rebounding': 0.7},
            'SG': {'scoring': 1.1, 'playmaking': 0.9, 'defense': 1.0},
            'SF': {'scoring': 1.0, 'defense': 1.1, 'rebounding': 0.9},
            'PF': {'rebounding': 1.2, 'defense': 1.1, 'scoring': 0.9},
            'C': {'rebounding': 1.3, 'defense': 1.2, 'playmaking': 0.7}
        }
    
    def calculate_score(
        self,
        current: PlayerMetrics,
        historical: List[PlayerMetrics],
        position: str,
        league_data: Optional[List[PlayerMetrics]] = None
    ) -> ScoringResult:
        """
        Calculate comprehensive player score
        
        Args:
            current: Current period metrics
            historical: Previous periods for trend analysis
            position: Player position
            league_data: League-wide data for percentile calculation
        """
        
        # Calculate each category score
        category_scores = {
            'scoring': self._score_scoring(current, position),
            'efficiency': self._score_efficiency(current, position),
            'playmaking': self._score_playmaking(current, position),
            'defense': self._score_defense(current, position),
            'rebounding': self._score_rebounding(current, position),
            'consistency': self._score_consistency(current, historical)
        }
        
        # Calculate weighted overall score
        overall = sum(
            score * self.WEIGHTS[cat] 
            for cat, score in category_scores.items()
        )
        
        # Calculate percentiles if league data available
        percentiles = {}
        if league_data:
            percentiles = self._calculate_percentiles(current, league_data)
        
        # Determine trend
        trend = self._analyze_trend(current, historical)
        
        # Calculate confidence based on sample size
        confidence = self._calculate_confidence(current, historical)
        
        # Generate alerts
        alerts = self._generate_alerts(current, historical, category_scores)
        
        return ScoringResult(
            player_id=current.player_id,
            overall_score=round(overall, 1),
            category_scores={k: round(v, 1) for k, v in category_scores.items()},
            percentile_ranks=percentiles,
            trend_direction=trend,
            confidence_score=confidence,
            alerts=alerts,
            timestamp=datetime.now()
        )
    
    def _score_scoring(self, metrics: PlayerMetrics, position: str) -> float:
        """
        Score player's scoring ability (0-100 scale)
        Factors: PPG, shooting volume, true shooting %
        """
        # Points per game component (40%)
        ppg_score = min(100, (metrics.points / 30) * 100)
        
        # True shooting percentage component (40%)
        ts_pct = self._calculate_true_shooting(metrics)
        ts_score = min(100, (ts_pct / 0.65) * 100)
        
        # Volume component (20%)
        volume_score = min(100, (metrics.fg_attempted / 20) * 100)
        
        raw_score = (ppg_score * 0.4 + ts_score * 0.4 + volume_score * 0.2)
        
        # Apply position adjustment
        adjustment = self.position_adjustments.get(position, {}).get('scoring', 1.0)
        return min(100, raw_score * adjustment)
    
    def _score_efficiency(self, metrics: PlayerMetrics, position: str) -> float:
        """
        Score player's efficiency (0-100 scale)
        Factors: TS%, AST/TO ratio, usage rate efficiency
        """
        # True shooting percentage (50%)
        ts_pct = self._calculate_true_shooting(metrics)
        ts_score = min(100, (ts_pct / 0.65) * 100)
        
        # Assist to turnover ratio (30%)
        ast_to_ratio = metrics.assists / max(metrics.turnovers, 0.5)
        ratio_score = min(100, (ast_to_ratio / 3.0) * 100)
        
        # Usage rate efficiency (20%)
        # Points per usage rate
        usage_eff = metrics.points / max(metrics.usage_rate, 10)
        usage_score = min(100, (usage_eff / 1.2) * 100)
        
        return ts_score * 0.5 + ratio_score * 0.3 + usage_score * 0.2
    
    def _score_playmaking(self, metrics: PlayerMetrics, position: str) -> float:
        """
        Score player's playmaking ability (0-100 scale)
        Factors: APG, AST%, pure point rating
        """
        # Assists per game (60%)
        apg_score = min(100, (metrics.assists / 10) * 100)
        
        # Assist to turnover ratio (40%)
        ast_to_ratio = metrics.assists / max(metrics.turnovers, 0.5)
        ratio_score = min(100, (ast_to_ratio / 4.0) * 100)
        
        raw_score = apg_score * 0.6 + ratio_score * 0.4
        
        # Apply position adjustment
        adjustment = self.position_adjustments.get(position, {}).get('playmaking', 1.0)
        return min(100, raw_score * adjustment)
    
    def _score_defense(self, metrics: PlayerMetrics, position: str) -> float:
        """
        Score player's defensive impact (0-100 scale)
        Factors: STL, BLK, defensive plus-minus
        """
        # Steals component (40%)
        stl_score = min(100, (metrics.steals / 2.0) * 100)
        
        # Blocks component (30%)
        blk_score = min(100, (metrics.blocks / 2.0) * 100)
        
        # Plus-minus component (30%)
        pm_score = min(100, max(0, (metrics.plus_minus + 10) / 20 * 100))
        
        raw_score = stl_score * 0.4 + blk_score * 0.3 + pm_score * 0.3
        
        # Apply position adjustment
        adjustment = self.position_adjustments.get(position, {}).get('defense', 1.0)
        return min(100, raw_score * adjustment)
    
    def _score_rebounding(self, metrics: PlayerMetrics, position: str) -> float:
        """
        Score player's rebounding (0-100 scale)
        """
        # Rebounds per game
        rpg_score = min(100, (metrics.rebounds / 12) * 100)
        
        # Apply position adjustment
        adjustment = self.position_adjustments.get(position, {}).get('rebounding', 1.0)
        return min(100, rpg_score * adjustment)
    
    def _score_consistency(
        self, 
        current: PlayerMetrics, 
        historical: List[PlayerMetrics]
    ) -> float:
        """
        Score performance consistency (0-100 scale)
        Based on variance in key stats over time
        """
        if not historical or len(historical) < 3:
            return 75.0  # Default neutral score
        
        # Extract key metrics over time
        points = [m.points for m in historical] + [current.points]
        efficiency = [self._calculate_true_shooting(m) for m in historical] + \
                    [self._calculate_true_shooting(current)]
        
        # Calculate coefficient of variation (lower is better)
        cv_points = np.std(points) / max(np.mean(points), 1.0)
        cv_efficiency = np.std(efficiency) / max(np.mean(efficiency), 0.01)
        
        # Convert to 0-100 scale (invert so lower variance = higher score)
        points_consistency = max(0, 100 - (cv_points * 200))
        eff_consistency = max(0, 100 - (cv_efficiency * 200))
        
        return (points_consistency * 0.6 + eff_consistency * 0.4)
    
    def _calculate_true_shooting(self, metrics: PlayerMetrics) -> float:
        """Calculate true shooting percentage"""
        total_attempts = 2 * (metrics.fg_attempted + 0.44 * metrics.ft_attempted)
        if total_attempts == 0:
            return 0.0
        return metrics.points / total_attempts
    
    def _calculate_percentiles(
        self,
        player: PlayerMetrics,
        league_data: List[PlayerMetrics]
    ) -> Dict[str, float]:
        """Calculate player's percentile rank in each category"""
        percentiles = {}
        
        # Points percentile
        league_points = [p.points for p in league_data]
        percentiles['points'] = stats.percentileofscore(league_points, player.points)
        
        # Efficiency percentile
        league_ts = [self._calculate_true_shooting(p) for p in league_data]
        player_ts = self._calculate_true_shooting(player)
        percentiles['efficiency'] = stats.percentileofscore(league_ts, player_ts)
        
        # Assists percentile
        league_assists = [p.assists for p in league_data]
        percentiles['assists'] = stats.percentileofscore(league_assists, player.assists)
        
        # Rebounds percentile
        league_rebounds = [p.rebounds for p in league_data]
        percentiles['rebounds'] = stats.percentileofscore(league_rebounds, player.rebounds)
        
        return {k: round(v, 1) for k, v in percentiles.items()}
    
    def _analyze_trend(
        self,
        current: PlayerMetrics,
        historical: List[PlayerMetrics]
    ) -> str:
        """
        Analyze performance trend over time
        Returns: 'up', 'down', or 'stable'
        """
        if not historical or len(historical) < 2:
            return 'stable'
        
        # Calculate scores for historical periods
        recent_scores = []
        for metrics in historical[-3:]:  # Last 3 periods
            score = self._score_scoring(metrics, 'SG')  # Use neutral position
            recent_scores.append(score)
        
        current_score = self._score_scoring(current, 'SG')
        recent_scores.append(current_score)
        
        # Linear regression to detect trend
        x = np.arange(len(recent_scores))
        slope, _, _, _, _ = stats.linregress(x, recent_scores)
        
        # Classify trend
        if slope > 1.5:
            return 'up'
        elif slope < -1.5:
            return 'down'
        else:
            return 'stable'
    
    def _calculate_confidence(
        self,
        current: PlayerMetrics,
        historical: List[PlayerMetrics]
    ) -> float:
        """
        Calculate confidence score based on sample size and stability
        Returns 0-1 confidence score
        """
        # Base confidence on games played
        games_confidence = min(1.0, current.games_played / 15)
        
        # Historical stability factor
        if historical and len(historical) >= 3:
            all_games = [m.games_played for m in historical] + [current.games_played]
            stability = 1.0 - (np.std(all_games) / max(np.mean(all_games), 1.0))
            stability = max(0.5, stability)
        else:
            stability = 0.7
        
        return round(games_confidence * 0.6 + stability * 0.4, 2)
    
    def _generate_alerts(
        self,
        current: PlayerMetrics,
        historical: List[PlayerMetrics],
        category_scores: Dict[str, float]
    ) -> List[str]:
        """Generate performance alerts and warnings"""
        alerts = []
        
        # Check for exceptional performance
        if category_scores['scoring'] >= 95:
            alerts.append("Elite scoring performance - Top 5% league-wide")
        
        if category_scores['efficiency'] >= 95:
            alerts.append("Career-high efficiency week")
        
        # Check for concerning trends
        if historical and len(historical) >= 2:
            # Minutes trend
            recent_minutes = [m.minutes for m in historical[-2:]] + [current.minutes]
            if all(recent_minutes[i] > recent_minutes[i+1] for i in range(len(recent_minutes)-1)):
                alerts.append("Decreased minutes last 3 weeks - monitor closely")
            
            # Turnover increase
            recent_to = [m.turnovers for m in historical[-2:]] + [current.turnovers]
            if current.turnovers > np.mean(recent_to[:-1]) * 1.3:
                alerts.append("Turnover rate elevated - 30% above recent average")
        
        # Check usage and load
        if current.usage_rate > 30:
            alerts.append("High usage rate - monitor for fatigue")
        
        # Efficiency concerns
        ts_pct = self._calculate_true_shooting(current)
        if ts_pct < 0.50:
            alerts.append("Below-average shooting efficiency - consider shot selection")
        
        # Positive consistency
        if category_scores['consistency'] >= 90:
            alerts.append("Highly consistent performance - reliable fantasy asset")
        
        return alerts


class ScoringAPIService:
    """
    API service layer for scoring system integration
    """
    
    def __init__(self):
        self.engine = PlayerScoringEngine()
        self.cache = {}  # Simple cache for demo
    
    def score_player(
        self,
        player_id: str,
        timeframe: str = 'current'
    ) -> Dict:
        """
        Main API endpoint for player scoring
        
        Args:
            player_id: Unique player identifier
            timeframe: 'current', 'week', 'month', 'season'
        """
        # Fetch player data (would be from database)
        current, historical, position = self._fetch_player_data(player_id, timeframe)
        
        # Fetch league data for percentiles
        league_data = self._fetch_league_data(timeframe)
        
        # Calculate score
        result = self.engine.calculate_score(current, historical, position, league_data)
        
        # Format for API response
        return {
            'player_id': result.player_id,
            'score': result.overall_score,
            'categories': result.category_scores,
            'percentiles': result.percentile_ranks,
            'trend': result.trend_direction,
            'confidence': result.confidence_score,
            'alerts': result.alerts,
            'timestamp': result.timestamp.isoformat(),
            'metadata': {
                'timeframe': timeframe,
                'games_played': current.games_played,
                'minutes_per_game': round(current.minutes, 1)
            }
        }
    
    def batch_score_players(
        self,
        player_ids: List[str],
        timeframe: str = 'current'
    ) -> List[Dict]:
        """Score multiple players in batch"""
        return [self.score_player(pid, timeframe) for pid in player_ids]
    
    def compare_players(
        self,
        player_ids: List[str],
        timeframe: str = 'current'
    ) -> Dict:
        """Compare multiple players side by side"""
        scores = self.batch_score_players(player_ids, timeframe)
        
        return {
            'players': scores,
            'comparison': {
                'highest_overall': max(scores, key=lambda x: x['score']),
                'highest_by_category': self._get_category_leaders(scores),
                'most_consistent': max(scores, key=lambda x: x['categories']['consistency'])
            }
        }
    
    def get_trending_players(
        self,
        direction: str = 'up',
        limit: int = 10
    ) -> List[Dict]:
        """Get players with strongest trends"""
        # Would query database for all players
        all_players = self._fetch_all_players()
        
        # Filter by trend direction
        trending = [p for p in all_players if p['trend'] == direction]
        
        # Sort by score and limit
        trending.sort(key=lambda x: x['score'], reverse=True)
        return trending[:limit]
    
    def _fetch_player_data(self, player_id: str, timeframe: str):
        """Mock data fetching - would be actual database queries"""
        # This would fetch from database
        current = PlayerMetrics(
            player_id=player_id,
            games_played=10,
            minutes=35.0,
            points=28.5,
            rebounds=8.5,
            assists=9.2,
            steals=1.5,
            blocks=0.5,
            turnovers=3.2,
            fg_made=9.5,
            fg_attempted=19.0,
            fg3_made=2.5,
            fg3_attempted=7.0,
            ft_made=7.0,
            ft_attempted=8.0,
            plus_minus=5.5,
            usage_rate=32.0
        )
        
        historical = []
        position = 'PG'
        
        return current, historical, position
    
    def _fetch_league_data(self, timeframe: str) -> List[PlayerMetrics]:
        """Fetch league-wide data for percentile calculations"""
        return []  # Would return all players' metrics
    
    def _fetch_all_players(self) -> List[Dict]:
        """Fetch all players for trending analysis"""
        return []  # Would return all scored players
    
    def _get_category_leaders(self, scores: List[Dict]) -> Dict:
        """Find category leaders from comparison"""
        categories = ['scoring', 'efficiency', 'playmaking', 'defense', 'rebounding']
        leaders = {}
        
        for cat in categories:
            leaders[cat] = max(scores, key=lambda x: x['categories'][cat])
        
        return leaders


# Usage Examples
if __name__ == "__main__":
    # Initialize service
    service = ScoringAPIService()
    
    # Score single player
    result = service.score_player("player_123", timeframe='current')
    print(f"Player Score: {result['score']}")
    print(f"Categories: {result['categories']}")
    print(f"Alerts: {result['alerts']}")
    
    # Compare multiple players
    comparison = service.compare_players(
        ["player_123", "player_456", "player_789"]
    )
    print(f"\nHighest Overall: {comparison['comparison']['highest_overall']['player_id']}")
    
    # Get trending players
    trending_up = service.get_trending_players(direction='up', limit=5)
    print(f"\nTop 5 Trending Up: {[p['player_id'] for p in trending_up]}")

        