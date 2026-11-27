import { useEffect, useState } from 'react';
import {
  createProduct,
  deleteProduct,
  getProducts,
  getStats,
  updateProduct,
} from '../services/apiService.js';

const EMPTY_FORM = { name: '', price: '', description: '' };

export default function AdminProductsView() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [editingPrice, setEditingPrice] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [statsError, setStatsError] = useState('');
  const [message, setMessage] = useState('');

  async function loadData(showLoading = true) {
    setError('');
    setStatsError('');
    if (showLoading) setIsLoading(true);
    const [productResult, statsResult] = await Promise.allSettled([getProducts(), getStats()]);

    if (productResult.status === 'fulfilled') {
      setProducts(productResult.value);
    } else {
      setError(productResult.reason.message || 'Не вдалося завантажити каталог.');
    }

    if (statsResult.status === 'fulfilled') {
      setStats(statsResult.value);
    } else {
      setStats(null);
      setStatsError(statsResult.reason.message || 'Не вдалося завантажити статистику.');
    }
    setIsLoading(false);
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    setIsSaving(true);
    try {
      await createProduct({
        name: form.name.trim(),
        price: Number(form.price),
        description: form.description.trim() || null,
      });
      setForm(EMPTY_FORM);
      setMessage('Товар додано до каталогу.');
      await loadData(false);
    } catch (err) {
      setError(err.message || 'Не вдалося додати товар.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handlePriceUpdate(productId) {
    setError('');
    setMessage('');
    setIsSaving(true);
    try {
      await updateProduct(productId, { price: Number(editingPrice) });
      setEditingId(null);
      setEditingPrice('');
      setMessage('Ціну оновлено.');
      await loadData(false);
    } catch (err) {
      setError(err.message || 'Не вдалося змінити ціну.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(product) {
    if (!window.confirm(`Видалити товар «${product.name}»?`)) return;
    setError('');
    setMessage('');
    try {
      await deleteProduct(product.id);
      setMessage('Товар видалено.');
      await loadData();
    } catch (err) {
      setError(err.message || 'Не вдалося видалити товар.');
    }
  }

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <section aria-label="Керування товарами">
      <h2>Номенклатура</h2>
      {error && <p role="alert" className="error">{error}</p>}
      {message && <p role="status" className="success">{message}</p>}

      <form className="data-form" onSubmit={handleCreate}>
        <h3>Додати товар</h3>
        <label>
          Назва
          <input
            value={form.name}
            onChange={(event) => updateForm('name', event.target.value)}
            maxLength={100}
            required
          />
        </label>
        <label>
          Ціна (грн)
          <input
            type="number"
            value={form.price}
            onChange={(event) => updateForm('price', event.target.value)}
            min="0.01"
            step="0.01"
            required
          />
        </label>
        <label>
          Опис
          <textarea
            value={form.description}
            onChange={(event) => updateForm('description', event.target.value)}
            rows="2"
          />
        </label>
        <button type="submit" disabled={isSaving}>
          {isSaving ? 'Збереження…' : 'Додати товар'}
        </button>
      </form>

      {isLoading && <p role="status">Завантаження каталогу…</p>}
      {!isLoading && products.length === 0 && <p className="muted">Товарів поки немає.</p>}
      <ul className="catalog-list">
        {products.map((product) => (
          <li key={product.id} className="catalog-item">
            <div className="catalog-product-info">
              <strong>{product.name}</strong>
              {product.description && <p className="muted">{product.description}</p>}
              {editingId === product.id ? (
                <form
                  className="inline-form"
                  onSubmit={(event) => { event.preventDefault(); handlePriceUpdate(product.id); }}
                >
                  <label>
                    Нова ціна (грн)
                    <input
                      type="number"
                      value={editingPrice}
                      onChange={(event) => setEditingPrice(event.target.value)}
                      min="0.01"
                      step="0.01"
                      required
                    />
                  </label>
                  <button type="submit" disabled={isSaving}>Зберегти</button>
                  <button type="button" onClick={() => setEditingId(null)}>Скасувати</button>
                </form>
              ) : (
                <p className="muted">{Number(product.price).toFixed(2)} грн</p>
              )}
            </div>
            <div className="item-actions">
              {editingId !== product.id && (
                <button
                  type="button"
                  onClick={() => { setEditingId(product.id); setEditingPrice(String(product.price)); }}
                >
                  Змінити ціну
                </button>
              )}
              <button
                type="button"
                className="danger-button"
                onClick={() => handleDelete(product)}
              >
                Видалити
              </button>
            </div>
          </li>
        ))}
      </ul>

      <section className="stats-section" aria-label="Фінансові показники">
        <h2>Фінансові показники</h2>
        {statsError && <p role="alert" className="error">{statsError}</p>}
        {stats?.has_data ? (
          <>
            <div className="stats-grid">
              <article className="stat-card"><span>Загальний виторг</span><strong>{Number(stats.total_revenue).toFixed(2)} грн</strong></article>
              <article className="stat-card"><span>Усього замовлень</span><strong>{stats.total_orders}</strong></article>
              <article className="stat-card"><span>Рахунків виставлено</span><strong>{stats.invoiced_orders_count}</strong></article>
              <article className="stat-card"><span>Середній чек</span><strong>{Number(stats.average_check).toFixed(2)} грн</strong></article>
            </div>
            <h3>Замовлення за статусом</h3>
            <ul className="stats-list">
              {Object.entries(stats.orders_by_status).map(([status, count]) => (
                <li key={status}><span>{status}</span><strong>{count}</strong></li>
              ))}
            </ul>
            <h3>Популярні товари</h3>
            {stats.top_products.length ? (
              <ul className="stats-list">
                {stats.top_products.map((product) => (
                  <li key={product.product_id}>
                    <span>{product.name} — {product.total_quantity} шт. у {product.orders_count} замовл.</span>
                    <strong>{Number(product.total_amount).toFixed(2)} грн</strong>
                  </li>
                ))}
              </ul>
            ) : <p className="muted">Даних про продажі товарів ще немає.</p>}
          </>
        ) : (
          <p className="muted">{stats ? 'Даних для звіту ще немає.' : 'Статистику не завантажено.'}</p>
        )}
      </section>
    </section>
  );
}
