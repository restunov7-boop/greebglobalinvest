"""community product purchase requests

Revision ID: 202607020005
Revises: 202607020004
Create Date: 2026-07-02 00:05:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607020005"
down_revision: str | None = "202607020004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_product_purchase_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("project_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="new", nullable=False),
        sa.Column("contact_method", sa.String(length=32), nullable=True),
        sa.Column("contact_value", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("admin_note", sa.Text(), nullable=True),
        sa.Column("handled_by_project_user_id", sa.Uuid(), nullable=True),
        sa.Column("handled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status in ('new', 'contacted', 'approved', 'rejected', 'cancelled')",
            name="ck_cpr_status",
        ),
        sa.ForeignKeyConstraint(["handled_by_project_user_id"], ["project_users.id"], name="fk_cpr_handled_by_pu_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["community_products.id"], name="fk_cpr_product_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_cpr_project_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_user_id"], ["project_users.id"], name="fk_cpr_project_user_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_cpr_project_status_created",
        "community_product_purchase_requests",
        ["project_id", "status", "created_at"],
    )
    op.create_index(
        "ix_cpr_project_product",
        "community_product_purchase_requests",
        ["project_id", "product_id"],
    )
    op.create_index(
        "ix_cpr_project_user",
        "community_product_purchase_requests",
        ["project_id", "project_user_id"],
    )
    op.create_index(
        "ix_cpr_project_id",
        "community_product_purchase_requests",
        ["project_id"],
    )
    op.create_index(
        "ix_cpr_product_id",
        "community_product_purchase_requests",
        ["product_id"],
    )
    op.create_index(
        "ix_cpr_project_user_id",
        "community_product_purchase_requests",
        ["project_user_id"],
    )
    op.create_index(
        "ix_cpr_status",
        "community_product_purchase_requests",
        ["status"],
    )
    op.create_index(
        "ix_cpr_handled_by_pu",
        "community_product_purchase_requests",
        ["handled_by_project_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_cpr_handled_by_pu", table_name="community_product_purchase_requests")
    op.drop_index("ix_cpr_status", table_name="community_product_purchase_requests")
    op.drop_index("ix_cpr_project_user_id", table_name="community_product_purchase_requests")
    op.drop_index("ix_cpr_product_id", table_name="community_product_purchase_requests")
    op.drop_index("ix_cpr_project_id", table_name="community_product_purchase_requests")
    op.drop_index("ix_cpr_project_user", table_name="community_product_purchase_requests")
    op.drop_index("ix_cpr_project_product", table_name="community_product_purchase_requests")
    op.drop_index("ix_cpr_project_status_created", table_name="community_product_purchase_requests")
    op.drop_table("community_product_purchase_requests")
