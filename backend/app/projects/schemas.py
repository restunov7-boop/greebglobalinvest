from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectRead(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ProjectUserRead(BaseModel):
    project_slug: str
    role: str
    status: str
    is_premium: bool
    premium_until: datetime | None = None
    access_state: str
    access_until: datetime | None = None
    moderation_state: str
    capabilities: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
