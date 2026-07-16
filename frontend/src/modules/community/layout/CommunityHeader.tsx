import { GGI_BRAND_NAME } from "../labels";

export function CommunityHeader({ onMenuOpen }: { onMenuOpen: () => void }) {
  return (
    <header className="community-header">
      <button className="community-header__menu-button" type="button" aria-label="Открыть меню" onClick={onMenuOpen}>
        <span />
        <span />
        <span />
      </button>
      <div className="community-header__title">
        <span>Закрытая панель</span>
        <strong>{GGI_BRAND_NAME}</strong>
      </div>
      <div className="community-header__bell" aria-label="Уведомления" title="Уведомления">
        ◦
      </div>
    </header>
  );
}
