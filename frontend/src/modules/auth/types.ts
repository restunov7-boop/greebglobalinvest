export type AuthUser = {
  id: string;
  display_name: string | null;
  avatar_url: string | null;
};

export type ProjectUser = {
  project_slug: string;
  role: "member" | "moderator" | "admin" | "owner";
  status: "active" | "blocked" | "left";
  is_premium: boolean;
  premium_until: string | null;
  access_state: "pending" | "active" | "expired" | "revoked";
  access_until: string | null;
  moderation_state: "normal" | "banned";
  capabilities: string[];
};

export type AuthSession = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
  project_user: ProjectUser;
};

export type MeResponse = {
  user: AuthUser;
  project_user: ProjectUser;
};
