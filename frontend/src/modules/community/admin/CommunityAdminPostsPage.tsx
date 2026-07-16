import { useEffect, useMemo, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import {
  createCommunityAdminPost,
  getCommunityAdminPost,
  hideCommunityAdminPost,
  listCommunityAdminPosts,
  updateCommunityAdminPost,
} from "../api";
import { contentStatusLabel } from "../labels";
import type {
  CommunityAdminContentStatus,
  CommunityAdminPost,
  CommunityAdminPostListItem,
  CommunityAdminPostPayload,
  CommunityAdminStatusFilter,
} from "../types";

type PostFormState = {
  id: string | null;
  title: string;
  excerpt: string;
  content: string;
  cover_url: string;
  status: CommunityAdminContentStatus;
  is_pinned: boolean;
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

const emptyForm: PostFormState = {
  id: null,
  title: "",
  excerpt: "",
  content: "",
  cover_url: "",
  status: "draft",
  is_pinned: false,
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

function formFromPost(post: CommunityAdminPost): PostFormState {
  return {
    id: post.id,
    title: post.title,
    excerpt: post.excerpt,
    content: post.content,
    cover_url: post.cover_url ?? "",
    status: post.status,
    is_pinned: post.is_pinned,
    scheduled_at: toDateTimeInput(post.scheduled_at),
    published_at: toDateTimeInput(post.published_at),
  };
}

function payloadFromForm(form: PostFormState): CommunityAdminPostPayload {
  return {
    title: form.title.trim(),
    excerpt: form.excerpt.trim(),
    content: form.content.trim(),
    cover_url: form.cover_url.trim() || null,
    status: form.status,
    is_pinned: form.is_pinned,
    scheduled_at: toApiDate(form.scheduled_at),
    published_at: toApiDate(form.published_at),
  };
}

function validatePostForm(form: PostFormState): string | null {
  if (!form.title.trim()) {
    return "Укажите заголовок.";
  }
  if (!form.excerpt.trim()) {
    return "Укажите краткое описание.";
  }
  if (!form.content.trim()) {
    return "Заполните текст поста.";
  }
  if (form.status === "scheduled" && !form.scheduled_at) {
    return "Для запланированного поста укажите дату публикации.";
  }
  return null;
}

export function CommunityAdminPostsPage() {
  const [filter, setFilter] = useState<CommunityAdminStatusFilter>("all");
  const [items, setItems] = useState<CommunityAdminPostListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isEditingLoading, setIsEditingLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [form, setForm] = useState<PostFormState>(emptyForm);

  const isEditing = form.id !== null;

  const loadPosts = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await listCommunityAdminPosts({ status: filter });
      setItems(payload.items);
      setTotal(payload.total);
      setAccessDenied(false);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить посты.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadPosts();
  }, [filter]);

  const summary = useMemo(() => `${total} материалов`, [total]);

  const handleCreate = () => {
    setForm(emptyForm);
    setFormError(null);
  };

  const handleEdit = async (postId: string) => {
    setIsEditingLoading(true);
    setFormError(null);
    try {
      const post = await getCommunityAdminPost(postId);
      setForm(formFromPost(post));
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось открыть пост.");
    } finally {
      setIsEditingLoading(false);
    }
  };

  const handleSubmit = async () => {
    const validationError = validatePostForm(form);
    if (validationError) {
      setFormError(validationError);
      return;
    }
    setIsSaving(true);
    setFormError(null);
    try {
      const payload = payloadFromForm(form);
      if (form.id) {
        await updateCommunityAdminPost(form.id, payload);
      } else {
        await createCommunityAdminPost(payload);
      }
      setForm(emptyForm);
      await loadPosts();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось сохранить пост.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleHide = async (postId: string) => {
    setFormError(null);
    try {
      await hideCommunityAdminPost(postId);
      await loadPosts();
      if (form.id === postId) {
        setForm(emptyForm);
      }
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось скрыть пост.");
    }
  };

  if (isLoading) {
    return <LoadingState title="Загружаем посты" description="Получаем админский список материалов проекта." />;
  }

  if (accessDenied) {
    return <EmptyState title="Нет доступа к админ-разделу" description="Backend не подтвердил права администратора для этой операции." />;
  }

  if (error) {
    return <ErrorState title="Посты недоступны" description="Не удалось получить админский список постов." />;
  }

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>Админ-панель GlobalGreenInvest</span>
          <h1>Посты</h1>
          <p>{summary}</p>
        </div>
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={handleCreate}>
          Создать пост
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

      <div className="community-admin-grid">
        <div className="community-admin-list">
          {items.length === 0 ? (
            <EmptyState title="Постов нет" description="Для выбранного статуса материалы не найдены." />
          ) : (
            items.map((item) => (
              <article className="community-admin-card" key={item.id}>
                <div className="community-admin-card__meta">
                  <span>{contentStatusLabel(item.status)}</span>
                  {item.is_pinned && <span>Закреплен</span>}
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

        <PostForm form={form} isEditing={isEditing} isSaving={isSaving} onChange={setForm} onSubmit={() => void handleSubmit()} />
      </div>
    </section>
  );
}

function PostForm({
  form,
  isEditing,
  isSaving,
  onChange,
  onSubmit,
}: {
  form: PostFormState;
  isEditing: boolean;
  isSaving: boolean;
  onChange: (form: PostFormState) => void;
  onSubmit: () => void;
}) {
  return (
    <aside className="community-admin-form">
      <div className="community-admin-form__header">
        <span>{isEditing ? "Редактирование" : "Создание"}</span>
        <h2>{isEditing ? "Изменить пост" : "Новый пост"}</h2>
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
        Cover URL
        <input value={form.cover_url} onChange={(event) => onChange({ ...form, cover_url: event.target.value })} />
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
        <input type="checkbox" checked={form.is_pinned} onChange={(event) => onChange({ ...form, is_pinned: event.target.checked })} />
        Закрепить на главной
      </label>
      <button className="community-admin-button community-admin-button--primary" type="button" onClick={onSubmit} disabled={isSaving}>
        {isSaving ? "Сохраняем" : isEditing ? "Сохранить" : "Создать"}
      </button>
    </aside>
  );
}
