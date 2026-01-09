"""
Succession Planning Service

Advanced leadership pipeline development and succession planning system for organizations.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.services.skill_gap_analysis import LearningRecommendation, SkillGapAnalyzer

logger = logging.getLogger(__name__)


class ReadinessLevel(Enum):
    READY_NOW = "ready_now"  # Can step into role immediately
    READY_1_2_YEARS = "ready_1_2_years"  # Ready within 1-2 years with development
    READY_3_5_YEARS = "ready_3_5_years"  # Ready within 3-5 years with significant development
    POTENTIAL = "potential"  # Has potential but needs substantial development
    NOT_READY = "not_ready"  # Not currently viable for succession


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DevelopmentCategory(Enum):
    LEADERSHIP = "leadership"
    STRATEGIC_THINKING = "strategic_thinking"
    FINANCIAL_ACUMEN = "financial_acumen"
    CHANGE_MANAGEMENT = "change_management"
    STAKEHOLDER_MANAGEMENT = "stakeholder_management"
    OPERATIONAL_EXCELLENCE = "operational_excellence"
    INNOVATION = "innovation"


@dataclass
class RoleProfile:
    """Comprehensive profile for a leadership role"""

    role_id: str
    role_name: str
    level: str  # executive, senior_management, middle_management, team_lead
    department: str
    critical_functions: list[str]
    required_competencies: dict[str, float]  # competency -> required level (0-100)
    experience_requirements: dict[str, int]  # experience type -> years required
    leadership_style_requirements: dict[str, float]  # style -> preference weight
    risk_tolerances: dict[str, float]  # risk factors -> acceptable levels


@dataclass
class CandidateProfile:
    """Comprehensive candidate assessment for succession"""

    user_id: str
    current_role: str
    career_aspirations: list[str]
    readiness_level: ReadinessLevel
    readiness_score: float  # 0-100
    leadership_potential: float  # 0-100
    mobility_score: float  # 0-100
    risk_score: float  # 0-100 (lower is better)
    development_needs: list[dict[str, Any]]
    strengths: list[str]
    development_areas: list[str]
    promotion_timeline: int  # months until ready
    retention_risk: float  # 0-100 (higher is riskier)


@dataclass
class SuccessionCandidate:
    """Succession planning candidate match"""

    candidate: CandidateProfile
    target_role: RoleProfile
    match_score: float  # 0-100
    gap_analysis: dict[str, float]
    development_plan: list[LearningRecommendation]
    risk_assessment: dict[str, Any]
    financial_impact: dict[str, float]
    success_probability: float


@dataclass
class LeadershipPipeline:
    """Leadership pipeline analysis for organization"""

    pipeline_level: str
    total_positions: int
    ready_candidates: int
    gap_percentage: float
    bench_strength: float  # 0-100
    diversity_metrics: dict[str, Any]
    risk_level: RiskLevel
    development_recommendations: list[str]


@dataclass
class SuccessionScenario:
    """What-if scenario for succession planning"""

    scenario_name: str
    departure_roles: list[str]
    timeline_months: int
    business_impact: dict[str, float]
    readiness_status: str
    required_actions: list[str]
    financial_risk: float
    operational_risk: float


class SuccessionPlanner:
    """Advanced succession planning and leadership pipeline analysis"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.skill_analyzer = SkillGapAnalyzer(db_session)
        self.role_profiles = self._load_role_profiles()
        self.succession_history = self._load_succession_history()
        self.industry_benchmarks = self._load_industry_benchmarks()

    def _load_role_profiles(self) -> dict[str, RoleProfile]:
        """Load comprehensive role profiles for succession planning"""
        # In production, this would come from a competency framework database
        return {
            "ceo": RoleProfile(
                role_id="ceo",
                role_name="Chief Executive Officer",
                level="executive",
                department="executive",
                critical_functions=[
                    "strategic_vision",
                    "stakeholder_management",
                    "financial_oversight",
                    "organizational_leadership",
                    "public_relations",
                    "board_relations",
                ],
                required_competencies={
                    "strategic_thinking": 95,
                    "leadership": 98,
                    "financial_acumen": 90,
                    "change_management": 92,
                    "communication": 95,
                    "decision_making": 96,
                    "innovation": 85,
                    "global_perspective": 88,
                },
                experience_requirements={
                    "executive_leadership": 10,
                    "p_and_l_management": 8,
                    "board_experience": 3,
                    "industry_experience": 15,
                },
                leadership_style_requirements={
                    "transformational": 0.8,
                    "visionary": 0.9,
                    "collaborative": 0.6,
                    "decisive": 0.7,
                },
                risk_tolerances={
                    "strategic_risk": 0.7,
                    "financial_risk": 0.5,
                    "operational_risk": 0.3,
                    "reputation_risk": 0.4,
                },
            ),
            "cto": RoleProfile(
                role_id="cto",
                role_name="Chief Technology Officer",
                level="executive",
                department="technology",
                critical_functions=[
                    "technology_strategy",
                    "innovation_management",
                    "team_leadership",
                    "technical_oversight",
                    "digital_transformation",
                    "cybersecurity",
                ],
                required_competencies={
                    "technical_leadership": 95,
                    "strategic_thinking": 88,
                    "innovation": 92,
                    "change_management": 85,
                    "financial_acumen": 75,
                    "communication": 85,
                    "project_management": 90,
                    "emerging_tech": 93,
                },
                experience_requirements={
                    "technology_leadership": 12,
                    "team_management": 10,
                    "budget_management": 8,
                    "digital_transformation": 5,
                },
                leadership_style_requirements={
                    "transformational": 0.7,
                    "innovative": 0.9,
                    "analytical": 0.8,
                    "collaborative": 0.6,
                },
                risk_tolerances={
                    "technology_risk": 0.6,
                    "security_risk": 0.4,
                    "innovation_risk": 0.8,
                    "operational_risk": 0.5,
                },
            ),
            "director_engineering": RoleProfile(
                role_id="director_engineering",
                role_name="Director of Engineering",
                level="senior_management",
                department="technology",
                critical_functions=[
                    "engineering_leadership",
                    "technical_architecture",
                    "team_development",
                    "project_delivery",
                    "process_improvement",
                    "talent_management",
                ],
                required_competencies={
                    "technical_leadership": 90,
                    "people_management": 88,
                    "project_management": 92,
                    "strategic_thinking": 80,
                    "communication": 85,
                    "problem_solving": 88,
                    "process_improvement": 85,
                },
                experience_requirements={
                    "engineering_management": 8,
                    "team_leadership": 6,
                    "project_management": 10,
                    "technology_stack": 8,
                },
                leadership_style_requirements={
                    "servant_leadership": 0.8,
                    "collaborative": 0.7,
                    "analytical": 0.7,
                    "results_oriented": 0.8,
                },
                risk_tolerances={
                    "technical_risk": 0.5,
                    "delivery_risk": 0.4,
                    "people_risk": 0.3,
                    "quality_risk": 0.3,
                },
            ),
            "senior_manager_product": RoleProfile(
                role_id="senior_manager_product",
                role_name="Senior Product Manager",
                level="middle_management",
                department="product",
                critical_functions=[
                    "product_strategy",
                    "roadmap_planning",
                    "stakeholder_alignment",
                    "user_research",
                    "market_analysis",
                    "go_to_market",
                ],
                required_competencies={
                    "product_strategy": 88,
                    "analytical_thinking": 85,
                    "communication": 90,
                    "stakeholder_management": 87,
                    "market_research": 82,
                    "project_management": 83,
                    "data_analysis": 80,
                },
                experience_requirements={
                    "product_management": 6,
                    "team_leadership": 3,
                    "cross_functional": 4,
                    "industry_knowledge": 5,
                },
                leadership_style_requirements={
                    "collaborative": 0.8,
                    "analytical": 0.7,
                    "customer_focused": 0.9,
                    "strategic": 0.6,
                },
                risk_tolerances={
                    "market_risk": 0.6,
                    "technology_risk": 0.4,
                    "timeline_risk": 0.5,
                    "resource_risk": 0.4,
                },
            ),
        }

    def _load_succession_history(self) -> dict[str, Any]:
        """Load historical succession data for learning"""
        return {
            "promotion_success_rates": {
                "ceo": 0.75,
                "cto": 0.82,
                "director": 0.85,
                "manager": 0.88,
            },
            "average_development_time": {
                "ready_now": 0,
                "ready_1_2_years": 18,
                "ready_3_5_years": 42,
                "potential": 60,
            },
            "common_failure_factors": [
                "cultural_fit_issues",
                "stakeholder_management",
                "strategic_thinking_gap",
                "change_resistance",
            ],
        }

    def _load_industry_benchmarks(self) -> dict[str, Any]:
        """Load industry benchmarks for succession planning"""
        return {
            "bench_strength_averages": {
                "technology": 0.68,
                "healthcare": 0.72,
                "finance": 0.71,
                "manufacturing": 0.65,
            },
            "leadership_pipeline_health": {
                "excellent": 0.85,
                "good": 0.70,
                "adequate": 0.55,
                "needs_improvement": 0.40,
            },
            "diversity_targets": {
                "gender_balance": 0.40,
                "ethnic_diversity": 0.30,
                "age_diversity": 0.25,
            },
        }

    async def analyze_leadership_pipeline(
        self, organization_id: str
    ) -> dict[str, LeadershipPipeline]:
        """Analyze leadership pipeline strength across all levels"""
        try:
            pipeline_analysis = {}

            # Get current leadership roles and incumbents
            leadership_roles = await self._get_leadership_roles(organization_id)

            # Analyze each pipeline level
            pipeline_levels = ["executive", "senior_management", "middle_management", "team_lead"]

            for level in pipeline_levels:
                level_roles = [role for role in leadership_roles if role["level"] == level]
                total_positions = len(level_roles)

                if total_positions == 0:
                    continue

                # Identify potential successors for each role
                ready_candidates = 0
                all_candidates = []

                for role in level_roles:
                    role_profile = self.role_profiles.get(role["role_id"])
                    if role_profile:
                        candidates = await self._identify_succession_candidates(
                            role_profile, organization_id
                        )
                        all_candidates.extend(candidates)

                        # Count ready candidates
                        ready_count = len(
                            [
                                c
                                for c in candidates
                                if c.readiness_level
                                in [ReadinessLevel.READY_NOW, ReadinessLevel.READY_1_2_YEARS]
                            ]
                        )
                        ready_candidates += ready_count

                # Calculate metrics
                gap_percentage = max(
                    0, (total_positions - ready_candidates) / total_positions * 100
                )
                bench_strength = ready_candidates / total_positions if total_positions > 0 else 0

                # Calculate diversity metrics
                diversity_metrics = await self._calculate_diversity_metrics(all_candidates)

                # Assess risk level
                risk_level = self._assess_pipeline_risk(
                    gap_percentage, bench_strength, diversity_metrics
                )

                # Generate development recommendations
                development_recommendations = await self._generate_pipeline_recommendations(
                    level, gap_percentage, all_candidates
                )

                pipeline_analysis[level] = LeadershipPipeline(
                    pipeline_level=level,
                    total_positions=total_positions,
                    ready_candidates=ready_candidates,
                    gap_percentage=gap_percentage,
                    bench_strength=bench_strength,
                    diversity_metrics=diversity_metrics,
                    risk_level=risk_level,
                    development_recommendations=development_recommendations,
                )

            logger.info(f"Analyzed leadership pipeline for org {organization_id}")
            return pipeline_analysis

        except Exception as e:
            logger.error(f"Error analyzing leadership pipeline for org {organization_id}: {e}")
            raise

    async def identify_succession_candidates(
        self, role_id: str, organization_id: str, include_external: bool = False
    ) -> list[SuccessionCandidate]:
        """Identify and rank potential successors for a specific role"""
        try:
            role_profile = self.role_profiles.get(role_id)
            if not role_profile:
                raise ValueError(f"Role profile not found for role_id: {role_id}")

            # Get internal candidates
            internal_candidates = await self._identify_succession_candidates(
                role_profile, organization_id
            )

            # Get external candidates if requested
            external_candidates = []
            if include_external:
                external_candidates = await self._identify_external_candidates(role_profile)

            # Combine and rank all candidates
            all_candidates = internal_candidates + external_candidates

            # Convert to SuccessionCandidate objects
            succession_candidates = []
            for candidate_profile in all_candidates:
                # Calculate match score
                match_score = await self._calculate_role_match_score(
                    candidate_profile, role_profile
                )

                # Generate gap analysis
                gap_analysis = await self._analyze_candidate_gaps(candidate_profile, role_profile)

                # Create development plan
                development_plan = await self._create_succession_development_plan(
                    candidate_profile, role_profile, gap_analysis
                )

                # Assess risks
                risk_assessment = await self._assess_succession_risks(
                    candidate_profile, role_profile
                )

                # Calculate financial impact
                financial_impact = await self._calculate_succession_financial_impact(
                    candidate_profile, role_profile
                )

                # Calculate success probability
                success_probability = await self._calculate_succession_success_probability(
                    candidate_profile, role_profile, gap_analysis, risk_assessment
                )

                succession_candidate = SuccessionCandidate(
                    candidate=candidate_profile,
                    target_role=role_profile,
                    match_score=match_score,
                    gap_analysis=gap_analysis,
                    development_plan=development_plan,
                    risk_assessment=risk_assessment,
                    financial_impact=financial_impact,
                    success_probability=success_probability,
                )

                succession_candidates.append(succession_candidate)

            # Sort by match score and success probability
            succession_candidates.sort(
                key=lambda x: (x.match_score * x.success_probability), reverse=True
            )

            logger.info(
                f"Identified {len(succession_candidates)} succession candidates for role {role_id}"
            )
            return succession_candidates

        except Exception as e:
            logger.error(f"Error identifying succession candidates for role {role_id}: {e}")
            raise

    async def create_development_programs(
        self, organization_id: str, target_roles: list[str] | None = None
    ) -> dict[str, Any]:
        """Create comprehensive development programs for succession candidates"""
        try:
            # Get leadership pipeline analysis
            pipeline_analysis = await self.analyze_leadership_pipeline(organization_id)

            development_programs = {
                "accelerated_leadership": [],
                "emerging_leaders": [],
                "high_potential": [],
                "technical_leadership": [],
                "executive_prep": [],
            }

            # Analyze each pipeline level
            for level, pipeline in pipeline_analysis.items():
                if pipeline.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    # Create accelerated programs for high-risk areas
                    program = await self._create_accelerated_leadership_program(
                        level, organization_id, pipeline
                    )
                    development_programs["accelerated_leadership"].append(program)

                # Create emerging leaders program
                if pipeline.bench_strength < 0.6:
                    program = await self._create_emerging_leaders_program(
                        level, organization_id, pipeline
                    )
                    development_programs["emerging_leaders"].append(program)

                # Create high-potential program
                program = await self._create_high_potential_program(
                    level, organization_id, pipeline
                )
                development_programs["high_potential"].append(program)

                # Create technical leadership programs
                if level in ["senior_management", "middle_management"]:
                    program = await self._create_technical_leadership_program(
                        level, organization_id, pipeline
                    )
                    development_programs["technical_leadership"].append(program)

            # Create executive preparation program
            if pipeline_analysis.get("executive", LeadershipPipeline()).risk_level != RiskLevel.LOW:
                program = await self._create_executive_preparation_program(organization_id)
                development_programs["executive_prep"].append(program)

            # Calculate overall program investment and ROI
            total_investment = await self._calculate_development_investment(development_programs)
            expected_roi = await self._calculate_development_roi(
                development_programs, organization_id
            )

            logger.info(f"Created development programs for org {organization_id}")
            return {
                "programs": development_programs,
                "total_investment": total_investment,
                "expected_roi": expected_roi,
                "timeline": "24-36 months",
                "participants": await self._count_program_participants(development_programs),
            }

        except Exception as e:
            logger.error(f"Error creating development programs for org {organization_id}: {e}")
            raise

    async def simulate_succession_scenarios(
        self, organization_id: str, scenarios: list[dict[str, Any]]
    ) -> list[SuccessionScenario]:
        """Simulate different succession scenarios and assess organizational readiness"""
        try:
            scenario_results = []

            for scenario_config in scenarios:
                scenario = await self._create_succession_scenario(organization_id, scenario_config)
                scenario_results.append(scenario)

            logger.info(
                f"Simulated {len(scenario_results)} succession scenarios for org {organization_id}"
            )
            return scenario_results

        except Exception as e:
            logger.error(f"Error simulating succession scenarios for org {organization_id}: {e}")
            raise

    async def generate_succession_dashboard(
        self, organization_id: str, time_horizon_months: int = 24
    ) -> dict[str, Any]:
        """Generate comprehensive succession planning dashboard data"""
        try:
            # Get pipeline analysis
            pipeline_analysis = await self.analyze_leadership_pipeline(organization_id)

            # Get succession scenarios
            scenarios = await self._generate_default_scenarios(organization_id)
            scenario_results = await self.simulate_succession_scenarios(organization_id, scenarios)

            # Get risk assessment
            risk_assessment = await self._assess_organization_risks(organization_id)

            # Get diversity and inclusion metrics
            diversity_metrics = await self._get_diversity_inclusion_metrics(organization_id)

            # Get development program status
            development_programs = await self.create_development_programs(organization_id)

            # Calculate key metrics
            key_metrics = {
                "overall_bench_strength": self._calculate_overall_bench_strength(pipeline_analysis),
                "leadership_risk_score": self._calculate_leadership_risk_score(pipeline_analysis),
                "development_investment": development_programs.get("total_investment", 0),
                "expected_roi": development_programs.get("expected_roi", 0),
                "diversity_score": self._calculate_diversity_score(diversity_metrics),
                "readiness_timeline": self._calculate_readiness_timeline(pipeline_analysis),
            }

            dashboard_data = {
                "pipeline_analysis": {
                    level: {
                        "total_positions": pipeline.total_positions,
                        "ready_candidates": pipeline.ready_candidates,
                        "gap_percentage": pipeline.gap_percentage,
                        "bench_strength": pipeline.bench_strength,
                        "risk_level": pipeline.risk_level.value,
                    }
                    for level, pipeline in pipeline_analysis.items()
                },
                "scenario_results": [
                    {
                        "name": scenario.scenario_name,
                        "timeline_months": scenario.timeline_months,
                        "readiness_status": scenario.readiness_status,
                        "business_impact": scenario.business_impact,
                        "financial_risk": scenario.financial_risk,
                        "operational_risk": scenario.operational_risk,
                        "required_actions": scenario.required_actions,
                    }
                    for scenario in scenario_results
                ],
                "risk_assessment": risk_assessment,
                "diversity_metrics": diversity_metrics,
                "development_programs": development_programs,
                "key_metrics": key_metrics,
                "recommendations": await self._generate_executive_recommendations(
                    pipeline_analysis, risk_assessment, diversity_metrics
                ),
                "updated_date": datetime.utcnow().isoformat(),
            }

            logger.info(f"Generated succession dashboard for org {organization_id}")
            return dashboard_data

        except Exception as e:
            logger.error(f"Error generating succession dashboard for org {organization_id}: {e}")
            raise

    # Helper methods
    async def _identify_succession_candidates(
        self, role_profile: RoleProfile, organization_id: str
    ) -> list[CandidateProfile]:
        """Identify internal candidates for succession"""
        # This would integrate with HR systems and performance data
        # For now, return mock data
        candidates = []

        # Mock candidates with varying readiness levels
        mock_candidates = [
            {
                "user_id": "user_001",
                "name": "Sarah Johnson",
                "current_role": "Senior Engineering Manager",
                "readiness_level": ReadinessLevel.READY_1_2_YEARS,
                "leadership_potential": 0.85,
                "mobility_score": 0.9,
            },
            {
                "user_id": "user_002",
                "name": "Michael Chen",
                "current_role": "Director of Product",
                "readiness_level": ReadinessLevel.READY_NOW,
                "leadership_potential": 0.92,
                "mobility_score": 0.7,
            },
            {
                "user_id": "user_003",
                "name": "Amanda Rodriguez",
                "current_role": "Senior Manager",
                "readiness_level": ReadinessLevel.READY_3_5_YEARS,
                "leadership_potential": 0.78,
                "mobility_score": 0.95,
            },
        ]

        for mock_data in mock_candidates:
            candidate = CandidateProfile(
                user_id=mock_data["user_id"],
                current_role=mock_data["current_role"],
                career_aspirations=["executive_leadership", "strategic_impact"],
                readiness_level=mock_data["readiness_level"],
                readiness_score=85.0,  # Would be calculated from actual assessments
                leadership_potential=mock_data["leadership_potential"],
                mobility_score=mock_data["mobility_score"],
                risk_score=25.0,  # Lower is better
                development_needs=[
                    {"category": "strategic_thinking", "gap": 15},
                    {"category": "financial_acumen", "gap": 20},
                ],
                strengths=["team_leadership", "innovation", "change_management"],
                development_areas=["board_relations", "investor_relations"],
                promotion_timeline=18,  # months
                retention_risk=30.0,  # percentage
            )
            candidates.append(candidate)

        return candidates

    async def _calculate_role_match_score(
        self, candidate: CandidateProfile, role: RoleProfile
    ) -> float:
        """Calculate how well a candidate matches a role"""
        # Simplified calculation - would integrate with comprehensive assessment data
        base_score = candidate.readiness_score

        # Adjust for leadership potential
        leadership_adjustment = candidate.leadership_potential * 0.2

        # Adjust for mobility
        mobility_adjustment = candidate.mobility_score * 0.1

        # Adjust for risk (lower risk is better)
        risk_adjustment = (100 - candidate.risk_score) * 0.1

        total_score = base_score + leadership_adjustment + mobility_adjustment + risk_adjustment
        return min(100, total_score)

    async def _analyze_candidate_gaps(
        self, candidate: CandidateProfile, role: RoleProfile
    ) -> dict[str, float]:
        """Analyze competency gaps for candidate"""
        # Simplified gap analysis - would integrate with actual competency assessments
        gaps = {}

        for competency, required_level in role.required_competencies.items():
            # Mock current competency levels
            current_levels = {
                "strategic_thinking": 75,
                "leadership": 85,
                "financial_acumen": 65,
                "change_management": 80,
                "communication": 88,
                "innovation": 82,
                "technical_leadership": 90,
            }

            current_level = current_levels.get(competency, 70)
            gap = max(0, required_level - current_level)
            gaps[competency] = gap

        return gaps

    async def _create_succession_development_plan(
        self, candidate: CandidateProfile, role: RoleProfile, gap_analysis: dict[str, float]
    ) -> list[LearningRecommendation]:
        """Create personalized development plan for succession"""
        # This would integrate with the skill gap analysis service
        # For now, return mock recommendations
        recommendations = []

        for competency, gap in gap_analysis.items():
            if gap > 10:  # Only include significant gaps
                # Create mock learning recommendation
                recommendation = LearningRecommendation(
                    skill_name=competency,
                    learning_style="mixed",  # Would be determined from personality
                    recommended_resources=[
                        {
                            "name": f"Advanced {competency.title()} Program",
                            "provider": "Executive Education",
                            "duration": 12,
                            "cost": 5000,
                            "style": "mixed",
                        }
                    ],
                    estimated_duration=180,  # days
                    difficulty_level="advanced",
                    completion_probability=0.85,
                    expected_improvement=min(100, gap * 0.8),
                    cost_estimate=5000,
                )
                recommendations.append(recommendation)

        return recommendations
