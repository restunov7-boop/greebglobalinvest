import { useEffect, useMemo, useState } from "react";

import { ErrorState } from "../../../shared/ui/ErrorState";
import { LoadingState } from "../../../shared/ui/LoadingState";
import {
  createCommunityAdminProduct,
  createCommunityAdminProductMaterial,
  deleteCommunityAdminProductMaterial,
  hideCommunityAdminProduct,
  listCommunityAdminProductMaterials,
  listCommunityAdminProducts,
  updateCommunityAdminProduct,
  updateCommunityAdminProductMaterial,
} from "../api";
import { materialTypeLabel } from "../labels";
import type {
  CommunityAdminProduct,
  CommunityAdminProductMaterial,
  CommunityAdminProductMaterialPayload,
  CommunityAdminProductPayload,
} from "../types";

type ProductForm = CommunityAdminProductPayload & { id: string | null; price_usd_text: string; price_rub_text: string };
type MaterialForm = CommunityAdminProductMaterialPayload & { id: string | null; sort_order_text: string };

const productEmpty: ProductForm = {
  id: null,
  slug: "",
  title: "",
  short_description: "",
  description: "",
  cover_url: null,
  price_usd: null,
  price_rub: null,
  price_usd_text: "",
  price_rub_text: "",
  sort_order: 0,
  is_published: false,
  access_duration_type: "lifetime",
};

const materialEmpty: MaterialForm = {
  id: null,
  title: "",
  description: null,
  material_type: "text",
  content: null,
  url: null,
  file_url: null,
  sort_order: 0,
  sort_order_text: "0",
  is_locked: true,
};

function formFromProduct(product: CommunityAdminProduct): ProductForm {
  return {
    ...product,
    id: product.id,
    price_usd_text: product.price_usd ?? "",
    price_rub_text: product.price_rub ?? "",
  };
}

function productPayload(form: ProductForm): CommunityAdminProductPayload {
  return {
    slug: form.slug.trim(),
    title: form.title.trim(),
    short_description: form.short_description.trim(),
    description: form.description.trim(),
    cover_url: form.cover_url?.trim() || null,
    price_usd: form.price_usd_text.trim() || null,
    price_rub: form.price_rub_text.trim() || null,
    sort_order: Number(form.sort_order) || 0,
    is_published: form.is_published,
    access_duration_type: form.access_duration_type,
  };
}

function formFromMaterial(material: CommunityAdminProductMaterial): MaterialForm {
  return { ...material, id: material.id, sort_order_text: String(material.sort_order) };
}

function materialPayload(form: MaterialForm): CommunityAdminProductMaterialPayload {
  const text = (value: string | null) => value?.trim() || null;
  return {
    title: form.title.trim(),
    description: text(form.description),
    material_type: form.material_type,
    content: text(form.content),
    url: text(form.url),
    file_url: text(form.file_url),
    sort_order: Number(form.sort_order_text) || 0,
    is_locked: form.is_locked,
  };
}

