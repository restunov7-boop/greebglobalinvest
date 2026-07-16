import { useEffect, useState } from "react";

import { getCommunityPublicLinks } from "../api";
import type { CommunityPublicLinks } from "../types";

export function CommunityLockedPage() {
  const [links, setLinks] = useState<CommunityPublicLinks | null>(null);

  useEffect(() => {
    getCommunityPublicLinks().then(setLinks).catch(() => setLinks(null));
  }, []);

  return (
    <section className="community-placeholder">
      <div className="community-placeholder__eyebrow">GlobalGreenInvest</div>
      <h1>Доступ не активен</h1>
      <p>Для входа в закрытое приложение необходимо активировать подписку. Если вы уже оплатили доступ — напишите в поддержку.</p>
      {links?.support_url && (
        <a className="community-admin-button community-admin-button--primary" href={links.support_url} target="_blank" rel="noreferrer">
          Написать в поддержку
        </a>
      )}
    </section>
  );
}
