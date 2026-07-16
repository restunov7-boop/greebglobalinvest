from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.community.models import (
    CommunityAdminAuditLog,
    CommunityProduct,
    CommunityProductAccess,
    CommunityProductMaterial,
    CommunityProductPurchaseRequest,
)
from app.community.permissions import COMMUNITY_PROJECT_SLUG
from app.database import SessionLocal
from app.main import app
from app.projects.models import Project, ProjectUser
from app.projects.service import ensure_default_project, get_project_by_slug
from app.users.models import TelegramIdentity, User
from tests.conftest import login


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


def _set_current_project_user(
    *,
    role: str = "admin",
    status: str = "active",
    access_state: str = "active",
    moderation_state: str = "normal",
) -> None:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project_user.role = role
        project_user.status = status
        project_user.access_state = access_state
        project_user.moderation_state = moderation_state
        project_user.access_until = datetime.now(UTC) + timedelta(days=30)
        if access_state == "expired":
            project_user.access_until = datetime.now(UTC) - timedelta(days=1)
        db.commit()
    finally:
        db.close()


def _create_product(*, title: str = "Request Product", is_published: bool = True, project: Project | None = None) -> UUID:
    db = SessionLocal()
    try:
        selected_project = db.merge(project) if project is not None else db.merge(_community_project())
        admin = (
            db.query(ProjectUser)
            .filter(ProjectUser.project_id == selected_project.id)
            .order_by(ProjectUser.created_at.asc())
            .first()
        )
        if admin is None:
            user = User(display_name="Foreign Admin", is_active=True)
            db.add(user)
            db.flush()
            admin = ProjectUser(
                user_id=user.id,
                project_id=selected_project.id,
                role="admin",
                status="active",
                is_premium=False,
                access_state="active",
                moderation_state="normal",
            )
            db.add(admin)
            db.flush()
        product = CommunityProduct(
            project_id=selected_project.id,
            slug=title.lower().replace(" ", "-"),
            title=title,
            short_description="Short",
            description="Full",
            price_usd=100,
            sort_order=1,
            is_published=is_published,
            created_by_project_user_id=admin.id,
        )
        db.add(product)
        db.flush()
        db.add(
            CommunityProductMaterial(
                project_id=selected_project.id,
                product_id=product.id,
                title="Locked Material",
                material_type="text",
                content="Secret",
                sort_order=1,
                is_locked=True,
            )
        )
        product_id = product.id
        db.commit()
        return product_id
    finally:
        db.close()


