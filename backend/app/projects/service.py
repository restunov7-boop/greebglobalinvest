from sqlalchemy.orm import Session

from app.projects.models import Project, ProjectUser
from app.users.models import User

DEFAULT_PROJECT_SLUG = "doch-vinodela"
DEFAULT_PROJECT_NAME = "Дочь винодела"


def get_project_by_slug(db: Session, slug: str) -> Project | None:
    return db.query(Project).filter(Project.slug == slug).one_or_none()


def ensure_default_project(db: Session) -> Project:
    project = get_project_by_slug(db, DEFAULT_PROJECT_SLUG)
    if project is not None:
        return project

    project = Project(slug=DEFAULT_PROJECT_SLUG, name=DEFAULT_PROJECT_NAME, is_active=True)
    db.add(project)
    db.flush()
    return project


def get_project_user(db: Session, user: User, project: Project) -> ProjectUser | None:
    return (
        db.query(ProjectUser)
        .filter(ProjectUser.user_id == user.id, ProjectUser.project_id == project.id)
        .one_or_none()
    )


def ensure_project_user(db: Session, user: User, project: Project) -> ProjectUser:
    project_user = get_project_user(db, user, project)
    if project_user is not None:
        return project_user

    project_user = ProjectUser(
        user_id=user.id,
        project_id=project.id,
        role="member",
        status="active",
        is_premium=False,
        access_state="active",
        moderation_state="normal",
    )
    db.add(project_user)
    db.flush()
    return project_user


def is_project_access_active(project_user: ProjectUser) -> bool:
    return project_user.access_state == "active"


def is_project_user_banned(project_user: ProjectUser) -> bool:
    return project_user.moderation_state == "banned"
