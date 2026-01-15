# app/services/team_personality_service.py
"""
Team Personality Service
Aggregates individual personality assessments into team-level insights.
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.assessment import Assessment, AssessmentResponse
from app.db.models.score import Score
from app.db.models.team import Team, TeamMember
from app.db.models.team_personality_map import TeamPersonalityMap


class TeamPersonalityService:
    """
    Service for aggregating and analyzing team personality data.
    """

    # Big Five personality dimensions (OCEAN)
    BIG_FIVE_DIMENSIONS = [
        "Openness",
        "Conscientiousness",
        "Extraversion",
        "Agreeableness",
        "Neuroticism"
    ]

    # Dimension to JSONB field mapping
    DIMENSION_FIELD_MAP = {
        "Openness": "openness",
        "Conscientiousness": "conscientiousness",
        "Extraversion": "extraversion",
        "Agreeableness": "agreeableness",
        "Neuroticism": "neuroticism"
    }

    @staticmethod
    async def get_team_composition(
        db: AsyncSession,
        team_id: str,
        force_refresh: bool = False
    ) -> Optional[TeamPersonalityMap]:
        """
        Get team personality composition.
        Returns cached data if available, otherwise calculates fresh.

        Args:
            db: Database session
            team_id: Team UUID
            force_refresh: If True, recalculate even if cached data exists

        Returns:
            TeamPersonalityMap object or None if no assessments found
        """
        # Check if we have cached data
        if not force_refresh:
            cached = await db.execute(
                select(TeamPersonalityMap)
                .filter(TeamPersonalityMap.team_id == team_id)
                .order_by(TeamPersonalityMap.updated_at.desc())
                .limit(1)
            )
            cached_map = cached.scalar_one_or_none()

            if cached_map:
                # Check if cache is fresh (less than 24 hours old)
                age = (datetime.utcnow() - cached_map.updated_at).total_seconds()
                if age < 86400:  # 24 hours
                    return cached_map

        # No cached data or force_refresh - calculate fresh
        return await TeamPersonalityService._calculate_team_composition(db, team_id)

    @staticmethod
    async def _calculate_team_composition(
        db: AsyncSession,
        team_id: str
    ) -> Optional[TeamPersonalityMap]:
        """
        Calculate team personality composition from raw assessment data.

        Args:
            db: Database session
            team_id: Team UUID

        Returns:
            TeamPersonalityMap object or None if no assessments found
        """
        # Get team with members
        team_result = await db.execute(
            select(Team)
            .options(selectinload(Team.members))
            .filter(Team.id == team_id)
        )
        team = team_result.scalar_one_or_none()

        if not team or not team.members:
            return None

        # Get all assessment IDs for this team
        assessment_result = await db.execute(
            select(Assessment.id)
            .filter(
                Assessment.team_id == team_id,
                Assessment.framework_code == "BIG_FIVE"  # Only Big Five assessments
            )
        )
        assessment_ids = [row[0] for row in assessment_result.fetchall()]

        if not assessment_ids:
            return None

        # Get all scores for these assessments, grouped by dimension
        scores_by_dimension = {dim: [] for dim in TeamPersonalityService.BIG_FIVE_DIMENSIONS}

        scores_result = await db.execute(
            select(Score.dimension, Score.value)
            .filter(Score.assessment_id.in_(assessment_ids))
        )

        for dimension, value in scores_result.fetchall():
            if dimension in scores_by_dimension:
                scores_by_dimension[dimension].append(float(value))

        # Check if we have any scores
        if not any(scores_by_dimension.values()):
            return None

        # Calculate statistics for each dimension
        dimension_stats = {}
        for dimension, scores in scores_by_dimension.items():
            if scores:  # Only calculate if we have data
                dimension_stats[dimension] = TeamPersonalityService._calculate_dimension_stats(scores)

        # Determine team composition type
        composition_type = TeamPersonalityService._determine_composition_type(dimension_stats)

        # Generate strengths and gaps
        strengths, gaps = TeamPersonalityService._generate_strengths_and_gaps(dimension_stats)

        # Calculate compatibility and diversity scores
        internal_compatibility = TeamPersonalityService._calculate_compatibility(dimension_stats)
        diversity_score = TeamPersonalityService._calculate_diversity(dimension_stats)

        # Create or update TeamPersonalityMap
        existing_map = await db.execute(
            select(TeamPersonalityMap).filter(TeamPersonalityMap.team_id == team_id)
        )
        existing = existing_map.scalar_one_or_none()

        if existing:
            # Update existing
            personality_map = existing
            personality_map.updated_at = datetime.utcnow()
        else:
            # Create new
            personality_map = TeamPersonalityMap(
                team_id=team_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(personality_map)

        # Update fields
        personality_map.assessment_ids = [str(aid) for aid in assessment_ids]
        personality_map.team_size = len(team.members)

        # Set dimension statistics
        for dimension, stats in dimension_stats.items():
            field_name = TeamPersonalityService.DIMENSION_FIELD_MAP[dimension]
            setattr(personality_map, field_name, stats)

        personality_map.composition_type = composition_type
        personality_map.strengths = strengths
        personality_map.gaps = gaps
        personality_map.internal_compatibility = internal_compatibility
        personality_map.diversity_score = diversity_score
        personality_map.calculation_version = "1.0"

        # Commit to database
        await db.commit()
        await db.refresh(personality_map)

        return personality_map

    @staticmethod
    def _calculate_dimension_stats(scores: List[float]) -> Dict[str, Any]:
        """
        Calculate statistics for a personality dimension.

        Args:
            scores: List of scores for this dimension

        Returns:
            Dictionary with avg, min, max, std_dev, distribution
        """
        if not scores:
            return {
                "avg": 0.0,
                "min": 0.0,
                "max": 0.0,
                "std_dev": 0.0,
                "distribution": [0, 0, 0, 0, 0]
            }

        scores_array = np.array(scores)

        # Calculate basic statistics
        avg = float(np.mean(scores_array))
        min_val = float(np.min(scores_array))
        max_val = float(np.max(scores_array))
        std_dev = float(np.std(scores_array))

        # Calculate distribution (quintiles: very low, low, medium, high, very high)
        # Assuming 1-5 scale
        distribution = [0, 0, 0, 0, 0]  # [very low, low, medium, high, very high]
        for score in scores:
            if score <= 1.0:
                distribution[0] += 1
            elif score <= 2.0:
                distribution[1] += 1
            elif score <= 3.0:
                distribution[2] += 1
            elif score <= 4.0:
                distribution[3] += 1
            else:
                distribution[4] += 1

        # Convert to percentages
        total = len(scores)
        distribution_pct = [round((count / total) * 100, 2) for count in distribution]

        return {
            "avg": round(avg, 2),
            "min": round(min_val, 2),
            "max": round(max_val, 2),
            "std_dev": round(std_dev, 2),
            "distribution": distribution_pct
        }

    @staticmethod
    def _determine_composition_type(dimension_stats: Dict[str, Dict[str, Any]]) -> str:
        """
        Determine overall team personality type based on dimension averages.

        Args:
            dimension_stats: Statistics for each dimension

        Returns:
            Composition type string
        """
        if not dimension_stats:
            return "Unknown"

        # Get average scores for each dimension
        averages = {
            dim: stats.get("avg", 0)
            for dim, stats in dimension_stats.items()
        }

        # Determine type based on highest dimensions
        sorted_dims = sorted(averages.items(), key=lambda x: x[1], reverse=True)
        top_dims = [dim for dim, avg in sorted_dims[:2]]

        # Map dimension combinations to composition types
        type_map = {
            ("Openness", "Extraversion"): "Creative & Social",
            ("Openness", "Agreeableness"): "Collaborative Innovators",
            ("Conscientiousness", "Agreeableness"): "Reliable Team Players",
            ("Conscientiousness", "Extraversion"): "Driven & Organized",
            ("Extraversion", "Agreeableness"): "People-Oriented",
            ("Openness", "Conscientiousness"): "Strategic Thinkers",
            ("Neuroticism", "Agreeableness"): "Sensitive Collaborators",
            ("Neuroticism", "Conscientiousness"): "Detail-Oriented Perfectionists",
        }

        key = tuple(sorted(top_dims))
        return type_map.get(key, "Balanced Team")

    @staticmethod
    def _generate_strengths_and_gaps(
        dimension_stats: Dict[str, Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """
        Generate team strengths and gaps based on personality composition.

        Args:
            dimension_stats: Statistics for each dimension

        Returns:
            Tuple of (strengths list, gaps list)
        """
        strengths = []
        gaps = []

        if not dimension_stats:
            return strengths, gaps

        # Get average scores
        averages = {
            dim: stats.get("avg", 0)
            for dim, stats in dimension_stats.items()
        }

        # High scores = strengths
        if averages.get("Openness", 0) >= 3.5:
            strengths.append("Creative problem-solving and innovation")
        if averages.get("Conscientiousness", 0) >= 3.5:
            strengths.append("Strong organization and attention to detail")
        if averages.get("Extraversion", 0) >= 3.5:
            strengths.append("Excellent communication and social engagement")
        if averages.get("Agreeableness", 0) >= 3.5:
            strengths.append("Collaborative and supportive team culture")
        if averages.get("Neuroticism", 0) <= 2.0:  # Low neuroticism = high stability
            strengths.append("Emotional stability and stress resilience")

        # Low scores = potential gaps
        if averages.get("Openness", 0) <= 2.5:
            gaps.append("May resist change or new ideas")
        if averages.get("Conscientiousness", 0) <= 2.5:
            gaps.append("May struggle with organization and follow-through")
        if averages.get("Extraversion", 0) <= 2.5:
            gaps.append("May have limited external networking and communication")
        if averages.get("Agreeableness", 0) <= 2.5:
            gaps.append("May experience interpersonal conflicts")
        if averages.get("Neuroticism", 0) >= 3.5:  # High neuroticism
            gaps.append("May be susceptible to stress and burnout")

        # Check for diversity (all scores clustered = low diversity)
        std_devs = [stats.get("std_dev", 0) for stats in dimension_stats.values()]
        avg_std_dev = np.mean(std_devs) if std_devs else 0

        if avg_std_dev < 0.5:
            gaps.append("Low personality diversity may limit perspective variety")

        return strengths, gaps

    @staticmethod
    def _calculate_compatibility(dimension_stats: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate internal compatibility score (how well personalities complement).

        Args:
            dimension_stats: Statistics for each dimension

        Returns:
            Compatibility score (0-1)
        """
        if not dimension_stats:
            return 0.0

        # Simple heuristic: moderate diversity = good compatibility
        # Too similar = lack diverse perspectives
        # Too different = potential conflicts

        std_devs = [stats.get("std_dev", 0) for stats in dimension_stats.values()]
        avg_std_dev = np.mean(std_devs) if std_devs else 0

        # Optimal std_dev is around 0.7-1.0 on a 1-5 scale
        if avg_std_dev < 0.5:
            # Too similar
            return 0.5 + (avg_std_dev / 1.0)
        elif avg_std_dev > 1.5:
            # Too different
            return max(0.5, 1.0 - ((avg_std_dev - 1.5) / 2.0))
        else:
            # Sweet spot
            return 0.9

    @staticmethod
    def _calculate_diversity(dimension_stats: Dict[str, Dict[str, Any]]) -> float:
        """
        Calculate personality diversity score.

        Args:
            dimension_stats: Statistics for each dimension

        Returns:
            Diversity score (0-1, higher = more diverse)
        """
        if not dimension_stats:
            return 0.0

        # Use average standard deviation as diversity indicator
        std_devs = [stats.get("std_dev", 0) for stats in dimension_stats.values()]
        avg_std_dev = np.mean(std_devs) if std_devs else 0

        # On a 1-5 scale, max std_dev is ~2.0
        # Normalize to 0-1
        return min(1.0, avg_std_dev / 2.0)

    @staticmethod
    async def compare_teams(
        db: AsyncSession,
        team_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Compare personality composition across multiple teams.

        Args:
            db: Database session
            team_ids: List of team UUIDs to compare

        Returns:
            List of team composition data for comparison
        """
        results = []

        for team_id in team_ids:
            composition = await TeamPersonalityService.get_team_composition(db, team_id)
            if composition:
                results.append({
                    "team_id": str(team_id),
                    "composition_type": composition.composition_type,
                    "team_size": composition.team_size,
                    "diversity_score": composition.diversity_score,
                    "internal_compatibility": composition.internal_compatibility,
                    "openness": composition.openness,
                    "conscientiousness": composition.conscientiousness,
                    "extraversion": composition.extraversion,
                    "agreeableness": composition.agreeableness,
                    "neuroticism": composition.neuroticism,
                })

        return results


# Singleton instance
team_personality_service = TeamPersonalityService()
