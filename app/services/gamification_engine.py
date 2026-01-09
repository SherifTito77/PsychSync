"""
Enhanced Gamification Engine

Advanced achievement system with point tracking, leaderboards, and engagement mechanics.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AchievementCategory(Enum):
    MILESTONE = "milestone"
    ENGAGEMENT = "engagement"
    LEADERSHIP = "leadership"
    SKILL_MASTER = "skill_master"
    EXPERIMENTAL = "experimental"
    SOCIAL = "social"
    LEARNING = "learning"
    CHALLENGE = "challenge"


class BadgeTier(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


class LeaderboardType(Enum):
    POINTS = "points"
    LEVEL = "level"
    ACHIEVEMENTS = "achievements"
    STREAK = "streak"
    WEEKLY_SCORE = "weekly_score"
    EXPERIMENTAL_PARTICIPATION = "experimental_participation"


@dataclass
class AchievementDefinition:
    """Definition for a specific achievement"""

    id: str
    name: str
    description: str
    category: AchievementCategory
    badge_tier: BadgeTier
    badge_emoji: str
    points: int
    prerequisites: list[str]  # Required achievements before unlocking
    conditions: dict[str, Any]  # Conditions to earn achievement
    rewards: dict[str, Any]  # Additional rewards beyond points
    hidden: bool  # Whether achievement is hidden until unlocked
    limited_time: datetime | None  # If achievement has time limit
    repeatable: bool  # Whether achievement can be earned multiple times


@dataclass
class UserAchievement:
    """User's earned achievement instance"""

    user_id: str
    achievement_id: str
    earned_date: datetime
    progress: float  # 0-1 for partial progress
    milestone_data: dict[str, Any]  # Data about how achievement was earned
    repeat_count: int  # For repeatable achievements
    shared: bool  # Whether user has shared this achievement


@dataclass
class LeaderboardEntry:
    """Entry in a leaderboard"""

    rank: int
    user_id: str
    display_name: str
    score: float
    level: int
    badge_tier: BadgeTier
    avatar: str
    change_from_previous: int  # Rank change from previous period
    last_updated: datetime


@dataclass
class GamificationEvent:
    """Event that can trigger achievement progress"""

    event_type: str
    user_id: str
    timestamp: datetime
    event_data: dict[str, Any]
    session_id: str | None = None


