"""
Team Optimization API Endpoints

Analyzes candidate members and recommends optimal team compositions
based on personality traits (Big Five), skills coverage, role diversity,
and project requirements.
"""

import logging
import time
from itertools import combinations
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.db.models.user import User
from app.services.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/team-optimizer", tags=["Team Optimization"])


class MemberTraits(BaseModel):
    # Big Five (OCEAN) — primary traits
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5

    # Emotional Intelligence — Layer 1
    empathy: Optional[float] = None  # 0-1, understanding others' emotional states
    self_regulation: Optional[float] = None  # 0-1, managing stress under pressure
    social_awareness: Optional[float] = None  # 0-1, reading team dynamics

    # Cognitive Style — Layer 1
    risk_tolerance: Optional[float] = None  # 0-1, comfort with uncertainty
    autonomy_preference: Optional[float] = None  # 0-1, self-directed vs needs direction
    detail_orientation: Optional[float] = None  # 0-1, QA mindset vs big-picture

    # Collaboration — Layer 1
    conflict_style: Optional[str] = (
        None  # competing/avoiding/collaborating/accommodating/compromising
    )
    feedback_receptivity: Optional[float] = None  # 0-1, openness to criticism
    leadership_emergence: Optional[float] = None  # 0-1, tendency to step up

    # Cognitive load preference
    cognitive_load_preference: Optional[float] = (
        None  # 0-1, how much complexity they thrive under
    )


# Role-specific ideal trait ranges (Layer 2)
ROLE_TRAIT_PRESETS: Dict[str, Dict[str, Any]] = {
    "developer": {
        "openness": 0.6,
        "conscientiousness": 0.7,
        "extraversion": 0.4,
        "agreeableness": 0.5,
        "neuroticism": 0.3,
        "risk_tolerance": 0.5,
        "autonomy_preference": 0.7,
        "detail_orientation": 0.7,
        "feedback_receptivity": 0.7,
        "cognitive_load_preference": 0.7,
        "role_specific_traits": [
            "systematic_thinking",
            "ambiguity_tolerance",
            "debugging_patience",
        ],
    },
    "designer": {
        "openness": 0.85,
        "conscientiousness": 0.5,
        "extraversion": 0.5,
        "agreeableness": 0.6,
        "neuroticism": 0.3,
        "empathy": 0.8,
        "detail_orientation": 0.6,
        "feedback_receptivity": 0.8,
        "cognitive_load_preference": 0.5,
        "role_specific_traits": [
            "aesthetic_sensitivity",
            "user_empathy",
            "iteration_comfort",
        ],
    },
    "pm": {
        "openness": 0.6,
        "conscientiousness": 0.75,
        "extraversion": 0.7,
        "agreeableness": 0.65,
        "neuroticism": 0.25,
        "empathy": 0.7,
        "social_awareness": 0.8,
        "risk_tolerance": 0.6,
        "leadership_emergence": 0.7,
        "cognitive_load_preference": 0.8,
        "role_specific_traits": [
            "stakeholder_management",
            "ambiguity_tolerance",
            "prioritization_bias",
        ],
    },
    "qa": {
        "openness": 0.4,
        "conscientiousness": 0.85,
        "extraversion": 0.4,
        "agreeableness": 0.5,
        "neuroticism": 0.3,
        "detail_orientation": 0.9,
        "autonomy_preference": 0.5,
        "feedback_receptivity": 0.6,
        "cognitive_load_preference": 0.6,
        "role_specific_traits": [
            "skepticism_index",
            "thoroughness",
            "process_adherence",
        ],
    },
    "devops": {
        "openness": 0.5,
        "conscientiousness": 0.8,
        "extraversion": 0.4,
        "agreeableness": 0.5,
        "neuroticism": 0.2,
        "self_regulation": 0.8,
        "risk_tolerance": 0.4,
        "autonomy_preference": 0.8,
        "cognitive_load_preference": 0.8,
        "role_specific_traits": [
            "stress_threshold",
            "incident_ownership",
            "automation_mindset",
        ],
    },
    "lead": {
        "openness": 0.6,
        "conscientiousness": 0.7,
        "extraversion": 0.65,
        "agreeableness": 0.6,
        "neuroticism": 0.2,
        "empathy": 0.7,
        "social_awareness": 0.75,
        "self_regulation": 0.8,
        "leadership_emergence": 0.85,
        "feedback_receptivity": 0.7,
        "role_specific_traits": ["delegation", "mentoring", "strategic_thinking"],
    },
}


