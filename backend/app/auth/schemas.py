from pydantic import BaseModel

from app.projects.schemas import ProjectUserRead
from app.users.schemas import UserSummary


class TelegramAuthRequest(BaseModel):
    init_data: str
    project_slug: str | None = None


class AuthSession(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary
    project_user: ProjectUserRead


class MeResponse(BaseModel):
    user: UserSummary
    project_user: ProjectUserRead
