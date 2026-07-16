from datetime import UTC, datetime, timedelta

from app.community.models import (
    CommunityNotificationSetting,
    CommunityProduct,
    CommunityProductAccess,
    CommunityProductMaterial,
    CommunityProjectLink,
    CommunityProjectPage,
)
from app.database import SessionLocal
from app.projects.models import Project, ProjectUser
from app.projects.service import get_project_by_slug
from app.users.models import User
from tests.conftest import login


def _current_project_user() -> ProjectUser:
    db = SessionLocal()
    try:
        project = get_project_by_slug(db, "global-green-invest")
        assert project is not None
        return db.query(ProjectUser).filter(ProjectUser.project_id == project.id).one()
    finally:
        db.close()


def _set_current_project_user(role: str = "member", access_state: str = "active", moderation_state: str = "normal") -> None:
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


def _seed_mvp_data() -> dict[str, object]:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project = project_user.project
        db.add_all(
            [
                CommunityProjectLink(project_id=project.id, type="support", title="Support", url="https://t.me/demo_support", is_active=True),
                CommunityProjectLink(project_id=project.id, type="telegram_bot", title="Bot", url="https://t.me/demo_bot", is_active=True),
                CommunityProjectLink(project_id=project.id, type="website", title="Website", url="https://example.com", is_active=True),
                CommunityProjectLink(
                    project_id=project.id,
                    type="blogger_telegram",
                    title="Blogger",
                    url="https://t.me/demo_blogger",
                    is_active=True,
                ),
                CommunityProjectPage(project_id=project.id, slug="rules", title="Rules", content="Rules content", is_published=True),
                CommunityProjectPage(project_id=project.id, slug="disclaimer", title="Disclaimer", content="Disclaimer content", is_published=True),
                CommunityProjectPage(project_id=project.id, slug="about", title="About", content="About content", is_published=True),
            ]
        )
        product = CommunityProduct(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            slug="demo-product",
            title="Demo Product",
            short_description="Short",
            description="Description",
            price_usd=100,
            sort_order=1,
            is_published=True,
            access_duration_type="lifetime",
        )
        hidden_product = CommunityProduct(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            slug="hidden-product",
            title="Hidden Product",
            short_description="Hidden",
            description="Hidden",
            sort_order=2,
            is_published=False,
            access_duration_type="lifetime",
        )
        db.add_all([product, hidden_product])
        db.flush()
        unlocked = CommunityProductMaterial(
            project_id=project.id,
            product_id=product.id,
            title="Intro",
            material_type="text",
            content="Unlocked content",
            sort_order=1,
            is_locked=False,
        )
        locked = CommunityProductMaterial(
            project_id=project.id,
            product_id=product.id,
            title="Locked",
            material_type="text",
            content="Locked content",
            sort_order=2,
            is_locked=True,
        )
        db.add_all([unlocked, locked])
        db.commit()
        return {"product_id": product.id, "hidden_product_id": hidden_product.id, "locked_material_id": locked.id}
    finally:
        db.close()


def test_profile_settings_rules_public_links_and_notification_update(client):
    headers = login(client)
    _seed_mvp_data()

    profile = client.get("/api/v1/community/profile", headers=headers)
    settings = client.get("/api/v1/community/settings", headers=headers)
    rules = client.get("/api/v1/community/rules", headers=headers)
    public_links = client.get("/api/v1/community/public-links")
    patch = client.patch("/api/v1/community/settings/notifications", headers=headers, json={"notifications_enabled": False})

    assert profile.status_code == 200, profile.text
    assert "role" not in profile.json()["data"]
    assert profile.json()["data"]["support_url"] == "https://t.me/demo_support"
    assert settings.status_code == 200, settings.text
    assert settings.json()["data"]["notifications_enabled"] is True
    assert rules.status_code == 200, rules.text
    assert rules.json()["data"]["disclaimer"] == "Disclaimer content"
    assert public_links.status_code == 200, public_links.text
    assert public_links.json()["data"]["support_url"] == "https://t.me/demo_support"
    assert patch.status_code == 200, patch.text
    assert patch.json()["data"]["notifications_enabled"] is False
    assert _notification_setting_count() == 1


def test_member_products_hide_locked_materials_without_active_product_access(client):
    headers = login(client)
    seeded = _seed_mvp_data()

    listing = client.get("/api/v1/community/products", headers=headers)
    detail = client.get(f"/api/v1/community/products/{seeded['product_id']}", headers=headers)
    hidden = client.get(f"/api/v1/community/products/{seeded['hidden_product_id']}", headers=headers)

    assert listing.status_code == 200, listing.text
    assert [item["title"] for item in listing.json()["data"]] == ["Demo Product"]
    assert listing.json()["data"][0]["has_access"] is False
    assert detail.status_code == 200, detail.text
    data = detail.json()["data"]
    assert data["has_access"] is False
    assert [item["title"] for item in data["materials"]] == ["Intro"]
    assert data["locked_materials_count"] == 1
    assert hidden.status_code == 404