class EnhancedGamificationEngine:
    """Advanced gamification engine with comprehensive achievement tracking"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.achievement_definitions = self._load_achievement_definitions()
        self.badge_system = self._initialize_badge_system()
        self.leaderboards = self._initialize_leaderboards()
        self.event_handlers = self._initialize_event_handlers()

    def _load_achievement_definitions(self) -> dict[str, AchievementDefinition]:
        """Load comprehensive achievement definitions"""
        return {
            # Milestone Achievements
            "first_assessment": AchievementDefinition(
                id="first_assessment",
                name="Assessment Pioneer",
                description="Complete your first psychological assessment",
                category=AchievementCategory.MILESTONE,
                badge_tier=BadgeTier.BRONZE,
                badge_emoji="🎯",
                points=100,
                prerequisites=[],
                conditions={"assessment_count": 1},
                rewards={"unlock_feature": "basic_analytics"},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            "power_user": AchievementDefinition(
                id="power_user",
                name="Power User",
                description="Complete 50 psychological assessments",
                category=AchievementCategory.MILESTONE,
                badge_tier=BadgeTier.PLATINUM,
                badge_emoji="⚡",
                points=2000,
                prerequisites=["first_assessment"],
                conditions={"assessment_count": 50},
                rewards={"unlock_feature": "advanced_analytics"},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            # Engagement Achievements
            "daily_streak_7": AchievementDefinition(
                id="daily_streak_7",
                name="Week Warrior",
                description="Maintain a 7-day activity streak",
                category=AchievementCategory.ENGAGEMENT,
                badge_tier=BadgeTier.SILVER,
                badge_emoji="🔥",
                points=500,
                prerequisites=[],
                conditions={"current_streak": 7},
                rewards={"streak_bonus": 50},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            "daily_streak_30": AchievementDefinition(
                id="daily_streak_30",
                name="Month Master",
                description="Maintain a 30-day activity streak",
                category=AchievementCategory.ENGAGEMENT,
                badge_tier=BadgeTier.GOLD,
                badge_emoji="🏆",
                points=3000,
                prerequisites=["daily_streak_7"],
                conditions={"current_streak": 30},
                rewards={"streak_bonus": 200, "badge": "loyal_user"},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            # Leadership Achievements
            "team_leader": AchievementDefinition(
                id="team_leader",
                name="Team Leader",
                description="Lead a team to top performance ranking",
                category=AchievementCategory.LEADERSHIP,
                badge_tier=BadgeTier.GOLD,
                badge_emoji="👑",
                points=750,
                prerequisites=[],
                conditions={"team_ranking": 1, "min_team_size": 5},
                rewards={"leadership_points": 100, "unlock_feature": "team_insights"},
                hidden=False,
                limited_time=None,
                repeatable=True,
            ),
            "mentor_excellence": AchievementDefinition(
                id="mentor_excellence",
                name="Mentor Excellence",
                description="Help 10 team members achieve significant improvements",
                category=AchievementCategory.LEADERSHIP,
                badge_tier=BadgeTier.PLATINUM,
                badge_emoji="🌟",
                points=1500,
                prerequisites=["team_leader"],
                conditions={"mentees_helped": 10, "average_improvement": 0.25},
                rewards={"mentor_badge": True, "unlock_feature": "mentoring_tools"},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            # Skill Master Achievements
            "skill_master_5": AchievementDefinition(
                id="skill_master_5",
                name="Skill Master",
                description="Achieve mastery in 5 different skills",
                category=AchievementCategory.SKILL_MASTER,
                badge_tier=BadgeTier.GOLD,
                badge_emoji="🏅",
                points=1000,
                prerequisites=[],
                conditions={"mastered_skills": 5, "min_mastery_level": 0.9},
                rewards={"skill_points": 200, "unlock_feature": "skill_comparison"},
                hidden=False,
                limited_time=None,
                repeatable=True,
            ),
            "polymath": AchievementDefinition(
                id="polymath",
                name="Polymath",
                description="Achieve mastery in 10 different categories",
                category=AchievementCategory.SKILL_MASTER,
                badge_tier=BadgeTier.DIAMOND,
                badge_emoji="🧠",
                points=5000,
                prerequisites=["skill_master_5"],
                conditions={"mastered_categories": 10, "min_mastery_level": 0.85},
                rewards={"polymath_badge": True, "unlock_feature": "advanced_insights"},
                hidden=True,
                limited_time=None,
                repeatable=False,
            ),
            # Experimental Achievements
            "experimental_explorer": AchievementDefinition(
                id="experimental_explorer",
                name="Innovation Explorer",
                description="Try experimental features and provide feedback",
                category=AchievementCategory.EXPERIMENTAL,
                badge_tier=BadgeTier.SILVER,
                badge_emoji="🚀",
                points=300,
                prerequisites=[],
                conditions={"experimental_features_tried": 3, "feedback_provided": True},
                rewards={"experimental_access": True, "points_bonus": 100},
                hidden=False,
                limited_time=datetime(2024, 12, 31),
                repeatable=False,
            ),
            "early_adopter": AchievementDefinition(
                id="early_adopter",
                name="Early Adopter",
                description="Be among the first 100 users to try new features",
                category=AchievementCategory.EXPERIMENTAL,
                badge_tier=BadgeTier.GOLD,
                badge_emoji="🌟",
                points=500,
                prerequisites=[],
                conditions={"early_user": True, "feature_adoption_time": 7},
                rewards={"early_adopter_badge": True, "priority_access": True},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            # Learning Achievements
            "quick_learner": AchievementDefinition(
                id="quick_learner",
                name="Quick Learner",
                description="Complete a learning path in record time",
                category=AchievementCategory.LEARNING,
                badge_tier=BadgeTier.SILVER,
                badge_emoji="⚡",
                points=400,
                prerequisites=[],
                conditions={"learning_path_completion": True, "completion_time_ratio": 0.5},
                rewards={"learning_points": 150, "path_bonus": True},
                hidden=False,
                limited_time=None,
                repeatable=True,
            ),
            "knowledge_seeker": AchievementDefinition(
                id="knowledge_seeker",
                name="Knowledge Seeker",
                description="Complete 20 different learning modules",
                category=AchievementCategory.LEARNING,
                badge_tier=BadgeTier.GOLD,
                badge_emoji="📚",
                points=800,
                prerequisites=["quick_learner"],
                conditions={"completed_modules": 20, "diversity_score": 0.7},
                rewards={"knowledge_points": 300, "unlock_feature": "advanced_learning"},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            # Challenge Achievements
            "weekly_champion": AchievementDefinition(
                id="weekly_champion",
                name="Weekly Champion",
                description="Top the weekly leaderboard",
                category=AchievementCategory.CHALLENGE,
                badge_tier=BadgeTier.GOLD,
                badge_emoji="🏆",
                points=1000,
                prerequisites=[],
                conditions={"weekly_rank": 1, "min_score": 1000},
                rewards={"champion_badge": True, "weekly_bonus": 200},
                hidden=False,
                limited_time=None,
                repeatable=True,
            ),
            "perfectionist": AchievementDefinition(
                id="perfectionist",
                name="Perfectionist",
                description="Complete 100 assessments with 95%+ accuracy",
                category=AchievementCategory.CHALLENGE,
                badge_tier=BadgeTier.DIAMOND,
                badge_emoji="💎",
                points=3000,
                prerequisites=["power_user"],
                conditions={"perfect_assessments": 100, "min_accuracy": 0.95},
                rewards={"perfectionist_badge": True, "accuracy_bonus": True},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            # Social Achievements
            "collaborator": AchievementDefinition(
                id="collaborator",
                name="Collaborator",
                description="Participate in 10 team activities",
                category=AchievementCategory.SOCIAL,
                badge_tier=BadgeTier.SILVER,
                badge_emoji="🤝",
                points=350,
                prerequisites=[],
                conditions={"team_activities": 10, "collaboration_score": 0.8},
                rewards={"collaboration_points": 100, "social_unlock": True},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
            "community_builder": AchievementDefinition(
                id="community_builder",
                name="Community Builder",
                description="Help 20 new users get started",
                category=AchievementCategory.SOCIAL,
                badge_tier=BadgeTier.GOLD,
                badge_emoji="🏘️",
                points=1200,
                prerequisites=["collaborator"],
                conditions={"new_users_helped": 20, "helpfulness_score": 0.9},
                rewards={"community_points": 500, "mentor_status": True},
                hidden=False,
                limited_time=None,
                repeatable=False,
            ),
        }

    def _initialize_badge_system(self) -> dict[str, Any]:
        """Initialize badge system with tiers and rewards"""
        return {
            "tiers": {
                BadgeTier.BRONZE: {
                    "min_points": 0,
                    "color": "#CD7F32",
                    "benefits": ["basic_analytics", "profile_customization"],
                },
                BadgeTier.SILVER: {
                    "min_points": 1000,
                    "color": "#C0C0C0",
                    "benefits": ["advanced_analytics", "priority_support", "custom_themes"],
                },
                BadgeTier.GOLD: {
                    "min_points": 5000,
                    "color": "#FFD700",
                    "benefits": ["premium_analytics", "beta_access", "exclusive_content"],
                },
                BadgeTier.PLATINUM: {
                    "min_points": 15000,
                    "color": "#E5E4E2",
                    "benefits": [
                        "enterprise_analytics",
                        "personal_consultation",
                        "early_feature_access",
                    ],
                },
                BadgeTier.DIAMOND: {
                    "min_points": 50000,
                    "color": "#B9F2FF",
                    "benefits": ["vip_support", "custom_solutions", "strategic_partnership"],
                },
            },
            "special_badges": {
                "founder": {"emoji": "👑", "description": "Founding member of the platform"},
                "innovation_leader": {
                    "emoji": "💡",
                    "description": "Led experimental feature adoption",
                },
                "mentor_excellence": {
                    "emoji": "🌟",
                    "description": "Outstanding mentorship contributions",
                },
                "community_champion": {
                    "emoji": "🏆",
                    "description": "Exceptional community building",
                },
            },
        }

    def _initialize_leaderboards(self) -> dict[str, Any]:
        """Initialize leaderboard configurations"""
        return {
            LeaderboardType.POINTS: {
                "name": "Points Leaderboard",
                "description": "Users ranked by total points earned",
                "update_frequency": "hourly",
                "decay_factor": 0.98,  # Weekly decay for engagement
                "entry_limit": 1000,
            },
            LeaderboardType.WEEKLY_SCORE: {
                "name": "Weekly Champions",
                "description": "Top performers this week",
                "update_frequency": "daily",
                "reset_frequency": "weekly",
                "entry_limit": 100,
            },
            LeaderboardType.STREAK: {
                "name": "Streak Masters",
                "description": "Users with longest activity streaks",
                "update_frequency": "daily",
                "entry_limit": 500,
            },
            LeaderboardType.LEVEL: {
                "name": "Level Leaders",
                "description": "Users by experience level",
                "update_frequency": "daily",
                "entry_limit": 1000,
            },
            LeaderboardType.ACHIEVEMENTS: {
                "name": "Achievement Hunters",
                "description": "Users by total achievements earned",
                "update_frequency": "daily",
                "entry_limit": 500,
            },
            LeaderboardType.EXPERIMENTAL_PARTICIPATION: {
                "name": "Innovation Leaders",
                "description": "Most active in experimental features",
                "update_frequency": "daily",
                "entry_limit": 200,
            },
        }

    def _initialize_event_handlers(self) -> dict[str, Any]:
        """Initialize event handlers for achievement tracking"""
        return {
            "assessment_completed": self._handle_assessment_completed,
            "login": self._handle_login_event,
            "team_activity": self._handle_team_activity,
            "learning_progress": self._handle_learning_progress,
            "experimental_feature_used": self._handle_experimental_feature,
            "social_interaction": self._handle_social_interaction,
            "challenge_completed": self._handle_challenge_completed,
            "milestone_reached": self._handle_milestone_reached,
        }

    async def process_gamification_event(self, event: GamificationEvent) -> list[UserAchievement]:
        """Process a gamification event and award achievements"""
        try:
            # Get user's current achievement progress
            user_progress = await self._get_user_achievement_progress(event.user_id)
            newly_earned = []

            # Check all achievements that could be triggered by this event
            potential_achievements = await self._get_relevant_achievements(event.event_type)

            for achievement_def in potential_achievements:
                if not await self._can_earn_achievement(
                    event.user_id, achievement_def, user_progress
                ):
                    continue

                # Check if event contributes to achievement progress
                progress_update = await self._calculate_progress_update(event, achievement_def)

                if progress_update > 0:
                    updated_progress = await self._update_achievement_progress(
                        event.user_id, achievement_def.id, progress_update
                    )

                    # Check if achievement is now complete
                    if updated_progress >= 1.0:
                        user_achievement = await self._award_achievement(
                            event.user_id, achievement_def, event.event_data
                        )
                        newly_earned.append(user_achievement)

            # Update user stats and leaderboards
            await self._update_user_stats(event.user_id)
            await self._update_leaderboards(event.user_id)

            return newly_earned

        except Exception as e:
            logger.error(f"Error processing gamification event for user {event.user_id}: {e}")
            return []

    async def get_user_achievements(
        self, user_id: str, include_hidden: bool = False
    ) -> list[dict[str, Any]]:
        """Get all achievements earned by a user"""
        try:
            user_achievements = await self._get_user_achievement_progress(user_id)
            result = []

            for achievement_id, progress_data in user_achievements.items():
                achievement_def = self.achievement_definitions.get(achievement_id)
                if not achievement_def:
                    continue

                # Skip hidden achievements unless completed or explicitly requested
                if (
                    achievement_def.hidden
                    and not include_hidden
                    and progress_data.get("progress", 0) < 1.0
                ):
                    continue

                result.append(
                    {
                        "id": achievement_id,
                        "name": achievement_def.name,
                        "description": achievement_def.description,
                        "category": achievement_def.category.value,
                        "badge_tier": achievement_def.badge_tier.value,
                        "badge_emoji": achievement_def.badge_emoji,
                        "points": achievement_def.points,
                        "progress": progress_data.get("progress", 0),
                        "earned": progress_data.get("progress", 0) >= 1.0,
                        "earned_date": progress_data.get("earned_date"),
                        "repeat_count": progress_data.get("repeat_count", 0),
                        "hidden": achievement_def.hidden,
                        "prerequisites": achievement_def.prerequisites,
                    }
                )

            # Sort by points and earned status
            result.sort(key=lambda x: (not x["earned"], -x["points"]))

            return result

        except Exception as e:
            logger.error(f"Error getting achievements for user {user_id}: {e}")
            return []

    async def get_leaderboard(
        self, leaderboard_type: LeaderboardType, limit: int = 50, time_period: str = "all_time"
    ) -> list[LeaderboardEntry]:
        """Get leaderboard entries"""
        try:
            config = self.leaderboards.get(leaderboard_type)
            if not config:
                raise ValueError(f"Unknown leaderboard type: {leaderboard_type}")

            # In production, this would query the database
            # For now, return mock data
            mock_entries = [
                LeaderboardEntry(
                    rank=1,
                    user_id="user_001",
                    display_name="Alex Chen",
                    score=15420.0,
                    level=25,
                    badge_tier=BadgeTier.PLATINUM,
                    avatar="👤",
                    change_from_previous=-1,
                    last_updated=datetime.utcnow(),
                ),
                LeaderboardEntry(
                    rank=2,
                    user_id="user_002",
                    display_name="Sarah Johnson",
                    score=14200.0,
                    level=23,
                    badge_tier=BadgeTier.GOLD,
                    avatar="👤",
                    change_from_previous=1,
                    last_updated=datetime.utcnow(),
                ),
                LeaderboardEntry(
                    rank=3,
                    user_id="user_003",
                    display_name="Mike Davis",
                    score=13800.0,
                    level=22,
                    badge_tier=BadgeTier.GOLD,
                    avatar="👤",
                    change_from_previous=0,
                    last_updated=datetime.utcnow(),
                ),
            ]

            return mock_entries[:limit]

        except Exception as e:
            logger.error(f"Error getting {leaderboard_type.value} leaderboard: {e}")
            return []

    async def calculate_user_level(self, total_points: int) -> dict[str, Any]:
        """Calculate user level and progression"""
        try:
            # Exponential level progression
            base_points = 500
            level_multiplier = 1.5

            level = 1
            points_for_current_level = 0
            points_for_next_level = base_points

            while total_points >= points_for_next_level:
                level += 1
                points_for_current_level = points_for_next_level
                points_for_next_level = int(points_for_next_level * level_multiplier)

            progress_in_level = total_points - points_for_current_level
            level_size = points_for_next_level - points_for_current_level
            progress_percentage = progress_in_level / level_size if level_size > 0 else 0

            # Calculate badge tier
            badge_tier = BadgeTier.BRONZE
            for tier, config in self.badge_system["tiers"].items():
                if total_points >= config["min_points"]:
                    badge_tier = tier

            return {
                "level": level,
                "points_for_current_level": points_for_current_level,
                "points_for_next_level": points_for_next_level,
                "progress_percentage": progress_percentage,
                "badge_tier": badge_tier.value,
                "unlocked_features": self.badge_system["tiers"][badge_tier]["benefits"],
            }

        except Exception as e:
            logger.error(f"Error calculating user level for {total_points} points: {e}")
            return {
                "level": 1,
                "points_for_current_level": 0,
                "points_for_next_level": 500,
                "progress_percentage": 0,
                "badge_tier": BadgeTier.BRONZE.value,
                "unlocked_features": [],
            }

    async def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            user_achievements = await self.get_user_achievements(user_id)
            total_points = sum(
                a["points"] * (1 if a["earned"] else a["progress"]) for a in user_achievements
            )

            level_info = await self.calculate_user_level(total_points)

            # Calculate engagement metrics
            earned_achievements = [a for a in user_achievements if a["earned"]]
            category_breakdown = {}
            for achievement in earned_achievements:
                category = achievement["category"]
                category_breakdown[category] = category_breakdown.get(category, 0) + 1

            return {
                "total_points": total_points,
                "level_info": level_info,
                "total_achievements": len(earned_achievements),
                "category_breakdown": category_breakdown,
                "current_streak": await self._get_current_streak(user_id),
                "longest_streak": await self._get_longest_streak(user_id),
                "achievement_completion_rate": len(earned_achievements) / len(user_achievements)
                if user_achievements
                else 0,
                "leaderboard_rank": await self._get_user_leaderboard_rank(user_id),
                "unlocked_features": level_info["unlocked_features"],
                "special_badges": await self._get_user_special_badges(user_id),
            }

        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {}

    # Event Handler Methods
    async def _handle_assessment_completed(self, event: GamificationEvent) -> None:
        """Handle assessment completion events"""
        # Progress for assessment-related achievements

    async def _handle_login_event(self, event: GamificationEvent) -> None:
        """Handle user login events"""
        # Update streak, check daily login achievements

    async def _handle_team_activity(self, event: GamificationEvent) -> None:
        """Handle team activity events"""
        # Progress for collaboration and leadership achievements

    async def _handle_learning_progress(self, event: GamificationEvent) -> None:
        """Handle learning progress events"""
        # Progress for learning achievements

    async def _handle_experimental_feature(self, event: GamificationEvent) -> None:
        """Handle experimental feature usage events"""
        # Progress for experimental achievements

    async def _handle_social_interaction(self, event: GamificationEvent) -> None:
        """Handle social interaction events"""
        # Progress for social achievements

    async def _handle_challenge_completed(self, event: GamificationEvent) -> None:
        """Handle challenge completion events"""
        # Progress for challenge achievements

    async def _handle_milestone_reached(self, event: GamificationEvent) -> None:
        """Handle milestone events"""
        # Progress for milestone achievements

    # Helper Methods
    async def _get_user_achievement_progress(self, user_id: str) -> dict[str, dict]:
        """Get user's progress on all achievements"""
        # In production, query database for user's achievement progress
        # For now, return mock data
        return {
            "first_assessment": {"progress": 1.0, "earned_date": datetime.utcnow()},
            "daily_streak_7": {"progress": 0.7},
            "power_user": {"progress": 0.15},
            "team_leader": {"progress": 0.8},
        }

    async def _get_relevant_achievements(self, event_type: str) -> list[AchievementDefinition]:
        """Get achievements that could be triggered by this event type"""
        relevant_achievements = []

        for achievement_def in self.achievement_definitions.values():
            # Check if event type matches achievement conditions
            if self._event_matches_achievement(event_type, achievement_def):
                relevant_achievements.append(achievement_def)

        return relevant_achievements

    def _event_matches_achievement(
        self, event_type: str, achievement_def: AchievementDefinition
    ) -> bool:
        """Check if event type is relevant to achievement"""
        # Simplified logic - in production, this would be more sophisticated
        event_achievement_mapping = {
            "assessment_completed": ["first_assessment", "power_user", "perfectionist"],
            "login": ["daily_streak_7", "daily_streak_30"],
            "team_activity": ["team_leader", "mentor_excellence", "collaborator"],
            "learning_progress": ["quick_learner", "knowledge_seeker"],
            "experimental_feature_used": ["experimental_explorer", "early_adopter"],
            "social_interaction": ["collaborator", "community_builder"],
            "challenge_completed": ["weekly_champion"],
        }

        return achievement_def.id in event_achievement_mapping.get(event_type, [])

    async def _can_earn_achievement(
        self, user_id: str, achievement_def: AchievementDefinition, user_progress: dict
    ) -> bool:
        """Check if user can earn achievement (prerequisites, not already earned, etc.)"""
        # Check if already earned (and not repeatable)
        if not achievement_def.repeatable:
            if user_progress.get(achievement_def.id, {}).get("progress", 0) >= 1.0:
                return False

        # Check prerequisites
        for prereq in achievement_def.prerequisites:
            if user_progress.get(prereq, {}).get("progress", 0) < 1.0:
                return False

        # Check time limits
        if achievement_def.limited_time and datetime.utcnow() > achievement_def.limited_time:
            return False

        return True

    async def _calculate_progress_update(
        self, event: GamificationEvent, achievement_def: AchievementDefinition
    ) -> float:
        """Calculate how much progress this event contributes to achievement"""
        # Simplified progress calculation
        # In production, this would be more sophisticated based on event data
        progress_mapping = {
            "assessment_completed": {
                "first_assessment": 1.0,
                "power_user": 0.02,
                "perfectionist": 0.01,
            },
            "login": {"daily_streak_7": 0.14, "daily_streak_30": 0.03},
            "team_activity": {"team_leader": 0.2, "collaborator": 0.1},
            "experimental_feature_used": {"experimental_explorer": 0.33},
        }

        return progress_mapping.get(event.event_type, {}).get(achievement_def.id, 0)

    async def _update_achievement_progress(
        self, user_id: str, achievement_id: str, progress_update: float
    ) -> float:
        """Update user's progress on an achievement"""
        # In production, this would update the database
        user_progress = await self._get_user_achievement_progress(user_id)
        current_progress = user_progress.get(achievement_id, {}).get("progress", 0)
        new_progress = min(1.0, current_progress + progress_update)
        return new_progress

    async def _award_achievement(
        self, user_id: str, achievement_def: AchievementDefinition, event_data: dict
    ) -> UserAchievement:
        """Award achievement to user"""
        # Create user achievement record
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_def.id,
            earned_date=datetime.utcnow(),
            progress=1.0,
            milestone_data=event_data,
            repeat_count=1,
            shared=False,
        )

        # Award points and unlock rewards
        await self._award_points(user_id, achievement_def.points)
        await self._unlock_rewards(user_id, achievement_def.rewards)

        # Log achievement unlock
        logger.info(f"Achievement unlocked: {achievement_def.name} for user {user_id}")

        return user_achievement

    async def _award_points(self, user_id: str, points: int) -> None:
        """Award points to user"""
        # In production, update user's total points in database

    async def _unlock_rewards(self, user_id: str, rewards: dict[str, Any]) -> None:
        """Unlock rewards for achievement"""
        # In production, process reward unlocking

    async def _update_user_stats(self, user_id: str) -> None:
        """Update user statistics and leaderboards"""
        # Update various user statistics

    async def _update_leaderboards(self, user_id: str) -> None:
        """Update user's position on leaderboards"""
        # Update leaderboard rankings

    async def _get_current_streak(self, user_id: str) -> int:
        """Get user's current activity streak"""
        # In production, calculate from user activity logs
        return 5  # Mock data

    async def _get_longest_streak(self, user_id: str) -> int:
        """Get user's longest activity streak"""
        # In production, calculate from user activity history
        return 23  # Mock data

    async def _get_user_leaderboard_rank(self, user_id: str) -> int | None:
        """Get user's rank on main leaderboard"""
        # In production, query leaderboard database
        return 42  # Mock data

    async def _get_user_special_badges(self, user_id: str) -> list[str]:
        """Get special badges earned by user"""
        # In production, query user's special badges
        return ["innovation_leader", "mentor_excellence"]  # Mock data
