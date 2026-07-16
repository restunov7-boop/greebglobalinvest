from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.community.models import CommunityAdminAuditLog, CommunityProduct, CommunityProductAccess, CommunityProductMaterial
from app.database import SessionLocal
from app.projects.models import Project, ProjectUser
from app.projects.service import get_project_by_slug
from app.users.models import TelegramIdentity, User
from tests.conftest import login


def _current_project_user() -> ProjectUser:
    db = SessionLocal()
    try:
        project = get_project_by_slug(db, "global-green-invest")
        assert project is not None
        project_user = db.query(ProjectUser).filter(ProjectUser.project_id == project.id).order_by(ProjectUser.created_at.asc()).first()
        assert project_user is not None
        return project_user
    finally:
        db.close()


def _set_current_project_user(role: str = "admin", access_state: str = "active", moderation_state: str = "normal") -> None:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project_user.role = role
        project_user.status = "active"
        project_user.access_state = access_state
        project_user.moderation_state = moderation_state
        db.commit()
    finally:
        db.close()


def _create_target_user(username: str = "target_member") -> ProjectUser:
    db = SessionLocal()
    try:
        project = get_project_by_slug(db, "global-green-invest")
        assert project is not None
        user = User(display_name="Target", is_active=True)
        db.add(user)
        db.flush()
        telegram = TelegramIdentity(
            user_id=user.id,
            telegram_id=f"tg_{username}",
            username=username,
            first_name="Target",
            photo_url="https://example.com/avatar.png",
        )
        project_user = ProjectUser(
            user_id=user.id,
            project_id=project.id,
            role="member",
            status="active",
            access_state="pending",
            moderation_state="normal",
        )
        db.add_all([telegram, project_user])
        db.commit()
        db.refresh(project_user)
        return project_user
    finally:
        db.close()


def _create_foreign_project_user() -> ProjectUser:
    db = SessionLocal()
    try:
        user = User(display_name="Foreign", is_active=True)
        project = Project(slug="foreign-project", name="Foreign", is_active=True)
        db.add_all([user, project])
        db.flush()
        project_user = ProjectUser(
            user_id=user.id,
            project_id=project.id,
            role="admin",
            status="active",
            access_state="active",
            moderation_state="normal",
        )
        db.add(project_user)
        db.commit()
        db.refresh(project_user)
        return project_user
    finally:
        db.close()


def _seed_product() -> str:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        product = CommunityProduct(
            project_id=project_user.project_id,
            created_by_project_user_id=project_user.id,
            slug="access-product",
            title="Access Product",
            short_description="Short",
            description="Description",
            sort_order=1,
            is_published=True,
            access_duration_type="lifetime",
        )
        db.add(product)
        db.flush()
        db.add(
            CommunityProductMaterial(
                project_id=project_user.project_id,
                product_id=product.id,
                title="Locked",
                material_type="text",
                content="Locked content",
                sort_order=1,
                is_locked=True,
            )
        )
        db.commit()
        return str(product.id)
    finally:
        db.close()


def test_member_cannot_list_admin_users(client):
    headers = login(client)

    response = client.get("/api/v1/community/admin/users", headers=headers)

    assert response.status_code == 403


def test_admin_lists_searches_filters_and_reads_user_detail(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    target = _create_target_user(username="green_target")
    foreign_user = _create_foreign_project_user()

    response = client.get("/api/v1/community/admin/users?q=green_target&access_state=pending", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["project_user_id"] == str(target.id)
    assert data["items"][0]["telegram_username"] == "green_target"

    detail = client.get(f"/api/v1/community/admin/users/{target.id}", headers=headers)
    foreign = client.get(f"/api/v1/community/admin/users/{foreign_user.id}", headers=headers)

    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["project_user_id"] == str(target.id)
    assert detail.json()["data"]["product_access"] == []
    assert foreign.status_code == 404


def test_admin_updates_project_access_and_quick_actions(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    target = _create_target_user()
    next_until = (datetime.now(UTC) + timedelta(days=10)).isoformat()

    activate = client.patch(
        f"/api/v1/community/admin/users/{target.id}/project-access",
        headers=headers,
        json={"access_state": "active", "access_until": next_until, "moderation_state": "normal", "role": "member"},
    )
    assert activate.status_code == 200, activate.text
    assert activate.json()["data"]["access_state"] == "active"
    assert activate.json()["data"]["access_until"] is not None

    extended = client.post(f"/api/v1/community/admin/users/{target.id}/extend-one-year", headers=headers)
    assert extended.status_code == 200, extended.text
    assert extended.json()["data"]["access_state"] == "active"

    banned = client.post(f"/api/v1/community/admin/users/{target.id}/ban", headers=headers)
    assert banned.status_code == 200, banned.text
    assert banned.json()["data"]["moderation_state"] == "banned"

    unbanned = client.post(f"/api/v1/community/admin/users/{target.id}/unban", headers=headers)
    assert unbanned.status_code == 200, unbanned.text
    assert unbanned.json()["data"]["moderation_state"] == "normal"

    db = SessionLocal()
    try:
        assert db.query(CommunityAdminAuditLog).filter(CommunityAdminAuditLog.action == "project_access.extended").count() == 1
    finally:
        db.close()


def test_banned_and_revoked_current_user_is_blocked_from_member_endpoints(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    current_id = _current_project_user().id

    ban = client.post(f"/api/v1/community/admin/users/{current_id}/ban", headers=headers)
    assert ban.status_code == 200, ban.text
    assert client.get("/api/v1/community/profile", headers=headers).status_code == 403

    _set_current_project_user(role="admin", access_state="active", moderation_state="normal")
    revoke = client.patch(f"/api/v1/community/admin/users/{current_id}/project-access", headers=headers, json={"access_state": "revoked"})
    assert revoke.status_code == 200, revoke.text
    assert client.get("/api/v1/community/products", headers=headers).status_code == 403


def test_product_access_can_be_granted_and_revoked_for_user(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    target = _create_target_user()
    product_id = _seed_product()

    grant = client.post(
        "/api/v1/community/admin/product-access",
        headers=headers,
        json={"product_id": product_id, "project_user_id": str(target.id), "access_state": "active"},
    )
    assert grant.status_code == 200, grant.text
    access_id = grant.json()["data"]["id"]

    detail = client.get(f"/api/v1/community/admin/users/{target.id}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["product_access"][0]["product_title"] == "Access Product"
    assert detail.json()["data"]["product_access"][0]["access_state"] == "active"

    revoke = client.patch(f"/api/v1/community/admin/product-access/{access_id}", headers=headers, json={"access_state": "revoked"})
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["data"]["access_state"] == "revoked"

    db = SessionLocal()
    try:
        access = db.query(CommunityProductAccess).filter(CommunityProductAccess.id == UUID(access_id)).one()
        assert access.access_state == "revoked"
    finally:
        db.close()


def test_banned_admin_and_wine_only_admin_cannot_manage_users(client):
    headers = login(client)
    _set_current_project_user(role="admin", moderation_state="banned")
    assert client.get("/api/v1/community/admin/users", headers=headers).status_code == 403

    _set_current_project_user(role="member", moderation_state="normal")
    assert client.get("/api/v1/community/admin/users", headers=headers).status_code == 403
