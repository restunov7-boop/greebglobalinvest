import { useEffect, useMemo, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import {
  createCommunityAdminInsight,
  getCommunityAdminInsight,
  hideCommunityAdminInsight,
  listCommunityAdminInsights,
  updateCommunityAdminInsight,
} from "../api";
import { contentStatusLabel } from "../labels";
import type {
  CommunityAdminContentStatus,
  CommunityAdminInsight,
  CommunityAdminInsightListItem,
  CommunityAdminInsightPayload,
  CommunityAdminStatusFilter,
} from "../types";

type InsightFormState = {
  id: string | null;
  title: string;
  excerpt: string;
  content: string;
  is_urgent: boolean;
  status: CommunityAdminContentStatus;
  scheduled_at: string;
  published_at: string;
};

const statusFilters: Array<{ value: CommunityAdminStatusFilter; label: string }> = [
  { value: "all", label: "Все" },
  { value: "draft", label: "Черновики" },
  { value: "scheduled", label: "Запланированные" },
  { value: "published", label: "Опубликованные" },
  { value: "hidden", label: "Скрытые" },
];

const emptyForm: InsightFormState = {
  id: null,
  title: "",
  excerpt: "",
  content: "",
  is_urgent: false,
  status: "draft",
  scheduled_at: "",
  published_at: "",
};

function toDateTimeInput(value: string | null): string {
  if (!value) {
    return "";
  }
  return value.slice(0, 16);
}

function toApiDate(value: string): string | null {
  return value ? new Date(value).toISOString() : null;
}

function formatAdminDate(value: string | null): string {
  if (!value) {
    return "Дата не задана";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formFromInsight(insight: CommunityAdminInsight): InsightFormState {
  return {
    id: insight.id,
    title: insight.title,
    excerpt: insight.excerpt,
    content: insight.content,
    is_urgent: insight.is_urgent,
    status: insight.status,
    scheduled_at: toDateTimeInput(insight.scheduled_at),
    published_at: toDateTimeInput(insight.published_at),
  };
}

function payloadFromForm(form: InsightFormState): CommunityAdminInsightPayload {
  return {
    title: form.title.trim(),
    excerpt: form.excerpt.trim(),
    content: form.content.trim(),
    is_urgent: form.is_urgent,
    status: form.status,
    scheduled_at: toApiDate(form.scheduled_at),
    published_at: toApiDate(form.published_at),
  };
}

function validateInsightForm(form: InsightFormState): string | null {
  if (!form.title.trim()) {
    return "Укажите заголовок.";
  }
  if (!form.excerpt.trim()) {
    return "Укажите краткое описание.";
  }
  if (!form.content.trim()) {
    return "Заполните текст инсайда.";
  }
  if (form.status === "scheduled" && !form.scheduled_at) {
    return "Для запланированного инсайда укажите дату публикации.";
  }
  return null;
}

export function CommunityAdminInsightsPage() {
  const [filter, setFilter] = useState<CommunityAdminStatusFilter>("all");
  const [items, setItems] = useState<CommunityAdminInsightListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isEditingLoading, setIsEditingLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);
  const [form, setForm] = useState<InsightFormState>(emptyForm);

  const isEditing = form.id !== null;
  const showUrgentPublishNotice = form.is_urgent && form.status === "published";

  const loadInsights = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await listCommunityAdminInsights({ status: filter });
      setItems(payload.items);
      setTotal(payload.total);
      setAccessDenied(false);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить инсайты.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadInsights();
  }, [filter]);

  const summary = useMemo(() => `${total} материалов`, [total]);

  const handleCreate = () => {
    setForm(emptyForm);
    setFormError(null);
    setSaveNotice(null);
  };

  const handleEdit = async (insightId: string) => {
    setIsEditingLoading(true);
    setFormError(null);
    try {
      const insight = await getCommunityAdminInsight(insightId);
      setForm(formFromInsight(insight));
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось открыть инсайт.");
    } finally {
      setIsEditingLoading(false);
    }
  };

  const handleSubmit = async () => {
    const validationError = validateInsightForm(form);
    if (validationError) {
      setFormError(validationError);
      return;
    }
    setIsSaving(true);
    setFormError(null);
    setSaveNotice(null);
    try {
      const payload = payloadFromForm(form);
      let savedInsight: CommunityAdminInsight;
      if (form.id) {
        savedInsight = await updateCommunityAdminInsight(form.id, payload);
      } else {
        savedInsight = await createCommunityAdminInsight(payload);
      }
      const notificationSummary = savedInsight.urgent_notification_summary;
      if (notificationSummary) {
        setSaveNotice(
          `Подготовлено уведомлений: ${notificationSummary.notifications_created}. Уже существовали: ${notificationSummary.skipped_existing}. Telegram-отправка пока отключена.`,
        );
      }
      setForm(emptyForm);
      await loadInsights();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось сохранить инсайт.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleHide = async (insightId: string) => {
    setFormError(null);
    try {
      await hideCommunityAdminInsight(insightId);
      await loadInsights();
      if (form.id === insightId) {
        setForm(emptyForm);
      }
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось скрыть инсайт.");
    }
  };

  if (isLoading) {
    return <LoadingState title="Загружаем инсайты" description="Получаем админский список материалов проекта." />;
  }

  if (accessDenied) {
    return <EmptyState title="Нет доступа к админ-разделу" description="Backend не подтвердил права администратора для этой операции." />;
  }

  if (error) {
    return <ErrorState title="Инсайты недоступны" description="Не удалось получить админский список инсайтов." />;
  }

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>Админ-панель GlobalGreenInvest</span>
          <h1>Инсайты</h1>
          <p>{summary}</p>
        </div>
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={handleCreate}>
          Создать инсайт
        </button>
      </header>

      <div className="community-admin-filters" aria-label="Фильтр статуса">
        {statusFilters.map((item) => (
          <button
            key={item.value}
            className={filter === item.value ? "community-admin-filter community-admin-filter--active" : "community-admin-filter"}
            type="button"
            onClick={() => setFilter(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {formError && <p className="community-admin-inline-error">{formError}</p>}
      {saveNotice && <p className="community-admin-notice">{saveNotice}</p>}

      <div className="community-admin-grid">
        <div className="community-admin-list">
          {items.length === 0 ? (
            <EmptyState title="Инсайтов нет" description="Для выбранного статуса материалы не найдены." />
          ) : (
            items.map((item) => (
              <article className="community-admin-card" key={item.id}>
                <div className="community-admin-card__meta">
                  <span>{contentStatusLabel(item.status)}</span>
                  {item.is_urgent && <span>Срочный</span>}
                </div>
                <h2>{item.title}</h2>
                <p>{item.excerpt}</p>
                <div className="community-admin-card__stats">
                  <span>{item.status === "scheduled" ? formatAdminDate(item.scheduled_at) : formatAdminDate(item.published_at)}</span>
                  <span>Просмотры {item.view_count}</span>
                </div>
                <div className="community-admin-card__actions">
                  <button type="button" onClick={() => void handleEdit(item.id)} disabled={isEditingLoading}>
                    Редактировать
                  </button>
                  <button type="button" onClick={() => void handleHide(item.id)} disabled={item.status === "hidden"}>
                    Скрыть
                  </button>
                </div>
              </article>
            ))
          )}
        </div>

        <InsightForm
          form={form}
          isEditing={isEditing}
          isSaving={isSaving}
          showUrgentPublishNotice={showUrgentPublishNotice}
          onChange={setForm}
          onSubmit={() => void handleSubmit()}
        />
      </div>
    </section>
  );
}

function InsightForm({
  form,
  isEditing,
  isSaving,
  showUrgentPublishNotice,
  onChange,
  onSubmit,
}: {
  form: InsightFormState;
  isEditing: boolean;
  isSaving: boolean;
  showUrgentPublishNotice: boolean;
  onChange: (form: InsightFormState) => void;
  onSubmit: () => void;
}) {
  return (
    <aside className="community-admin-form">
      <div className="community-admin-form__header">
        <span>{isEditing ? "Редактирование" : "Создание"}</span>
        <h2>{isEditing ? "Изменить инсайт" : "Новый инсайт"}</h2>
      </div>
      <label>
        Заголовок
        <input value={form.title} onChange={(event) => onChange({ ...form, title: event.target.value })} />
      </label>
      <label>
        Краткое описание
        <textarea rows={3} value={form.excerpt} onChange={(event) => onChange({ ...form, excerpt: event.target.value })} />
      </label>
      <label>
        Контент
        <textarea rows={8} value={form.content} onChange={(event) => onChange({ ...form, content: event.target.value })} />
      </label>
      <label>
        Статус
        <select value={form.status} onChange={(event) => onChange({ ...form, status: event.target.value as CommunityAdminContentStatus })}>
          <option value="draft">Черновик</option>
          <option value="scheduled">Запланирован</option>
          <option value="published">Опубликован</option>
          <option value="hidden">Скрыт</option>
        </select>
      </label>
      <label>
        Дата публикации по расписанию
        <input type="datetime-local" value={form.scheduled_at} onChange={(event) => onChange({ ...form, scheduled_at: event.target.value })} />
      </label>
      <label>
        Дата публикации
        <input type="datetime-local" value={form.published_at} onChange={(event) => onChange({ ...form, published_at: event.target.value })} />
      </label>
      <label className="community-admin-checkbox">
        <input type="checkbox" checked={form.is_urgent} onChange={(event) => onChange({ ...form, is_urgent: event.target.checked })} />
        Срочный инсайт
      </label>
      {showUrgentPublishNotice && (
        <p className="community-admin-notice">
          После публикации записи попадут в очередь уведомлений. Обработать очередь можно в настройках админки; реальные сообщения в Telegram пока не отправляются.
        </p>
      )}
      <button className="community-admin-button community-admin-button--primary" type="button" onClick={onSubmit} disabled={isSaving}>
        {isSaving ? "Сохраняем" : isEditing ? "Сохранить" : "Создать"}
      </button>
    </aside>
  );
}
