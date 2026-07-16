import { useEffect, useState } from "react";

import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import { getCommunityProfile } from "../api";
import type { CommunityProfile } from "../types";

function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "long", year: "numeric" }).format(new Date(value)) : "Без срока";
}

export function CommunityProfilePage() {
  const [profile, setProfile] = useState<CommunityProfile | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getCommunityProfile()
      .then(setProfile)
      .catch(() => setError(true));
  }, []);

  if (error) {
    return <ErrorState title="Профиль недоступен" description="Не удалось получить профиль участника." />;
  }
  if (!profile) {
    return <LoadingState title="Загружаем профиль" />;
  }

  return (
    <section className="community-simple-page">
      <header className="community-simple-page__header">
        {profile.telegram_avatar_url && <img src={profile.telegram_avatar_url} alt="" />}
        <div>
          <span>GlobalGreenInvest</span>
          <h1>{profile.telegram_first_name ?? "Участник"}</h1>
          {profile.telegram_username && <p>@{profile.telegram_username}</p>}
        </div>
      </header>
      <div className="community-simple-grid">
        <div className="community-simple-card">
          <span>Access</span>
          <strong>{profile.access_state}</strong>
          <p>Действует до: {formatDate(profile.access_until)}</p>
        </div>
        <div className="community-simple-card">
          <span>Status</span>
          <strong>{profile.moderation_state}</strong>
          {profile.support_url && <a href={profile.support_url} target="_blank" rel="noreferrer">Написать в поддержку</a>}
        </div>
      </div>
    </section>
  );
}
