from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.config import settings
from app.community.models import CommunityNotification, CommunityNotificationSetting
from app.community.permissions import COMMUNITY_PROJECT_SLUG
from app.database import SessionLocal
from app.main import app
from app.projects.models import Project, ProjectUser
from app.projects.service import ensure_default_project, get_project_by_slug
from app.users.models import TelegramIdentity, User
from tests.conftest import login


class FakeTelegramResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


def _community_project() -> Project:
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


def _create_target_user(username: str) -> UUID:
    db = SessionLocal()
    try:
        project = db.merge(_community_project())
        user = User(display_name=username, is_active=True)
        db.add(user)
        db.flush()
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


def _publish_urgent_insight(client, headers) -> None:
    response = client.post(
        "/api/v1/community/admin/insights",
        headers=headers,
        json={
            "title": "Real sender test",
            "excerpt": "A calm urgent note.",
            "content": "Educational context only.",
            "is_urgent": True,
            "status": "published",
            "scheduled_at": None,
            "published_at": None,
        },
    )
    assert response.status_code == 200, response.text


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


def test_sender_status_defaults_to_mock_and_does_not_expose_token(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    settings.telegram_bot_token = "secret-token"

    response = client.get("/api/v1/community/admin/notifications/sender-status", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["mode"] == "mock"
    assert data["real_enabled"] is False
    assert data["token_configured"] is True
    assert "secret-token" not in response.text


def test_real_mode_without_token_fails_safely_without_network(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("missing_token_target")
    _publish_urgent_insight(client, headers)
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = ""
    settings.telegram_real_send_scope = "all"

    def fail_if_called(*args, **kwargs):
        raise AssertionError("real network should not be called without token")

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fail_if_called)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["mode"] == "real"
    assert data["failed"] == 1
    notification = _notification_for(target_id)
    assert notification.processing_status == "failed"
    assert notification.processing_error == "telegram_bot_token_missing"


def test_real_dry_run_does_not_call_network_or_mutate(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("dry_run_real_target")
    _publish_urgent_insight(client, headers)
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = "fake-token"
    settings.telegram_real_send_scope = "all"

    def fail_if_called(*args, **kwargs):
        raise AssertionError("dry-run must not call Telegram")

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fail_if_called)

    response = client.post(
        "/api/v1/community/admin/notifications/process-pending",
        headers=headers,
        json={"limit": 50, "dry_run": True},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["mode"] == "real"
    assert data["sent"] == 1
    assert _notification_for(target_id).processing_status == "pending"


def test_real_success_marks_sent_and_processing_is_idempotent(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("real_success_target")
    _publish_urgent_insight(client, headers)
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = "fake-token"
    settings.telegram_real_send_scope = "all"
    calls: list[dict] = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeTelegramResponse(200, {"ok": True, "result": {"message_id": 777}})

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    first = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})
    second = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert first.status_code == 200, first.text
    assert first.json()["data"]["sent"] == 1
    assert second.json()["data"]["processed"] == 0
    assert len(calls) == 1
    assert calls[0]["json"]["chat_id"] == "tg_real_success_target"
    assert "fake-token" in calls[0]["url"]
    notification = _notification_for(target_id)
    assert notification.processing_status == "sent"
    assert notification.mock_message_id == "777"


def test_real_api_error_marks_failed(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("real_api_error_target")
    _publish_urgent_insight(client, headers)
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = "fake-token"
    settings.telegram_real_send_scope = "all"

    def fake_post(url, json, timeout):
        return FakeTelegramResponse(400, {"ok": False, "description": "Bad Request: chat not found"})

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    assert response.json()["data"]["failed"] == 1
    notification = _notification_for(target_id)
    assert notification.processing_status == "failed"
    assert "chat not found" in notification.processing_error


def test_real_network_error_marks_failed_and_loop_continues(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    first_id = _create_target_user("network_first")
    second_id = _create_target_user("network_second")
    _publish_urgent_insight(client, headers)
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = "fake-token"
    settings.telegram_real_send_scope = "all"
    calls = 0

    def fake_post(url, json, timeout):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.ConnectError("offline")
        return FakeTelegramResponse(200, {"ok": True, "result": {"message_id": 778}})

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["failed"] == 1
    assert data["sent"] == 1
    statuses = {_notification_for(first_id).processing_status, _notification_for(second_id).processing_status}
    assert statuses == {"failed", "sent"}


def test_sender_status_and_processing_permissions(client):
    headers = login(client)
    _set_current_project_user(role="member")
    member_status = client.get("/api/v1/community/admin/notifications/sender-status", headers=headers)
    member_process = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={})
    assert member_status.status_code == 403
    assert member_process.status_code == 403

    _set_current_project_user(role="admin", moderation_state="banned")
    banned_status = client.get("/api/v1/community/admin/notifications/sender-status", headers=headers)
    banned_process = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={})
    assert banned_status.status_code == 403
    assert banned_process.status_code == 403


def test_real_processing_remains_globalgreeninvest_scoped(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    _create_target_user("scoped_real_target")
    _publish_urgent_insight(client, headers)
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = "fake-token"
    settings.telegram_real_send_scope = "all"

    db = SessionLocal()
    try:
        foreign_project = Project(slug="foreign-real-notifications", name="Foreign", is_active=True)
        foreign_user = User(display_name="Foreign", is_active=True)
        db.add_all([foreign_project, foreign_user])
        db.flush()
        foreign_project_user = ProjectUser(
            user_id=foreign_user.id,
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

    def fake_post(url, json, timeout):
        return FakeTelegramResponse(200, {"ok": True, "result": {"message_id": 779}})

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})
    assert response.status_code == 200, response.text

    db = SessionLocal()
    try:
        foreign_notification = db.query(CommunityNotification).filter(CommunityNotification.id == foreign_notification_id).one()
        assert foreign_notification.processing_status == "pending"
    finally:
        db.close()


def test_wine_only_admin_cannot_view_sender_status():
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
        response = test_client.get(
            "/api/v1/community/admin/notifications/sender-status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
