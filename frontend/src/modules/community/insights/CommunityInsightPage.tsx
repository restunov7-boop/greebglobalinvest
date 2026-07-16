import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import { getCommunityInsight, toggleCommunityInsightUseful } from "../api";
import type { CommunityInsightDetail } from "../types";

function formatDetailDate(value: string | null): string {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(value));
}

export function CommunityInsightPage() {
  const { insightId } = useParams();
  const navigate = useNavigate();
  const [insight, setInsight] = useState<CommunityInsightDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [isTogglingUseful, setIsTogglingUseful] = useState(false);
  const [toggleError, setToggleError] = useState<string | null>(null);

  useEffect(() => {
    if (!insightId) {
      setNotFound(true);
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    getCommunityInsight(insightId)
      .then((payload) => {
        if (!isMounted) {
          return;
        }
        setInsight(payload);
        setError(null);
        setNotFound(false);
      })
      .catch((requestError) => {
        if (!isMounted) {
          return;
        }

        if (requestError instanceof ApiError && requestError.status === 403) {
          const message = requestError.message.toLowerCase();
          navigate(message.includes("restricted") ? "/app/banned" : "/app/locked", { replace: true });
          return;
        }

        if (requestError instanceof ApiError && requestError.status === 404) {
          setNotFound(true);
          return;
        }

        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить инсайт.");
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [insightId, navigate]);

  const handleToggleUseful = async () => {
    if (!insightId || isTogglingUseful) {
      return;
    }

    setIsTogglingUseful(true);
    setToggleError(null);

    try {
      const payload = await toggleCommunityInsightUseful(insightId);
      setInsight((current) =>
        current
          ? {
              ...current,
              useful_count: payload.useful_count,
              is_useful_by_me: payload.is_useful_by_me,
            }
          : current,
      );
    } catch {
      setToggleError("Не удалось обновить отметку. Попробуйте позже.");
    } finally {
      setIsTogglingUseful(false);
    }
  };

  if (isLoading) {
    return <LoadingState title="Загружаем инсайт" description="Проверяем доступ и получаем опубликованный материал." />;
  }

  if (notFound) {
    return (
      <EmptyState
        title="Материал недоступен"
        description="Инсайт не найден, скрыт или ещё не опубликован."
        action={
          <Link className="ghost-action" to="/app">
            Вернуться на главную
          </Link>
        }
      />
    );
  }

  if (error || !insight) {
    return (
      <ErrorState
        title="Инсайт недоступен"
        description="Не удалось получить материал. Проверьте подключение или попробуйте позже."
      />
    );
  }

  return (
    <article className="community-detail">
      <Link className="community-detail__back" to="/app">
        Назад на главную
      </Link>

      <header className="community-detail__header">
        <div className="community-detail__meta">
          {insight.is_urgent && <span className="community-detail__badge community-detail__badge--urgent">Срочно</span>}
          <span>GlobalGreenInvest</span>
          {insight.published_at && <span>{formatDetailDate(insight.published_at)}</span>}
          {insight.is_new && <span>NEW</span>}
        </div>
        <h1>{insight.title}</h1>
        {insight.excerpt && <p>{insight.excerpt}</p>}
      </header>

      <div className="community-detail__body">{insight.content}</div>

      <footer className="community-detail__footer">
        <div className="community-detail__stats">
          <span>Просмотры {insight.view_count}</span>
          <span>Полезно {insight.useful_count}</span>
        </div>
        <button
          className={insight.is_useful_by_me ? "community-useful-button community-useful-button--active" : "community-useful-button"}
          type="button"
          onClick={handleToggleUseful}
          disabled={isTogglingUseful}
        >
          Полезно <span>{insight.useful_count}</span>
        </button>
      </footer>

      {toggleError && <p className="community-detail__inline-error">{toggleError}</p>}
    </article>
  );
}
