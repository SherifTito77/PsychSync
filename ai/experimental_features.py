
#ai/experimental_features.py
"""
Experimental Features Lab for PsychSync
A/B testing framework, gamification engine, and feature flags.

Requirements:
    pip install pydantic
"""

import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json


# ============================================================================
# A/B Testing Framework
# ============================================================================

class VariantType(Enum):
    """A/B test variant types."""
    CONTROL = "control"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    VARIANT_C = "variant_c"


@dataclass
class ABTest:
    """A/B test configuration."""
    test_id: str
    name: str
    description: str
    variants: List[str]
    allocation_percentages: List[float]
    start_date: datetime
    end_date: Optional[datetime]
    is_active: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        if len(self.variants) != len(self.allocation_percentages):
            raise ValueError("Variants and allocation percentages must match")
        
        if abs(sum(self.allocation_percentages) - 1.0) > 0.001:
            raise ValueError("Allocation percentages must sum to 1.0")
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat() if self.end_date else None
        return data


@dataclass
class ABTestAssignment:
    """Record of user assignment to A/B test variant."""
    user_id: str
    test_id: str
    variant: str
    assigned_at: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['assigned_at'] = self.assigned_at.isoformat()
        return data


class ABTestingFramework:
    """
    Framework for managing A/B tests and feature experiments.
    """
    
    def __init__(self):
        """Initialize A/B testing framework."""
        self.active_tests: Dict[str, ABTest] = {}
        self.assignments: Dict[str, Dict[str, ABTestAssignment]] = {}
    
    def create_test(
        self,
        test_id: str,
        name: str,
        description: str,
        variants: List[str],
        allocation_percentages: List[float],
        duration_days: int
    ) -> ABTest:
        """
        Create a new A/B test.
        
        Args:
            test_id: Unique identifier for test
            name: Human-readable test name
            description: Test description
            variants: List of variant names (e.g., ['control', 'variant_a'])
            allocation_percentages: Allocation % for each variant (must sum to 1.0)
            duration_days: Test duration in days
            
        Returns:
            ABTest object
        """
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=duration_days)
        
        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            variants=variants,
            allocation_percentages=allocation_percentages,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        self.active_tests[test_id] = test
        self.assignments[test_id] = {}
        
        return test
    
    def assign_variant(
        self,
        user_id: str,
        test_id: str,
        force_variant: Optional[str] = None
    ) -> str:
        """
        Assign user to a test variant.
        Uses consistent hashing to ensure same user always gets same variant.
        
        Args:
            user_id: User identifier
            test_id: Test identifier
            force_variant: Force specific variant (for testing)
            
        Returns:
            Assigned variant name
        """
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} does not exist")
        
        test = self.active_tests[test_id]
        
        # Check if already assigned
        if test_id in self.assignments and user_id in self.assignments[test_id]:
            return self.assignments[test_id][user_id].variant
        
        # Force variant if specified
        if force_variant:
            if force_variant not in test.variants:
                raise ValueError(f"Invalid variant: {force_variant}")
            variant = force_variant
        else:
            # Consistent hashing for deterministic assignment
            hash_input = f"{user_id}:{test_id}".encode()
            hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
            random_value = (hash_value % 10000) / 10000.0
            
            # Determine variant based on allocation
            cumulative = 0.0
            variant = test.variants[-1]  # Default to last
            
            for i, percentage in enumerate(test.allocation_percentages):
                cumulative += percentage
                if random_value < cumulative:
                    variant = test.variants[i]
                    break
        
        # Record assignment
        assignment = ABTestAssignment(
            user_id=user_id,
            test_id=test_id,
            variant=variant,
            assigned_at=datetime.utcnow()
        )
        
        if test_id not in self.assignments:
            self.assignments[test_id] = {}
        
        self.assignments[test_id][user_id] = assignment
        
        return variant
    
    def get_variant(self, user_id: str, test_id: str) -> Optional[str]:
        """Get user's assigned variant if exists."""
        if test_id in self.assignments and user_id in self.assignments[test_id]:
            return self.assignments[test_id][user_id].variant
        return None
    
    def get_test_statistics(self, test_id: str) -> Dict:
        """Get statistics for a test."""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} does not exist")
        
        test = self.active_tests[test_id]
        assignments = self.assignments.get(test_id, {})
        
        # Count assignments per variant
        variant_counts = {variant: 0 for variant in test.variants}
        for assignment in assignments.values():
            variant_counts[assignment.variant] += 1
        
        total_assignments = len(assignments)
        
        # Calculate actual allocation percentages
        actual_percentages = {
            variant: (count / total_assignments * 100) if total_assignments > 0 else 0
            for variant, count in variant_counts.items()
        }
        
        return {
            'test_id': test_id,
            'name': test.name,
            'is_active': test.is_active,
            'total_participants': total_assignments,
            'variant_counts': variant_counts,
            'actual_allocation_percentages': actual_percentages,
            'expected_allocation_percentages': {
                variant: perc * 100
                for variant, perc in zip(test.variants, test.allocation_percentages)
            }
        }
    
    def end_test(self, test_id: str):
        """End an active test."""
        if test_id in self.active_tests:
            self.active_tests[test_id].is_active = False
            self.active_tests[test_id].end_date = datetime.utcnow()


