from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.community.models import CommunityAdminAuditLog, CommunityInsight, CommunityPost
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


def _seed_admin_content() -> dict[str, object]:
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project = project_user.project
        other_user = User(display_name="Other Admin", is_active=True)
        db.add(other_user)
        db.flush()
        other_project = Project(slug="admin-content-other", name="Other Admin Content", is_active=True)
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

        posts = [
            CommunityPost(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title=f"{status} post",
                excerpt="Post excerpt",
                content="Post content",
                status=status,
                scheduled_at=now + timedelta(days=1) if status == "scheduled" else None,
                published_at=now if status == "published" else None,
            )
            for status in ("draft", "scheduled", "published", "hidden")
        ]
        insights = [
            CommunityInsight(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title=f"{status} insight",
                excerpt="Insight excerpt",
                content="Insight content",
                status=status,
                scheduled_at=now + timedelta(days=1) if status == "scheduled" else None,
                published_at=now if status == "published" else None,
            )
            for status in ("draft", "scheduled", "published", "hidden")
        ]
        other_post = CommunityPost(
            project_id=other_project.id,
            author_project_user_id=other_project_user.id,
            title="Other project post",
            excerpt="Other",
            content="Other",
            status="published",
            published_at=now,
        )
        other_insight = CommunityInsight(
            project_id=other_project.id,
            author_project_user_id=other_project_user.id,
            title="Other project insight",
            excerpt="Other",
            content="Other",
            status="published",
            published_at=now,
        )
        db.add_all([*posts, *insights, other_post, other_insight])
        db.commit()
        return {
            "draft_post_id": posts[0].id,
            "published_post_id": posts[2].id,
            "other_post_id": other_post.id,
            "draft_insight_id": insights[0].id,
            "published_insight_id": insights[2].id,
            "other_insight_id": other_insight.id,
        }
    finally:
        db.close()


def test_admin_content_permissions(client):
    headers = login(client)

    member_response = client.get("/api/v1/community/admin/posts", headers=headers)
    assert member_response.status_code == 403

    _set_current_project_user(role="admin")
    admin_response = client.get("/api/v1/community/admin/posts", headers=headers)
    assert admin_response.status_code == 200, admin_response.text

    _set_current_project_user(role="owner")
    owner_response = client.get("/api/v1/community/admin/posts", headers=headers)
    assert owner_response.status_code == 200, owner_response.text

    _set_current_project_user(role="admin", moderation_state="banned")
    banned_response = client.get("/api/v1/community/admin/posts", headers=headers)
    assert banned_response.status_code == 403


