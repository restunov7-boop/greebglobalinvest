"""community notification processing

Revision ID: 202607020004
Revises: 202607020003
Create Date: 2026-07-02 00:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607020004"
down_revision: str | None = "202607020003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "community_notifications",
        sa.Column("processing_status", sa.String(length=32), server_default="pending", nullable=False),
    )
    op.add_column("community_notifications", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("community_notifications", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column("community_notifications", sa.Column("mock_message_id", sa.String(length=120), nullable=True))
    op.create_index(
        "ix_community_notifications_processing_status",
        "community_notifications",
        ["processing_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_notifications_processing_status", table_name="community_notifications")
    op.drop_column("community_notifications", "mock_message_id")
    op.drop_column("community_notifications", "processing_error")
    op.drop_column("community_notifications", "processed_at")
    op.drop_column("community_notifications", "processing_status")
