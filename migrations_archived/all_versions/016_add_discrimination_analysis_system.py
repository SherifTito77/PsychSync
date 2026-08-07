"""add_discrimination_analysis_system

Revision ID: 016_add_discrimination_analysis_system
Revises: 015_add_legal_rights_system
Create Date: 2026-01-16 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "016_add_discrimination_analysis_system"
down_revision: Union[str, None] = "015_add_legal_rights_system"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create demographic_profiles table
    op.create_table(
        "demographic_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gender", sa.String(length=50)),
        sa.Column("race", sa.String(length=50)),
        sa.Column("ethnicity", sa.String(length=50)),
        sa.Column("age_range", sa.String(length=20)),
        sa.Column("religion", sa.String(length=50)),
        sa.Column("disability_status", sa.String(length=50)),
        sa.Column("sexual_orientation", sa.String(length=50)),
        sa.Column("gender_identity", sa.String(length=50)),
        sa.Column("veteran_status", sa.String(length=50)),
        sa.Column("marital_status", sa.String(length=50)),
        sa.Column(
            "data_classification", sa.String(length=20), server_default="sensitive"
        ),
        sa.Column("consent_given", sa.Boolean(), server_default="true"),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.Column("verified", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "idx_demographic_profiles_user", "demographic_profiles", ["user_id"]
    )
    op.create_index(
        "idx_demographic_profiles_org", "demographic_profiles", ["organization_id"]
    )

    # Create equity_analyses table
    op.create_table(
        "equity_analyses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_type", sa.String(length=50), nullable=False),
        sa.Column(
            "analysis_date",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("analyzed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("time_period_start", sa.DateTime()),
        sa.Column("time_period_end", sa.DateTime()),
        sa.Column("total_employees_analyzed", sa.Integer(), server_default="0"),
        sa.Column("departments_analyzed", postgresql.JSONB()),
        sa.Column("protected_classes_analyzed", postgresql.JSONB()),
        sa.Column("disparity_detected", sa.Boolean(), server_default="false"),
        sa.Column("severity_level", sa.String(length=20)),
        sa.Column("statistical_significance", sa.Float()),
        sa.Column("confidence_interval", sa.String(length=50)),
        sa.Column("effect_size", sa.Float()),
        sa.Column("effect_size_interpretation", sa.String(length=50)),
        sa.Column("group_statistics", postgresql.JSONB()),
        sa.Column("baseline_group", sa.String(length=100)),
        sa.Column("affected_groups", postgresql.JSONB()),
        sa.Column("estimated_pay_gap", sa.Float()),
        sa.Column("affected_employees_count", sa.Integer()),
        sa.Column("recommended_actions", postgresql.JSONB()),
        sa.Column("priority_level", sa.String(length=20)),
        sa.Column("status", sa.String(length=50), server_default="pending_review"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("review_notes", sa.Text()),
        sa.Column("follow_up_required", sa.Boolean(), server_default="false"),
        sa.Column("follow_up_date", sa.DateTime()),
        sa.Column("follow_up_completed", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["analyzed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_equity_analyses_org_type",
        "equity_analyses",
        ["organization_id", "analysis_type"],
    )
    op.create_index(
        "idx_equity_analyses_severity", "equity_analyses", ["severity_level"]
    )
    op.create_index("idx_equity_analyses_date", "equity_analyses", ["analysis_date"])

    # Create pay_equity_records table
    op.create_table(
        "pay_equity_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True)),
        sa.Column("demographic_dimension", sa.String(length=50), nullable=False),
        sa.Column("demographic_value", sa.String(length=50), nullable=False),
        sa.Column("department", sa.String(length=100)),
        sa.Column("job_level", sa.String(length=50)),
        sa.Column("employee_count", sa.Integer(), server_default="0"),
        sa.Column("mean_salary", sa.Numeric(precision=12, scale=2)),
        sa.Column("median_salary", sa.Numeric(precision=12, scale=2)),
        sa.Column("min_salary", sa.Numeric(precision=12, scale=2)),
        sa.Column("max_salary", sa.Numeric(precision=12, scale=2)),
        sa.Column("std_deviation", sa.Float()),
        sa.Column("salary_gap_percent", sa.Float()),
        sa.Column("salary_gap_amount", sa.Numeric(precision=12, scale=2)),
        sa.Column("adjusted_salary_gap", sa.Numeric(precision=12, scale=2)),
        sa.Column("p_value", sa.Float()),
        sa.Column("statistically_significant", sa.Boolean(), server_default="false"),
        sa.Column("period_start", sa.DateTime()),
        sa.Column("period_end", sa.DateTime()),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["equity_analyses.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_pay_equity_org_dimension",
        "pay_equity_records",
        ["organization_id", "demographic_dimension"],
    )
    op.create_index("idx_pay_equity_analysis", "pay_equity_records", ["analysis_id"])

    # Create promotion_tracking table
    op.create_table(
        "promotion_tracking",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("promotion_date", sa.DateTime(), nullable=False),
        sa.Column("from_level", sa.String(length=50)),
        sa.Column("to_level", sa.String(length=50)),
        sa.Column("from_department", sa.String(length=100)),
        sa.Column("to_department", sa.String(length=100)),
        sa.Column("months_in_previous_role", sa.Integer()),
        sa.Column("performance_rating", sa.String(length=20)),
        sa.Column("years_of_experience", sa.Integer()),
        sa.Column("peer_group_average_promotion_time", sa.Integer()),
        sa.Column("promotion_speed_percentile", sa.Float()),
        sa.Column("delayed_promotion", sa.Boolean(), server_default="false"),
        sa.Column("delay_reason", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["equity_analyses.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create hiring_metrics table
    op.create_table(
        "hiring_metrics",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True)),
        sa.Column("job_title", sa.String(length=100)),
        sa.Column("department", sa.String(length=100)),
        sa.Column("job_level", sa.String(length=50)),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("demographic_dimension", sa.String(length=50), nullable=False),
        sa.Column("demographic_value", sa.String(length=50), nullable=False),
        sa.Column("applicants_count", sa.Integer(), server_default="0"),
        sa.Column("interviewed_count", sa.Integer(), server_default="0"),
        sa.Column("offered_count", sa.Integer(), server_default="0"),
        sa.Column("hired_count", sa.Integer(), server_default="0"),
        sa.Column("interview_rate", sa.Float()),
        sa.Column("offer_rate", sa.Float()),
        sa.Column("acceptance_rate", sa.Float()),
        sa.Column("overall_hire_rate", sa.Float()),
        sa.Column("baseline_hire_rate", sa.Float()),
        sa.Column("rate_difference", sa.Float()),
        sa.Column("percent_difference", sa.Float()),
        sa.Column("p_value", sa.Float()),
        sa.Column("statistically_significant", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["analysis_id"], ["equity_analyses.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_hiring_metrics_org_period",
        "hiring_metrics",
        ["organization_id", "period_start", "period_end"],
    )
    op.create_index(
        "idx_hiring_metrics_dimension", "hiring_metrics", ["demographic_dimension"]
    )

    # Create discrimination_complaints table
    op.create_table(
        "discrimination_complaints",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("complainant_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_anonymous", sa.Boolean(), server_default="false"),
        sa.Column("anonymous_fingerprint", sa.String(length=255)),
        sa.Column("complaint_type", sa.String(length=50), nullable=False),
        sa.Column("discrimination_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("incident_date", sa.DateTime()),
        sa.Column("incident_location", sa.String(length=100)),
        sa.Column("perpetrator_type", sa.String(length=50)),
        sa.Column("perpetrator_id", postgresql.UUID(as_uuid=True)),
        sa.Column("witness_ids", postgresql.JSONB()),
        sa.Column("evidence_urls", postgresql.JSONB()),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("credible", sa.Boolean(), server_default="true"),
        sa.Column("status", sa.String(length=50), server_default="open"),
        sa.Column("assigned_investigator_id", postgresql.UUID(as_uuid=True)),
        sa.Column("priority", sa.String(length=20), server_default="medium"),
        sa.Column("investigation_findings", sa.Text()),
        sa.Column("substantiated", sa.Boolean()),
        sa.Column("resolution_notes", sa.Text()),
        sa.Column("corrective_actions", postgresql.JSONB()),
        sa.Column("resolved_at", sa.DateTime()),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("legal_review_required", sa.Boolean(), server_default="false"),
        sa.Column("external_legal_aid", sa.Boolean(), server_default="false"),
        sa.Column("legal_aid_contact", postgresql.JSONB()),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["assigned_investigator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["complainant_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["perpetrator_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_discrimination_complaints_org_status",
        "discrimination_complaints",
        ["organization_id", "status"],
    )
    op.create_index(
        "idx_discrimination_complaints_severity",
        "discrimination_complaints",
        ["severity"],
    )
    op.create_index(
        "idx_discrimination_complaints_type",
        "discrimination_complaints",
        ["complaint_type"],
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(
        "idx_discrimination_complaints_type", table_name="discrimination_complaints"
    )
    op.drop_index(
        "idx_discrimination_complaints_severity", table_name="discrimination_complaints"
    )
    op.drop_index(
        "idx_discrimination_complaints_org_status",
        table_name="discrimination_complaints",
    )
    op.drop_table("discrimination_complaints")

    op.drop_index("idx_hiring_metrics_dimension", table_name="hiring_metrics")
    op.drop_index("idx_hiring_metrics_org_period", table_name="hiring_metrics")
    op.drop_table("hiring_metrics")

    op.drop_table("promotion_tracking")

    op.drop_index("idx_pay_equity_analysis", table_name="pay_equity_records")
    op.drop_index("idx_pay_equity_org_dimension", table_name="pay_equity_records")
    op.drop_table("pay_equity_records")

    op.drop_index("idx_equity_analyses_date", table_name="equity_analyses")
    op.drop_index("idx_equity_analyses_severity", table_name="equity_analyses")
    op.drop_index("idx_equity_analyses_org_type", table_name="equity_analyses")
    op.drop_table("equity_analyses")

    op.drop_index("idx_demographic_profiles_org", table_name="demographic_profiles")
    op.drop_index("idx_demographic_profiles_user", table_name="demographic_profiles")
    op.drop_table("demographic_profiles")
