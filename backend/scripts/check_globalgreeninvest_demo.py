from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.community.models import (  # noqa: E402
    CommunityChatLink,
    CommunityExchange,
    CommunityInsight,
    CommunityPost,
    CommunityProduct,
    CommunityProductAccess,
    CommunityProductMaterial,
    CommunityProjectLink,
)
from app.community.permissions import COMMUNITY_ADMIN_ROLES, COMMUNITY_PROJECT_SLUG  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.projects.models import Project, ProjectUser  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.slug == COMMUNITY_PROJECT_SLUG).one_or_none()
        if project is None:
            print(f"[WARN] Project {COMMUNITY_PROJECT_SLUG!r} does not exist")
            return

        print(f"project_slug={project.slug}")
        print(f"project_id={project.id}")
        project_users = db.query(ProjectUser).filter(ProjectUser.project_id == project.id)
        active_project_users = project_users.filter(ProjectUser.status == "active", ProjectUser.access_state == "active").count()
        admin_project_users = project_users.filter(ProjectUser.role.in_(COMMUNITY_ADMIN_ROLES), ProjectUser.status == "active").count()

        print(f"project_users={project_users.count()}")
        print(f"active_project_users={active_project_users}")
        print(f"active_admin_project_users={admin_project_users}")
        print(f"posts={db.query(CommunityPost).filter(CommunityPost.project_id == project.id).count()}")
        print(f"insights={db.query(CommunityInsight).filter(CommunityInsight.project_id == project.id).count()}")
        print(f"products={db.query(CommunityProduct).filter(CommunityProduct.project_id == project.id).count()}")
        print(f"product_materials={db.query(CommunityProductMaterial).filter(CommunityProductMaterial.project_id == project.id).count()}")
        print(f"product_access_rows={db.query(CommunityProductAccess).filter(CommunityProductAccess.project_id == project.id).count()}")
        print(f"chats={db.query(CommunityChatLink).filter(CommunityChatLink.project_id == project.id).count()}")
        print(f"exchanges={db.query(CommunityExchange).filter(CommunityExchange.project_id == project.id).count()}")

        links = (
            db.query(CommunityProjectLink)
            .filter(CommunityProjectLink.project_id == project.id, CommunityProjectLink.is_active.is_(True))
            .order_by(CommunityProjectLink.type.asc())
            .all()
        )
        for link in links:
            print(f"link.{link.type}={link.url}")

        if active_project_users == 0:
            print("[WARN] No active project_user exists for GlobalGreenInvest")
        if admin_project_users == 0:
            print("[WARN] No active admin/owner project_user exists for GlobalGreenInvest")
        if db.query(CommunityProductAccess).filter(CommunityProductAccess.project_id == project.id).count() == 0:
            print("[WARN] No product access rows exist")
    finally:
        db.close()


if __name__ == "__main__":
    main()
