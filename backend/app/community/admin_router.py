from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.community.permissions import require_community_admin
from app.community.schemas import (
    CommunityAdminChatPayload,
    CommunityAdminExchangePayload,
    CommunityAdminInsightCreate,
    CommunityAdminInsightUpdate,
    CommunityAdminNotificationProcessPayload,
    CommunityAdminPostCreate,
    CommunityAdminPostUpdate,
    CommunityAdminProductAccessCreate,
    CommunityAdminProductAccessUpdate,
    CommunityAdminPurchaseRequestApproveGrant,
    CommunityAdminPurchaseRequestUpdate,
    CommunityAdminProductMaterialPayload,
    CommunityAdminProductPayload,
    CommunityAdminUserProjectAccessUpdate,
)
from app.community.service import (
    approve_and_grant_purchase_request,
    ban_admin_user,
    create_admin_chat,
    create_admin_exchange,
    create_admin_insight,
    create_admin_post,
    create_admin_product,
    create_admin_product_material,
    delete_admin_product_material,
    get_admin_product,
    get_admin_notification_sender_status,
    get_admin_chat,
    get_admin_exchange,
    get_admin_insight,
    get_admin_post,
    get_admin_user_detail,
    get_community_info,
    hide_admin_chat,
    hide_admin_exchange,
    hide_admin_insight,
    hide_admin_post,
    hide_admin_product,
    list_admin_chats,
    list_admin_exchanges,
    list_admin_insights,
    list_admin_notifications,
    list_admin_posts,
    list_admin_product_access,
    list_admin_product_materials,
    list_admin_products,
    list_admin_purchase_requests,
    list_admin_users,
    process_pending_telegram_notifications,
    extend_admin_user_one_year,
    grant_admin_product_access,
    unban_admin_user,
    update_admin_user_project_access,
    update_admin_product_access,
    update_admin_purchase_request,
    update_admin_product,
    update_admin_product_material,
    update_admin_chat,
    update_admin_exchange,
    update_admin_insight,
    update_admin_post,
)
from app.database import get_db
from app.projects.models import ProjectUser
from app.shared.responses import success_response

router = APIRouter(prefix="/community/admin", tags=["community-admin"])


@router.get("/info")
def community_admin_info(
    _: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_community_info(scope="admin").model_dump(mode="json"))


