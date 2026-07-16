from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.schemas import TelegramAuthRequest
from app.auth.service import authenticate_with_telegram, build_me_response
from app.database import get_db
from app.permissions.dependencies import require_auth, require_project_user
from app.shared.responses import success_response
from app.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram")
def login_with_telegram(
    payload: TelegramAuthRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    session = authenticate_with_telegram(db, payload.init_data, project_slug=payload.project_slug)
    return success_response(session.model_dump(mode="json"))


@router.get("/me")
def get_me(
    user: Annotated[User, Depends(require_auth)],
    project_user=Depends(require_project_user),
) -> dict[str, object]:
    return success_response(build_me_response(user, project_user).model_dump(mode="json"))
