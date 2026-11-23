"""Add durable review jobs, pull request identities, findings and feedback."""

from alembic import op
import sqlalchemy as sa

revision = "0002_automation"
down_revision = "0001_legacy"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "automation_repositories",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column("installation_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(250), nullable=False),
    )
    op.create_table(
        "automation_pull_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository_id", sa.BigInteger(), sa.ForeignKey("automation_repositories.id"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.UniqueConstraint("repository_id", "number"),
    )
    op.create_table(
        "automation_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pull_request_id", sa.Integer(), sa.ForeignKey("automation_pull_requests.id")),
        sa.Column("delivery", sa.String(80), unique=True),
        sa.Column("head_sha", sa.String(40)),
        sa.Column("base_sha", sa.String(40)),
        sa.Column("policy", sa.String(80), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON()),
        sa.Column("result", sa.JSON()),
        sa.Column("error", sa.String(300)),
        sa.Column("lease", sa.String(36)),
        sa.Column("available_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("pull_request_id", "head_sha", "base_sha", "policy"),
    )
    op.create_index("ix_automation_jobs_owner_id", "automation_jobs", ["owner_id"])
    op.create_index("ix_automation_jobs_dispatch", "automation_jobs", ["status", "available_at"])
    op.create_table(
        "automation_findings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("automation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("rule_id", sa.String(200), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("line", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("evidence_sha256", sa.String(64), nullable=False),
        sa.Column("suppressed", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_automation_findings_job_id", "automation_findings", ["job_id"])
    op.create_table(
        "automation_feedback",
        sa.Column("finding_id", sa.Integer(), sa.ForeignKey("automation_findings.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("verdict", sa.String(20), nullable=False),
    )


def downgrade():
    for table in ("automation_feedback", "automation_findings", "automation_jobs",
                  "automation_pull_requests", "automation_repositories"):
        op.drop_table(table)