def test_admin_posts_crud_is_project_scoped_and_hidden_content_is_member_invisible(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    seeded = _seed_admin_content()

    list_response = client.get("/api/v1/community/admin/posts", headers=headers)
    assert list_response.status_code == 200, list_response.text
    list_data = list_response.json()["data"]
    assert list_data["total"] == 4
    assert {item["status"] for item in list_data["items"]} == {"draft", "scheduled", "published", "hidden"}

    published_filter = client.get("/api/v1/community/admin/posts?status=published", headers=headers)
    assert published_filter.status_code == 200, published_filter.text
    assert published_filter.json()["data"]["total"] == 1

    cross_project = client.get(f"/api/v1/community/admin/posts/{seeded['other_post_id']}", headers=headers)
    assert cross_project.status_code == 404

    draft_payload = {
        "title": "Created draft",
        "excerpt": "Created draft excerpt",
        "content": "Created draft content",
        "status": "draft",
        "is_pinned": False,
    }
    draft_response = client.post("/api/v1/community/admin/posts", headers=headers, json=draft_payload)
    assert draft_response.status_code == 200, draft_response.text
    draft_data = draft_response.json()["data"]
    assert draft_data["status"] == "draft"
    assert draft_data["view_count"] == 0

    published_response = client.post(
        "/api/v1/community/admin/posts",
        headers=headers,
        json={**draft_payload, "title": "Created published", "status": "published", "is_pinned": True},
    )
    assert published_response.status_code == 200, published_response.text
    published_data = published_response.json()["data"]
    assert published_data["status"] == "published"
    assert published_data["published_at"] is not None
    assert published_data["is_pinned"] is True

    detail_response = client.get(f"/api/v1/community/admin/posts/{draft_data['id']}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["data"]["content"] == "Created draft content"

    update_response = client.patch(
        f"/api/v1/community/admin/posts/{draft_data['id']}",
        headers=headers,
        json={"title": "Updated post", "status": "published"},
    )
    assert update_response.status_code == 200, update_response.text
    updated_data = update_response.json()["data"]
    assert updated_data["title"] == "Updated post"
    assert updated_data["status"] == "published"
    assert updated_data["published_at"] is not None

    delete_response = client.delete(f"/api/v1/community/admin/posts/{seeded['published_post_id']}", headers=headers)
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["data"]["status"] == "hidden"
    assert _post_exists(seeded["published_post_id"]) is True

    member_detail = client.get(f"/api/v1/community/posts/{seeded['published_post_id']}", headers=headers)
    assert member_detail.status_code == 404
    dashboard = client.get("/api/v1/community/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    dashboard_titles = {item["title"] for item in dashboard.json()["data"]["posts"]}
    assert "published post" not in dashboard_titles


def test_admin_insights_crud_is_project_scoped_and_never_sends_telegram(client):
    headers = login(client)
    _set_current_project_user(role="admin")
    seeded = _seed_admin_content()

    list_response = client.get("/api/v1/community/admin/insights", headers=headers)
    assert list_response.status_code == 200, list_response.text
    list_data = list_response.json()["data"]
    assert list_data["total"] == 4
    assert {item["status"] for item in list_data["items"]} == {"draft", "scheduled", "published", "hidden"}

    hidden_filter = client.get("/api/v1/community/admin/insights?status=hidden", headers=headers)
    assert hidden_filter.status_code == 200, hidden_filter.text
    assert hidden_filter.json()["data"]["total"] == 1

    cross_project = client.get(f"/api/v1/community/admin/insights/{seeded['other_insight_id']}", headers=headers)
    assert cross_project.status_code == 404

    draft_payload = {
        "title": "Created draft insight",
        "excerpt": "Created draft insight excerpt",
        "content": "Created draft insight content",
        "is_urgent": False,
        "status": "draft",
    }
    draft_response = client.post("/api/v1/community/admin/insights", headers=headers, json=draft_payload)
    assert draft_response.status_code == 200, draft_response.text
    draft_data = draft_response.json()["data"]
    assert draft_data["status"] == "draft"
    assert draft_data["view_count"] == 0

    urgent_response = client.post(
        "/api/v1/community/admin/insights",
        headers=headers,
        json={**draft_payload, "title": "Urgent published insight", "status": "published", "is_urgent": True},
    )
    assert urgent_response.status_code == 200, urgent_response.text
    urgent_data = urgent_response.json()["data"]
    assert urgent_data["status"] == "published"
    assert urgent_data["published_at"] is not None
    assert urgent_data["is_urgent"] is True
    assert urgent_data["telegram_notification_sent_at"] is None

    detail_response = client.get(f"/api/v1/community/admin/insights/{draft_data['id']}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["data"]["content"] == "Created draft insight content"

    update_response = client.patch(
        f"/api/v1/community/admin/insights/{draft_data['id']}",
        headers=headers,
        json={"title": "Updated insight", "status": "published", "is_urgent": True},
    )
    assert update_response.status_code == 200, update_response.text
    updated_data = update_response.json()["data"]
    assert updated_data["title"] == "Updated insight"
    assert updated_data["status"] == "published"
    assert updated_data["published_at"] is not None
    assert updated_data["telegram_notification_sent_at"] is None

    delete_response = client.delete(f"/api/v1/community/admin/insights/{seeded['published_insight_id']}", headers=headers)
    assert delete_response.status_code == 200, delete_response.text
    assert delete_response.json()["data"]["status"] == "hidden"
    assert _insight_exists(seeded["published_insight_id"]) is True

    member_detail = client.get(f"/api/v1/community/insights/{seeded['published_insight_id']}", headers=headers)
    assert member_detail.status_code == 404
    dashboard = client.get("/api/v1/community/dashboard", headers=headers)
    assert dashboard.status_code == 200, dashboard.text
    dashboard_titles = {item["title"] for item in dashboard.json()["data"]["insights"]}
    assert "published insight" not in dashboard_titles


def test_admin_scheduled_validation_and_audit_log(client):
    headers = login(client)
    _set_current_project_user(role="admin")

    invalid_post = client.post(
        "/api/v1/community/admin/posts",
        headers=headers,
        json={
            "title": "Scheduled without date",
            "excerpt": "Excerpt",
            "content": "Content",
            "status": "scheduled",
            "is_pinned": False,
        },
    )
    assert invalid_post.status_code == 422

    insight_response = client.post(
        "/api/v1/community/admin/insights",
        headers=headers,
        json={
            "title": "Audited urgent insight",
            "excerpt": "Excerpt",
            "content": "Content",
            "is_urgent": True,
            "status": "published",
        },
    )
    assert insight_response.status_code == 200, insight_response.text
    insight_id = insight_response.json()["data"]["id"]
    assert _audit_count("urgent_insight.published", insight_id) == 1


def _post_exists(post_id) -> bool:
    db = SessionLocal()
    try:
        return db.query(CommunityPost).filter(CommunityPost.id == post_id).one_or_none() is not None
    finally:
        db.close()


def _insight_exists(insight_id) -> bool:
    db = SessionLocal()
    try:
        return db.query(CommunityInsight).filter(CommunityInsight.id == insight_id).one_or_none() is not None
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
