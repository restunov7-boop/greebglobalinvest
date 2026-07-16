from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.community.permissions import COMMUNITY_PROJECT_SLUG, get_community_project
from app.database import SessionLocal
from app.main import app
from app.projects.models import Project, ProjectUser
from app.projects.service import DEFAULT_PROJECT_SLUG, ensure_default_project, get_project_by_slug
from app.users.models import User
from tests.conftest import login


def test_wine_club_default_project_constant_is_kept():
    assert DEFAULT_PROJECT_SLUG == "doch-vinodela"


def test_community_project_resolver_uses_globalgreeninvest():
    db = SessionLocal()
    try:
        project = Project(slug=COMMUNITY_PROJECT_SLUG, name="GlobalGreenInvest", is_active=True)
        db.add(project)
        db.commit()
        resolved = get_community_project(db)
        assert resolved is not None
        assert resolved.slug == "global-green-invest"
    finally:
        db.close()


def test_community_endpoints_use_global_project_not_wine_default(client):
    headers = login(client)

    response = client.get("/api/v1/community/profile", headers=headers)

    assert response.status_code == 200, response.text
    db = SessionLocal()
    try:
        default_project = get_project_by_slug(db, DEFAULT_PROJECT_SLUG)
        community_project = get_project_by_slug(db, COMMUNITY_PROJECT_SLUG)
        assert default_project is not None
        assert community_project is not None
        assert default_project.id != community_project.id
    finally:
        db.close()


def test_user_with_only_wine_project_user_cannot_access_community():
    db = SessionLocal()
    try:
        user = User(display_name="Wine Only", is_active=True)
        db.add(user)
        db.flush()
        wine_project = ensure_default_project(db)
        db.add(
            ProjectUser(
                user_id=user.id,
                project_id=wine_project.id,
                role="member",
                status="active",
                is_premium=False,
                access_state="active",
                moderation_state="normal",
            )
        )
        community_project = Project(slug=COMMUNITY_PROJECT_SLUG, name="GlobalGreenInvest", is_active=True)
        db.add(community_project)
        db.commit()
        token = create_access_token(subject=str(user.id))
    finally:
        db.close()

    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/community/profile", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
