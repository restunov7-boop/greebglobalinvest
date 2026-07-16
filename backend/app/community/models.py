from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.projects.models import Project, ProjectUser
from app.shared.db import TimestampMixin

COMMUNITY_CONTENT_STATUSES = ("draft", "scheduled", "published", "hidden")
COMMUNITY_TARGET_TYPES = ("post", "insight")
COMMUNITY_REACTION_TYPES = ("useful",)
COMMUNITY_NOTIFICATION_TYPES = ("urgent_insight", "system", "access")
COMMUNITY_NOTIFICATION_PROCESSING_STATUSES = ("pending", "mock_sent", "sent", "skipped", "failed")
COMMUNITY_PROJECT_LINK_TYPES = ("support", "telegram_bot", "website", "blogger_telegram")
COMMUNITY_PRODUCT_ACCESS_DURATION_TYPES = ("lifetime", "fixed_until", "custom")
COMMUNITY_PRODUCT_MATERIAL_TYPES = ("text", "link", "file_view", "external_site")
COMMUNITY_PRODUCT_ACCESS_STATES = ("active", "expired", "revoked")
COMMUNITY_PRODUCT_ACCESS_SOURCES = ("manual", "legacy_import", "csv_import", "sql_import", "future_payment")
COMMUNITY_PRODUCT_PURCHASE_REQUEST_STATUSES = ("new", "contacted", "approved", "rejected", "cancelled")

PRODUCT_ACCESS_DURATION_LIFETIME = "lifetime"
PRODUCT_MATERIAL_TYPE_TEXT = "text"
PRODUCT_ACCESS_STATE_ACTIVE = "active"
PRODUCT_ACCESS_SOURCE_MANUAL = "manual"


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CommunityPost(TimestampMixin, Base):
    __tablename__ = "community_posts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    author_project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", server_default="draft", nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    project: Mapped[Project] = relationship()
    author_project_user: Mapped[ProjectUser] = relationship()

    __table_args__ = (
        CheckConstraint(
            "status in ('draft', 'scheduled', 'published', 'hidden')",
            name="ck_community_posts_status",
        ),
    )


class CommunityInsight(TimestampMixin, Base):
    __tablename__ = "community_insights"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    author_project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", server_default="draft", nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    telegram_notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship()
    author_project_user: Mapped[ProjectUser] = relationship()

    __table_args__ = (
        CheckConstraint(
            "status in ('draft', 'scheduled', 'published', 'hidden')",
            name="ck_community_insights_status",
        ),
    )


class CommunityReaction(CreatedAtMixin, Base):
    __tablename__ = "community_reactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    reaction_type: Mapped[str] = mapped_column(String(32), nullable=False)

    project: Mapped[Project] = relationship()
    project_user: Mapped[ProjectUser] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "project_user_id",
            "target_type",
            "target_id",
            "reaction_type",
            name="uq_community_reactions_project_user_target_reaction",
        ),
        CheckConstraint("target_type in ('post', 'insight')", name="ck_community_reactions_target_type"),
        CheckConstraint("reaction_type = 'useful'", name="ck_community_reactions_reaction_type"),
    )


class CommunityContentRead(Base):
    __tablename__ = "community_content_reads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project: Mapped[Project] = relationship()
    project_user: Mapped[ProjectUser] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "project_user_id",
            "content_type",
            "content_id",
            name="uq_community_content_reads_project_user_content",
        ),
        CheckConstraint("content_type in ('post', 'insight')", name="ck_community_content_reads_content_type"),
    )


class CommunityChatLink(TimestampMixin, Base):
    __tablename__ = "community_chat_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_by_project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project: Mapped[Project] = relationship()
    created_by_project_user: Mapped[ProjectUser] = relationship()


class CommunityExchange(TimestampMixin, Base):
    __tablename__ = "community_exchanges"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    team_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    external_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    promo_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_by_project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project: Mapped[Project] = relationship()
    created_by_project_user: Mapped[ProjectUser] = relationship()


class CommunityNotification(CreatedAtMixin, Base):
    __tablename__ = "community_notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(32), default="pending", server_default="pending", nullable=False, index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    mock_message_id: Mapped[str | None] = mapped_column(String(120), nullable=True)

    project: Mapped[Project] = relationship()
    project_user: Mapped[ProjectUser] = relationship()

    __table_args__ = (
        CheckConstraint("type in ('urgent_insight', 'system', 'access')", name="ck_community_notifications_type"),
        CheckConstraint(
            "processing_status in ('pending', 'mock_sent', 'sent', 'skipped', 'failed')",
            name="ck_community_notifications_processing_status",
        ),
    )


class CommunityNotificationSetting(TimestampMixin, Base):
    __tablename__ = "community_notification_settings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    project: Mapped[Project] = relationship()
    project_user: Mapped[ProjectUser] = relationship()

    __table_args__ = (
        UniqueConstraint("project_id", "project_user_id", name="uq_community_notification_settings_project_user"),
    )


