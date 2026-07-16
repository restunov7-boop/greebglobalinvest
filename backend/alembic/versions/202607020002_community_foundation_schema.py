"""community foundation schema

Revision ID: 202607020002
Revises: 202607020001
Create Date: 2026-07-02 00:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202607020002"
down_revision: str | None = "202607020001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "community_posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("author_project_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status in ('draft', 'scheduled', 'published', 'hidden')",
            name="ck_community_posts_status",
        ),
        sa.ForeignKeyConstraint(["author_project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_posts_project_id", "community_posts", ["project_id"])
    op.create_index(
        "ix_community_posts_author_project_user_id",
        "community_posts",
        ["author_project_user_id"],
    )

    op.create_table(
        "community_insights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("author_project_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_urgent", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("telegram_notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status in ('draft', 'scheduled', 'published', 'hidden')",
            name="ck_community_insights_status",
        ),
        sa.ForeignKeyConstraint(["author_project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_insights_project_id", "community_insights", ["project_id"])
    op.create_index(
        "ix_community_insights_author_project_user_id",
        "community_insights",
        ["author_project_user_id"],
    )

    op.create_table(
        "community_reactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("project_user_id", sa.Uuid(), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("reaction_type", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("reaction_type = 'useful'", name="ck_community_reactions_reaction_type"),
        sa.CheckConstraint("target_type in ('post', 'insight')", name="ck_community_reactions_target_type"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "project_user_id",
            "target_type",
            "target_id",
            "reaction_type",
            name="uq_community_reactions_project_user_target_reaction",
        ),
    )
    op.create_index("ix_community_reactions_project_id", "community_reactions", ["project_id"])
    op.create_index("ix_community_reactions_project_user_id", "community_reactions", ["project_user_id"])
    op.create_index("ix_community_reactions_target_id", "community_reactions", ["target_id"])

    op.create_table(
        "community_content_reads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("project_user_id", sa.Uuid(), nullable=False),
        sa.Column("content_type", sa.String(length=32), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("content_type in ('post', 'insight')", name="ck_community_content_reads_content_type"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "project_id",
            "project_user_id",
            "content_type",
            "content_id",
            name="uq_community_content_reads_project_user_content",
        ),
    )
    op.create_index("ix_community_content_reads_project_id", "community_content_reads", ["project_id"])
    op.create_index("ix_community_content_reads_project_user_id", "community_content_reads", ["project_user_id"])
    op.create_index("ix_community_content_reads_content_id", "community_content_reads", ["content_id"])

    op.create_table(
        "community_chat_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("telegram_url", sa.String(length=1024), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_by_project_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_chat_links_project_id", "community_chat_links", ["project_id"])
    op.create_index(
        "ix_community_chat_links_created_by_project_user_id",
        "community_chat_links",
        ["created_by_project_user_id"],
    )

    op.create_table(
        "community_exchanges",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("team_comment", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=1024), nullable=True),
        sa.Column("external_url", sa.String(length=1024), nullable=False),
        sa.Column("promo_code", sa.String(length=120), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_by_project_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_exchanges_project_id", "community_exchanges", ["project_id"])
    op.create_index(
        "ix_community_exchanges_created_by_project_user_id",
        "community_exchanges",
        ["created_by_project_user_id"],
    )

    op.create_table(
        "community_notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("project_user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(length=32), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("type in ('urgent_insight', 'system', 'access')", name="ck_community_notifications_type"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_notifications_project_id", "community_notifications", ["project_id"])
    op.create_index("ix_community_notifications_project_user_id", "community_notifications", ["project_user_id"])
    op.create_index("ix_community_notifications_target_id", "community_notifications", ["target_id"])

    op.create_table(
        "community_notification_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("project_user_id", sa.Uuid(), nullable=False),
        sa.Column("notifications_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "project_user_id", name="uq_community_notification_settings_project_user"),
    )
    op.create_index(
        "ix_community_notification_settings_project_id",
        "community_notification_settings",
        ["project_id"],
    )
    op.create_index(
        "ix_community_notification_settings_project_user_id",
        "community_notification_settings",
        ["project_user_id"],
    )

    op.create_table(
        "community_project_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "type in ('support', 'telegram_bot', 'website', 'blogger_telegram')",
            name="ck_community_project_links_type",
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_project_links_project_id", "community_project_links", ["project_id"])

    op.create_table(
        "community_project_pages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "slug", name="uq_community_project_pages_project_slug"),
    )
    op.create_index("ix_community_project_pages_project_id", "community_project_pages", ["project_id"])

    op.create_table(
        "community_admin_audit_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("actor_project_user_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_project_user_id"], ["project_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_admin_audit_log_project_id", "community_admin_audit_log", ["project_id"])
    op.create_index(
        "ix_community_admin_audit_log_actor_project_user_id",
        "community_admin_audit_log",
        ["actor_project_user_id"],
    )
    op.create_index("ix_community_admin_audit_log_entity_id", "community_admin_audit_log", ["entity_id"])


def downgrade() -> None:
    op.drop_index("ix_community_admin_audit_log_entity_id", table_name="community_admin_audit_log")
    op.drop_index("ix_community_admin_audit_log_actor_project_user_id", table_name="community_admin_audit_log")
    op.drop_index("ix_community_admin_audit_log_project_id", table_name="community_admin_audit_log")
    op.drop_table("community_admin_audit_log")

    op.drop_index("ix_community_project_pages_project_id", table_name="community_project_pages")
    op.drop_table("community_project_pages")

    op.drop_index("ix_community_project_links_project_id", table_name="community_project_links")
    op.drop_table("community_project_links")

    op.drop_index(
        "ix_community_notification_settings_project_user_id",
        table_name="community_notification_settings",
    )
    op.drop_index("ix_community_notification_settings_project_id", table_name="community_notification_settings")
    op.drop_table("community_notification_settings")

    op.drop_index("ix_community_notifications_target_id", table_name="community_notifications")
    op.drop_index("ix_community_notifications_project_user_id", table_name="community_notifications")
    op.drop_index("ix_community_notifications_project_id", table_name="community_notifications")
    op.drop_table("community_notifications")

    op.drop_index("ix_community_exchanges_created_by_project_user_id", table_name="community_exchanges")
    op.drop_index("ix_community_exchanges_project_id", table_name="community_exchanges")
    op.drop_table("community_exchanges")

    op.drop_index("ix_community_chat_links_created_by_project_user_id", table_name="community_chat_links")
    op.drop_index("ix_community_chat_links_project_id", table_name="community_chat_links")
    op.drop_table("community_chat_links")

    op.drop_index("ix_community_content_reads_content_id", table_name="community_content_reads")
    op.drop_index("ix_community_content_reads_project_user_id", table_name="community_content_reads")
    op.drop_index("ix_community_content_reads_project_id", table_name="community_content_reads")
    op.drop_table("community_content_reads")

    op.drop_index("ix_community_reactions_target_id", table_name="community_reactions")
    op.drop_index("ix_community_reactions_project_user_id", table_name="community_reactions")
    op.drop_index("ix_community_reactions_project_id", table_name="community_reactions")
    op.drop_table("community_reactions")

    op.drop_index("ix_community_insights_author_project_user_id", table_name="community_insights")
    op.drop_index("ix_community_insights_project_id", table_name="community_insights")
    op.drop_table("community_insights")

    op.drop_index("ix_community_posts_author_project_user_id", table_name="community_posts")
    op.drop_index("ix_community_posts_project_id", table_name="community_posts")
    op.drop_table("community_posts")

