from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import String, or_, func
from sqlalchemy.orm import Session

from app.config import settings
from app.community.models import (
    CommunityAdminAuditLog,
    CommunityChatLink,
    CommunityContentRead,
    CommunityExchange,
    CommunityInsight,
    CommunityNotification,
    CommunityNotificationSetting,
    CommunityPost,
    CommunityProduct,
    CommunityProductAccess,
    CommunityProductMaterial,
    CommunityProductPurchaseRequest,
    CommunityProjectLink,
    CommunityProjectPage,
    CommunityReaction,
)
from app.community.schemas import (
    COMMUNITY_ADMIN_STATUS_FILTERS,
    CommunityAdminChat,
    CommunityAdminChatPayload,
    CommunityAdminExchange,
    CommunityAdminExchangePayload,
    CommunityAdminInsightCreate,
    CommunityAdminInsightDetail,
    CommunityAdminInsightListItem,
    CommunityAdminInsightListResponse,
    CommunityAdminInsightUpdate,
    CommunityAdminNotificationItem,
    CommunityAdminNotificationListResponse,
    CommunityAdminNotificationSenderStatus,
    CommunityAdminNotificationProcessSummary,
    CommunityAdminPostCreate,
    CommunityAdminPostDetail,
    CommunityAdminPostListItem,
    CommunityAdminPostListResponse,
    CommunityAdminPostUpdate,
    CommunityAdminProduct,
    CommunityAdminProductAccess,
    CommunityAdminProductAccessCreate,
    CommunityAdminProductAccessUpdate,
    CommunityAdminPurchaseRequestApproveGrant,
    CommunityAdminPurchaseRequestItem,
    CommunityAdminPurchaseRequestListResponse,
    CommunityAdminPurchaseRequestUpdate,
    CommunityAdminUserDetail,
    CommunityAdminUserListItem,
    CommunityAdminUserListResponse,
    CommunityAdminUserProductAccessItem,
    CommunityAdminUserProjectAccessUpdate,
    CommunityAdminProductMaterial,
    CommunityAdminProductMaterialPayload,
    CommunityAdminProductPayload,
    CommunityDashboardChatLink,
    CommunityDashboardContentItem,
    CommunityDashboardInsightItem,
    CommunityDashboardNotification,
    CommunityDashboardResponse,
    CommunityExchangeResponse,
    CommunityInfo,
    CommunityChatLinkResponse,
    CommunityInsightDetailResponse,
    CommunityNotificationSettingsPatch,
    CommunityPostDetailResponse,
    CommunityProductDetail,
    CommunityProductListItem,
    CommunityProductMaterialResponse,
    CommunityProductPurchaseRequestCreate,
    CommunityProductPurchaseRequestCreated,
    CommunityProductPurchaseRequestItem,
    CommunityProfileResponse,
    CommunityPublicLinks,
    CommunityRulesResponse,
    CommunitySettingsResponse,
    CommunityUsefulToggleResponse,
    CommunityUrgentNotificationSummary,
)
from app.community.telegram_sender import (
    compose_urgent_insight_message,
    get_telegram_sender,
    normalized_telegram_real_send_scope,
    normalized_telegram_sender_mode,
)
from app.projects.models import ProjectUser
from app.users.models import TelegramIdentity
from app.shared.errors import ConflictError, NotFoundError, ValidationAppError

GLOBAL_GREEN_INVEST_PROJECT_SLUG = "global-green-invest"
GLOBAL_GREEN_INVEST_BRAND_NAME = "🍀 ЗЕЛЁНЫЙ / TG Investor"


def get_community_info(scope: str = "member") -> CommunityInfo:
    return CommunityInfo(
        project_slug=GLOBAL_GREEN_INVEST_PROJECT_SLUG,
        brand_name=GLOBAL_GREEN_INVEST_BRAND_NAME,
        status="bootstrap_skeleton",
        scope=scope,
    )


def get_community_dashboard(db: Session, project_user: ProjectUser) -> CommunityDashboardResponse:
    now = datetime.now(UTC)
    pinned_post = _get_pinned_post(db, project_user, now)
    posts = _get_latest_posts(db, project_user, now, pinned_post_id=pinned_post.id if pinned_post else None)
    insights = _get_latest_insights(db, project_user, now)
    chat_links = _get_chat_links(db, project_user)
    notifications = _get_important_notifications(db, project_user)

    post_ids = [post.id for post in posts]
    if pinned_post is not None:
        post_ids.append(pinned_post.id)
    insight_ids = [insight.id for insight in insights]

    read_posts = _read_content_ids(db, project_user, "post", post_ids)
    read_insights = _read_content_ids(db, project_user, "insight", insight_ids)
    useful_counts = _useful_counts(db, project_user.project_id, post_ids, insight_ids)
    my_useful = _my_useful_targets(db, project_user, post_ids, insight_ids)

    return CommunityDashboardResponse(
        important_notifications=[
            CommunityDashboardNotification(
                id=item.id,
                type=item.type,
                title=item.title,
                body=item.body,
                target_type=item.target_type,
                target_id=item.target_id,
                created_at=item.created_at,
                is_read=item.is_read,
            )
            for item in notifications
        ],
        pinned_post=_post_item(pinned_post, read_posts, useful_counts, my_useful) if pinned_post else None,
        posts=[_post_item(post, read_posts, useful_counts, my_useful) for post in posts],
        insights=[_insight_item(insight, read_insights, useful_counts, my_useful) for insight in insights],
        chat_links=[
            CommunityDashboardChatLink(
                id=item.id,
                title=item.title,
                telegram_url=item.telegram_url,
                sort_order=item.sort_order,
            )
            for item in chat_links
        ],
    )


DEFAULT_DISCLAIMER = (
    "Материалы внутри приложения отражают мнение команды и не являются финансовой рекомендацией. "
    "Пользователь самостоятельно принимает решения и несёт ответственность за свои действия."
)


def get_public_links(db: Session, project_id: UUID | None = None) -> CommunityPublicLinks:
    selected_project_id = project_id or _public_links_project_id(db)
    links = _project_links(db, selected_project_id) if selected_project_id else {}
    return CommunityPublicLinks(
        support_url=links.get("support"),
        telegram_bot_url=links.get("telegram_bot"),
        website_url=links.get("website"),
        blogger_telegram_url=links.get("blogger_telegram"),
    )


def get_community_profile(db: Session, project_user: ProjectUser) -> CommunityProfileResponse:
    telegram = (
        db.query(TelegramIdentity)
        .filter(TelegramIdentity.user_id == project_user.user_id)
        .order_by(TelegramIdentity.updated_at.desc())
        .first()
    )
    links = get_public_links(db, project_user.project_id)
    return CommunityProfileResponse(
        telegram_first_name=telegram.first_name if telegram else None,
        telegram_username=telegram.username if telegram else None,
        telegram_avatar_url=telegram.photo_url if telegram else None,
        access_state=project_user.access_state,
        access_until=project_user.access_until,
        moderation_state=project_user.moderation_state,
        support_url=links.support_url,
    )


def get_community_settings(db: Session, project_user: ProjectUser) -> CommunitySettingsResponse:
    setting = _get_or_create_notification_setting(db, project_user)
    links = get_public_links(db, project_user.project_id)
    about = _project_page(db, project_user.project_id, "about")
    rules = _project_page(db, project_user.project_id, "rules")
    disclaimer = _project_page(db, project_user.project_id, "disclaimer")
    db.commit()
    return CommunitySettingsResponse(
        notifications_enabled=setting.notifications_enabled,
        support_url=links.support_url,
        telegram_bot_url=links.telegram_bot_url,
        website_url=links.website_url,
        blogger_telegram_url=links.blogger_telegram_url,
        about_title=about.title if about else None,
        about_content=about.content if about else None,
        rules_title=rules.title if rules else None,
        rules_content=rules.content if rules else None,
        disclaimer=disclaimer.content if disclaimer else DEFAULT_DISCLAIMER,
    )


def update_notification_settings(
    db: Session,
    project_user: ProjectUser,
    payload: CommunityNotificationSettingsPatch,
) -> CommunitySettingsResponse:
    setting = _get_or_create_notification_setting(db, project_user)
    setting.notifications_enabled = payload.notifications_enabled
    db.commit()
    return get_community_settings(db, project_user)


def get_community_rules(db: Session, project_user: ProjectUser) -> CommunityRulesResponse:
    rules = _project_page(db, project_user.project_id, "rules")
    disclaimer = _project_page(db, project_user.project_id, "disclaimer")
    links = get_public_links(db, project_user.project_id)
    return CommunityRulesResponse(
        title=rules.title if rules else "Правила и дисклеймер",
        content=rules.content if rules else "Соблюдайте правила сообщества и используйте материалы ответственно.",
        disclaimer=disclaimer.content if disclaimer else DEFAULT_DISCLAIMER,
        support_url=links.support_url,
    )


def list_community_products(db: Session, project_user: ProjectUser) -> list[CommunityProductListItem]:
    products = (
        db.query(CommunityProduct)
        .filter(
            CommunityProduct.project_id == project_user.project_id,
            CommunityProduct.is_published.is_(True),
        )
        .order_by(CommunityProduct.sort_order.asc(), CommunityProduct.created_at.asc())
        .all()
    )
    access_by_product = _active_product_access_by_product(db, project_user, [product.id for product in products])
    return [_product_list_item(product, access_by_product.get(product.id)) for product in products]


def get_community_product_detail(db: Session, project_user: ProjectUser, product_id_or_slug: str) -> CommunityProductDetail:
    product = _get_member_product_model(db, project_user, product_id_or_slug)
    access = _active_product_access_by_product(db, project_user, [product.id]).get(product.id)
    has_access = access is not None
    materials = (
        db.query(CommunityProductMaterial)
        .filter(
            CommunityProductMaterial.project_id == project_user.project_id,
            CommunityProductMaterial.product_id == product.id,
            CommunityProductMaterial.deleted_at.is_(None),
        )
        .order_by(CommunityProductMaterial.sort_order.asc(), CommunityProductMaterial.created_at.asc())
        .all()
    )
    visible_materials = [material for material in materials if not material.is_locked or has_access]
    locked_count = len([material for material in materials if material.is_locked])
    links = get_public_links(db, project_user.project_id)
    base = _product_list_item(product, access)
    return CommunityProductDetail(
        **base.model_dump(),
        materials=[_product_material_response(material) for material in visible_materials],
        has_locked_materials=locked_count > 0,
        locked_materials_count=locked_count,
        support_url=links.support_url,
        purchase_request=_member_purchase_request_item(_latest_product_purchase_request(db, project_user, product)) if not has_access else None,
    )


