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
    openness: float = 0.5
    conscientiousness: float = 0.5
    extraversion: float = 0.5
    agreeableness: float = 0.5
    neuroticism: float = 0.5


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

    # --- Compatibility (trait complementarity) ---
    # Teams work better when they have a mix of high-E and moderate-E members
    compatibility = personality_balance * 0.7 + role_diversity * 0.3

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