class MemberInput(BaseModel):
    id: Any
    name: str = ""
    role: str = "developer"
    traits: MemberTraits = MemberTraits()
    skills: List[str] = []
    experience_years: float = 0
    availability: float = 1.0


class ProjectRequirements(BaseModel):
    project_type: str = "web_app"
    duration_weeks: int = 12
    complexity: str = "medium"
    required_skills: List[str] = []
    team_size_min: int = 3
    team_size_max: int = 6


class OptimizeRequest(BaseModel):
    members: List[MemberInput]
    project_requirements: ProjectRequirements = ProjectRequirements()
    objective: str = "maximize_performance"


def _role_fit_score(member: MemberInput) -> float:
    """How well a member's traits match their role's ideal profile."""
    preset = ROLE_TRAIT_PRESETS.get(member.role)
    if not preset:
        return 0.5
    diffs = []
    for trait_name, ideal_val in preset.items():
        if trait_name == "role_specific_traits" or not isinstance(
            ideal_val, (int, float)
        ):
            continue
        actual = getattr(member.traits, trait_name, None)
        if actual is not None:
            diffs.append(abs(actual - ideal_val))
    if not diffs:
        return 0.5
    return max(0, 1.0 - (sum(diffs) / len(diffs)) * 2)


def _compute_conflict_potential(team: List[MemberInput]) -> float:
    """
    Compute conflict potential index from Thomas-Kilmann conflict styles.
    Returns 0.0 (no conflict risk) to 1.0 (high conflict risk).
    """
    styles = [m.traits.conflict_style for m in team if m.traits.conflict_style]
    if len(styles) < 2:
        return 0.0

    # Pairwise friction matrix — higher = more friction when these two styles meet
    FRICTION = {
        ("competing", "competing"): 0.95,
        ("competing", "avoiding"): 0.55,
        ("competing", "accommodating"): 0.60,
        ("competing", "compromising"): 0.35,
        ("competing", "collaborating"): 0.25,
        ("avoiding", "avoiding"): 0.70,
        ("avoiding", "accommodating"): 0.40,
        ("avoiding", "compromising"): 0.30,
        ("avoiding", "collaborating"): 0.20,
        ("accommodating", "accommodating"): 0.45,
        ("accommodating", "compromising"): 0.15,
        ("accommodating", "collaborating"): 0.10,
        ("compromising", "compromising"): 0.10,
        ("compromising", "collaborating"): 0.05,
        ("collaborating", "collaborating"): 0.05,
    }

    total_friction = 0.0
    pair_count = 0
    for a, b in combinations(styles, 2):
        key = (a, b) if (a, b) in FRICTION else (b, a)
        total_friction += FRICTION.get(key, 0.3)
        pair_count += 1

    avg_friction = total_friction / pair_count if pair_count else 0.0

    # Amplifier: concentration of competing styles raises ceiling
    competing_ratio = styles.count("competing") / len(styles)
    if competing_ratio > 0.5:
        avg_friction = min(1.0, avg_friction * 1.3)

    return min(1.0, avg_friction)


