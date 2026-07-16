from fastapi import APIRouter
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.community.permissions import require_active_community_access
from app.community.schemas import CommunityNotificationSettingsPatch, CommunityProductPurchaseRequestCreate
from app.community.service import (
    create_product_purchase_request,
    get_community_profile,
    get_community_product_detail,
    get_community_rules,
    get_community_settings,
    get_community_dashboard,
    get_community_info,
    get_public_links,
    get_insight_detail,
    get_post_detail,
    list_community_chats,
    list_community_exchanges,
    list_my_purchase_requests,
    list_community_products,
    toggle_insight_useful,
    toggle_post_useful,
    update_notification_settings,
)
from app.database import get_db
from app.projects.models import ProjectUser
from app.shared.responses import success_response

router = APIRouter(prefix="/community", tags=["community"])


@router.get("/info")
def community_info() -> dict[str, object]:
    return success_response(get_community_info().model_dump(mode="json"))


@router.get("/dashboard")
def community_dashboard(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(get_community_dashboard(db, project_user).model_dump(mode="json"))


@router.get("/profile")
def community_profile(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(get_community_profile(db, project_user).model_dump(mode="json"))


@router.get("/settings")
def community_settings(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(get_community_settings(db, project_user).model_dump(mode="json"))


@router.patch("/settings/notifications")
def community_update_notifications(
    payload: CommunityNotificationSettingsPatch,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(update_notification_settings(db, project_user, payload).model_dump(mode="json"))


@router.get("/rules")
def community_rules(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(get_community_rules(db, project_user).model_dump(mode="json"))


@router.get("/public-links")
def community_public_links(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, object]:
    return success_response(get_public_links(db).model_dump(mode="json"))


@router.get("/chats")
def community_chats(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_community_chats(db, project_user)])


@router.get("/exchanges")
def community_exchanges(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_community_exchanges(db, project_user)])


@router.get("/products")
def community_products(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_community_products(db, project_user)])


@router.get("/products/{product_id}")
def community_product_detail(
    product_id: str,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(get_community_product_detail(db, project_user, product_id).model_dump(mode="json"))


@router.post("/products/{product_id}/purchase-request")
def community_create_product_purchase_request(
    product_id: str,
    payload: CommunityProductPurchaseRequestCreate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(create_product_purchase_request(db, project_user, product_id, payload).model_dump(mode="json"))


@router.get("/my-purchase-requests")
def community_my_purchase_requests(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_my_purchase_requests(db, project_user)])


@router.get("/posts/{post_id}")
def community_post_detail(
    post_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(get_post_detail(db, project_user, post_id).model_dump(mode="json"))


@router.get("/insights/{insight_id}")
def community_insight_detail(
    insight_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(get_insight_detail(db, project_user, insight_id).model_dump(mode="json"))


@router.post("/posts/{post_id}/useful")
def community_post_useful(
    post_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(toggle_post_useful(db, project_user, post_id).model_dump(mode="json"))


@router.post("/insights/{insight_id}/useful")
def community_insight_useful(
    insight_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_active_community_access)],
) -> dict[str, object]:
    return success_response(toggle_insight_useful(db, project_user, insight_id).model_dump(mode="json"))
