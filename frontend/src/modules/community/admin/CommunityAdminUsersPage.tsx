import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import {
  banCommunityAdminUser,
  extendCommunityAdminUserOneYear,
  getCommunityAdminUser,
  grantCommunityAdminProductAccess,
  listCommunityAdminProducts,
  listCommunityAdminUsers,
  unbanCommunityAdminUser,
  updateCommunityAdminProductAccess,
  updateCommunityAdminUserProjectAccess,
} from "../api";
import { accessStateLabel, moderationStateLabel, productAccessSourceLabel, roleLabel } from "../labels";
import type {
  CommunityAdminModerationState,
  CommunityAdminProduct,
  CommunityAdminProductAccessState,
  CommunityAdminProjectAccessState,
  CommunityAdminProjectRole,
  CommunityAdminUserDetail,
  CommunityAdminUserListItem,
  CommunityAdminUserListParams,
} from "../types";

type Filters = Required<Pick<CommunityAdminUserListParams, "access_state" | "moderation_state" | "role">> & {
  q: string;
};

type ProjectAccessForm = {
  access_state: CommunityAdminProjectAccessState;
  access_until: string;
  moderation_state: CommunityAdminModerationState;
  role: CommunityAdminProjectRole;
};

type ProductAccessForm = {
  product_id: string;
  access_state: CommunityAdminProductAccessState;
  access_until: string;
};

const filtersInitial: Filters = {
  q: "",
  access_state: "all",
  moderation_state: "all",
  role: "all",
};

const productAccessInitial: ProductAccessForm = {
  product_id: "",
  access_state: "active",
  access_until: "",
};

function toDateInput(value: string | null): string {
  if (!value) return "";
  return value.slice(0, 16);
}

function fromDateInput(value: string): string | null {
  return value.trim() ? value : null;
}

function projectAccessForm(user: CommunityAdminUserDetail): ProjectAccessForm {
  return {
    access_state: user.access_state,
    access_until: toDateInput(user.access_until),
    moderation_state: user.moderation_state,
    role: user.role,
  };
}

function displayName(user: CommunityAdminUserListItem): string {
  if (user.telegram_first_name && user.telegram_username) return `${user.telegram_first_name} (@${user.telegram_username})`;
  if (user.telegram_username) return `@${user.telegram_username}`;
  if (user.telegram_first_name) return user.telegram_first_name;
  return user.user_id.slice(0, 8);
}

function statusLabel(value: string): string {
  return accessStateLabel(value) !== value
    ? accessStateLabel(value)
    : moderationStateLabel(value) !== value
      ? moderationStateLabel(value)
      : roleLabel(value);
}

