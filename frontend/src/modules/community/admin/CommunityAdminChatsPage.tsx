import { useEffect, useMemo, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import {
  createCommunityAdminChat,
  getCommunityAdminChat,
  hideCommunityAdminChat,
  listCommunityAdminChats,
  updateCommunityAdminChat,
} from "../api";
import type { CommunityAdminChat, CommunityAdminChatPayload } from "../types";

type ChatFormState = {
  id: string | null;
  title: string;
  telegram_url: string;
  sort_order: string;
  is_published: boolean;
};

const emptyForm: ChatFormState = {
  id: null,
  title: "",
  telegram_url: "",
  sort_order: "0",
  is_published: false,
};

function formFromChat(chat: CommunityAdminChat): ChatFormState {
  return {
    id: chat.id,
    title: chat.title,
    telegram_url: chat.telegram_url,
    sort_order: String(chat.sort_order),
    is_published: chat.is_published,
  };
}

function payloadFromForm(form: ChatFormState): CommunityAdminChatPayload {
  return {
    title: form.title.trim(),
    telegram_url: form.telegram_url.trim(),
    sort_order: Number(form.sort_order) || 0,
    is_published: form.is_published,
  };
}

function validateForm(form: ChatFormState): string | null {
  if (!form.title.trim()) {
    return "Укажите название чата.";
  }
  if (!form.telegram_url.trim()) {
    return "Укажите Telegram URL.";
  }
  return null;
}

export function CommunityAdminChatsPage() {
  const [items, setItems] = useState<CommunityAdminChat[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isEditingLoading, setIsEditingLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [form, setForm] = useState<ChatFormState>(emptyForm);

  const isEditing = form.id !== null;
  const summary = useMemo(() => `${items.length} ссылок`, [items.length]);

  const loadChats = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await listCommunityAdminChats();
      setItems(payload);
      setAccessDenied(false);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить чаты.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadChats();
  }, []);

  const handleEdit = async (chatId: string) => {
    setIsEditingLoading(true);
    setFormError(null);
    try {
      setForm(formFromChat(await getCommunityAdminChat(chatId)));
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось открыть чат.");
    } finally {
      setIsEditingLoading(false);
    }
  };

  const handleSubmit = async () => {
    const validationError = validateForm(form);
    if (validationError) {
      setFormError(validationError);
      return;
    }
    setIsSaving(true);
    setFormError(null);
    try {
      const payload = payloadFromForm(form);
      if (form.id) {
        await updateCommunityAdminChat(form.id, payload);
      } else {
        await createCommunityAdminChat(payload);
      }
      setForm(emptyForm);
      await loadChats();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось сохранить чат.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleHide = async (chatId: string) => {
    setFormError(null);
    try {
      await hideCommunityAdminChat(chatId);
      if (form.id === chatId) {
        setForm(emptyForm);
      }
      await loadChats();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось скрыть чат.");
    }
  };

  if (isLoading) {
    return <LoadingState title="Загружаем чаты" description="Получаем админский список Telegram-ссылок." />;
  }
  if (accessDenied) {
    return <EmptyState title="Нет доступа к админ-разделу" description="Backend не подтвердил права администратора." />;
  }
  if (error) {
    return <ErrorState title="Чаты недоступны" description="Не удалось получить админский список чатов." />;
  }

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>Админ-панель GlobalGreenInvest</span>
          <h1>Чаты</h1>
          <p>{summary}</p>
        </div>
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => setForm(emptyForm)}>
          Создать чат
        </button>
      </header>
      {formError && <p className="community-admin-inline-error">{formError}</p>}
      <div className="community-admin-grid">
        <div className="community-admin-list">
          {items.length === 0 ? (
            <EmptyState title="Чатов нет" description="Добавьте первую Telegram-ссылку для проекта." />
          ) : (
            items.map((item) => (
              <article className="community-admin-card" key={item.id}>
                <div className="community-admin-card__meta">
                  <span>{item.is_published ? "Опубликован" : "Скрыт"}</span>
                  <span>Порядок {item.sort_order}</span>
                </div>
                <h2>{item.title}</h2>
                <p>{item.telegram_url}</p>
                <div className="community-admin-card__actions">
                  <button type="button" onClick={() => void handleEdit(item.id)} disabled={isEditingLoading}>
                    Редактировать
                  </button>
                  <button type="button" onClick={() => void handleHide(item.id)} disabled={!item.is_published}>
                    Скрыть
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
        <ChatForm form={form} isEditing={isEditing} isSaving={isSaving} onChange={setForm} onSubmit={() => void handleSubmit()} />
      </div>
    </section>
  );
}

function ChatForm({
  form,
  isEditing,
  isSaving,
  onChange,
  onSubmit,
}: {
  form: ChatFormState;
  isEditing: boolean;
  isSaving: boolean;
  onChange: (form: ChatFormState) => void;
  onSubmit: () => void;
}) {
  return (
    <aside className="community-admin-form">
      <div className="community-admin-form__header">
        <span>{isEditing ? "Редактирование" : "Создание"}</span>
        <h2>{isEditing ? "Изменить чат" : "Новый чат"}</h2>
      </div>
      <label>
        Название
        <input value={form.title} onChange={(event) => onChange({ ...form, title: event.target.value })} />
      </label>
      <label>
        Telegram URL
        <input value={form.telegram_url} onChange={(event) => onChange({ ...form, telegram_url: event.target.value })} />
      </label>
      <label>
        Порядок
        <input type="number" value={form.sort_order} onChange={(event) => onChange({ ...form, sort_order: event.target.value })} />
      </label>
      <label className="community-admin-checkbox">
        <input type="checkbox" checked={form.is_published} onChange={(event) => onChange({ ...form, is_published: event.target.checked })} />
        Опубликован
      </label>
      <button className="community-admin-button community-admin-button--primary" type="button" onClick={onSubmit} disabled={isSaving}>
        {isSaving ? "Сохраняем" : isEditing ? "Сохранить" : "Создать"}
      </button>
    </aside>
  );
}
