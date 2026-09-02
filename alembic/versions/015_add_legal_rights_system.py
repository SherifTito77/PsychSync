"""add_legal_rights_system

Revision ID: 015c_add_legal_rights_system
Revises: c2049af57c94
Create Date: 2026-01-16 15:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "015c_add_legal_rights_system"
down_revision: Union[str, None] = "c2049af57c94"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create labor_laws table
    op.create_table(
        "labor_laws",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("country_name", sa.String(length=100), nullable=False),
        sa.Column("state_region", sa.String(length=100)),
        sa.Column("continent", sa.String(length=2), nullable=False),
        sa.Column("law_name", sa.String(length=255), nullable=False),
        sa.Column("law_code", sa.String(length=100)),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("min_wage", sa.Float()),
        sa.Column("max_weekly_hours", sa.Integer()),
        sa.Column("overtime_threshold", sa.Integer()),
        sa.Column("overtime_rate", sa.Float()),
        sa.Column("mandatory_break_minutes", sa.Integer()),
        sa.Column("min_vacation_days", sa.Integer()),
        sa.Column("discrimination_protection_level", sa.Integer()),
        sa.Column("safety_protection_level", sa.Integer()),
        sa.Column("privacy_protection_level", sa.Integer()),
        sa.Column("termination_protection_level", sa.Integer()),
        sa.Column("provisions", postgresql.JSONB()),
        sa.Column("resources", postgresql.JSONB()),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.Column("effective_date", sa.DateTime()),
        sa.Column("source_url", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("verified", sa.Boolean(), server_default="false"),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True)),
        sa.Column("verified_date", sa.DateTime()),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_labor_laws_country_category", "labor_laws", ["country_code", "category"]
    )
    op.create_index("idx_labor_laws_country_code", "labor_laws", ["country_code"])
    op.create_index("idx_labor_laws_continent", "labor_laws", ["continent"])
    op.create_index("idx_labor_laws_category", "labor_laws", ["category"])

    # Create employee_rights_resources table
    op.create_table(
        "employee_rights_resources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True)),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("summary", sa.Text()),
        sa.Column("url", sa.Text()),
        sa.Column("target_audience", postgresql.JSONB()),
        sa.Column("skill_level", sa.String(length=50)),
        sa.Column("thumbnail_url", sa.String(length=500)),
        sa.Column("video_url", sa.String(length=500)),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("display_order", sa.Integer(), server_default="0"),
        sa.Column("language", sa.String(length=10), server_default="en"),
        sa.Column("is_featured", sa.Boolean(), server_default="false"),
        sa.Column("view_count", sa.Integer(), server_default="0"),
        sa.Column("helpful_count", sa.Integer(), server_default="0"),
        sa.Column("not_helpful_count", sa.Integer(), server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.Column("published_at", sa.DateTime()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("is_published", sa.Boolean(), server_default="false"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("approved_at", sa.DateTime()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_employee_rights_resources_org",
        "employee_rights_resources",
        ["organization_id"],
    )
    op.create_index(
        "idx_employee_rights_resources_category",
        "employee_rights_resources",
        ["category"],
    )
    op.create_index(
        "idx_employee_rights_resources_published",
        "employee_rights_resources",
        ["is_published"],
    )

    # Create contract_violations table
    op.create_table(
        "contract_violations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("affected_employee_id", postgresql.UUID(as_uuid=True)),
        sa.Column("violation_type", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("labor_law_violated", sa.String(length=255)),
        sa.Column("law_reference", sa.Text()),
        sa.Column(
            "detected_at",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("detection_method", sa.String(length=100)),
        sa.Column("detected_by", postgresql.UUID(as_uuid=True)),
        sa.Column("evidence_data", postgresql.JSONB()),
        sa.Column("evidence_urls", postgresql.JSONB()),
        sa.Column("incident_date_range", postgresql.JSONB()),
        sa.Column("affected_employees_count", sa.Integer(), server_default="1"),
        sa.Column("estimated_financial_impact", sa.Float()),
        sa.Column("legal_risk_score", sa.Integer()),
        sa.Column("status", sa.String(length=50), server_default="open"),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True)),
        sa.Column("priority", sa.String(length=20), server_default="medium"),
        sa.Column("resolution_notes", sa.Text()),
        sa.Column("resolved_at", sa.DateTime()),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("corrective_actions", postgresql.JSONB()),
        sa.Column("legal_review_required", sa.Boolean(), server_default="false"),
        sa.Column("legal_review_date", sa.DateTime()),
        sa.Column("legal_review_notes", sa.Text()),
        sa.Column("external_legal_aid", sa.Boolean(), server_default="false"),
        sa.Column("legal_aid_contact", postgresql.JSONB()),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["affected_employee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["detected_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_contract_violations_org_status",
        "contract_violations",
        ["organization_id", "status"],
    )
    op.create_index(
        "idx_contract_violations_severity", "contract_violations", ["severity"]
    )
    op.create_index(
        "idx_contract_violations_detected_at", "contract_violations", ["detected_at"]
    )
    op.create_index(
        "idx_contract_violations_category", "contract_violations", ["category"]
    )

    # Create rights_knowledge_checks table
    op.create_table(
        "rights_knowledge_checks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("check_type", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("questions", postgresql.JSONB(), nullable=False),
        sa.Column("responses", postgresql.JSONB(), nullable=False),
        sa.Column("correct_answers", postgresql.JSONB()),
        sa.Column("score_percentage", sa.Integer()),
        sa.Column("passed", sa.Boolean(), server_default="false"),
        sa.Column("passing_threshold", sa.Integer(), server_default="70"),
        sa.Column("knowledge_gaps", postgresql.JSONB()),
        sa.Column("recommended_resources", postgresql.JSONB()),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rights_knowledge_checks_user", "rights_knowledge_checks", ["user_id"]
    )
    op.create_index(
        "idx_rights_knowledge_checks_org",
        "rights_knowledge_checks",
        ["organization_id"],
    )

    # Create legal_aid_resources table
    op.create_table(
        "legal_aid_resources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("state_region", sa.String(length=100)),
        sa.Column("city", sa.String(length=100)),
        sa.Column("resource_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("email", sa.String(length=255)),
        sa.Column("website", sa.Text()),
        sa.Column("address", sa.Text()),
        sa.Column("specializations", postgresql.JSONB()),
        sa.Column("languages_spoken", postgresql.JSONB()),
        sa.Column("free_consultation", sa.Boolean(), server_default="false"),
        sa.Column("sliding_scale", sa.Boolean(), server_default="false"),
        sa.Column("emergency_services", sa.Boolean(), server_default="false"),
        sa.Column("verified", sa.Boolean(), server_default="false"),
        sa.Column("rating", sa.Float()),
        sa.Column("review_count", sa.Integer(), server_default="0"),
        sa.Column("response_time_hours", sa.Integer()),
        sa.Column("operating_hours", postgresql.JSONB()),
        sa.Column("consultation_fee", sa.Float()),
        sa.Column("hourly_rate", sa.Float()),
        sa.Column("pro_bono", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.Column("last_verified", sa.DateTime()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_legal_aid_resources_country", "legal_aid_resources", ["country_code"]
    )
    op.create_index(
        "idx_legal_aid_resources_type", "legal_aid_resources", ["resource_type"]
    )
    op.create_index(
        "idx_legal_aid_resources_state", "legal_aid_resources", ["state_region"]
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index("idx_legal_aid_resources_state", table_name="legal_aid_resources")
    op.drop_index("idx_legal_aid_resources_type", table_name="legal_aid_resources")
    op.drop_index("idx_legal_aid_resources_country", table_name="legal_aid_resources")
    op.drop_table("legal_aid_resources")

    op.drop_index(
        "idx_rights_knowledge_checks_org", table_name="rights_knowledge_checks"
    )
    op.drop_index(
        "idx_rights_knowledge_checks_user", table_name="rights_knowledge_checks"
    )
    op.drop_table("rights_knowledge_checks")

    op.drop_index("idx_contract_violations_category", table_name="contract_violations")
    op.drop_index(
        "idx_contract_violations_detected_at", table_name="contract_violations"
    )
    op.drop_index("idx_contract_violations_severity", table_name="contract_violations")
    op.drop_index(
        "idx_contract_violations_org_status", table_name="contract_violations"
    )
    op.drop_table("contract_violations")

    op.drop_index(
        "idx_employee_rights_resources_published",
        table_name="employee_rights_resources",
    )
    op.drop_index(
        "idx_employee_rights_resources_category", table_name="employee_rights_resources"
    )
    op.drop_index(
        "idx_employee_rights_resources_org", table_name="employee_rights_resources"
    )
    op.drop_table("employee_rights_resources")

    op.drop_index("idx_labor_laws_category", table_name="labor_laws")
    op.drop_index("idx_labor_laws_continent", table_name="labor_laws")
    op.drop_index("idx_labor_laws_country_code", table_name="labor_laws")
    op.drop_index("idx_labor_laws_country_category", table_name="labor_laws")
    op.drop_table("labor_laws")