def _compute_team_composites(
    team: List[MemberInput],
    project_reqs: ProjectRequirements,
) -> Dict[str, Any]:
    """Compute Layer 3 team-level composite scores."""
    # 1. Cognitive Diversity Score — moderate variance in thinking styles is optimal
    cog_traits = [
        "risk_tolerance",
        "autonomy_preference",
        "detail_orientation",
        "cognitive_load_preference",
    ]
    cog_variances = []
    for trait in cog_traits:
        vals = [
            getattr(m.traits, trait)
            for m in team
            if getattr(m.traits, trait) is not None
        ]
        if len(vals) >= 2:
            avg = sum(vals) / len(vals)
            var = sum((v - avg) ** 2 for v in vals) / len(vals)
            cog_variances.append(var)
    if cog_variances:
        avg_var = sum(cog_variances) / len(cog_variances)
        if avg_var < 0.01:
            cognitive_diversity = 0.3  # groupthink
        elif avg_var > 0.1:
            cognitive_diversity = max(0.2, 1.0 - (avg_var - 0.06) * 5)  # chaos
        else:
            cognitive_diversity = min(1.0, 0.5 + avg_var * 10)
    else:
        cognitive_diversity = 0.5

    # 2. Conflict Potential Index
    conflict_potential = _compute_conflict_potential(team)

    # 3. Bandwidth Alignment — does team's cognitive load preference match complexity?
    complexity_demand = {"low": 0.3, "medium": 0.5, "high": 0.7, "critical": 0.9}
    demand = complexity_demand.get(project_reqs.complexity, 0.5)
    load_prefs = [
        m.traits.cognitive_load_preference
        for m in team
        if m.traits.cognitive_load_preference is not None
    ]
    if load_prefs:
        team_load_avg = sum(load_prefs) / len(load_prefs)
        bandwidth_alignment = max(0, 1.0 - abs(team_load_avg - demand) * 2.5)
    else:
        bandwidth_alignment = 0.5

    # 4. Risk Profile Match — team risk tolerance vs project type needs
    project_risk_map = {
        "web_app": 0.4,
        "mobile": 0.5,
        "data_pipeline": 0.3,
        "ml_system": 0.7,
        "infrastructure": 0.3,
        "research": 0.8,
    }
    target_risk = project_risk_map.get(project_reqs.project_type, 0.5)
    risk_vals = [
        m.traits.risk_tolerance for m in team if m.traits.risk_tolerance is not None
    ]
    if risk_vals:
        team_risk_avg = sum(risk_vals) / len(risk_vals)
        risk_profile_match = max(0, 1.0 - abs(team_risk_avg - target_risk) * 2.5)
    else:
        risk_profile_match = 0.5

    # 5. Communication Style Spread
    comm_traits = ["extraversion", "social_awareness", "feedback_receptivity"]
    comm_vals = []
    for m in team:
        member_comm = [
            getattr(m.traits, t)
            for t in comm_traits
            if getattr(m.traits, t, None) is not None
        ]
        if member_comm:
            comm_vals.append(sum(member_comm) / len(member_comm))
    if len(comm_vals) >= 2:
        avg_comm = sum(comm_vals) / len(comm_vals)
        comm_var = sum((v - avg_comm) ** 2 for v in comm_vals) / len(comm_vals)
        if comm_var < 0.01:
            communication_spread = 0.4  # echo chamber
        elif comm_var > 0.08:
            communication_spread = max(0.3, 1.0 - (comm_var - 0.04) * 8)
        else:
            communication_spread = min(1.0, 0.5 + comm_var * 12)
    else:
        communication_spread = 0.5

    return {
        "cognitive_diversity_score": round(cognitive_diversity, 3),
        "conflict_potential_index": round(conflict_potential, 3),
        "bandwidth_alignment": round(bandwidth_alignment, 3),
        "risk_profile_match": round(risk_profile_match, 3),
        "communication_style_spread": round(communication_spread, 3),
    }


