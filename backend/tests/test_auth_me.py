from tests.conftest import login

import hashlib
import hmac
import json
from datetime import UTC, datetime
from urllib.parse import urlencode

from app.config import settings
from app.projects.models import ProjectUser
from app.projects.service import is_project_access_active, is_project_user_banned


def test_dev_auth_login_returns_member_project_access(client):
    response = client.post("/api/v1/auth/telegram", json={"init_data": "dev_mock_init_data"})

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["access_token"]
    assert data["project_user"]["project_slug"] == "doch-vinodela"
    assert data["project_user"]["role"] == "member"
    assert data["project_user"]["status"] == "active"
    assert data["project_user"]["access_state"] == "active"
    assert data["project_user"]["access_until"] is None
    assert data["project_user"]["moderation_state"] == "normal"
    assert data["project_user"]["capabilities"] == ["view_app"]


def test_auth_me_returns_current_user_and_project_user(client):
    headers = login(client)

    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["user"]["display_name"] == "CORE"
    assert data["project_user"]["project_slug"] == "doch-vinodela"
    assert data["project_user"]["role"] == "member"
    assert data["project_user"]["status"] == "active"
    assert data["project_user"]["access_state"] == "active"
    assert data["project_user"]["access_until"] is None
    assert data["project_user"]["moderation_state"] == "normal"
    assert "view_app" in data["project_user"]["capabilities"]
    assert "access_admin" not in data["project_user"]["capabilities"]


def test_project_user_access_helpers_read_new_access_fields():
    project_user = ProjectUser(access_state="active", moderation_state="normal")

    assert is_project_access_active(project_user) is True
    assert is_project_user_banned(project_user) is False

    project_user.access_state = "revoked"
    project_user.moderation_state = "banned"

    assert is_project_access_active(project_user) is False
    assert is_project_user_banned(project_user) is True


def _signed_init_data(bot_token: str, user: dict[str, object] | None = None, auth_date: int | None = None) -> str:
    payload = {
        "auth_date": str(auth_date or int(datetime.now(UTC).timestamp())),
        "query_id": "test-query",
        "user": json.dumps(user or {"id": 777001, "first_name": "Pilot", "username": "pilot_user"}, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode(payload)


def test_real_telegram_init_data_can_login_to_globalgreeninvest(client):
    settings.app_env = "production"
    settings.dev_auth_enabled = False
    settings.telegram_bot_token = "test_bot_token"

    response = client.post(
        "/api/v1/auth/telegram",
        json={"init_data": _signed_init_data(settings.telegram_bot_token), "project_slug": "global-green-invest"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["access_token"]
    assert data["project_user"]["project_slug"] == "global-green-invest"
    assert data["project_user"]["access_state"] == "pending"
    assert data["project_user"]["moderation_state"] == "normal"


def test_real_telegram_init_data_rejects_invalid_hash(client):
    settings.app_env = "production"
    settings.dev_auth_enabled = False
    settings.telegram_bot_token = "test_bot_token"
    init_data = _signed_init_data(settings.telegram_bot_token).replace("hash=", "hash=bad")

    response = client.post("/api/v1/auth/telegram", json={"init_data": init_data, "project_slug": "global-green-invest"})

    assert response.status_code == 401


def test_real_telegram_init_data_requires_payload(client):
    settings.app_env = "production"
    settings.dev_auth_enabled = False
    settings.telegram_bot_token = "test_bot_token"

    response = client.post("/api/v1/auth/telegram", json={"init_data": "", "project_slug": "global-green-invest"})

    assert response.status_code == 401
