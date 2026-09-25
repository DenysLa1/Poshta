import { STATUS_LABELS } from '../orderRules.js';

export default function OrderItem({ order }) {
  return (
    <article className="order-card">
      <header className="order-header">
        <div>
          <h2>Замовлення №{order.id}</h2>
          <p className="customer">{order.customerName}</p>
        </div>
        <span className={`status status-${order.status}`}>
          {STATUS_LABELS[order.status]} ({order.status})
        </span>
      </header>

      <h3>Продукти</h3>
      {order.products.length > 0 ? (
        <ul className="product-list">
          {order.products.map((product) => (
            <li key={product.id}>
              {product.name} — {product.quantity} шт.
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">Продуктів поки немає.</p>
      )}
    </article>
  );
}