def create_product_purchase_request(
    db: Session,
    project_user: ProjectUser,
    product_id_or_slug: str,
    payload: CommunityProductPurchaseRequestCreate,
) -> CommunityProductPurchaseRequestCreated:
    product = _get_member_product_model(db, project_user, product_id_or_slug)
    if _active_product_access_by_product(db, project_user, [product.id]).get(product.id) is not None:
        raise ConflictError("already_has_access")
    existing = _open_product_purchase_request(db, project_user, product)
    if existing is not None:
        raise ConflictError("request_already_exists", details={"request_id": str(existing.id)})
    request = CommunityProductPurchaseRequest(
        project_id=project_user.project_id,
        product_id=product.id,
        project_user_id=project_user.id,
        status="new",
        contact_method=payload.contact_method,
        contact_value=(payload.contact_value or "").strip() or None,
        message=(payload.message or "").strip() or None,
    )
    db.add(request)
    db.flush()
    _add_audit_log(db, project_user, "purchase_request.created", "purchase_request", request.id)
    db.commit()
    db.refresh(request)
    return CommunityProductPurchaseRequestCreated(
        request_id=request.id,
        status=request.status,
        product_id=product.id,
        product_title=product.title,
        created_at=request.created_at,
    )


def list_my_purchase_requests(db: Session, project_user: ProjectUser) -> list[CommunityProductPurchaseRequestItem]:
    rows = (
        db.query(CommunityProductPurchaseRequest)
        .filter(
            CommunityProductPurchaseRequest.project_id == project_user.project_id,
            CommunityProductPurchaseRequest.project_user_id == project_user.id,
        )
        .order_by(CommunityProductPurchaseRequest.created_at.desc())
        .limit(50)
        .all()
    )
    return [_member_purchase_request_item(row) for row in rows]


def get_post_detail(db: Session, project_user: ProjectUser, post_id: UUID) -> CommunityPostDetailResponse:
    now = datetime.now(UTC)
    post = get_published_post_or_404(db, project_user, post_id, now)
    mark_content_read(db, project_user, "post", post.id, now)
    post.view_count += 1
    db.commit()
    db.refresh(post)

    return CommunityPostDetailResponse(
        id=post.id,
        title=post.title,
        excerpt=post.excerpt,
        content=post.content,
        cover_url=post.cover_url,
        published_at=post.published_at,
        view_count=post.view_count,
        useful_count=get_useful_count(db, project_user.project_id, "post", post.id),
        is_useful_by_me=is_useful_by_project_user(db, project_user, "post", post.id),
        is_new=False,
    )


def get_insight_detail(db: Session, project_user: ProjectUser, insight_id: UUID) -> CommunityInsightDetailResponse:
    now = datetime.now(UTC)
    insight = get_published_insight_or_404(db, project_user, insight_id, now)
    mark_content_read(db, project_user, "insight", insight.id, now)
    insight.view_count += 1
    db.commit()
    db.refresh(insight)

    return CommunityInsightDetailResponse(
        id=insight.id,
        title=insight.title,
        excerpt=insight.excerpt,
        content=insight.content,
        is_urgent=insight.is_urgent,
        published_at=insight.published_at,
        view_count=insight.view_count,
        useful_count=get_useful_count(db, project_user.project_id, "insight", insight.id),
        is_useful_by_me=is_useful_by_project_user(db, project_user, "insight", insight.id),
        is_new=False,
    )


def toggle_post_useful(db: Session, project_user: ProjectUser, post_id: UUID) -> CommunityUsefulToggleResponse:
    now = datetime.now(UTC)
    post = get_published_post_or_404(db, project_user, post_id, now)
    return toggle_useful_reaction(db, project_user, "post", post.id)


def toggle_insight_useful(db: Session, project_user: ProjectUser, insight_id: UUID) -> CommunityUsefulToggleResponse:
    now = datetime.now(UTC)
    insight = get_published_insight_or_404(db, project_user, insight_id, now)
    return toggle_useful_reaction(db, project_user, "insight", insight.id)


def list_community_chats(db: Session, project_user: ProjectUser) -> list[CommunityChatLinkResponse]:
    chats = _get_chat_links(db, project_user, limit=None)
    return [_chat_link_response(chat) for chat in chats]


def list_community_exchanges(db: Session, project_user: ProjectUser) -> list[CommunityExchangeResponse]:
    exchanges = (
        db.query(CommunityExchange)
        .filter(
            CommunityExchange.project_id == project_user.project_id,
            CommunityExchange.is_published.is_(True),
        )
        .order_by(CommunityExchange.sort_order.asc(), CommunityExchange.created_at.asc())
        .all()
    )
    return [_exchange_response(exchange) for exchange in exchanges]


def list_admin_chats(db: Session, project_user: ProjectUser) -> list[CommunityAdminChat]:
    chats = (
        db.query(CommunityChatLink)
        .filter(CommunityChatLink.project_id == project_user.project_id)
        .order_by(CommunityChatLink.sort_order.asc(), CommunityChatLink.created_at.asc())
        .all()
    )
    return [_admin_chat(chat) for chat in chats]


def create_admin_chat(db: Session, project_user: ProjectUser, payload: CommunityAdminChatPayload) -> CommunityAdminChat:
    _validate_required_text(payload.title, "title")
    _validate_required_text(payload.telegram_url, "telegram_url")
    chat = CommunityChatLink(
        project_id=project_user.project_id,
        created_by_project_user_id=project_user.id,
        title=payload.title.strip(),
        telegram_url=payload.telegram_url.strip(),
        sort_order=payload.sort_order,
        is_published=payload.is_published,
    )
    db.add(chat)
    db.flush()
    _add_audit_log(db, project_user, "chat.created", "chat", chat.id)
    db.commit()
    db.refresh(chat)
    return _admin_chat(chat)


def get_admin_chat(db: Session, project_user: ProjectUser, chat_id: UUID) -> CommunityAdminChat:
    return _admin_chat(_get_admin_chat_model(db, project_user, chat_id))


def update_admin_chat(
    db: Session,
    project_user: ProjectUser,
    chat_id: UUID,
    payload: CommunityAdminChatPayload,
) -> CommunityAdminChat:
    _validate_required_text(payload.title, "title")
    _validate_required_text(payload.telegram_url, "telegram_url")
    chat = _get_admin_chat_model(db, project_user, chat_id)
    chat.title = payload.title.strip()
    chat.telegram_url = payload.telegram_url.strip()
    chat.sort_order = payload.sort_order
    chat.is_published = payload.is_published
    db.flush()
    _add_audit_log(db, project_user, "chat.updated", "chat", chat.id)
    db.commit()
    db.refresh(chat)
    return _admin_chat(chat)


def hide_admin_chat(db: Session, project_user: ProjectUser, chat_id: UUID) -> CommunityAdminChat:
    chat = _get_admin_chat_model(db, project_user, chat_id)
    chat.is_published = False
    db.flush()
    _add_audit_log(db, project_user, "chat.hidden", "chat", chat.id)
    db.commit()
    db.refresh(chat)
    return _admin_chat(chat)


def list_admin_exchanges(db: Session, project_user: ProjectUser) -> list[CommunityAdminExchange]:
    exchanges = (
        db.query(CommunityExchange)
        .filter(CommunityExchange.project_id == project_user.project_id)
        .order_by(CommunityExchange.sort_order.asc(), CommunityExchange.created_at.asc())
        .all()
    )
    return [_admin_exchange(exchange) for exchange in exchanges]


def create_admin_exchange(
    db: Session,
    project_user: ProjectUser,
    payload: CommunityAdminExchangePayload,
) -> CommunityAdminExchange:
    _validate_exchange_payload(payload)
    exchange = CommunityExchange(
        project_id=project_user.project_id,
        created_by_project_user_id=project_user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        team_comment=_optional_text(payload.team_comment),
        logo_url=_optional_text(payload.logo_url),
        external_url=payload.external_url.strip(),
        promo_code=_optional_text(payload.promo_code),
        sort_order=payload.sort_order,
        is_published=payload.is_published,
    )
    db.add(exchange)
    db.flush()
    _add_audit_log(db, project_user, "exchange.created", "exchange", exchange.id)
    db.commit()
    db.refresh(exchange)
    return _admin_exchange(exchange)


def get_admin_exchange(db: Session, project_user: ProjectUser, exchange_id: UUID) -> CommunityAdminExchange:
    return _admin_exchange(_get_admin_exchange_model(db, project_user, exchange_id))


def update_admin_exchange(
    db: Session,
    project_user: ProjectUser,
    exchange_id: UUID,
    payload: CommunityAdminExchangePayload,
) -> CommunityAdminExchange:
    _validate_exchange_payload(payload)
    exchange = _get_admin_exchange_model(db, project_user, exchange_id)
    exchange.title = payload.title.strip()
    exchange.description = payload.description.strip()
    exchange.team_comment = _optional_text(payload.team_comment)
    exchange.logo_url = _optional_text(payload.logo_url)
    exchange.external_url = payload.external_url.strip()
    exchange.promo_code = _optional_text(payload.promo_code)
    exchange.sort_order = payload.sort_order
    exchange.is_published = payload.is_published
    db.flush()
    _add_audit_log(db, project_user, "exchange.updated", "exchange", exchange.id)
    db.commit()
    db.refresh(exchange)
    return _admin_exchange(exchange)


def hide_admin_exchange(db: Session, project_user: ProjectUser, exchange_id: UUID) -> CommunityAdminExchange:
    exchange = _get_admin_exchange_model(db, project_user, exchange_id)
    exchange.is_published = False
    db.flush()
    _add_audit_log(db, project_user, "exchange.hidden", "exchange", exchange.id)
    db.commit()
    db.refresh(exchange)
    return _admin_exchange(exchange)


def list_admin_products(db: Session, project_user: ProjectUser) -> list[CommunityAdminProduct]:
    products = (
        db.query(CommunityProduct)
        .filter(CommunityProduct.project_id == project_user.project_id)
        .order_by(CommunityProduct.sort_order.asc(), CommunityProduct.created_at.asc())
        .all()
    )
    return [_admin_product(product) for product in products]


def create_admin_product(db: Session, project_user: ProjectUser, payload: CommunityAdminProductPayload) -> CommunityAdminProduct:
    _validate_product_payload(payload)
    product = CommunityProduct(
        project_id=project_user.project_id,
        created_by_project_user_id=project_user.id,
        slug=payload.slug.strip(),
        title=payload.title.strip(),
        short_description=payload.short_description.strip(),
        description=payload.description.strip(),
        cover_url=_optional_text(payload.cover_url),
        price_usd=payload.price_usd,
        price_rub=payload.price_rub,
        sort_order=payload.sort_order,
        is_published=payload.is_published,
        access_duration_type=payload.access_duration_type,
    )
    db.add(product)
    db.flush()
    _add_audit_log(db, project_user, "product.created", "product", product.id)
    db.commit()
    db.refresh(product)
    return _admin_product(product)


def get_admin_product(db: Session, project_user: ProjectUser, product_id: UUID) -> CommunityAdminProduct:
    return _admin_product(_get_admin_product_model(db, project_user, product_id))


