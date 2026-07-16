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

export function CommunitySidebar({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  return (
    <aside className={isOpen ? "community-sidebar is-open" : "community-sidebar"} aria-hidden={!isOpen}>
      <div className="community-sidebar__top">
        <NavLink className="community-sidebar__brand" to="/app" end onClick={onClose} tabIndex={isOpen ? undefined : -1}>
          <strong>{GGI_BRAND_NAME}</strong>
          <span>GlobalGreenInvest</span>
        </NavLink>
        <button className="community-sidebar__close" type="button" aria-label="Закрыть меню" onClick={onClose} tabIndex={isOpen ? undefined : -1}>
          ×
        </button>
      </div>
      <nav className="community-sidebar__nav" aria-label="Навигация сообщества">
        {navItems.map((item) => (
          <NavLink key={item.to} to={item.to} end={item.end} onClick={onClose} tabIndex={isOpen ? undefined : -1}>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
