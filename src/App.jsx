import { useEffect, useState } from 'react';
import OrderList from './components/OrderList.jsx';
import { getOrders } from './services/ordersService.js';

export default function App() {
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isActive = true;

    async function loadOrders() {
      try {
        const data = await getOrders();
        if (isActive) setOrders(data);
      } catch {
        if (isActive) setError('Не вдалося завантажити замовлення.');
      } finally {
        if (isActive) setIsLoading(false);
      }
    }

    loadOrders();
    return () => { isActive = false; };
  }, []);

  return (
    <main className="app">
      <header className="page-header">
        <p className="eyebrow">Sprint 1 · Опрацювання замовлень</p>
        <h1>Замовлення</h1>
      </header>

      {isLoading && <p role="status">Завантаження замовлень…</p>}
      {error && <p role="alert" className="error">{error}</p>}
      {!isLoading && !error && <OrderList orders={orders} />}
    </main>
  );
}