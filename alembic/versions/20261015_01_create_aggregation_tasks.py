"""create aggregation tasks table

Revision ID: 20261015_01
Revises:
Create Date: 2026-10-15
"""

from alembic import op
import sqlalchemy as sa

revision = "20261015_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aggregation_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_urls", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "completed", "failed", name="task_status", native_enum=False),
            nullable=False,
        ),
        sa.Column("urls_total", sa.Integer(), nullable=False),
        sa.Column("urls_processed", sa.Integer(), nullable=False),
        sa.Column("metrics_generated", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_aggregation_tasks_status", "aggregation_tasks", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_aggregation_tasks_status", table_name="aggregation_tasks")
    op.drop_table("aggregation_tasks")
