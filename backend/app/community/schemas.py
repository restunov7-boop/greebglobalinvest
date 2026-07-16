from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

COMMUNITY_CONTENT_STATUSES = ("draft", "scheduled", "published", "hidden")
COMMUNITY_ADMIN_STATUS_FILTERS = (*COMMUNITY_CONTENT_STATUSES, "all")
COMMUNITY_PRODUCT_ACCESS_DURATION_TYPES = ("lifetime", "fixed_until", "custom")
COMMUNITY_PRODUCT_MATERIAL_TYPES = ("text", "link", "file_view", "external_site")
COMMUNITY_PRODUCT_ACCESS_STATES = ("active", "expired", "revoked")
COMMUNITY_PRODUCT_PURCHASE_REQUEST_STATUSES = ("new", "contacted", "approved", "rejected", "cancelled")
COMMUNITY_PRODUCT_PURCHASE_REQUEST_OPEN_STATUSES = ("new", "contacted")
COMMUNITY_PROJECT_ACCESS_STATES = ("pending", "active", "expired", "revoked")
COMMUNITY_PROJECT_MODERATION_STATES = ("normal", "banned")
COMMUNITY_PROJECT_ROLES = ("member", "admin", "owner")
COMMUNITY_NOTIFICATION_PROCESSING_STATUSES = ("pending", "mock_sent", "sent", "skipped", "failed")


class CommunityInfo(BaseModel):
    project_slug: str
    brand_name: str
    status: str
    scope: str


