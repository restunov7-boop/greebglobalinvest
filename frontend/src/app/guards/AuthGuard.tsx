import { PropsWithChildren, useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuthStore } from "../../modules/auth/store";
import { CommunityAuthState } from "../../modules/community/ui/CommunityState";
import { PlaceholderPage } from "../../shared/ui/PlaceholderPage";
import { useTelegram } from "../../shared/lib/telegram/useTelegram";

const devTelegramMockEnabled = import.meta.env.VITE_DEV_TELEGRAM_MOCK === "true";
const isGlobalGreenInvest = import.meta.env.VITE_PROJECT_SLUG === "global-green-invest";
const authTitle = isGlobalGreenInvest ? "GlobalGreenInvest" : "CORE";

export function AuthGuard({ children }: PropsWithChildren) {
  const telegram = useTelegram();
  const location = useLocation();
  const { accessToken, isAuthenticated, isLoading, error, login, loadMe, projectUser, setError } = useAuthStore();
  const isCommunityRoute = location.pathname.startsWith("/app") || (isGlobalGreenInvest && location.pathname.startsWith("/admin"));
  const isSystemRoute = location.pathname === "/app/locked" || location.pathname === "/app/banned";

  useEffect(() => {
    if (isAuthenticated || isLoading || error) {
      return;
    }

    if (accessToken) {
      void loadMe();
      return;
    }

    if (devTelegramMockEnabled) {
      void login(telegram.initData || "dev_mock_init_data");
      return;
    }

    if (telegram.initData) {
      void login(telegram.initData);
      return;
    }

    setError("Открой приложение через Telegram-бота. В браузере прямой вход отключён для реального пилота.");
  }, [accessToken, error, isAuthenticated, isLoading, loadMe, login, setError, telegram.initData]);

  if (error) {
    if (isCommunityRoute) {
      return (
        <CommunityAuthState
          tone="error"
          title="Не удалось подключить закрытую панель"
          description={error}
        />
      );
    }
    return <PlaceholderPage eyebrow={authTitle} title="Ошибка входа" description={error} />;
  }

  if (!isAuthenticated) {
    if (isCommunityRoute) {
      return (
        <CommunityAuthState
          title="Подключаем закрытую панель сообщества"
          description="Проверяем Telegram-доступ и синхронизируем профиль участника."
        />
      );
    }
    return <PlaceholderPage eyebrow={authTitle} title="Входим в приложение" description="Проверяем Telegram-доступ и профиль участника." />;
  }

  if (isCommunityRoute && projectUser?.project_slug === "global-green-invest" && !isSystemRoute) {
    if (projectUser.moderation_state === "banned") {
      return <Navigate to="/app/banned" replace />;
    }
    if (projectUser.status !== "active" || projectUser.access_state !== "active") {
      return <Navigate to="/app/locked" replace />;
    }
  }

  return <>{children}</>;
}
