"""
Skill Gap Analysis Service

Advanced skill gap analysis and competency development system for organizations.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import (
    User,
)
from app.services.team_optimization_service import (
    # PersonalityProfile, SkillRequirement, CompetencyLevel,  # TODO: Implement these classes
    get_personality_profile_for_user,
)

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    TECHNICAL = "technical"
    SOFT_SKILLS = "soft_skills"
    LEADERSHIP = "leadership"
    DOMAIN = "domain"
    METHODOLOGY = "methodology"


class LearningStyle(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"
    MIXED = "mixed"


@dataclass
class SkillAssessment:
    """Individual skill assessment result"""

    skill_name: str
    category: SkillCategory
    current_level: float  # 0-100
    required_level: float  # 0-100
    gap_percentage: float
    priority: str  # critical, high, medium, low
    assessment_date: datetime
    confidence_score: float


@dataclass
class SkillDemand:
    """Future skill demand prediction"""

    skill_name: str
    category: SkillCategory
    current_demand: float
    predicted_demand_12m: float
    predicted_demand_24m: float
    growth_rate: float
    market_trend: str  # growing, stable, declining
    industry_relevance: float


@dataclass
class LearningRecommendation:
    """Personalized learning recommendation"""

    skill_name: str
    learning_style: LearningStyle
    recommended_resources: list[dict]
    estimated_duration: int  # days
    difficulty_level: str  # beginner, intermediate, advanced
    completion_probability: float
    expected_improvement: float
    cost_estimate: float | None


@dataclass
class DevelopmentProgram:
    """Structured development program recommendation"""

    program_name: str
    target_skills: list[str]
    duration_weeks: int
    delivery_method: str  # online, in_person, blended, mentorship
    provider: str
    estimated_cost: float
    expected_roi: float
    success_rate: float
    prerequisites: list[str]


@dataclass
class CareerTrajectory:
    """Career path analysis with skill requirements"""

    current_role: str
    target_role: str
    time_to_promotion: int  # months
    required_skills: list[dict]
    skill_development_plan: list[LearningRecommendation]
    promotion_probability: float
    salary_impact: float


class SkillGapAnalyzer:
    """Advanced skill gap analysis engine"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.industry_trends = self._load_industry_trends()
        self.learning_resources = self._load_learning_resources()

    def _load_industry_trends(self) -> dict[str, dict]:
        """Load industry skill trends and market demand data"""
        # In production, this would integrate with external APIs
        return {
            "technical": {
                "cloud_computing": {"growth_rate": 0.15, "trend": "growing"},
                "ai_ml": {"growth_rate": 0.25, "trend": "growing"},
                "cybersecurity": {"growth_rate": 0.20, "trend": "growing"},
                "data_analysis": {"growth_rate": 0.18, "trend": "growing"},
                "devops": {"growth_rate": 0.12, "trend": "growing"},
                "mobile_development": {"growth_rate": 0.08, "trend": "stable"},
                "web_development": {"growth_rate": 0.05, "trend": "stable"},
            },
            "soft_skills": {
                "leadership": {"growth_rate": 0.10, "trend": "growing"},
                "communication": {"growth_rate": 0.08, "trend": "stable"},
                "collaboration": {"growth_rate": 0.06, "trend": "stable"},
                "problem_solving": {"growth_rate": 0.12, "trend": "growing"},
                "adaptability": {"growth_rate": 0.15, "trend": "growing"},
                "emotional_intelligence": {"growth_rate": 0.14, "trend": "growing"},
            },
        }

    def _load_learning_resources(self) -> dict[str, list[dict]]:
        """Load learning resource database"""
        return {
            "online_courses": [
                {
                    "provider": "Coursera",
                    "courses": [
                        {
                            "name": "Machine Learning",
                            "skill": "ai_ml",
                            "duration": 12,
                            "cost": 79,
                            "style": "visual",
                        },
                        {
                            "name": "Cloud Architecture",
                            "skill": "cloud_computing",
                            "duration": 8,
                            "cost": 89,
                            "style": "reading",
                        },
                        {
                            "name": "Leadership Essentials",
                            "skill": "leadership",
                            "duration": 6,
                            "cost": 69,
                            "style": "mixed",
                        },
                    ],
                }
            ],
            "certifications": [
                {
                    "provider": "AWS",
                    "certifications": [
                        {
                            "name": "AWS Solutions Architect",
                            "skill": "cloud_computing",
                            "duration": 16,
                            "cost": 300,
                            "style": "reading",
                        }
                    ],
                }
            ],
            "workshops": [
                {
                    "provider": "Internal Training",
                    "workshops": [
                        {
                            "name": "Communication Skills",
                            "skill": "communication",
                            "duration": 2,
                            "cost": 0,
                            "style": "kinesthetic",
                        }
                    ],
                }
            ],
        }

    async def analyze_individual_skill_gaps(self, user_id: str) -> list[SkillAssessment]:
        """Analyze skill gaps for an individual user"""
        try:
            # Get user's personality profile for skill prediction
            personality_profile = await get_personality_profile_for_user(user_id, self.db)

            # Get current skill assessments
            current_assessments = await self._get_current_skill_assessments(user_id)

            # Get role requirements
            role_requirements = await self._get_role_requirements(user_id)

            skill_gaps = []

            for skill, requirement in role_requirements.items():
                current_level = current_assessments.get(skill, 0)
                gap_percentage = max(0, (requirement - current_level) / requirement * 100)

                # Determine priority based on role importance and gap size
                priority = self._calculate_skill_priority(
                    skill, gap_percentage, personality_profile
                )

                assessment = SkillAssessment(
                    skill_name=skill,
                    category=self._categorize_skill(skill),
                    current_level=current_level,
                    required_level=requirement,
                    gap_percentage=gap_percentage,
                    priority=priority,
                    assessment_date=datetime.utcnow(),
                    confidence_score=self._calculate_assessment_confidence(
                        current_level, personality_profile
                    ),
                )

                skill_gaps.append(assessment)

            # Sort by priority and gap size
            skill_gaps.sort(key=lambda x: (x.priority, -x.gap_percentage))

            logger.info(f"Analyzed {len(skill_gaps)} skill gaps for user {user_id}")
            return skill_gaps

        except Exception as e:
            logger.error(f"Error analyzing skill gaps for user {user_id}: {e}")
            raise

    async def analyze_organizational_skill_gaps(self, organization_id: str) -> dict[str, Any]:
        """Analyze skill gaps across the entire organization"""
        try:
            # Get all users in organization
            users = self.db.query(User).filter(User.organization_id == organization_id).all()

            # Aggregate skill gaps by department and role
            organizational_gaps = {
                "overall_gaps": {},
                "department_gaps": {},
                "critical_gaps": [],
                "skill_supply_demand": {},
                "recommendations": [],
            }

            all_skill_assessments = []

            for user in users:
                user_gaps = await self.analyze_individual_skill_gaps(user.id)
                all_skill_assessments.extend(user_gaps)

                # Group by department (you might need to add department to User model)
                department = getattr(user, "department", "General")
                if department not in organizational_gaps["department_gaps"]:
                    organizational_gaps["department_gaps"][department] = []

                organizational_gaps["department_gaps"][department].extend(user_gaps)

            # Calculate overall skill gaps
            skill_gap_summary = self._aggregate_skill_gaps(all_skill_assessments)
            organizational_gaps["overall_gaps"] = skill_gap_summary

            # Identify critical gaps (high priority + high gap percentage)
            organizational_gaps["critical_gaps"] = [
                gap
                for gap in all_skill_assessments
                if gap.priority in ["critical", "high"] and gap.gap_percentage > 40
            ]

            # Calculate skill supply vs demand
            organizational_gaps["skill_supply_demand"] = await self._calculate_skill_supply_demand(
                organization_id
            )

            logger.info(f"Analyzed organizational skill gaps for org {organization_id}")
            return organizational_gaps

        except Exception as e:
            logger.error(
                f"Error analyzing organizational skill gaps for org {organization_id}: {e}"
            )
            raise

    async def predict_future_skill_demands(
        self, organization_id: str, timeframe_months: int = 24
    ) -> list[SkillDemand]:
        """Predict future skill demands based on industry trends and organizational goals"""
        try:
            # Get current organizational skill demands
            current_demands = await self._get_current_skill_demands(organization_id)

            # Get organizational strategic goals and industry
            org_info = self._get_organization_info(organization_id)
            industry = org_info.get("industry", "technology")

            skill_demands = []

            for category_data in self.industry_trends.values():
                for skill_name, trend_data in category_data.items():
                    current_demand = current_demands.get(skill_name, 50)  # Default baseline

                    # Apply industry growth rate
                    growth_rate = trend_data["growth_rate"]
                    predicted_demand = current_demand * (1 + growth_rate) ** (timeframe_months / 12)

                    # Adjust for organizational strategic initiatives
                    strategic_adjustment = self._calculate_strategic_adjustment(
                        skill_name, org_info.get("strategic_initiatives", [])
                    )

                    final_demand = predicted_demand * (1 + strategic_adjustment)

                    skill_demand = SkillDemand(
                        skill_name=skill_name,
                        category=self._categorize_skill(skill_name),
                        current_demand=current_demand,
                        predicted_demand_12m=current_demand * (1 + growth_rate),
                        predicted_demand_24m=final_demand,
                        growth_rate=growth_rate,
                        market_trend=trend_data["trend"],
                        industry_relevance=self._calculate_industry_relevance(skill_name, industry),
                    )

                    skill_demands.append(skill_demand)

            # Sort by growth potential and relevance
            skill_demands.sort(key=lambda x: (x.growth_rate * x.industry_relevance), reverse=True)

            logger.info(f"Predicted future skill demands for org {organization_id}")
            return skill_demands[:20]  # Return top 20 skills

        except Exception as e:
            logger.error(f"Error predicting future skill demands for org {organization_id}: {e}")
            raise

    async def recommend_learning_path(
        self, user_id: str, target_skills: list[str]
    ) -> list[LearningRecommendation]:
        """Generate personalized learning recommendations"""
        try:
            # Get user profile and preferences
            personality_profile = await get_personality_profile_for_user(user_id, self.db)
            learning_style = self._determine_learning_style(personality_profile)

            # Get current skill levels
            current_assessments = await self._get_current_skill_assessments(user_id)

            recommendations = []

            for skill in target_skills:
                current_level = current_assessments.get(skill, 0)
                target_level = 100  # Full proficiency
                gap_size = target_level - current_level

                # Find appropriate learning resources
                suitable_resources = self._find_suitable_resources(
                    skill, learning_style, current_level, gap_size
                )

                # Calculate completion probability based on personality and learning style match
                completion_probability = self._calculate_completion_probability(
                    personality_profile, learning_style, suitable_resources
                )

                # Estimate duration and difficulty
                duration, difficulty = self._estimate_learning_parameters(
                    gap_size, learning_style, suitable_resources
                )

                recommendation = LearningRecommendation(
                    skill_name=skill,
                    learning_style=learning_style,
                    recommended_resources=suitable_resources,
                    estimated_duration=duration,
                    difficulty_level=difficulty,
                    completion_probability=completion_probability,
                    expected_improvement=min(
                        100, current_level + gap_size * 0.8
                    ),  # Conservative estimate
                    cost_estimate=sum(r.get("cost", 0) for r in suitable_resources),
                )

                recommendations.append(recommendation)

            # Sort by completion probability and expected improvement
            recommendations.sort(
                key=lambda x: (x.completion_probability * x.expected_improvement), reverse=True
            )

            logger.info(f"Generated learning recommendations for user {user_id}")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating learning recommendations for user {user_id}: {e}")
            raise

    async def recommend_development_programs(
        self, user_id: str, organization_id: str
    ) -> list[DevelopmentProgram]:
        """Recommend structured development programs"""
        try:
            # Get user skill gaps
            skill_gaps = await self.analyze_individual_skill_gaps(user_id)
            target_skills = [
                gap.skill_name for gap in skill_gaps if gap.priority in ["critical", "high"]
            ]

            # Get available programs
            available_programs = await self._get_available_programs(organization_id)

            program_recommendations = []

            for program in available_programs:
                # Calculate skill coverage
                skill_coverage = len(set(program["target_skills"]) & set(target_skills)) / len(
                    target_skills
                )

                # Calculate expected ROI based on organizational data
                expected_roi = await self._calculate_program_roi(program, organization_id)

                # Calculate success probability for this user
                success_probability = await self._calculate_success_probability(user_id, program)

                if skill_coverage > 0.3:  # Program covers at least 30% of target skills
                    recommendation = DevelopmentProgram(
                        program_name=program["name"],
                        target_skills=program["target_skills"],
                        duration_weeks=program["duration"],
                        delivery_method=program["delivery_method"],
                        provider=program["provider"],
                        estimated_cost=program["cost"],
                        expected_roi=expected_roi,
                        success_rate=program["success_rate"],
                        prerequisites=program.get("prerequisites", []),
                    )

                    program_recommendations.append(recommendation)

            # Sort by ROI and success rate
            program_recommendations.sort(
                key=lambda x: (x.expected_roi * x.success_rate), reverse=True
            )

            logger.info(f"Recommended development programs for user {user_id}")
            return program_recommendations[:5]  # Return top 5 recommendations

        except Exception as e:
            logger.error(f"Error recommending development programs for user {user_id}: {e}")
            raise

    async def analyze_career_trajectories(self, user_id: str) -> list[CareerTrajectory]:
        """Analyze potential career paths and development requirements"""
        try:
            # Get current role and skills
            current_role = await self._get_user_current_role(user_id)
            current_skills = await self._get_current_skill_assessments(user_id)

            # Get possible career progressions
            career_paths = await self._get_career_progression_paths(current_role)

            trajectories = []

            for target_role in career_paths:
                # Get role requirements for target position
                role_requirements = await self._get_role_requirements_by_name(target_role)

                # Calculate skill gaps for this role
                skill_gaps = []
                for skill, required_level in role_requirements.items():
                    current_level = current_skills.get(skill, 0)
                    if current_level < required_level:
                        skill_gaps.append(
                            {
                                "skill": skill,
                                "current_level": current_level,
                                "required_level": required_level,
                                "gap": required_level - current_level,
                            }
                        )

                # Estimate time to promotion based on skill gaps and organizational data
                time_to_promotion = self._estimate_promotion_timeline(skill_gaps)

                # Generate learning plan
                target_skills_list = [gap["skill"] for gap in skill_gaps]
                learning_plan = await self.recommend_learning_path(user_id, target_skills_list)

                # Calculate promotion probability
                promotion_probability = self._calculate_promotion_probability(
                    current_skills, role_requirements, learning_plan
                )

                # Estimate salary impact
                salary_impact = await self._estimate_salary_impact(current_role, target_role)

                trajectory = CareerTrajectory(
                    current_role=current_role,
                    target_role=target_role,
                    time_to_promotion=time_to_promotion,
                    required_skills=skill_gaps,
                    skill_development_plan=learning_plan,
                    promotion_probability=promotion_probability,
                    salary_impact=salary_impact,
                )

                trajectories.append(trajectory)

            # Sort by promotion probability and salary impact
            trajectories.sort(
                key=lambda x: (x.promotion_probability * x.salary_impact), reverse=True
            )

            logger.info(f"Analyzed career trajectories for user {user_id}")
            return trajectories

        except Exception as e:
            logger.error(f"Error analyzing career trajectories for user {user_id}: {e}")
            raise

    # Helper methods
    async def _get_current_skill_assessments(self, user_id: str) -> dict[str, float]:
        """Get current skill assessment scores for user"""
        # This would integrate with your assessment system
        # For now, return mock data
        return {
            "leadership": 65,
            "communication": 78,
            "technical_skills": 82,
            "problem_solving": 71,
            "teamwork": 85,
            "adaptability": 68,
            "ai_ml": 45,
            "cloud_computing": 52,
        }

    async def _get_role_requirements(self, user_id: str) -> dict[str, float]:
        """Get skill requirements for user's current role"""
        # This would integrate with your role/competency framework
        return {
            "leadership": 80,
            "communication": 85,
            "technical_skills": 75,
            "problem_solving": 80,
            "teamwork": 90,
            "adaptability": 75,
        }

    async def _get_role_requirements_by_name(self, role_name: str) -> dict[str, float]:
        """Get skill requirements for a specific role"""
        role_requirements = {
            "Senior Developer": {
                "technical_skills": 90,
                "problem_solving": 85,
                "leadership": 70,
                "communication": 75,
            },
            "Team Lead": {
                "leadership": 85,
                "communication": 90,
                "problem_solving": 80,
                "technical_skills": 70,
            },
            "Engineering Manager": {
                "leadership": 95,
                "communication": 90,
                "strategic_thinking": 85,
                "team_development": 90,
            },
        }
        return role_requirements.get(role_name, {})

    def _categorize_skill(self, skill_name: str) -> SkillCategory:
        """Categorize skill into type"""
        technical_skills = [
            "ai_ml",
            "cloud_computing",
            "data_analysis",
            "devops",
            "mobile_development",
            "web_development",
        ]
        soft_skills = ["communication", "collaboration", "adaptability", "emotional_intelligence"]
        leadership_skills = ["leadership", "team_development", "strategic_thinking"]

        if skill_name in technical_skills:
            return SkillCategory.TECHNICAL
        if skill_name in soft_skills:
            return SkillCategory.SOFT_SKILLS
        if skill_name in leadership_skills:
            return SkillCategory.LEADERSHIP
        return SkillCategory.DOMAIN

    def _calculate_skill_priority(
        self, skill_name: str, gap_percentage: float, personality
    ) -> str:  # TODO: Fix PersonalityProfile type
        """Calculate skill development priority"""
        if gap_percentage > 50:
            return "critical"
        if gap_percentage > 30:
            return "high"
        if gap_percentage > 15:
            return "medium"
        return "low"

    def _calculate_assessment_confidence(
        self, current_level: float, personality
    ) -> float:  # TODO: Fix PersonalityProfile type
        """Calculate confidence score for skill assessment"""
        # Base confidence on assessment recency and consistency
        base_confidence = 0.8

        # Adjust based on personality traits that affect self-assessment accuracy
        if personality and personality.traits:
            if personality.traits.get("conscientiousness", 0) > 0.7:
                base_confidence += 0.1  # More self-aware
            if personality.traits.get("neuroticism", 0) > 0.7:
                base_confidence -= 0.1  # May underestimate abilities

        return min(1.0, base_confidence)

    def _aggregate_skill_gaps(self, assessments: list[SkillAssessment]) -> dict[str, Any]:
        """Aggregate individual skill gaps into organizational view"""
        skill_summary = {}

        for assessment in assessments:
            if assessment.skill_name not in skill_summary:
                skill_summary[assessment.skill_name] = {
                    "total_gaps": 0,
                    "avg_gap": 0,
                    "priority_count": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                    "category": assessment.category.value,
                }

            summary = skill_summary[assessment.skill_name]
            summary["total_gaps"] += 1
            summary["avg_gap"] += assessment.gap_percentage
            summary["priority_count"][assessment.priority] += 1

        # Calculate averages
        for skill_data in skill_summary.values():
            if skill_data["total_gaps"] > 0:
                skill_data["avg_gap"] /= skill_data["total_gaps"]

        return skill_summary