def _score_team(
    team: List[MemberInput],
    project_reqs: ProjectRequirements,
) -> Dict[str, Any]:
    members_count = len(team)

    # --- Personality balance (Big Five) ---
    trait_names = [
        "openness",
        "conscientiousness",
        "extraversion",
        "agreeableness",
        "neuroticism",
    ]
    trait_values = {t: [] for t in trait_names}
    for m in team:
        for t in trait_names:
            trait_values[t].append(getattr(m.traits, t, 0.5))

    # Lower variance = more balanced team; also reward moderate average (not extreme)
    balance_scores = []
    for t in trait_names:
        vals = trait_values[t]
        avg = sum(vals) / len(vals)
        variance = sum((v - avg) ** 2 for v in vals) / len(vals)
        # Ideal: avg near 0.5-0.7 for most traits (except neuroticism, lower is better)
        if t == "neuroticism":
            avg_score = max(0, 1.0 - avg)  # Lower neuroticism is better
        else:
            avg_score = 1.0 - abs(avg - 0.6) * 2  # Penalize extremes
        avg_score = max(0, min(1, avg_score))
        var_score = max(0, 1.0 - variance * 4)  # Penalize high variance
        balance_scores.append(avg_score * 0.6 + var_score * 0.4)

    personality_balance = sum(balance_scores) / len(balance_scores)

    # --- Emotional Intelligence (Layer 1) ---
    ei_traits = ["empathy", "self_regulation", "social_awareness"]
    ei_values = []
    for m in team:
        member_ei = [
            getattr(m.traits, t) for t in ei_traits if getattr(m.traits, t) is not None
        ]
        if member_ei:
            ei_values.append(sum(member_ei) / len(member_ei))
    ei_score = sum(ei_values) / len(ei_values) if ei_values else None

    # --- Role fit (Layer 2) ---
    role_fit_scores = [_role_fit_score(m) for m in team]
    role_fit = sum(role_fit_scores) / len(role_fit_scores)

    # --- Collaboration readiness ---
    feedback_vals = [
        m.traits.feedback_receptivity
        for m in team
        if m.traits.feedback_receptivity is not None
    ]
    leadership_vals = [
        m.traits.leadership_emergence
        for m in team
        if m.traits.leadership_emergence is not None
    ]
    if feedback_vals or leadership_vals:
        fb_score = (sum(feedback_vals) / len(feedback_vals)) if feedback_vals else 0.5
        if leadership_vals:
            max_lead = max(leadership_vals)
            lead_score = 1.0 if max_lead > 0.6 else max_lead / 0.6
        else:
            lead_score = 0.5
        collaboration_score = fb_score * 0.6 + lead_score * 0.4
    else:
        collaboration_score = None

    # --- Skill coverage ---
    team_skills = set()
    for m in team:
        team_skills.update(s.lower().strip() for s in m.skills)

    required = [s.lower().strip() for s in project_reqs.required_skills]
    if required:
        covered = sum(1 for s in required if s in team_skills)
        skill_coverage_score = covered / len(required)
    else:
        # No explicit requirements: reward skill diversity
        skill_coverage_score = min(len(team_skills) / max(members_count * 2, 1), 1.0)

    # --- Role diversity ---
    roles = [m.role for m in team]
    unique_roles = len(set(roles))
    role_diversity = min(unique_roles / max(members_count * 0.6, 1), 1.0)

    # --- Experience & availability ---
    avg_experience = sum(m.experience_years for m in team) / members_count
    experience_score = min(avg_experience / 8.0, 1.0)  # Cap at 8 years

    avg_availability = sum(m.availability for m in team) / members_count

    # --- Compatibility (enhanced with EI + collaboration) ---
    compatibility = personality_balance * 0.7 + role_diversity * 0.3
    if ei_score is not None:
        compatibility = compatibility * 0.7 + ei_score * 0.3
    if collaboration_score is not None:
        compatibility = compatibility * 0.85 + collaboration_score * 0.15

    # --- Overall score ---
    complexity_weights = {
        "low": {
            "personality": 0.15,
            "skills": 0.35,
            "diversity": 0.20,
            "experience": 0.15,
            "availability": 0.15,
        },
        "medium": {
            "personality": 0.25,
            "skills": 0.30,
            "diversity": 0.15,
            "experience": 0.20,
            "availability": 0.10,
        },
        "high": {
            "personality": 0.30,
            "skills": 0.25,
            "diversity": 0.15,
            "experience": 0.25,
            "availability": 0.05,
        },
        "critical": {
            "personality": 0.30,
            "skills": 0.25,
            "diversity": 0.10,
            "experience": 0.30,
            "availability": 0.05,
        },
    }
    w = complexity_weights.get(project_reqs.complexity, complexity_weights["medium"])

    overall = (
        personality_balance * w["personality"]
        + skill_coverage_score * w["skills"]
        + role_diversity * w["diversity"]
        + experience_score * w["experience"]
        + avg_availability * w["availability"]
    )

    # Blend in extended traits when available (up to 15% influence)
    extended_signals = [role_fit]
    if ei_score is not None:
        extended_signals.append(ei_score)
    if collaboration_score is not None:
        extended_signals.append(collaboration_score)
    extended_avg = sum(extended_signals) / len(extended_signals)
    overall = overall * 0.85 + extended_avg * 0.15

    # --- Team composites (Layer 3) ---
    composites = _compute_team_composites(team, project_reqs)

    # Build strengths / risks
    strengths = []
    risks = []

    if personality_balance > 0.7:
        strengths.append("Well-balanced personality composition")
    elif personality_balance < 0.4:
        risks.append("Personality imbalance may cause friction")

    if skill_coverage_score > 0.8:
        strengths.append("Excellent skill coverage for project requirements")
    elif skill_coverage_score < 0.5:
        risks.append("Significant skill gaps — consider training or additional hires")

    if role_diversity > 0.7:
        strengths.append("Good role diversity across the team")
    elif unique_roles == 1:
        risks.append("All members share the same role — limited perspective diversity")

    if avg_experience > 5:
        strengths.append(f"Experienced team (avg {avg_experience:.1f} years)")
    elif avg_experience < 2:
        risks.append("Relatively junior team — consider adding a senior member")

    if avg_availability > 0.9:
        strengths.append("High team availability")
    elif avg_availability < 0.6:
        risks.append("Low average availability may slow delivery")

    # Extended trait insights
    if ei_score is not None and ei_score > 0.7:
        strengths.append("High emotional intelligence — strong interpersonal dynamics")
    elif ei_score is not None and ei_score < 0.35:
        risks.append("Low team EI — interpersonal friction likely under stress")

    if role_fit > 0.75:
        strengths.append("Team members are well-matched to their roles")
    elif role_fit < 0.4:
        risks.append(
            "Role-trait misalignment — some members may struggle in their roles"
        )

    if collaboration_score is not None and collaboration_score > 0.7:
        strengths.append("Strong collaboration readiness (feedback + leadership)")

    # Composite-based warnings
    if composites["cognitive_diversity_score"] < 0.35:
        risks.append("Low cognitive diversity — groupthink risk")
    elif composites["cognitive_diversity_score"] > 0.85:
        strengths.append("Healthy cognitive diversity across the team")

    if composites["conflict_potential_index"] > 0.6:
        risks.append("High conflict potential — consider facilitated team norming")

    if composites["bandwidth_alignment"] < 0.4:
        risks.append("Team bandwidth doesn't match project complexity")
    elif composites["bandwidth_alignment"] > 0.75:
        strengths.append("Team bandwidth well-aligned with project demands")

    if composites["risk_profile_match"] < 0.4:
        risks.append("Team risk tolerance mismatched with project type")

    # Role distribution
    role_dist = {}
    for r in roles:
        role_dist[r] = role_dist.get(r, 0) + 1

    # Skill coverage detail
    skill_detail = {}
    for s in required if required else sorted(team_skills):
        skill_detail[s] = 100.0 if s in team_skills else 0.0

    return {
        "overall_score": round(overall * 100, 1),
        "compatibility_score": round(compatibility, 3),
        "skill_coverage": round(skill_coverage_score, 3),
        "diversity_score": round(role_diversity, 3),
        "personality_balance": round(personality_balance, 3),
        "experience_score": round(experience_score, 3),
        "role_fit": round(role_fit, 3),
        "ei_score": round(ei_score, 3) if ei_score is not None else None,
        "collaboration_score": (
            round(collaboration_score, 3) if collaboration_score is not None else None
        ),
        "composites": composites,
        "estimated_velocity": f"{round(overall * avg_experience * avg_availability * 10, 1)} pts/sprint",
        "strengths": strengths,
        "risks": risks,
        "roles_distribution": role_dist,
        "skill_coverage_detail": skill_detail,
        "member_ids": [m.id for m in team],
    }


