from datetime import UTC, datetime, timedelta
from uuid import UUID

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
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {"ok": True, "result": {"message_id": 9001}}

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


def _create_target_user(username: str, *, telegram_id: str | None = None) -> UUID:
    db = SessionLocal()
    try:
        project = db.merge(_community_project())
        user = User(display_name=username, is_active=True)
        db.add(user)
        db.flush()
        db.add(
            TelegramIdentity(
                user_id=user.id,
                telegram_id=telegram_id or f"tg_{username}",
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
            "title": "Pilot sender test",
            "excerpt": "A calm pilot note.",
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


def _enable_real(*, scope: str = "pilot", pilot_chat_id: str = "", pilot_user_id: str = "") -> None:
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = "fake-token"
    settings.telegram_real_send_scope = scope
    settings.telegram_pilot_chat_id = pilot_chat_id
    settings.telegram_pilot_telegram_user_id = pilot_user_id


def test_real_send_scope_defaults_to_pilot(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    settings.telegram_sender_mode = "real"
    settings.telegram_bot_token = "fake-token"
    settings.telegram_real_send_scope = ""

    response = client.get("/api/v1/community/admin/notifications/sender-status", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["real_send_scope"] == "pilot"
    assert data["pilot_target_configured"] is False
    assert "fake-token" not in response.text


def test_real_pilot_target_missing_blocks_real_send_without_network(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("pilot_missing")
    _publish_urgent_insight(client, headers)
    _enable_real(scope="pilot")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("pilot without target must not call Telegram")

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fail_if_called)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["skipped"] == 1
    notification = _notification_for(target_id)
    assert notification.processing_status == "skipped"
    assert notification.processing_error == "real_mode_pilot_target_missing"


def test_mock_mode_ignores_pilot_scope_and_still_mock_sends(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    target_id = _create_target_user("mock_ignores_pilot")
    _publish_urgent_insight(client, headers)
    settings.telegram_sender_mode = "mock"
    settings.telegram_real_send_scope = "pilot"

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    assert response.json()["data"]["sent_mock"] == 1
    assert _notification_for(target_id).processing_status == "mock_sent"


def test_real_pilot_matching_chat_id_sends_only_pilot(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    pilot_id = _create_target_user("pilot_match", telegram_id="777001")
    other_id = _create_target_user("pilot_other", telegram_id="777002")
    _publish_urgent_insight(client, headers)
    _enable_real(scope="pilot", pilot_chat_id="777001")
    calls: list[dict] = []

    def fake_post(url, json, timeout):
        calls.append(json)
        return FakeTelegramResponse()

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["sent"] == 1
    assert data["skipped"] == 1
    assert calls == [{"chat_id": "777001", "text": calls[0]["text"], "disable_web_page_preview": True}]
    assert _notification_for(pilot_id).processing_status == "sent"
    other = _notification_for(other_id)
    assert other.processing_status == "skipped"
    assert other.processing_error == "real_mode_pilot_recipient_mismatch"


def test_real_pilot_matching_telegram_user_id_sends(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    pilot_id = _create_target_user("pilot_user_id", telegram_id="888001")
    _publish_urgent_insight(client, headers)
    _enable_real(scope="pilot", pilot_user_id="888001")
    calls = 0

    def fake_post(url, json, timeout):
        nonlocal calls
        calls += 1
        return FakeTelegramResponse()

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    assert response.json()["data"]["sent"] == 1
    assert calls == 1
    assert _notification_for(pilot_id).processing_status == "sent"


def test_real_all_sends_to_all_eligible_only_when_explicit(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    _create_target_user("all_one", telegram_id="900001")
    _create_target_user("all_two", telegram_id="900002")
    _publish_urgent_insight(client, headers)
    _enable_real(scope="all")
    calls: list[str] = []

    def fake_post(url, json, timeout):
        calls.append(json["chat_id"])
        return FakeTelegramResponse()

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert response.status_code == 200, response.text
    assert response.json()["data"]["sent"] == 2
    assert sorted(calls) == ["900001", "900002"]


def test_real_pilot_and_all_dry_run_do_not_call_network_or_mutate(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    pilot_id = _create_target_user("dry_pilot", telegram_id="910001")
    other_id = _create_target_user("dry_other", telegram_id="910002")
    _publish_urgent_insight(client, headers)
    _enable_real(scope="pilot", pilot_chat_id="910001")

    def fail_if_called(*args, **kwargs):
        raise AssertionError("dry-run must not call Telegram")

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fail_if_called)

    pilot_response = client.post(
        "/api/v1/community/admin/notifications/process-pending",
        headers=headers,
        json={"limit": 50, "dry_run": True},
    )
    assert pilot_response.status_code == 200, pilot_response.text
    pilot_data = pilot_response.json()["data"]
    assert pilot_data["sent"] == 1
    assert pilot_data["skipped"] == 1
    assert _notification_for(pilot_id).processing_status == "pending"
    assert _notification_for(other_id).processing_status == "pending"

    settings.telegram_real_send_scope = "all"
    all_response = client.post(
        "/api/v1/community/admin/notifications/process-pending",
        headers=headers,
        json={"limit": 50, "dry_run": True},
    )
    assert all_response.status_code == 200, all_response.text
    assert all_response.json()["data"]["sent"] == 2
    assert _notification_for(pilot_id).processing_status == "pending"
    assert _notification_for(other_id).processing_status == "pending"


def test_real_pilot_processing_is_idempotent(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    _create_target_user("pilot_idempotent", telegram_id="920001")
    _publish_urgent_insight(client, headers)
    _enable_real(scope="pilot", pilot_chat_id="920001")
    calls = 0

    def fake_post(url, json, timeout):
        nonlocal calls
        calls += 1
        return FakeTelegramResponse()

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    first = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})
    second = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})

    assert first.status_code == 200, first.text
    assert first.json()["data"]["sent"] == 1
    assert second.json()["data"]["processed"] == 0
    assert calls == 1


def test_real_pilot_permissions_block_member_and_banned_admin(client):
    headers = login(client)
    _set_current_project_user(role="member")
    assert client.get("/api/v1/community/admin/notifications/sender-status", headers=headers).status_code == 403
    assert client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={}).status_code == 403

    _set_current_project_user(role="admin", moderation_state="banned")
    assert client.get("/api/v1/community/admin/notifications/sender-status", headers=headers).status_code == 403
    assert client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={}).status_code == 403


def test_real_pilot_processing_remains_globalgreeninvest_scoped(client, monkeypatch):
    headers = login(client)
    _set_current_project_user(role="admin")
    _set_current_notifications(False)
    _create_target_user("pilot_scoped", telegram_id="930001")
    _publish_urgent_insight(client, headers)
    _enable_real(scope="pilot", pilot_chat_id="930001")

    db = SessionLocal()
    try:
        foreign_project = Project(slug="foreign-pilot-notifications", name="Foreign", is_active=True)
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
        return FakeTelegramResponse()

    monkeypatch.setattr("app.community.telegram_sender.httpx.post", fake_post)

    response = client.post("/api/v1/community/admin/notifications/process-pending", headers=headers, json={"limit": 50})
    assert response.status_code == 200, response.text

    db = SessionLocal()
    try:
        foreign_notification = db.query(CommunityNotification).filter(CommunityNotification.id == foreign_notification_id).one()
        assert foreign_notification.processing_status == "pending"
    finally:
        db.close()


def test_wine_only_admin_cannot_view_pilot_sender_status():
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
