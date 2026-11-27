import { useEffect, useState } from 'react';
import OrderList from './OrderList.jsx';
import { createOrder, getProducts } from '../services/apiService.js';

// Кабінет клієнта: каталог товарів, кошик та створення замовлення.
export default function ClientCatalogView({ user }) {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let isActive = true;
    getProducts()
      .then((data) => { if (isActive) setProducts(data); })
      .catch((err) => { if (isActive) setError(err.message); })
      .finally(() => { if (isActive) setIsLoading(false); });
    return () => { isActive = false; };
  }, []);

  function addToCart(productId) {
    setCart((current) => ({ ...current, [productId]: (current[productId] || 0) + 1 }));
    setError('');
    setMessage('');
  }

  async function handleOrder() {
    if (!cartCount || isSubmitting) return;
    setError('');
    setMessage('');
    setIsSubmitting(true);
    try {
      const items = Object.entries(cart).map(([productId, quantity]) => ({
        product_id: Number(productId),
        quantity,
      }));
      const order = await createOrder(user.id, items);
      setMessage(`Замовлення №${order.id} створено. Статус: ${order.status}.`);
      setCart({});
    } catch (err) {
      setError(err.message || 'Не вдалося створити замовлення.');
    } finally {
      setIsSubmitting(false);
    }
  }

  const cartCount = Object.values(cart).reduce((sum, quantity) => sum + quantity, 0);
  const cartTotal = Object.entries(cart).reduce((sum, [productId, quantity]) => {
    const product = products.find((item) => item.id === Number(productId));
    return sum + (product ? product.price * quantity : 0);
  }, 0);

  return (
    <section aria-label="Каталог товарів">
      <h2>Каталог</h2>
      {isLoading && <p role="status">Завантаження товарів…</p>}
      {error && <p role="alert" className="error">{error}</p>}
      {!isLoading && !error && products.length === 0 && (
        <p className="muted">Товарів поки немає.</p>
      )}

      <ul className="catalog-list">
        {products.map((product) => (
          <li key={product.id} className="catalog-item">
            <div>
              <strong>{product.name}</strong>
              {product.description && <p className="muted">{product.description}</p>}
              <p className="muted">{product.price} грн</p>
            </div>
            <button type="button" onClick={() => addToCart(product.id)} disabled={isLoading}>
              У кошик
            </button>
          </li>
        ))}
      </ul>

      {cartCount > 0 && (
        <div className="cart-bar">
          <span>Кошик: {cartCount} шт. — {cartTotal.toFixed(2)} грн</span>
          <button type="button" onClick={handleOrder} disabled={isSubmitting}>
            {isSubmitting ? 'Оформлення…' : 'Оформити замовлення'}
          </button>
        </div>
      )}

      {message && <p role="status" className="success">{message}</p>}
    </section>
  );
}
