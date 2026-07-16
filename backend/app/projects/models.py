from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.db import TimestampMixin


PROJECT_USER_ROLES = ("member", "moderator", "admin", "owner")
PROJECT_USER_STATUSES = ("active", "blocked", "left")
PROJECT_USER_ACCESS_STATES = ("pending", "active", "expired", "revoked")
PROJECT_USER_MODERATION_STATES = ("normal", "banned")


class Project(TimestampMixin, Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    project_users: Mapped[list[ProjectUser]] = relationship(back_populates="project")

    __table_args__ = (UniqueConstraint("slug", name="uq_projects_slug"),)


class ProjectUser(TimestampMixin, Base):
    __tablename__ = "project_users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="member", server_default="member", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_state: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    access_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderation_state: Mapped[str] = mapped_column(String(32), default="normal", server_default="normal", nullable=False)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    onboarding_data_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    privacy_settings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notification_settings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    project: Mapped[Project] = relationship(back_populates="project_users")

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_project_users_user_project"),
        CheckConstraint(
            "role in ('member', 'moderator', 'admin', 'owner')",
            name="ck_project_users_role",
        ),
        CheckConstraint(
            "status in ('active', 'blocked', 'left')",
            name="ck_project_users_status",
        ),
        CheckConstraint(
            "access_state in ('pending', 'active', 'expired', 'revoked')",
            name="ck_project_users_access_state",
        ),
        CheckConstraint(
            "moderation_state in ('normal', 'banned')",
            name="ck_project_users_moderation_state",
        ),
    )
