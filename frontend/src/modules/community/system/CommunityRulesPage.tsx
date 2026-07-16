import { useEffect, useState } from "react";

import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import { getCommunityRules } from "../api";
import type { CommunityRules } from "../types";

export function CommunityRulesPage() {
  const [rules, setRules] = useState<CommunityRules | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getCommunityRules()
      .then(setRules)
      .catch(() => setError(true));
  }, []);

  if (error) return <ErrorState title="Правила недоступны" description="Не удалось получить правила проекта." />;
  if (!rules) return <LoadingState title="Загружаем правила" />;

  return (
    <section className="community-simple-page">
      <header className="community-simple-page__header">
        <div>
          <span>GlobalGreenInvest</span>
          <h1>{rules.title}</h1>
        </div>
      </header>
      <article className="community-detail__body">{rules.content}</article>
      <article className="community-simple-card">
        <span>Disclaimer</span>
        <p>{rules.disclaimer}</p>
        {rules.support_url && <a href={rules.support_url} target="_blank" rel="noreferrer">Поддержка</a>}
      </article>
    </section>
  );
}
