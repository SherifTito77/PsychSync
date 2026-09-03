# app/services/skills_graph_service.py
"""
Skills & Competency Graph Service

Manages skill inventory, proficiency tracking, and the co-occurrence
graph that reveals skill clusters and organizational capability gaps.

Key operations:
  - Record/update user skill proficiencies
  - Build co-occurrence adjacency graph from UserSkill overlaps
  - Compute team skill coverage and gap analysis
  - Identify skill clusters (densely connected skill groups)
"""

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.skills import Skill, SkillAdjacency, UserSkill
from app.db.models.team import Team, TeamMember

logger = logging.getLogger(__name__)


class SkillsGraphService:
    """Manages the organizational skills graph."""

    async def add_skill(
        self,
        db: AsyncSession,
        org_id: UUID,
        name: str,
        category: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """Register a canonical skill for the organization."""
        skill = Skill(
            organization_id=org_id,
            name=name,
            category=category,
            description=description,
        )
        db.add(skill)
        await db.commit()
        await db.refresh(skill)
        return {"id": str(skill.id), "name": skill.name, "category": skill.category}

    async def record_proficiency(
        self,
        db: AsyncSession,
        user_id: UUID,
        skill_id: UUID,
        proficiency: float,
        source: str = "self_report",
        evidence: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Record or update a user's proficiency in a skill."""
        proficiency = max(0.0, min(100.0, proficiency))

        # Upsert: check for existing record with same source
        result = await db.execute(
            select(UserSkill).where(
                and_(
                    UserSkill.user_id == user_id,
                    UserSkill.skill_id == skill_id,
                    UserSkill.source == source,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.proficiency = proficiency
            existing.evidence = evidence
            existing.updated_at = datetime.now(timezone.utc)
        else:
            us = UserSkill(
                user_id=user_id,
                skill_id=skill_id,
                proficiency=proficiency,
                source=source,
                evidence=evidence,
            )
            db.add(us)

        await db.commit()
        return {
            "user_id": str(user_id),
            "skill_id": str(skill_id),
            "proficiency": proficiency,
        }

    async def get_user_skills(
        self, db: AsyncSession, user_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all skills for a user with proficiency levels."""
        result = await db.execute(
            select(UserSkill, Skill)
            .join(Skill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user_id)
            .order_by(UserSkill.proficiency.desc())
        )
        rows = result.all()
        return [
            {
                "skill_id": str(us.skill_id),
                "skill_name": skill.name,
                "category": skill.category,
                "proficiency": us.proficiency,
                "source": us.source,
            }
            for us, skill in rows
        ]

    async def get_org_skills(
        self, db: AsyncSession, org_id: UUID
    ) -> List[Dict[str, Any]]:
        """List all canonical skills for an organization."""
        result = await db.execute(
            select(Skill)
            .where(Skill.organization_id == org_id)
            .order_by(Skill.category, Skill.name)
        )
        skills = result.scalars().all()
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "category": s.category,
                "description": s.description,
            }
            for s in skills
        ]

    async def build_adjacency_graph(
        self, db: AsyncSession, org_id: UUID
    ) -> Dict[str, Any]:
        """Build/rebuild the skill co-occurrence graph.

        For each pair of skills, counts how many users have both.
        Weight = co-occurrence_count / total_users_with_either_skill (Jaccard).
        """
        # Get all user-skill pairs for this org
        result = await db.execute(
            select(UserSkill.user_id, UserSkill.skill_id)
            .join(Skill, UserSkill.skill_id == Skill.id)
            .where(Skill.organization_id == org_id)
        )
        rows = result.all()

        # Build user -> skills mapping
        user_skills: Dict[str, Set[str]] = defaultdict(set)
        skill_users: Dict[str, Set[str]] = defaultdict(set)
        for user_id, skill_id in rows:
            uid = str(user_id)
            sid = str(skill_id)
            user_skills[uid].add(sid)
            skill_users[sid].add(uid)

        # Compute co-occurrence for all skill pairs
        skill_ids = list(skill_users.keys())
        edges: List[Tuple[str, str, float, int]] = []

        for i in range(len(skill_ids)):
            for j in range(i + 1, len(skill_ids)):
                sa, sb = skill_ids[i], skill_ids[j]
                both = skill_users[sa] & skill_users[sb]
                if len(both) < 2:
                    continue
                # Jaccard similarity
                either = skill_users[sa] | skill_users[sb]
                weight = len(both) / len(either) if either else 0
                edges.append((sa, sb, weight, len(both)))

        # Persist: clear old adjacencies and write new
        await db.execute(
            delete(SkillAdjacency).where(SkillAdjacency.organization_id == org_id)
        )

        now = datetime.now(timezone.utc)
        for sa, sb, weight, sample in edges:
            db.add(
                SkillAdjacency(
                    organization_id=org_id,
                    skill_a_id=sa,
                    skill_b_id=sb,
                    weight=weight,
                    sample_size=sample,
                    computed_at=now,
                )
            )

        await db.commit()
        return {
            "organization_id": str(org_id),
            "total_skills": len(skill_ids),
            "total_edges": len(edges),
            "top_pairs": sorted(edges, key=lambda e: e[2], reverse=True)[:10],
        }

    async def team_skill_coverage(
        self, db: AsyncSession, team_id: UUID, org_id: UUID
    ) -> Dict[str, Any]:
        """Analyze a team's skill coverage against org-wide skill catalog.

        Returns which skills the team has, average proficiency per skill,
        and gaps (org skills not represented on the team).
        """
        # Get team members
        result = await db.execute(
            select(TeamMember.user_id).where(TeamMember.team_id == team_id)
        )
        member_ids = [str(r[0]) for r in result.all()]

        if not member_ids:
            return {"error": "No team members found", "team_id": str(team_id)}

        # Get all org skills
        all_skills = await self.get_org_skills(db, org_id)
        all_skill_ids = {s["id"] for s in all_skills}
        skill_name_map = {s["id"]: s["name"] for s in all_skills}

        # Get team member skills
        result = await db.execute(
            select(UserSkill.skill_id, func.avg(UserSkill.proficiency), func.count())
            .where(UserSkill.user_id.in_(member_ids))
            .group_by(UserSkill.skill_id)
        )
        team_skills = {}
        for skill_id, avg_prof, count in result.all():
            sid = str(skill_id)
            team_skills[sid] = {
                "skill_id": sid,
                "skill_name": skill_name_map.get(sid, "Unknown"),
                "avg_proficiency": round(float(avg_prof), 1),
                "members_with_skill": int(count),
                "coverage_pct": round(int(count) / len(member_ids) * 100, 1),
            }

        # Gaps: org skills not on team
        covered_ids = set(team_skills.keys())
        gaps = [
            {"skill_id": sid, "skill_name": skill_name_map.get(sid, "Unknown")}
            for sid in all_skill_ids - covered_ids
        ]

        # Gap score (0-100, higher = better equipped)
        # 40% coverage ratio + 35% avg proficiency depth + 25% breadth (bus factor)
        total = max(len(all_skill_ids), 1)
        coverage_ratio = len(covered_ids) / total

        if team_skills:
            avg_proficiency = sum(
                s["avg_proficiency"] for s in team_skills.values()
            ) / len(team_skills)
            avg_breadth = sum(s["coverage_pct"] for s in team_skills.values()) / len(
                team_skills
            )
        else:
            avg_proficiency = 0.0
            avg_breadth = 0.0

        gap_score = round(
            coverage_ratio * 40
            + (avg_proficiency / 100) * 35
            + (avg_breadth / 100) * 25,
            1,
        )

        return {
            "team_id": str(team_id),
            "member_count": len(member_ids),
            "skills_covered": len(covered_ids),
            "skills_total": len(all_skill_ids),
            "coverage_ratio": round(len(covered_ids) / max(len(all_skill_ids), 1), 2),
            "gap_score": gap_score,
            "skills": sorted(
                team_skills.values(), key=lambda s: s["avg_proficiency"], reverse=True
            ),
            "gaps": gaps,
        }

    async def skill_clusters(
        self, db: AsyncSession, org_id: UUID
    ) -> List[Dict[str, Any]]:
        """Identify skill clusters from the adjacency graph.

        Uses simple connected-component detection on edges with weight > 0.3.
        Each cluster represents a competency domain.
        """
        result = await db.execute(
            select(SkillAdjacency).where(
                and_(
                    SkillAdjacency.organization_id == org_id,
                    SkillAdjacency.weight > 0.3,
                )
            )
        )
        edges = result.scalars().all()

        # Union-Find for connected components
        parent: Dict[str, str] = {}

        def find(x: str) -> str:
            while parent.get(x, x) != x:
                parent[x] = parent.get(parent[x], parent[x])
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for edge in edges:
            sa = str(edge.skill_a_id)
            sb = str(edge.skill_b_id)
            parent.setdefault(sa, sa)
            parent.setdefault(sb, sb)
            union(sa, sb)

        # Group by root
        clusters_map: Dict[str, List[str]] = defaultdict(list)
        for node in parent:
            clusters_map[find(node)].append(node)

        # Resolve skill names
        skill_ids = list(parent.keys())
        if skill_ids:
            result = await db.execute(
                select(Skill.id, Skill.name, Skill.category).where(
                    Skill.id.in_(skill_ids)
                )
            )
            name_map = {
                str(r[0]): {"name": r[1], "category": r[2]} for r in result.all()
            }
        else:
            name_map = {}

        clusters = []
        for root, members in clusters_map.items():
            if len(members) < 2:
                continue
            clusters.append(
                {
                    "cluster_id": root,
                    "size": len(members),
                    "skills": [
                        {
                            "skill_id": m,
                            "name": name_map.get(m, {}).get("name", "Unknown"),
                            "category": name_map.get(m, {}).get("category", ""),
                        }
                        for m in members
                    ],
                }
            )

        return sorted(clusters, key=lambda c: c["size"], reverse=True)


skills_graph_service = SkillsGraphService()
