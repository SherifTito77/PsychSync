"""add feature_x column to organizations"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("organizations", sa.Column("feature_x", sa.String(), nullable=True))

def downgrade():
    op.drop_column("organizations", "feature_x")
