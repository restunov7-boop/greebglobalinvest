import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import {
  approveAndGrantCommunityAdminPurchaseRequest,
  listCommunityAdminProducts,
  listCommunityAdminPurchaseRequests,
  updateCommunityAdminPurchaseRequest,
} from "../api";
import type {
  CommunityAdminProduct,
  CommunityAdminPurchaseRequest,
  CommunityProductPurchaseRequestStatus,
} from "../types";

type Filters = {
  status: "all" | CommunityProductPurchaseRequestStatus;
  product_id: string;
  q: string;
};

const filtersInitial: Filters = {
  status: "all",
  product_id: "",
  q: "",
};

function requestStatusLabel(status: string): string {
  return (
    {
      new: "Новая",
      contacted: "Связались",
      approved: "Одобрена",
      rejected: "Отклонена",
      cancelled: "Отменена",
    }[status] ?? status
  );
}

function contactLabel(request: CommunityAdminPurchaseRequest): string {
  if (request.contact_value) return request.contact_value;
  if (request.telegram_username) return `@${request.telegram_username}`;
  if (request.telegram_first_name) return request.telegram_first_name;
  return request.user_id.slice(0, 8);
}

function formatDate(value: string | null): string {
  if (!value) return "не указано";
  return new Date(value).toLocaleString();
}

export function CommunityAdminPurchaseRequestsPage() {
  const [filters, setFilters] = useState<Filters>(filtersInitial);
  const [requests, setRequests] = useState<CommunityAdminPurchaseRequest[]>([]);
  const [products, setProducts] = useState<CommunityAdminProduct[]>([]);
  const [total, setTotal] = useState(0);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [grantUntil, setGrantUntil] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const productById = useMemo(() => new Map(products.map((product) => [product.id, product])), [products]);

  async function loadRequests(nextFilters = filters) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listCommunityAdminPurchaseRequests({
        status: nextFilters.status,
        product_id: nextFilters.product_id || undefined,
        q: nextFilters.q || undefined,
        limit: 50,
        offset: 0,
      });
      setRequests(response.items);
      setTotal(response.total);
      setNotes((current) => {
        const next = { ...current };
        for (const request of response.items) {
          if (next[request.request_id] === undefined) next[request.request_id] = request.admin_note ?? "";
        }
        return next;
      });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить заявки.");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadProducts() {
    setProducts(await listCommunityAdminProducts());
  }

  useEffect(() => {
    void loadProducts();
    void loadRequests();
  }, []);

  async function applyFilters() {
    await loadRequests(filters);
  }

  async function updateStatus(request: CommunityAdminPurchaseRequest, status: CommunityProductPurchaseRequestStatus) {
    setActionError(null);
    setNotice(null);
    await updateCommunityAdminPurchaseRequest(request.request_id, {
      status,
      admin_note: notes[request.request_id]?.trim() || null,
    });
    setNotice("Статус заявки обновлён. Доступ к продукту не выдавался автоматически.");
    await loadRequests(filters);
  }

  async function approveAndGrant(request: CommunityAdminPurchaseRequest) {
    setActionError(null);
    setNotice(null);
    try {
      await approveAndGrantCommunityAdminPurchaseRequest(request.request_id, {
        access_until: grantUntil[request.request_id]?.trim() || null,
      });
      setNotice("Заявка одобрена, доступ к продукту выдан вручную.");
      await loadRequests(filters);
    } catch (requestError) {
      setActionError(requestError instanceof Error ? requestError.message : "Не удалось одобрить заявку.");
    }
  }

  if (isLoading) return <LoadingState title="Загружаем заявки" />;
  if (error) return <ErrorState title="Заявки недоступны" description={error} />;

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>Админ-панель GlobalGreenInvest</span>
          <h1>Заявки на продукты</h1>
          <p>{total} заявок. Создание заявки не выдаёт доступ автоматически.</p>
        </div>
      </header>

      <div className="community-admin-user-filters community-admin-request-filters">
        <label>
          Поиск
          <input
            value={filters.q}
            placeholder="@username, контакт или комментарий"
            onChange={(event) => setFilters({ ...filters, q: event.target.value })}
          />
        </label>
        <label>
          Статус
          <select
            value={filters.status}
            onChange={(event) => setFilters({ ...filters, status: event.target.value as Filters["status"] })}
          >
            <option value="all">Все</option>
            <option value="new">Новые</option>
            <option value="contacted">Связались</option>
            <option value="approved">Одобрены</option>
            <option value="rejected">Отклонены</option>
            <option value="cancelled">Отменены</option>
          </select>
        </label>
        <label>
          Продукт
          <select value={filters.product_id} onChange={(event) => setFilters({ ...filters, product_id: event.target.value })}>
            <option value="">Все продукты</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.title}
              </option>
            ))}
          </select>
        </label>
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => void applyFilters()}>
          Применить
        </button>
      </div>

      {actionError && <p className="community-admin-inline-error">{actionError}</p>}
      {notice && <p className="community-admin-notice">{notice}</p>}

      <div className="community-admin-list">
        {requests.length === 0 && <p className="community-admin-empty">Заявок пока нет.</p>}
        {requests.map((request) => (
          <article className="community-admin-card" key={request.request_id}>
            <div className="community-admin-card__meta">
              <span className={`community-admin-badge community-admin-badge--${request.status}`}>
                {requestStatusLabel(request.status)}
              </span>
              <span>{productById.get(request.product_id)?.title ?? request.product_title}</span>
              <span>{formatDate(request.created_at)}</span>
              {request.has_active_product_access && <span>Доступ уже активен</span>}
            </div>
            <h2>{contactLabel(request)}</h2>
            <p>{request.message || "Комментарий пользователя не указан."}</p>
            <div className="community-admin-request-grid">
              <label>
                Заметка админа
                <textarea
                  rows={3}
                  value={notes[request.request_id] ?? ""}
                  onChange={(event) => setNotes({ ...notes, [request.request_id]: event.target.value })}
                />
              </label>
              <label>
                Доступ до
                <input
                  type="datetime-local"
                  value={grantUntil[request.request_id] ?? ""}
                  onChange={(event) => setGrantUntil({ ...grantUntil, [request.request_id]: event.target.value })}
                />
              </label>
            </div>
            <div className="community-admin-card__stats">
              <span>Пользователь {request.project_user_id}</span>
              <span>Контакт: {request.contact_method || "не указан"} / {request.contact_value || "не указан"}</span>
              {request.handled_at && <span>Обработана {formatDate(request.handled_at)}</span>}
            </div>
            <div className="community-admin-card__actions">
              <button type="button" onClick={() => void updateStatus(request, "contacted")}>
                Связались
              </button>
              <button type="button" onClick={() => void updateStatus(request, "rejected")}>
                Отклонить
              </button>
              <button type="button" onClick={() => void updateStatus(request, "cancelled")}>
                Отменить
              </button>
              <button
                className="community-admin-button--primary"
                type="button"
                onClick={() => void approveAndGrant(request)}
                disabled={request.has_active_product_access}
              >
                Одобрить и выдать доступ
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
