import OrderItem from './OrderItem.jsx';

export default function OrderList({ orders, onStatusChange, updatingOrderId = null }) {
  if (orders.length === 0) return <p>Замовлень не знайдено.</p>;

  return (
    <section aria-label="Список замовлень">
      <p className="order-count">Усього замовлень: {orders.length}</p>
      <ul className="order-list">
        {orders.map((order) => (
          <li key={order.id}>
            <OrderItem
              order={order}
              onStatusChange={onStatusChange}
              isUpdating={updatingOrderId === order.id}
            />
          </li>
        ))}
      </ul>
    </section>
  );
}
