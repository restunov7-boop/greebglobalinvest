from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.schemas import AuthSession, MeResponse
from app.auth.telegram import validate_telegram_init_data
from app.permissions.service import get_capabilities_for_role
from app.projects.models import ProjectUser
from app.projects.schemas import ProjectUserRead
from app.projects.service import ensure_default_project, ensure_project_user
from app.shared.errors import AuthenticationError
from app.users.models import User
from app.users.schemas import UserSummary
from app.users.service import create_or_update_telegram_identity, create_user_from_telegram, get_telegram_identity


def authenticate_with_telegram(db: Session, init_data: str) -> AuthSession:
    telegram_user = validate_telegram_init_data(init_data)
    identity = get_telegram_identity(db, telegram_user.telegram_id)

    if identity is None:
        user = create_user_from_telegram(db, telegram_user)
    else:
        user = identity.user
        if telegram_user.display_name and not user.display_name:
            user.display_name = telegram_user.display_name
        if telegram_user.photo_url:
            user.avatar_url = telegram_user.photo_url

    create_or_update_telegram_identity(db, user, telegram_user)
    project = ensure_default_project(db)
    project_user = ensure_project_user(db, user, project)
    db.commit()
    db.refresh(user)
    db.refresh(project_user)
    db.refresh(project_user.project)

    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"project_user_id": str(project_user.id), "project_id": str(project.id)},
    )
    return AuthSession(
        access_token=access_token,
        user=UserSummary.model_validate(user),
        project_user=project_user_to_read(project_user),
    )


def build_me_response(user: User, project_user: ProjectUser) -> MeResponse:
    return MeResponse(
        user=UserSummary.model_validate(user),
        project_user=project_user_to_read(project_user),
    )


def user_id_from_token_payload(payload: dict[str, object]) -> UUID:
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise AuthenticationError("Access token subject is missing")
    try:
        return UUID(subject)
    except ValueError as exc:
        raise AuthenticationError("Access token subject is invalid") from exc


def project_user_to_read(project_user: ProjectUser) -> ProjectUserRead:
    return ProjectUserRead(
        project_slug=project_user.project.slug,
        role=project_user.role,
        status=project_user.status,
        is_premium=project_user.is_premium,
        premium_until=project_user.premium_until,
        access_state=project_user.access_state,
        access_until=project_user.access_until,
        moderation_state=project_user.moderation_state,
        capabilities=get_capabilities_for_role(project_user.role),
    )