class CommunityDashboardNotification(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    target_type: str | None = None
    target_id: UUID | None = None
    created_at: datetime
    is_read: bool


class CommunityDashboardContentItem(BaseModel):
    id: UUID
    title: str
    excerpt: str
    cover_url: str | None = None
    published_at: datetime | None = None
    is_new: bool
    useful_count: int
    is_useful_by_me: bool


class CommunityDashboardInsightItem(CommunityDashboardContentItem):
    is_urgent: bool


class CommunityDashboardChatLink(BaseModel):
    id: UUID
    title: str
    telegram_url: str
    sort_order: int


class CommunityDashboardResponse(BaseModel):
    important_notifications: list[CommunityDashboardNotification]
    pinned_post: CommunityDashboardContentItem | None = None
    posts: list[CommunityDashboardContentItem]
    insights: list[CommunityDashboardInsightItem]
    chat_links: list[CommunityDashboardChatLink]


class CommunityPostDetailResponse(BaseModel):
    id: UUID
    title: str
    excerpt: str
    content: str
    cover_url: str | None = None
    published_at: datetime | None = None
    view_count: int
    useful_count: int
    is_useful_by_me: bool
    is_new: bool


class CommunityInsightDetailResponse(BaseModel):
    id: UUID
    title: str
    excerpt: str
    content: str
    is_urgent: bool
    published_at: datetime | None = None
    view_count: int
    useful_count: int
    is_useful_by_me: bool
    is_new: bool


class CommunityUsefulToggleResponse(BaseModel):
    useful_count: int
    is_useful_by_me: bool


class CommunityAdminPostListItem(BaseModel):
    id: UUID
    title: str
    excerpt: str
    cover_url: str | None = None
    status: str
    is_pinned: bool
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    view_count: int
    created_at: datetime
    updated_at: datetime


class CommunityAdminPostDetail(CommunityAdminPostListItem):
    content: str
    author_project_user_id: UUID


class CommunityAdminPostCreate(BaseModel):
    title: str
    excerpt: str
    content: str
    cover_url: str | None = None
    status: str = "draft"
    is_pinned: bool = False
    scheduled_at: datetime | None = None
    published_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in COMMUNITY_CONTENT_STATUSES:
            raise ValueError("Unsupported content status")
        return value


class CommunityAdminPostUpdate(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    cover_url: str | None = None
    status: str | None = None
    is_pinned: bool | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in COMMUNITY_CONTENT_STATUSES:
            raise ValueError("Unsupported content status")
        return value


class CommunityAdminPostListResponse(BaseModel):
    items: list[CommunityAdminPostListItem]
    total: int
    limit: int
    offset: int


class CommunityAdminInsightListItem(BaseModel):
    id: UUID
    title: str
    excerpt: str
    is_urgent: bool
    status: str
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    view_count: int
    telegram_notification_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CommunityUrgentNotificationSummary(BaseModel):
    eligible_users: int
    notifications_created: int
    telegram_jobs_created: int = 0
    skipped_disabled: int
    skipped_no_telegram: int
    skipped_existing: int


class CommunityAdminInsightDetail(CommunityAdminInsightListItem):
    content: str
    author_project_user_id: UUID
    urgent_notification_summary: CommunityUrgentNotificationSummary | None = None


class CommunityAdminInsightCreate(BaseModel):
    title: str
    excerpt: str
    content: str
    is_urgent: bool = False
    status: str = "draft"
    scheduled_at: datetime | None = None
    published_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in COMMUNITY_CONTENT_STATUSES:
            raise ValueError("Unsupported content status")
        return value


class CommunityAdminInsightUpdate(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content: str | None = None
    is_urgent: bool | None = None
    status: str | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in COMMUNITY_CONTENT_STATUSES:
            raise ValueError("Unsupported content status")
        return value


class CommunityAdminInsightListResponse(BaseModel):
    items: list[CommunityAdminInsightListItem]
    total: int
    limit: int
    offset: int


class CommunityAdminNotificationItem(BaseModel):
    id: UUID
    kind: str
    status: str
    project_user_id: UUID
    user_id: UUID
    telegram_username: str | None = None
    target_type: str | None = None
    target_id: UUID | None = None
    insight_title: str | None = None
    title: str
    body: str
    created_at: datetime
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    error_message: str | None = None
    mock_message_id: str | None = None


class CommunityAdminNotificationListResponse(BaseModel):
    items: list[CommunityAdminNotificationItem]
    total: int
    limit: int
    offset: int


class CommunityAdminNotificationProcessPayload(BaseModel):
    limit: int = 50
    dry_run: bool = False


class CommunityAdminNotificationProcessSummary(BaseModel):
    processed: int
    sent_mock: int
    sent: int = 0
    skipped: int
    failed: int
    remaining_pending: int
    dry_run: bool = False
    mode: str = "mock"


class CommunityAdminNotificationSenderStatus(BaseModel):
    mode: str
    real_enabled: bool
    token_configured: bool
    real_send_scope: str = "pilot"
    pilot_target_configured: bool = False
    api_base_url: str
    warning: str | None = None


class CommunityChatLinkResponse(BaseModel):
    id: UUID
    title: str
    telegram_url: str
    sort_order: int


class CommunityExchangeResponse(BaseModel):
    id: UUID
    title: str
    description: str
    team_comment: str | None = None
    logo_url: str | None = None
    external_url: str
    promo_code: str | None = None
    sort_order: int


class CommunityAdminChat(BaseModel):
    id: UUID
    title: str
    telegram_url: str
    sort_order: int
    is_published: bool
    created_by_project_user_id: UUID
    created_at: datetime
    updated_at: datetime


class CommunityAdminChatPayload(BaseModel):
    title: str
    telegram_url: str
    sort_order: int = 0
    is_published: bool = False


class CommunityAdminExchange(BaseModel):
    id: UUID
    title: str
    description: str
    team_comment: str | None = None
    logo_url: str | None = None
    external_url: str
    promo_code: str | None = None
    sort_order: int
    is_published: bool
    created_by_project_user_id: UUID
    created_at: datetime
    updated_at: datetime


class CommunityAdminExchangePayload(BaseModel):
    title: str
    description: str
    team_comment: str | None = None
    logo_url: str | None = None
    external_url: str
    promo_code: str | None = None
    sort_order: int = 0
    is_published: bool = False


class CommunityPublicLinks(BaseModel):
    support_url: str | None = None
    telegram_bot_url: str | None = None
    website_url: str | None = None
    blogger_telegram_url: str | None = None


class CommunityProfileResponse(BaseModel):
    telegram_first_name: str | None = None
    telegram_username: str | None = None
    telegram_avatar_url: str | None = None
    access_state: str
    access_until: datetime | None = None
    moderation_state: str
    support_url: str | None = None


class CommunitySettingsResponse(CommunityPublicLinks):
    notifications_enabled: bool
    about_title: str | None = None
    about_content: str | None = None
    rules_title: str | None = None
    rules_content: str | None = None
    disclaimer: str | None = None


class CommunityNotificationSettingsPatch(BaseModel):
    notifications_enabled: bool


class CommunityRulesResponse(BaseModel):
    title: str
    content: str
    disclaimer: str
    support_url: str | None = None


class CommunityProductListItem(BaseModel):
    id: UUID
    slug: str
    title: str
    short_description: str
    description: str
    cover_url: str | None = None
    price_usd: Decimal | None = None
    price_rub: Decimal | None = None
    sort_order: int
    access_duration_type: str
    has_access: bool
    access_until: datetime | None = None


class CommunityProductMaterialResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    material_type: str
    content: str | None = None
    url: str | None = None
    file_url: str | None = None
    sort_order: int
    is_locked: bool


class CommunityProductDetail(CommunityProductListItem):
    materials: list[CommunityProductMaterialResponse]
    has_locked_materials: bool
    locked_materials_count: int
    support_url: str | None = None
    purchase_request: "CommunityProductPurchaseRequestItem | None" = None


class CommunityProductPurchaseRequestCreate(BaseModel):
    contact_method: str | None = None
    contact_value: str | None = None
    message: str | None = None

    @field_validator("contact_method")
    @classmethod
    def validate_contact_method(cls, value: str | None) -> str | None:
        if value is not None and value not in ("telegram", "phone", "email", "other"):
            raise ValueError("Unsupported contact method")
        return value


class CommunityProductPurchaseRequestItem(BaseModel):
    request_id: UUID
    product_id: UUID
    product_title: str
    status: str
    created_at: datetime
    updated_at: datetime
    admin_note: str | None = None


class CommunityProductPurchaseRequestCreated(BaseModel):
    request_id: UUID
    status: str
    product_id: UUID
    product_title: str
    created_at: datetime


class CommunityAdminPurchaseRequestItem(BaseModel):
    request_id: UUID
    status: str
    product_id: UUID
    product_title: str
    project_user_id: UUID
    user_id: UUID
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    contact_method: str | None = None
    contact_value: str | None = None
    message: str | None = None
    admin_note: str | None = None
    created_at: datetime
    updated_at: datetime
    handled_at: datetime | None = None
    handled_by: UUID | None = None
    has_active_product_access: bool


class CommunityAdminPurchaseRequestListResponse(BaseModel):
    items: list[CommunityAdminPurchaseRequestItem]
    total: int
    limit: int
    offset: int


class CommunityAdminPurchaseRequestUpdate(BaseModel):
    status: str | None = None
    admin_note: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is not None and value not in COMMUNITY_PRODUCT_PURCHASE_REQUEST_STATUSES:
            raise ValueError("Unsupported purchase request status")
        return value


class CommunityAdminPurchaseRequestApproveGrant(BaseModel):
    access_until: datetime | None = None


class CommunityAdminProduct(BaseModel):
    id: UUID
    slug: str
    title: str
    short_description: str
    description: str
    cover_url: str | None = None
    price_usd: Decimal | None = None
    price_rub: Decimal | None = None
    sort_order: int
    is_published: bool
    access_duration_type: str
    created_by_project_user_id: UUID
    created_at: datetime
    updated_at: datetime


class CommunityAdminProductPayload(BaseModel):
    slug: str
    title: str
    short_description: str
    description: str
    cover_url: str | None = None
    price_usd: Decimal | None = None
    price_rub: Decimal | None = None
    sort_order: int = 0
    is_published: bool = False
    access_duration_type: str = "lifetime"

    @field_validator("access_duration_type")
    @classmethod
    def validate_access_duration_type(cls, value: str) -> str:
        if value not in COMMUNITY_PRODUCT_ACCESS_DURATION_TYPES:
            raise ValueError("Unsupported product access duration type")
        return value


class CommunityAdminProductMaterial(BaseModel):
    id: UUID
    product_id: UUID
    title: str
    description: str | None = None
    material_type: str
    content: str | None = None
    url: str | None = None
    file_url: str | None = None
    sort_order: int
    is_locked: bool
    deleted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CommunityAdminProductMaterialPayload(BaseModel):
    title: str
    description: str | None = None
    material_type: str
    content: str | None = None
    url: str | None = None
    file_url: str | None = None
    sort_order: int = 0
    is_locked: bool = True

    @field_validator("material_type")
    @classmethod
    def validate_material_type(cls, value: str) -> str:
        if value not in COMMUNITY_PRODUCT_MATERIAL_TYPES:
            raise ValueError("Unsupported material type")
        return value


class CommunityAdminProductAccess(BaseModel):
    id: UUID
    product_id: UUID
    project_user_id: UUID
    access_state: str
    access_until: datetime | None = None
    source: str
    granted_by_project_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class CommunityAdminUserProductAccessItem(BaseModel):
    access_id: UUID
    product_id: UUID
    product_title: str
    access_state: str
    access_until: datetime | None = None
    source: str
    created_at: datetime
    updated_at: datetime


class CommunityAdminUserListItem(BaseModel):
    project_user_id: UUID
    user_id: UUID
    telegram_username: str | None = None
    telegram_first_name: str | None = None
    telegram_photo_url: str | None = None
    role: str
    status: str
    access_state: str
    access_until: datetime | None = None
    moderation_state: str
    created_at: datetime
    updated_at: datetime
    product_access_count: int
    active_product_access_count: int


class CommunityAdminUserDetail(CommunityAdminUserListItem):
    product_access: list[CommunityAdminUserProductAccessItem]


class CommunityAdminUserListResponse(BaseModel):
    items: list[CommunityAdminUserListItem]
    total: int
    limit: int
    offset: int


class CommunityAdminUserProjectAccessUpdate(BaseModel):
    access_state: str | None = None
    access_until: datetime | None = None
    status: str | None = None
    role: str | None = None
    moderation_state: str | None = None

    @field_validator("access_state")
    @classmethod
    def validate_access_state(cls, value: str | None) -> str | None:
        if value is not None and value not in COMMUNITY_PROJECT_ACCESS_STATES:
            raise ValueError("Unsupported project access state")
        return value

    @field_validator("moderation_state")
    @classmethod
    def validate_moderation_state(cls, value: str | None) -> str | None:
        if value is not None and value not in COMMUNITY_PROJECT_MODERATION_STATES:
            raise ValueError("Unsupported moderation state")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str | None) -> str | None:
        if value is not None and value not in COMMUNITY_PROJECT_ROLES:
            raise ValueError("Unsupported project role")
        return value


class CommunityAdminProductAccessCreate(BaseModel):
    product_id: UUID
    project_user_id: UUID
    access_state: str = "active"
    access_until: datetime | None = None
    source: str = "manual"

    @field_validator("access_state")
    @classmethod
    def validate_access_state(cls, value: str) -> str:
        if value not in COMMUNITY_PRODUCT_ACCESS_STATES:
            raise ValueError("Unsupported product access state")
        return value


class CommunityAdminProductAccessUpdate(BaseModel):
    access_state: str
    access_until: datetime | None = None

    @field_validator("access_state")
    @classmethod
    def validate_access_state(cls, value: str) -> str:
        if value not in COMMUNITY_PRODUCT_ACCESS_STATES:
            raise ValueError("Unsupported product access state")
        return value
