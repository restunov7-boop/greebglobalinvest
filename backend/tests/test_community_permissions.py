from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import uuid

import pytest

from app.community.models import CommunityProduct, CommunityProductAccess
from app.community.permissions import (
    assert_same_project,
    has_active_product_access,
    is_community_admin,
    is_project_access_active,
    is_project_user_banned,
    is_published_content,
    require_active_community_access,
    require_community_admin,
    require_not_banned,
    require_product_access,
    require_published_content,
    require_same_project,
)
from app.database import SessionLocal
from app.projects.models import ProjectUser
from app.projects.service import ensure_default_project
from app.shared.errors import NotFoundError, PermissionDeniedError
from app.users.models import User


def project_user(**overrides: object) -> ProjectUser:
    values = {
        "id": uuid.uuid4(),
        "project_id": uuid.uuid4(),
        "user_id": uuid.uuid4(),
        "role": "member",
        "status": "active",
        "access_state": "active",
        "access_until": None,
        "moderation_state": "normal",
    }
    values.update(overrides)
    return ProjectUser(**values)


def test_active_project_access_passes():
    user = project_user()

    assert is_project_access_active(user) is True
    assert require_active_community_access(user) is user


@pytest.mark.parametrize("access_state", ["pending", "expired", "revoked"])
def test_inactive_access_states_fail(access_state):
    user = project_user(access_state=access_state)

    assert is_project_access_active(user) is False
    with pytest.raises(PermissionDeniedError):
        require_active_community_access(user)


def test_expired_access_until_fails():
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    user = project_user(access_until=datetime(2000, 1, 1, tzinfo=UTC))

    assert is_project_access_active(user, now=now) is False
    with pytest.raises(PermissionDeniedError):
        require_active_community_access(user)


def test_banned_user_fails_even_with_active_access():
    user = project_user(access_state="active", moderation_state="banned")

    assert is_project_user_banned(user) is True
    with pytest.raises(PermissionDeniedError):
        require_not_banned(user)
    with pytest.raises(PermissionDeniedError):
        require_active_community_access(user)


@pytest.mark.parametrize("role", ["owner", "admin"])
def test_owner_and_admin_pass_admin_check(role):
    user = project_user(role=role)

    assert is_community_admin(user) is True
    assert require_community_admin(user) is user


def test_member_fails_admin_check():
    user = project_user(role="member")

    assert is_community_admin(user) is False
    with pytest.raises(PermissionDeniedError):
        require_community_admin(user)


def test_same_project_helpers_allow_matching_project():
    project_id = uuid.uuid4()
    entity = SimpleNamespace(project_id=project_id)

    assert_same_project(project_id, project_id)
    assert require_same_project(entity, project_id) is entity


def test_same_project_helpers_hide_mismatched_project():
    with pytest.raises(NotFoundError):
        assert_same_project(uuid.uuid4(), uuid.uuid4())

    with pytest.raises(NotFoundError):
        require_same_project(SimpleNamespace(project_id=uuid.uuid4()), uuid.uuid4())


def test_published_content_requires_status_published_and_dates():
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    published = SimpleNamespace(status="published", published_at=now, scheduled_at=None)
    scheduled_past = SimpleNamespace(status="published", published_at=now, scheduled_at=now - timedelta(minutes=1))
    scheduled_future = SimpleNamespace(status="published", published_at=now, scheduled_at=now + timedelta(minutes=1))
    draft = SimpleNamespace(status="draft", published_at=now, scheduled_at=None)
    missing_published_at = SimpleNamespace(status="published", published_at=None, scheduled_at=None)

    assert is_published_content(published, now=now) is True
    assert is_published_content(scheduled_past, now=now) is True
    assert is_published_content(scheduled_future, now=now) is False
    assert is_published_content(draft, now=now) is False
    assert is_published_content(missing_published_at, now=now) is False
    assert require_published_content(published) is published

    with pytest.raises(NotFoundError):
        require_published_content(draft)


def test_product_access_helper_handles_active_expired_revoked_and_lifetime_access():
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    db = SessionLocal()
    try:
        project = ensure_default_project(db)
        user = User(display_name="Product Access User", is_active=True)
        db.add(user)
        db.flush()

        member = ProjectUser(
            user_id=user.id,
            project_id=project.id,
            role="member",
            status="active",
            is_premium=False,
            access_state="active",
            moderation_state="normal",
        )
        db.add(member)
        db.flush()

        product = CommunityProduct(
            project_id=project.id,
            slug="skin-farm-type-1",
            title="Skin Farm Type 1",
            short_description="Product placeholder",
            description="Product placeholder",
            access_duration_type="lifetime",
            created_by_project_user_id=member.id,
        )
        db.add(product)
        db.flush()

        access = CommunityProductAccess(
            project_id=project.id,
            product_id=product.id,
            project_user_id=member.id,
            access_state="active",
            access_until=None,
            source="manual",
            granted_by_project_user_id=member.id,
        )
        db.add(access)
        db.flush()

        assert has_active_product_access(db, project.id, member.id, product.id, now=now) is True
        assert require_product_access(product.id, db, member) is member

        access.access_until = datetime(2000, 1, 1, tzinfo=UTC)
        db.flush()
        assert has_active_product_access(db, project.id, member.id, product.id, now=now) is False
        with pytest.raises(PermissionDeniedError):
            require_product_access(product.id, db, member)

        access.access_until = None
        access.access_state = "revoked"
        db.flush()
        assert has_active_product_access(db, project.id, member.id, product.id, now=now) is False

        access.access_state = "expired"
        db.flush()
        assert has_active_product_access(db, project.id, member.id, product.id, now=now) is False

        access.access_state = "active"
        access.access_until = now + timedelta(days=1)
        db.flush()
        assert has_active_product_access(db, project.id, member.id, product.id, now=now) is True

        assert has_active_product_access(db, uuid.uuid4(), member.id, product.id, now=now) is False
        assert has_active_product_access(db, project.id, uuid.uuid4(), product.id, now=now) is False
        assert has_active_product_access(db, project.id, member.id, uuid.uuid4(), now=now) is False
    finally:
        db.close()
