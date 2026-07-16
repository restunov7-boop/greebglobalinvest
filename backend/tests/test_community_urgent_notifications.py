from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.community.models import CommunityNotification, CommunityNotificationSetting
from app.community.permissions import COMMUNITY_PROJECT_SLUG
from app.config import settings
from app.database import SessionLocal
from app.projects.models import Project, ProjectUser
from app.projects.service import get_project_by_slug
from app.users.models import TelegramIdentity, User
from tests.conftest import login


def _community_project():
    db = SessionLocal()
    try:
        project = get_project_by_slug(db, COMMUNITY_PROJECT_SLUG)
        assert project is not None
        return project
    finally:
        db.close()


def _current_project_user() -> ProjectUser:
    db = SessionLocal()
    try:
        project = get_project_by_slug(db, COMMUNITY_PROJECT_SLUG)
        assert project is not None
        project_user = (
            db.query(ProjectUser)
            .join(TelegramIdentity, TelegramIdentity.user_id == ProjectUser.user_id)
            .filter(
                ProjectUser.project_id == project.id,
                TelegramIdentity.telegram_id == settings.dev_telegram_id,
            )
            .one()
        )
        return project_user
    finally:
        db.close()


def _set_current_project_user(role: str = "admin", moderation_state: str = "normal") -> None:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project_user.role = role
        project_user.status = "active"
        project_user.access_state = "active"
        project_user.moderation_state = moderation_state
        project_user.access_until = datetime.now(UTC) + timedelta(days=30)
        db.commit()
    finally:
        db.close()


def _create_target_user(
    username: str,
    *,
    access_state: str = "active",
    moderation_state: str = "normal",
    with_telegram: bool = True,
    notifications_enabled: bool | None = None,
    project_id: UUID | None = None,
):
    db = SessionLocal()
    try:
        if project_id is None:
            selected_project = db.merge(_community_project())
        else:
            selected_project = db.query(Project).filter(Project.id == project_id).one()
        user = User(display_name=username, is_active=True)
        db.add(user)
        db.flush()
        if with_telegram:
            db.add(
                TelegramIdentity(
                    user_id=user.id,
                    telegram_id=f"tg_{username}",
                    username=username,
                    first_name=username,
                    auth_date=datetime.now(UTC),
                )
            )
        project_user = ProjectUser(
            user_id=user.id,
            project_id=selected_project.id,
            role="member",
            status="active",
            is_premium=False,
            access_state=access_state,
            access_until=datetime.now(UTC) + timedelta(days=30) if access_state == "active" else None,
            moderation_state=moderation_state,
        )
        db.add(project_user)
        db.flush()
        if notifications_enabled is not None:
            db.add(
                CommunityNotificationSetting(
                    project_id=selected_project.id,
                    project_user_id=project_user.id,
                    notifications_enabled=notifications_enabled,
                )
            )
        project_user_id = project_user.id
        db.commit()
        return project_user_id
    finally:
        db.close()


def _notification_count(insight_id: str | None = None) -> int:
    db = SessionLocal()
    try:
        query = db.query(CommunityNotification)
        if insight_id is not None:
            query = query.filter(CommunityNotification.target_id == UUID(insight_id))
        return query.count()
    finally:
        db.close()


def _has_notification(project_user_id, insight_id: str) -> bool:
    db = SessionLocal()
    try:
        return (
            db.query(CommunityNotification)
            .filter(
                CommunityNotification.project_user_id == project_user_id,
                CommunityNotification.target_id == UUID(insight_id),
                CommunityNotification.type == "urgent_insight",
            )
            .one_or_none()
            is not None
        )
    finally:
        db.close()


def _create_insight(client, headers, *, is_urgent: bool, status: str):
    scheduled_at = (datetime.now(UTC) + timedelta(days=1)).isoformat() if status == "scheduled" else None
    response = client.post(
        "/api/v1/community/admin/insights",
        headers=headers,
        json={
            "title": "Urgent market note",
            "excerpt": "Short excerpt",
            "content": "Longer safe educational content",
            "is_urgent": is_urgent,
            "status": status,
            "scheduled_at": scheduled_at,
            "published_at": None,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_non_urgent_scheduled_and_hidden_insights_create_no_notifications(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    _create_target_user("active_target")

    _create_insight(client, headers, is_urgent=False, status="published")
    _create_insight(client, headers, is_urgent=True, status="scheduled")
    _create_insight(client, headers, is_urgent=True, status="hidden")

    assert _notification_count() == 0


def test_urgent_published_insight_creates_notifications_for_eligible_users(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    target_id = _create_target_user("active_target")

    insight = _create_insight(client, headers, is_urgent=True, status="published")

    assert insight["telegram_notification_sent_at"] is None
    assert insight["urgent_notification_summary"]["notifications_created"] >= 1
    assert insight["urgent_notification_summary"]["telegram_jobs_created"] == 0
    assert _has_notification(target_id, insight["id"])


def test_urgent_notifications_respect_settings_access_and_no_telegram(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    disabled_id = _create_target_user("disabled_target", notifications_enabled=False)
    pending_id = _create_target_user("pending_target", access_state="pending")
    banned_id = _create_target_user("banned_target", moderation_state="banned")
    no_telegram_id = _create_target_user("no_telegram_target", with_telegram=False)

    insight = _create_insight(client, headers, is_urgent=True, status="published")
    summary = insight["urgent_notification_summary"]

    assert not _has_notification(disabled_id, insight["id"])
    assert not _has_notification(pending_id, insight["id"])
    assert not _has_notification(banned_id, insight["id"])
    assert _has_notification(no_telegram_id, insight["id"])
    assert summary["skipped_disabled"] == 1
    assert summary["skipped_no_telegram"] >= 1


def test_updating_published_insight_to_urgent_is_idempotent(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    _create_target_user("active_target")
    insight = _create_insight(client, headers, is_urgent=False, status="published")

    first = client.patch(
        f"/api/v1/community/admin/insights/{insight['id']}",
        headers=headers,
        json={"is_urgent": True},
    )
    assert first.status_code == 200, first.text
    first_count = _notification_count(insight["id"])

    second = client.patch(
        f"/api/v1/community/admin/insights/{insight['id']}",
        headers=headers,
        json={"is_urgent": True},
    )
    assert second.status_code == 200, second.text

    assert _notification_count(insight["id"]) == first_count
    assert second.json()["data"]["urgent_notification_summary"] is None


def test_notifications_are_project_scoped_and_visible_to_admin_only(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    foreign_project = Project(slug="foreign-project", name="Foreign", is_active=True)
    db = SessionLocal()
    try:
        db.add(foreign_project)
        db.flush()
        foreign_project_id = foreign_project.id
        db.commit()
    finally:
        db.close()
    foreign_user_id = _create_target_user("foreign_target", project_id=foreign_project_id)

    insight = _create_insight(client, headers, is_urgent=True, status="published")

    assert not _has_notification(foreign_user_id, insight["id"])
    listing = client.get("/api/v1/community/admin/notifications?type=urgent_insight", headers=headers)
    assert listing.status_code == 200, listing.text
    assert listing.json()["data"]["total"] >= 1

    _set_current_project_user(role="member")
    member_listing = client.get("/api/v1/community/admin/notifications", headers=headers)
    assert member_listing.status_code == 403

    _set_current_project_user(role="admin", moderation_state="banned")
    banned_listing = client.get("/api/v1/community/admin/notifications", headers=headers)
    assert banned_listing.status_code == 403
