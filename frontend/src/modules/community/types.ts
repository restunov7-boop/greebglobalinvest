export const GLOBAL_GREEN_INVEST_PROJECT_SLUG = "global-green-invest";
export const GLOBAL_GREEN_INVEST_BRAND_NAME = "🍀 ЗЕЛЁНЫЙ / TG Investor";

export type CommunityPlaceholderPage = {
  title: string;
  description: string;
};

export type CommunityAdminInfo = {
  project_slug?: string;
  project_name?: string;
  brand_name?: string;
  role?: string;
  can_access_admin?: boolean;
  scope?: string;
};

export type CommunityDashboardNotification = {
  id: string;
  type: string;
  title: string;
  body: string;
  target_type: string | null;
  target_id: string | null;
  created_at: string;
  is_read: boolean;
};

export type CommunityDashboardContentItem = {
  id: string;
  title: string;
  excerpt: string;
  cover_url: string | null;
  published_at: string | null;
  is_new: boolean;
  useful_count: number;
  is_useful_by_me: boolean;
};

export type CommunityDashboardInsightItem = CommunityDashboardContentItem & {
  is_urgent: boolean;
};

export type CommunityDashboardChatLink = {
  id: string;
  title: string;
  telegram_url: string;
  sort_order: number;
};

export type CommunityDashboardResponse = {
  important_notifications: CommunityDashboardNotification[];
  pinned_post: CommunityDashboardContentItem | null;
  posts: CommunityDashboardContentItem[];
  insights: CommunityDashboardInsightItem[];
  chat_links: CommunityDashboardChatLink[];
};

export type CommunityPostDetail = {
  id: string;
  title: string;
  excerpt: string;
  content: string;
  cover_url: string | null;
  published_at: string | null;
  view_count: number;
  useful_count: number;
  is_useful_by_me: boolean;
  is_new: boolean;
};

export type CommunityInsightDetail = {
  id: string;
  title: string;
  excerpt: string;
  content: string;
  is_urgent: boolean;
  published_at: string | null;
  view_count: number;
  useful_count: number;
  is_useful_by_me: boolean;
  is_new: boolean;
};

export type CommunityUsefulToggleResponse = {
  useful_count: number;
  is_useful_by_me: boolean;
};

export type CommunityAdminContentStatus = "draft" | "scheduled" | "published" | "hidden";
export type CommunityAdminStatusFilter = CommunityAdminContentStatus | "all";

export type CommunityAdminListParams = {
  status?: CommunityAdminStatusFilter;
  limit?: number;
  offset?: number;
};

export type CommunityAdminPostListItem = {
  id: string;
  title: string;
  excerpt: string;
  cover_url: string | null;
  status: CommunityAdminContentStatus;
  is_pinned: boolean;
  scheduled_at: string | null;
  published_at: string | null;
  view_count: number;
  created_at: string;
  updated_at: string;
};

export type CommunityAdminPost = CommunityAdminPostListItem & {
  content: string;
  author_project_user_id: string;
};

export type CommunityAdminPostPayload = {
  title: string;
  excerpt: string;
  content: string;
  cover_url: string | null;
  status: CommunityAdminContentStatus;
  is_pinned: boolean;
  scheduled_at: string | null;
  published_at: string | null;
};