class CommunityProjectLink(TimestampMixin, Base):
    __tablename__ = "community_project_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    project: Mapped[Project] = relationship()

    __table_args__ = (
        CheckConstraint(
            "type in ('support', 'telegram_bot', 'website', 'blogger_telegram')",
            name="ck_community_project_links_type",
        ),
    )


class CommunityProjectPage(TimestampMixin, Base):
    __tablename__ = "community_project_pages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    project: Mapped[Project] = relationship()

    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_community_project_pages_project_slug"),
    )


class CommunityAdminAuditLog(CreatedAtMixin, Base):
    __tablename__ = "community_admin_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    project: Mapped[Project] = relationship()
    actor_project_user: Mapped[ProjectUser] = relationship()


class CommunityProduct(TimestampMixin, Base):
    __tablename__ = "community_products"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    price_usd: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    price_rub: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False, index=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    access_duration_type: Mapped[str] = mapped_column(
        String(32),
        default=PRODUCT_ACCESS_DURATION_LIFETIME,
        server_default=PRODUCT_ACCESS_DURATION_LIFETIME,
        nullable=False,
    )
    created_by_project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    project: Mapped[Project] = relationship()
    created_by_project_user: Mapped[ProjectUser] = relationship()

    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_community_products_project_slug"),
        CheckConstraint(
            "access_duration_type in ('lifetime', 'fixed_until', 'custom')",
            name="ck_community_products_access_duration_type",
        ),
        Index("ix_community_products_project_published", "project_id", "is_published"),
    )


class CommunityProductMaterial(TimestampMixin, Base):
    __tablename__ = "community_product_materials"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("community_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    material_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    project: Mapped[Project] = relationship()
    product: Mapped[CommunityProduct] = relationship()

    __table_args__ = (
        CheckConstraint(
            "material_type in ('text', 'link', 'file_view', 'external_site')",
            name="ck_community_product_materials_material_type",
        ),
        Index("ix_community_product_materials_project_product", "project_id", "product_id"),
    )


class CommunityProductAccess(TimestampMixin, Base):
    __tablename__ = "community_product_access"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("community_products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    access_state: Mapped[str] = mapped_column(
        String(32),
        default=PRODUCT_ACCESS_STATE_ACTIVE,
        server_default=PRODUCT_ACCESS_STATE_ACTIVE,
        nullable=False,
    )
    access_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(
        String(32),
        default=PRODUCT_ACCESS_SOURCE_MANUAL,
        server_default=PRODUCT_ACCESS_SOURCE_MANUAL,
        nullable=False,
    )
    granted_by_project_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("project_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    project: Mapped[Project] = relationship()
    product: Mapped[CommunityProduct] = relationship()
    project_user: Mapped[ProjectUser] = relationship(foreign_keys=[project_user_id])
    granted_by_project_user: Mapped[ProjectUser | None] = relationship(foreign_keys=[granted_by_project_user_id])

    __table_args__ = (
        UniqueConstraint("project_id", "product_id", "project_user_id", name="uq_community_product_access_project_product_user"),
        CheckConstraint(
            "access_state in ('active', 'expired', 'revoked')",
            name="ck_community_product_access_access_state",
        ),
        CheckConstraint(
            "source in ('manual', 'legacy_import', 'csv_import', 'sql_import', 'future_payment')",
            name="ck_community_product_access_source",
        ),
        Index("ix_community_product_access_project_user", "project_id", "project_user_id"),
        Index("ix_community_product_access_project_product", "project_id", "product_id"),
    )


class CommunityProductPurchaseRequest(TimestampMixin, Base):
    __tablename__ = "community_product_purchase_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", name="fk_cpr_project_id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("community_products.id", name="fk_cpr_product_id", ondelete="CASCADE"),
        nullable=False,
    )
    project_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("project_users.id", name="fk_cpr_project_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), default="new", server_default="new", nullable=False)
    contact_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contact_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    handled_by_project_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("project_users.id", name="fk_cpr_handled_by_pu_id", ondelete="SET NULL"),
        nullable=True,
    )
    handled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship()
    product: Mapped[CommunityProduct] = relationship()
    project_user: Mapped[ProjectUser] = relationship(foreign_keys=[project_user_id])
    handled_by_project_user: Mapped[ProjectUser | None] = relationship(foreign_keys=[handled_by_project_user_id])

    __table_args__ = (
        CheckConstraint(
            "status in ('new', 'contacted', 'approved', 'rejected', 'cancelled')",
            name="ck_cpr_status",
        ),
        Index("ix_cpr_project_status_created", "project_id", "status", "created_at"),
        Index("ix_cpr_project_product", "project_id", "product_id"),
        Index("ix_cpr_project_user", "project_id", "project_user_id"),
        Index("ix_cpr_project_id", "project_id"),
        Index("ix_cpr_product_id", "product_id"),
        Index("ix_cpr_project_user_id", "project_user_id"),
        Index("ix_cpr_status", "status"),
        Index("ix_cpr_handled_by_pu", "handled_by_project_user_id"),
    )
