import { Link } from "react-router-dom";

import { GGI_BRAND_NAME } from "../labels";

export function CommunityAdminNoAccessPage() {
  return (
    <section className="community-admin-state community-admin-state--denied" role="alert">
      <span>{GGI_BRAND_NAME}</span>
      <h1>Нет доступа к админ-панели</h1>
      <p>Этот раздел доступен только администраторам проекта GlobalGreenInvest.</p>
      <Link className="community-admin-button community-admin-button--primary" to="/app">
        Вернуться в приложение
      </Link>
    </section>
  );
}