def update_admin_product(
    db: Session,
    project_user: ProjectUser,
    product_id: UUID,
    payload: CommunityAdminProductPayload,
) -> CommunityAdminProduct:
    _validate_product_payload(payload)
    product = _get_admin_product_model(db, project_user, product_id)
    product.slug = payload.slug.strip()
    product.title = payload.title.strip()
    product.short_description = payload.short_description.strip()
    product.description = payload.description.strip()
    product.cover_url = _optional_text(payload.cover_url)
    product.price_usd = payload.price_usd
    product.price_rub = payload.price_rub
    product.sort_order = payload.sort_order
    product.is_published = payload.is_published
    product.access_duration_type = payload.access_duration_type
    db.flush()
    _add_audit_log(db, project_user, "product.updated", "product", product.id)
    db.commit()
    db.refresh(product)
    return _admin_product(product)


def hide_admin_product(db: Session, project_user: ProjectUser, product_id: UUID) -> CommunityAdminProduct:
    product = _get_admin_product_model(db, project_user, product_id)
    product.is_published = False
    db.flush()
    _add_audit_log(db, project_user, "product.hidden", "product", product.id)
    db.commit()
    db.refresh(product)
    return _admin_product(product)


def list_admin_product_materials(db: Session, project_user: ProjectUser, product_id: UUID) -> list[CommunityAdminProductMaterial]:
    product = _get_admin_product_model(db, project_user, product_id)
    materials = (
        db.query(CommunityProductMaterial)
        .filter(
            CommunityProductMaterial.project_id == project_user.project_id,
            CommunityProductMaterial.product_id == product.id,
            CommunityProductMaterial.deleted_at.is_(None),
        )
        .order_by(CommunityProductMaterial.sort_order.asc(), CommunityProductMaterial.created_at.asc())
        .all()
    )
    return [_admin_product_material(material) for material in materials]


def create_admin_product_material(
    db: Session,
    project_user: ProjectUser,
    product_id: UUID,
    payload: CommunityAdminProductMaterialPayload,
) -> CommunityAdminProductMaterial:
    product = _get_admin_product_model(db, project_user, product_id)
    _validate_material_payload(payload)
    material = CommunityProductMaterial(
        project_id=project_user.project_id,
        product_id=product.id,
        title=payload.title.strip(),
        description=_optional_text(payload.description),
        material_type=payload.material_type,
        content=_optional_text(payload.content),
        url=_optional_text(payload.url),
        file_url=_optional_text(payload.file_url),
        sort_order=payload.sort_order,
        is_locked=payload.is_locked,
    )
    db.add(material)
    db.flush()
    _add_audit_log(db, project_user, "product_material.created", "product_material", material.id)
    db.commit()
    db.refresh(material)
    return _admin_product_material(material)


def update_admin_product_material(
    db: Session,
    project_user: ProjectUser,
    product_id: UUID,
    material_id: UUID,
    payload: CommunityAdminProductMaterialPayload,
) -> CommunityAdminProductMaterial:
    _get_admin_product_model(db, project_user, product_id)
    _validate_material_payload(payload)
    material = _get_admin_product_material_model(db, project_user, product_id, material_id)
    material.title = payload.title.strip()
    material.description = _optional_text(payload.description)
    material.material_type = payload.material_type
    material.content = _optional_text(payload.content)
    material.url = _optional_text(payload.url)
    material.file_url = _optional_text(payload.file_url)
    material.sort_order = payload.sort_order
    material.is_locked = payload.is_locked
    db.flush()
    _add_audit_log(db, project_user, "product_material.updated", "product_material", material.id)
    db.commit()
    db.refresh(material)
    return _admin_product_material(material)


def delete_admin_product_material(db: Session, project_user: ProjectUser, product_id: UUID, material_id: UUID) -> CommunityAdminProductMaterial:
    material = _get_admin_product_material_model(db, project_user, product_id, material_id)
    material.deleted_at = datetime.now(UTC)
    db.flush()
    _add_audit_log(db, project_user, "product_material.deleted", "product_material", material.id)
    db.commit()
    db.refresh(material)
    return _admin_product_material(material)


def list_admin_product_access(
    db: Session,
    project_user: ProjectUser,
    product_id: UUID | None = None,
    target_project_user_id: UUID | None = None,
) -> list[CommunityAdminProductAccess]:
    query = db.query(CommunityProductAccess).filter(CommunityProductAccess.project_id == project_user.project_id)
    if product_id is not None:
        query = query.filter(CommunityProductAccess.product_id == product_id)
    if target_project_user_id is not None:
        query = query.filter(CommunityProductAccess.project_user_id == target_project_user_id)
    return [_admin_product_access(item) for item in query.order_by(CommunityProductAccess.created_at.desc()).all()]


