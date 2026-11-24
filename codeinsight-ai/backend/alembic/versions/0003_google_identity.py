"""Store Google account subjects independently of email addresses."""
from alembic import op
import sqlalchemy as sa

revision = "0003_google_identity"
down_revision = "0002_automation"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("google_subject", sa.String(255), nullable=True))
    op.create_index("ix_users_google_subject", "users", ["google_subject"], unique=True)


def downgrade():
    op.drop_index("ix_users_google_subject", table_name="users")
    op.drop_column("users", "google_subject")