def _create_target_member(username: str) -> tuple[UUID, dict[str, str]]:
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
        token = create_access_token(subject=str(user.id))
        db.commit()
        return project_user_id, {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


def _request_count() -> int:
    db = SessionLocal()
    try:
        return db.query(CommunityProductPurchaseRequest).count()
    finally:
        db.close()


def test_active_member_can_create_and_list_own_purchase_request(client):
    headers = login(client)
    _set_current_project_user(role="member")
    product_id = _create_product()

    response = client.post(
        f"/api/v1/community/products/{product_id}/purchase-request",
        headers=headers,
        json={"contact_method": "telegram", "contact_value": "@buyer", "message": "Need access"},
    )
    listing = client.get("/api/v1/community/my-purchase-requests", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["status"] == "new"
    assert data["product_id"] == str(product_id)
    assert listing.status_code == 200, listing.text
    assert len(listing.json()["data"]) == 1
    assert listing.json()["data"][0]["request_id"] == data["request_id"]
    assert _request_count() == 1


def test_banned_revoked_expired_pending_users_cannot_create_purchase_request(client):
    headers = login(client)
    product_id = _create_product()
    for state in (
        {"moderation_state": "banned"},
        {"access_state": "revoked"},
        {"access_state": "expired"},
        {"access_state": "pending"},
    ):
        _set_current_project_user(role="member", **state)
        response = client.post(f"/api/v1/community/products/{product_id}/purchase-request", headers=headers, json={})
        assert response.status_code == 403


def test_hidden_product_duplicate_and_existing_access_are_blocked(client):
    headers = login(client)
    _set_current_project_user(role="member")
    hidden_product_id = _create_product(title="Hidden Product", is_published=False)
    visible_product_id = _create_product(title="Visible Product")

    hidden = client.post(f"/api/v1/community/products/{hidden_product_id}/purchase-request", headers=headers, json={})
    first = client.post(f"/api/v1/community/products/{visible_product_id}/purchase-request", headers=headers, json={})
    duplicate = client.post(f"/api/v1/community/products/{visible_product_id}/purchase-request", headers=headers, json={})

    assert hidden.status_code == 404
    assert first.status_code == 200
    assert duplicate.status_code == 409

    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        db.add(
            CommunityProductAccess(
                project_id=project_user.project_id,
                project_user_id=project_user.id,
                product_id=hidden_product_id,
                access_state="active",
            )
        )
        db.commit()
    finally:
        db.close()

    already = client.post(f"/api/v1/community/products/{hidden_product_id}/purchase-request", headers=headers, json={})
    assert already.status_code == 404


def test_user_lists_only_own_purchase_requests(client):
    admin_headers = login(client)
    _set_current_project_user(role="admin")
    product_id = _create_product()
    _, member_headers = _create_target_member("request_member")
    other_user_id, _ = _create_target_member("other_request_member")

    response = client.post(f"/api/v1/community/products/{product_id}/purchase-request", headers=member_headers, json={})
    assert response.status_code == 200, response.text

    db = SessionLocal()
    try:
        project = db.merge(_community_project())
        db.add(
            CommunityProductPurchaseRequest(
                project_id=project.id,
                product_id=product_id,
                project_user_id=other_user_id,
                status="new",
            )
        )
        db.commit()
    finally:
        db.close()

    own = client.get("/api/v1/community/my-purchase-requests", headers=member_headers)
    admin = client.get("/api/v1/community/admin/purchase-requests", headers=admin_headers)
    assert len(own.json()["data"]) == 1
    assert admin.json()["data"]["total"] == 2


def test_admin_can_update_status_and_member_is_blocked(client):
    admin_headers = login(client)
    _set_current_project_user(role="admin")
    product_id = _create_product()
    _, member_headers = _create_target_member("status_member")
    created = client.post(f"/api/v1/community/products/{product_id}/purchase-request", headers=member_headers, json={})
    request_id = created.json()["data"]["request_id"]

    member_list = client.get("/api/v1/community/admin/purchase-requests", headers=member_headers)
    contacted = client.patch(
        f"/api/v1/community/admin/purchase-requests/{request_id}",
        headers=admin_headers,
        json={"status": "contacted", "admin_note": "Wrote in Telegram"},
    )

    assert member_list.status_code == 403
    assert contacted.status_code == 200, contacted.text
    data = contacted.json()["data"]
    assert data["status"] == "contacted"
    assert data["admin_note"] == "Wrote in Telegram"
    assert data["handled_at"] is not None


def test_approve_and_grant_is_idempotent_and_unlocks_materials(client):
    admin_headers = login(client)
    _set_current_project_user(role="admin")
    product_id = _create_product(title="Grant Product")
    _, member_headers = _create_target_member("grant_member")
    created = client.post(f"/api/v1/community/products/{product_id}/purchase-request", headers=member_headers, json={})
    request_id = created.json()["data"]["request_id"]

    before = client.get(f"/api/v1/community/products/{product_id}", headers=member_headers)
    first = client.post(
        f"/api/v1/community/admin/purchase-requests/{request_id}/approve-and-grant",
        headers=admin_headers,
        json={},
    )
    second = client.post(
        f"/api/v1/community/admin/purchase-requests/{request_id}/approve-and-grant",
        headers=admin_headers,
        json={},
    )
    after = client.get(f"/api/v1/community/products/{product_id}", headers=member_headers)

    assert before.json()["data"]["has_access"] is False
    assert before.json()["data"]["materials"] == []
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["data"]["status"] == "approved"
    assert after.json()["data"]["has_access"] is True
    assert len(after.json()["data"]["materials"]) == 1

    db = SessionLocal()
    try:
        accesses = db.query(CommunityProductAccess).filter(CommunityProductAccess.product_id == product_id).all()
        assert len(accesses) == 1
        audit = db.query(CommunityAdminAuditLog).filter(CommunityAdminAuditLog.action == "purchase_request.approved_and_granted").count()
        assert audit >= 1
    finally:
        db.close()


def test_wine_only_admin_and_banned_admin_are_blocked_from_purchase_admin(client):
    headers = login(client)
    _set_current_project_user(role="admin", moderation_state="banned")
    banned = client.get("/api/v1/community/admin/purchase-requests", headers=headers)
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
        wine_only = test_client.get(
            "/api/v1/community/admin/purchase-requests",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert wine_only.status_code == 403


def test_project_scoping_prevents_cross_project_request_handling(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    db = SessionLocal()
    try:
        foreign_project = Project(slug="foreign-purchase-requests", name="Foreign", is_active=True)
        foreign_user = User(display_name="Foreign User", is_active=True)
        foreign_admin_user = User(display_name="Foreign Admin", is_active=True)
        db.add_all([foreign_project, foreign_user, foreign_admin_user])
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
        foreign_admin = ProjectUser(
            user_id=foreign_admin_user.id,
            project_id=foreign_project.id,
            role="admin",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(foreign_admin)
        db.flush()
        foreign_product = CommunityProduct(
            project_id=foreign_project.id,
            slug="foreign-product",
            title="Foreign Product",
            short_description="Short",
            description="Full",
            is_published=True,
            created_by_project_user_id=foreign_admin.id,
        )
        db.add(foreign_product)
        db.flush()
        foreign_request = CommunityProductPurchaseRequest(
            project_id=foreign_project.id,
            product_id=foreign_product.id,
            project_user_id=foreign_project_user.id,
            status="new",
        )
        db.add(foreign_request)
        db.commit()
        foreign_request_id = foreign_request.id
    finally:
        db.close()

    listing = client.get("/api/v1/community/admin/purchase-requests", headers=headers)
    update = client.patch(
        f"/api/v1/community/admin/purchase-requests/{foreign_request_id}",
        headers=headers,
        json={"status": "contacted"},
    )

    assert listing.status_code == 200
    assert listing.json()["data"]["total"] == 0
    assert update.status_code == 404
