from tests.conftest import login

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
