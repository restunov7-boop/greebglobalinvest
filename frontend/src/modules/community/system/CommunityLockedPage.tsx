import { useEffect, useState } from "react";

import { getCommunityPublicLinks } from "../api";
import { GGI_BRAND_NAME } from "../labels";
import type { CommunityPublicLinks } from "../types";

export function CommunityLockedPage() {
  const [links, setLinks] = useState<CommunityPublicLinks | null>(null);

  useEffect(() => {
    getCommunityPublicLinks().then(setLinks).catch(() => setLinks(null));
  }, []);

  return (
    <section className="community-placeholder">
      <div className="community-placeholder__eyebrow">{GGI_BRAND_NAME}</div>
      <h1>Доступ к панели пока не активирован</h1>
      <p>Если подписка уже оплачена, напиши в поддержку — мы проверим доступ вручную.</p>
      {links?.support_url && (
        <a className="community-admin-button community-admin-button--primary" href={links.support_url} target="_blank" rel="noreferrer">
          Написать в поддержку
        </a>
      )}
    </section>
  );
}
