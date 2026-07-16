import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../../../shared/ui/EmptyState";
import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import { listCommunityProducts } from "../api";
import type { CommunityProduct } from "../types";

function price(product: CommunityProduct): string {
  const parts = [];
  if (product.price_usd) parts.push(`$${product.price_usd}`);
  if (product.price_rub) parts.push(`${product.price_rub} RUB`);
  return parts.join(" / ") || "Цена по запросу";
}

export function CommunityProductsPage() {
  const [products, setProducts] = useState<CommunityProduct[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    listCommunityProducts()
      .then(setProducts)
      .catch(() => setError(true))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <LoadingState title="Загружаем продукты" />;
  if (error) return <ErrorState title="Продукты недоступны" description="Не удалось получить каталог продуктов." />;
  if (products.length === 0) return <EmptyState title="Продукты пока не опубликованы" description="Каталог появится после публикации продуктов." />;

  return (
    <section className="community-products">
      <header className="community-exchanges__header">
        <span>GlobalGreenInvest</span>
        <h1>Продукты</h1>
      </header>
      <div className="community-exchange-grid">
        {products.map((product) => (
          <article className="community-exchange-card" key={product.id}>
            {product.cover_url && <img src={product.cover_url} alt="" />}
            <div className="community-exchange-card__body">
              <h2>{product.title}</h2>
              <p>{product.short_description}</p>
              <div className="community-exchange-card__promo">{price(product)}</div>
              <div className="community-dashboard-badge">{product.has_access ? "Доступ открыт" : "Материалы закрыты"}</div>
            </div>
            <Link className="community-admin-button community-admin-button--primary" to={`/app/products/${product.id}`}>
              {product.has_access ? "Открыть →" : "Подробнее →"}
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}
