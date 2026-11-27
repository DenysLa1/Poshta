import { useEffect, useState } from 'react';
import OrderList from './OrderList.jsx';
import { getOrders, updateOrderStatus } from '../services/apiService.js';

// Кабінет працівника: список замовлень та покрокова зміна статусів (FSM).
// Працівник НЕ може створювати замовлення — лише опрацьовує наявні.
export default function EmployeeOrdersView() {
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadOrders() {
    setIsLoading(true);
    setError('');
    try {
      setOrders(await getOrders());
    } catch {
      setError('Не вдалося завантажити замовлення.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadOrders();
  }, []);

  async function handleStatusChange(orderId, nextStatus) {
    setError('');
    try {
      await updateOrderStatus(orderId, nextStatus);
      await loadOrders(); // Перезавантажуємо список після зміни статусу
    } catch (err) {
      setError(err.message || 'Не вдалося змінити статус.');
    }
  }

  return (
    <div>
      {isLoading && <p role="status">Завантаження замовлень…</p>}
      {error && <p role="alert" className="error">{error}</p>}
      {!isLoading && <OrderList orders={orders} onStatusChange={handleStatusChange} />}
    </div>
  );
}
