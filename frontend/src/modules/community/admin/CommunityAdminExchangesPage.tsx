import { useEffect, useMemo, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import {
  createCommunityAdminExchange,
  getCommunityAdminExchange,
  hideCommunityAdminExchange,
  listCommunityAdminExchanges,
  updateCommunityAdminExchange,
} from "../api";
import type { CommunityAdminExchange, CommunityAdminExchangePayload } from "../types";

type ExchangeFormState = {
  id: string | null;
  title: string;
  description: string;
  team_comment: string;
  logo_url: string;
  external_url: string;
  promo_code: string;
  sort_order: string;
  is_published: boolean;
};

const emptyForm: ExchangeFormState = {
  id: null,
  title: "",
  description: "",
  team_comment: "",
  logo_url: "",
  external_url: "",
  promo_code: "",
  sort_order: "0",
  is_published: false,
};

function formFromExchange(exchange: CommunityAdminExchange): ExchangeFormState {
  return {
    id: exchange.id,
    title: exchange.title,
    description: exchange.description,
    team_comment: exchange.team_comment ?? "",
    logo_url: exchange.logo_url ?? "",
    external_url: exchange.external_url,
    promo_code: exchange.promo_code ?? "",
    sort_order: String(exchange.sort_order),
    is_published: exchange.is_published,
  };
}

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed || null;
}

function payloadFromForm(form: ExchangeFormState): CommunityAdminExchangePayload {
  return {
    title: form.title.trim(),
    description: form.description.trim(),
    team_comment: optionalText(form.team_comment),
    logo_url: optionalText(form.logo_url),
    external_url: form.external_url.trim(),
    promo_code: optionalText(form.promo_code),
    sort_order: Number(form.sort_order) || 0,
    is_published: form.is_published,
  };
}

function validateForm(form: ExchangeFormState): string | null {
  if (!form.title.trim()) {
    return "Укажите название биржи.";
  }
  if (!form.description.trim()) {
    return "Укажите описание.";
  }
  if (!form.external_url.trim()) {
    return "Укажите external URL.";
  }
  return null;
}

export function CommunityAdminExchangesPage() {
  const [items, setItems] = useState<CommunityAdminExchange[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isEditingLoading, setIsEditingLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [form, setForm] = useState<ExchangeFormState>(emptyForm);

  const isEditing = form.id !== null;
  const summary = useMemo(() => `${items.length} площадок`, [items.length]);

  const loadExchanges = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await listCommunityAdminExchanges();
      setItems(payload);
      setAccessDenied(false);
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить биржи.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadExchanges();
  }, []);

  const handleEdit = async (exchangeId: string) => {
    setIsEditingLoading(true);
    setFormError(null);
    try {
      setForm(formFromExchange(await getCommunityAdminExchange(exchangeId)));
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось открыть биржу.");
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
        await updateCommunityAdminExchange(form.id, payload);
      } else {
        await createCommunityAdminExchange(payload);
      }
      setForm(emptyForm);
      await loadExchanges();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось сохранить биржу.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleHide = async (exchangeId: string) => {
    setFormError(null);
    try {
      await hideCommunityAdminExchange(exchangeId);
      if (form.id === exchangeId) {
        setForm(emptyForm);
      }
      await loadExchanges();
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.status === 403) {
        setAccessDenied(true);
        return;
      }
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось скрыть биржу.");
    }
  };

  if (isLoading) {
    return <LoadingState title="Загружаем биржи" description="Получаем админский список внешних площадок." />;
  }
  if (accessDenied) {
    return <EmptyState title="Нет доступа к админ-разделу" description="Backend не подтвердил права администратора." />;
  }
  if (error) {
    return <ErrorState title="Биржи недоступны" description="Не удалось получить админский список бирж." />;
  }

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>Админ-панель GlobalGreenInvest</span>
          <h1>Биржи</h1>
          <p>{summary}</p>
        </div>
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => setForm(emptyForm)}>
          Создать биржу
        </button>
      </header>
      {formError && <p className="community-admin-inline-error">{formError}</p>}
      <div className="community-admin-grid">
        <div className="community-admin-list">
          {items.length === 0 ? (
            <EmptyState title="Бирж нет" description="Добавьте первую внешнюю площадку для проекта." />
          ) : (
            items.map((item) => (
              <article className="community-admin-card" key={item.id}>
                <div className="community-admin-card__meta">
                  <span>{item.is_published ? "Опубликована" : "Скрыта"}</span>
                  <span>Порядок {item.sort_order}</span>
                </div>
                <h2>{item.title}</h2>
                <p>{item.external_url}</p>
                <div className="community-admin-card__stats">
                  {item.promo_code && <span>Промокод {item.promo_code}</span>}
                </div>
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
        <ExchangeForm form={form} isEditing={isEditing} isSaving={isSaving} onChange={setForm} onSubmit={() => void handleSubmit()} />
      </div>
    </section>
  );
}

function ExchangeForm({
  form,
  isEditing,
  isSaving,
  onChange,
  onSubmit,
}: {
  form: ExchangeFormState;
  isEditing: boolean;
  isSaving: boolean;
  onChange: (form: ExchangeFormState) => void;
  onSubmit: () => void;
}) {
  return (
    <aside className="community-admin-form">
      <div className="community-admin-form__header">
        <span>{isEditing ? "Редактирование" : "Создание"}</span>
        <h2>{isEditing ? "Изменить биржу" : "Новая биржа"}</h2>
      </div>
      <label>
        Название
        <input value={form.title} onChange={(event) => onChange({ ...form, title: event.target.value })} />
      </label>
      <label>
        Описание
        <textarea rows={4} value={form.description} onChange={(event) => onChange({ ...form, description: event.target.value })} />
      </label>
      <label>
        Комментарий команды
        <textarea rows={3} value={form.team_comment} onChange={(event) => onChange({ ...form, team_comment: event.target.value })} />
      </label>
      <label>
        Logo URL
        <input value={form.logo_url} onChange={(event) => onChange({ ...form, logo_url: event.target.value })} />
      </label>
      <label>
        External URL
        <input value={form.external_url} onChange={(event) => onChange({ ...form, external_url: event.target.value })} />
      </label>
      <label>
        Promo code
        <input value={form.promo_code} onChange={(event) => onChange({ ...form, promo_code: event.target.value })} />
      </label>
      <label>
        Порядок
        <input type="number" value={form.sort_order} onChange={(event) => onChange({ ...form, sort_order: event.target.value })} />
      </label>
      <label className="community-admin-checkbox">
        <input type="checkbox" checked={form.is_published} onChange={(event) => onChange({ ...form, is_published: event.target.checked })} />
        Опубликована
      </label>
      <button className="community-admin-button community-admin-button--primary" type="button" onClick={onSubmit} disabled={isSaving}>
        {isSaving ? "Сохраняем" : isEditing ? "Сохранить" : "Создать"}
      </button>
    </aside>
  );
}
