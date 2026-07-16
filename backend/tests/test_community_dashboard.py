from datetime import UTC, datetime, timedelta

from app.community.models import (
    CommunityChatLink,
    CommunityContentRead,
    CommunityInsight,
    CommunityNotification,
    CommunityPost,
    CommunityReaction,
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


def _seed_dashboard_data() -> dict[str, object]:
    now = datetime.now(UTC)
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project = project_user.project

        other_user = User(display_name="Other", is_active=True)
        db.add(other_user)
        db.flush()
        other_project_user = ProjectUser(
            user_id=other_user.id,
            project_id=project.id,
            role="member",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(other_project_user)
        db.flush()

        other_project = Project(slug="other-community", name="Other Community", is_active=True)
        db.add(other_project)
        db.flush()
        other_project_user_2 = ProjectUser(
            user_id=other_user.id,
            project_id=other_project.id,
            role="member",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(other_project_user_2)
        db.flush()

        pinned = CommunityPost(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="Pinned",
            excerpt="Pinned excerpt",
            content="Pinned content",
            status="published",
            is_pinned=True,
            published_at=now - timedelta(minutes=1),
        )
        db.add(pinned)
        db.flush()

        posts = []
        for index in range(5):
            post = CommunityPost(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title=f"Post {index}",
                excerpt=f"Post excerpt {index}",
                content=f"Post content {index}",
                status="published",
                published_at=now - timedelta(minutes=10 + index),
            )
            posts.append(post)
            db.add(post)

        excluded_posts = [
            CommunityPost(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title="Draft",
                excerpt="Draft excerpt",
                content="Draft content",
                status="draft",
                published_at=now,
            ),
            CommunityPost(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title="Hidden",
                excerpt="Hidden excerpt",
                content="Hidden content",
                status="hidden",
                published_at=now,
            ),
            CommunityPost(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title="Scheduled Future",
                excerpt="Scheduled excerpt",
                content="Scheduled content",
                status="published",
                scheduled_at=now + timedelta(days=1),
                published_at=now,
            ),
            CommunityPost(
                project_id=other_project.id,
                author_project_user_id=other_project_user_2.id,
                title="Other Project Post",
                excerpt="Other excerpt",
                content="Other content",
                status="published",
                published_at=now,
            ),
        ]
        for post in excluded_posts:
            db.add(post)

        urgent = CommunityInsight(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="Urgent Insight",
            excerpt="Urgent excerpt",
            content="Urgent content",
            is_urgent=True,
            status="published",
            published_at=now - timedelta(hours=3),
        )
        regular_new = CommunityInsight(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="Regular Insight Newer",
            excerpt="Regular newer excerpt",
            content="Regular newer content",
            is_urgent=False,
            status="published",
            published_at=now - timedelta(minutes=5),
        )
        regular_old = CommunityInsight(
            project_id=project.id,
            author_project_user_id=project_user.id,
            title="Regular Insight Old",
            excerpt="Regular old excerpt",
            content="Regular old content",
            is_urgent=False,
            status="published",
            published_at=now - timedelta(hours=4),
        )
        excluded_insights = [
            CommunityInsight(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title="Draft Insight",
                excerpt="Draft insight excerpt",
                content="Draft insight content",
                status="draft",
                published_at=now,
            ),
            CommunityInsight(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title="Hidden Insight",
                excerpt="Hidden insight excerpt",
                content="Hidden insight content",
                status="hidden",
                published_at=now,
            ),
            CommunityInsight(
                project_id=project.id,
                author_project_user_id=project_user.id,
                title="Future Insight",
                excerpt="Future insight excerpt",
                content="Future insight content",
                status="published",
                scheduled_at=now + timedelta(days=1),
                published_at=now,
            ),
            CommunityInsight(
                project_id=other_project.id,
                author_project_user_id=other_project_user_2.id,
                title="Other Project Insight",
                excerpt="Other insight excerpt",
                content="Other insight content",
                status="published",
                published_at=now,
            ),
        ]
        db.add_all([urgent, regular_new, regular_old, *excluded_insights])
        db.flush()

        for index in range(6):
            db.add(
                CommunityChatLink(
                    project_id=project.id,
                    title=f"Chat {index}",
                    telegram_url=f"https://t.me/chat{index}",
                    sort_order=index,
                    is_published=True,
                    created_by_project_user_id=project_user.id,
                )
            )
        db.add(
            CommunityChatLink(
                project_id=project.id,
                title="Hidden Chat",
                telegram_url="https://t.me/hidden",
                sort_order=99,
                is_published=False,
                created_by_project_user_id=project_user.id,
            )
        )

        notification = CommunityNotification(
            project_id=project.id,
            project_user_id=project_user.id,
            type="urgent_insight",
            title="Important",
            body="Unread urgent insight",
            target_type="insight",
            target_id=urgent.id,
            is_read=False,
        )
        db.add(notification)
        db.add(
            CommunityNotification(
                project_id=project.id,
                project_user_id=project_user.id,
                type="urgent_insight",
                title="Read notification",
                body="Read urgent insight",
                target_type="insight",
                target_id=regular_old.id,
                is_read=True,
            )
        )

        db.add(CommunityContentRead(project_id=project.id, project_user_id=project_user.id, content_type="post", content_id=posts[0].id))
        db.add(CommunityContentRead(project_id=project.id, project_user_id=project_user.id, content_type="insight", content_id=urgent.id))

        db.add(
            CommunityReaction(
                project_id=project.id,
                project_user_id=project_user.id,
                target_type="post",
                target_id=posts[0].id,
                reaction_type="useful",
            )
        )
        db.add(
            CommunityReaction(
                project_id=project.id,
                project_user_id=other_project_user.id,
                target_type="post",
                target_id=posts[0].id,
                reaction_type="useful",
            )
        )
        db.add(
            CommunityReaction(
                project_id=project.id,
                project_user_id=other_project_user.id,
                target_type="insight",
                target_id=urgent.id,
                reaction_type="useful",
            )
        )

        db.commit()
        return {
            "project_user_id": project_user.id,
            "read_post_id": posts[0].id,
            "urgent_insight_id": urgent.id,
        }
    finally:
        db.close()


def test_active_member_gets_dashboard_with_project_scoped_published_data(client):
    headers = login(client)
    seeded = _seed_dashboard_data()
    before_reads = _content_read_count()

    response = client.get("/api/v1/community/dashboard", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert len(data["important_notifications"]) == 1
    assert data["important_notifications"][0]["title"] == "Important"
    assert data["pinned_post"]["title"] == "Pinned"
    assert len(data["posts"]) == 3
    assert [item["title"] for item in data["posts"]] == ["Post 0", "Post 1", "Post 2"]
    assert len(data["insights"]) == 3
    assert data["insights"][0]["title"] == "Urgent Insight"
    assert data["insights"][0]["is_urgent"] is True
    assert len(data["chat_links"]) == 5
    assert [item["sort_order"] for item in data["chat_links"]] == [0, 1, 2, 3, 4]

    returned_titles = {data["pinned_post"]["title"]}
    returned_titles.update(item["title"] for item in data["posts"])
    returned_titles.update(item["title"] for item in data["insights"])
    assert "Draft" not in returned_titles
    assert "Hidden" not in returned_titles
    assert "Scheduled Future" not in returned_titles
    assert "Other Project Post" not in returned_titles
    assert "Draft Insight" not in returned_titles
    assert "Hidden Insight" not in returned_titles
    assert "Future Insight" not in returned_titles
    assert "Other Project Insight" not in returned_titles

    read_post = next(item for item in data["posts"] if item["id"] == str(seeded["read_post_id"]))
    assert read_post["is_new"] is False
    assert read_post["useful_count"] == 2
    assert read_post["is_useful_by_me"] is True
    unread_post = next(item for item in data["posts"] if item["title"] == "Post 1")
    assert unread_post["is_new"] is True
    assert unread_post["useful_count"] == 0
    assert unread_post["is_useful_by_me"] is False

    urgent = next(item for item in data["insights"] if item["id"] == str(seeded["urgent_insight_id"]))
    assert urgent["is_new"] is False
    assert urgent["useful_count"] == 1
    assert urgent["is_useful_by_me"] is False
    assert _content_read_count() == before_reads


def test_dashboard_blocks_inactive_and_banned_members(client):
    headers = login(client)

    for access_state in ("pending", "expired", "revoked"):
        _set_project_user_state(access_state=access_state, moderation_state="normal")
        response = client.get("/api/v1/community/dashboard", headers=headers)
        assert response.status_code == 403

    _set_project_user_state(access_state="active", moderation_state="banned")
    response = client.get("/api/v1/community/dashboard", headers=headers)
    assert response.status_code == 403


def _set_project_user_state(access_state: str, moderation_state: str) -> None:
    db = SessionLocal()
    try:
        project_user = db.merge(_current_project_user())
        project_user.access_state = access_state
        project_user.moderation_state = moderation_state
        db.commit()
    finally:
        db.close()


def _content_read_count() -> int:
    db = SessionLocal()
    try:
        return db.query(CommunityContentRead).count()
    finally:
        db.close()
