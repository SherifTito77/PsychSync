# app/schemas/network_analysis.py
"""
Pydantic schemas for Organizational Network Analysis API.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CollaborationNomination(BaseModel):
    nominee_id: UUID
    network_type: str = Field(..., pattern="^(advice|trust|energy|collaboration)$")
    strength: int = Field(default=3, ge=1, le=5)


class CollaborationSurveySubmit(BaseModel):
    nominations: list[CollaborationNomination] = Field(..., min_length=1, max_length=50)
    survey_round: str | None = None


class CollaborationSurveyResult(BaseModel):
    saved: int
    respondent_id: str
    survey_round: str | None = None


class NetworkNodeResponse(BaseModel):
    user_id: str
    name: str
    degree_centrality: float
    betweenness_centrality: float
    bridging_score: float
    team_count: int
    role: str
    teams: list[str]
    community_id: int | None = None


class NetworkEdgeResponse(BaseModel):
    source: str
    target: str
    weight: float


class CommunityResponse(BaseModel):
    id: int
    members: list[str]
    size: int
    internal_density: float
    health_score: float | None = None


class NetworkStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    density: float
    avg_degree_centrality: float
    num_communities: int = 0


class TemporalSnapshotResponse(BaseModel):
    date: str
    total_nodes: int
    total_edges: int
    density: float
    avg_degree_centrality: float
    num_communities: int | None = None
    num_isolates: int | None = None
    num_influencers: int | None = None
    num_bridges: int | None = None


class PersonalityNetworkInsight(BaseModel):
    type: str
    user_id: str
    name: str
    message: str


class CommunityProfile(BaseModel):
    community_id: int
    size: int
    avg_personality: dict[str, float]
    dominant_trait: str


class SurveyNetworkResponse(BaseModel):
    network_type: str
    survey_round: str | None = None
    total_respondents: int
    total_nominees: int
    edges: list[dict]
    top_nominated: list[dict]
