import { useEffect, useState } from 'react';
import { getProducts, createOrder } from '../services/apiService.js';

// Кабінет клієнта: каталог товарів, кошик та оформлення замовлення.
// Клієнт НЕ бачить і не може змінювати статуси замовлень.
export default function ClientCatalogView({ user }) {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({}); // { [id товару]: кількість }
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    getProducts()
      .then(setProducts)
      .catch(() => setError('Не вдалося завантажити товари.'))
      .finally(() => setIsLoading(false));
  }, []);

  function addToCart(productId) {
    setCart((current) => ({ ...current, [productId]: (current[productId] || 0) + 1 }));
  }

  async function handleOrder() {
    setError('');
    setMessage('');
    try {
      const items = Object.entries(cart).map(([productId, quantity]) => ({
        product_id: Number(productId),
        quantity,
      }));
      const order = await createOrder(user.id, items);
      setMessage('Замовлення №' + order.id + ' створено. Статус: Нове.');
      setCart({});
    } catch (err) {
      setError(err.message || 'Не вдалося створити замовлення.');
    }
  }

  // Кількість товарів у кошику та їхня сумарна вартість.
  const cartCount = Object.values(cart).reduce((sum, quantity) => sum + quantity, 0);
  const cartTotal = Object.entries(cart).reduce((sum, [productId, quantity]) => {
    const product = products.find((p) => p.id === Number(productId));
    return sum + (product ? product.price * quantity : 0);
  }, 0);

  return (
    <section aria-label="Каталог товарів">
      <h2>Каталог</h2>

      {isLoading && <p role="status">Завантаження товарів…</p>}
      {error && <p role="alert" className="error">{error}</p>}
      {products.length === 0 && !isLoading && !error && (
        <p className="muted">Товарів поки немає.</p>
      )}

      <ul className="catalog-list">
        {products.map((product) => (
          <li key={product.id} className="catalog-item">
            <div>
              <strong>{product.name}</strong>
              <p className="muted">{product.price} грн</p>
            </div>
            <button type="button" onClick={() => addToCart(product.id)}>
              У кошик
            </button>
          </li>
        ))}
      </ul>

      {cartCount > 0 && (
        <div className="cart-bar">
          <span>Кошик: {cartCount} шт. — {cartTotal} грн</span>
          <button type="button" onClick={handleOrder}>
            Оформити замовлення
          </button>
        </div>
      )}

      {message && <p className="success">{message}</p>}
    </section>
  );
}
