import { useEffect, useState } from 'react';
import OrderList from './OrderList.jsx';
import { getOrders, getProducts, updateOrderStatus } from '../services/apiService.js';

function formatOrders(orders, products) {
  return orders.map((order) => ({
    id: order.id,
    userId: order.user_id,
    customerName: 'Клієнт #' + order.user_id,
    status: order.status,
    totalPrice: order.total_price,
    products: order.items.map((item) => {
      const product = products.find((entry) => entry.id === item.product_id);
      return {
        id: item.id,
        name: product ? product.name : 'Товар #' + item.product_id,
        quantity: item.quantity,
      };
    }),
  }));
}

// Кабінет працівника: пошук замовлень та зміна статусів згідно з FSM.
export default function EmployeeOrdersView() {
  const [orders, setOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingOrderId, setUpdatingOrderId] = useState(null);

  async function loadOrders(query = search, showLoading = true) {
    setError('');
    if (showLoading) setIsLoading(true);
    try {
      const data = await getOrders({ search: query });
      setOrders(formatOrders(data, products));
    } catch (err) {
      setError(err.message || 'Не вдалося завантажити замовлення.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    let isActive = true;
    Promise.all([getProducts(), getOrders()])
      .then(([productData, orderData]) => {
        if (!isActive) return;
        setProducts(productData);
        setOrders(formatOrders(orderData, productData));
      })
      .catch((err) => { if (isActive) setError(err.message || 'Не вдалося завантажити дані.'); })
      .finally(() => { if (isActive) setIsLoading(false); });
    return () => { isActive = false; };
  }, []);

  async function handleSearch(event) {
    event.preventDefault();
    const query = searchInput.trim();
    setSearch(query);
    await loadOrders(query);
  }

  async function handleStatusChange(orderId, nextStatus) {
    setError('');
    setUpdatingOrderId(orderId);
    try {
      await updateOrderStatus(orderId, nextStatus);
      await loadOrders(search, false);
    } catch (err) {
      setError(err.message || 'Не вдалося змінити статус.');
    } finally {
      setUpdatingOrderId(null);
    }
  }

  return (
    <section aria-label="Опрацювання замовлень">
      <h2>Замовлення</h2>
      <form className="search-form" onSubmit={handleSearch}>
        <label htmlFor="order-search">Пошук за номером замовлення або логіном клієнта</label>
        <div className="search-row">
          <input
            id="order-search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Номер або логін"
          />
          <button type="submit" disabled={isLoading}>Знайти</button>
          {search && (
            <button type="button" onClick={() => { setSearchInput(''); setSearch(''); loadOrders(''); }}>
              Очистити
            </button>
          )}
        </div>
      </form>

      {error && <p role="alert" className="error">{error}</p>}
      {isLoading && <p role="status">Завантаження замовлень…</p>}
      {!isLoading && !error && (
        <OrderList
          orders={orders}
          onStatusChange={handleStatusChange}
          updatingOrderId={updatingOrderId}
        />
      )}
    </section>
  );
}