# ============================================================================
# Gamification Engine
# ============================================================================

class AchievementType(Enum):
    """Types of achievements."""
    ATTENDANCE = "attendance"
    HOMEWORK = "homework"
    IMPROVEMENT = "improvement"
    MILESTONE = "milestone"
    ENGAGEMENT = "engagement"


@dataclass
class Achievement:
    """Achievement definition."""
    achievement_id: str
    name: str
    description: str
    achievement_type: AchievementType
    points: int
    icon: str
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['achievement_type'] = self.achievement_type.value
        return data


@dataclass
class UserProgress:
    """User's gamification progress."""
    user_id: str
    total_points: int
    level: int
    achievements_earned: List[str]
    streak_days: int
    last_activity: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_activity'] = self.last_activity.isoformat()
        return data


class GamificationEngine:
    """
    Gamification system for increasing client engagement.
    """
    
    def __init__(self):
        """Initialize gamification engine."""
        self.achievements: Dict[str, Achievement] = {}
        self.user_progress: Dict[str, UserProgress] = {}
        self._initialize_achievements()
    
    def _initialize_achievements(self):
        """Set up default achievements."""
        default_achievements = [
            Achievement(
                "first_session",
                "First Step",
                "Attended your first session",
                AchievementType.ATTENDANCE,
                points=10,
                icon="🎯"
            ),
            Achievement(
                "five_sessions",
                "Committed",
                "Attended 5 sessions",
                AchievementType.ATTENDANCE,
                points=50,
                icon="🌟"
            ),
            Achievement(
                "homework_master",
                "Homework Master",
                "Completed 10 homework assignments",
                AchievementType.HOMEWORK,
                points=100,
                icon="📚"
            ),
            Achievement(
                "week_streak",
                "Week Warrior",
                "7-day activity streak",
                AchievementType.ENGAGEMENT,
                points=75,
                icon="🔥"
            ),
            Achievement(
                "improvement_25",
                "Progress Pioneer",
                "25% improvement in symptoms",
                AchievementType.IMPROVEMENT,
                points=150,
                icon="📈"
            ),
            Achievement(
                "improvement_50",
                "Halfway Hero",
                "50% improvement in symptoms",
                AchievementType.IMPROVEMENT,
                points=300,
                icon="🏆"
            ),
            Achievement(
                "recovery",
                "Champion of Change",
                "Reached recovery milestone",
                AchievementType.MILESTONE,
                points=500,
                icon="👑"
            )
        ]
        
        for achievement in default_achievements:
            self.achievements[achievement.achievement_id] = achievement
    
    def get_user_progress(self, user_id: str) -> UserProgress:
        """Get or create user progress."""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(
                user_id=user_id,
                total_points=0,
                level=1,
                achievements_earned=[],
                streak_days=0,
                last_activity=datetime.utcnow()
            )
        return self.user_progress[user_id]
    
    def award_points(self, user_id: str, points: int, reason: str) -> Dict:
        """
        Award points to a user.
        
        Args:
            user_id: User identifier
            points: Points to award
            reason: Reason for points
            
        Returns:
            Dictionary with updated progress
        """
        progress = self.get_user_progress(user_id)
        
        old_points = progress.total_points
        old_level = progress.level
        
        progress.total_points += points
        progress.last_activity = datetime.utcnow()
        
        # Calculate new level (100 points per level)
        new_level = (progress.total_points // 100) + 1
        progress.level = new_level
        
        level_up = new_level > old_level
        
        return {
            'user_id': user_id,
            'points_awarded': points,
            'reason': reason,
            'total_points': progress.total_points,
            'level': progress.level,
            'level_up': level_up,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def unlock_achievement(self, user_id: str, achievement_id: str) -> Dict:
        """
        Unlock an achievement for a user.
        
        Args:
            user_id: User identifier
            achievement_id: Achievement to unlock
            
        Returns:
            Dictionary with achievement details
        """
        if achievement_id not in self.achievements:
            raise ValueError(f"Achievement {achievement_id} does not exist")
        
        progress = self.get_user_progress(user_id)
        achievement = self.achievements[achievement_id]
        
        # Check if already unlocked
        if achievement_id in progress.achievements_earned:
            return {
                'success': False,
                'message': 'Achievement already unlocked'
            }
        
        # Unlock achievement
        progress.achievements_earned.append(achievement_id)
        progress.total_points += achievement.points
        progress.last_activity = datetime.utcnow()
        
        # Check for level up
        new_level = (progress.total_points // 100) + 1
        level_up = new_level > progress.level
        progress.level = new_level
        
        return {
            'success': True,
            'achievement': achievement.to_dict(),
            'points_awarded': achievement.points,
            'total_points': progress.total_points,
            'level': progress.level,
            'level_up': level_up,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def update_streak(self, user_id: str) -> Dict:
        """
        Update user's activity streak.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with streak information
        """
        progress = self.get_user_progress(user_id)
        
        now = datetime.utcnow()
        last_activity = progress.last_activity
        
        # Calculate days since last activity
        days_since = (now - last_activity).days
        
        if days_since == 0:
            # Same day, no change
            pass
        elif days_since == 1:
            # Consecutive day, increment streak
            progress.streak_days += 1
            progress.last_activity = now
            
            # Check for streak achievements
            if progress.streak_days == 7 and 'week_streak' not in progress.achievements_earned:
                self.unlock_achievement(user_id, 'week_streak')
        else:
            # Streak broken
            progress.streak_days = 1
            progress.last_activity = now
        
        return {
            'user_id': user_id,
            'streak_days': progress.streak_days,
            'last_activity': progress.last_activity.isoformat()
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """
        Get top users by points.
        
        Args:
            limit: Number of top users to return
            
        Returns:
            List of user progress dictionaries
        """
        sorted_users = sorted(
            self.user_progress.values(),
            key=lambda x: x.total_points,
            reverse=True
        )
        
        leaderboard = []
        for rank, progress in enumerate(sorted_users[:limit], 1):
            leaderboard.append({
                'rank': rank,
                'user_id': progress.user_id,
                'total_points': progress.total_points,
                'level': progress.level,
                'achievements_count': len(progress.achievements_earned),
                'streak_days': progress.streak_days
            })
        
        return leaderboard
    
    def check_and_award_achievements(self, user_id: str, context: Dict) -> List[Dict]:
        """
        Check if user qualifies for any achievements based on context.
        
        Args:
            user_id: User identifier
            context: Context data (sessions_attended, homework_completed, etc.)
            
        Returns:
            List of newly unlocked achievements
        """
        progress = self.get_user_progress(user_id)
        unlocked = []
        
        # Check attendance achievements
        if context.get('sessions_attended') == 1 and 'first_session' not in progress.achievements_earned:
            result = self.unlock_achievement(user_id, 'first_session')
            if result['success']:
                unlocked.append(result)
        
        if context.get('sessions_attended') >= 5 and 'five_sessions' not in progress.achievements_earned:
            result = self.unlock_achievement(user_id, 'five_sessions')
            if result['success']:
                unlocked.append(result)
        
        # Check homework achievements
        if context.get('homework_completed') >= 10 and 'homework_master' not in progress.achievements_earned:
            result = self.unlock_achievement(user_id, 'homework_master')
            if result['success']:
                unlocked.append(result)
        
        # Check improvement achievements
        improvement_pct = context.get('improvement_percentage', 0)
        if improvement_pct >= 25 and 'improvement_25' not in progress.achievements_earned:
            result = self.unlock_achievement(user_id, 'improvement_25')
            if result['success']:
                unlocked.append(result)
        
        if improvement_pct >= 50 and 'improvement_50' not in progress.achievements_earned:
            result = self.unlock_achievement(user_id, 'improvement_50')
            if result['success']:
                unlocked.append(result)
        
        # Check recovery
        if context.get('recovered', False) and 'recovery' not in progress.achievements_earned:
            result = self.unlock_achievement(user_id, 'recovery')
            if result['success']:
                unlocked.append(result)
        
        return unlocked


# ============================================================================
# Feature Flags
# ============================================================================

class FeatureFlag:
    """
    Feature flag system for gradual rollouts.
    """
    
    def __init__(self):
        """Initialize feature flags."""
        self.flags: Dict[str, Dict] = {}
    
    def create_flag(
        self,
        flag_name: str,
        description: str,
        enabled: bool = False,
        rollout_percentage: float = 0.0,
        whitelist_users: Optional[List[str]] = None
    ):
        """
        Create a feature flag.
        
        Args:
            flag_name: Feature flag identifier
            description: Flag description
            enabled: Whether flag is enabled globally
            rollout_percentage: Percentage of users to enable (0-100)
            whitelist_users: List of users who always get feature
        """
        self.flags[flag_name] = {
            'description': description,
            'enabled': enabled,
            'rollout_percentage': rollout_percentage,
            'whitelist_users': whitelist_users or [],
            'created_at': datetime.utcnow().isoformat()
        }
    
    def is_enabled(self, flag_name: str, user_id: str) -> bool:
        """
        Check if feature is enabled for user.
        
        Args:
            flag_name: Feature flag name
            user_id: User identifier
            
        Returns:
            True if feature is enabled for user
        """
        if flag_name not in self.flags:
            return False
        
        flag = self.flags[flag_name]
        
        # Check if globally enabled
        if flag['enabled']:
            return True
        
        # Check whitelist
        if user_id in flag['whitelist_users']:
            return True
        
        # Check rollout percentage
        if flag['rollout_percentage'] > 0:
            hash_input = f"{user_id}:{flag_name}".encode()
            hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
            user_percentage = (hash_value % 100)
            
            return user_percentage < flag['rollout_percentage']
        
        return False
    
    def update_flag(self, flag_name: str, **kwargs):
        """Update flag settings."""
        if flag_name in self.flags:
            self.flags[flag_name].update(kwargs)


# Example usage
if __name__ == "__main__":
    print("Experimental Features Lab Demo")
    print("=" * 60)
    
    # 1. A/B Testing
    print("\n1. A/B Testing Framework")
    print("-" * 60)
    
    ab_framework = ABTestingFramework()
    
    # Create test
    test = ab_framework.create_test(
        test_id="onboarding_flow_v1",
        name="Onboarding Flow Experiment",
        description="Test new onboarding flow vs. control",
        variants=["control", "new_flow"],
        allocation_percentages=[0.5, 0.5],
        duration_days=30
    )
    
    print(f"Created test: {test.name}")
    print(f"Variants: {test.variants}")
    
    # Assign users
    for i in range(100):
        user_id = f"user_{i}"
        variant = ab_framework.assign_variant(user_id, test.test_id)
    
    stats = ab_framework.get_test_statistics(test.test_id)
    print(f"\nTest Statistics:")
    print(f"  Participants: {stats['total_participants']}")
    print(f"  Variant distribution: {stats['variant_counts']}")
    print(f"  Actual allocation: {stats['actual_allocation_percentages']}")
    
    # 2. Gamification
    print("\n2. Gamification Engine")
    print("-" * 60)
    
    gamification = GamificationEngine()
    
    # Award points
    result = gamification.award_points("user_1", 50, "Completed session")
    print(f"Awarded points: {result['points_awarded']} - {result['reason']}")
    print(f"Total points: {result['total_points']}, Level: {result['level']}")
    
    # Unlock achievement
    achievement_result = gamification.unlock_achievement("user_1", "first_session")
    if achievement_result['success']:
        print(f"\nUnlocked: {achievement_result['achievement']['name']}")
        print(f"  {achievement_result['achievement']['description']}")
        print(f"  +{achievement_result['points_awarded']} points")
    
    # Check achievements automatically
    context = {
        'sessions_attended': 5,
        'homework_completed': 12,
        'improvement_percentage': 30
    }
    
    new_achievements = gamification.check_and_award_achievements("user_2", context)
    print(f"\nAuto-awarded {len(new_achievements)} achievements for user_2")
    
    # Leaderboard
    for i in range(5):
        gamification.award_points(f"user_{i}", random.randint(50, 500), "Activity")
    
    leaderboard = gamification.get_leaderboard(limit=5)
    print("\nLeaderboard:")
    for entry in leaderboard:
        print(f"  {entry['rank']}. User {entry['user_id']}: {entry['total_points']} pts (Level {entry['level']})")
    
    # 3. Feature Flags
    print("\n3. Feature Flags")
    print("-" * 60)
    
    flags = FeatureFlag()
    
    # Create flags
    flags.create_flag(
        "new_dashboard",
        "New dashboard UI",
        enabled=False,
        rollout_percentage=25
    )
    
    flags.create_flag(
        "ai_insights",
        "AI-powered insights",
        enabled=False,
        rollout_percentage=10,
        whitelist_users=["admin_1", "beta_tester_1"]
    )
    
    # Check flags for users
    enabled_count = 0
    for i in range(100):
        if flags.is_enabled("new_dashboard", f"user_{i}"):
            enabled_count += 1
    
    print(f"New dashboard enabled for {enabled_count}/100 users (target: 25%)")
    
    # Whitelist check
    print(f"AI insights for admin_1: {flags.is_enabled('ai_insights', 'admin_1')}")
    print(f"AI insights for regular user: {flags.is_enabled('ai_insights', 'user_50')}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")