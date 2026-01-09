# app/services/onboarding_service.py
# Core business logic for value-first onboarding experience
import asyncio
from typing import Any
import uuid

from app.schemas.onboarding import (
    ActionItem,
    DetailedInsight,
    ImplementationRoadmap,
    OnboardingStatus,
    PredictedOutcome,
    QuickInsights,
    Recommendation,
    TeamChallenge,
    TeamProfile,
    UserRole,
    ValueMetrics,
)
from app.services.analytics_service import AnalyticsService
from app.services.nlp_service import NLPService


class OnboardingService:
    """
    Service for generating instant behavioral insights and managing
    value-first onboarding experience.
    """

    def __init__(self):
        self.nlp_service = NLPService()
        self.analytics_service = AnalyticsService()

        # Pre-defined insights database for instant responses
        self.insight_templates = self._load_insight_templates()

    def _load_insight_templates(self) -> dict[str, dict[str, Any]]:
        """Load pre-defined insight templates for instant responses."""
        return {
            "manager": {
                "communication": {
                    "primary_benefit": "Reduce team misunderstandings by 60% and save 8+ hours of productivity monthly",
                    "risk_areas": [
                        "Information silos",
                        "Misaligned expectations",
                        "Delayed feedback",
                    ],
                    "strengths": ["Natural leadership", "Goal-oriented", "Decision-making"],
                    "opportunities": [
                        "Improved meeting efficiency",
                        "Better documentation",
                        "Structured communication",
                    ],
                    "conversion_probability": 0.85,
                    "estimated_time_to_value": "2 weeks",
                },
                "productivity": {
                    "primary_benefit": "Increase team output by 25% through better role alignment and motivation",
                    "risk_areas": ["Role misalignment", "Low engagement", "Inefficient processes"],
                    "strengths": [
                        "Process optimization",
                        "Resource management",
                        "Performance tracking",
                    ],
                    "opportunities": [
                        "Automation opportunities",
                        "Skill development",
                        "Process redesign",
                    ],
                    "conversion_probability": 0.82,
                    "estimated_time_to_value": "1 month",
                },
                "turnover": {
                    "primary_benefit": "Reduce voluntary turnover by 40% and save $200K+ in replacement costs",
                    "risk_areas": ["Burnout risk", "Career stagnation", "Compensation gaps"],
                    "strengths": ["Team development", "Talent retention", "Career coaching"],
                    "opportunities": [
                        "Career pathing",
                        "Recognition programs",
                        "Work-life balance",
                    ],
                    "conversion_probability": 0.78,
                    "estimated_time_to_value": "3 months",
                },
                "collaboration": {
                    "primary_benefit": "Improve project completion speed by 30% through better team dynamics",
                    "risk_areas": ["Poor coordination", "Duplicate work", "Knowledge gaps"],
                    "strengths": [
                        "Team building",
                        "Cross-functional collaboration",
                        "Knowledge sharing",
                    ],
                    "opportunities": ["Collaboration tools", "Team restructuring", "Skill sharing"],
                    "conversion_probability": 0.80,
                    "estimated_time_to_value": "2 weeks",
                },
                "conflict": {
                    "primary_benefit": "Reduce meeting conflicts by 60% and improve decision quality",
                    "risk_areas": [
                        "Personality clashes",
                        "Communication style differences",
                        "Decision paralysis",
                    ],
                    "strengths": ["Conflict resolution", "Mediation", "Consensus building"],
                    "opportunities": [
                        "Communication training",
                        "Decision frameworks",
                        "Team agreements",
                    ],
                    "conversion_probability": 0.75,
                    "estimated_time_to_value": "1-2 weeks",
                },
            },
            "hr": {
                "communication": {
                    "primary_benefit": "Break down organizational silos and improve cross-department knowledge sharing",
                    "risk_areas": [
                        "Department silos",
                        "Information hoarding",
                        "Poor change management",
                    ],
                    "strengths": [
                        "Organizational design",
                        "Communication strategy",
                        "Change management",
                    ],
                    "opportunities": [
                        "Organization redesign",
                        "Communication platforms",
                        "Knowledge management",
                    ],
                    "conversion_probability": 0.88,
                    "estimated_time_to_value": "1 quarter",
                },
                "productivity": {
                    "primary_benefit": "Standardize high productivity across teams and increase organizational output by 15%",
                    "risk_areas": ["Inconsistent processes", "Skill gaps", "Low motivation"],
                    "strengths": [
                        "Performance management",
                        "Training programs",
                        "Process standardization",
                    ],
                    "opportunities": [
                        "Performance systems",
                        "Learning platforms",
                        "Productivity tools",
                    ],
                    "conversion_probability": 0.85,
                    "estimated_time_to_value": "3-6 months",
                },
                "turnover": {
                    "primary_benefit": "Identify turnover risk 6 months early and reduce replacement costs by $500K+",
                    "risk_areas": ["High performers at risk", "Toxic teams", "Poor culture fit"],
                    "strengths": [
                        "Retention strategies",
                        "Culture assessment",
                        "Succession planning",
                    ],
                    "opportunities": [
                        "Retention programs",
                        "Culture initiatives",
                        "Leadership development",
                    ],
                    "conversion_probability": 0.90,
                    "estimated_time_to_value": "6 months",
                },
            },
            "lead": {
                "communication": {
                    "primary_benefit": "Reduce team misunderstandings by 40% and improve meeting efficiency",
                    "risk_areas": [
                        "Poor information flow",
                        "Unclear expectations",
                        "Inadequate feedback",
                    ],
                    "strengths": ["Direct communication", "Clear expectations", "Regular feedback"],
                    "opportunities": [
                        "Meeting optimization",
                        "Communication tools",
                        "Feedback systems",
                    ],
                    "conversion_probability": 0.83,
                    "estimated_time_to_value": "2 weeks",
                },
                "productivity": {
                    "primary_benefit": "Improve sprint completion rate by 20% through better task allocation",
                    "risk_areas": ["Skill mismatches", "Poor estimation", "Blocking issues"],
                    "strengths": ["Task planning", "Skill assessment", "Problem solving"],
                    "opportunities": ["Skill mapping", "Process improvement", "Automation"],
                    "conversion_probability": 0.80,
                    "estimated_time_to_value": "1 sprint",
                },
            },
            "member": {
                "communication": {
                    "primary_benefit": "Improve personal communication effectiveness by 25% and reduce misunderstandings",
                    "risk_areas": [
                        "Communication style mismatches",
                        "Poor articulation",
                        "Listening gaps",
                    ],
                    "strengths": ["Adaptability", "Learning ability", "Team collaboration"],
                    "opportunities": [
                        "Communication training",
                        "Personal development",
                        "Mentoring",
                    ],
                    "conversion_probability": 0.75,
                    "estimated_time_to_value": "1 week",
                },
                "productivity": {
                    "primary_benefit": "Increase personal productivity by 30% through work style optimization",
                    "risk_areas": ["Distractions", "Poor time management", "Skill gaps"],
                    "strengths": ["Focus", "Self-motivation", "Continuous learning"],
                    "opportunities": ["Productivity tools", "Time management", "Skill development"],
                    "conversion_probability": 0.78,
                    "estimated_time_to_value": "Immediate",
                },
            },
            "executive": {
                "communication": {
                    "primary_benefit": "Accelerate strategic initiatives by 30% through improved executive-team alignment",
                    "risk_areas": [
                        "Strategic misalignment",
                        "Poor communication cascade",
                        "Resistance to change",
                    ],
                    "strengths": [
                        "Strategic vision",
                        "Leadership communication",
                        "Decision making",
                    ],
                    "opportunities": [
                        "Communication strategy",
                        "Change management",
                        "Leadership alignment",
                    ],
                    "conversion_probability": 0.92,
                    "estimated_time_to_value": "1 quarter",
                },
                "productivity": {
                    "primary_benefit": "Unlock $2-3M productivity improvement through organizational behavior optimization",
                    "risk_areas": [
                        "Organizational inefficiency",
                        "Poor resource allocation",
                        "Low innovation",
                    ],
                    "strengths": [
                        "Strategic thinking",
                        "Resource optimization",
                        "Innovation leadership",
                    ],
                    "opportunities": [
                        "Organizational redesign",
                        "Innovation programs",
                        "Digital transformation",
                    ],
                    "conversion_probability": 0.88,
                    "estimated_time_to_value": "12 months",
                },
            },
        }

    async def generate_quick_insights(
        self,
        role: UserRole,
        challenge: TeamChallenge,
        team_size: str | None = None,
        industry: str | None = None,
        user_id: str | None = None,
    ) -> QuickInsights:
        """
        Generate instant insights based on role and challenge.
        This is the core of the value-first approach - returns actionable insights in <100ms.
        """

        # Get base template for this role/challenge combination
        role_str = role.value
        challenge_str = challenge.value

        # Fallback to manager data if role not found
        base_template = self.insight_templates.get(role_str, {}).get(
            challenge_str, self.insight_templates.get("manager", {}).get("communication", {})
        )

        # Generate personalized recommendations
        recommendations = await self._generate_recommendations(role, challenge, team_size, industry)

        # Create insights object
        insights = QuickInsights(
            primary_benefit=base_template.get("primary_benefit", ""),
            risk_areas=base_template.get("risk_areas", []),
            strengths=base_template.get("strengths", []),
            opportunities=base_template.get("opportunities", []),
            recommendations=recommendations,
            conversion_probability=base_template.get("conversion_probability", 0.75),
            estimated_time_to_value=base_template.get("estimated_time_to_value", "2 weeks"),
        )

        # Store for potential follow-up (async, non-blocking)
        if user_id:
            asyncio.create_task(self._store_insights_for_user(user_id, insights))

        return insights

    async def _generate_recommendations(
        self, role: UserRole, challenge: TeamChallenge, team_size: str | None, industry: str | None
    ) -> list[Recommendation]:
        """Generate personalized recommendations based on role and challenge."""

        recommendations = []

        # Role-specific recommendations
        if role == UserRole.MANAGER:
            if challenge == TeamChallenge.COMMUNICATION:
                recommendations.extend(
                    [
                        Recommendation(
                            title="Implement daily standups with structured updates",
                            description="15-minute meetings with clear agenda and action items",
                            priority="High",
                            effort="Low",
                            expected_outcome="Reduce misunderstandings by 40% in 2 weeks",
                        ),
                        Recommendation(
                            title="Create team communication charter",
                            description="Define communication norms, channels, and response times",
                            priority="Medium",
                            effort="Medium",
                            expected_outcome="Improve information flow by 60%",
                        ),
                    ]
                )
            elif challenge == TeamChallenge.PRODUCTIVITY:
                recommendations.extend(
                    [
                        Recommendation(
                            title="Conduct skill-role alignment audit",
                            description="Match team members' strengths with current responsibilities",
                            priority="High",
                            effort="Medium",
                            expected_outcome="Increase output by 20% in 1 month",
                        )
                    ]
                )

        elif role == UserRole.HR:
            if challenge == TeamChallenge.TURNOVER:
                recommendations.extend(
                    [
                        Recommendation(
                            title="Implement stay interview program",
                            description="Regular conversations with high-performers about job satisfaction",
                            priority="High",
                            effort="Medium",
                            expected_outcome="Reduce turnover risk by 35%",
                        )
                    ]
                )

        # Add team size adjustments
        if team_size and "20+" in team_size:
            recommendations.append(
                Recommendation(
                    title="Establish sub-team leads",
                    description="Create smaller communication units within large teams",
                    priority="Medium",
                    effort="Medium",
                    expected_outcome="Improve coordination by 45%",
                )
            )

        # Industry-specific adjustments
        if industry and "tech" in industry.lower():
            recommendations.append(
                Recommendation(
                    title="Implement async communication protocols",
                    description="Optimize for distributed teams across time zones",
                    priority="High",
                    effort="Low",
                    expected_outcome="Reduce meeting load by 30%",
                )
            )

        return recommendations[:3]  # Limit to top 3 for quick assessment

    async def generate_detailed_team_insights(
        self,
        user_id: str,
        team_id: str | None,
        assessment_data: dict[str, Any] | None,
        team_composition: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Generate deeper insights for registered users."""

        # This would integrate with actual assessment data
        # For now, return enhanced insights

        team_profile = TeamProfile(
            team_size=len(team_composition) if team_composition else 5,
            avg_experience=5.2,
            personality_distribution={
                "analytical": 0.3,
                "creative": 0.2,
                "social": 0.3,
                "practical": 0.2,
            },
            communication_style="collaborative",
            work_preference="hybrid",
            current_performance=0.72,
            potential_performance=0.88,
        )

        detailed_insights = [
            DetailedInsight(
                category="communication",
                title="Communication style diversity creates both opportunities and challenges",
                description="Your team shows complementary communication styles that can enhance problem-solving when properly managed.",
                evidence=[
                    "Assessment results show varied communication preferences",
                    "Meeting feedback indicates some members feel unheard",
                ],
                impact_score=0.75,
                urgency="Medium",
            )
        ]

        action_items = [
            ActionItem(
                title="Facilitate communication style workshop",
                description="Help team understand and appreciate different communication approaches",
                responsible="Team Lead",
                timeline="2 weeks",
                resources=["Communication assessment tool", "Training materials"],
                success_metrics=["Improved meeting satisfaction", "Reduced misunderstandings"],
                priority_score=0.85,
            )
        ]

        predicted_outcomes = [
            PredictedOutcome(
                metric="Team Productivity",
                current_value=0.72,
                predicted_value=0.85,
                confidence_interval=[0.80, 0.90],
                timeframe="3 months",
            )
        ]

        implementation_roadmap = [
            ImplementationRoadmap(
                phase="Foundation",
                duration="2 weeks",
                activities=[
                    "Complete team assessments",
                    "Hold communication workshop",
                    "Establish team agreements",
                ],
                dependencies=["Team participation", "Management buy-in"],
                expected_outcomes=["Improved team awareness", "Reduced friction"],
            )
        ]

        return {
            "team_profile": team_profile,
            "detailed_insights": detailed_insights,
            "action_items": action_items,
            "predicted_outcomes": predicted_outcomes,
            "implementation_roadmap": implementation_roadmap,
        }

    async def get_onboarding_status(self, user_id: str) -> OnboardingStatus:
        """Get user's onboarding progress and recommended actions."""

        # Check user's current state
        completed_steps = []
        current_step = "welcome"

        # This would check actual database state
        # For now, return basic status

        return OnboardingStatus(
            is_authenticated=True,
            onboarding_complete=False,
            current_step=current_step,
            completed_steps=completed_steps,
            recommended_actions=[
                "Complete team setup to unlock insights",
                "Invite team members for comprehensive analysis",
                "Take full personality assessment",
            ],
            progress_percentage=0.25,
            estimated_remaining_time="5 minutes",
        )

    async def process_setup_step(
        self, user_id: str, step: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process individual setup wizard steps."""

        # Handle different setup steps
        if step == "team_creation":
            # Process team creation
            team_id = str(uuid.uuid4())
            return {
                "success": True,
                "step": step,
                "team_id": team_id,
                "next_step": "member_invitation",
            }

        if step == "quick_assessment":
            # Process quick assessment
            return {"success": True, "step": step, "next_step": "first_insights"}

        return {"success": True, "step": step, "next_step": "dashboard"}

    async def calculate_value_metrics(self, user_id: str) -> ValueMetrics:
        """Calculate real-time value metrics for user's team."""

        # This would pull actual team data
        # For now, return calculated estimates

        return ValueMetrics(
            productivity_improvement=0.23,
            communication_efficiency=0.45,
            conflict_reduction=0.60,
            turnover_risk_reduction=0.35,
            team_satisfaction_score=0.78,
            roi_estimate=3.2,
            time_to_value="6 weeks",
            monthly_value_created=12500.0,
        )

    async def _store_insights_for_user(self, user_id: str, insights: QuickInsights) -> None:
        """Store generated insights for user (async, non-blocking)."""
        try:
            # Store insights for follow-up and personalization
            pass
        except Exception as e:
            # Don't fail the main request for storage issues
            print(f"Failed to store insights: {e}")
