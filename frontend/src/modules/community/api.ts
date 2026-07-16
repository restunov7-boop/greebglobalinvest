import { apiClient } from "../../shared/api/client";

import type {
  CommunityAdminChat,
  CommunityAdminChatPayload,
  CommunityAdminExchange,
  CommunityAdminExchangePayload,
  CommunityAdminInfo,
  CommunityAdminNotificationListParams,
  CommunityAdminNotificationListResponse,
  CommunityAdminNotificationProcessPayload,
  CommunityAdminNotificationProcessSummary,
  CommunityAdminNotificationSenderStatus,
  CommunityAdminProduct,
  CommunityAdminProductAccess,
  CommunityAdminProductAccessPayload,
  CommunityAdminProductAccessUpdatePayload,
  CommunityAdminProductMaterial,
  CommunityAdminProductMaterialPayload,
  CommunityAdminProductPayload,
  CommunityAdminPurchaseRequest,
  CommunityAdminPurchaseRequestApprovePayload,
  CommunityAdminPurchaseRequestListParams,
  CommunityAdminPurchaseRequestListResponse,
  CommunityAdminPurchaseRequestUpdatePayload,
  CommunityAdminUserDetail,
  CommunityAdminUserListParams,
  CommunityAdminUserListResponse,
  CommunityAdminUserProjectAccessUpdatePayload,
  CommunityAdminInsight,
  CommunityAdminInsightListResponse,
  CommunityAdminInsightPayload,
  CommunityAdminListParams,
  CommunityAdminPost,
  CommunityAdminPostListResponse,
  CommunityAdminPostPayload,
  CommunityDashboardResponse,
  CommunityChatLink,
  CommunityExchange,
  CommunityInsightDetail,
  CommunityPostDetail,
  CommunityProduct,
  CommunityProductDetail,
  CommunityProductPurchaseRequest,
  CommunityProductPurchaseRequestCreated,
  CommunityProductPurchaseRequestPayload,
  CommunityProfile,
  CommunityPublicLinks,
  CommunityRules,
  CommunitySettings,
  CommunityUsefulToggleResponse,
} from "./types";

export const communityApiPaths = {
  info: "/community/info",
  adminInfo: "/community/admin/info",
  adminNotifications: "/community/admin/notifications",
  adminNotificationsSenderStatus: "/community/admin/notifications/sender-status",
  adminNotificationsProcessPending: "/community/admin/notifications/process-pending",
  dashboard: "/community/dashboard",
  post: (postId: string) => `/community/posts/${postId}`,
  insight: (insightId: string) => `/community/insights/${insightId}`,
  postUseful: (postId: string) => `/community/posts/${postId}/useful`,
  insightUseful: (insightId: string) => `/community/insights/${insightId}/useful`,
  adminPosts: "/community/admin/posts",
  adminPost: (postId: string) => `/community/admin/posts/${postId}`,
  adminInsights: "/community/admin/insights",
  adminInsight: (insightId: string) => `/community/admin/insights/${insightId}`,
  chats: "/community/chats",
  exchanges: "/community/exchanges",
  adminChats: "/community/admin/chats",
  adminChat: (chatId: string) => `/community/admin/chats/${chatId}`,
  adminExchanges: "/community/admin/exchanges",
  adminExchange: (exchangeId: string) => `/community/admin/exchanges/${exchangeId}`,
  profile: "/community/profile",
  settings: "/community/settings",
  notificationSettings: "/community/settings/notifications",
  rules: "/community/rules",
  publicLinks: "/community/public-links",
  products: "/community/products",
  product: (productId: string) => `/community/products/${productId}`,
  productPurchaseRequest: (productId: string) => `/community/products/${productId}/purchase-request`,
  myPurchaseRequests: "/community/my-purchase-requests",
  adminProducts: "/community/admin/products",
  adminProduct: (productId: string) => `/community/admin/products/${productId}`,
  adminProductMaterials: (productId: string) => `/community/admin/products/${productId}/materials`,
  adminProductMaterial: (productId: string, materialId: string) => `/community/admin/products/${productId}/materials/${materialId}`,
  adminUsers: "/community/admin/users",
  adminUser: (projectUserId: string) => `/community/admin/users/${projectUserId}`,
  adminUserProjectAccess: (projectUserId: string) => `/community/admin/users/${projectUserId}/project-access`,
  adminUserExtendOneYear: (projectUserId: string) => `/community/admin/users/${projectUserId}/extend-one-year`,
  adminUserBan: (projectUserId: string) => `/community/admin/users/${projectUserId}/ban`,
  adminUserUnban: (projectUserId: string) => `/community/admin/users/${projectUserId}/unban`,
  adminProductAccess: "/community/admin/product-access",
  adminProductAccessItem: (accessId: string) => `/community/admin/product-access/${accessId}`,
  adminPurchaseRequests: "/community/admin/purchase-requests",
  adminPurchaseRequest: (requestId: string) => `/community/admin/purchase-requests/${requestId}`,
  adminPurchaseRequestApproveGrant: (requestId: string) => `/community/admin/purchase-requests/${requestId}/approve-and-grant`,
} as const;

