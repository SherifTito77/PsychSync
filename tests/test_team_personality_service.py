"""
Unit Tests for Team Personality Service
Tests for team personality aggregation, insights generation, and team comparison.

Coverage Areas:
- Dimension statistics calculation
- Team composition type determination
- Strengths and gaps generation
- Compatibility and diversity scoring
- Caching behavior
- Edge cases and error handling
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.assessment import Assessment
from app.db.models.score import Score
from app.db.models.team import Team, TeamMember
from app.db.models.team_personality_map import TeamPersonalityMap
from app.services.team_personality_service import TeamPersonalityService


class TestCalculateDimensionStats:
    """Test dimension statistics calculation"""

    def test_calculate_dimension_stats_normal_case(self):
        """Test statistics calculation with normal data"""
        scores = [3.5, 4.0, 4.5, 3.0, 3.8]

        result = TeamPersonalityService._calculate_dimension_stats(scores)

        assert result["avg"] == 3.76
        assert result["min"] == 3.0
        assert result["max"] == 4.5
        assert 0.0 < result["std_dev"] < 1.0
        assert len(result["distribution"]) == 5
        assert sum(result["distribution"]) == 100.0

    def test_calculate_dimension_stats_empty_list(self):
        """Test statistics calculation with empty scores"""
        scores = []

        result = TeamPersonalityService._calculate_dimension_stats(scores)

        assert result["avg"] == 0.0
        assert result["min"] == 0.0
        assert result["max"] == 0.0
        assert result["std_dev"] == 0.0
        assert result["distribution"] == [0, 0, 0, 0, 0]

    def test_calculate_dimension_stats_uniform_scores(self):
        """Test statistics calculation when all scores are identical"""
        scores = [3.0, 3.0, 3.0, 3.0, 3.0]

        result = TeamPersonalityService._calculate_dimension_stats(scores)

        assert result["avg"] == 3.0
        assert result["min"] == 3.0
        assert result["max"] == 3.0
        assert result["std_dev"] == 0.0
        assert result["distribution"] == [0, 0, 100.0, 0, 0]

    def test_calculate_dimension_stats_extreme_values(self):
        """Test statistics calculation with min/max values"""
        scores = [1.0, 1.0, 5.0, 5.0, 3.0]

        result = TeamPersonalityService._calculate_dimension_stats(scores)

        assert result["avg"] == 3.0
        assert result["min"] == 1.0
        assert result["max"] == 5.0
        assert result["std_dev"] > 0
        assert result["distribution"] == [40.0, 0, 20.0, 0, 40.0]

    def test_calculate_dimension_stats_distribution_quintiles(self):
        """Test distribution calculation maps scores to correct quintiles"""
        # Very low (≤1.0), Low (≤2.0), Medium (≤3.0), High (≤4.0), Very High (>4.0)
        scores = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

        result = TeamPersonalityService._calculate_dimension_stats(scores)

        # Very low: 0.5, 1.0 (2 scores)
        assert result["distribution"][0] == 20.0
        # Low: 1.5, 2.0 (2 scores)
        assert result["distribution"][1] == 20.0
        # Medium: 2.5, 3.0 (2 scores)
        assert result["distribution"][2] == 20.0
        # High: 3.5, 4.0 (2 scores)
        assert result["distribution"][3] == 20.0
        # Very high: 4.5, 5.0 (2 scores)
        assert result["distribution"][4] == 20.0


class TestDetermineCompositionType:
    """Test team composition type determination"""

    def test_creative_social_team(self):
        """Test determination of Creative & Social team type"""
        dimension_stats = {
            "Openness": {"avg": 4.2},
            "Extraversion": {"avg": 4.0},
            "Conscientiousness": {"avg": 3.0},
            "Agreeableness": {"avg": 3.0},
            "Neuroticism": {"avg": 2.5},
        }

        result = TeamPersonalityService._determine_composition_type(dimension_stats)

        assert result == "Creative & Social"

    def test_strategic_thinkers_team(self):
        """Test determination of Strategic Thinkers team type"""
        dimension_stats = {
            "Openness": {"avg": 4.0},
            "Conscientiousness": {"avg": 4.2},
            "Extraversion": {"avg": 3.0},
            "Agreeableness": {"avg": 3.0},
            "Neuroticism": {"avg": 2.5},
        }

        result = TeamPersonalityService._determine_composition_type(dimension_stats)

        assert result == "Strategic Thinkers"

    def test_balanced_team(self):
        """Test determination of Balanced Team type"""
        dimension_stats = {
            "Openness": {"avg": 3.0},
            "Conscientiousness": {"avg": 3.0},
            "Extraversion": {"avg": 3.0},
            "Agreeableness": {"avg": 3.0},
            "Neuroticism": {"avg": 3.0},
        }

        result = TeamPersonalityService._determine_composition_type(dimension_stats)

        assert result == "Balanced Team"

    def test_empty_dimension_stats(self):
        """Test determination with empty dimension stats"""
        dimension_stats = {}

        result = TeamPersonalityService._determine_composition_type(dimension_stats)

        assert result == "Unknown"

    def test_people_oriented_team(self):
        """Test determination of People-Oriented team type"""
        dimension_stats = {
            "Extraversion": {"avg": 4.2},
            "Agreeableness": {"avg": 4.0},
            "Openness": {"avg": 3.0},
            "Conscientiousness": {"avg": 3.0},
            "Neuroticism": {"avg": 2.5},
        }

        result = TeamPersonalityService._determine_composition_type(dimension_stats)

        assert result == "People-Oriented"


class TestGenerateStrengthsAndGaps:
    """Test strengths and gaps generation"""

    def test_high_openness_generates_creative_strength(self):
        """Test high Openness generates creative problem-solving strength"""
        dimension_stats = {
            "Openness": {"avg": 4.0, "std_dev": 0.5},
            "Conscientiousness": {"avg": 3.0, "std_dev": 0.5},
            "Extraversion": {"avg": 3.0, "std_dev": 0.5},
            "Agreeableness": {"avg": 3.0, "std_dev": 0.5},
            "Neuroticism": {"avg": 3.0, "std_dev": 0.5},
        }

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        assert "Creative problem-solving and innovation" in strengths

    def test_low_conscientiousness_generates_organisation_gap(self):
        """Test low Conscientiousness generates organization gap"""
        dimension_stats = {
            "Openness": {"avg": 3.0, "std_dev": 0.5},
            "Conscientiousness": {"avg": 2.0, "std_dev": 0.5},
            "Extraversion": {"avg": 3.0, "std_dev": 0.5},
            "Agreeableness": {"avg": 3.0, "std_dev": 0.5},
            "Neuroticism": {"avg": 3.0, "std_dev": 0.5},
        }

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        assert "May struggle with organization and follow-through" in gaps

    def test_low_neuroticism_generates_stability_strength(self):
        """Test low Neuroticism generates emotional stability strength"""
        dimension_stats = {
            "Openness": {"avg": 3.0, "std_dev": 0.5},
            "Conscientiousness": {"avg": 3.0, "std_dev": 0.5},
            "Extraversion": {"avg": 3.0, "std_dev": 0.5},
            "Agreeableness": {"avg": 3.0, "std_dev": 0.5},
            "Neuroticism": {"avg": 1.5, "std_dev": 0.5},
        }

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        assert "Emotional stability and stress resilience" in strengths

    def test_high_extraversion_generates_communication_strength(self):
        """Test high Extraversion generates communication strength"""
        dimension_stats = {
            "Openness": {"avg": 3.0, "std_dev": 0.5},
            "Conscientiousness": {"avg": 3.0, "std_dev": 0.5},
            "Extraversion": {"avg": 4.2, "std_dev": 0.5},
            "Agreeableness": {"avg": 3.0, "std_dev": 0.5},
            "Neuroticism": {"avg": 3.0, "std_dev": 0.5},
        }

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        assert "Excellent communication and social engagement" in strengths

    def test_low_diversity_generates_diversity_gap(self):
        """Test low diversity (low std_dev) generates perspective variety gap"""
        dimension_stats = {
            "Openness": {"avg": 3.0, "std_dev": 0.2},
            "Conscientiousness": {"avg": 3.0, "std_dev": 0.3},
            "Extraversion": {"avg": 3.0, "std_dev": 0.2},
            "Agreeableness": {"avg": 3.0, "std_dev": 0.3},
            "Neuroticism": {"avg": 3.0, "std_dev": 0.2},
        }

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        assert "Low personality diversity may limit perspective variety" in gaps

    def test_empty_dimension_stats(self):
        """Test with empty dimension stats"""
        dimension_stats = {}

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        assert len(strengths) == 0
        assert len(gaps) == 0

    def test_multiple_strengths_and_gaps(self):
        """Test generation of multiple strengths and gaps"""
        dimension_stats = {
            "Openness": {"avg": 4.0, "std_dev": 0.8},
            "Conscientiousness": {"avg": 2.0, "std_dev": 0.8},
            "Extraversion": {"avg": 4.0, "std_dev": 0.8},
            "Agreeableness": {"avg": 4.0, "std_dev": 0.8},
            "Neuroticism": {"avg": 1.5, "std_dev": 0.8},
        }

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        # Should have multiple strengths
        assert len(strengths) >= 3
        # Should have at least one gap (low conscientiousness)
        assert len(gaps) >= 1


class TestCalculateCompatibility:
    """Test internal compatibility scoring"""

    def test_optimal_compatibility(self):
        """Test compatibility score with optimal diversity (std_dev ~0.7-1.0)"""
        dimension_stats = {
            "Openness": {"std_dev": 0.8},
            "Conscientiousness": {"std_dev": 0.9},
            "Extraversion": {"std_dev": 0.7},
            "Agreeableness": {"std_dev": 0.8},
            "Neuroticism": {"std_dev": 0.9},
        }

        result = TeamPersonalityService._calculate_compatibility(dimension_stats)

        assert result == 0.9

    def test_low_diversity_compatibility(self):
        """Test compatibility score with low diversity (std_dev < 0.5)"""
        dimension_stats = {
            "Openness": {"std_dev": 0.3},
            "Conscientiousness": {"std_dev": 0.4},
            "Extraversion": {"std_dev": 0.3},
            "Agreeableness": {"std_dev": 0.4},
            "Neuroticism": {"std_dev": 0.3},
        }

        result = TeamPersonalityService._calculate_compatibility(dimension_stats)

        # Should be 0.5 + avg_std_dev, so around 0.8-0.9
        assert 0.5 < result < 1.0

    def test_high_diversity_compatibility(self):
        """Test compatibility score with high diversity (std_dev > 1.5)"""
        dimension_stats = {
            "Openness": {"std_dev": 1.8},
            "Conscientiousness": {"std_dev": 1.7},
            "Extraversion": {"std_dev": 1.9},
            "Agreeableness": {"std_dev": 1.8},
            "Neuroticism": {"std_dev": 1.7},
        }

        result = TeamPersonalityService._calculate_compatibility(dimension_stats)

        # Should be reduced for very high diversity
        assert 0.5 <= result < 1.0

    def test_empty_dimension_stats(self):
        """Test compatibility with empty dimension stats"""
        dimension_stats = {}

        result = TeamPersonalityService._calculate_compatibility(dimension_stats)

        assert result == 0.0


class TestCalculateDiversity:
    """Test diversity scoring"""

    def test_high_diversity_score(self):
        """Test diversity score with high std_dev (near 2.0)"""
        dimension_stats = {
            "Openness": {"std_dev": 1.8},
            "Conscientiousness": {"std_dev": 1.9},
            "Extraversion": {"std_dev": 2.0},
            "Agreeableness": {"std_dev": 1.7},
            "Neuroticism": {"std_dev": 1.8},
        }

        result = TeamPersonalityService._calculate_diversity(dimension_stats)

        # Should be near 1.0 (max diversity)
        assert result > 0.85
        assert result <= 1.0

    def test_medium_diversity_score(self):
        """Test diversity score with medium std_dev (around 1.0)"""
        dimension_stats = {
            "Openness": {"std_dev": 1.0},
            "Conscientiousness": {"std_dev": 0.9},
            "Extraversion": {"std_dev": 1.1},
            "Agreeableness": {"std_dev": 1.0},
            "Neuroticism": {"std_dev": 0.9},
        }

        result = TeamPersonalityService._calculate_diversity(dimension_stats)

        # Should be around 0.45-0.55
        assert 0.40 < result < 0.60

    def test_low_diversity_score(self):
        """Test diversity score with low std_dev (near 0)"""
        dimension_stats = {
            "Openness": {"std_dev": 0.2},
            "Conscientiousness": {"std_dev": 0.3},
            "Extraversion": {"std_dev": 0.2},
            "Agreeableness": {"std_dev": 0.3},
            "Neuroticism": {"std_dev": 0.2},
        }

        result = TeamPersonalityService._calculate_diversity(dimension_stats)

        # Should be near 0.0 (low diversity)
        assert result < 0.20

    def test_empty_dimension_stats(self):
        """Test diversity with empty dimension stats"""
        dimension_stats = {}

        result = TeamPersonalityService._calculate_diversity(dimension_stats)

        assert result == 0.0


class TestGetTeamComposition:
    """Test main team composition getter with caching"""

    @pytest.mark.asyncio
    async def test_returns_cached_data_when_fresh(self):
        """Test that fresh cached data is returned without recalculation"""
        db = Mock(spec=AsyncSession)

        # Mock cached data (less than 24 hours old)
        cached_map = Mock(spec=TeamPersonalityMap)
        cached_map.updated_at = datetime.utcnow() - timedelta(hours=12)
        cached_map.team_id = "test-team-id"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = cached_map
        db.execute.return_value = mock_result

        result = await TeamPersonalityService.get_team_composition(
            db=db, team_id="test-team-id", force_refresh=False
        )

        assert result == cached_map
        # Should not call _calculate_team_composition
        # (we can verify this by checking that db.execute was only called once)

    @pytest.mark.asyncio
    async def test_recaches_when_data_is_stale(self):
        """Test that stale cached data triggers recalculation"""
        db = Mock(spec=AsyncSession)

        # Mock stale cached data (more than 24 hours old)
        cached_map = Mock(spec=TeamPersonalityMap)
        cached_map.updated_at = datetime.utcnow() - timedelta(hours=30)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = cached_map
        db.execute.return_value = mock_result

        # Mock _calculate_team_composition to return fresh data
        with patch.object(
            TeamPersonalityService,
            "_calculate_team_composition",
            new_callable=AsyncMock,
        ) as mock_calculate:
            fresh_map = Mock(spec=TeamPersonalityMap)
            mock_calculate.return_value = fresh_map

            result = await TeamPersonalityService.get_team_composition(
                db=db, team_id="test-team-id", force_refresh=False
            )

            assert result == fresh_map
            mock_calculate.assert_called_once()

    @pytest.mark.asyncio
    async def test_force_refresh_ignores_cache(self):
        """Test that force_refresh parameter bypasses cache entirely"""
        db = Mock(spec=AsyncSession)

        # Mock _calculate_team_composition
        with patch.object(
            TeamPersonalityService,
            "_calculate_team_composition",
            new_callable=AsyncMock,
        ) as mock_calculate:
            fresh_map = Mock(spec=TeamPersonalityMap)
            mock_calculate.return_value = fresh_map

            result = await TeamPersonalityService.get_team_composition(
                db=db, team_id="test-team-id", force_refresh=True
            )

            assert result == fresh_map
            mock_calculate.assert_called_once_with(db, "test-team-id")
            # Should not check cache at all when force_refresh=True

    @pytest.mark.asyncio
    async def test_no_cache_calculates_fresh(self):
        """Test that absence of cache triggers calculation"""
        db = Mock(spec=AsyncSession)

        # Mock no cached data
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        # Mock _calculate_team_composition
        with patch.object(
            TeamPersonalityService,
            "_calculate_team_composition",
            new_callable=AsyncMock,
        ) as mock_calculate:
            fresh_map = Mock(spec=TeamPersonalityMap)
            mock_calculate.return_value = fresh_map

            result = await TeamPersonalityService.get_team_composition(
                db=db, team_id="test-team-id", force_refresh=False
            )

            assert result == fresh_map
            mock_calculate.assert_called_once()


class TestCalculateTeamComposition:
    """Test full team composition calculation from database"""

    @pytest.mark.asyncio
    async def test_no_team_returns_none(self):
        """Test that non-existent team returns None"""
        db = Mock(spec=AsyncSession)

        # Mock team query returns None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        result = await TeamPersonalityService._calculate_team_composition(
            db=db, team_id="nonexistent-team-id"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_team_with_no_members_returns_none(self):
        """Test that team with no members returns None"""
        db = Mock(spec=AsyncSession)

        # Mock team with no members
        mock_team = Mock(spec=Team)
        mock_team.members = []

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_team
        db.execute.return_value = mock_result

        result = await TeamPersonalityService._calculate_team_composition(
            db=db, team_id="team-with-no-members"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_team_with_no_assessments_returns_none(self):
        """Test that team with no assessments returns None"""
        db = Mock(spec=AsyncSession)

        # Mock team with members
        mock_team = Mock(spec=Team)
        mock_team.id = "test-team-id"
        mock_team.members = [Mock(), Mock()]  # 2 members

        # First call returns team, second returns empty list (no assessments)
        mock_results = [
            Mock(scalar_one_or_none=Mock(return_value=mock_team)),
            Mock(fetchmany=Mock(return_value=[])),
        ]
        db.execute.side_effect = mock_results

        result = await TeamPersonalityService._calculate_team_composition(
            db=db, team_id="test-team-id"
        )

        assert result is None


class TestCompareTeams:
    """Test multi-team comparison functionality"""

    @pytest.mark.asyncio
    async def test_compare_multiple_teams(self):
        """Test comparison of multiple teams"""
        db = Mock(spec=AsyncSession)

        # Mock get_team_composition to return team data
        with patch.object(
            TeamPersonalityService, "get_team_composition", new_callable=AsyncMock
        ) as mock_get_composition:
            # Create mock team data
            team1 = Mock(spec=TeamPersonalityMap)
            team1.composition_type = "Creative & Social"
            team1.team_size = 10
            team1.diversity_score = 0.65
            team1.internal_compatibility = 0.85
            team1.openness = {"avg": 4.2}
            team1.conscientiousness = {"avg": 3.8}
            team1.extraversion = {"avg": 4.0}
            team1.agreeableness = {"avg": 3.5}
            team1.neuroticism = {"avg": 2.3}

            team2 = Mock(spec=TeamPersonalityMap)
            team2.composition_type = "Strategic Thinkers"
            team2.team_size = 8
            team2.diversity_score = 0.45
            team2.internal_compatibility = 0.75
            team2.openness = {"avg": 3.5}
            team2.conscientiousness = {"avg": 4.2}
            team2.extraversion = {"avg": 3.0}
            team2.agreeableness = {"avg": 3.8}
            team2.neuroticism = {"avg": 2.5}

            mock_get_composition.side_effect = [team1, team2]

            result = await TeamPersonalityService.compare_teams(
                db=db, team_ids=["team1-id", "team2-id"]
            )

            assert len(result) == 2
            assert result[0]["composition_type"] == "Creative & Social"
            assert result[1]["composition_type"] == "Strategic Thinkers"
            assert result[0]["team_size"] == 10
            assert result[1]["team_size"] == 8

    @pytest.mark.asyncio
    async def test_compare_filters_out_teams_with_no_data(self):
        """Test that teams without personality data are filtered out"""
        db = Mock(spec=AsyncSession)

        # Mock get_team_composition to return None for one team
        with patch.object(
            TeamPersonalityService, "get_team_composition", new_callable=AsyncMock
        ) as mock_get_composition:
            team1 = Mock(spec=TeamPersonalityMap)
            team1.composition_type = "Creative & Social"
            team1.team_size = 10
            team1.diversity_score = 0.65
            team1.internal_compatibility = 0.85
            team1.openness = {"avg": 4.2}
            team1.conscientiousness = {"avg": 3.8}
            team1.extraversion = {"avg": 4.0}
            team1.agreeableness = {"avg": 3.5}
            team1.neuroticism = {"avg": 2.3}

            mock_get_composition.side_effect = [team1, None, None]

            result = await TeamPersonalityService.compare_teams(
                db=db, team_ids=["team1-id", "team2-id", "team3-id"]
            )

            # Should only return the first team
            assert len(result) == 1
            assert result[0]["composition_type"] == "Creative & Social"

    @pytest.mark.asyncio
    async def test_compare_empty_team_list(self):
        """Test comparison with empty team list"""
        db = Mock(spec=AsyncSession)

        result = await TeamPersonalityService.compare_teams(db=db, team_ids=[])

        assert result == []


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_dimension_stats_with_single_score(self):
        """Test dimension stats with only one score"""
        scores = [3.5]

        result = TeamPersonalityService._calculate_dimension_stats(scores)

        assert result["avg"] == 3.5
        assert result["min"] == 3.5
        assert result["max"] == 3.5
        assert result["std_dev"] == 0.0

    def test_dimension_stats_with_large_dataset(self):
        """Test dimension stats with 1000 scores"""
        # Generate 1000 random scores between 1 and 5
        scores = [1.0 + (i % 40) / 10.0 for i in range(1000)]

        result = TeamPersonalityService._calculate_dimension_stats(scores)

        # Verify basic properties
        assert 1.0 <= result["avg"] <= 5.0
        assert result["min"] == 1.0
        assert result["max"] == 5.0
        assert result["std_dev"] > 0
        assert sum(result["distribution"]) == 100.0

    def test_composition_type_with_missing_dimensions(self):
        """Test composition type when not all dimensions have data"""
        dimension_stats = {
            "Openness": {"avg": 4.0},
            "Extraversion": {"avg": 3.5},
            # Missing other dimensions
        }

        result = TeamPersonalityService._determine_composition_type(dimension_stats)

        # Should still return a type based on available data
        assert result in ["Creative & Social", "Balanced Team", "Unknown"]

    def test_strengths_gaps_boundary_conditions(self):
        """Test strengths and gaps at exact threshold values"""
        # Test at exact threshold (3.5 for strengths, 2.5 for gaps)
        dimension_stats = {
            "Openness": {"avg": 3.5, "std_dev": 0.8},  # Exactly at strength threshold
            "Conscientiousness": {
                "avg": 2.5,
                "std_dev": 0.8,
            },  # Exactly at gap threshold
            "Extraversion": {"avg": 3.0, "std_dev": 0.8},
            "Agreeableness": {"avg": 3.0, "std_dev": 0.8},
            "Neuroticism": {"avg": 3.0, "std_dev": 0.8},
        }

        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(
            dimension_stats
        )

        # 3.5 should trigger strength
        assert "Creative problem-solving and innovation" in strengths
        # 2.5 should trigger gap
        assert "May struggle with organization and follow-through" in gaps


# Test coverage markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.services,
]
