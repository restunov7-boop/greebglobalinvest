import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import { getCommunityPost, toggleCommunityPostUseful } from "../api";
import type { CommunityPostDetail } from "../types";

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

export function CommunityPostPage() {
  const { postId } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState<CommunityPostDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [isTogglingUseful, setIsTogglingUseful] = useState(false);
  const [toggleError, setToggleError] = useState<string | null>(null);

  useEffect(() => {
    if (!postId) {
      setNotFound(true);
      setIsLoading(false);
      return;
    }

    let isMounted = true;

    getCommunityPost(postId)
      .then((payload) => {
        if (!isMounted) {
          return;
        }
        setPost(payload);
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

        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить материал.");
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [navigate, postId]);

  const handleToggleUseful = async () => {
    if (!postId || isTogglingUseful) {
      return;
    }

    setIsTogglingUseful(true);
    setToggleError(null);

    try {
      const payload = await toggleCommunityPostUseful(postId);
      setPost((current) =>
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
    return <LoadingState title="Загружаем материал" description="Проверяем доступ и получаем опубликованный пост." />;
  }

  if (notFound) {
    return (
      <EmptyState
        title="Материал недоступен"
        description="Пост не найден, скрыт или ещё не опубликован."
        action={
          <Link className="ghost-action" to="/app">
            Вернуться на главную
          </Link>
        }
      />
    );
  }

  if (error || !post) {
    return (
      <ErrorState
        title="Пост недоступен"
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
          <span>GlobalGreenInvest</span>
          {post.published_at && <span>{formatDetailDate(post.published_at)}</span>}
          {post.is_new && <span>NEW</span>}
        </div>
        <h1>{post.title}</h1>
        {post.excerpt && <p>{post.excerpt}</p>}
      </header>

      {post.cover_url && <img className="community-detail__cover" src={post.cover_url} alt="" />}

      <div className="community-detail__body">{post.content}</div>

      <footer className="community-detail__footer">
        <div className="community-detail__stats">
          <span>Просмотры {post.view_count}</span>
          <span>Полезно {post.useful_count}</span>
        </div>
        <button
          className={post.is_useful_by_me ? "community-useful-button community-useful-button--active" : "community-useful-button"}
          type="button"
          onClick={handleToggleUseful}
          disabled={isTogglingUseful}
        >
          Полезно <span>{post.useful_count}</span>
        </button>
      </footer>

      {toggleError && <p className="community-detail__inline-error">{toggleError}</p>}
    </article>
  );
}