function withAdminListParams(path: string, params: CommunityAdminListParams = {}): string {
  const search = new URLSearchParams();
  if (params.status) {
    search.set("status", params.status);
  }
  if (params.limit !== undefined) {
    search.set("limit", String(params.limit));
  }
  if (params.offset !== undefined) {
    search.set("offset", String(params.offset));
  }
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

function withAdminUserParams(path: string, params: CommunityAdminUserListParams = {}): string {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.access_state) search.set("access_state", params.access_state);
  if (params.moderation_state) search.set("moderation_state", params.moderation_state);
  if (params.role) search.set("role", params.role);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

function withAdminNotificationParams(path: string, params: CommunityAdminNotificationListParams = {}): string {
  const search = new URLSearchParams();
  if (params.type) search.set("type", params.type);
  if (params.status) search.set("status", params.status);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

function withAdminPurchaseRequestParams(path: string, params: CommunityAdminPurchaseRequestListParams = {}): string {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.product_id) search.set("product_id", params.product_id);
  if (params.q) search.set("q", params.q);
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export async function getCommunityDashboard(): Promise<CommunityDashboardResponse> {
  const response = await apiClient.get<CommunityDashboardResponse>(communityApiPaths.dashboard);
  return response.data;
}

export async function getCommunityAdminInfo(): Promise<CommunityAdminInfo> {
  const response = await apiClient.get<CommunityAdminInfo>(communityApiPaths.adminInfo);
  return response.data;
}

export async function listCommunityAdminNotifications(
  params?: CommunityAdminNotificationListParams,
): Promise<CommunityAdminNotificationListResponse> {
  const response = await apiClient.get<CommunityAdminNotificationListResponse>(
    withAdminNotificationParams(communityApiPaths.adminNotifications, params),
  );
  return response.data;
}

export async function getCommunityAdminNotificationSenderStatus(): Promise<CommunityAdminNotificationSenderStatus> {
  const response = await apiClient.get<CommunityAdminNotificationSenderStatus>(communityApiPaths.adminNotificationsSenderStatus);
  return response.data;
}

export async function processCommunityAdminPendingNotifications(
  payload: CommunityAdminNotificationProcessPayload = {},
): Promise<CommunityAdminNotificationProcessSummary> {
  const response = await apiClient.post<CommunityAdminNotificationProcessSummary>(
    communityApiPaths.adminNotificationsProcessPending,
    payload,
  );
  return response.data;
}

export async function getCommunityPost(postId: string): Promise<CommunityPostDetail> {
  const response = await apiClient.get<CommunityPostDetail>(communityApiPaths.post(postId));
  return response.data;
}

export async function getCommunityInsight(insightId: string): Promise<CommunityInsightDetail> {
  const response = await apiClient.get<CommunityInsightDetail>(communityApiPaths.insight(insightId));
  return response.data;
}

export async function toggleCommunityPostUseful(postId: string): Promise<CommunityUsefulToggleResponse> {
  const response = await apiClient.post<CommunityUsefulToggleResponse>(communityApiPaths.postUseful(postId), {});
  return response.data;
}

export async function toggleCommunityInsightUseful(insightId: string): Promise<CommunityUsefulToggleResponse> {
  const response = await apiClient.post<CommunityUsefulToggleResponse>(communityApiPaths.insightUseful(insightId), {});
  return response.data;
}

export async function listCommunityChats(): Promise<CommunityChatLink[]> {
  const response = await apiClient.get<CommunityChatLink[]>(communityApiPaths.chats);
  return response.data;
}

export async function listCommunityExchanges(): Promise<CommunityExchange[]> {
  const response = await apiClient.get<CommunityExchange[]>(communityApiPaths.exchanges);
  return response.data;
}

export async function getCommunityProfile(): Promise<CommunityProfile> {
  const response = await apiClient.get<CommunityProfile>(communityApiPaths.profile);
  return response.data;
}

export async function getCommunitySettings(): Promise<CommunitySettings> {
  const response = await apiClient.get<CommunitySettings>(communityApiPaths.settings);
  return response.data;
}

export async function updateCommunityNotifications(notifications_enabled: boolean): Promise<CommunitySettings> {
  const response = await apiClient.patch<CommunitySettings>(communityApiPaths.notificationSettings, { notifications_enabled });
  return response.data;
}

export async function getCommunityRules(): Promise<CommunityRules> {
  const response = await apiClient.get<CommunityRules>(communityApiPaths.rules);
  return response.data;
}

export async function getCommunityPublicLinks(): Promise<CommunityPublicLinks> {
  const response = await apiClient.get<CommunityPublicLinks>(communityApiPaths.publicLinks);
  return response.data;
}

export async function listCommunityProducts(): Promise<CommunityProduct[]> {
  const response = await apiClient.get<CommunityProduct[]>(communityApiPaths.products);
  return response.data;
}

export async function getCommunityProduct(productId: string): Promise<CommunityProductDetail> {
  const response = await apiClient.get<CommunityProductDetail>(communityApiPaths.product(productId));
  return response.data;
}

export async function createCommunityProductPurchaseRequest(
  productId: string,
  payload: CommunityProductPurchaseRequestPayload,
): Promise<CommunityProductPurchaseRequestCreated> {
  const response = await apiClient.post<CommunityProductPurchaseRequestCreated>(
    communityApiPaths.productPurchaseRequest(productId),
    payload,
  );
  return response.data;
}

export async function listMyCommunityPurchaseRequests(): Promise<CommunityProductPurchaseRequest[]> {
  const response = await apiClient.get<CommunityProductPurchaseRequest[]>(communityApiPaths.myPurchaseRequests);
  return response.data;
}

export async function listCommunityAdminPurchaseRequests(
  params?: CommunityAdminPurchaseRequestListParams,
): Promise<CommunityAdminPurchaseRequestListResponse> {
  const response = await apiClient.get<CommunityAdminPurchaseRequestListResponse>(
    withAdminPurchaseRequestParams(communityApiPaths.adminPurchaseRequests, params),
  );
  return response.data;
}

export async function updateCommunityAdminPurchaseRequest(
  requestId: string,
  payload: CommunityAdminPurchaseRequestUpdatePayload,
): Promise<CommunityAdminPurchaseRequest> {
  const response = await apiClient.patch<CommunityAdminPurchaseRequest>(communityApiPaths.adminPurchaseRequest(requestId), payload);
  return response.data;
}

export async function approveAndGrantCommunityAdminPurchaseRequest(
  requestId: string,
  payload: CommunityAdminPurchaseRequestApprovePayload,
): Promise<CommunityAdminPurchaseRequest> {
  const response = await apiClient.post<CommunityAdminPurchaseRequest>(
    communityApiPaths.adminPurchaseRequestApproveGrant(requestId),
    payload,
  );
  return response.data;
}

export async function listCommunityAdminPosts(params?: CommunityAdminListParams): Promise<CommunityAdminPostListResponse> {
  const response = await apiClient.get<CommunityAdminPostListResponse>(withAdminListParams(communityApiPaths.adminPosts, params));
  return response.data;
}

export async function createCommunityAdminPost(payload: CommunityAdminPostPayload): Promise<CommunityAdminPost> {
  const response = await apiClient.post<CommunityAdminPost>(communityApiPaths.adminPosts, payload);
  return response.data;
}

export async function getCommunityAdminPost(postId: string): Promise<CommunityAdminPost> {
  const response = await apiClient.get<CommunityAdminPost>(communityApiPaths.adminPost(postId));
  return response.data;
}

export async function updateCommunityAdminPost(postId: string, payload: CommunityAdminPostPayload): Promise<CommunityAdminPost> {
  const response = await apiClient.patch<CommunityAdminPost>(communityApiPaths.adminPost(postId), payload);
  return response.data;
}

export async function hideCommunityAdminPost(postId: string): Promise<CommunityAdminPost> {
  const response = await apiClient.delete<CommunityAdminPost>(communityApiPaths.adminPost(postId));
  return response.data;
}

export async function listCommunityAdminInsights(params?: CommunityAdminListParams): Promise<CommunityAdminInsightListResponse> {
  const response = await apiClient.get<CommunityAdminInsightListResponse>(
    withAdminListParams(communityApiPaths.adminInsights, params),
  );
  return response.data;
}

export async function createCommunityAdminInsight(payload: CommunityAdminInsightPayload): Promise<CommunityAdminInsight> {
  const response = await apiClient.post<CommunityAdminInsight>(communityApiPaths.adminInsights, payload);
  return response.data;
}

export async function getCommunityAdminInsight(insightId: string): Promise<CommunityAdminInsight> {
  const response = await apiClient.get<CommunityAdminInsight>(communityApiPaths.adminInsight(insightId));
  return response.data;
}

export async function updateCommunityAdminInsight(
  insightId: string,
  payload: CommunityAdminInsightPayload,
): Promise<CommunityAdminInsight> {
  const response = await apiClient.patch<CommunityAdminInsight>(communityApiPaths.adminInsight(insightId), payload);
  return response.data;
}

export async function hideCommunityAdminInsight(insightId: string): Promise<CommunityAdminInsight> {
  const response = await apiClient.delete<CommunityAdminInsight>(communityApiPaths.adminInsight(insightId));
  return response.data;
}

export async function listCommunityAdminChats(): Promise<CommunityAdminChat[]> {
  const response = await apiClient.get<CommunityAdminChat[]>(communityApiPaths.adminChats);
  return response.data;
}

export async function createCommunityAdminChat(payload: CommunityAdminChatPayload): Promise<CommunityAdminChat> {
  const response = await apiClient.post<CommunityAdminChat>(communityApiPaths.adminChats, payload);
  return response.data;
}

export async function getCommunityAdminChat(chatId: string): Promise<CommunityAdminChat> {
  const response = await apiClient.get<CommunityAdminChat>(communityApiPaths.adminChat(chatId));
  return response.data;
}

export async function updateCommunityAdminChat(chatId: string, payload: CommunityAdminChatPayload): Promise<CommunityAdminChat> {
  const response = await apiClient.patch<CommunityAdminChat>(communityApiPaths.adminChat(chatId), payload);
  return response.data;
}

export async function hideCommunityAdminChat(chatId: string): Promise<CommunityAdminChat> {
  const response = await apiClient.delete<CommunityAdminChat>(communityApiPaths.adminChat(chatId));
  return response.data;
}

export async function listCommunityAdminExchanges(): Promise<CommunityAdminExchange[]> {
  const response = await apiClient.get<CommunityAdminExchange[]>(communityApiPaths.adminExchanges);
  return response.data;
}

export async function createCommunityAdminExchange(payload: CommunityAdminExchangePayload): Promise<CommunityAdminExchange> {
  const response = await apiClient.post<CommunityAdminExchange>(communityApiPaths.adminExchanges, payload);
  return response.data;
}

export async function getCommunityAdminExchange(exchangeId: string): Promise<CommunityAdminExchange> {
  const response = await apiClient.get<CommunityAdminExchange>(communityApiPaths.adminExchange(exchangeId));
  return response.data;
}

export async function updateCommunityAdminExchange(
  exchangeId: string,
  payload: CommunityAdminExchangePayload,
): Promise<CommunityAdminExchange> {
  const response = await apiClient.patch<CommunityAdminExchange>(communityApiPaths.adminExchange(exchangeId), payload);
  return response.data;
}

export async function hideCommunityAdminExchange(exchangeId: string): Promise<CommunityAdminExchange> {
  const response = await apiClient.delete<CommunityAdminExchange>(communityApiPaths.adminExchange(exchangeId));
  return response.data;
}

export async function listCommunityAdminProducts(): Promise<CommunityAdminProduct[]> {
  const response = await apiClient.get<CommunityAdminProduct[]>(communityApiPaths.adminProducts);
  return response.data;
}

export async function createCommunityAdminProduct(payload: CommunityAdminProductPayload): Promise<CommunityAdminProduct> {
  const response = await apiClient.post<CommunityAdminProduct>(communityApiPaths.adminProducts, payload);
  return response.data;
}

export async function updateCommunityAdminProduct(productId: string, payload: CommunityAdminProductPayload): Promise<CommunityAdminProduct> {
  const response = await apiClient.patch<CommunityAdminProduct>(communityApiPaths.adminProduct(productId), payload);
  return response.data;
}

export async function hideCommunityAdminProduct(productId: string): Promise<CommunityAdminProduct> {
  const response = await apiClient.delete<CommunityAdminProduct>(communityApiPaths.adminProduct(productId));
  return response.data;
}

export async function listCommunityAdminProductMaterials(productId: string): Promise<CommunityAdminProductMaterial[]> {
  const response = await apiClient.get<CommunityAdminProductMaterial[]>(communityApiPaths.adminProductMaterials(productId));
  return response.data;
}

export async function createCommunityAdminProductMaterial(
  productId: string,
  payload: CommunityAdminProductMaterialPayload,
): Promise<CommunityAdminProductMaterial> {
  const response = await apiClient.post<CommunityAdminProductMaterial>(communityApiPaths.adminProductMaterials(productId), payload);
  return response.data;
}

export async function updateCommunityAdminProductMaterial(
  productId: string,
  materialId: string,
  payload: CommunityAdminProductMaterialPayload,
): Promise<CommunityAdminProductMaterial> {
  const response = await apiClient.patch<CommunityAdminProductMaterial>(communityApiPaths.adminProductMaterial(productId, materialId), payload);
  return response.data;
}

export async function deleteCommunityAdminProductMaterial(productId: string, materialId: string): Promise<CommunityAdminProductMaterial> {
  const response = await apiClient.delete<CommunityAdminProductMaterial>(communityApiPaths.adminProductMaterial(productId, materialId));
  return response.data;
}

export async function listCommunityAdminUsers(params?: CommunityAdminUserListParams): Promise<CommunityAdminUserListResponse> {
  const response = await apiClient.get<CommunityAdminUserListResponse>(withAdminUserParams(communityApiPaths.adminUsers, params));
  return response.data;
}

export async function getCommunityAdminUser(projectUserId: string): Promise<CommunityAdminUserDetail> {
  const response = await apiClient.get<CommunityAdminUserDetail>(communityApiPaths.adminUser(projectUserId));
  return response.data;
}

export async function updateCommunityAdminUserProjectAccess(
  projectUserId: string,
  payload: CommunityAdminUserProjectAccessUpdatePayload,
): Promise<CommunityAdminUserDetail> {
  const response = await apiClient.patch<CommunityAdminUserDetail>(communityApiPaths.adminUserProjectAccess(projectUserId), payload);
  return response.data;
}

export async function extendCommunityAdminUserOneYear(projectUserId: string): Promise<CommunityAdminUserDetail> {
  const response = await apiClient.post<CommunityAdminUserDetail>(communityApiPaths.adminUserExtendOneYear(projectUserId), {});
  return response.data;
}

export async function banCommunityAdminUser(projectUserId: string): Promise<CommunityAdminUserDetail> {
  const response = await apiClient.post<CommunityAdminUserDetail>(communityApiPaths.adminUserBan(projectUserId), {});
  return response.data;
}

export async function unbanCommunityAdminUser(projectUserId: string): Promise<CommunityAdminUserDetail> {
  const response = await apiClient.post<CommunityAdminUserDetail>(communityApiPaths.adminUserUnban(projectUserId), {});
  return response.data;
}

export async function grantCommunityAdminProductAccess(
  payload: CommunityAdminProductAccessPayload,
): Promise<CommunityAdminProductAccess> {
  const response = await apiClient.post<CommunityAdminProductAccess>(communityApiPaths.adminProductAccess, payload);
  return response.data;
}

export async function updateCommunityAdminProductAccess(
  accessId: string,
  payload: CommunityAdminProductAccessUpdatePayload,
): Promise<CommunityAdminProductAccess> {
  const response = await apiClient.patch<CommunityAdminProductAccess>(communityApiPaths.adminProductAccessItem(accessId), payload);
  return response.data;
}
