"""community product schema

Revision ID: 202607020003
Revises: 202607020002
Create Date: 2026-07-02 00:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607020003"
down_revision: str | None = "202607020002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_products",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("cover_url", sa.String(length=1024), nullable=True),
        sa.Column("price_usd", sa.Numeric(12, 2), nullable=True),
        sa.Column("price_rub", sa.Numeric(12, 2), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("access_duration_type", sa.String(length=32), server_default="lifetime", nullable=False),
        sa.Column("created_by_project_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "access_duration_type in ('lifetime', 'fixed_until', 'custom')",
            name="ck_community_products_access_duration_type",
        ),
        sa.ForeignKeyConstraint(["created_by_project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "slug", name="uq_community_products_project_slug"),
    )
    op.create_index("ix_community_products_project_id", "community_products", ["project_id"])
    op.create_index("ix_community_products_project_published", "community_products", ["project_id", "is_published"])
    op.create_index("ix_community_products_sort_order", "community_products", ["sort_order"])
    op.create_index(
        "ix_community_products_created_by_project_user_id",
        "community_products",
        ["created_by_project_user_id"],
    )

    op.create_table(
        "community_product_materials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("material_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("file_url", sa.String(length=1024), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_locked", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "material_type in ('text', 'link', 'file_view', 'external_site')",
            name="ck_community_product_materials_material_type",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["community_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_product_materials_project_id", "community_product_materials", ["project_id"])
    op.create_index("ix_community_product_materials_product_id", "community_product_materials", ["product_id"])
    op.create_index(
        "ix_community_product_materials_project_product",
        "community_product_materials",
        ["project_id", "product_id"],
    )
    op.create_index("ix_community_product_materials_deleted_at", "community_product_materials", ["deleted_at"])

    op.create_table(
        "community_product_access",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("project_user_id", sa.Uuid(), nullable=False),
        sa.Column("access_state", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("access_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("granted_by_project_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "access_state in ('active', 'expired', 'revoked')",
            name="ck_community_product_access_access_state",
        ),
        sa.CheckConstraint(
            "source in ('manual', 'legacy_import', 'csv_import', 'sql_import', 'future_payment')",
            name="ck_community_product_access_source",
        ),
        sa.ForeignKeyConstraint(["granted_by_project_user_id"], ["project_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["community_products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "product_id",
            "project_user_id",
            name="uq_community_product_access_project_product_user",
        ),
    )
    op.create_index("ix_community_product_access_project_id", "community_product_access", ["project_id"])
    op.create_index("ix_community_product_access_product_id", "community_product_access", ["product_id"])
    op.create_index("ix_community_product_access_project_user_id", "community_product_access", ["project_user_id"])
    op.create_index(
        "ix_community_product_access_project_user",
        "community_product_access",
        ["project_id", "project_user_id"],
    )
    op.create_index(
        "ix_community_product_access_project_product",
        "community_product_access",
        ["project_id", "product_id"],
    )
    op.create_index(
        "ix_community_product_access_granted_by_project_user_id",
        "community_product_access",
        ["granted_by_project_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_community_product_access_granted_by_project_user_id", table_name="community_product_access")
    op.drop_index("ix_community_product_access_project_product", table_name="community_product_access")
    op.drop_index("ix_community_product_access_project_user", table_name="community_product_access")
    op.drop_index("ix_community_product_access_project_user_id", table_name="community_product_access")
    op.drop_index("ix_community_product_access_product_id", table_name="community_product_access")
    op.drop_index("ix_community_product_access_project_id", table_name="community_product_access")
    op.drop_table("community_product_access")

    op.drop_index("ix_community_product_materials_deleted_at", table_name="community_product_materials")
    op.drop_index("ix_community_product_materials_project_product", table_name="community_product_materials")
    op.drop_index("ix_community_product_materials_product_id", table_name="community_product_materials")
    op.drop_index("ix_community_product_materials_project_id", table_name="community_product_materials")
    op.drop_table("community_product_materials")

    op.drop_index("ix_community_products_created_by_project_user_id", table_name="community_products")
    op.drop_index("ix_community_products_sort_order", table_name="community_products")
    op.drop_index("ix_community_products_project_published", table_name="community_products")
    op.drop_index("ix_community_products_project_id", table_name="community_products")
    op.drop_table("community_products")

