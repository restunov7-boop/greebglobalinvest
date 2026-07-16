import { PropsWithChildren, useEffect } from "react";

import { useAuthStore } from "../../modules/auth/store";
import { PlaceholderPage } from "../../shared/ui/PlaceholderPage";
import { useTelegram } from "../../shared/lib/telegram/useTelegram";

const devTelegramMockEnabled = import.meta.env.VITE_DEV_TELEGRAM_MOCK === "true";
const isGlobalGreenInvest = import.meta.env.VITE_PROJECT_SLUG === "global-green-invest";
const authTitle = isGlobalGreenInvest ? "GlobalGreenInvest" : "CORE";

export function AuthGuard({ children }: PropsWithChildren) {
  const telegram = useTelegram();
  const { accessToken, isAuthenticated, isLoading, error, login, loadMe, setError } = useAuthStore();

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

    setError("Не удалось получить данные Telegram. Откройте приложение внутри Telegram или включите dev mock.");
  }, [accessToken, error, isAuthenticated, isLoading, loadMe, login, setError, telegram.initData]);

  if (error) {
    return <PlaceholderPage eyebrow={authTitle} title="Ошибка входа" description={error} />;
  }

  if (!isAuthenticated) {
    return <PlaceholderPage eyebrow={authTitle} title="Входим в приложение" description="Проверяем Telegram-доступ и профиль участника." />;
  }

  return <>{children}</>;
}
