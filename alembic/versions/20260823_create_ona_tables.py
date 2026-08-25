"""Create ONA (Organizational Network Analysis) tables

Creates: network_edges, network_snapshots, collaboration_survey_responses

Enables persistent graph storage, temporal network evolution tracking,
and self-reported collaboration survey data collection.

Revision ID: 20260823_ona_tables
Revises: None (standalone - branched migration history)
Create Date: 2026-08-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP

revision: str = "20260823_ona_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- network_edges ---
    op.create_table(
        "network_edges",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("target_user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("edge_type", sa.String(50), nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column(
            "first_observed_at",
            TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "last_observed_at",
            TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.UniqueConstraint(
            "organization_id",
            "source_user_id",
            "target_user_id",
            "edge_type",
            name="uq_network_edge",
        ),
        comment="Persistent graph edges for organizational network analysis",
    )
    op.create_index(
        "idx_network_edge_org_type", "network_edges", ["organization_id", "edge_type"]
    )
    op.create_index(
        "idx_network_edge_source",
        "network_edges",
        ["source_user_id", "last_observed_at"],
    )
    op.create_index(
        "idx_network_edge_target",
        "network_edges",
        ["target_user_id", "last_observed_at"],
    )
    op.create_index(
        "idx_network_edge_temporal",
        "network_edges",
        ["organization_id", "last_observed_at"],
    )

    # --- network_snapshots ---
    op.create_table(
        "network_snapshots",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("total_nodes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_edges", sa.Integer, nullable=False, server_default="0"),
        sa.Column("density", sa.Numeric(6, 4), nullable=True),
        sa.Column("avg_degree_centrality", sa.Numeric(5, 3), nullable=True),
        sa.Column("avg_betweenness_centrality", sa.Numeric(5, 3), nullable=True),
        sa.Column("modularity_score", sa.Numeric(5, 3), nullable=True),
        sa.Column("num_communities", sa.Integer, nullable=True),
        sa.Column("num_isolates", sa.Integer, nullable=True),
        sa.Column("num_influencers", sa.Integer, nullable=True),
        sa.Column("num_bridges", sa.Integer, nullable=True),
        sa.Column("node_metrics", sa.JSON, nullable=True),
        sa.Column("communities", sa.JSON, nullable=True),
        sa.Column("cross_team_density", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "organization_id", "snapshot_date", name="uq_network_snapshot_date"
        ),
        comment="Point-in-time network snapshots for temporal analysis",
    )
    op.create_index(
        "idx_snapshot_org_date",
        "network_snapshots",
        ["organization_id", "snapshot_date"],
    )

    # --- collaboration_survey_responses ---
    op.create_table(
        "collaboration_survey_responses",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
        sa.Column("respondent_id", UUID(as_uuid=True), nullable=False),
        sa.Column("nominee_id", UUID(as_uuid=True), nullable=False),
        sa.Column("network_type", sa.String(30), nullable=False),
        sa.Column("strength", sa.Integer, nullable=False, server_default="1"),
        sa.Column("survey_round", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "respondent_id",
            "nominee_id",
            "network_type",
            "survey_round",
            name="uq_collab_survey_response",
        ),
        comment="Self-reported collaboration network survey responses",
    )
    op.create_index(
        "idx_collab_survey_org_type",
        "collaboration_survey_responses",
        ["organization_id", "network_type"],
    )
    op.create_index(
        "idx_collab_survey_respondent",
        "collaboration_survey_responses",
        ["respondent_id", "network_type"],
    )
    op.create_index(
        "idx_collab_survey_round",
        "collaboration_survey_responses",
        ["organization_id", "survey_round"],
    )


def downgrade() -> None:
    op.drop_table("collaboration_survey_responses")
    op.drop_table("network_snapshots")
    op.drop_table("network_edges")
