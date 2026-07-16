from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.community.models import CommunityProductAccess
from app.database import get_db
from app.permissions.dependencies import require_auth
from app.projects.models import Project, ProjectUser
from app.projects.service import get_project_by_slug
from app.shared.errors import NotFoundError, PermissionDeniedError
from app.users.models import User

COMMUNITY_ADMIN_ROLES = ("owner", "admin")
COMMUNITY_PROJECT_SLUG = "global-green-invest"
COMMUNITY_PROJECT_NAME = "GlobalGreenInvest / 🍀 ЗЕЛЁНЫЙ / TG Investor"


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(UTC)


def _comparable_datetime(value: datetime, reference: datetime) -> datetime:
    if value.tzinfo is None and reference.tzinfo is not None:
        return value.replace(tzinfo=reference.tzinfo)
    if value.tzinfo is not None and reference.tzinfo is None:
        return value.replace(tzinfo=None)
    return value


def is_access_until_valid(project_user: ProjectUser, now: datetime | None = None) -> bool:
    if project_user.access_until is None:
        return True
    current = _now(now)
    access_until = _comparable_datetime(project_user.access_until, current)
    return access_until >= current


def is_project_user_banned(project_user: ProjectUser) -> bool:
    return project_user.moderation_state == "banned"


def is_project_access_active(project_user: ProjectUser, now: datetime | None = None) -> bool:
    return (
        project_user.status == "active"
        and project_user.access_state == "active"
        and is_access_until_valid(project_user, now=now)
    )


def get_community_project(db: Session) -> Project | None:
    return get_project_by_slug(db, COMMUNITY_PROJECT_SLUG)


def require_community_project_user(
    user: Annotated[User, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectUser:
    project = get_community_project(db)
    if project is None or not project.is_active:
        raise PermissionDeniedError("Community project access is required")
    project_user = (
        db.query(ProjectUser)
        .filter(ProjectUser.user_id == user.id, ProjectUser.project_id == project.id)
        .one_or_none()
    )
    if project_user is None or project_user.status != "active":
        raise PermissionDeniedError("Active community project access is required")
    return project_user


def require_not_banned(
    project_user: Annotated[ProjectUser, Depends(require_community_project_user)],
) -> ProjectUser:
    if is_project_user_banned(project_user):
        raise PermissionDeniedError("Community access is restricted")
    return project_user


def require_active_community_access(
    project_user: Annotated[ProjectUser, Depends(require_not_banned)],
) -> ProjectUser:
    require_not_banned(project_user)
    if not is_project_access_active(project_user):
        raise PermissionDeniedError("Active community access is required")
    return project_user


def is_community_admin(project_user: ProjectUser) -> bool:
    return project_user.role in COMMUNITY_ADMIN_ROLES


def require_community_admin(
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> ProjectUser:
    require_active_community_access(project_user)
    if not is_community_admin(project_user):
        raise PermissionDeniedError("Community admin access is required")
    return project_user


def assert_same_project(entity_project_id: UUID, current_project_id: UUID) -> None:
    if entity_project_id != current_project_id:
        raise NotFoundError("Resource was not found")


def require_same_project(entity: object, project_id: UUID) -> object:
    entity_project_id = getattr(entity, "project_id", None)
    if not isinstance(entity_project_id, UUID):
        raise NotFoundError("Resource was not found")
    assert_same_project(entity_project_id, project_id)
    return entity


def is_published_content(entity: object, now: datetime | None = None) -> bool:
    if getattr(entity, "status", None) != "published":
        return False
    if getattr(entity, "published_at", None) is None:
        return False

    scheduled_at = getattr(entity, "scheduled_at", None)
    if scheduled_at is None:
        return True

    current = _now(now)
    scheduled_at = _comparable_datetime(scheduled_at, current)
    return scheduled_at <= current


def require_published_content(entity: object) -> object:
    if not is_published_content(entity):
        raise NotFoundError("Content was not found")
    return entity


def has_active_product_access(
    db: Session,
    project_id: UUID,
    project_user_id: UUID,
    product_id: UUID,
    now: datetime | None = None,
) -> bool:
    access = (
        db.query(CommunityProductAccess)
        .filter(
            CommunityProductAccess.project_id == project_id,
            CommunityProductAccess.project_user_id == project_user_id,
            CommunityProductAccess.product_id == product_id,
        )
        .one_or_none()
    )
    if access is None or access.access_state != "active":
        return False
    if access.access_until is None:
        return True

    current = _now(now)
    access_until = _comparable_datetime(access.access_until, current)
    return access_until >= current


def require_product_access(
    product_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> ProjectUser:
    if not has_active_product_access(db, project_user.project_id, project_user.id, product_id):
        raise PermissionDeniedError("Active product access is required")
    return project_user
