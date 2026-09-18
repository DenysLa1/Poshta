import OrderItem from './OrderItem.jsx';

export default function OrderList({ orders }) {
  if (orders.length === 0) return <p>Замовлень поки немає.</p>;

  return (
    <section aria-label="Список замовлень">
      <p className="order-count">Усього замовлень: {orders.length}</p>
      <ul className="order-list">
        {orders.map((order) => (
          <li key={order.id}>
            <OrderItem order={order} />
          </li>
        ))}
      </ul>
    </section>
  );
}