def test_member_products_return_locked_materials_with_active_access_only(client):
    headers = login(client)
    seeded = _seed_mvp_data()
    _grant_product_access(seeded["product_id"], "active", None)

    active = client.get(f"/api/v1/community/products/{seeded['product_id']}", headers=headers)
    assert active.status_code == 200, active.text
    assert [item["title"] for item in active.json()["data"]["materials"]] == ["Intro", "Locked"]

    _grant_product_access(seeded["product_id"], "revoked", None)
    revoked = client.get(f"/api/v1/community/products/{seeded['product_id']}", headers=headers)
    assert [item["title"] for item in revoked.json()["data"]["materials"]] == ["Intro"]

    _grant_product_access(seeded["product_id"], "active", datetime.now(UTC) - timedelta(days=1))
    expired = client.get(f"/api/v1/community/products/{seeded['product_id']}", headers=headers)
    assert [item["title"] for item in expired.json()["data"]["materials"]] == ["Intro"]


def test_admin_product_material_and_access_endpoints(client):
    headers = login(client)
    seeded = _seed_mvp_data()

    assert client.get("/api/v1/community/admin/products", headers=headers).status_code == 403
    _set_current_project_user(role="admin")

    create = client.post(
        "/api/v1/community/admin/products",
        headers=headers,
        json={
            "slug": "admin-product",
            "title": "Admin Product",
            "short_description": "Short",
            "description": "Description",
            "cover_url": None,
            "price_usd": "10.00",
            "price_rub": None,
            "sort_order": 3,
            "is_published": True,
            "access_duration_type": "lifetime",
        },
    )
    assert create.status_code == 200, create.text
    product_id = create.json()["data"]["id"]

    update = client.patch(
        f"/api/v1/community/admin/products/{product_id}",
        headers=headers,
        json={
            "slug": "admin-product-updated",
            "title": "Admin Product Updated",
            "short_description": "Short",
            "description": "Description",
            "cover_url": None,
            "price_usd": None,
            "price_rub": None,
            "sort_order": 4,
            "is_published": True,
            "access_duration_type": "lifetime",
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["data"]["title"] == "Admin Product Updated"

    material = client.post(
        f"/api/v1/community/admin/products/{product_id}/materials",
        headers=headers,
        json={
            "title": "Material",
            "description": "Material description",
            "material_type": "text",
            "content": "Material content",
            "url": None,
            "file_url": None,
            "sort_order": 1,
            "is_locked": True,
        },
    )
    assert material.status_code == 200, material.text
    material_id = material.json()["data"]["id"]

    delete_material = client.delete(f"/api/v1/community/admin/products/{product_id}/materials/{material_id}", headers=headers)
    assert delete_material.status_code == 200, delete_material.text
    assert delete_material.json()["data"]["deleted_at"] is not None

    hide_product = client.delete(f"/api/v1/community/admin/products/{product_id}", headers=headers)
    assert hide_product.status_code == 200, hide_product.text
    assert hide_product.json()["data"]["is_published"] is False

    access = client.post(
        "/api/v1/community/admin/product-access",
        headers=headers,
        json={"product_id": str(seeded["product_id"]), "project_user_id": str(_current_project_user().id), "access_state": "active"},
    )
    assert access.status_code == 200, access.text
    access_id = access.json()["data"]["id"]
    revoke = client.patch(f"/api/v1/community/admin/product-access/{access_id}", headers=headers, json={"access_state": "revoked"})
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["data"]["access_state"] == "revoked"


def test_mvp_endpoints_block_inactive_and_banned_users(client):
    headers = login(client)
    _seed_mvp_data()

    for access_state in ("pending", "expired", "revoked"):
        _set_current_project_user(access_state=access_state, moderation_state="normal")
        assert client.get("/api/v1/community/profile", headers=headers).status_code == 403
        assert client.get("/api/v1/community/products", headers=headers).status_code == 403

    _set_current_project_user(access_state="active", moderation_state="banned")
    assert client.get("/api/v1/community/settings", headers=headers).status_code == 403
    assert client.get("/api/v1/community/rules", headers=headers).status_code == 403


def _grant_product_access(product_id, access_state: str, access_until) -> None:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        access = (
            db.query(CommunityProductAccess)
            .filter(
                CommunityProductAccess.project_id == project_user.project_id,
                CommunityProductAccess.product_id == product_id,
                CommunityProductAccess.project_user_id == project_user.id,
            )
            .one_or_none()
        )
        if access is None:
            access = CommunityProductAccess(project_id=project_user.project_id, product_id=product_id, project_user_id=project_user.id)
            db.add(access)
        access.access_state = access_state
        access.access_until = access_until
        access.source = "manual"
        access.granted_by_project_user_id = project_user.id
        db.commit()
    finally:
        db.close()


def _notification_setting_count() -> int:
    db = SessionLocal()
    try:
        return db.query(CommunityNotificationSetting).count()
    finally:
        db.close()