export function CommunityAdminUsersPage() {
  const [filters, setFilters] = useState<Filters>(filtersInitial);
  const [users, setUsers] = useState<CommunityAdminUserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<CommunityAdminUserDetail | null>(null);
  const [products, setProducts] = useState<CommunityAdminProduct[]>([]);
  const [projectForm, setProjectForm] = useState<ProjectAccessForm | null>(null);
  const [productForm, setProductForm] = useState<ProductAccessForm>(productAccessInitial);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const selectedListUser = useMemo(
    () => users.find((user) => user.project_user_id === selectedUserId) ?? null,
    [selectedUserId, users],
  );

  async function loadUsers(nextFilters = filters) {
    setIsLoading(true);
    setError(null);
    try {
      const response = await listCommunityAdminUsers({
        q: nextFilters.q || undefined,
        access_state: nextFilters.access_state,
        moderation_state: nextFilters.moderation_state,
        role: nextFilters.role,
        limit: 50,
        offset: 0,
      });
      setUsers(response.items);
      setTotal(response.total);
      if (!selectedUserId && response.items[0]) {
        setSelectedUserId(response.items[0].project_user_id);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить пользователей.");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadSelectedUser(projectUserId: string | null) {
    if (!projectUserId) {
      setSelectedUser(null);
      setProjectForm(null);
      return;
    }
    setIsDetailLoading(true);
    setFormError(null);
    try {
      const detail = await getCommunityAdminUser(projectUserId);
      setSelectedUser(detail);
      setProjectForm(projectAccessForm(detail));
    } catch (requestError) {
      setFormError(requestError instanceof Error ? requestError.message : "Не удалось загрузить карточку пользователя.");
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function loadProducts() {
    const items = await listCommunityAdminProducts();
    setProducts(items);
    setProductForm((current) => ({ ...current, product_id: current.product_id || items[0]?.id || "" }));
  }

  useEffect(() => {
    void loadUsers();
    void loadProducts();
  }, []);

  useEffect(() => {
    void loadSelectedUser(selectedUserId);
  }, [selectedUserId]);

  async function applyFilters() {
    await loadUsers(filters);
  }

  async function saveProjectAccess() {
    if (!selectedUser || !projectForm) return;
    setFormError(null);
    const detail = await updateCommunityAdminUserProjectAccess(selectedUser.project_user_id, {
      access_state: projectForm.access_state,
      access_until: fromDateInput(projectForm.access_until),
      moderation_state: projectForm.moderation_state,
      role: projectForm.role,
    });
    setSelectedUser(detail);
    setProjectForm(projectAccessForm(detail));
    await loadUsers(filters);
  }

  async function applyQuickAction(action: "extend" | "ban" | "unban" | "revoke") {
    if (!selectedUser) return;
    setFormError(null);
    let detail: CommunityAdminUserDetail;
    if (action === "extend") detail = await extendCommunityAdminUserOneYear(selectedUser.project_user_id);
    else if (action === "ban") detail = await banCommunityAdminUser(selectedUser.project_user_id);
    else if (action === "unban") detail = await unbanCommunityAdminUser(selectedUser.project_user_id);
    else detail = await updateCommunityAdminUserProjectAccess(selectedUser.project_user_id, { access_state: "revoked" });
    setSelectedUser(detail);
    setProjectForm(projectAccessForm(detail));
    await loadUsers(filters);
  }

  async function grantProductAccess() {
    if (!selectedUser || !productForm.product_id) return;
    setFormError(null);
    await grantCommunityAdminProductAccess({
      product_id: productForm.product_id,
      project_user_id: selectedUser.project_user_id,
      access_state: productForm.access_state,
      access_until: fromDateInput(productForm.access_until),
      source: "manual",
    });
    await loadSelectedUser(selectedUser.project_user_id);
    await loadUsers(filters);
  }

  async function revokeProductAccess(accessId: string) {
    if (!selectedUser) return;
    setFormError(null);
    await updateCommunityAdminProductAccess(accessId, { access_state: "revoked", access_until: null });
    await loadSelectedUser(selectedUser.project_user_id);
    await loadUsers(filters);
  }

  if (isLoading) return <LoadingState title="Загружаем пользователей" />;
  if (error) return <ErrorState title="Пользователи недоступны" description={error} />;

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>Админ-панель GlobalGreenInvest</span>
          <h1>Пользователи / Доступы</h1>
          <p>{total} пользователей проекта</p>
        </div>
      </header>

      <div className="community-admin-user-filters">
        <label>
          Поиск
          <input
            value={filters.q}
            placeholder="@username, имя или user id"
            onChange={(event) => setFilters({ ...filters, q: event.target.value })}
          />
        </label>
        <label>
          Доступ
          <select
            value={filters.access_state}
            onChange={(event) => setFilters({ ...filters, access_state: event.target.value as Filters["access_state"] })}
          >
            <option value="all">Все</option>
            <option value="pending">Ожидает</option>
            <option value="active">Активен</option>
            <option value="expired">Истёк</option>
            <option value="revoked">Отозван</option>
          </select>
        </label>
        <label>
          Модерация
          <select
            value={filters.moderation_state}
            onChange={(event) => setFilters({ ...filters, moderation_state: event.target.value as Filters["moderation_state"] })}
          >
            <option value="all">Все</option>
            <option value="normal">Норма</option>
            <option value="banned">Забанен</option>
          </select>
        </label>
        <label>
          Роль
          <select value={filters.role} onChange={(event) => setFilters({ ...filters, role: event.target.value as Filters["role"] })}>
            <option value="all">Все</option>
            <option value="member">Участник</option>
            <option value="admin">Админ</option>
            <option value="owner">Владелец</option>
          </select>
        </label>
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => void applyFilters()}>
          Применить
        </button>
      </div>

      {formError && <p className="community-admin-inline-error">{formError}</p>}

      <div className="community-admin-users-layout">
        <div className="community-admin-users-list">
          {users.length === 0 && <p className="community-admin-empty">Пользователи не найдены.</p>}
          {users.map((user) => (
            <button
              className={`community-admin-user-row ${user.project_user_id === selectedUserId ? "is-selected" : ""}`}
              key={user.project_user_id}
              type="button"
              onClick={() => setSelectedUserId(user.project_user_id)}
            >
              <span className="community-admin-user-row__avatar">
                {user.telegram_photo_url ? <img src={user.telegram_photo_url} alt="" /> : displayName(user).slice(0, 1).toUpperCase()}
              </span>
              <span className="community-admin-user-row__main">
                <strong>{displayName(user)}</strong>
                <small>{user.user_id}</small>
              </span>
              <span className={`community-admin-badge community-admin-badge--${user.access_state}`}>{statusLabel(user.access_state)}</span>
              <span className={`community-admin-badge community-admin-badge--${user.moderation_state}`}>{statusLabel(user.moderation_state)}</span>
              <span className="community-admin-user-row__products">
                {user.active_product_access_count}/{user.product_access_count} продуктов
              </span>
            </button>
          ))}
        </div>

        <aside className="community-admin-user-panel">
          {isDetailLoading && <LoadingState title="Открываем пользователя" />}
          {!isDetailLoading && selectedUser && projectForm && (
            <>
              <div className="community-admin-user-panel__header">
                <span>Пользователь</span>
                <h2>{displayName(selectedUser)}</h2>
                <p>{selectedListUser?.user_id ?? selectedUser.user_id}</p>
              </div>

              <section className="community-admin-user-section">
                <h3>Доступ к приложению</h3>
                <label>
                  Состояние доступа
                  <select
                    value={projectForm.access_state}
                    onChange={(event) => setProjectForm({ ...projectForm, access_state: event.target.value as CommunityAdminProjectAccessState })}
                  >
                    <option value="pending">Ожидает</option>
                    <option value="active">Активен</option>
                    <option value="expired">Истёк</option>
                    <option value="revoked">Отозван</option>
                  </select>
                </label>
                <label>
                  Доступ до
                  <input
                    type="datetime-local"
                    value={projectForm.access_until}
                    onChange={(event) => setProjectForm({ ...projectForm, access_until: event.target.value })}
                  />
                </label>
                <label>
                  Модерация
                  <select
                    value={projectForm.moderation_state}
                    onChange={(event) =>
                      setProjectForm({ ...projectForm, moderation_state: event.target.value as CommunityAdminModerationState })
                    }
                  >
                    <option value="normal">Норма</option>
                    <option value="banned">Забанен</option>
                  </select>
                </label>
                <label>
                  Роль
                  <select
                    value={projectForm.role}
                    onChange={(event) => setProjectForm({ ...projectForm, role: event.target.value as CommunityAdminProjectRole })}
                  >
                    <option value="member">Участник</option>
                    <option value="admin">Админ</option>
                    <option value="owner">Владелец</option>
                  </select>
                </label>
                <div className="community-admin-actions-wrap">
                  <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => void saveProjectAccess()}>
                    Сохранить доступ
                  </button>
                  <button className="community-admin-button" type="button" onClick={() => void applyQuickAction("extend")}>
                    +1 год
                  </button>
                  <button className="community-admin-button" type="button" onClick={() => void applyQuickAction("revoke")}>
                    Отозвать доступ
                  </button>
                  <button className="community-admin-button" type="button" onClick={() => void applyQuickAction("ban")}>
                    Забанить
                  </button>
                  <button className="community-admin-button" type="button" onClick={() => void applyQuickAction("unban")}>
                    Разбанить
                  </button>
                </div>
              </section>

              <section className="community-admin-user-section">
                <h3>Доступ к продуктам</h3>
                <div className="community-admin-product-access-form">
                  <label>
                    Продукт
                    <select
                      value={productForm.product_id}
                      onChange={(event) => setProductForm({ ...productForm, product_id: event.target.value })}
                    >
                      {products.map((product) => (
                        <option key={product.id} value={product.id}>
                          {product.title}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Состояние
                    <select
                      value={productForm.access_state}
                      onChange={(event) =>
                        setProductForm({ ...productForm, access_state: event.target.value as CommunityAdminProductAccessState })
                      }
                    >
                      <option value="active">Активен</option>
                      <option value="expired">Истёк</option>
                      <option value="revoked">Отозван</option>
                    </select>
                  </label>
                  <label>
                    Доступ до
                    <input
                      type="datetime-local"
                      value={productForm.access_until}
                      onChange={(event) => setProductForm({ ...productForm, access_until: event.target.value })}
                    />
                  </label>
                  <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => void grantProductAccess()}>
                    Выдать доступ
                  </button>
                </div>

                <div className="community-admin-product-access-list">
                  {selectedUser.product_access.length === 0 && <p className="community-admin-empty">Доступов к продуктам пока нет.</p>}
                  {selectedUser.product_access.map((access) => (
                    <article className="community-admin-product-access-card" key={access.access_id}>
                      <div>
                        <strong>{access.product_title}</strong>
                        <span className={`community-admin-badge community-admin-badge--${access.access_state}`}>
                          {statusLabel(access.access_state)}
                        </span>
                      </div>
                      <p>
                        {access.access_until ? `до ${new Date(access.access_until).toLocaleDateString()}` : "без срока"}
                        {" · "}
                        {productAccessSourceLabel(access.source)}
                      </p>
                      <button type="button" onClick={() => void revokeProductAccess(access.access_id)} disabled={access.access_state === "revoked"}>
                        Отозвать доступ
                      </button>
                    </article>
                  ))}
                </div>
              </section>
            </>
          )}
          {!isDetailLoading && !selectedUser && <p className="community-admin-empty">Выберите пользователя.</p>}
        </aside>
      </div>
    </section>
  );
}
