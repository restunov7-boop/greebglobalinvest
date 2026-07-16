from uuid import UUID

from app.community.models import CommunityAdminAuditLog, CommunityChatLink, CommunityExchange
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


def _seed_links_and_exchanges() -> dict[str, object]:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project = project_user.project
        other_user = User(display_name="Other", is_active=True)
        db.add(other_user)
        db.flush()
        other_project = Project(slug="community-links-other", name="Other Community Links", is_active=True)
        db.add(other_project)
        db.flush()
        other_project_user = ProjectUser(
            user_id=other_user.id,
            project_id=other_project.id,
            role="admin",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(other_project_user)
        db.flush()

        chat_late = CommunityChatLink(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            title="Late Chat",
            telegram_url="https://t.me/late",
            sort_order=20,
            is_published=True,
        )
        chat_early = CommunityChatLink(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            title="Early Chat",
            telegram_url="https://t.me/early",
            sort_order=10,
            is_published=True,
        )
        hidden_chat = CommunityChatLink(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            title="Hidden Chat",
            telegram_url="https://t.me/hidden",
            sort_order=1,
            is_published=False,
        )
        other_chat = CommunityChatLink(
            project_id=other_project.id,
            created_by_project_user_id=other_project_user.id,
            title="Other Chat",
            telegram_url="https://t.me/other",
            sort_order=0,
            is_published=True,
        )
        exchange_late = CommunityExchange(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            title="Late Exchange",
            description="Late description",
            external_url="https://exchange.example/late",
            sort_order=20,
            is_published=True,
        )
        exchange_early = CommunityExchange(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            title="Early Exchange",
            description="Early description",
            team_comment="Team comment",
            logo_url="https://cdn.example/logo.png",
            external_url="https://exchange.example/early",
            promo_code="CORE",
            sort_order=10,
            is_published=True,
        )
        hidden_exchange = CommunityExchange(
            project_id=project.id,
            created_by_project_user_id=project_user.id,
            title="Hidden Exchange",
            description="Hidden description",
            external_url="https://exchange.example/hidden",
            sort_order=1,
            is_published=False,
        )
        other_exchange = CommunityExchange(
            project_id=other_project.id,
            created_by_project_user_id=other_project_user.id,
            title="Other Exchange",
            description="Other description",
            external_url="https://exchange.example/other",
            sort_order=0,
            is_published=True,
        )
        db.add_all([chat_late, chat_early, hidden_chat, other_chat, exchange_late, exchange_early, hidden_exchange, other_exchange])
        db.commit()
        return {
            "chat_id": chat_early.id,
            "hidden_chat_id": hidden_chat.id,
            "other_chat_id": other_chat.id,
            "exchange_id": exchange_early.id,
            "hidden_exchange_id": hidden_exchange.id,
            "other_exchange_id": other_exchange.id,
        }
    finally:
        db.close()


def test_member_chats_are_published_project_scoped_and_sorted(client):
    headers = login(client)
    _seed_links_and_exchanges()

    response = client.get("/api/v1/community/chats", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert [item["title"] for item in data] == ["Early Chat", "Late Chat"]
    assert all("telegram_url" in item for item in data)


def test_member_exchanges_are_published_project_scoped_and_sorted(client):
    headers = login(client)
    _seed_links_and_exchanges()

    response = client.get("/api/v1/community/exchanges", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert [item["title"] for item in data] == ["Early Exchange", "Late Exchange"]
    assert data[0]["team_comment"] == "Team comment"
    assert data[0]["promo_code"] == "CORE"


def test_member_chats_and_exchanges_block_inactive_and_banned_users(client):
    headers = login(client)
    _seed_links_and_exchanges()

    for access_state in ("pending", "expired", "revoked"):
        _set_current_project_user(access_state=access_state, moderation_state="normal")
        assert client.get("/api/v1/community/chats", headers=headers).status_code == 403
        assert client.get("/api/v1/community/exchanges", headers=headers).status_code == 403

    _set_current_project_user(access_state="active", moderation_state="banned")
    assert client.get("/api/v1/community/chats", headers=headers).status_code == 403
    assert client.get("/api/v1/community/exchanges", headers=headers).status_code == 403


def test_admin_chats_crud_soft_hide_project_scoping_and_audit(client):
    headers = login(client)
    seeded = _seed_links_and_exchanges()

    assert client.get("/api/v1/community/admin/chats", headers=headers).status_code == 403
    _set_current_project_user(role="admin")

    create = client.post(
        "/api/v1/community/admin/chats",
        headers=headers,
        json={"title": "Admin Chat", "telegram_url": "https://t.me/admin", "sort_order": 7, "is_published": True},
    )
    assert create.status_code == 200, create.text
    created = create.json()["data"]
    assert created["title"] == "Admin Chat"
    assert created["is_published"] is True

    listing = client.get("/api/v1/community/admin/chats", headers=headers)
    assert listing.status_code == 200, listing.text
    titles = {item["title"] for item in listing.json()["data"]}
    assert {"Early Chat", "Late Chat", "Hidden Chat", "Admin Chat"}.issubset(titles)

    detail = client.get(f"/api/v1/community/admin/chats/{created['id']}", headers=headers)
    assert detail.status_code == 200, detail.text

    update = client.patch(
        f"/api/v1/community/admin/chats/{created['id']}",
        headers=headers,
        json={"title": "Updated Chat", "telegram_url": "https://t.me/updated", "sort_order": 3, "is_published": False},
    )
    assert update.status_code == 200, update.text
    assert update.json()["data"]["title"] == "Updated Chat"
    assert update.json()["data"]["is_published"] is False

    hide = client.delete(f"/api/v1/community/admin/chats/{seeded['chat_id']}", headers=headers)
    assert hide.status_code == 200, hide.text
    assert hide.json()["data"]["is_published"] is False
    assert _chat_exists(seeded["chat_id"]) is True

    cross_project = client.get(f"/api/v1/community/admin/chats/{seeded['other_chat_id']}", headers=headers)
    assert cross_project.status_code == 404
    assert _audit_count("chat.created", created["id"]) == 1
    assert _audit_count("chat.hidden", str(seeded["chat_id"])) == 1


def test_admin_exchanges_crud_soft_hide_project_scoping_and_audit(client):
    headers = login(client)
    seeded = _seed_links_and_exchanges()

    assert client.get("/api/v1/community/admin/exchanges", headers=headers).status_code == 403
    _set_current_project_user(role="admin")

    create = client.post(
        "/api/v1/community/admin/exchanges",
        headers=headers,
        json={
            "title": "Admin Exchange",
            "description": "Admin description",
            "team_comment": "Stable option",
            "logo_url": None,
            "external_url": "https://exchange.example/admin",
            "promo_code": "ADMIN",
            "sort_order": 4,
            "is_published": True,
        },
    )
    assert create.status_code == 200, create.text
    created = create.json()["data"]
    assert created["title"] == "Admin Exchange"
    assert created["is_published"] is True

    listing = client.get("/api/v1/community/admin/exchanges", headers=headers)
    assert listing.status_code == 200, listing.text
    titles = {item["title"] for item in listing.json()["data"]}
    assert {"Early Exchange", "Late Exchange", "Hidden Exchange", "Admin Exchange"}.issubset(titles)

    detail = client.get(f"/api/v1/community/admin/exchanges/{created['id']}", headers=headers)
    assert detail.status_code == 200, detail.text

    update = client.patch(
        f"/api/v1/community/admin/exchanges/{created['id']}",
        headers=headers,
        json={
            "title": "Updated Exchange",
            "description": "Updated description",
            "team_comment": None,
            "logo_url": None,
            "external_url": "https://exchange.example/updated",
            "promo_code": None,
            "sort_order": 2,
            "is_published": False,
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["data"]["title"] == "Updated Exchange"
    assert update.json()["data"]["is_published"] is False

    hide = client.delete(f"/api/v1/community/admin/exchanges/{seeded['exchange_id']}", headers=headers)
    assert hide.status_code == 200, hide.text
    assert hide.json()["data"]["is_published"] is False
    assert _exchange_exists(seeded["exchange_id"]) is True

    cross_project = client.get(f"/api/v1/community/admin/exchanges/{seeded['other_exchange_id']}", headers=headers)
    assert cross_project.status_code == 404
    assert _audit_count("exchange.created", created["id"]) == 1
    assert _audit_count("exchange.hidden", str(seeded["exchange_id"])) == 1


def _chat_exists(chat_id) -> bool:
    db = SessionLocal()
    try:
        return db.query(CommunityChatLink).filter(CommunityChatLink.id == chat_id).one_or_none() is not None
    finally:
        db.close()


def _exchange_exists(exchange_id) -> bool:
    db = SessionLocal()
    try:
        return db.query(CommunityExchange).filter(CommunityExchange.id == exchange_id).one_or_none() is not None
    finally:
        db.close()


def _audit_count(action: str, entity_id: str) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(CommunityAdminAuditLog)
            .filter(
                CommunityAdminAuditLog.action == action,
                CommunityAdminAuditLog.entity_id == UUID(entity_id),
            )
            .count()
        )
    finally:
        db.close()
