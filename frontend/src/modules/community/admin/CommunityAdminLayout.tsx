import { NavLink, Outlet } from "react-router-dom";

import { GGI_BRAND_NAME } from "../labels";

const adminNavItems = [
  { to: "/app", label: "В приложение" },
  { to: "/admin/posts", label: "Посты" },
  { to: "/admin/insights", label: "Инсайды" },
  { to: "/admin/chats", label: "Чаты" },
  { to: "/admin/exchanges", label: "Биржи" },
  { to: "/admin/products", label: "Продукты" },
  { to: "/admin/requests", label: "Заявки" },
  { to: "/admin/users", label: "Пользователи" },
  { to: "/admin/settings", label: "Настройки" },
];

export function CommunityAdminLayout() {
  return (
    <div className="community-admin-shell">
      <aside className="community-admin-sidebar">
        <div className="community-admin-sidebar__brand">
          <strong>{GGI_BRAND_NAME}</strong>
          <span>Админ-панель</span>
        </div>
        <nav className="community-admin-sidebar__nav" aria-label="Админ-навигация GlobalGreenInvest">
          {adminNavItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/app"}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <section className="community-admin-shell__body">
        <header className="community-admin-topbar">
          <span>GlobalGreenInvest</span>
          <strong>Операционная панель проекта</strong>
        </header>
        <main className="community-admin-shell__main">
          <Outlet />
        </main>
      </section>
    </div>
  );
}