@router.post("/optimize")
async def optimize_team(
    request: OptimizeRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    start_time = time.time()
    members = request.members
    reqs = request.project_requirements

    if len(members) < reqs.team_size_min:
        return {
            "overall_score": 0.0,
            "recommended_teams": [],
            "skill_coverage": {},
            "insights": [f"Need at least {reqs.team_size_min} members to optimize."],
            "metrics": {
                "total_candidates_evaluated": 0,
                "optimization_time_seconds": 0.0,
                "confidence_score": 0,
                "algorithm_used": "none",
            },
        }

    # Generate and score all valid team sizes
    scored_teams = []
    total_evaluated = 0

    for size in range(reqs.team_size_min, min(reqs.team_size_max, len(members)) + 1):
        combos = list(combinations(members, size))

        # For large candidate pools, sample instead of exhaustive search
        if len(combos) > 500:
            import random

            random.seed(42)
            combos = random.sample(combos, 500)

        for combo in combos:
            team_list = list(combo)
            score_result = _score_team(team_list, reqs)
            scored_teams.append(score_result)
            total_evaluated += 1

    # Sort by overall score descending, take top 3
    scored_teams.sort(key=lambda t: t["overall_score"], reverse=True)
    top_teams = scored_teams[:3]

    # Aggregate skill coverage from best team
    best_skill_coverage = top_teams[0]["skill_coverage_detail"] if top_teams else {}

    # Generate insights
    insights = []
    if top_teams:
        best = top_teams[0]
        if best["overall_score"] > 80:
            insights.append(
                "Found an excellent team configuration with strong synergy."
            )
        elif best["overall_score"] > 60:
            insights.append(
                "Good team configurations available with room for improvement."
            )
        else:
            insights.append(
                "Current candidate pool produces moderate team fits. Consider expanding the pool."
            )

        if len(top_teams) > 1:
            spread = top_teams[0]["overall_score"] - top_teams[-1]["overall_score"]
            if spread < 5:
                insights.append(
                    "Top team options are very close in quality — any would work well."
                )
            else:
                insights.append(
                    f"Top recommendation scores {spread:.1f}% higher than alternatives."
                )

        all_skills = set()
        for m in members:
            all_skills.update(s.lower().strip() for s in m.skills)
        required = [s.lower().strip() for s in reqs.required_skills]
        missing = [s for s in required if s not in all_skills]
        if missing:
            insights.append(
                f"No candidates cover these required skills: {', '.join(missing)}"
            )

    elapsed = time.time() - start_time
    confidence = min(0.95, 0.5 + (total_evaluated / max(len(members) * 10, 1)) * 0.45)

    return {
        "overall_score": top_teams[0]["overall_score"] if top_teams else 0.0,
        "recommended_teams": top_teams,
        "skill_coverage": best_skill_coverage,
        "insights": insights,
        "metrics": {
            "total_candidates_evaluated": total_evaluated,
            "optimization_time_seconds": round(elapsed, 3),
            "confidence_score": round(confidence, 3),
            "algorithm_used": (
                "exhaustive_combinatorial"
                if total_evaluated <= 500
                else "sampled_combinatorial"
            ),
        },
    }


@router.post("/analyze")
async def analyze_team(
    request: OptimizeRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    if not request.members:
        return {
            "team_name": "Team Analysis",
            "overall_score": 0.0,
            "compatibility_score": 0.0,
            "skill_coverage_score": 0.0,
            "diversity_score": 0.0,
            "strengths": [],
            "gaps": [],
            "recommendations": ["Add team members to analyze."],
        }

    result = _score_team(request.members, request.project_requirements)
    return {
        "team_name": "Current Team",
        "overall_score": result["overall_score"],
        "compatibility_score": result["compatibility_score"],
        "skill_coverage_score": result["skill_coverage"],
        "diversity_score": result["diversity_score"],
        "strengths": result["strengths"],
        "gaps": result["risks"],
        "recommendations": (
            result["risks"] if result["risks"] else ["Team composition looks good!"]
        ),
    }


@router.post("/compatibility")
async def check_compatibility(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "user_1": {},
        "user_2": {},
        "compatibility_score": 0.0,
        "compatibility_level": "unknown",
        "color_indicator": "gray",
        "recommendations": ["Provide two user profiles to check compatibility."],
    }


@router.get("/candidates")
async def get_candidates(
    current_user: User = Depends(get_current_user),
) -> list:
    return []


@router.get("/recommendations/{team_id}")
async def get_team_recommendations(
    team_id: int,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "team_id": team_id,
        "team_name": "",
        "recommendations": [],
        "gaps": [],
        "priority_actions": [],
    }
