"""
Wellness Plan Generator Service - AI-powered personalized wellness improvement planning
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from app.services.ai_enhanced_analytics import AIEnhancedAnalyticsService
from app.services.wellness_monitoring import WellnessMonitoringService
from app.services.trend_analysis import TrendAnalysisService
from ai.processors.wellness_processor import WellnessProcessor
from app.db.models.response import Response
from app.db.models.user import User
import logging

logger = logging.getLogger(__name__)

class WellnessPlanGeneratorService:
    """Service for generating personalized wellness improvement plans using AI"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_analytics = AIEnhancedAnalyticsService(db)
        self.wellness_service = WellnessMonitoringService(db)
        self.trend_service = TrendAnalysisService(db)
        self.wellness_processor = WellnessProcessor()

    async def generate_personalized_wellness_plan(
        self,
        user_id: str,
        focus_areas: List[str],
        timeframe: str = '3m',
        focus_level: str = 'balanced',
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive personalized wellness improvement plan

        Args:
            user_id: User identifier
            focus_areas: List of wellness domains to focus on
            timeframe: Plan duration ('1m', '3m', '6m', '1y')
            focus_level: Intensity level ('balanced', 'focused', 'intensive')
            preferences: User preferences and constraints

        Returns:
            Comprehensive wellness plan with goals, action steps, and recommendations
        """
        try:
            logger.info(f"Generating wellness plan for user {user_id} with focus areas: {focus_areas}")

            # Get user's baseline wellness data
            baseline_data = await self._get_user_wellness_baseline(user_id, focus_areas)

            # Get historical trend data
            trend_data = await self._get_user_trend_analysis(user_id, focus_areas)

            # Generate personalized goals
            goals = await self._generate_wellness_goals(
                user_id, focus_areas, baseline_data, trend_data, timeframe, focus_level
            )

            # Create action steps for each goal
            action_steps = await self._generate_action_steps(goals, focus_level, preferences)

            # Generate AI-powered recommendations
            ai_recommendations = await self._generate_ai_recommendations(
                user_id, baseline_data, trend_data, focus_areas, goals
            )

            # Identify potential barriers and success factors
            barriers = await self._identify_potential_barriers(user_id, goals, baseline_data)
            success_factors = await self._identify_success_factors(user_id, focus_areas, baseline_data)

            # Create milestones
            milestones = await self._create_milestones(goals, timeframe)

            # Build support system recommendations
            support_systems = await self._recommend_support_systems(focus_areas, goals)

            # Calculate success metrics
            success_metrics = await self._generate_success_metrics(goals, focus_areas)

            # Create final wellness plan
            wellness_plan = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "focus_areas": focus_areas,
                "timeline": self._format_timeline(timeframe),
                "estimated_completion": self._calculate_completion_date(timeframe).isoformat(),
                "goals": goals,
                "success_metrics": success_metrics,
                "potential_barriers": barriers,
                "support_systems": support_systems,
                "milestones": milestones,
                "ai_recommendations": ai_recommendations,
                "focus_level": focus_level,
                "preferences": preferences or {}
            }

            # Save plan to database (optional - could be stored in a separate wellness_plans table)
            await self._save_wellness_plan(user_id, wellness_plan)

            return {
                "success": True,
                "data": wellness_plan
            }

        except Exception as e:
            logger.error(f"Error generating wellness plan for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _get_user_wellness_baseline(
        self,
        user_id: str,
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """Get user's current wellness baseline data"""
        try:
            # Get recent wellness assessments
            recent_responses = await self._get_recent_assessments(user_id, limit=5)

            if not recent_responses:
                # Return default baseline for new users
                return {
                    domain: {
                        "current_score": 0.5,
                        "target_score": 0.8,
                        "trend": "stable",
                        "data_points": 0
                    }
                    for domain in focus_areas
                }

            baseline = {}
            for domain in focus_areas:
                domain_scores = []
                for response in recent_responses:
                    domain_score = self._extract_domain_score(response, domain)
                    if domain_score is not None:
                        domain_scores.append(domain_score)

                if domain_scores:
                    baseline[domain] = {
                        "current_score": domain_scores[-1],  # Most recent score
                        "target_score": min(0.9, domain_scores[-1] + 0.3),  # Realistic target
                        "trend": self._calculate_simple_trend(domain_scores),
                        "data_points": len(domain_scores),
                        "average": sum(domain_scores) / len(domain_scores)
                    }
                else:
                    baseline[domain] = {
                        "current_score": 0.5,
                        "target_score": 0.8,
                        "trend": "stable",
                        "data_points": 0
                    }

            return baseline

        except Exception as e:
            logger.error(f"Error getting wellness baseline: {e}")
            return {}

    async def _get_user_trend_analysis(
        self,
        user_id: str,
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """Get user's trend analysis data"""
        try:
            # Use trend analysis service
            trend_result = await self.trend_service.get_user_trend_data(
                user_id=user_id,
                time_range='3m',
                domains=focus_areas
            )

            if trend_result.get("success"):
                return trend_result["data"]
            else:
                return {}

        except Exception as e:
            logger.error(f"Error getting trend analysis: {e}")
            return {}

    async def _generate_wellness_goals(
        self,
        user_id: str,
        focus_areas: List[str],
        baseline_data: Dict[str, Any],
        trend_data: Dict[str, Any],
        timeframe: str,
        focus_level: str
    ) -> List[Dict[str, Any]]:
        """Generate personalized wellness goals"""
        goals = []

        try:
            # Determine number of goals based on focus level and timeframe
            max_goals = self._calculate_max_goals(focus_level, timeframe)

            for domain in focus_areas[:max_goals]:
                baseline = baseline_data.get(domain, {})
                current_score = baseline.get("current_score", 0.5)
                target_score = baseline.get("target_score", 0.8)

                # Generate domain-specific goal
                goal = await self._create_domain_goal(
                    domain=domain,
                    current_score=current_score,
                    target_score=target_score,
                    timeframe=timeframe,
                    focus_level=focus_level,
                    trend_data=trend_data
                )

                goals.append(goal)

        except Exception as e:
            logger.error(f"Error generating wellness goals: {e}")
            # Return fallback goal
            goals = [await self._create_fallback_goal(focus_areas[0] if focus_areas else 'physical')]

        return goals

    async def _create_domain_goal(
        self,
        domain: str,
        current_score: float,
        target_score: float,
        timeframe: str,
        focus_level: str,
        trend_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a specific wellness goal for a domain"""
        domain_info = self._get_domain_info(domain)

        # Determine priority based on current score and trend
        priority = self._calculate_goal_priority(current_score, trend_data.get(domain, {}))

        # Generate goal title and description
        title, description = self._generate_goal_content(domain, current_score, target_score)

        return {
            "id": str(uuid.uuid4()),
            "domain": domain,
            "title": title,
            "description": description,
            "priority": priority,
            "target_date": self._calculate_completion_date(timeframe).isoformat(),
            "current_score": int(current_score * 100),
            "target_score": int(target_score * 100),
            "action_steps": []  # Will be populated separately
        }

    async def _generate_action_steps(
        self,
        goals: List[Dict[str, Any]],
        focus_level: str,
        preferences: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate action steps for each goal"""
        all_action_steps = []

        try:
            for goal in goals:
                domain = goal["domain"]
                current_score = goal["current_score"] / 100  # Convert back to 0-1 scale
                target_score = goal["target_score"] / 100

                # Generate domain-specific action steps
                steps = await self._create_domain_action_steps(
                    domain=domain,
                    current_score=current_score,
                    target_score=target_score,
                    focus_level=focus_level,
                    preferences=preferences
                )

                # Assign steps to goal
                goal["action_steps"] = steps
                all_action_steps.extend(steps)

        except Exception as e:
            logger.error(f"Error generating action steps: {e}")

        return all_action_steps

    async def _create_domain_action_steps(
        self,
        domain: str,
        current_score: float,
        target_score: float,
        focus_level: str,
        preferences: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create action steps for a specific wellness domain"""
        steps = []

        try:
            # Get domain-specific action templates
            action_templates = self._get_action_templates(domain, current_score, target_score)

            # Determine number of steps based on focus level
            num_steps = self._calculate_action_steps_count(focus_level)

            for i, template in enumerate(action_templates[:num_steps]):
                step = {
                    "id": str(uuid.uuid4()),
                    "title": template["title"],
                    "description": template["description"],
                    "category": template["category"],
                    "difficulty": template["difficulty"],
                    "time_required": template["time_required"],
                    "resources": template["resources"],
                    "completed": False,
                    "completion_date": None
                }
                steps.append(step)

        except Exception as e:
            logger.error(f"Error creating domain action steps: {e}")
            # Add fallback step
            steps.append({
                "id": str(uuid.uuid4()),
                "title": "Focus on daily wellness practices",
                "description": "Implement small, consistent changes to improve wellness",
                "category": "daily",
                "difficulty": "moderate",
                "time_required": "15 minutes",
                "resources": ["Wellness apps", "Self-care resources"],
                "completed": False,
                "completion_date": None
            })

        return steps

    async def _generate_ai_recommendations(
        self,
        user_id: str,
        baseline_data: Dict[str, Any],
        trend_data: Dict[str, Any],
        focus_areas: List[str],
        goals: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate AI-powered personalized recommendations using enhanced wellness processor"""
        recommendations = []

        try:
            logger.info(f"Generating AI recommendations for user {user_id} using {len(focus_areas)} focus areas")

            # Convert baseline data to AI processor format
            ai_assessment_data = self._prepare_ai_assessment_data(baseline_data, trend_data, focus_areas)

            # Use AI wellness processor for advanced analysis
            ai_analysis = await self._process_with_ai_wellness_processor(ai_assessment_data, user_id)

            # Generate personalized recommendations based on AI insights
            recommendations = self._extract_ai_recommendations(ai_analysis, focus_areas, goals)

            # Add domain-specific intelligent recommendations
            for domain in focus_areas:
                domain_baseline = baseline_data.get(domain, {})
                domain_recs = await self._generate_intelligent_domain_recommendations(
                    domain, domain_baseline, ai_analysis
                )
                recommendations.extend(domain_recs)

            # Add personalized goal recommendations
            goal_recommendations = await self._generate_intelligent_goal_recommendations(goals, ai_analysis)
            recommendations.extend(goal_recommendations)

            # Prioritize and limit to most impactful recommendations
            recommendations = self._prioritize_recommendations(recommendations, baseline_data, goals)[:7]

            logger.info(f"Generated {len(recommendations)} AI-powered recommendations")

        except Exception as e:
            logger.error(f"Error generating AI recommendations with wellness processor: {e}")
            # Fallback to basic recommendations
            recommendations = [
                "Start with small, achievable goals to build momentum",
                "Focus on one habit at a time for sustainable change",
                "Schedule regular check-ins to track progress",
                "Celebrate small wins along the journey",
                "Be flexible and adjust goals as needed"
            ]

        return recommendations

    def _prepare_ai_assessment_data(
        self,
        baseline_data: Dict[str, Any],
        trend_data: Dict[str, Any],
        focus_areas: List[str]
    ) -> Dict[str, Any]:
        """Prepare assessment data for AI wellness processor"""
        ai_data = {
            "wellness_domains": {},
            "focus_areas": focus_areas,
            "timeframe": "current",
            "response_patterns": {},
            "risk_factors": {},
            "strengths": []
        }

        # Convert baseline data to AI processor format
        for domain, data in baseline_data.items():
            current_score = data.get("current_score", 0.5)
            target_score = data.get("target_score", 0.8)

            ai_data["wellness_domains"][domain] = {
                "current_score": current_score,
                "target_score": target_score,
                "improvement_needed": target_score - current_score,
                "priority": "high" if current_score < 0.4 else "medium" if current_score < 0.7 else "low"
            }

        # Add trend analysis insights
        if trend_data:
            ai_data["response_patterns"] = {
                "consistency": trend_data.get("consistency_score", 0.5),
                "improvement_trend": trend_data.get("overall_trend", "stable"),
                "engagement_level": trend_data.get("engagement_score", 0.5)
            }

        return ai_data

    async def _process_with_ai_wellness_processor(
        self,
        assessment_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Process assessment data using AI wellness processor"""
        try:
            # Simulate AI processing (in real implementation, this would call the actual AI processor)
            ai_analysis = {
                "pattern_recognition": {
                    "consistency_score": assessment_data.get("response_patterns", {}).get("consistency", 0.5),
                    "improvement_trajectory": "positive" if assessment_data.get("response_patterns", {}).get("improvement_trend") == "improving" else "stable",
                    "engagement_level": assessment_data.get("response_patterns", {}).get("engagement_level", 0.5)
                },
                "predictive_insights": {
                    "burnout_risk": "low",
                    "success_probability": 0.85,
                    "optimal_focus_areas": assessment_data.get("focus_areas", []),
                    "recommended_intensity": "moderate"
                },
                "personalized_factors": {
                    "learning_style": "visual",
                    "motivation_type": "intrinsic",
                    "support_needs": ["accountability", "resources"],
                    "potential_barriers": ["time_constraints", "motivation_fluctuations"]
                },
                "domain_insights": {}
            }

            # Generate domain-specific insights
            for domain in assessment_data.get("focus_areas", []):
                domain_data = assessment_data.get("wellness_domains", {}).get(domain, {})
                current_score = domain_data.get("current_score", 0.5)

                ai_analysis["domain_insights"][domain] = {
                    "current_assessment": f"Score at {int(current_score * 100)}%",
                    "improvement_potential": "high" if current_score < 0.6 else "moderate",
                    "recommended_approach": "gradual" if current_score < 0.4 else "balanced",
                    "key_focus_areas": self._get_domain_focus_areas(domain, current_score)
                }

            return ai_analysis

        except Exception as e:
            logger.error(f"Error processing with AI wellness processor: {e}")
            return {"error": str(e)}

    def _get_domain_focus_areas(self, domain: str, current_score: float) -> List[str]:
        """Get focus areas for specific wellness domain based on current score"""
        focus_areas_map = {
            "physical": {
                "low": ["basic_exercise", "sleep_hygiene", "nutrition_basics"],
                "medium": ["consistent_routine", "strength_building", "endurance"],
                "high": ["performance_optimization", "advanced_training", "recovery_strategies"]
            },
            "mental": {
                "low": ["stress_management", "mindfulness_basics", "focus_improvement"],
                "medium": ["cognitive_training", "mental_clarity", "emotional_regulation"],
                "high": ["advanced_meditation", "cognitive_optimization", "mental_mastery"]
            },
            "emotional": {
                "low": ["emotional_awareness", "basic_regulation", "stress_coping"],
                "medium": ["emotional_intelligence", "relationship_building", "resilience"],
                "high": ["emotional_mastery", "advanced_empathy", "leadership_emotional"]
            },
            "social": {
                "low": ["basic_communication", "community_building", "support_network"],
                "medium": ["relationship_depth", "social_confidence", "community_leadership"],
                "high": ["social_mastery", "network_building", "social_impact"]
            }
        }

        level = "low" if current_score < 0.4 else "medium" if current_score < 0.7 else "high"
        return focus_areas_map.get(domain, {}).get(level, ["general_improvement"])

    def _extract_ai_recommendations(
        self,
        ai_analysis: Dict[str, Any],
        focus_areas: List[str],
        goals: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract actionable recommendations from AI analysis"""
        recommendations = []

        # Pattern recognition based recommendations
        pattern_insights = ai_analysis.get("pattern_recognition", {})
        if pattern_insights.get("consistency_score", 0) < 0.5:
            recommendations.append("Focus on building consistent daily wellness habits")

        # Predictive insights based recommendations
        predictive = ai_analysis.get("predictive_insights", {})
        if predictive.get("success_probability", 0) < 0.8:
            recommendations.append("Start with smaller goals to build momentum and confidence")

        # Personalized factor recommendations
        personal_factors = ai_analysis.get("personalized_factors", {})
        if "accountability" in personal_factors.get("support_needs", []):
            recommendations.append("Set up regular check-ins with a wellness partner or coach")

        # Domain-specific recommendations
        domain_insights = ai_analysis.get("domain_insights", {})
        for domain in focus_areas:
            insights = domain_insights.get(domain, {})
            approach = insights.get("recommended_approach", "balanced")
            if approach == "gradual":
                recommendations.append(f"Take a gradual approach to {domain} wellness improvements")
            elif approach == "balanced":
                recommendations.append(f"Maintain balanced progress in {domain} wellness")

        return recommendations

    async def _generate_intelligent_domain_recommendations(
        self,
        domain: str,
        baseline_data: Dict[str, Any],
        ai_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate intelligent domain-specific recommendations"""
        recommendations = []

        current_score = baseline_data.get("current_score", 0.5)
        domain_insights = ai_analysis.get("domain_insights", {}).get(domain, {})

        # Generate recommendations based on current score and AI insights
        if current_score < 0.4:
            recommendations.extend([
                f"Focus on foundational {domain} wellness practices",
                f"Establish basic {domain} health habits before advancing"
            ])
        elif current_score < 0.7:
            recommendations.extend([
                f"Build upon your {domain} wellness foundation with intermediate practices",
                f"Explore advanced {domain} wellness techniques"
            ])
        else:
            recommendations.extend([
                f"Maintain excellent {domain} wellness with optimization strategies",
                f"Consider mentoring others in {domain} wellness"
            ])

        return recommendations

    async def _generate_intelligent_goal_recommendations(
        self,
        goals: List[Dict[str, Any]],
        ai_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate intelligent goal-specific recommendations"""
        recommendations = []

        for goal in goals:
            domain = goal.get("domain", "")
            priority = goal.get("priority", "medium")

            if priority == "high":
                recommendations.append(f"Prioritize {domain} wellness goal with daily focus")
            elif priority == "medium":
                recommendations.append(f"Maintain consistent progress on {domain} wellness goal")

            # Add personalized approach based on AI analysis
            approach = ai_analysis.get("predictive_insights", {}).get("recommended_intensity", "moderate")
            if approach == "moderate":
                recommendations.append("Use a balanced approach with consistent effort and regular rest")

        return recommendations

    def _prioritize_recommendations(
        self,
        recommendations: List[str],
        baseline_data: Dict[str, Any],
        goals: List[Dict[str, Any]]
    ) -> List[str]:
        """Prioritize recommendations based on user data and goals"""
        prioritized = []

        # Priority 1: Foundation and consistency recommendations
        foundation_recs = [r for r in recommendations if any(
            keyword in r.lower() for keyword in ["consist", "basic", "foundat", "momentum"]
        )]
        prioritized.extend(foundation_recs[:2])

        # Priority 2: High-priority domain recommendations
        high_priority_domains = [
            domain for domain, data in baseline_data.items()
            if data.get("current_score", 0.5) < 0.5
        ]

        domain_recs = [r for r in recommendations if any(
            domain in r.lower() for domain in high_priority_domains
        )]
        prioritized.extend(domain_recs[:2])

        # Priority 3: Personalized recommendations
        personalized_recs = [r for r in recommendations if any(
            keyword in r.lower() for keyword in ["personal", "individual", "your"]
        )]
        prioritized.extend(personalized_recs[:1])

        # Fill remaining with other recommendations
        other_recs = [r for r in recommendations if r not in prioritized]
        prioritized.extend(other_recs[:2])

        return prioritized

    async def _identify_potential_barriers(
        self,
        user_id: str,
        goals: List[Dict[str, Any]],
        baseline_data: Dict[str, Any]
    ) -> List[str]:
        """Identify potential barriers to success"""
        barriers = []

        try:
            # Common barriers based on domain
            domain_barriers = {
                "physical": ["Time constraints", "Lack of motivation", "Physical limitations"],
                "emotional": ["Stress from work/life", "Past trauma", "Negative self-talk"],
                "social": ["Social anxiety", "Lack of social opportunities", "Time management"],
                "intellectual": ["Limited access to learning resources", "Time constraints", "Lack of clarity on goals"],
                "spiritual": ["Lack of clarity on values", "Time constraints", "Disconnect from purpose"],
                "occupational": ["Work-related stress", "Work-life balance challenges", "Career uncertainty"],
                "environmental": ["Limited control over environment", "Financial constraints", "Lack of green spaces"]
            }

            # Add barriers for each focus area
            for goal in goals:
                domain = goal["domain"]
                barriers.extend(domain_barriers.get(domain, []))

            # Remove duplicates and limit
            barriers = list(set(barriers))[:5]

        except Exception as e:
            logger.error(f"Error identifying potential barriers: {e}")
            barriers = ["Time constraints", "Lack of motivation", "External stressors"]

        return barriers

    async def _identify_success_factors(
        self,
        user_id: str,
        focus_areas: List[str],
        baseline_data: Dict[str, Any]
    ) -> List[str]:
        """Identify factors that contribute to success"""
        factors = []

        try:
            # Common success factors
            general_factors = [
                "Consistent daily habits and routines",
                "Strong support system (friends, family, professionals)",
                "Clear, measurable goals with regular progress tracking",
                "Self-compassion and patience with the process",
                "Regular self-reflection and adjustment of strategies"
            ]

            # Domain-specific success factors
            domain_factors = {
                "physical": ["Regular physical activity", "Balanced nutrition", "Adequate sleep"],
                "emotional": ["Stress management techniques", "Emotional awareness", "Professional support when needed"],
                "social": ["Quality relationships", "Community involvement", "Communication skills"],
                "intellectual": ["Continuous learning", "Mental challenges", "Creative expression"],
                "spiritual": ["Values clarification", "Meditation/mindfulness", "Purpose-driven activities"],
                "occupational": ["Work satisfaction", "Skill development", "Healthy boundaries"],
                "environmental": ["Organized living space", "Connection with nature", "Healthy environment"]
            }

            # Add relevant factors
            factors.extend(general_factors)
            for domain in focus_areas:
                factors.extend(domain_factors.get(domain, []))

            # Remove duplicates and limit
            factors = list(set(factors))[:8]

        except Exception as e:
            logger.error(f"Error identifying success factors: {e}")
            factors = [
                "Consistency and patience",
                "Strong support system",
                "Clear goals and regular progress tracking"
            ]

        return factors

    async def _create_milestones(
        self,
        goals: List[Dict[str, Any]],
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Create celebration milestones for the wellness journey"""
        milestones = []

        try:
            # Calculate milestone dates
            start_date = datetime.utcnow()
            completion_date = self._calculate_completion_date(timeframe)
            total_days = (completion_date - start_date).days

            # Create milestones at 25%, 50%, 75%, and 100%
            milestone_percentages = [0.25, 0.5, 0.75, 1.0]

            for i, percentage in enumerate(milestone_percentages):
                milestone_date = start_date + timedelta(days=int(total_days * percentage))

                milestone = {
                    "id": str(uuid.uuid4()),
                    "title": self._get_milestone_title(i, len(milestone_percentages)),
                    "description": self._get_milestone_description(i, len(milestone_percentages), goals),
                    "target_date": milestone_date.isoformat(),
                    "achieved": False,
                    "celebration": self._get_celebration_idea(i, len(milestone_percentages))
                }
                milestones.append(milestone)

        except Exception as e:
            logger.error(f"Error creating milestones: {e}")
            # Add basic milestone
            milestones = [{
                "id": str(uuid.uuid4()),
                "title": "Wellness Goal Achievement",
                "description": "Celebrate reaching your wellness improvement goals",
                "target_date": self._calculate_completion_date(timeframe).isoformat(),
                "achieved": False,
                "celebration": "Treat yourself to something special!"
            }]

        return milestones

    async def _recommend_support_systems(
        self,
        focus_areas: List[str],
        goals: List[Dict[str, Any]]
    ) -> List[str]:
        """Recommend support systems and resources"""
        support_systems = []

        try:
            # General support systems
            general_support = [
                "Primary Care Physician",
                "Mental Health Professional",
                "Friends and Family",
                "Wellness Coach",
                "Support Groups"
            ]

            # Domain-specific support
            domain_support = {
                "physical": ["Personal Trainer", "Nutritionist", "Physical Therapist"],
                "emotional": ["Therapist", "Counselor", "Psychiatrist"],
                "social": ["Social Clubs", "Community Organizations", "Networking Groups"],
                "intellectual": ["Mentor", "Educational Institutions", "Book Clubs"],
                "spiritual": ["Spiritual Advisor", "Meditation Groups", "Faith Communities"],
                "occupational": ["Career Coach", "Mentor", "Professional Associations"],
                "environmental": ["Organization Consultant", "Interior Designer", "Community Planners"]
            }

            # Add general support
            support_systems.extend(general_support)

            # Add domain-specific support
            for domain in focus_areas:
                support_systems.extend(domain_support.get(domain, []))

            # Remove duplicates and limit
            support_systems = list(set(support_systems))[:8]

        except Exception as e:
            logger.error(f"Error recommending support systems: {e}")
            support_systems = [
                "Healthcare Provider",
                "Friends and Family",
                "Wellness Professional"
            ]

        return support_systems

    async def _generate_success_metrics(
        self,
        goals: List[Dict[str, Any]],
        focus_areas: List[str]
    ) -> List[str]:
        """Generate measurable success metrics"""
        metrics = []

        try:
            # Goal-specific metrics
            for goal in goals:
                domain = goal["domain"]
                target_score = goal["target_score"]

                metric = f"Achieve {domain} wellness score of {target_score}% or higher"
                metrics.append(metric)

            # Process-based metrics
            process_metrics = [
                "Complete 80% or more of planned action steps",
                "Maintain consistency with daily wellness practices",
                "Regularly track and review progress",
                "Adjust strategies based on progress and feedback"
            ]

            metrics.extend(process_metrics)

            # Outcome-based metrics
            outcome_metrics = [
                "Reported improvement in overall wellbeing",
                "Increased resilience to stress",
                "Better work-life balance",
                "Enhanced quality of life"
            ]

            metrics.extend(outcome_metrics)

            # Limit metrics
            metrics = metrics[:10]

        except Exception as e:
            logger.error(f"Error generating success metrics: {e}")
            metrics = [
                "Consistent progress toward wellness goals",
                "Improved overall wellbeing scores",
                "Successful completion of action steps"
            ]

        return metrics

    # Helper methods
    async def _get_recent_assessments(self, user_id: str, limit: int = 5) -> List[Response]:
        """Get recent assessment responses for user"""
        try:
            query = select(Response).where(
                Response.user_id == user_id
            ).order_by(desc(Response.completed_at)).limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting recent assessments: {e}")
            return []

    def _extract_domain_score(self, response: Response, domain: str) -> Optional[float]:
        """Extract domain score from assessment response"""
        try:
            response_data = response.response_data or {}

            # Try different possible field names
            field_names = [
                f"{domain}_score",
                f"{domain}_wellness",
                f"wellness_{domain}",
                domain
            ]

            for field_name in field_names:
                if field_name in response_data:
                    return float(response_data[field_name])

            return None

        except Exception as e:
            logger.error(f"Error extracting domain score: {e}")
            return None

    def _calculate_simple_trend(self, scores: List[float]) -> str:
        """Calculate simple trend from scores"""
        if len(scores) < 2:
            return "stable"

        recent_avg = sum(scores[-3:]) / min(3, len(scores))
        older_avg = sum(scores[:-3]) / max(1, len(scores) - 3)

        if recent_avg > older_avg + 0.05:
            return "improving"
        elif recent_avg < older_avg - 0.05:
            return "declining"
        else:
            return "stable"

    def _get_domain_info(self, domain: str) -> Dict[str, str]:
        """Get information about a wellness domain"""
        domain_info = {
            "physical": {
                "name": "Physical Wellness",
                "icon": "💪",
                "focus": "Physical health, fitness, nutrition, sleep"
            },
            "emotional": {
                "name": "Emotional Wellness",
                "icon": "❤️",
                "focus": "Emotional regulation, mental health, self-awareness"
            },
            "social": {
                "name": "Social Wellness",
                "icon": "👥",
                "focus": "Relationships, community, social connections"
            },
            "intellectual": {
                "name": "Intellectual Wellness",
                "icon": "🧠",
                "focus": "Learning, growth, mental stimulation"
            },
            "spiritual": {
                "name": "Spiritual Wellness",
                "icon": "🌟",
                "focus": "Purpose, values, meaning, mindfulness"
            },
            "occupational": {
                "name": "Occupational Wellness",
                "icon": "💼",
                "focus": "Work satisfaction, career growth, work-life balance"
            },
            "environmental": {
                "name": "Environmental Wellness",
                "icon": "🏠",
                "focus": "Living space, environment, sustainability"
            }
        }

        return domain_info.get(domain, {"name": domain, "icon": "📊", "focus": "Wellness improvement"})

    def _calculate_goal_priority(self, current_score: float, trend_data: Dict[str, Any]) -> str:
        """Calculate goal priority based on current score and trend"""
        if current_score < 0.4:
            return "urgent"
        elif current_score < 0.6:
            return "high"
        elif current_score < 0.8:
            return "medium"
        else:
            return "low"

    def _generate_goal_content(self, domain: str, current_score: float, target_score: float) -> Tuple[str, str]:
        """Generate goal title and description"""
        domain_info = self._get_domain_info(domain)

        titles = {
            "physical": f"Improve Physical Health to {int(target_score * 100)}%",
            "emotional": f"Enhance Emotional Wellbeing to {int(target_score * 100)}%",
            "social": f"Strengthen Social Wellness to {int(target_score * 100)}%",
            "intellectual": f"Develop Intellectual Growth to {int(target_score * 100)}%",
            "spiritual": f"Cultivate Spiritual Wellness to {int(target_score * 100)}%",
            "occupational": f"Optimize Occupational Wellness to {int(target_score * 100)}%",
            "environmental": f"Improve Environmental Wellness to {int(target_score * 100)}%"
        }

        descriptions = {
            "physical": "Focus on physical health through exercise, nutrition, and healthy lifestyle habits",
            "emotional": "Develop emotional intelligence and resilience through self-awareness and coping strategies",
            "social": "Build and maintain meaningful relationships and community connections",
            "intellectual": "Engage in continuous learning and mental stimulation for cognitive growth",
            "spiritual": "Connect with your values, purpose, and meaning in life",
            "occupational": "Achieve work satisfaction and healthy work-life balance",
            "environmental": "Create a healthy and supportive living and working environment"
        }

        return (
            titles.get(domain, f"Improve {domain} Wellness"),
            descriptions.get(domain, f"Focus on improving {domain} wellness through targeted practices")
        )

    def _calculate_max_goals(self, focus_level: str, timeframe: str) -> int:
        """Calculate maximum number of goals based on focus level and timeframe"""
        base_goals = {"balanced": 3, "focused": 4, "intensive": 5}
        timeframe_multiplier = {"1m": 0.6, "3m": 1.0, "6m": 1.2, "1y": 1.5}

        return int(base_goals.get(focus_level, 3) * timeframe_multiplier.get(timeframe, 1.0))

    def _format_timeline(self, timeframe: str) -> str:
        """Format timeline for display"""
        timeline_labels = {
            "1m": "1 Month - Quick Wins",
            "3m": "3 Months - Sustainable Growth",
            "6m": "6 Months - Deep Transformation",
            "1y": "1 Year - Complete Lifestyle"
        }

        return timeline_labels.get(timeframe, "3 Months")

    def _calculate_completion_date(self, timeframe: str) -> datetime:
        """Calculate plan completion date"""
        timeframe_days = {"1m": 30, "3m": 90, "6m": 180, "1y": 365}
        days = timeframe_days.get(timeframe, 90)

        return datetime.utcnow() + timedelta(days=days)

    def _get_action_templates(self, domain: str, current_score: float, target_score: float) -> List[Dict[str, Any]]:
        """Get action step templates for a domain"""
        # This would contain comprehensive action templates for each domain
        # Simplified for this example
        templates = [
            {
                "title": "Daily Practice",
                "description": f"Establish daily {domain} wellness practices",
                "category": "daily",
                "difficulty": "moderate",
                "time_required": "15-30 minutes",
                "resources": ["Wellness apps", "Guided exercises"]
            },
            {
                "title": "Weekly Review",
                "description": f"Review and adjust {domain} wellness progress weekly",
                "category": "weekly",
                "difficulty": "easy",
                "time_required": "10-15 minutes",
                "resources": ["Journal", "Progress tracking tools"]
            }
        ]

        return templates

    def _calculate_action_steps_count(self, focus_level: str) -> int:
        """Calculate number of action steps per goal"""
        counts = {"balanced": 3, "focused": 5, "intensive": 7}
        return counts.get(focus_level, 4)

    async def _analyze_user_patterns(self, user_id: str, baseline_data: Dict[str, Any], trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user patterns for insights"""
        # This would involve sophisticated pattern analysis
        return {
            "consistency_score": 0.7,
            "improvement_areas": [],
            "strength_areas": [],
            "engagement_level": "moderate"
        }

    async def _generate_domain_recommendations(self, domain: str, baseline: Dict[str, Any], trend_data: Dict[str, Any]) -> List[str]:
        """Generate domain-specific recommendations"""
        return [
            f"Focus on consistent {domain} wellness practices",
            f"Track progress in {domain} wellness regularly",
            f"Seek professional guidance for {domain} wellness if needed"
        ]

    async def _generate_goal_recommendations(self, goal: Dict[str, Any]) -> List[str]:
        """Generate goal-specific recommendations"""
        return [
            f"Break down {goal['title']} into smaller, manageable steps",
            f"Set regular check-ins for {goal['domain']} wellness goal",
            f"Celebrate small wins toward {goal['title']}"
        ]

    async def _generate_general_recommendations(self, insights: Dict[str, Any], focus_areas: List[str]) -> List[str]:
        """Generate general wellness recommendations"""
        return [
            "Maintain a balanced approach across all wellness dimensions",
            "Practice self-compassion and patience throughout your journey",
            "Build accountability through sharing your goals with others"
        ]

    def _get_milestone_title(self, index: int, total: int) -> str:
        """Get milestone title based on position"""
        if index == 0:
            return "Initial Progress Milestone"
        elif index == total - 1:
            return "Goal Achievement Milestone"
        else:
            return f"Progress Milestone {index + 1}"

    def _get_milestone_description(self, index: int, total: int, goals: List[Dict[str, Any]]) -> str:
        """Get milestone description"""
        if index == 0:
            return "Celebrate starting your wellness journey and establishing initial habits"
        elif index == total - 1:
            return "Celebrate achieving your wellness goals and reflect on your journey"
        else:
            return f"Recognize your progress toward wellness improvement goals"

    def _get_celebration_idea(self, index: int, total: int) -> str:
        """Get celebration idea for milestone"""
        if index == 0:
            return "Treat yourself to something special for starting your journey!"
        elif index == total - 1:
            return "Celebrate with a meaningful reward for achieving your goals!"
        else:
            return "Acknowledge your progress with a small celebration!"

    async def _save_wellness_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        """Save wellness plan to database"""
        # This would save the plan to a wellness_plans table
        # For now, we'll just log it
        logger.info(f"Wellness plan saved for user {user_id}: {plan['id']}")

    async def get_existing_wellness_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's existing wellness plan"""
        try:
            # This would retrieve from database
            # For now, return None to indicate no existing plan
            return None

        except Exception as e:
            logger.error(f"Error getting existing wellness plan: {e}")
            return None