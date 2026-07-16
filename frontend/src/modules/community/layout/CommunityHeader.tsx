import { GGI_BRAND_NAME } from "../labels";

export function CommunityHeader() {
  return (
    <header className="community-header">
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