export function CommunityAdminProductsPage() {
  const [products, setProducts] = useState<CommunityAdminProduct[]>([]);
  const [materials, setMaterials] = useState<CommunityAdminProductMaterial[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [productForm, setProductForm] = useState<ProductForm>(productEmpty);
  const [materialForm, setMaterialForm] = useState<MaterialForm>(materialEmpty);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const selectedProduct = useMemo(() => products.find((product) => product.id === selectedProductId) ?? null, [products, selectedProductId]);

  const loadProducts = async () => {
    setIsLoading(true);
    try {
      const payload = await listCommunityAdminProducts();
      setProducts(payload);
      if (!selectedProductId && payload[0]) setSelectedProductId(payload[0].id);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить продукты.");
    } finally {
      setIsLoading(false);
    }
  };

  const loadMaterials = async (productId: string | null) => {
    if (!productId) {
      setMaterials([]);
      return;
    }
    setMaterials(await listCommunityAdminProductMaterials(productId));
  };

  useEffect(() => {
    void loadProducts();
  }, []);

  useEffect(() => {
    void loadMaterials(selectedProductId);
  }, [selectedProductId]);

  const saveProduct = async () => {
    const payload = productPayload(productForm);
    if (!payload.slug || !payload.title || !payload.short_description || !payload.description) {
      setFormError("Заполните slug, название, краткое описание и описание продукта.");
      return;
    }
    setFormError(null);
    if (productForm.id) await updateCommunityAdminProduct(productForm.id, payload);
    else await createCommunityAdminProduct(payload);
    setProductForm(productEmpty);
    await loadProducts();
  };

  const saveMaterial = async () => {
    if (!selectedProductId) {
      setFormError("Выберите продукт для материалов.");
      return;
    }
    const payload = materialPayload(materialForm);
    if (!payload.title || !payload.material_type) {
      setFormError("Укажите название и тип материала.");
      return;
    }
    setFormError(null);
    if (materialForm.id) await updateCommunityAdminProductMaterial(selectedProductId, materialForm.id, payload);
    else await createCommunityAdminProductMaterial(selectedProductId, payload);
    setMaterialForm(materialEmpty);
    await loadMaterials(selectedProductId);
  };

  if (isLoading) return <LoadingState title="Загружаем продукты" />;
  if (error) return <ErrorState title="Продукты недоступны" description="Не удалось получить админский список продуктов." />;

  return (
    <section className="community-admin-content">
      <header className="community-admin-content__header">
        <div>
          <span>Админ-панель GlobalGreenInvest</span>
          <h1>Продукты</h1>
          <p>{products.length} продуктов</p>
        </div>
        <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => setProductForm(productEmpty)}>
          Создать продукт
        </button>
      </header>
      {formError && <p className="community-admin-inline-error">{formError}</p>}
      <div className="community-admin-grid">
        <div className="community-admin-list">
          {products.map((product) => (
            <article className="community-admin-card" key={product.id}>
              <div className="community-admin-card__meta">
                <span>{product.is_published ? "Опубликован" : "Скрыт"}</span>
                <span>Порядок {product.sort_order}</span>
              </div>
              <h2>{product.title}</h2>
              <p>{product.short_description}</p>
              <div className="community-admin-card__actions">
                <button type="button" onClick={() => { setSelectedProductId(product.id); setProductForm(formFromProduct(product)); }}>
                  Редактировать
                </button>
                <button type="button" onClick={() => setSelectedProductId(product.id)}>Материалы</button>
                <button type="button" onClick={() => void hideCommunityAdminProduct(product.id).then(loadProducts)} disabled={!product.is_published}>
                  Скрыть
                </button>
              </div>
            </article>
          ))}
        </div>
        <aside className="community-admin-form">
          <div className="community-admin-form__header">
            <span>{productForm.id ? "Редактирование" : "Создание"}</span>
            <h2>Продукт</h2>
          </div>
          <label>Slug<input value={productForm.slug} onChange={(event) => setProductForm({ ...productForm, slug: event.target.value })} /></label>
          <label>Название<input value={productForm.title} onChange={(event) => setProductForm({ ...productForm, title: event.target.value })} /></label>
          <label>Краткое описание<textarea rows={3} value={productForm.short_description} onChange={(event) => setProductForm({ ...productForm, short_description: event.target.value })} /></label>
          <label>Описание<textarea rows={5} value={productForm.description} onChange={(event) => setProductForm({ ...productForm, description: event.target.value })} /></label>
          <label>Cover URL<input value={productForm.cover_url ?? ""} onChange={(event) => setProductForm({ ...productForm, cover_url: event.target.value })} /></label>
          <label>USD<input value={productForm.price_usd_text} onChange={(event) => setProductForm({ ...productForm, price_usd_text: event.target.value })} /></label>
          <label>RUB<input value={productForm.price_rub_text} onChange={(event) => setProductForm({ ...productForm, price_rub_text: event.target.value })} /></label>
          <label>Порядок<input type="number" value={productForm.sort_order} onChange={(event) => setProductForm({ ...productForm, sort_order: Number(event.target.value) })} /></label>
          <label>Срок доступа<select value={productForm.access_duration_type} onChange={(event) => setProductForm({ ...productForm, access_duration_type: event.target.value })}><option value="lifetime">Без срока</option><option value="fixed_until">До даты</option><option value="custom">Индивидуально</option></select></label>
          <label className="community-admin-checkbox"><input type="checkbox" checked={productForm.is_published} onChange={(event) => setProductForm({ ...productForm, is_published: event.target.checked })} />Опубликован</label>
          <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => void saveProduct()}>Сохранить продукт</button>
        </aside>
      </div>
      <section className="community-admin-content">
        <header className="community-admin-content__header">
          <div>
            <span>Материалы</span>
            <h1>{selectedProduct?.title ?? "Выберите продукт"}</h1>
          </div>
          <button className="community-admin-button" type="button" onClick={() => setMaterialForm(materialEmpty)}>Новый материал</button>
        </header>
        <div className="community-admin-grid">
          <div className="community-admin-list">
            {materials.map((material) => (
              <article className="community-admin-card" key={material.id}>
                <div className="community-admin-card__meta"><span>{materialTypeLabel(material.material_type)}</span><span>{material.is_locked ? "Закрытый" : "Открытый"}</span></div>
                <h2>{material.title}</h2>
                <p>{material.description}</p>
                <div className="community-admin-card__actions">
                  <button type="button" onClick={() => setMaterialForm(formFromMaterial(material))}>Редактировать</button>
                  <button type="button" onClick={() => selectedProductId && void deleteCommunityAdminProductMaterial(selectedProductId, material.id).then(() => loadMaterials(selectedProductId))}>Скрыть</button>
                </div>
              </article>
            ))}
          </div>
          <aside className="community-admin-form">
            <div className="community-admin-form__header"><span>{materialForm.id ? "Редактирование" : "Создание"}</span><h2>Материал</h2></div>
            <label>Название<input value={materialForm.title} onChange={(event) => setMaterialForm({ ...materialForm, title: event.target.value })} /></label>
            <label>Описание<textarea rows={2} value={materialForm.description ?? ""} onChange={(event) => setMaterialForm({ ...materialForm, description: event.target.value })} /></label>
            <label>Тип<select value={materialForm.material_type} onChange={(event) => setMaterialForm({ ...materialForm, material_type: event.target.value as MaterialForm["material_type"] })}><option value="text">Текст</option><option value="link">Ссылка</option><option value="file_view">Файл</option><option value="external_site">Внешний сайт</option></select></label>
            <label>Контент<textarea rows={5} value={materialForm.content ?? ""} onChange={(event) => setMaterialForm({ ...materialForm, content: event.target.value })} /></label>
            <label>URL<input value={materialForm.url ?? ""} onChange={(event) => setMaterialForm({ ...materialForm, url: event.target.value })} /></label>
            <label>Файл URL<input value={materialForm.file_url ?? ""} onChange={(event) => setMaterialForm({ ...materialForm, file_url: event.target.value })} /></label>
            <label>Порядок<input type="number" value={materialForm.sort_order_text} onChange={(event) => setMaterialForm({ ...materialForm, sort_order_text: event.target.value })} /></label>
            <label className="community-admin-checkbox"><input type="checkbox" checked={materialForm.is_locked} onChange={(event) => setMaterialForm({ ...materialForm, is_locked: event.target.checked })} />Закрытый</label>
            <button className="community-admin-button community-admin-button--primary" type="button" onClick={() => void saveMaterial()}>Сохранить материал</button>
          </aside>
        </div>
      </section>
    </section>
  );
}
