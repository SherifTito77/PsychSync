"""
File Path: app/services/team_optimization_service.py
Service layer for team optimization
Bridges API endpoints and optimization engine
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.db.models.user import User
from app.core.database import SessionLocal  # Changed from app.db.session
from app.db.models.team import Team, TeamMember, TeamRole
from app.db.models.assessment import AssessmentResponse
from app.services.optimizer.team_optimizer import (
    TeamOptimizationEngine,
    TeamMemberProfile,
    TeamRequirements,
    OptimizedTeam
)

logger = logging.getLogger(__name__)


class TeamOptimizationService:
    """Service for team composition optimization"""
    
    def __init__(self):
        self.optimizer = TeamOptimizationEngine()
    
    async def optimize_team_composition(
        self,
        db: Session,
        team_requirements: Dict[str, Any],
        organization_id: int,
        existing_team_id: Optional[int] = None
    ) -> OptimizedTeam:
        """
        Optimize team composition based on requirements
        
        Args:
            db: Database session
            team_requirements: Team requirements dict
            organization_id: Organization ID
            existing_team_id: Optional existing team ID
        
        Returns:
            OptimizedTeam with selected members
        """
        logger.info(f"Starting team optimization for org {organization_id}")
        
        # Get candidate pool from organization
        candidates = await self._build_candidate_pool(db, organization_id)
        
        if not candidates:
            raise ValueError("No eligible candidates found for optimization")
        
        # Get existing team members if team exists
        existing_members = []
        if existing_team_id:
            existing_members = await self._get_existing_members(
                db,
                existing_team_id
            )
        
        # Convert requirements dict to TeamRequirements object
        requirements = self._build_requirements(team_requirements)
        
        # Run optimization
        optimized_team = self.optimizer.optimize_team(
            candidates,
            requirements,
            existing_members
        )
        
        logger.info(
            f"Team optimization complete: {len(optimized_team.members)} members "
            f"with score {optimized_team.overall_score:.2f}"
        )
        
        return optimized_team
    
    async def analyze_team(
        self,
        db: Session,
        team_id: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Analyze existing team composition
        
        Args:
            db: Database session
            team_id: Team ID to analyze
            organization_id: Organization ID
        
        Returns:
            Team analysis results
        """
        logger.info(f"Analyzing team {team_id}")
        
        # Get team
        team = result = await db.execute(query)
        return result.scalars().all()
        
        if not team:
            raise ValueError(f"Team {team_id} not found")
        
        # Get team members
        members = await self._get_existing_members(db, team_id)
        
        if not members:
            raise ValueError("Team has no members to analyze")
        
        # Create mock requirements for analysis
        requirements = TeamRequirements(
            team_id=team.id,
            team_name=team.name,
            min_size=len(members),
            max_size=len(members),
            target_size=len(members),
            required_roles={},
            optional_roles={},
            required_skills={},
            desired_skills={},
            min_personality_diversity=0.3,
            max_personality_similarity=0.7
        )
        
        # Run analysis
        analysis = self.optimizer._create_team_result(
            members,
            requirements,
            overall_score=85.0  # Will be calculated
        )
        
        return {
            'team_id': team.id,
            'team_name': team.name,
            'member_count': len(members),
            'overall_score': analysis.overall_score,
            'compatibility_score': analysis.compatibility_score,
            'skill_coverage_score': analysis.skill_coverage_score,
            'diversity_score': analysis.diversity_score,
            'balance_score': analysis.balance_score,
            'strengths': analysis.strengths,
            'gaps': analysis.gaps,
            'recommendations': analysis.recommendations,
            'personality_profile': analysis.personality_profile,
            'role_distribution': analysis.role_distribution
        }
    
    async def check_member_compatibility(
        self,
        db: Session,
        user_id_1: int,
        user_id_2: int,
        organization_id: int
    ) -> Dict[str, Any]:
        """
        Check compatibility between two team members
        
        Args:
            db: Database session
            user_id_1: First user ID
            user_id_2: Second user ID
            organization_id: Organization ID
        
        Returns:
            Compatibility analysis
        """
        logger.info(f"Checking compatibility: {user_id_1} <-> {user_id_2}")
        
        # Get both users
        user1 = result = await db.execute(query)
        return result.scalars().all()
        
        user2 = result = await db.execute(query)
        return result.scalars().all()
        
        if not user1 or not user2:
            raise ValueError("One or both users not found")
        
        # Convert to profiles
        profile1 = await self._user_to_profile(db, user1)
        profile2 = await self._user_to_profile(db, user2)
        
        # Calculate compatibility
        compatibility_score = self.optimizer._calculate_personality_compatibility(
            profile1,
            profile2
        )
        
        # Determine level
        if compatibility_score >= 75:
            level = "High"
            color = "green"
        elif compatibility_score >= 50:
            level = "Medium"
            color = "yellow"
        else:
            level = "Low"
            color = "red"
        
        return {
            'user_1': {
                'id': user1.id,
                'name': user1.full_name,
                'email': user1.email
            },
            'user_2': {
                'id': user2.id,
                'name': user2.full_name,
                'email': user2.email
            },
            'compatibility_score': round(compatibility_score, 2),
            'compatibility_level': level,
            'color_indicator': color,
            'recommendations': self._generate_collaboration_tips(
                profile1,
                profile2,
                compatibility_score
            )
        }
    
    async def get_candidate_pool(
        self,
        db: Session,
        organization_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available candidates for team optimization
        
        Args:
            db: Database session
            organization_id: Organization ID
            filters: Optional filters
        
        Returns:
            List of candidate profiles
        """
        candidates = await self._build_candidate_pool(
            db,
            organization_id,
            filters
        )
        
        return [
            {
                'user_id': c.user_id,
                'name': c.name,
                'email': c.email,
                'department': c.department,
                'seniority_level': c.seniority_level,
                'availability': c.availability,
                'skills': c.skills,
                'personality_traits': {
                    'openness': c.openness,
                    'conscientiousness': c.conscientiousness,
                    'extraversion': c.extraversion,
                    'agreeableness': c.agreeableness,
                    'neuroticism': c.neuroticism
                }
            }
            for c in candidates
        ]
    
    # =====================================================================
    # HELPER METHODS
    # =====================================================================
    
    async def _build_candidate_pool(
        self,
        db: Session,
        organization_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[TeamMemberProfile]:
        """Build pool of candidate profiles"""
        query = db.query(User).filter(
            User.organization_id == organization_id,
            User.is_active == True
        )
        
        # Apply filters if provided
        if filters:
            if 'min_availability' in filters:
                # Would filter by availability if stored in User model
                pass
            if 'department' in filters:
                # Would filter by department
                pass
            if 'skills' in filters:
                # Would filter by required skills
                pass
        
        users = query.all()
        
        profiles = []
        for user in users:
            profile = await self._user_to_profile(db, user)
            profiles.append(profile)
        
        return profiles
    
    async def _get_existing_members(
        self,
        db: Session,
        team_id: int
    ) -> List[TeamMemberProfile]:
        """Get existing team member profiles"""
        team_members = result = await db.execute(query)
        return result.scalars().all()
        
        profiles = []
        for tm in team_members:
            if tm.user and tm.user.is_active:
                profile = await self._user_to_profile(db, tm.user)
                profiles.append(profile)
        
        return profiles
    
    async def _user_to_profile(
        self,
        db: Session,
        user: User
    ) -> TeamMemberProfile:
        """Convert User to TeamMemberProfile"""
        
        # Get latest personality assessment
        personality = await self._get_user_personality(db, user.id)
        
        # Get skills from assessments or profile
        skills = await self._get_user_skills(db, user.id)
        
        # Default values - should be fetched from actual data
        profile = TeamMemberProfile(
            user_id=user.id,
            name=user.full_name or user.email,
            email=user.email,
            openness=personality.get('openness', 60.0),
            conscientiousness=personality.get('conscientiousness', 70.0),
            extraversion=personality.get('extraversion', 55.0),
            agreeableness=personality.get('agreeableness', 65.0),
            neuroticism=personality.get('neuroticism', 40.0),
            skills=skills,
            preferred_roles=['Member'],  # Default role
            role_compatibility={'Member': 80.0},
            availability=80.0,  # Default availability
            max_teams=3,
            current_teams=await self._count_user_teams(db, user.id),
            past_performance=75.0,  # Would calculate from actual data
            collaboration_score=70.0,  # Would calculate from actual data
            department="General",  # Would get from user profile
            seniority_level="Mid",  # Would get from user profile
            tenure_months=12  # Would calculate from user.created_at
        )
        
        return profile
    
    async def _get_user_personality(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, float]:
        """Get user's personality traits from latest assessment"""
        
        # Get latest personality assessment response
        response = db.query(AssessmentResponse).filter(
            AssessmentResponse.respondent_id == user_id,
            AssessmentResponse.completed_at.isnot(None)
        ).order_by(
            AssessmentResponse.completed_at.desc()
        ).first()
        
        if response and response.score_data:
            # Extract personality traits from score data
            return {
                'openness': response.score_data.get('openness', 60.0),
                'conscientiousness': response.score_data.get('conscientiousness', 70.0),
                'extraversion': response.score_data.get('extraversion', 55.0),
                'agreeableness': response.score_data.get('agreeableness', 65.0),
                'neuroticism': response.score_data.get('neuroticism', 40.0)
            }
        
        # Return defaults if no assessment data
        return {
            'openness': 60.0,
            'conscientiousness': 70.0,
            'extraversion': 55.0,
            'agreeableness': 65.0,
            'neuroticism': 40.0
        }
    
    async def _get_user_skills(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, float]:
        """Get user's skills from assessments or profile"""
        
        # Would extract from skills assessments
        # Placeholder implementation
        return {
            'Leadership': 70.0,
            'Communication': 75.0,
            'Problem Solving': 80.0,
            'Teamwork': 85.0
        }
    
    async def _count_user_teams(
        self,
        db: Session,
        user_id: int
    ) -> int:
        """Count number of teams user is currently in"""
        return db.query(TeamMember).filter(
            TeamMember.user_id == user_id
        ).count()
    
    def _build_requirements(
        self,
        requirements_dict: Dict[str, Any]
    ) -> TeamRequirements:
        """Convert requirements dict to TeamRequirements object"""
        return TeamRequirements(
            team_id=requirements_dict.get('team_id', 0),
            team_name=requirements_dict.get('team_name', 'New Team'),
            min_size=requirements_dict.get('min_size', 3),
            max_size=requirements_dict.get('max_size', 10),
            target_size=requirements_dict.get('target_size', 5),
            required_roles=requirements_dict.get('required_roles', {}),
            optional_roles=requirements_dict.get('optional_roles', {}),
            required_skills=requirements_dict.get('required_skills', {}),
            desired_skills=requirements_dict.get('desired_skills', {}),
            min_personality_diversity=requirements_dict.get('min_personality_diversity', 0.3),
            max_personality_similarity=requirements_dict.get('max_personality_similarity', 0.7),
            max_same_department=requirements_dict.get('max_same_department'),
            min_senior_members=requirements_dict.get('min_senior_members'),
            max_junior_members=requirements_dict.get('max_junior_members')
        )
    
    def _generate_collaboration_tips(
        self,
        profile1: TeamMemberProfile,
        profile2: TeamMemberProfile,
        compatibility_score: float
    ) -> List[str]:
        """Generate collaboration recommendations"""
        tips = []
        
        if compatibility_score >= 75:
            tips.append("Excellent compatibility - leverage natural synergy")
            tips.append("Consider pairing on complex projects")
        elif compatibility_score >= 50:
            tips.append("Good compatibility - establish clear communication")
            tips.append("Define roles and responsibilities early")
        else:
            tips.append("Moderate compatibility - structured interaction recommended")
            tips.append("Consider team-building activities")
        
        # Personality-specific tips
        if abs(profile1.extraversion - profile2.extraversion) > 40:
            tips.append("Balance meeting styles for introvert-extravert differences")
        
        if profile1.conscientiousness > 75 and profile2.conscientiousness < 50:
            tips.append("Align on quality standards and deadlines early")
        
        return tips