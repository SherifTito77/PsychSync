# app/api/v1/endpoints/skills.py
"""
Skills & Competency Graph Endpoints

CRUD for skills, proficiency recording, graph building, and gap analysis.
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.security import get_current_user
from app.services.skills_graph_service import skills_graph_service

router = APIRouter(prefix="/skills", tags=["skills"])


class AddSkillRequest(BaseModel):
    name: str = Field(..., max_length=100)
    category: str = Field(..., description="technical, soft_skills, leadership, domain")
    description: str = Field("", max_length=500)


class RecordProficiencyRequest(BaseModel):
    user_id: UUID
    skill_id: UUID
    proficiency: float = Field(..., ge=0, le=100)
    source: str = Field(
        "self_report", description="self_report, manager, assessment, inferred"
    )
    evidence: list[dict] | None = None


@router.post("/{organization_id}", response_model=dict[str, Any])
async def add_skill(
    organization_id: UUID,
    body: AddSkillRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Register a new skill in the organization's catalog."""
    return await skills_graph_service.add_skill(
        db, organization_id, body.name, body.category, body.description
    )


@router.get("/{organization_id}", response_model=list[dict[str, Any]])
async def list_skills(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all skills in the organization's catalog."""
    return await skills_graph_service.get_org_skills(db, organization_id)


@router.post("/{organization_id}/proficiency", response_model=dict[str, Any])
async def record_proficiency(
    organization_id: UUID,
    body: RecordProficiencyRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record or update a user's skill proficiency."""
    return await skills_graph_service.record_proficiency(
        db, body.user_id, body.skill_id, body.proficiency, body.source, body.evidence
    )


@router.get("/{organization_id}/user/{user_id}", response_model=list[dict[str, Any]])
async def get_user_skills(
    organization_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all skills for a specific user."""
    return await skills_graph_service.get_user_skills(db, user_id)


@router.post("/{organization_id}/graph/build", response_model=dict[str, Any])
async def build_graph(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Build/rebuild the skill co-occurrence adjacency graph."""
    return await skills_graph_service.build_adjacency_graph(db, organization_id)


@router.get("/{organization_id}/graph/clusters", response_model=list[dict[str, Any]])
async def get_clusters(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get skill clusters (competency domains) from the adjacency graph."""
    return await skills_graph_service.skill_clusters(db, organization_id)


@router.get("/{organization_id}/team/{team_id}/coverage", response_model=dict[str, Any])
async def team_coverage(
    organization_id: UUID,
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Analyze a team's skill coverage and gaps."""
    return await skills_graph_service.team_skill_coverage(db, team_id, organization_id)
