"""project user access model

Revision ID: 202607020001
Revises: 202606300002
Create Date: 2026-07-02 00:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607020001"
down_revision: str | None = "202606300002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("project_users") as batch_op:
        batch_op.add_column(
            sa.Column("access_state", sa.String(length=32), server_default="active", nullable=False),
        )
        batch_op.add_column(
            sa.Column("access_until", sa.DateTime(timezone=True), nullable=True),
        )
        batch_op.add_column(
            sa.Column("moderation_state", sa.String(length=32), server_default="normal", nullable=False),
        )
        batch_op.create_check_constraint(
            "ck_project_users_access_state",
            "access_state in ('pending', 'active', 'expired', 'revoked')",
        )
        batch_op.create_check_constraint(
            "ck_project_users_moderation_state",
            "moderation_state in ('normal', 'banned')",
        )
    op.execute("UPDATE project_users SET access_state = 'active' WHERE access_state IS NULL")
    op.execute("UPDATE project_users SET moderation_state = 'normal' WHERE moderation_state IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("project_users") as batch_op:
        batch_op.drop_constraint("ck_project_users_moderation_state", type_="check")
        batch_op.drop_constraint("ck_project_users_access_state", type_="check")
        batch_op.drop_column("moderation_state")
        batch_op.drop_column("access_until")
        batch_op.drop_column("access_state")