export type CommunityAdminPostListResponse = {
  items: CommunityAdminPostListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type CommunityAdminInsightListItem = {
  id: string;
  title: string;
  excerpt: string;
  is_urgent: boolean;
  status: CommunityAdminContentStatus;
  scheduled_at: string | null;
  published_at: string | null;
  view_count: number;
  telegram_notification_sent_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CommunityUrgentNotificationSummary = {
  eligible_users: number;
  notifications_created: number;
  telegram_jobs_created: number;
  skipped_disabled: number;
  skipped_no_telegram: number;
  skipped_existing: number;
};

export type CommunityAdminInsight = CommunityAdminInsightListItem & {
  content: string;
  author_project_user_id: string;
  urgent_notification_summary?: CommunityUrgentNotificationSummary | null;
};

export type CommunityAdminInsightPayload = {
  title: string;
  excerpt: string;
  content: string;
  is_urgent: boolean;
  status: CommunityAdminContentStatus;
  scheduled_at: string | null;
  published_at: string | null;
};

export type CommunityAdminInsightListResponse = {
  items: CommunityAdminInsightListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type CommunityAdminNotificationItem = {
  id: string;
  kind: string;
  status: "pending" | "mock_sent" | "sent" | "skipped" | "failed";
  project_user_id: string;
  user_id: string;
  telegram_username: string | null;
  target_type: string | null;
  target_id: string | null;
  insight_title: string | null;
  title: string;
  body: string;
  created_at: string;
  scheduled_at: string | null;
  sent_at: string | null;
  error_message: string | null;
  mock_message_id: string | null;
};

export type CommunityAdminNotificationListResponse = {
  items: CommunityAdminNotificationItem[];
  total: number;
  limit: number;
  offset: number;
};

export type CommunityAdminNotificationListParams = {
  type?: string;
  status?: "all" | "pending" | "mock_sent" | "sent" | "skipped" | "failed";
  limit?: number;
  offset?: number;
};

export type CommunityAdminNotificationProcessPayload = {
  limit?: number;
  dry_run?: boolean;
};

export type CommunityAdminNotificationProcessSummary = {
  processed: number;
  sent_mock: number;
  sent: number;
  skipped: number;
  failed: number;
  remaining_pending: number;
  dry_run: boolean;
  mode: "mock" | "real";
};

export type CommunityAdminNotificationSenderStatus = {
  mode: "mock" | "real";
  real_enabled: boolean;
  token_configured: boolean;
  real_send_scope: "pilot" | "all";
  pilot_target_configured: boolean;
  api_base_url: string;
  warning: string | null;
};

export type CommunityChatLink = {
  id: string;
  title: string;
  telegram_url: string;
  sort_order: number;
};

export type CommunityExchange = {
  id: string;
  title: string;
  description: string;
  team_comment: string | null;
  logo_url: string | null;
  external_url: string;
  promo_code: string | null;
  sort_order: number;
};

export type CommunityAdminChat = {
  id: string;
  title: string;
  telegram_url: string;
  sort_order: number;
  is_published: boolean;
  created_by_project_user_id: string;
  created_at: string;
  updated_at: string;
};

export type CommunityAdminChatPayload = {
  title: string;
  telegram_url: string;
  sort_order: number;
  is_published: boolean;
};

export type CommunityAdminExchange = {
  id: string;
  title: string;
  description: string;
  team_comment: string | null;
  logo_url: string | null;
  external_url: string;
  promo_code: string | null;
  sort_order: number;
  is_published: boolean;
  created_by_project_user_id: string;
  created_at: string;
  updated_at: string;
};

export type CommunityAdminExchangePayload = {
  title: string;
  description: string;
  team_comment: string | null;
  logo_url: string | null;
  external_url: string;
  promo_code: string | null;
  sort_order: number;
  is_published: boolean;
};

export type CommunityPublicLinks = {
  support_url: string | null;
  telegram_bot_url: string | null;
  website_url: string | null;
  blogger_telegram_url: string | null;
};

export type CommunityProfile = {
  telegram_first_name: string | null;
  telegram_username: string | null;
  telegram_avatar_url: string | null;
  access_state: string;
  access_until: string | null;
  moderation_state: string;
  support_url: string | null;
};

export type CommunitySettings = CommunityPublicLinks & {
  notifications_enabled: boolean;
  about_title: string | null;
  about_content: string | null;
  rules_title: string | null;
  rules_content: string | null;
  disclaimer: string | null;
};

export type CommunityRules = {
  title: string;
  content: string;
  disclaimer: string;
  support_url: string | null;
};

export type CommunityProductMaterial = {
  id: string;
  title: string;
  description: string | null;
  material_type: "text" | "link" | "file_view" | "external_site";
  content: string | null;
  url: string | null;
  file_url: string | null;
  sort_order: number;
  is_locked: boolean;
};

export type CommunityProductPurchaseRequestStatus = "new" | "contacted" | "approved" | "rejected" | "cancelled";

export type CommunityProductPurchaseRequest = {
  request_id: string;
  product_id: string;
  product_title: string;
  status: CommunityProductPurchaseRequestStatus;
  created_at: string;
  updated_at: string;
  admin_note: string | null;
};

export type CommunityProductPurchaseRequestPayload = {
  contact_method: "telegram" | "phone" | "email" | "other" | null;
  contact_value: string | null;
  message: string | null;
};

export type CommunityProductPurchaseRequestCreated = {
  request_id: string;
  status: CommunityProductPurchaseRequestStatus;
  product_id: string;
  product_title: string;
  created_at: string;
};

export type CommunityProduct = {
  id: string;
  slug: string;
  title: string;
  short_description: string;
  description: string;
  cover_url: string | null;
  price_usd: string | null;
  price_rub: string | null;
  sort_order: number;
  access_duration_type: string;
  has_access: boolean;
  access_until: string | null;
};

export type CommunityProductDetail = CommunityProduct & {
  materials: CommunityProductMaterial[];
  has_locked_materials: boolean;
  locked_materials_count: number;
  support_url: string | null;
  purchase_request: CommunityProductPurchaseRequest | null;
};

export type CommunityAdminPurchaseRequest = {
  request_id: string;
  status: CommunityProductPurchaseRequestStatus;
  product_id: string;
  product_title: string;
  project_user_id: string;
  user_id: string;
  telegram_username: string | null;
  telegram_first_name: string | null;
  contact_method: string | null;
  contact_value: string | null;
  message: string | null;
  admin_note: string | null;
  created_at: string;
  updated_at: string;
  handled_at: string | null;
  handled_by: string | null;
  has_active_product_access: boolean;
};

export type CommunityAdminPurchaseRequestListResponse = {
  items: CommunityAdminPurchaseRequest[];
  total: number;
  limit: number;
  offset: number;
};

export type CommunityAdminPurchaseRequestListParams = {
  status?: "all" | CommunityProductPurchaseRequestStatus;
  product_id?: string;
  q?: string;
  limit?: number;
  offset?: number;
};

export type CommunityAdminPurchaseRequestUpdatePayload = {
  status?: CommunityProductPurchaseRequestStatus;
  admin_note?: string | null;
};

export type CommunityAdminPurchaseRequestApprovePayload = {
  access_until: string | null;
};

export type CommunityAdminProduct = {
  id: string;
  slug: string;
  title: string;
  short_description: string;
  description: string;
  cover_url: string | null;
  price_usd: string | null;
  price_rub: string | null;
  sort_order: number;
  is_published: boolean;
  access_duration_type: string;
  created_by_project_user_id: string;
  created_at: string;
  updated_at: string;
};

export type CommunityAdminProductPayload = {
  slug: string;
  title: string;
  short_description: string;
  description: string;
  cover_url: string | null;
  price_usd: string | null;
  price_rub: string | null;
  sort_order: number;
  is_published: boolean;
  access_duration_type: string;
};

export type CommunityAdminProductMaterial = CommunityProductMaterial & {
  product_id: string;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type CommunityAdminProductMaterialPayload = {
  title: string;
  description: string | null;
  material_type: "text" | "link" | "file_view" | "external_site";
  content: string | null;
  url: string | null;
  file_url: string | null;
  sort_order: number;
  is_locked: boolean;
};

export type CommunityAdminProductAccessState = "active" | "expired" | "revoked";
export type CommunityAdminProjectAccessState = "pending" | "active" | "expired" | "revoked";
export type CommunityAdminModerationState = "normal" | "banned";
export type CommunityAdminProjectRole = "member" | "admin" | "owner";

export type CommunityAdminProductAccess = {
  id: string;
  product_id: string;
  project_user_id: string;
  access_state: CommunityAdminProductAccessState;
  access_until: string | null;
  source: string;
  granted_by_project_user_id: string | null;
  created_at: string;
  updated_at: string;
};

export type CommunityAdminProductAccessPayload = {
  product_id: string;
  project_user_id: string;
  access_state: CommunityAdminProductAccessState;
  access_until: string | null;
  source?: string;
};

export type CommunityAdminProductAccessUpdatePayload = {
  access_state: CommunityAdminProductAccessState;
  access_until: string | null;
};

export type CommunityAdminUserProductAccessItem = {
  access_id: string;
  product_id: string;
  product_title: string;
  access_state: CommunityAdminProductAccessState;
  access_until: string | null;
  source: string;
  created_at: string;
  updated_at: string;
};

export type CommunityAdminUserListItem = {
  project_user_id: string;
  user_id: string;
  telegram_username: string | null;
  telegram_first_name: string | null;
  telegram_photo_url: string | null;
  role: CommunityAdminProjectRole;
  status: string;
  access_state: CommunityAdminProjectAccessState;
  access_until: string | null;
  moderation_state: CommunityAdminModerationState;
  created_at: string;
  updated_at: string;
  product_access_count: number;
  active_product_access_count: number;
};

export type CommunityAdminUserDetail = CommunityAdminUserListItem & {
  product_access: CommunityAdminUserProductAccessItem[];
};

export type CommunityAdminUserListResponse = {
  items: CommunityAdminUserListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type CommunityAdminUserListParams = {
  q?: string;
  access_state?: "all" | CommunityAdminProjectAccessState;
  moderation_state?: "all" | CommunityAdminModerationState;
  role?: "all" | CommunityAdminProjectRole;
  limit?: number;
  offset?: number;
};

export type CommunityAdminUserProjectAccessUpdatePayload = {
  access_state?: CommunityAdminProjectAccessState;
  access_until?: string | null;
  status?: string;
  role?: CommunityAdminProjectRole;
  moderation_state?: CommunityAdminModerationState;
};
