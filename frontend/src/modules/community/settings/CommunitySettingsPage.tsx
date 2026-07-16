import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import { getCommunitySettings, updateCommunityNotifications } from "../api";
import type { CommunitySettings } from "../types";

export function CommunitySettingsPage() {
  const [settings, setSettings] = useState<CommunitySettings | null>(null);
  const [error, setError] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    getCommunitySettings()
      .then(setSettings)
      .catch(() => setError(true));
  }, []);

  const toggleNotifications = async () => {
    if (!settings || isSaving) return;
    const previous = settings;
    const nextValue = !settings.notifications_enabled;
    setSettings({ ...settings, notifications_enabled: nextValue });
    setIsSaving(true);
    setSaveError(null);
    try {
      setSettings(await updateCommunityNotifications(nextValue));
    } catch {
      setSettings(previous);
      setSaveError("Не удалось обновить настройки уведомлений.");
    } finally {
      setIsSaving(false);
    }
  };

  if (error) return <ErrorState title="Настройки недоступны" description="Не удалось получить настройки проекта." />;
  if (!settings) return <LoadingState title="Загружаем настройки" />;

  return (
    <section className="community-simple-page">
      <header className="community-simple-page__header">
        <div>
          <span>GlobalGreenInvest</span>
          <h1>Настройки</h1>
          {settings.about_content && <p>{settings.about_content}</p>}
        </div>
      </header>
      <div className="community-simple-grid">
        <div className="community-simple-card">
          <span>Notifications</span>
          <strong>Срочные инсайды</strong>
          <label className="community-admin-checkbox">
            <input type="checkbox" checked={settings.notifications_enabled} onChange={() => void toggleNotifications()} disabled={isSaving} />
            Уведомления включены
          </label>
          {saveError && <p className="community-admin-inline-error">{saveError}</p>}
        </div>
        <div className="community-simple-card">
          <span>Telegram-бот</span>
          <strong>Нажмите Start в боте, чтобы получать срочные инсайды.</strong>
          {settings.telegram_bot_url && <a href={settings.telegram_bot_url} target="_blank" rel="noreferrer">Открыть бота</a>}
        </div>
        <div className="community-simple-card">
          <span>Links</span>
          {settings.support_url && <a href={settings.support_url} target="_blank" rel="noreferrer">Поддержка</a>}
          {settings.website_url && <a href={settings.website_url} target="_blank" rel="noreferrer">Сайт</a>}
          {settings.blogger_telegram_url && <a href={settings.blogger_telegram_url} target="_blank" rel="noreferrer">Telegram блогера</a>}
          <Link to="/app/rules">Правила и дисклеймер</Link>
        </div>
      </div>
    </section>
  );
}
