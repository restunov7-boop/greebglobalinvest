import { useEffect, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import { listCommunityExchanges } from "../api";
import type { CommunityExchange } from "../types";

export function CommunityExchangesPage() {
  const [exchanges, setExchanges] = useState<CommunityExchange[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);

  useEffect(() => {
    let isMounted = true;

    listCommunityExchanges()
      .then((payload) => {
        if (!isMounted) {
          return;
        }
        setExchanges(payload);
        setError(null);
        setAccessDenied(false);
      })
      .catch((requestError) => {
        if (!isMounted) {
          return;
        }
        if (requestError instanceof ApiError && requestError.status === 403) {
          setAccessDenied(true);
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить биржи.");
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  if (isLoading) {
    return <LoadingState title="Загружаем биржи" description="Получаем опубликованные ссылки проекта." />;
  }

  if (accessDenied) {
    return <EmptyState title="Доступ ограничен" description="Backend не подтвердил активный доступ к сообществу." />;
  }

  if (error) {
    return <ErrorState title="Биржи недоступны" description="Не удалось получить список бирж. Попробуйте позже." />;
  }

  if (exchanges.length === 0) {
    return <EmptyState title="Биржи пока не опубликованы" description="Здесь появятся проверенные внешние площадки проекта." />;
  }

  return (
    <section className="community-exchanges">
      <header className="community-exchanges__header">
        <span>GlobalGreenInvest</span>
        <h1>Биржи и внешние площадки</h1>
      </header>
      <div className="community-exchange-grid">
        {exchanges.map((exchange) => (
          <article className="community-exchange-card" key={exchange.id}>
            {exchange.logo_url && <img src={exchange.logo_url} alt="" />}
            <div className="community-exchange-card__body">
              <h2>{exchange.title}</h2>
              <p>{exchange.description}</p>
              {exchange.team_comment && <p className="community-exchange-card__note">{exchange.team_comment}</p>}
              {exchange.promo_code && <div className="community-exchange-card__promo">Промокод: {exchange.promo_code}</div>}
            </div>
            <a className="community-admin-button community-admin-button--primary" href={exchange.external_url} target="_blank" rel="noreferrer">
              Перейти →
            </a>
          </article>
        ))}
      </div>
    </section>
  );
}
