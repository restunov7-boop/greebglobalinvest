import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import { getCommunityDashboard } from "../api";
import { FloatingChatsDock } from "../FloatingChatsDock";
import type {
  CommunityDashboardContentItem,
  CommunityDashboardInsightItem,
  CommunityDashboardNotification,
  CommunityDashboardResponse,
} from "../types";

function formatDate(value: string | null): string {
  if (!value) {
    return "";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
  }).format(new Date(value));
}

function usefulLabel(item: CommunityDashboardContentItem): string {
  return item.is_useful_by_me ? `Полезно · ${item.useful_count}` : `Полезно ${item.useful_count}`;
}

function hasDashboardContent(data: CommunityDashboardResponse): boolean {
  return Boolean(
    data.important_notifications.length ||
      data.pinned_post ||
      data.posts.length ||
      data.insights.length ||
      data.chat_links.length,
  );
}

export function CommunityDashboardPage() {
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<CommunityDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    getCommunityDashboard()
      .then((payload) => {
        if (!isMounted) {
          return;
        }
        setDashboard(payload);
        setError(null);
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

        setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить главную.");
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [navigate]);

  const isEmpty = useMemo(() => dashboard !== null && !hasDashboardContent(dashboard), [dashboard]);

  if (isLoading) {
    return <LoadingState title="Загружаем главную" description="Собираем новости, инсайды и актуальные чаты." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Главная недоступна"
        description="Не удалось получить данные. Проверьте подключение или попробуйте позже."
      />
    );
  }

  if (!dashboard || isEmpty) {
    return (
      <EmptyState
        title="Главная пока пустая"
        description="Здесь появятся новости, инсайды и актуальные чаты после публикации материалов."
      />
    );
  }

  return (
    <section className={dashboard.chat_links.length > 0 ? "community-dashboard community-dashboard--with-floating-chats" : "community-dashboard"}>
      <FloatingChatsDock chats={dashboard.chat_links} />

      {dashboard.important_notifications.length > 0 && (
        <DashboardPanel title="Важное" tone="important">
          <div className="community-dashboard__stack">
            {dashboard.important_notifications.map((item) => (
              <NotificationCard key={item.id} item={item} />
            ))}
          </div>
        </DashboardPanel>
      )}

      {dashboard.pinned_post && (
        <DashboardPanel title="Закреплено">
          <ContentCard item={dashboard.pinned_post} to={`/app/posts/${dashboard.pinned_post.id}`} featured />
        </DashboardPanel>
      )}

      <div className="community-dashboard__columns">
        <DashboardPanel title="Новости и посты">
          {dashboard.posts.length > 0 ? (
            <div className="community-dashboard__stack">
              {dashboard.posts.map((item) => (
                <ContentCard key={item.id} item={item} to={`/app/posts/${item.id}`} />
              ))}
            </div>
          ) : (
            <p className="community-dashboard__muted">Пока нет опубликованных постов.</p>
          )}
        </DashboardPanel>

        <DashboardPanel title="Инсайды">
          {dashboard.insights.length > 0 ? (
            <div className="community-dashboard__stack">
              {dashboard.insights.map((item) => (
                <InsightCard key={item.id} item={item} />
              ))}
            </div>
          ) : (
            <p className="community-dashboard__muted">Пока нет опубликованных инсайдов.</p>
          )}
        </DashboardPanel>
      </div>
    </section>
  );
}

function DashboardPanel({
  title,
  tone,
  children,
}: {
  title: string;
  tone?: "important";
  children: ReactNode;
}) {
  return (
    <section className={tone === "important" ? "community-dashboard-panel community-dashboard-panel--important" : "community-dashboard-panel"}>
      <header className="community-dashboard-panel__header">
        <span>GlobalGreenInvest</span>
        <h2>{title}</h2>
      </header>
      {children}
    </section>
  );
}

function NotificationCard({ item }: { item: CommunityDashboardNotification }) {
  return (
    <article className="community-dashboard-card community-dashboard-card--notice">
      <div className="community-dashboard-card__meta">
        <span>{item.type}</span>
        <span>{formatDate(item.created_at)}</span>
      </div>
      <h3>{item.title}</h3>
      <p>{item.body}</p>
    </article>
  );
}

function ContentCard({
  item,
  to,
  featured = false,
}: {
  item: CommunityDashboardContentItem;
  to: string;
  featured?: boolean;
}) {
  return (
    <Link className={featured ? "community-dashboard-card community-dashboard-card--featured" : "community-dashboard-card"} to={to}>
      <div className="community-dashboard-card__meta">
        {item.is_new && <span className="community-dashboard-badge">NEW</span>}
        {item.published_at && <span>{formatDate(item.published_at)}</span>}
      </div>
      <h3>{item.title}</h3>
      <p>{item.excerpt}</p>
      <div className="community-dashboard-card__footer">
        <span>{usefulLabel(item)}</span>
      </div>
    </Link>
  );
}

function InsightCard({ item }: { item: CommunityDashboardInsightItem }) {
  return (
    <Link className="community-dashboard-card" to={`/app/insights/${item.id}`}>
      <div className="community-dashboard-card__meta">
        {item.is_urgent && <span className="community-dashboard-badge community-dashboard-badge--urgent">Срочно</span>}
        {item.is_new && <span className="community-dashboard-badge">NEW</span>}
        {item.published_at && <span>{formatDate(item.published_at)}</span>}
      </div>
      <h3>{item.title}</h3>
      <p>{item.excerpt}</p>
      <div className="community-dashboard-card__footer">
        <span>{usefulLabel(item)}</span>
      </div>
    </Link>
  );
}
