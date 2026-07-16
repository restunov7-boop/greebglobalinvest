import { apiClient } from "../../shared/api/client";

import type { AuthSession, MeResponse } from "./types";

const projectSlug = import.meta.env.VITE_PROJECT_SLUG?.trim() || undefined;

export async function loginWithTelegram(initData: string): Promise<AuthSession> {
  const response = await apiClient.post<AuthSession>("/auth/telegram", { init_data: initData, project_slug: projectSlug });
  return response.data;
}

export async function getMe(): Promise<MeResponse> {
  const response = await apiClient.get<MeResponse>("/auth/me");
  return response.data;
}
