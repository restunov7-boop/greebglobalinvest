from datetime import UTC, datetime, timedelta

from app.community.models import CommunityContentRead, CommunityInsight, CommunityPost, CommunityReaction
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


def _seed_content() -> dict[str, object]:
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project = project_user.project

        other_user = User(display_name="Other", is_active=True)
        db.add(other_user)
        db.flush()
        other_project = Project(slug="other-detail-project", name="Other Detail Project", is_active=True)
        db.add(other_project)
        db.flush()
        other_project_user = ProjectUser(
            user_id=other_user.id,
            project_id=other_project.id,
            role="member",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(other_project_user)
        db.flush()

        post = CommunityPost(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="Published Post",
            excerpt="Published post excerpt",
            content="Published post content",
            status="published",
            published_at=now,
        )
        insight = CommunityInsight(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="Published Insight",
            excerpt="Published insight excerpt",
            content="Published insight content",
            is_urgent=True,
            status="published",
            published_at=now,
        )
        db.add_all([post, insight])
        db.flush()

        blocked_posts = []
        blocked_insights = []
        for status in ("draft", "hidden", "scheduled"):
            blocked_posts.append(
                CommunityPost(
                    project_id=project.id,
                    author_project_user_id=project_user.id,
                    title=f"{status} post",
                    excerpt="blocked",
                    content="blocked",
                    status=status,
                    published_at=now,
                    scheduled_at=now + timedelta(days=1) if status == "scheduled" else None,
                )
            )
            blocked_insights.append(
                CommunityInsight(
                    project_id=project.id,
                    author_project_user_id=project_user.id,
                    title=f"{status} insight",
                    excerpt="blocked",
                    content="blocked",
                    status=status,
                    published_at=now,
                    scheduled_at=now + timedelta(days=1) if status == "scheduled" else None,
                )
            )
        future_post = CommunityPost(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="future post",
            excerpt="blocked",
            content="blocked",
            status="published",
            published_at=now,
            scheduled_at=now + timedelta(days=1),
        )
        future_insight = CommunityInsight(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="future insight",
            excerpt="blocked",
            content="blocked",
            status="published",
            published_at=now,
            scheduled_at=now + timedelta(days=1),
        )
        other_post = CommunityPost(
            project_id=other_project.id,
            author_project_user_id=other_project_user.id,
            title="Other Post",
            excerpt="other",
            content="other",
            status="published",
            published_at=now,
        )
        other_insight = CommunityInsight(
            project_id=other_project.id,
            author_project_user_id=other_project_user.id,
            title="Other Insight",
            excerpt="other",
            content="other",
            status="published",
            published_at=now,
        )
        db.add_all([*blocked_posts, *blocked_insights, future_post, future_insight, other_post, other_insight])
        db.flush()

        db.commit()
        return {
            "project_user_id": project_user.id,
            "post_id": post.id,
            "insight_id": insight.id,
            "blocked_post_ids": [item.id for item in [*blocked_posts, future_post, other_post]],
            "blocked_insight_ids": [item.id for item in [*blocked_insights, future_insight, other_insight]],
        }
    finally:
        db.close()


def test_active_member_can_open_published_post_and_insight_and_read_state_is_idempotent(client):
    headers = login(client)
    seeded = _seed_content()

    first_post = client.get(f"/api/v1/community/posts/{seeded['post_id']}", headers=headers)
    second_post = client.get(f"/api/v1/community/posts/{seeded['post_id']}", headers=headers)
    insight = client.get(f"/api/v1/community/insights/{seeded['insight_id']}", headers=headers)

    assert first_post.status_code == 200, first_post.text
    assert second_post.status_code == 200, second_post.text
    assert insight.status_code == 200, insight.text

    first_post_data = first_post.json()["data"]
    second_post_data = second_post.json()["data"]
    insight_data = insight.json()["data"]

    assert first_post_data["title"] == "Published Post"
    assert first_post_data["content"] == "Published post content"
    assert first_post_data["is_new"] is False
    assert first_post_data["view_count"] == 1
    assert second_post_data["view_count"] == 2
    assert insight_data["title"] == "Published Insight"
    assert insight_data["is_urgent"] is True
    assert insight_data["is_new"] is False
    assert insight_data["view_count"] == 1

    assert _read_count(seeded["project_user_id"], "post", seeded["post_id"]) == 1
    assert _read_count(seeded["project_user_id"], "insight", seeded["insight_id"]) == 1


def test_detail_blocks_inactive_banned_unpublished_and_cross_project_content(client):
    headers = login(client)
    seeded = _seed_content()

    for access_state in ("pending", "expired", "revoked"):
        _set_project_user_state(access_state=access_state, moderation_state="normal")
        response = client.get(f"/api/v1/community/posts/{seeded['post_id']}", headers=headers)
        assert response.status_code == 403

    _set_project_user_state(access_state="active", moderation_state="banned")
    response = client.get(f"/api/v1/community/insights/{seeded['insight_id']}", headers=headers)
    assert response.status_code == 403

    _set_project_user_state(access_state="active", moderation_state="normal")
    for post_id in seeded["blocked_post_ids"]:
        response = client.get(f"/api/v1/community/posts/{post_id}", headers=headers)
        assert response.status_code == 404
        toggle = client.post(f"/api/v1/community/posts/{post_id}/useful", headers=headers)
        assert toggle.status_code == 404

    for insight_id in seeded["blocked_insight_ids"]:
        response = client.get(f"/api/v1/community/insights/{insight_id}", headers=headers)
        assert response.status_code == 404
        toggle = client.post(f"/api/v1/community/insights/{insight_id}/useful", headers=headers)
        assert toggle.status_code == 404


def test_useful_toggle_for_post_and_insight(client):
    headers = login(client)
    seeded = _seed_content()

    post_on = client.post(f"/api/v1/community/posts/{seeded['post_id']}/useful", headers=headers)
    post_off = client.post(f"/api/v1/community/posts/{seeded['post_id']}/useful", headers=headers)
    insight_on = client.post(f"/api/v1/community/insights/{seeded['insight_id']}/useful", headers=headers)
    insight_off = client.post(f"/api/v1/community/insights/{seeded['insight_id']}/useful", headers=headers)

    assert post_on.status_code == 200, post_on.text
    assert post_on.json()["data"] == {"useful_count": 1, "is_useful_by_me": True}
    assert post_off.status_code == 200, post_off.text
    assert post_off.json()["data"] == {"useful_count": 0, "is_useful_by_me": False}
    assert insight_on.status_code == 200, insight_on.text
    assert insight_on.json()["data"] == {"useful_count": 1, "is_useful_by_me": True}
    assert insight_off.status_code == 200, insight_off.text
    assert insight_off.json()["data"] == {"useful_count": 0, "is_useful_by_me": False}

    assert _reaction_count(seeded["project_user_id"], "post", seeded["post_id"]) == 0
    assert _reaction_count(seeded["project_user_id"], "insight", seeded["insight_id"]) == 0


def _set_project_user_state(access_state: str, moderation_state: str) -> None:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project_user.access_state = access_state
        project_user.moderation_state = moderation_state
        db.commit()
    finally:
        db.close()


def _read_count(project_user_id, content_type: str, content_id) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(CommunityContentRead)
            .filter(
                CommunityContentRead.project_user_id == project_user_id,
                CommunityContentRead.content_type == content_type,
                CommunityContentRead.content_id == content_id,
            )
            .count()
        )
    finally:
        db.close()


def _reaction_count(project_user_id, target_type: str, target_id) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(CommunityReaction)
            .filter(
                CommunityReaction.project_user_id == project_user_id,
                CommunityReaction.target_type == target_type,
                CommunityReaction.target_id == target_id,
            )
            .count()
        )
    finally:
        db.close()
