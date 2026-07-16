from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.community.models import CommunityInsight, CommunityNotification, CommunityNotificationSetting
from app.community.permissions import COMMUNITY_PROJECT_SLUG
from app.community.telegram_sender import compose_urgent_insight_message
from app.database import SessionLocal
from app.main import app
from app.projects.models import Project, ProjectUser
from app.projects.service import ensure_default_project, get_project_by_slug
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
        return db.query(ProjectUser).filter(ProjectUser.project_id == project.id).order_by(ProjectUser.created_at.asc()).first()
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


def _set_current_notifications(enabled: bool) -> None:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        setting = (
            db.query(CommunityNotificationSetting)
            .filter(
                CommunityNotificationSetting.project_id == project_user.project_id,
                CommunityNotificationSetting.project_user_id == project_user.id,
            )
            .one_or_none()
        )
        if setting is None:
            setting = CommunityNotificationSetting(project_id=project_user.project_id, project_user_id=project_user.id)
            db.add(setting)
        setting.notifications_enabled = enabled
        db.commit()
    finally:
        db.close()


def _create_target_user(username: str, *, with_telegram: bool = True) -> UUID:
    db = SessionLocal()
    try:
        project = db.merge(_community_project())
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
            project_id=project.id,
            role="member",
            status="active",
            is_premium=False,
            access_state="active",
            access_until=datetime.now(UTC) + timedelta(days=30),
            moderation_state="normal",
        )
        db.add(project_user)
        db.flush()
        project_user_id = project_user.id
        db.commit()
        return project_user_id
    finally:
        db.close()


