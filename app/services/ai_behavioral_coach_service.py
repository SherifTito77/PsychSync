"""
AI Behavioral Coach & Digital Twin Service

Provides personalized behavioral coaching by synthesizing:
  - Individual assessment profiles (Big Five, MBTI, etc.)
  - Team dynamics context
  - Historical trends from the Behavioral Intelligence Engine
  - Work system signals (when available)

The "Digital Twin" is a behavioral profile snapshot that represents
an employee's working style, stress patterns, and growth trajectory,
enabling what-if simulations for team composition changes.

Coach outputs:
  - Personalized development recommendations
  - Communication style guidance for team interactions
  - Stress/burnout early intervention prompts
  - Growth trajectory projections

Digital Twin outputs:
  - Behavioral profile card
  - Team fit simulation
  - Predicted responses to organizational changes
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.response import Response
from app.db.models.team import Team, TeamMember
from app.db.models.user import User

logger = logging.getLogger(__name__)


class AIBehavioralCoachService:
    """Generates personalized coaching insights from behavioral data."""

    async def get_coaching_profile(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """Build a complete coaching profile for an individual."""
        user = await self._get_user(db, user_id)
        if not user:
            return {"error": "User not found", "user_id": user_id}

        # Gather data
        responses = await self._get_user_responses(db, user_id)
        teams = await self._get_user_teams(db, user_id)
        traits = self._extract_personality_traits(responses)
        work_style = self._derive_work_style(traits)
        stress_indicators = self._assess_stress_level(responses)
        growth_areas = self._identify_growth_areas(traits)

        return {
            "user_id": user_id,
            "user_name": user.full_name or user.email,
            "personality_profile": traits,
            "work_style": work_style,
            "stress_indicators": stress_indicators,
            "growth_areas": growth_areas,
            "coaching_recommendations": self._generate_coaching(
                traits, stress_indicators, growth_areas
            ),
            "communication_guide": self._communication_guide(traits),
            "team_context": {
                "team_count": len(teams),
                "team_names": [t["name"] for t in teams],
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def get_digital_twin(
        self,
        db: AsyncSession,
        user_id: str,
    ) -> Dict[str, Any]:
        """Generate a Digital Twin behavioral profile."""
        user = await self._get_user(db, user_id)
        if not user:
            return {"error": "User not found", "user_id": user_id}

        responses = await self._get_user_responses(db, user_id)
        traits = self._extract_personality_traits(responses)
        engagement = self._engagement_pattern(responses)

        return {
            "user_id": user_id,
            "user_name": user.full_name or user.email,
            "twin_version": "1.0",
            "behavioral_dna": {
                "openness": traits.get("openness", 50),
                "conscientiousness": traits.get("conscientiousness", 50),
                "extraversion": traits.get("extraversion", 50),
                "agreeableness": traits.get("agreeableness", 50),
                "neuroticism": traits.get("neuroticism", 50),
            },
            "work_preferences": self._derive_work_style(traits),
            "collaboration_style": self._collaboration_style(traits),
            "stress_resilience": 100 - traits.get("neuroticism", 50),
            "change_adaptability": traits.get("openness", 50),
            "engagement_pattern": engagement,
            "predicted_responses": {
                "to_high_pressure": self._predict_pressure_response(traits),
                "to_team_conflict": self._predict_conflict_response(traits),
                "to_org_change": self._predict_change_response(traits),
                "to_new_leadership": self._predict_leadership_response(traits),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def simulate_team_fit(
        self,
        db: AsyncSession,
        user_id: str,
        target_team_id: str,
    ) -> Dict[str, Any]:
        """Simulate how a person would fit into a specific team."""
        user = await self._get_user(db, user_id)
        if not user:
            return {"error": "User not found"}

        user_responses = await self._get_user_responses(db, user_id)
        user_traits = self._extract_personality_traits(user_responses)

        # Get team members' traits
        members = await self._get_team_member_ids(db, target_team_id)
        team_traits = []
        for mid in members:
            if mid == user_id:
                continue
            r = await self._get_user_responses(db, mid)
            team_traits.append(self._extract_personality_traits(r))

        if not team_traits:
            return {
                "user_id": user_id,
                "team_id": target_team_id,
                "fit_score": 50,
                "analysis": "Insufficient team data for simulation",
            }

        # Calculate fit
        fit = self._calculate_team_fit(user_traits, team_traits)

        return {
            "user_id": user_id,
            "user_name": user.full_name or user.email,
            "team_id": target_team_id,
            "fit_score": fit["overall"],
            "complementarity": fit["complementarity"],
            "conflict_risk": fit["conflict_risk"],
            "synergy_potential": fit["synergy_potential"],
            "analysis": fit["narrative"],
            "recommendations": fit["recommendations"],
        }

    # ══════════════════════════════════════════════════════════════════
    # TRAIT EXTRACTION
    # ══════════════════════════════════════════════════════════════════

    def _extract_personality_traits(self, responses: list) -> Dict[str, float]:
        """Extract Big Five trait scores from assessment responses."""
        if not responses:
            return {
                "openness": 50,
                "conscientiousness": 50,
                "extraversion": 50,
                "agreeableness": 50,
                "neuroticism": 50,
            }

        values = [r.answer_value for r in responses if r.answer_value is not None]
        if not values:
            return {
                "openness": 50,
                "conscientiousness": 50,
                "extraversion": 50,
                "agreeableness": 50,
                "neuroticism": 50,
            }

        avg = sum(values) / len(values)
        normalized = min(100, max(0, (avg - 1) / 4 * 100))

        # Without question-to-trait mapping, distribute based on response patterns
        variance = sum((v - avg) ** 2 for v in values) / len(values)
        spread = min(20, variance * 5)

        return {
            "openness": round(min(100, max(0, normalized + spread * 0.5)), 1),
            "conscientiousness": round(min(100, max(0, normalized + spread * 0.2)), 1),
            "extraversion": round(min(100, max(0, normalized - spread * 0.1)), 1),
            "agreeableness": round(min(100, max(0, normalized + spread * 0.3)), 1),
            "neuroticism": round(min(100, max(0, 100 - normalized)), 1),
        }

    def _derive_work_style(self, traits: Dict[str, float]) -> Dict[str, Any]:
        """Map personality traits to work style preferences."""
        o, c, e, a, n = (
            traits.get("openness", 50),
            traits.get("conscientiousness", 50),
            traits.get("extraversion", 50),
            traits.get("agreeableness", 50),
            traits.get("neuroticism", 50),
        )

        return {
            "preferred_structure": (
                "flexible" if o > 60 else ("structured" if c > 60 else "balanced")
            ),
            "communication": (
                "collaborative" if e > 60 else ("independent" if e < 40 else "adaptive")
            ),
            "decision_making": (
                "analytical" if c > 60 else ("intuitive" if o > 60 else "consensus")
            ),
            "conflict_approach": (
                "diplomatic" if a > 60 else ("direct" if a < 40 else "balanced")
            ),
            "stress_management": (
                "resilient" if n < 40 else ("sensitive" if n > 60 else "moderate")
            ),
            "innovation_drive": (
                "pioneer" if o > 70 else ("pragmatist" if o < 40 else "adaptive")
            ),
            "team_role_affinity": self._team_role_affinity(traits),
        }

    def _team_role_affinity(self, traits: Dict[str, float]) -> str:
        """Suggest natural team role based on personality."""
        o, c, e, a = (
            traits.get("openness", 50),
            traits.get("conscientiousness", 50),
            traits.get("extraversion", 50),
            traits.get("agreeableness", 50),
        )

        if e > 65 and a > 55:
            return "Facilitator"
        if c > 65 and e < 50:
            return "Implementer"
        if o > 65 and e > 55:
            return "Innovator"
        if a > 65 and c > 55:
            return "Coordinator"
        if o > 60 and c < 45:
            return "Explorer"
        if c > 60 and a < 45:
            return "Challenger"
        return "Specialist"

    def _collaboration_style(self, traits: Dict[str, float]) -> Dict[str, str]:
        e, a = traits.get("extraversion", 50), traits.get("agreeableness", 50)
        return {
            "meetings": (
                "thrives in group discussions" if e > 60 else "prefers prepared agendas"
            ),
            "feedback": (
                "welcomes open feedback" if a > 60 else "prefers private feedback"
            ),
            "brainstorming": (
                "energized by group ideation"
                if e > 55 and traits.get("openness", 50) > 55
                else "prefers time to think first"
            ),
            "conflict": (
                "naturally mediates"
                if a > 65
                else "addresses directly" if a < 40 else "adapts to situation"
            ),
        }

    # ══════════════════════════════════════════════════════════════════
    # STRESS & ENGAGEMENT
    # ══════════════════════════════════════════════════════════════════

    def _assess_stress_level(self, responses: list) -> Dict[str, Any]:
        """Infer stress level from response patterns."""
        if not responses:
            return {"level": "unknown", "score": 0, "indicators": []}

        recent = [
            r
            for r in responses
            if r.created_at
            and (datetime.utcnow() - r.created_at.replace(tzinfo=None)).days < 30
        ]

        indicators = []
        score = 0

        # Rapid response times may indicate rushing
        times = [r.response_time_ms for r in recent if r.response_time_ms]
        if times:
            avg_time = sum(times) / len(times)
            if avg_time < 3000:
                indicators.append(
                    "Unusually fast responses — may indicate rushing or disengagement"
                )
                score += 20

        # Low answer values on wellbeing-type questions
        values = [r.answer_value for r in recent if r.answer_value is not None]
        if values:
            avg_val = sum(values) / len(values)
            if avg_val < 2.5:
                indicators.append(
                    "Below-average response scores — possible dissatisfaction"
                )
                score += 25

        # Declining engagement (fewer recent responses)
        if len(recent) == 0 and len(responses) > 5:
            indicators.append("No recent assessment activity — possible disengagement")
            score += 30

        level = "high" if score >= 50 else ("moderate" if score >= 25 else "low")
        return {"level": level, "score": min(score, 100), "indicators": indicators}

    def _engagement_pattern(self, responses: list) -> Dict[str, Any]:
        """Analyze engagement trends."""
        if not responses:
            return {"status": "new", "total_responses": 0, "trend": "unknown"}

        total = len(responses)
        recent = sum(
            1
            for r in responses
            if r.created_at
            and (datetime.utcnow() - r.created_at.replace(tzinfo=None)).days < 30
        )
        older = sum(
            1
            for r in responses
            if r.created_at
            and 30 <= (datetime.utcnow() - r.created_at.replace(tzinfo=None)).days < 60
        )

        if recent > older:
            trend = "increasing"
        elif recent < older and older > 0:
            trend = "decreasing"
        else:
            trend = "stable"

        return {
            "status": "active" if recent > 0 else "inactive",
            "total_responses": total,
            "recent_30d": recent,
            "trend": trend,
        }

    # ══════════════════════════════════════════════════════════════════
    # GROWTH & COACHING
    # ══════════════════════════════════════════════════════════════════

    def _identify_growth_areas(self, traits: Dict[str, float]) -> List[Dict[str, Any]]:
        """Identify top development areas based on trait profile."""
        areas = []

        o, c, e, a, n = (
            traits.get("openness", 50),
            traits.get("conscientiousness", 50),
            traits.get("extraversion", 50),
            traits.get("agreeableness", 50),
            traits.get("neuroticism", 50),
        )

        if o < 40:
            areas.append(
                {
                    "area": "Openness to Experience",
                    "current": o,
                    "suggestion": "Experiment with new approaches and seek diverse perspectives",
                    "priority": "medium",
                }
            )
        if c < 40:
            areas.append(
                {
                    "area": "Organization & Follow-through",
                    "current": c,
                    "suggestion": "Implement structured planning habits and milestone tracking",
                    "priority": "high",
                }
            )
        if n > 60:
            areas.append(
                {
                    "area": "Emotional Resilience",
                    "current": 100 - n,
                    "suggestion": "Develop stress management techniques and cognitive reframing skills",
                    "priority": "high",
                }
            )
        if a < 35:
            areas.append(
                {
                    "area": "Interpersonal Collaboration",
                    "current": a,
                    "suggestion": "Practice active listening and perspective-taking in team settings",
                    "priority": "medium",
                }
            )
        if e < 30:
            areas.append(
                {
                    "area": "Assertiveness & Visibility",
                    "current": e,
                    "suggestion": "Start with small group contributions and build toward broader visibility",
                    "priority": "low",
                }
            )

        return sorted(
            areas, key=lambda a: {"high": 0, "medium": 1, "low": 2}[a["priority"]]
        )

    def _generate_coaching(
        self,
        traits: Dict[str, float],
        stress: Dict[str, Any],
        growth_areas: list,
    ) -> List[Dict[str, str]]:
        """Generate personalized coaching recommendations."""
        recs = []

        if stress.get("level") == "high":
            recs.append(
                {
                    "type": "urgent",
                    "title": "Stress Management",
                    "message": "Your response patterns suggest elevated stress. Consider scheduling dedicated recovery time and discussing workload with your manager.",
                }
            )

        for area in growth_areas[:2]:
            recs.append(
                {
                    "type": "development",
                    "title": area["area"],
                    "message": area["suggestion"],
                }
            )

        # Strength-based coaching
        o, c, e, a = (
            traits.get("openness", 50),
            traits.get("conscientiousness", 50),
            traits.get("extraversion", 50),
            traits.get("agreeableness", 50),
        )

        if o > 70:
            recs.append(
                {
                    "type": "strength",
                    "title": "Innovation Driver",
                    "message": "Your high openness is a team asset. Consider leading brainstorming sessions or piloting new processes.",
                }
            )
        if c > 70:
            recs.append(
                {
                    "type": "strength",
                    "title": "Execution Excellence",
                    "message": "Your conscientiousness makes you a reliable executor. Others may lean on you — ensure you're delegating appropriately.",
                }
            )
        if e > 65 and a > 60:
            recs.append(
                {
                    "type": "strength",
                    "title": "Natural Leader",
                    "message": "Your combination of extraversion and agreeableness positions you well for people leadership. Seek mentoring or coaching opportunities.",
                }
            )

        return recs

    def _communication_guide(self, traits: Dict[str, float]) -> Dict[str, str]:
        """Generate a 'How to work with this person' guide."""
        e, a, c, o, n = (
            traits.get("extraversion", 50),
            traits.get("agreeableness", 50),
            traits.get("conscientiousness", 50),
            traits.get("openness", 50),
            traits.get("neuroticism", 50),
        )

        return {
            "preferred_communication": (
                "Face-to-face or video"
                if e > 60
                else "Written (email, Slack)" if e < 40 else "Either works"
            ),
            "meeting_style": (
                "Interactive discussion" if e > 55 else "Prepared agenda with pre-read"
            ),
            "feedback_approach": (
                "Supportive and specific" if n > 50 else "Direct and actionable"
            ),
            "motivation": (
                "Recognition and social impact"
                if e > 55 and a > 55
                else (
                    "Autonomy and mastery"
                    if o > 55
                    else "Clear goals and progress tracking"
                )
            ),
            "under_pressure": (
                "May need space to process"
                if n > 55
                else "Stays focused under pressure"
            ),
            "decision_speed": (
                "Deliberate — give time to analyze"
                if c > 60
                else "Quick — provide key info upfront"
            ),
        }

    # ══════════════════════════════════════════════════════════════════
    # PREDICTIONS (Digital Twin)
    # ══════════════════════════════════════════════════════════════════

    def _predict_pressure_response(self, traits: Dict[str, float]) -> Dict[str, str]:
        n, c = traits.get("neuroticism", 50), traits.get("conscientiousness", 50)
        if n > 60:
            return {
                "reaction": "Stressed",
                "recommendation": "Provide clear priorities and reduce ambiguity",
            }
        if c > 60:
            return {
                "reaction": "Focused",
                "recommendation": "Trust them to manage, offer support if asked",
            }
        return {
            "reaction": "Adaptive",
            "recommendation": "Check in periodically but don't micromanage",
        }

    def _predict_conflict_response(self, traits: Dict[str, float]) -> Dict[str, str]:
        a, e = traits.get("agreeableness", 50), traits.get("extraversion", 50)
        if a > 65:
            return {
                "reaction": "Avoidant",
                "recommendation": "Create safe space for them to voice concerns",
            }
        if a < 35:
            return {
                "reaction": "Confrontational",
                "recommendation": "Acknowledge their perspective first, then redirect",
            }
        return {
            "reaction": "Balanced",
            "recommendation": "Engage directly with structured conflict resolution",
        }

    def _predict_change_response(self, traits: Dict[str, float]) -> Dict[str, str]:
        o, n = traits.get("openness", 50), traits.get("neuroticism", 50)
        if o > 65:
            return {
                "reaction": "Enthusiastic",
                "recommendation": "Channel their energy as a change champion",
            }
        if o < 35 and n > 50:
            return {
                "reaction": "Resistant",
                "recommendation": "Provide extra transition time and clear rationale",
            }
        return {
            "reaction": "Cautious",
            "recommendation": "Share benefits and involve them in planning",
        }

    def _predict_leadership_response(self, traits: Dict[str, float]) -> Dict[str, str]:
        e, a, c = (
            traits.get("extraversion", 50),
            traits.get("agreeableness", 50),
            traits.get("conscientiousness", 50),
        )
        if e > 60 and a > 55:
            return {
                "reaction": "Quick trust builder",
                "recommendation": "Give them early opportunities to connect with new leader",
            }
        if c > 60:
            return {
                "reaction": "Performance-oriented",
                "recommendation": "Clarify expectations and success criteria early",
            }
        return {
            "reaction": "Wait-and-see",
            "recommendation": "Allow time to build trust through consistency",
        }

    # ══════════════════════════════════════════════════════════════════
    # TEAM FIT SIMULATION
    # ══════════════════════════════════════════════════════════════════

    def _calculate_team_fit(
        self, user_traits: Dict[str, float], team_traits: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """Calculate how well a person fits into a team's existing dynamics."""
        # Average team traits
        team_avg = {}
        for trait in [
            "openness",
            "conscientiousness",
            "extraversion",
            "agreeableness",
            "neuroticism",
        ]:
            vals = [t.get(trait, 50) for t in team_traits]
            team_avg[trait] = sum(vals) / len(vals) if vals else 50

        # Complementarity: user fills gaps in team
        complement_score = 0
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness"]:
            if team_avg[trait] < 40 and user_traits.get(trait, 50) > 60:
                complement_score += 25
            elif abs(user_traits.get(trait, 50) - team_avg[trait]) < 15:
                complement_score += 10

        # Conflict risk: high neuroticism mismatch
        n_diff = abs(
            user_traits.get("neuroticism", 50) - team_avg.get("neuroticism", 50)
        )
        a_user = user_traits.get("agreeableness", 50)
        conflict_risk = min(100, n_diff * 0.5 + max(0, 60 - a_user))

        # Synergy: similar work values
        c_diff = abs(
            user_traits.get("conscientiousness", 50)
            - team_avg.get("conscientiousness", 50)
        )
        synergy = max(0, 100 - c_diff * 1.5 - n_diff * 0.5)

        overall = min(
            100, complement_score * 0.3 + synergy * 0.4 + (100 - conflict_risk) * 0.3
        )

        # Narrative
        parts = []
        if overall > 70:
            parts.append("Strong fit — this person would complement the team well.")
        elif overall > 50:
            parts.append("Moderate fit — some adjustment period expected.")
        else:
            parts.append("Challenging fit — significant personality differences.")

        if complement_score > 50:
            parts.append("They fill important gaps in the team's personality profile.")
        if conflict_risk > 50:
            parts.append(
                "Elevated conflict risk — proactive relationship building recommended."
            )

        recs = []
        if conflict_risk > 50:
            recs.append(
                "Schedule structured onboarding with team norms and expectations"
            )
        if complement_score > 50:
            recs.append(
                "Leverage their unique strengths in areas where the team is weaker"
            )
        if overall < 50:
            recs.append("Consider a trial period or phased integration")
        if not recs:
            recs.append("Standard integration — person should fit naturally")

        return {
            "overall": round(overall, 1),
            "complementarity": round(complement_score, 1),
            "conflict_risk": round(conflict_risk, 1),
            "synergy_potential": round(synergy, 1),
            "narrative": " ".join(parts),
            "recommendations": recs,
        }

    # ══════════════════════════════════════════════════════════════════
    # DATA ACCESS
    # ══════════════════════════════════════════════════════════════════

    async def _get_user(self, db: AsyncSession, user_id: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _get_user_responses(self, db: AsyncSession, user_id: str) -> list:
        result = await db.execute(
            select(Response)
            .where(Response.user_id == user_id)
            .order_by(Response.created_at.desc())
            .limit(200)
        )
        return result.scalars().all()

    async def _get_user_teams(
        self, db: AsyncSession, user_id: str
    ) -> List[Dict[str, str]]:
        result = await db.execute(
            select(Team.id, Team.name)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user_id)
        )
        return [{"id": str(r[0]), "name": r[1]} for r in result.all()]

    async def _get_team_member_ids(self, db: AsyncSession, team_id: str) -> List[str]:
        result = await db.execute(
            select(TeamMember.user_id).where(TeamMember.team_id == team_id)
        )
        return [str(r[0]) for r in result.all()]
