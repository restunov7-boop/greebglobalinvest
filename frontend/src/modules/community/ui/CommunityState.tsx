import type { ReactNode } from "react";

import { GLOBAL_GREEN_INVEST_PROJECT_SLUG } from "../types";

type StateProps = {
  title: string;
  description?: string;
  action?: ReactNode;
};

type AuthStateProps = {
  title: string;
  description: string;
  tone?: "loading" | "error";
};

export function CommunityAuthState({ title, description, tone = "loading" }: AuthStateProps) {
  return (
    <section className={`community-auth-state community-auth-state--${tone}`} role={tone === "error" ? "alert" : "status"} aria-live="polite">
      <div className="community-auth-state__panel">
        <div className="community-auth-state__brand">
          <span>🍀 ЗЕЛЁНЫЙ / TG Investor</span>
          <strong>{title}</strong>
        </div>
        <p>{description}</p>
        <div className="community-auth-state__accent" aria-hidden="true" />
        <small>project: {GLOBAL_GREEN_INVEST_PROJECT_SLUG}</small>
      </div>
    </section>
  );
}

export function LoadingState({ title, description = "Синхронизируем данные закрытой панели." }: StateProps) {
  return (
    <section className="community-state-card" role="status" aria-live="polite">
      <span>GlobalGreenInvest</span>
      <h1>{title}</h1>
      <p>{description}</p>
      <div className="community-state-card__bar" aria-hidden="true" />
    </section>
  );
}

export function ErrorState({ title = "Раздел временно недоступен", description, action }: StateProps) {
  return (
    <section className="community-state-card community-state-card--error" role="alert">
      <span>GlobalGreenInvest</span>
      <h1>{title}</h1>
      <p>{description}</p>
      {action ?? (
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => window.location.reload()}>
          Повторить
        </button>
      )}
    </section>
  );
}

export function EmptyState({ title, description, action }: StateProps) {
  return (
    <section className="community-state-card community-state-card--empty">
      <span>GlobalGreenInvest</span>
      <h1>{title}</h1>
      <p>{description}</p>
      {action && <div>{action}</div>}
    </section>
  );
}
