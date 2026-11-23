"""Baseline for existing CodeInsight AI tables."""

from alembic import op
import sqlalchemy as sa

revision = "0001_legacy"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=True),
        sa.Column("github_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_github_id", "users", ["github_id"], unique=True)
    op.create_table(
        "settings",
        sa.Column("user_id", sa.String(), primary_key=True),
        sa.Column("dark_mode", sa.Boolean(), nullable=False),
        sa.Column("email_notifications", sa.Boolean(), nullable=False),
        sa.Column("preferred_ai_model", sa.String(), nullable=False),
        sa.Column("preferred_language", sa.String(), nullable=False),
    )
    op.create_table(
        "reviews",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("review_type", sa.String(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])


def downgrade():
    op.drop_table("reviews")
    op.drop_table("settings")
    op.drop_table("users")
