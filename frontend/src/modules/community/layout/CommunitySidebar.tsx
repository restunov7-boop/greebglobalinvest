import { NavLink } from "react-router-dom";

import { GGI_BRAND_NAME } from "../labels";

const navItems = [
  { to: "/app", label: "Главная", end: true },
  { to: "/app/products", label: "Продукты" },
  { to: "/app/exchanges", label: "Биржи" },
  { to: "/app/profile", label: "Профиль" },
  { to: "/app/settings", label: "Настройки" },
  { to: "/app/rules", label: "Правила" },
];

export function CommunitySidebar() {
  return (
    <aside className="community-sidebar">
      <NavLink className="community-sidebar__brand" to="/app" end>
        <strong>{GGI_BRAND_NAME}</strong>
        <span>GlobalGreenInvest</span>
      </NavLink>
      <nav className="community-sidebar__nav" aria-label="Навигация сообщества">
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end}>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
