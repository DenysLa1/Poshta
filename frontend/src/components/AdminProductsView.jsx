import { useEffect, useState } from 'react';
import { getProducts, getStats } from '../services/apiService.js';

// Каркас кабінету адміністратора: перелік номенклатури та фінансова статистика.
// Додавання товарів і зміна цін — наступний крок (див. Trello, Спринт 3).
export default function AdminProductsView() {
  const [products, setProducts] = useState([]);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getProducts()
      .then(setProducts)
      .catch(() => setError('Не вдалося завантажити товари.'));

    // Статистики на бекенді може ще не бути — тоді просто не показуємо її.
    getStats().then(setStats).catch(() => setStats(null));
  }, []);

  return (
    <section aria-label="Керування товарами">
      <h2>Номенклатура</h2>
      {error && <p role="alert" className="error">{error}</p>}
      {products.length === 0 && !error && <p className="muted">Товарів поки немає.</p>}

      <ul className="catalog-list">
        {products.map((product) => (
          <li key={product.id} className="catalog-item">
            <div>
              <strong>{product.name}</strong>
              <p className="muted">{product.price} грн</p>
            </div>
            <span className="muted">id: {product.id}</span>
          </li>
        ))}
      </ul>

      <h2>Фінансові показники</h2>
      {stats ? (
        <ul>
          {Object.entries(stats).map(([key, value]) => (
            <li key={key}>{key}: {value}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">Статистика з’явиться після реалізації GET /stats на бекенді.</p>
      )}
    </section>
  );
}
