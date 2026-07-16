import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { EmptyState } from "../ui/CommunityState";
import { ErrorState } from "../ui/CommunityState";
import { LoadingState } from "../ui/CommunityState";
import { ApiError } from "../../../shared/api/client";
import { createCommunityProductPurchaseRequest, getCommunityProduct } from "../api";
import type { CommunityProductDetail, CommunityProductMaterial, CommunityProductPurchaseRequestStatus } from "../types";

function price(product: CommunityProductDetail): string {
  const parts = [];
  if (product.price_usd) parts.push(`$${product.price_usd}`);
  if (product.price_rub) parts.push(`${product.price_rub} RUB`);
  return parts.join(" / ") || "Цена по запросу";
}

function requestStatusLabel(status: CommunityProductPurchaseRequestStatus): string {
  return (
    {
      new: "Новая заявка",
      contacted: "Связались",
      approved: "Одобрено",
      rejected: "Отклонено",
      cancelled: "Отменено",
    }[status] ?? status
  );
}

export function CommunityProductDetailPage() {
  const { productId } = useParams();
  const [product, setProduct] = useState<CommunityProductDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(false);
  const [contactMethod, setContactMethod] = useState<"telegram" | "phone" | "email" | "other">("telegram");
  const [contactValue, setContactValue] = useState("");
  const [message, setMessage] = useState("");
  const [requestError, setRequestError] = useState<string | null>(null);
  const [requestNotice, setRequestNotice] = useState<string | null>(null);
  const [isRequesting, setIsRequesting] = useState(false);

  async function loadProduct() {
    if (!productId) {
      setNotFound(true);
      setIsLoading(false);
      return;
    }
    try {
      const payload = await getCommunityProduct(productId);
      setProduct(payload);
      setNotFound(false);
      setError(false);
    } catch (requestError) {
      if (requestError instanceof Error && requestError.message.toLowerCase().includes("not found")) setNotFound(true);
      else setError(true);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadProduct();
  }, [productId]);

  async function submitPurchaseRequest() {
    if (!productId) return;
    setRequestError(null);
    setRequestNotice(null);
    setIsRequesting(true);
    try {
      await createCommunityProductPurchaseRequest(productId, {
        contact_method: contactMethod,
        contact_value: contactValue.trim() || null,
        message: message.trim() || null,
      });
      setRequestNotice("Заявка создана. Админ вручную проверит покупку и выдаст доступ, если всё подтверждено.");
      setContactValue("");
      setMessage("");
      await loadProduct();
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setRequestNotice("Заявка уже есть. Обновили статус продукта.");
        await loadProduct();
      } else {
        setRequestError(error instanceof Error ? error.message : "Не удалось создать заявку.");
      }
    } finally {
      setIsRequesting(false);
    }
  }

  if (isLoading) return <LoadingState title="Загружаем продукт" />;
  if (notFound) return <EmptyState title="Продукт недоступен" description="Продукт не найден или не опубликован." />;
  if (error || !product) return <ErrorState title="Продукт недоступен" description="Не удалось получить продукт." />;

  return (
    <section className="community-detail">
      <Link className="community-detail__back" to="/app/products">Назад к продуктам</Link>
      <header className="community-detail__header">
        <div className="community-detail__meta">
          <span>{product.has_access ? "Доступ открыт" : "Материалы закрыты"}</span>
          <span>{price(product)}</span>
        </div>
        <h1>{product.title}</h1>
        <p>{product.description}</p>
      </header>
      {!product.has_access && product.has_locked_materials && (
        <article className="community-simple-card">
          <span>Locked</span>
          <strong>Материалы продукта закрыты</strong>
          <p>Оставьте заявку или напишите блогеру. Доступ выдаётся вручную после подтверждения покупки.</p>
          {product.support_url && <a href={product.support_url} target="_blank" rel="noreferrer">Поддержка</a>}
        </article>
      )}
      {!product.has_access && (
        <article className="community-simple-card">
          <span>Заявка на продукт</span>
          <strong>
            {product.purchase_request
              ? `Статус: ${requestStatusLabel(product.purchase_request.status)}`
              : "Оставить заявку на доступ"}
          </strong>
          {product.purchase_request ? (
            <>
              <p>
                Заявка создана {new Date(product.purchase_request.created_at).toLocaleDateString()}. Админ обработает её вручную.
              </p>
              {product.purchase_request.admin_note && <p>Комментарий админа: {product.purchase_request.admin_note}</p>}
            </>
          ) : (
            <div className="community-purchase-request-form">
              <label>
                Способ связи
                <select value={contactMethod} onChange={(event) => setContactMethod(event.target.value as typeof contactMethod)}>
                  <option value="telegram">Telegram</option>
                  <option value="phone">Телефон</option>
                  <option value="email">Email</option>
                  <option value="other">Другое</option>
                </select>
              </label>
              <label>
                Контакт
                <input
                  value={contactValue}
                  placeholder="@username или другой контакт"
                  onChange={(event) => setContactValue(event.target.value)}
                />
              </label>
              <label>
                Комментарий
                <textarea
                  rows={3}
                  value={message}
                  placeholder="Например: хочу купить продукт, оплату согласую в Telegram"
                  onChange={(event) => setMessage(event.target.value)}
                />
              </label>
              {requestError && <p className="community-detail__inline-error">{requestError}</p>}
              {requestNotice && <p className="community-admin-notice">{requestNotice}</p>}
              <button
                className="community-admin-button community-admin-button--primary"
                type="button"
                onClick={() => void submitPurchaseRequest()}
                disabled={isRequesting}
              >
                {isRequesting ? "Создаём заявку" : "Оставить заявку"}
              </button>
            </div>
          )}
          {requestNotice && product.purchase_request && <p className="community-admin-notice">{requestNotice}</p>}
        </article>
      )}
      <div className="community-admin-list">
        {product.materials.length === 0 ? (
          <EmptyState title="Открытых материалов нет" description="Материалы появятся после выдачи доступа или публикации открытого блока." />
        ) : (
          product.materials.map((material) => <MaterialCard key={material.id} material={material} />)
        )}
      </div>
    </section>
  );
}

function MaterialCard({ material }: { material: CommunityProductMaterial }) {
  return (
    <article className="community-admin-card">
      <div className="community-admin-card__meta">
        <span>{material.material_type}</span>
        <span>{material.is_locked ? "Закрытый" : "Открытый"}</span>
      </div>
      <h2>{material.title}</h2>
      {material.description && <p>{material.description}</p>}
      {material.content && <div className="community-detail__body">{material.content}</div>}
      {material.url && <a className="community-admin-button" href={material.url} target="_blank" rel="noreferrer">Открыть ссылку</a>}
      {material.file_url && <a className="community-admin-button" href={material.file_url} target="_blank" rel="noreferrer">Открыть материал</a>}
    </article>
  );
}
