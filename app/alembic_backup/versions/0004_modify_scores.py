"""modify scores table - add normalized flag"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("scores", sa.Column("is_normalized", sa.Boolean(), server_default=sa.text("false")))

def downgrade():
    op.drop_column("scores", "is_normalized")