def _publish_urgent_insight(client, headers) -> str:
    response = client.post(
        "/api/v1/community/admin/insights",
        headers=headers,
        json={
            "title": "Calm market update",
            "excerpt": "A concise educational note.",
            "content": "No guarantees, only a structured observation.",
            "is_urgent": True,
            "status": "published",
            "scheduled_at": None,
            "published_at": None,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def _set_project_user_state(project_user_id: UUID, *, access_state: str = "active", moderation_state: str = "normal") -> None:
    db = SessionLocal()
    try:
        project_user = db.query(ProjectUser).filter(ProjectUser.id == project_user_id).one()
        project_user.access_state = access_state
        project_user.moderation_state = moderation_state
        if access_state == "expired":
            project_user.access_until = datetime.now(UTC) - timedelta(days=1)
        db.commit()
    finally:
        db.close()


def _set_notification_setting(project_user_id: UUID, enabled: bool) -> None:
    db = SessionLocal()
    try:
        project_user = db.query(ProjectUser).filter(ProjectUser.id == project_user_id).one()
        setting = (
            db.query(CommunityNotificationSetting)
            .filter(
                CommunityNotificationSetting.project_id == project_user.project_id,
                CommunityNotificationSetting.project_user_id == project_user.id,
            )
            .one_or_none()
        )
        if setting is None:
            setting = CommunityNotificationSetting(project_id=project_user.project_id, project_user_id=project_user.id)
            db.add(setting)
        setting.notifications_enabled = enabled
        db.commit()
    finally:
        db.close()


def _notification_for(project_user_id: UUID) -> CommunityNotification:
    db = SessionLocal()
    try:
        notification = (
            db.query(CommunityNotification)
            .filter(CommunityNotification.project_user_id == project_user_id)
            .order_by(CommunityNotification.created_at.desc())
            .first()
        )
        assert notification is not None
        return notification
    finally:
        db.close()


def test_process_pending_marks_notifications_mock_sent_without_token_or_network(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("mock_target")
    _publish_urgent_insight(client, headers)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["processed"] == 1
    assert data["sent_mock"] == 1
    assert data["failed"] == 0
    assert data["remaining_pending"] == 0
    notification = _notification_for(target_id)
    assert notification.processing_status == "mock_sent"
    assert notification.mock_message_id is not None
    assert notification.processed_at is not None


def test_processing_skips_ineligible_disabled_and_missing_telegram_users(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    active_id = _create_target_user("active_target")
    revoked_id = _create_target_user("revoked_target")
    banned_id = _create_target_user("banned_target")
    expired_id = _create_target_user("expired_target")
    disabled_id = _create_target_user("disabled_target")
    no_telegram_id = _create_target_user("no_telegram_target", with_telegram=False)
    _publish_urgent_insight(client, headers)

    _set_project_user_state(revoked_id, access_state="revoked")
    _set_project_user_state(banned_id, moderation_state="banned")
    _set_project_user_state(expired_id, access_state="expired")
    _set_notification_setting(disabled_id, False)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["processed"] == 6
    assert data["sent_mock"] == 1
    assert data["skipped"] == 5
    assert _notification_for(active_id).processing_status == "mock_sent"
    assert _notification_for(revoked_id).processing_status == "skipped"
    assert _notification_for(banned_id).processing_status == "skipped"
    assert _notification_for(expired_id).processing_status == "skipped"
    assert _notification_for(disabled_id).processing_status == "skipped"
    assert _notification_for(no_telegram_id).processing_status == "skipped"


def test_processing_is_idempotent_and_dry_run_does_not_mutate(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("idempotent_target")
    _publish_urgent_insight(client, headers)

    dry_run = client.post(
        "/api/v1/community/admin/notifications/process-pending",
        headers=headers,
        json={"limit": 50, "dry_run": True},
    )
    assert dry_run.status_code == 200, dry_run.text
    assert dry_run.json()["data"]["sent_mock"] == 1
    assert _notification_for(target_id).processing_status == "pending"

    first = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})
    second = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert first.json()["data"]["sent_mock"] == 1
    assert second.json()["data"]["processed"] == 0
    assert second.json()["data"]["remaining_pending"] == 0


def test_processing_permissions_block_member_banned_and_wine_only_admin(client):
    headers = login(client)
    _set_current_project_user(role="member")
    member = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={})
    assert member.status_code == 403

    _set_current_project_user(role="admin", moderation_state="banned")
    banned = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={})
    assert banned.status_code == 403

    db = SessionLocal()
    try:
        user = User(display_name="Wine Admin", is_active=True)
        db.add(user)
        db.flush()
        wine_project = ensure_default_project(db)
        db.add(
            ProjectUser(
                user_id=user.id,
                project_id=wine_project.id,
                role="admin",
                status="active",
                is_premium=False,
                access_state="active",
                moderation_state="normal",
            )
        )
        db.commit()
        token = create_access_token(subject=str(user.id))
    finally:
        db.close()

    with TestClient(app) as test_client:
        wine_only = test_client.post(
            "/api/v1/community/admin/notifications/process-pending",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )
    assert wine_only.status_code == 403


def test_processing_is_project_scoped(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    _create_target_user("scoped_target")
    _publish_urgent_insight(client, headers)

    db = SessionLocal()
    try:
        foreign_project = Project(slug="foreign-notifications", name="Foreign", is_active=True)
        user = User(display_name="Foreign User", is_active=True)
        db.add_all([foreign_project, user])
        db.flush()
        foreign_project_user = ProjectUser(
            user_id=user.id,
            project_id=foreign_project.id,
            role="member",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(foreign_project_user)
        db.flush()
        foreign_notification = CommunityNotification(
            project_id=foreign_project.id,
            project_user_id=foreign_project_user.id,
            type="urgent_insight",
            title="Foreign",
            body="Foreign",
            target_type="insight",
            target_id=None,
        )
        db.add(foreign_notification)
        db.commit()
        foreign_notification_id = foreign_notification.id
    finally:
        db.close()

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})
    assert response.status_code == 200, response.text

    db = SessionLocal()
    try:
        foreign_notification = db.query(CommunityNotification).filter(CommunityNotification.id == foreign_notification_id).one()
        assert foreign_notification.processing_status == "pending"
    finally:
        db.close()


def test_urgent_insight_message_composition_is_safe():
    insight = CommunityInsight(
        title="Skin market note",
        excerpt="Structured observation without promises.",
        content="Details",
        is_urgent=True,
        status="published",
    )

    message = compose_urgent_insight_message(insight)

    assert "Skin market note" in message
    assert "Structured observation" in message
    assert "guaranteed profit" not in message.lower()
    assert "гарант" not in message.lower()