def list_admin_users(
    db: Session,
    project_user: ProjectUser,
    q: str | None = None,
    access_state: str = "all",
    moderation_state: str = "all",
    role: str = "all",
    limit: int = 20,
    offset: int = 0,
) -> CommunityAdminUserListResponse:
    _validate_admin_user_filters(access_state, moderation_state, role, limit, offset)
    query = db.query(ProjectUser).filter(ProjectUser.project_id == project_user.project_id)

    if q and q.strip():
        search = f"%{q.strip()}%"
        query = query.outerjoin(TelegramIdentity, TelegramIdentity.user_id == ProjectUser.user_id).filter(
            or_(
                TelegramIdentity.username.ilike(search),
                TelegramIdentity.first_name.ilike(search),
                func.cast(ProjectUser.user_id, String).ilike(search),
            )
        )
    if access_state != "all":
        query = query.filter(ProjectUser.access_state == access_state)
    if moderation_state != "all":
        query = query.filter(ProjectUser.moderation_state == moderation_state)
    if role != "all":
        query = query.filter(ProjectUser.role == role)

    total = query.distinct().count()
    users = query.order_by(ProjectUser.created_at.desc()).offset(offset).limit(limit).all()
    return CommunityAdminUserListResponse(
        items=[_admin_user_list_item(db, item) for item in users],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_admin_user_detail(db: Session, project_user: ProjectUser, target_project_user_id: UUID) -> CommunityAdminUserDetail:
    target = _get_admin_project_user_model(db, project_user, target_project_user_id)
    base = _admin_user_list_item(db, target).model_dump()
    return CommunityAdminUserDetail(
        **base,
        product_access=_admin_user_product_access_items(db, project_user, target.id),
    )


def update_admin_user_project_access(
    db: Session,
    project_user: ProjectUser,
    target_project_user_id: UUID,
    payload: CommunityAdminUserProjectAccessUpdate,
) -> CommunityAdminUserDetail:
    target = _get_admin_project_user_model(db, project_user, target_project_user_id)
    data = payload.model_dump(exclude_unset=True)
    if "role" in data and data["role"] != target.role:
        _ensure_owner_change_is_safe(db, project_user, target, data["role"])
        target.role = data["role"]
        _add_audit_log(db, project_user, "user.role_updated", "project_user", target.id)
    if "access_state" in data and data["access_state"] != target.access_state:
        next_access_state = data["access_state"]
        target.access_state = next_access_state
        action = "project_access.granted" if next_access_state == "active" else "project_access.revoked"
        _add_audit_log(db, project_user, action, "project_user", target.id)
    if "access_until" in data:
        target.access_until = data["access_until"]
        _add_audit_log(db, project_user, "project_access.updated", "project_user", target.id)
    if "status" in data:
        target.status = data["status"]
        _add_audit_log(db, project_user, "project_access.status_updated", "project_user", target.id)
    if "moderation_state" in data and data["moderation_state"] != target.moderation_state:
        target.moderation_state = data["moderation_state"]
        action = "user.banned" if target.moderation_state == "banned" else "user.unbanned"
        _add_audit_log(db, project_user, action, "project_user", target.id)
    db.commit()
    db.refresh(target)
    return get_admin_user_detail(db, project_user, target.id)


def extend_admin_user_one_year(db: Session, project_user: ProjectUser, target_project_user_id: UUID) -> CommunityAdminUserDetail:
    target = _get_admin_project_user_model(db, project_user, target_project_user_id)
    now = datetime.now(UTC)
    start = target.access_until if target.access_until else now
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if start < now:
        start = now
    target.status = "active"
    target.access_state = "active"
    target.access_until = _add_one_year(start)
    db.flush()
    _add_audit_log(db, project_user, "project_access.extended", "project_user", target.id)
    db.commit()
    db.refresh(target)
    return get_admin_user_detail(db, project_user, target.id)


def ban_admin_user(db: Session, project_user: ProjectUser, target_project_user_id: UUID) -> CommunityAdminUserDetail:
    target = _get_admin_project_user_model(db, project_user, target_project_user_id)
    target.moderation_state = "banned"
    db.flush()
    _add_audit_log(db, project_user, "user.banned", "project_user", target.id)
    db.commit()
    db.refresh(target)
    return get_admin_user_detail(db, project_user, target.id)


def unban_admin_user(db: Session, project_user: ProjectUser, target_project_user_id: UUID) -> CommunityAdminUserDetail:
    target = _get_admin_project_user_model(db, project_user, target_project_user_id)
    target.moderation_state = "normal"
    db.flush()
    _add_audit_log(db, project_user, "user.unbanned", "project_user", target.id)
    db.commit()
    db.refresh(target)
    return get_admin_user_detail(db, project_user, target.id)


def grant_admin_product_access(
    db: Session,
    project_user: ProjectUser,
    payload: CommunityAdminProductAccessCreate,
) -> CommunityAdminProductAccess:
    _get_admin_product_model(db, project_user, payload.product_id)
    target = db.query(ProjectUser).filter(ProjectUser.id == payload.project_user_id, ProjectUser.project_id == project_user.project_id).one_or_none()
    if target is None:
        raise NotFoundError("Project user was not found")
    access = (
        db.query(CommunityProductAccess)
        .filter(
            CommunityProductAccess.project_id == project_user.project_id,
            CommunityProductAccess.product_id == payload.product_id,
            CommunityProductAccess.project_user_id == payload.project_user_id,
        )
        .one_or_none()
    )
    if access is None:
        access = CommunityProductAccess(
            project_id=project_user.project_id,
            product_id=payload.product_id,
            project_user_id=payload.project_user_id,
        )
        db.add(access)
    access.access_state = payload.access_state
    access.access_until = payload.access_until
    access.source = payload.source or "manual"
    access.granted_by_project_user_id = project_user.id
    db.flush()
    _add_audit_log(db, project_user, "product_access.granted", "product_access", access.id)
    db.commit()
    db.refresh(access)
    return _admin_product_access(access)


def update_admin_product_access(
    db: Session,
    project_user: ProjectUser,
    access_id: UUID,
    payload: CommunityAdminProductAccessUpdate,
) -> CommunityAdminProductAccess:
    access = (
        db.query(CommunityProductAccess)
        .filter(CommunityProductAccess.id == access_id, CommunityProductAccess.project_id == project_user.project_id)
        .one_or_none()
    )
    if access is None:
        raise NotFoundError("Product access was not found")
    access.access_state = payload.access_state
    access.access_until = payload.access_until
    db.flush()
    _add_audit_log(db, project_user, "product_access.updated", "product_access", access.id)
    db.commit()
    db.refresh(access)
    return _admin_product_access(access)


def list_admin_purchase_requests(
    db: Session,
    project_user: ProjectUser,
    status: str = "all",
    product_id: UUID | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> CommunityAdminPurchaseRequestListResponse:
    if status != "all" and status not in ("new", "contacted", "approved", "rejected", "cancelled"):
        raise ValidationAppError("Unsupported purchase request status")
    if limit < 1 or limit > 100:
        raise ValidationAppError("Limit must be between 1 and 100")
    if offset < 0:
        raise ValidationAppError("Offset must be greater than or equal to 0")

    query = db.query(CommunityProductPurchaseRequest).filter(CommunityProductPurchaseRequest.project_id == project_user.project_id)
    if status != "all":
        query = query.filter(CommunityProductPurchaseRequest.status == status)
    if product_id is not None:
        query = query.filter(CommunityProductPurchaseRequest.product_id == product_id)
    if q:
        pattern = f"%{q.strip()}%"
        query = (
            query.join(ProjectUser, ProjectUser.id == CommunityProductPurchaseRequest.project_user_id)
            .outerjoin(TelegramIdentity, TelegramIdentity.user_id == ProjectUser.user_id)
            .filter(
                or_(
                    TelegramIdentity.username.ilike(pattern),
                    TelegramIdentity.first_name.ilike(pattern),
                    CommunityProductPurchaseRequest.contact_value.ilike(pattern),
                    CommunityProductPurchaseRequest.message.ilike(pattern),
                )
            )
        )

    total = query.count()
    rows = query.order_by(CommunityProductPurchaseRequest.created_at.desc()).offset(offset).limit(limit).all()
    return CommunityAdminPurchaseRequestListResponse(
        items=[_admin_purchase_request_item(db, row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def update_admin_purchase_request(
    db: Session,
    project_user: ProjectUser,
    request_id: UUID,
    payload: CommunityAdminPurchaseRequestUpdate,
) -> CommunityAdminPurchaseRequestItem:
    request = _get_admin_purchase_request_model(db, project_user, request_id)
    data = payload.model_dump(exclude_unset=True)
    status_changed = "status" in data and data["status"] != request.status
    if "status" in data and data["status"] is not None:
        request.status = data["status"]
    if "admin_note" in data:
        request.admin_note = data["admin_note"]
    if status_changed and request.status in ("contacted", "approved", "rejected", "cancelled"):
        request.handled_by_project_user_id = project_user.id
        request.handled_at = datetime.now(UTC)
    db.flush()
    action = "purchase_request.status_updated"
    if status_changed and request.status == "rejected":
        action = "purchase_request.rejected"
    elif status_changed and request.status == "cancelled":
        action = "purchase_request.cancelled"
    _add_audit_log(db, project_user, action, "purchase_request", request.id)
    db.commit()
    db.refresh(request)
    return _admin_purchase_request_item(db, request)


def approve_and_grant_purchase_request(
    db: Session,
    project_user: ProjectUser,
    request_id: UUID,
    payload: CommunityAdminPurchaseRequestApproveGrant,
) -> CommunityAdminPurchaseRequestItem:
    request = _get_admin_purchase_request_model(db, project_user, request_id)
    _get_admin_product_model(db, project_user, request.product_id)
    access = (
        db.query(CommunityProductAccess)
        .filter(
            CommunityProductAccess.project_id == project_user.project_id,
            CommunityProductAccess.product_id == request.product_id,
            CommunityProductAccess.project_user_id == request.project_user_id,
        )
        .one_or_none()
    )
    if access is None:
        access = CommunityProductAccess(
            project_id=project_user.project_id,
            product_id=request.product_id,
            project_user_id=request.project_user_id,
        )
        db.add(access)
    access.access_state = "active"
    access.access_until = payload.access_until
    access.source = "manual"
    access.granted_by_project_user_id = project_user.id
    request.status = "approved"
    request.handled_by_project_user_id = project_user.id
    request.handled_at = datetime.now(UTC)
    db.flush()
    _add_audit_log(db, project_user, "purchase_request.approved_and_granted", "purchase_request", request.id)
    _add_audit_log(db, project_user, "product_access.granted", "product_access", access.id)
    db.commit()
    db.refresh(request)
    return _admin_purchase_request_item(db, request)


def list_admin_posts(
    db: Session,
    project_user: ProjectUser,
    status: str = "all",
    limit: int = 20,
    offset: int = 0,
) -> CommunityAdminPostListResponse:
    _validate_admin_list_params(status, limit, offset)
    query = db.query(CommunityPost).filter(CommunityPost.project_id == project_user.project_id)
    if status != "all":
        query = query.filter(CommunityPost.status == status)

    total = query.count()
    posts = query.order_by(CommunityPost.created_at.desc()).offset(offset).limit(limit).all()
    return CommunityAdminPostListResponse(
        items=[_admin_post_list_item(post) for post in posts],
        total=total,
        limit=limit,
        offset=offset,
    )


def create_admin_post(db: Session, project_user: ProjectUser, payload: CommunityAdminPostCreate) -> CommunityAdminPostDetail:
    current = datetime.now(UTC)
    data = payload.model_dump()
    _validate_scheduled_content(data["status"], data.get("scheduled_at"))
    if data["status"] == "published" and data.get("published_at") is None:
        data["published_at"] = current

    post = CommunityPost(
        **data,
        project_id=project_user.project_id,
        author_project_user_id=project_user.id,
        view_count=0,
    )
    db.add(post)
    db.flush()
    _add_audit_log(db, project_user, "post.created", "post", post.id)
    if post.status == "published":
        _add_audit_log(db, project_user, "post.published", "post", post.id)
    db.commit()
    db.refresh(post)
    return _admin_post_detail(post)


def get_admin_post(db: Session, project_user: ProjectUser, post_id: UUID) -> CommunityAdminPostDetail:
    return _admin_post_detail(_get_admin_post_model(db, project_user, post_id))


def update_admin_post(
    db: Session,
    project_user: ProjectUser,
    post_id: UUID,
    payload: CommunityAdminPostUpdate,
) -> CommunityAdminPostDetail:
    post = _get_admin_post_model(db, project_user, post_id)
    previous_status = post.status
    data = payload.model_dump(exclude_unset=True)
    next_status = data.get("status", post.status)
    next_scheduled_at = data.get("scheduled_at", post.scheduled_at)
    _validate_scheduled_content(next_status, next_scheduled_at)
    if next_status == "published" and data.get("published_at", post.published_at) is None:
        data["published_at"] = datetime.now(UTC)

    for field, value in data.items():
        setattr(post, field, value)

    db.flush()
    if previous_status != "published" and post.status == "published":
        _add_audit_log(db, project_user, "post.published", "post", post.id)
    if previous_status != "hidden" and post.status == "hidden":
        _add_audit_log(db, project_user, "post.hidden", "post", post.id)
    db.commit()
    db.refresh(post)
    return _admin_post_detail(post)


def hide_admin_post(db: Session, project_user: ProjectUser, post_id: UUID) -> CommunityAdminPostDetail:
    post = _get_admin_post_model(db, project_user, post_id)
    was_hidden = post.status == "hidden"
    post.status = "hidden"
    db.flush()
    if not was_hidden:
        _add_audit_log(db, project_user, "post.hidden", "post", post.id)
    db.commit()
    db.refresh(post)
    return _admin_post_detail(post)


def list_admin_insights(
    db: Session,
    project_user: ProjectUser,
    status: str = "all",
    limit: int = 20,
    offset: int = 0,
) -> CommunityAdminInsightListResponse:
    _validate_admin_list_params(status, limit, offset)
    query = db.query(CommunityInsight).filter(CommunityInsight.project_id == project_user.project_id)
    if status != "all":
        query = query.filter(CommunityInsight.status == status)

    total = query.count()
    insights = query.order_by(CommunityInsight.created_at.desc()).offset(offset).limit(limit).all()
    return CommunityAdminInsightListResponse(
        items=[_admin_insight_list_item(insight) for insight in insights],
        total=total,
        limit=limit,
        offset=offset,
    )


def list_admin_notifications(
    db: Session,
    project_user: ProjectUser,
    kind: str | None = None,
    status: str = "all",
    limit: int = 50,
    offset: int = 0,
) -> CommunityAdminNotificationListResponse:
    if limit < 1 or limit > 100:
        raise ValidationAppError("Limit must be between 1 and 100")
    if offset < 0:
        raise ValidationAppError("Offset must be greater than or equal to 0")
    if status not in ("all", "pending", "mock_sent", "sent", "skipped", "failed"):
        return CommunityAdminNotificationListResponse(items=[], total=0, limit=limit, offset=offset)

    query = db.query(CommunityNotification).filter(CommunityNotification.project_id == project_user.project_id)
    if kind:
        query = query.filter(CommunityNotification.type == kind)
    if status != "all":
        query = query.filter(CommunityNotification.processing_status == status)

    total = query.count()
    notifications = query.order_by(CommunityNotification.created_at.desc()).offset(offset).limit(limit).all()
    return CommunityAdminNotificationListResponse(
        items=[_admin_notification_item(db, item) for item in notifications],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_admin_notification_sender_status() -> CommunityAdminNotificationSenderStatus:
    mode = normalized_telegram_sender_mode(settings)
    real_send_scope = normalized_telegram_real_send_scope(settings)
    token_configured = bool(settings.telegram_bot_token.strip()) and settings.telegram_bot_token.strip() != "change_me"
    pilot_target_configured = _telegram_pilot_target_configured()
    warning: str | None = None
    if mode == "mock":
        warning = "mock_mode_no_real_telegram_messages"
    elif not token_configured:
        warning = "telegram_bot_token_missing"
    elif real_send_scope == "pilot" and pilot_target_configured:
        warning = "real_pilot_enabled"
    elif real_send_scope == "pilot":
        warning = "real_mode_pilot_target_missing"
    else:
        warning = "real_all_enabled"
    return CommunityAdminNotificationSenderStatus(
        mode=mode,
        real_enabled=mode == "real" and token_configured,
        token_configured=token_configured,
        real_send_scope=real_send_scope,
        pilot_target_configured=pilot_target_configured,
        api_base_url=settings.telegram_api_base_url,
        warning=warning,
    )


def process_pending_telegram_notifications(
    db: Session,
    actor_project_user: ProjectUser,
    limit: int = 50,
    dry_run: bool = False,
) -> CommunityAdminNotificationProcessSummary:
    if limit < 1 or limit > 100:
        raise ValidationAppError("Limit must be between 1 and 100")

    sender = get_telegram_sender(settings)
    sender_status = get_admin_notification_sender_status()
    pending = (
        db.query(CommunityNotification)
        .filter(
            CommunityNotification.project_id == actor_project_user.project_id,
            CommunityNotification.type == "urgent_insight",
            CommunityNotification.target_type == "insight",
            CommunityNotification.processing_status == "pending",
        )
        .order_by(CommunityNotification.created_at.asc())
        .limit(limit)
        .all()
    )
    now = datetime.now(UTC)
    sent_mock = 0
    sent = 0
    skipped = 0
    failed = 0

    for notification in pending:
        recipient = db.query(ProjectUser).filter(ProjectUser.id == notification.project_user_id).one_or_none()
        insight = _notification_insight(db, notification)
        status = "failed"
        error_message: str | None = None
        mock_message_id: str | None = None

        if recipient is None or recipient.project_id != actor_project_user.project_id:
            status = "skipped"
            error_message = "recipient_not_found"
        elif not _is_active_project_user_for_notifications(recipient, now):
            status = "skipped"
            error_message = "recipient_not_eligible"
        elif not _notification_setting_enabled(db, recipient):
            status = "skipped"
            error_message = "notifications_disabled"
        elif insight is None:
            status = "failed"
            error_message = "insight_not_found"
        else:
            telegram = _latest_telegram_identity(db, recipient)
            if telegram is None:
                status = "skipped"
                error_message = "missing_telegram_identity"
            elif dry_run:
                status, error_message = _dry_run_notification_status(sender, telegram)
            else:
                pilot_skip_reason = _real_pilot_skip_reason(sender.mode, telegram)
                if pilot_skip_reason is not None:
                    status = "skipped"
                    error_message = pilot_skip_reason
                else:
                    result = sender.send_message(telegram, compose_urgent_insight_message(insight))
                    status = result.status
                    error_message = result.error_message
                    mock_message_id = result.message_id

        if status == "mock_sent":
            sent_mock += 1
        elif status == "sent":
            sent += 1
        elif status == "skipped":
            skipped += 1
        else:
            failed += 1
            status = "failed"

        if not dry_run:
            notification.processing_status = status
            notification.processed_at = now
            notification.processing_error = error_message
            notification.mock_message_id = mock_message_id

    remaining_pending = _pending_urgent_notification_count(db, actor_project_user.project_id)
    if not dry_run:
        db.flush()
        remaining_pending = _pending_urgent_notification_count(db, actor_project_user.project_id)
        _add_audit_log(db, actor_project_user, "urgent_notifications.processed", "notification", actor_project_user.id)
        db.commit()

    return CommunityAdminNotificationProcessSummary(
        processed=len(pending),
        sent_mock=sent_mock,
        sent=sent,
        skipped=skipped,
        failed=failed,
        remaining_pending=remaining_pending,
        dry_run=dry_run,
        mode=sender_status.mode,
    )


def create_admin_insight(
    db: Session,
    project_user: ProjectUser,
    payload: CommunityAdminInsightCreate,
) -> CommunityAdminInsightDetail:
    current = datetime.now(UTC)
    data = payload.model_dump()
    _validate_scheduled_content(data["status"], data.get("scheduled_at"))
    if data["status"] == "published" and data.get("published_at") is None:
        data["published_at"] = current

    insight = CommunityInsight(
        **data,
        project_id=project_user.project_id,
        author_project_user_id=project_user.id,
        view_count=0,
    )
    db.add(insight)
    db.flush()
    _add_audit_log(db, project_user, "insight.created", "insight", insight.id)
    if insight.status == "published":
        _add_audit_log(
            db,
            project_user,
            "urgent_insight.published" if insight.is_urgent else "insight.published",
            "insight",
            insight.id,
        )
    urgent_notification_summary = (
        _create_urgent_insight_notifications(db, project_user, insight) if _is_urgent_published_insight(insight) else None
    )
    db.commit()
    db.refresh(insight)
    return _admin_insight_detail(insight, urgent_notification_summary)


def get_admin_insight(db: Session, project_user: ProjectUser, insight_id: UUID) -> CommunityAdminInsightDetail:
    return _admin_insight_detail(_get_admin_insight_model(db, project_user, insight_id))


def update_admin_insight(
    db: Session,
    project_user: ProjectUser,
    insight_id: UUID,
    payload: CommunityAdminInsightUpdate,
) -> CommunityAdminInsightDetail:
    insight = _get_admin_insight_model(db, project_user, insight_id)
    previous_status = insight.status
    previous_is_urgent = insight.is_urgent
    data = payload.model_dump(exclude_unset=True)
    next_status = data.get("status", insight.status)
    next_scheduled_at = data.get("scheduled_at", insight.scheduled_at)
    _validate_scheduled_content(next_status, next_scheduled_at)
    if next_status == "published" and data.get("published_at", insight.published_at) is None:
        data["published_at"] = datetime.now(UTC)

    for field, value in data.items():
        setattr(insight, field, value)

    db.flush()
    if previous_status != "published" and insight.status == "published":
        _add_audit_log(
            db,
            project_user,
            "urgent_insight.published" if insight.is_urgent else "insight.published",
            "insight",
            insight.id,
        )
    urgent_became_published = _is_urgent_published_insight(insight) and (
        previous_status != "published" or not previous_is_urgent
    )
    if urgent_became_published and previous_status == "published" and not previous_is_urgent:
        _add_audit_log(db, project_user, "urgent_insight.published", "insight", insight.id)
    if previous_status != "hidden" and insight.status == "hidden":
        _add_audit_log(db, project_user, "insight.hidden", "insight", insight.id)
    urgent_notification_summary = (
        _create_urgent_insight_notifications(db, project_user, insight) if urgent_became_published else None
    )
    db.commit()
    db.refresh(insight)
    return _admin_insight_detail(insight, urgent_notification_summary)


def hide_admin_insight(db: Session, project_user: ProjectUser, insight_id: UUID) -> CommunityAdminInsightDetail:
    insight = _get_admin_insight_model(db, project_user, insight_id)
    was_hidden = insight.status == "hidden"
    insight.status = "hidden"
    db.flush()
    if not was_hidden:
        _add_audit_log(db, project_user, "insight.hidden", "insight", insight.id)
    db.commit()
    db.refresh(insight)
    return _admin_insight_detail(insight)


def get_published_post_or_404(
    db: Session,
    project_user: ProjectUser,
    post_id: UUID,
    now: datetime | None = None,
) -> CommunityPost:
    current = now or datetime.now(UTC)
    post = (
        db.query(CommunityPost)
        .filter(CommunityPost.id == post_id, *_published_filter(CommunityPost, project_user, current))
        .one_or_none()
    )
    if post is None:
        raise NotFoundError("Post was not found")
    return post


def get_published_insight_or_404(
    db: Session,
    project_user: ProjectUser,
    insight_id: UUID,
    now: datetime | None = None,
) -> CommunityInsight:
    current = now or datetime.now(UTC)
    insight = (
        db.query(CommunityInsight)
        .filter(CommunityInsight.id == insight_id, *_published_filter(CommunityInsight, project_user, current))
        .one_or_none()
    )
    if insight is None:
        raise NotFoundError("Insight was not found")
    return insight


def mark_content_read(
    db: Session,
    project_user: ProjectUser,
    content_type: str,
    content_id: UUID,
    read_at: datetime | None = None,
) -> CommunityContentRead:
    current = read_at or datetime.now(UTC)
    read = (
        db.query(CommunityContentRead)
        .filter(
            CommunityContentRead.project_id == project_user.project_id,
            CommunityContentRead.project_user_id == project_user.id,
            CommunityContentRead.content_type == content_type,
            CommunityContentRead.content_id == content_id,
        )
        .one_or_none()
    )
    if read is None:
        read = CommunityContentRead(
            project_id=project_user.project_id,
            project_user_id=project_user.id,
            content_type=content_type,
            content_id=content_id,
            read_at=current,
        )
        db.add(read)
    else:
        read.read_at = current
    db.flush()
    return read


def get_useful_count(db: Session, project_id: UUID, target_type: str, target_id: UUID) -> int:
    return (
        db.query(CommunityReaction)
        .filter(
            CommunityReaction.project_id == project_id,
            CommunityReaction.target_type == target_type,
            CommunityReaction.target_id == target_id,
            CommunityReaction.reaction_type == "useful",
        )
        .count()
    )


def is_useful_by_project_user(
    db: Session,
    project_user: ProjectUser,
    target_type: str,
    target_id: UUID,
) -> bool:
    return (
        db.query(CommunityReaction)
        .filter(
            CommunityReaction.project_id == project_user.project_id,
            CommunityReaction.project_user_id == project_user.id,
            CommunityReaction.target_type == target_type,
            CommunityReaction.target_id == target_id,
            CommunityReaction.reaction_type == "useful",
        )
        .one_or_none()
        is not None
    )


def toggle_useful_reaction(
    db: Session,
    project_user: ProjectUser,
    target_type: str,
    target_id: UUID,
) -> CommunityUsefulToggleResponse:
    reaction = (
        db.query(CommunityReaction)
        .filter(
            CommunityReaction.project_id == project_user.project_id,
            CommunityReaction.project_user_id == project_user.id,
            CommunityReaction.target_type == target_type,
            CommunityReaction.target_id == target_id,
            CommunityReaction.reaction_type == "useful",
        )
        .one_or_none()
    )
    if reaction is None:
        reaction = CommunityReaction(
            project_id=project_user.project_id,
            project_user_id=project_user.id,
            target_type=target_type,
            target_id=target_id,
            reaction_type="useful",
        )
        db.add(reaction)
        is_useful = True
    else:
        db.delete(reaction)
        is_useful = False

    db.commit()
    return CommunityUsefulToggleResponse(
        useful_count=get_useful_count(db, project_user.project_id, target_type, target_id),
        is_useful_by_me=is_useful,
    )


def _published_filter(model, project_user: ProjectUser, now: datetime):
    return (
        model.project_id == project_user.project_id,
        model.status == "published",
        model.published_at.is_not(None),
        or_(model.scheduled_at.is_(None), model.scheduled_at <= now),
    )


def _get_pinned_post(db: Session, project_user: ProjectUser, now: datetime) -> CommunityPost | None:
    return (
        db.query(CommunityPost)
        .filter(*_published_filter(CommunityPost, project_user, now), CommunityPost.is_pinned.is_(True))
        .order_by(CommunityPost.published_at.desc(), CommunityPost.created_at.desc())
        .first()
    )


def _get_latest_posts(
    db: Session,
    project_user: ProjectUser,
    now: datetime,
    pinned_post_id: UUID | None = None,
) -> list[CommunityPost]:
    query = db.query(CommunityPost).filter(*_published_filter(CommunityPost, project_user, now))
    if pinned_post_id is not None:
        query = query.filter(CommunityPost.id != pinned_post_id)
    return query.order_by(CommunityPost.published_at.desc(), CommunityPost.created_at.desc()).limit(3).all()


def _get_latest_insights(db: Session, project_user: ProjectUser, now: datetime) -> list[CommunityInsight]:
    return (
        db.query(CommunityInsight)
        .filter(*_published_filter(CommunityInsight, project_user, now))
        .order_by(CommunityInsight.is_urgent.desc(), CommunityInsight.published_at.desc(), CommunityInsight.created_at.desc())
        .limit(3)
        .all()
    )


def _get_chat_links(db: Session, project_user: ProjectUser, limit: int | None = 5) -> list[CommunityChatLink]:
    query = (
        db.query(CommunityChatLink)
        .filter(
            CommunityChatLink.project_id == project_user.project_id,
            CommunityChatLink.is_published.is_(True),
        )
        .order_by(CommunityChatLink.sort_order.asc(), CommunityChatLink.created_at.asc())
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def _get_important_notifications(db: Session, project_user: ProjectUser) -> list[CommunityNotification]:
    return (
        db.query(CommunityNotification)
        .filter(
            CommunityNotification.project_id == project_user.project_id,
            CommunityNotification.project_user_id == project_user.id,
            CommunityNotification.type == "urgent_insight",
            CommunityNotification.is_read.is_(False),
        )
        .order_by(CommunityNotification.created_at.desc())
        .limit(5)
        .all()
    )


def _read_content_ids(
    db: Session,
    project_user: ProjectUser,
    content_type: str,
    content_ids: list[UUID],
) -> set[UUID]:
    if not content_ids:
        return set()
    rows = (
        db.query(CommunityContentRead.content_id)
        .filter(
            CommunityContentRead.project_id == project_user.project_id,
            CommunityContentRead.project_user_id == project_user.id,
            CommunityContentRead.content_type == content_type,
            CommunityContentRead.content_id.in_(content_ids),
        )
        .all()
    )
    return {row[0] for row in rows}


def _useful_counts(
    db: Session,
    project_id: UUID,
    post_ids: list[UUID],
    insight_ids: list[UUID],
) -> dict[tuple[str, UUID], int]:
    targets = []
    if post_ids:
        targets.append((CommunityReaction.target_type == "post", CommunityReaction.target_id.in_(post_ids)))
    if insight_ids:
        targets.append((CommunityReaction.target_type == "insight", CommunityReaction.target_id.in_(insight_ids)))
    if not targets:
        return {}

    rows = (
        db.query(CommunityReaction.target_type, CommunityReaction.target_id, func.count(CommunityReaction.id))
        .filter(
            CommunityReaction.project_id == project_id,
            CommunityReaction.reaction_type == "useful",
            or_(*[target_type & target_id for target_type, target_id in targets]),
        )
        .group_by(CommunityReaction.target_type, CommunityReaction.target_id)
        .all()
    )
    return {(target_type, target_id): count for target_type, target_id, count in rows}


def _my_useful_targets(
    db: Session,
    project_user: ProjectUser,
    post_ids: list[UUID],
    insight_ids: list[UUID],
) -> set[tuple[str, UUID]]:
    targets = []
    if post_ids:
        targets.append((CommunityReaction.target_type == "post", CommunityReaction.target_id.in_(post_ids)))
    if insight_ids:
        targets.append((CommunityReaction.target_type == "insight", CommunityReaction.target_id.in_(insight_ids)))
    if not targets:
        return set()

    rows = (
        db.query(CommunityReaction.target_type, CommunityReaction.target_id)
        .filter(
            CommunityReaction.project_id == project_user.project_id,
            CommunityReaction.project_user_id == project_user.id,
            CommunityReaction.reaction_type == "useful",
            or_(*[target_type & target_id for target_type, target_id in targets]),
        )
        .all()
    )
    return {(target_type, target_id) for target_type, target_id in rows}


def _post_item(
    post: CommunityPost,
    read_posts: set[UUID],
    useful_counts: dict[tuple[str, UUID], int],
    my_useful: set[tuple[str, UUID]],
) -> CommunityDashboardContentItem:
    return CommunityDashboardContentItem(
        id=post.id,
        title=post.title,
        excerpt=post.excerpt,
        cover_url=post.cover_url,
        published_at=post.published_at,
        is_new=post.id not in read_posts,
        useful_count=useful_counts.get(("post", post.id), 0),
        is_useful_by_me=("post", post.id) in my_useful,
    )


def _insight_item(
    insight: CommunityInsight,
    read_insights: set[UUID],
    useful_counts: dict[tuple[str, UUID], int],
    my_useful: set[tuple[str, UUID]],
) -> CommunityDashboardInsightItem:
    return CommunityDashboardInsightItem(
        id=insight.id,
        title=insight.title,
        excerpt=insight.excerpt,
        cover_url=None,
        published_at=insight.published_at,
        is_new=insight.id not in read_insights,
        useful_count=useful_counts.get(("insight", insight.id), 0),
        is_useful_by_me=("insight", insight.id) in my_useful,
        is_urgent=insight.is_urgent,
    )


def _validate_admin_list_params(status: str, limit: int, offset: int) -> None:
    if status not in COMMUNITY_ADMIN_STATUS_FILTERS:
        raise ValidationAppError("Unsupported content status filter")
    if limit < 1 or limit > 100:
        raise ValidationAppError("Limit must be between 1 and 100")
    if offset < 0:
        raise ValidationAppError("Offset must be greater than or equal to 0")


def _validate_admin_user_filters(access_state: str, moderation_state: str, role: str, limit: int, offset: int) -> None:
    if access_state not in ("all", "pending", "active", "expired", "revoked"):
        raise ValidationAppError("Unsupported access_state filter")
    if moderation_state not in ("all", "normal", "banned"):
        raise ValidationAppError("Unsupported moderation_state filter")
    if role not in ("all", "member", "admin", "owner"):
        raise ValidationAppError("Unsupported role filter")
    if limit < 1 or limit > 100:
        raise ValidationAppError("Limit must be between 1 and 100")
    if offset < 0:
        raise ValidationAppError("Offset must be greater than or equal to 0")


def _get_admin_project_user_model(db: Session, project_user: ProjectUser, target_project_user_id: UUID) -> ProjectUser:
    target = (
        db.query(ProjectUser)
        .filter(ProjectUser.id == target_project_user_id, ProjectUser.project_id == project_user.project_id)
        .one_or_none()
    )
    if target is None:
        raise NotFoundError("Project user was not found")
    return target


def _get_admin_purchase_request_model(db: Session, project_user: ProjectUser, request_id: UUID) -> CommunityProductPurchaseRequest:
    request = (
        db.query(CommunityProductPurchaseRequest)
        .filter(
            CommunityProductPurchaseRequest.id == request_id,
            CommunityProductPurchaseRequest.project_id == project_user.project_id,
        )
        .one_or_none()
    )
    if request is None:
        raise NotFoundError("Purchase request was not found")
    return request


def _latest_telegram_identity(db: Session, project_user: ProjectUser) -> TelegramIdentity | None:
    return (
        db.query(TelegramIdentity)
        .filter(TelegramIdentity.user_id == project_user.user_id)
        .order_by(TelegramIdentity.updated_at.desc())
        .first()
    )


def _product_access_counts(db: Session, project_user: ProjectUser) -> tuple[int, int]:
    rows = (
        db.query(CommunityProductAccess)
        .filter(
            CommunityProductAccess.project_id == project_user.project_id,
            CommunityProductAccess.project_user_id == project_user.id,
        )
        .all()
    )
    now = datetime.now(UTC)
    active_count = 0
    for row in rows:
        if row.access_state != "active":
            continue
        if row.access_until is None:
            active_count += 1
            continue
        access_until = row.access_until
        if access_until.tzinfo is None:
            access_until = access_until.replace(tzinfo=UTC)
        if access_until >= now:
            active_count += 1
    return len(rows), active_count


def _admin_user_list_item(db: Session, project_user: ProjectUser) -> CommunityAdminUserListItem:
    telegram = _latest_telegram_identity(db, project_user)
    product_access_count, active_product_access_count = _product_access_counts(db, project_user)
    return CommunityAdminUserListItem(
        project_user_id=project_user.id,
        user_id=project_user.user_id,
        telegram_username=telegram.username if telegram else None,
        telegram_first_name=telegram.first_name if telegram else None,
        telegram_photo_url=telegram.photo_url if telegram else None,
        role=project_user.role,
        status=project_user.status,
        access_state=project_user.access_state,
        access_until=project_user.access_until,
        moderation_state=project_user.moderation_state,
        created_at=project_user.created_at,
        updated_at=project_user.updated_at,
        product_access_count=product_access_count,
        active_product_access_count=active_product_access_count,
    )


def _admin_user_product_access_items(
    db: Session,
    admin_project_user: ProjectUser,
    target_project_user_id: UUID,
) -> list[CommunityAdminUserProductAccessItem]:
    rows = (
        db.query(CommunityProductAccess, CommunityProduct.title)
        .join(CommunityProduct, CommunityProduct.id == CommunityProductAccess.product_id)
        .filter(
            CommunityProductAccess.project_id == admin_project_user.project_id,
            CommunityProductAccess.project_user_id == target_project_user_id,
        )
        .order_by(CommunityProductAccess.created_at.desc())
        .all()
    )
    return [
        CommunityAdminUserProductAccessItem(
            access_id=access.id,
            product_id=access.product_id,
            product_title=product_title,
            access_state=access.access_state,
            access_until=access.access_until,
            source=access.source,
            created_at=access.created_at,
            updated_at=access.updated_at,
        )
        for access, product_title in rows
    ]


def _ensure_owner_change_is_safe(
    db: Session,
    admin_project_user: ProjectUser,
    target: ProjectUser,
    next_role: str,
) -> None:
    if target.role != "owner" or next_role == "owner":
        return
    owner_count = (
        db.query(ProjectUser)
        .filter(
            ProjectUser.project_id == admin_project_user.project_id,
            ProjectUser.role == "owner",
            ProjectUser.status == "active",
        )
        .count()
    )
    if owner_count <= 1:
        raise ValidationAppError("Cannot remove the last active owner")


def _add_one_year(value: datetime) -> datetime:
    try:
        return value.replace(year=value.year + 1)
    except ValueError:
        return value.replace(month=2, day=28, year=value.year + 1)


def _validate_scheduled_content(status: str, scheduled_at: datetime | None) -> None:
    if status == "scheduled" and scheduled_at is None:
        raise ValidationAppError("scheduled_at is required for scheduled content")


def _validate_required_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValidationAppError(f"{field_name} is required")


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _validate_exchange_payload(payload: CommunityAdminExchangePayload) -> None:
    _validate_required_text(payload.title, "title")
    _validate_required_text(payload.description, "description")
    _validate_required_text(payload.external_url, "external_url")


def _validate_product_payload(payload: CommunityAdminProductPayload) -> None:
    _validate_required_text(payload.slug, "slug")
    _validate_required_text(payload.title, "title")
    _validate_required_text(payload.short_description, "short_description")
    _validate_required_text(payload.description, "description")


def _validate_material_payload(payload: CommunityAdminProductMaterialPayload) -> None:
    _validate_required_text(payload.title, "title")
    _validate_required_text(payload.material_type, "material_type")


def _project_links(db: Session, project_id: UUID) -> dict[str, str]:
    rows = (
        db.query(CommunityProjectLink)
        .filter(CommunityProjectLink.project_id == project_id, CommunityProjectLink.is_active.is_(True))
        .all()
    )
    return {row.type: row.url for row in rows}


def _public_links_project_id(db: Session) -> UUID | None:
    global_link = (
        db.query(CommunityProjectLink.project_id)
        .join(CommunityProjectLink.project)
        .filter(CommunityProjectLink.is_active.is_(True), CommunityProjectLink.project.has(slug=GLOBAL_GREEN_INVEST_PROJECT_SLUG))
        .first()
    )
    if global_link:
        return global_link[0]
    fallback = db.query(CommunityProjectLink.project_id).filter(CommunityProjectLink.is_active.is_(True)).first()
    return fallback[0] if fallback else None


def _project_page(db: Session, project_id: UUID, slug: str) -> CommunityProjectPage | None:
    return (
        db.query(CommunityProjectPage)
        .filter(
            CommunityProjectPage.project_id == project_id,
            CommunityProjectPage.slug == slug,
            CommunityProjectPage.is_published.is_(True),
        )
        .one_or_none()
    )


def _get_or_create_notification_setting(db: Session, project_user: ProjectUser) -> CommunityNotificationSetting:
    setting = (
        db.query(CommunityNotificationSetting)
        .filter(
            CommunityNotificationSetting.project_id == project_user.project_id,
            CommunityNotificationSetting.project_user_id == project_user.id,
        )
        .one_or_none()
    )
    if setting is None:
        setting = CommunityNotificationSetting(
            project_id=project_user.project_id,
            project_user_id=project_user.id,
            notifications_enabled=True,
        )
        db.add(setting)
        db.flush()
    return setting


def _active_product_access_by_product(
    db: Session,
    project_user: ProjectUser,
    product_ids: list[UUID],
) -> dict[UUID, CommunityProductAccess]:
    if not product_ids:
        return {}
    now = datetime.now(UTC)
    rows = (
        db.query(CommunityProductAccess)
        .filter(
            CommunityProductAccess.project_id == project_user.project_id,
            CommunityProductAccess.project_user_id == project_user.id,
            CommunityProductAccess.product_id.in_(product_ids),
            CommunityProductAccess.access_state == "active",
        )
        .all()
    )
    result: dict[UUID, CommunityProductAccess] = {}
    for row in rows:
        if row.access_until is None:
            result[row.product_id] = row
            continue
        access_until = row.access_until
        if access_until.tzinfo is None:
            access_until = access_until.replace(tzinfo=UTC)
        if access_until >= now:
            result[row.product_id] = row
    return result


def _has_active_product_access(db: Session, project_id: UUID, project_user_id: UUID, product_id: UUID) -> bool:
    access = (
        db.query(CommunityProductAccess)
        .filter(
            CommunityProductAccess.project_id == project_id,
            CommunityProductAccess.project_user_id == project_user_id,
            CommunityProductAccess.product_id == product_id,
            CommunityProductAccess.access_state == "active",
        )
        .one_or_none()
    )
    if access is None:
        return False
    if access.access_until is None:
        return True
    access_until = access.access_until
    if access_until.tzinfo is None:
        access_until = access_until.replace(tzinfo=UTC)
    return access_until >= datetime.now(UTC)


def _open_product_purchase_request(
    db: Session,
    project_user: ProjectUser,
    product: CommunityProduct,
) -> CommunityProductPurchaseRequest | None:
    return (
        db.query(CommunityProductPurchaseRequest)
        .filter(
            CommunityProductPurchaseRequest.project_id == project_user.project_id,
            CommunityProductPurchaseRequest.product_id == product.id,
            CommunityProductPurchaseRequest.project_user_id == project_user.id,
            CommunityProductPurchaseRequest.status.in_(("new", "contacted")),
        )
        .order_by(CommunityProductPurchaseRequest.created_at.desc())
        .first()
    )


def _latest_product_purchase_request(
    db: Session,
    project_user: ProjectUser,
    product: CommunityProduct,
) -> CommunityProductPurchaseRequest | None:
    return (
        db.query(CommunityProductPurchaseRequest)
        .filter(
            CommunityProductPurchaseRequest.project_id == project_user.project_id,
            CommunityProductPurchaseRequest.product_id == product.id,
            CommunityProductPurchaseRequest.project_user_id == project_user.id,
        )
        .order_by(CommunityProductPurchaseRequest.created_at.desc())
        .first()
    )


def _member_purchase_request_item(request: CommunityProductPurchaseRequest | None) -> CommunityProductPurchaseRequestItem | None:
    if request is None:
        return None
    return CommunityProductPurchaseRequestItem(
        request_id=request.id,
        product_id=request.product_id,
        product_title=request.product.title,
        status=request.status,
        created_at=request.created_at,
        updated_at=request.updated_at,
        admin_note=request.admin_note,
    )


def _product_list_item(product: CommunityProduct, access: CommunityProductAccess | None) -> CommunityProductListItem:
    return CommunityProductListItem(
        id=product.id,
        slug=product.slug,
        title=product.title,
        short_description=product.short_description,
        description=product.description,
        cover_url=product.cover_url,
        price_usd=product.price_usd,
        price_rub=product.price_rub,
        sort_order=product.sort_order,
        access_duration_type=product.access_duration_type,
        has_access=access is not None,
        access_until=access.access_until if access else None,
    )


def _product_material_response(material: CommunityProductMaterial) -> CommunityProductMaterialResponse:
    return CommunityProductMaterialResponse(
        id=material.id,
        title=material.title,
        description=material.description,
        material_type=material.material_type,
        content=material.content,
        url=material.url,
        file_url=material.file_url,
        sort_order=material.sort_order,
        is_locked=material.is_locked,
    )


def _get_member_product_model(db: Session, project_user: ProjectUser, product_id_or_slug: str) -> CommunityProduct:
    query = db.query(CommunityProduct).filter(
        CommunityProduct.project_id == project_user.project_id,
        CommunityProduct.is_published.is_(True),
    )
    try:
        product_uuid = UUID(product_id_or_slug)
    except ValueError:
        product_uuid = None
    if product_uuid is not None:
        query = query.filter(CommunityProduct.id == product_uuid)
    else:
        query = query.filter(CommunityProduct.slug == product_id_or_slug)
    product = query.one_or_none()
    if product is None:
        raise NotFoundError("Product was not found")
    return product


def _get_admin_product_model(db: Session, project_user: ProjectUser, product_id: UUID) -> CommunityProduct:
    product = (
        db.query(CommunityProduct)
        .filter(CommunityProduct.id == product_id, CommunityProduct.project_id == project_user.project_id)
        .one_or_none()
    )
    if product is None:
        raise NotFoundError("Product was not found")
    return product


def _get_admin_product_material_model(
    db: Session,
    project_user: ProjectUser,
    product_id: UUID,
    material_id: UUID,
) -> CommunityProductMaterial:
    material = (
        db.query(CommunityProductMaterial)
        .filter(
            CommunityProductMaterial.id == material_id,
            CommunityProductMaterial.product_id == product_id,
            CommunityProductMaterial.project_id == project_user.project_id,
            CommunityProductMaterial.deleted_at.is_(None),
        )
        .one_or_none()
    )
    if material is None:
        raise NotFoundError("Product material was not found")
    return material


def _get_admin_chat_model(db: Session, project_user: ProjectUser, chat_id: UUID) -> CommunityChatLink:
    chat = (
        db.query(CommunityChatLink)
        .filter(
            CommunityChatLink.id == chat_id,
            CommunityChatLink.project_id == project_user.project_id,
        )
        .one_or_none()
    )
    if chat is None:
        raise NotFoundError("Chat was not found")
    return chat


def _get_admin_exchange_model(db: Session, project_user: ProjectUser, exchange_id: UUID) -> CommunityExchange:
    exchange = (
        db.query(CommunityExchange)
        .filter(
            CommunityExchange.id == exchange_id,
            CommunityExchange.project_id == project_user.project_id,
        )
        .one_or_none()
    )
    if exchange is None:
        raise NotFoundError("Exchange was not found")
    return exchange


def _get_admin_post_model(db: Session, project_user: ProjectUser, post_id: UUID) -> CommunityPost:
    post = (
        db.query(CommunityPost)
        .filter(
            CommunityPost.id == post_id,
            CommunityPost.project_id == project_user.project_id,
        )
        .one_or_none()
    )
    if post is None:
        raise NotFoundError("Post was not found")
    return post


def _get_admin_insight_model(db: Session, project_user: ProjectUser, insight_id: UUID) -> CommunityInsight:
    insight = (
        db.query(CommunityInsight)
        .filter(
            CommunityInsight.id == insight_id,
            CommunityInsight.project_id == project_user.project_id,
        )
        .one_or_none()
    )
    if insight is None:
        raise NotFoundError("Insight was not found")
    return insight


def _admin_post_list_item(post: CommunityPost) -> CommunityAdminPostListItem:
    return CommunityAdminPostListItem(
        id=post.id,
        title=post.title,
        excerpt=post.excerpt,
        cover_url=post.cover_url,
        status=post.status,
        is_pinned=post.is_pinned,
        scheduled_at=post.scheduled_at,
        published_at=post.published_at,
        view_count=post.view_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


def _admin_post_detail(post: CommunityPost) -> CommunityAdminPostDetail:
    return CommunityAdminPostDetail(
        **_admin_post_list_item(post).model_dump(),
        content=post.content,
        author_project_user_id=post.author_project_user_id,
    )


def _admin_insight_list_item(insight: CommunityInsight) -> CommunityAdminInsightListItem:
    return CommunityAdminInsightListItem(
        id=insight.id,
        title=insight.title,
        excerpt=insight.excerpt,
        is_urgent=insight.is_urgent,
        status=insight.status,
        scheduled_at=insight.scheduled_at,
        published_at=insight.published_at,
        view_count=insight.view_count,
        telegram_notification_sent_at=insight.telegram_notification_sent_at,
        created_at=insight.created_at,
        updated_at=insight.updated_at,
    )


def _is_urgent_published_insight(insight: CommunityInsight) -> bool:
    return insight.status == "published" and insight.is_urgent


def _is_active_project_user_for_notifications(project_user: ProjectUser, now: datetime) -> bool:
    if project_user.status != "active":
        return False
    if project_user.access_state != "active":
        return False
    if project_user.moderation_state == "banned":
        return False
    if project_user.access_until is None:
        return True
    access_until = project_user.access_until
    if access_until.tzinfo is None:
        access_until = access_until.replace(tzinfo=UTC)
    return access_until >= now


def _notification_setting_enabled(db: Session, project_user: ProjectUser) -> bool:
    setting = (
        db.query(CommunityNotificationSetting)
        .filter(
            CommunityNotificationSetting.project_id == project_user.project_id,
            CommunityNotificationSetting.project_user_id == project_user.id,
        )
        .one_or_none()
    )
    return True if setting is None else setting.notifications_enabled


def _telegram_pilot_targets() -> set[str]:
    return {
        value.strip()
        for value in (settings.telegram_pilot_chat_id, settings.telegram_pilot_telegram_user_id)
        if value.strip()
    }


def _telegram_pilot_target_configured() -> bool:
    return bool(_telegram_pilot_targets())


def _real_pilot_skip_reason(sender_mode: str, telegram: TelegramIdentity) -> str | None:
    if sender_mode != "real":
        return None
    if normalized_telegram_real_send_scope(settings) == "all":
        return None
    targets = _telegram_pilot_targets()
    if not targets:
        return "real_mode_pilot_target_missing"
    if telegram.telegram_id not in targets:
        return "real_mode_pilot_recipient_mismatch"
    return None


def _dry_run_notification_status(sender, telegram: TelegramIdentity) -> tuple[str, str | None]:
    pilot_skip_reason = _real_pilot_skip_reason(sender.mode, telegram)
    if pilot_skip_reason is not None:
        return "skipped", pilot_skip_reason
    if sender.mode == "real" and not sender.ready:
        return "failed", "telegram_bot_token_missing"
    return sender.dry_run_status, None


def _existing_urgent_insight_notification(db: Session, project_user: ProjectUser, insight: CommunityInsight) -> CommunityNotification | None:
    return (
        db.query(CommunityNotification)
        .filter(
            CommunityNotification.project_id == insight.project_id,
            CommunityNotification.project_user_id == project_user.id,
            CommunityNotification.type == "urgent_insight",
            CommunityNotification.target_type == "insight",
            CommunityNotification.target_id == insight.id,
        )
        .one_or_none()
    )


def _create_urgent_insight_notifications(
    db: Session,
    actor_project_user: ProjectUser,
    insight: CommunityInsight,
) -> CommunityUrgentNotificationSummary:
    if not _is_urgent_published_insight(insight):
        return CommunityUrgentNotificationSummary(
            eligible_users=0,
            notifications_created=0,
            telegram_jobs_created=0,
            skipped_disabled=0,
            skipped_no_telegram=0,
            skipped_existing=0,
        )

    now = datetime.now(UTC)
    eligible_users = 0
    notifications_created = 0
    skipped_disabled = 0
    skipped_no_telegram = 0
    skipped_existing = 0
    recipients = db.query(ProjectUser).filter(ProjectUser.project_id == insight.project_id).all()
    for recipient in recipients:
        if not _is_active_project_user_for_notifications(recipient, now):
            continue
        eligible_users += 1
        if not _notification_setting_enabled(db, recipient):
            skipped_disabled += 1
            continue
        if _latest_telegram_identity(db, recipient) is None:
            skipped_no_telegram += 1
        if _existing_urgent_insight_notification(db, recipient, insight) is not None:
            skipped_existing += 1
            continue
        body = insight.excerpt.strip() or insight.content.strip()[:240]
        db.add(
            CommunityNotification(
                project_id=insight.project_id,
                project_user_id=recipient.id,
                type="urgent_insight",
                title=f"Urgent insight: {insight.title}",
                body=body[:500],
                target_type="insight",
                target_id=insight.id,
                is_read=False,
            )
        )
        notifications_created += 1

    summary = CommunityUrgentNotificationSummary(
        eligible_users=eligible_users,
        notifications_created=notifications_created,
        telegram_jobs_created=0,
        skipped_disabled=skipped_disabled,
        skipped_no_telegram=skipped_no_telegram,
        skipped_existing=skipped_existing,
    )
    if notifications_created > 0:
        _add_audit_log(db, actor_project_user, "urgent_insight.notifications_created", "insight", insight.id)
    return summary


def _admin_notification_item(db: Session, notification: CommunityNotification) -> CommunityAdminNotificationItem:
    recipient = db.query(ProjectUser).filter(ProjectUser.id == notification.project_user_id).one()
    telegram = _latest_telegram_identity(db, recipient)
    insight = _notification_insight(db, notification)
    insight_title = insight.title if insight else None
    return CommunityAdminNotificationItem(
        id=notification.id,
        kind=notification.type,
        status=notification.processing_status,
        project_user_id=notification.project_user_id,
        user_id=recipient.user_id,
        telegram_username=telegram.username if telegram else None,
        target_type=notification.target_type,
        target_id=notification.target_id,
        insight_title=insight_title,
        title=notification.title,
        body=notification.body,
        created_at=notification.created_at,
        scheduled_at=None,
        sent_at=notification.processed_at,
        error_message=notification.processing_error,
        mock_message_id=notification.mock_message_id,
    )


def _notification_insight(db: Session, notification: CommunityNotification) -> CommunityInsight | None:
    if notification.target_type != "insight" or notification.target_id is None:
        return None
    return (
        db.query(CommunityInsight)
        .filter(
            CommunityInsight.project_id == notification.project_id,
            CommunityInsight.id == notification.target_id,
        )
        .one_or_none()
    )


def _pending_urgent_notification_count(db: Session, project_id: UUID) -> int:
    return (
        db.query(CommunityNotification)
        .filter(
            CommunityNotification.project_id == project_id,
            CommunityNotification.type == "urgent_insight",
            CommunityNotification.target_type == "insight",
            CommunityNotification.processing_status == "pending",
        )
        .count()
    )


def _admin_insight_detail(
    insight: CommunityInsight,
    urgent_notification_summary: CommunityUrgentNotificationSummary | None = None,
) -> CommunityAdminInsightDetail:
    return CommunityAdminInsightDetail(
        **_admin_insight_list_item(insight).model_dump(),
        content=insight.content,
        author_project_user_id=insight.author_project_user_id,
        urgent_notification_summary=urgent_notification_summary,
    )


def _chat_link_response(chat: CommunityChatLink) -> CommunityChatLinkResponse:
    return CommunityChatLinkResponse(
        id=chat.id,
        title=chat.title,
        telegram_url=chat.telegram_url,
        sort_order=chat.sort_order,
    )


def _exchange_response(exchange: CommunityExchange) -> CommunityExchangeResponse:
    return CommunityExchangeResponse(
        id=exchange.id,
        title=exchange.title,
        description=exchange.description,
        team_comment=exchange.team_comment,
        logo_url=exchange.logo_url,
        external_url=exchange.external_url,
        promo_code=exchange.promo_code,
        sort_order=exchange.sort_order,
    )


def _admin_chat(chat: CommunityChatLink) -> CommunityAdminChat:
    return CommunityAdminChat(
        id=chat.id,
        title=chat.title,
        telegram_url=chat.telegram_url,
        sort_order=chat.sort_order,
        is_published=chat.is_published,
        created_by_project_user_id=chat.created_by_project_user_id,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
    )


def _admin_exchange(exchange: CommunityExchange) -> CommunityAdminExchange:
    return CommunityAdminExchange(
        id=exchange.id,
        title=exchange.title,
        description=exchange.description,
        team_comment=exchange.team_comment,
        logo_url=exchange.logo_url,
        external_url=exchange.external_url,
        promo_code=exchange.promo_code,
        sort_order=exchange.sort_order,
        is_published=exchange.is_published,
        created_by_project_user_id=exchange.created_by_project_user_id,
        created_at=exchange.created_at,
        updated_at=exchange.updated_at,
    )


def _admin_product(product: CommunityProduct) -> CommunityAdminProduct:
    return CommunityAdminProduct(
        id=product.id,
        slug=product.slug,
        title=product.title,
        short_description=product.short_description,
        description=product.description,
        cover_url=product.cover_url,
        price_usd=product.price_usd,
        price_rub=product.price_rub,
        sort_order=product.sort_order,
        is_published=product.is_published,
        access_duration_type=product.access_duration_type,
        created_by_project_user_id=product.created_by_project_user_id,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def _admin_product_material(material: CommunityProductMaterial) -> CommunityAdminProductMaterial:
    return CommunityAdminProductMaterial(
        id=material.id,
        product_id=material.product_id,
        title=material.title,
        description=material.description,
        material_type=material.material_type,
        content=material.content,
        url=material.url,
        file_url=material.file_url,
        sort_order=material.sort_order,
        is_locked=material.is_locked,
        deleted_at=material.deleted_at,
        created_at=material.created_at,
        updated_at=material.updated_at,
    )


def _admin_product_access(access: CommunityProductAccess) -> CommunityAdminProductAccess:
    return CommunityAdminProductAccess(
        id=access.id,
        product_id=access.product_id,
        project_user_id=access.project_user_id,
        access_state=access.access_state,
        access_until=access.access_until,
        source=access.source,
        granted_by_project_user_id=access.granted_by_project_user_id,
        created_at=access.created_at,
        updated_at=access.updated_at,
    )


def _admin_purchase_request_item(db: Session, request: CommunityProductPurchaseRequest) -> CommunityAdminPurchaseRequestItem:
    recipient = db.query(ProjectUser).filter(ProjectUser.id == request.project_user_id).one()
    product = db.query(CommunityProduct).filter(CommunityProduct.id == request.product_id).one()
    telegram = _latest_telegram_identity(db, recipient)
    return CommunityAdminPurchaseRequestItem(
        request_id=request.id,
        status=request.status,
        product_id=request.product_id,
        product_title=product.title,
        project_user_id=request.project_user_id,
        user_id=recipient.user_id,
        telegram_username=telegram.username if telegram else None,
        telegram_first_name=telegram.first_name if telegram else None,
        contact_method=request.contact_method,
        contact_value=request.contact_value,
        message=request.message,
        admin_note=request.admin_note,
        created_at=request.created_at,
        updated_at=request.updated_at,
        handled_at=request.handled_at,
        handled_by=request.handled_by_project_user_id,
        has_active_product_access=_has_active_product_access(db, request.project_id, request.project_user_id, request.product_id),
    )


def _add_audit_log(
    db: Session,
    project_user: ProjectUser,
    action: str,
    entity_type: str,
    entity_id: UUID,
) -> None:
    db.add(
        CommunityAdminAuditLog(
            project_id=project_user.project_id,
            actor_project_user_id=project_user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=None,
        )
    )