@router.get("/notifications")
def community_admin_notifications(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
    type: str | None = Query(None),
    status: str = Query("all"),
    limit: int = Query(50),
    offset: int = Query(0),
) -> dict[str, object]:
    return success_response(
        list_admin_notifications(
            db,
            project_user,
            kind=type,
            status=status,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")
    )


@router.get("/notifications/sender-status")
def community_admin_notification_sender_status(
    _: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_admin_notification_sender_status().model_dump(mode="json"))


@router.post("/notifications/process-pending")
def community_admin_process_pending_notifications(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
    payload: CommunityAdminNotificationProcessPayload | None = None,
) -> dict[str, object]:
    selected_payload = payload or CommunityAdminNotificationProcessPayload()
    return success_response(
        process_pending_telegram_notifications(
            db,
            project_user,
            limit=selected_payload.limit,
            dry_run=selected_payload.dry_run,
        ).model_dump(mode="json")
    )


@router.get("/purchase-requests")
def community_admin_purchase_requests(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
    status: str = Query("all"),
    product_id: UUID | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
) -> dict[str, object]:
    return success_response(
        list_admin_purchase_requests(
            db,
            project_user,
            status=status,
            product_id=product_id,
            q=q,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")
    )


@router.patch("/purchase-requests/{request_id}")
def community_admin_update_purchase_request(
    request_id: UUID,
    payload: CommunityAdminPurchaseRequestUpdate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_purchase_request(db, project_user, request_id, payload).model_dump(mode="json"))


@router.post("/purchase-requests/{request_id}/approve-and-grant")
def community_admin_approve_and_grant_purchase_request(
    request_id: UUID,
    payload: CommunityAdminPurchaseRequestApproveGrant,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(approve_and_grant_purchase_request(db, project_user, request_id, payload).model_dump(mode="json"))


@router.get("/posts")
def community_admin_posts(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
    status: str = Query("all"),
    limit: int = Query(20),
    offset: int = Query(0),
) -> dict[str, object]:
    return success_response(list_admin_posts(db, project_user, status=status, limit=limit, offset=offset).model_dump(mode="json"))


@router.post("/posts")
def community_admin_create_post(
    payload: CommunityAdminPostCreate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(create_admin_post(db, project_user, payload).model_dump(mode="json"))


@router.get("/posts/{post_id}")
def community_admin_post_detail(
    post_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_admin_post(db, project_user, post_id).model_dump(mode="json"))


@router.patch("/posts/{post_id}")
def community_admin_update_post(
    post_id: UUID,
    payload: CommunityAdminPostUpdate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_post(db, project_user, post_id, payload).model_dump(mode="json"))


@router.delete("/posts/{post_id}")
def community_admin_hide_post(
    post_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(hide_admin_post(db, project_user, post_id).model_dump(mode="json"))


@router.get("/insights")
def community_admin_insights(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
    status: str = Query("all"),
    limit: int = Query(20),
    offset: int = Query(0),
) -> dict[str, object]:
    return success_response(list_admin_insights(db, project_user, status=status, limit=limit, offset=offset).model_dump(mode="json"))


@router.post("/insights")
def community_admin_create_insight(
    payload: CommunityAdminInsightCreate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(create_admin_insight(db, project_user, payload).model_dump(mode="json"))


@router.get("/insights/{insight_id}")
def community_admin_insight_detail(
    insight_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_admin_insight(db, project_user, insight_id).model_dump(mode="json"))


@router.patch("/insights/{insight_id}")
def community_admin_update_insight(
    insight_id: UUID,
    payload: CommunityAdminInsightUpdate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_insight(db, project_user, insight_id, payload).model_dump(mode="json"))


@router.delete("/insights/{insight_id}")
def community_admin_hide_insight(
    insight_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(hide_admin_insight(db, project_user, insight_id).model_dump(mode="json"))


@router.get("/chats")
def community_admin_chats(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_admin_chats(db, project_user)])


@router.post("/chats")
def community_admin_create_chat(
    payload: CommunityAdminChatPayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(create_admin_chat(db, project_user, payload).model_dump(mode="json"))


@router.get("/chats/{chat_id}")
def community_admin_chat_detail(
    chat_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_admin_chat(db, project_user, chat_id).model_dump(mode="json"))


@router.patch("/chats/{chat_id}")
def community_admin_update_chat(
    chat_id: UUID,
    payload: CommunityAdminChatPayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_chat(db, project_user, chat_id, payload).model_dump(mode="json"))


@router.delete("/chats/{chat_id}")
def community_admin_hide_chat(
    chat_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(hide_admin_chat(db, project_user, chat_id).model_dump(mode="json"))


@router.get("/exchanges")
def community_admin_exchanges(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_admin_exchanges(db, project_user)])


@router.post("/exchanges")
def community_admin_create_exchange(
    payload: CommunityAdminExchangePayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(create_admin_exchange(db, project_user, payload).model_dump(mode="json"))


@router.get("/exchanges/{exchange_id}")
def community_admin_exchange_detail(
    exchange_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_admin_exchange(db, project_user, exchange_id).model_dump(mode="json"))


@router.patch("/exchanges/{exchange_id}")
def community_admin_update_exchange(
    exchange_id: UUID,
    payload: CommunityAdminExchangePayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_exchange(db, project_user, exchange_id, payload).model_dump(mode="json"))


@router.delete("/exchanges/{exchange_id}")
def community_admin_hide_exchange(
    exchange_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(hide_admin_exchange(db, project_user, exchange_id).model_dump(mode="json"))


@router.get("/users")
def community_admin_users(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
    q: str | None = Query(None),
    access_state: str = Query("all"),
    moderation_state: str = Query("all"),
    role: str = Query("all"),
    limit: int = Query(20),
    offset: int = Query(0),
) -> dict[str, object]:
    return success_response(
        list_admin_users(
            db,
            project_user,
            q=q,
            access_state=access_state,
            moderation_state=moderation_state,
            role=role,
            limit=limit,
            offset=offset,
        ).model_dump(mode="json")
    )


@router.get("/users/{project_user_id}")
def community_admin_user_detail(
    project_user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_admin_user_detail(db, project_user, project_user_id).model_dump(mode="json"))


@router.patch("/users/{project_user_id}/project-access")
def community_admin_update_user_project_access(
    project_user_id: UUID,
    payload: CommunityAdminUserProjectAccessUpdate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_user_project_access(db, project_user, project_user_id, payload).model_dump(mode="json"))


@router.post("/users/{project_user_id}/extend-one-year")
def community_admin_extend_user_one_year(
    project_user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(extend_admin_user_one_year(db, project_user, project_user_id).model_dump(mode="json"))


@router.post("/users/{project_user_id}/ban")
def community_admin_ban_user(
    project_user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(ban_admin_user(db, project_user, project_user_id).model_dump(mode="json"))


@router.post("/users/{project_user_id}/unban")
def community_admin_unban_user(
    project_user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(unban_admin_user(db, project_user, project_user_id).model_dump(mode="json"))


@router.get("/products")
def community_admin_products(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_admin_products(db, project_user)])


@router.post("/products")
def community_admin_create_product(
    payload: CommunityAdminProductPayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(create_admin_product(db, project_user, payload).model_dump(mode="json"))


@router.get("/products/{product_id}")
def community_admin_product_detail(
    product_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(get_admin_product(db, project_user, product_id).model_dump(mode="json"))


@router.patch("/products/{product_id}")
def community_admin_update_product(
    product_id: UUID,
    payload: CommunityAdminProductPayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_product(db, project_user, product_id, payload).model_dump(mode="json"))


@router.delete("/products/{product_id}")
def community_admin_hide_product(
    product_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(hide_admin_product(db, project_user, product_id).model_dump(mode="json"))


@router.get("/products/{product_id}/materials")
def community_admin_product_materials(
    product_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response([item.model_dump(mode="json") for item in list_admin_product_materials(db, project_user, product_id)])


@router.post("/products/{product_id}/materials")
def community_admin_create_product_material(
    product_id: UUID,
    payload: CommunityAdminProductMaterialPayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(create_admin_product_material(db, project_user, product_id, payload).model_dump(mode="json"))


@router.patch("/products/{product_id}/materials/{material_id}")
def community_admin_update_product_material(
    product_id: UUID,
    material_id: UUID,
    payload: CommunityAdminProductMaterialPayload,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_product_material(db, project_user, product_id, material_id, payload).model_dump(mode="json"))


@router.delete("/products/{product_id}/materials/{material_id}")
def community_admin_delete_product_material(
    product_id: UUID,
    material_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(delete_admin_product_material(db, project_user, product_id, material_id).model_dump(mode="json"))


@router.get("/product-access")
def community_admin_product_access(
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
    product_id: UUID | None = Query(None),
    project_user_id: UUID | None = Query(None),
) -> dict[str, object]:
    return success_response(
        [item.model_dump(mode="json") for item in list_admin_product_access(db, project_user, product_id, project_user_id)]
    )


@router.post("/product-access")
def community_admin_grant_product_access(
    payload: CommunityAdminProductAccessCreate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(grant_admin_product_access(db, project_user, payload).model_dump(mode="json"))


@router.patch("/product-access/{access_id}")
def community_admin_update_product_access(
    access_id: UUID,
    payload: CommunityAdminProductAccessUpdate,
    db: Annotated[Session, Depends(get_db)],
    project_user: Annotated[ProjectUser, Depends(require_community_admin)],
) -> dict[str, object]:
    return success_response(update_admin_product_access(db, project_user, access_id, payload).model_dump(mode="json"))
