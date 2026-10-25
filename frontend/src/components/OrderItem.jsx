import { STATUS_LABELS, canTransition } from '../orderRules.js';

// Дозволені дії працівника для кожного статусу (порядок FSM).
const ACTIONS = [
  { status: 'Registered', label: 'Зареєструвати' },
  { status: 'Granted', label: 'Погодити' },
  { status: 'Shipped', label: 'Відправити' },
  { status: 'Invoiced', label: 'Виставити рахунок' },
  { status: 'Cancelled', label: 'Скасувати' },
];

export default function OrderItem({ order, onStatusChange }) {
  const nextActions = ACTIONS.filter((action) =>
    canTransition(order.status, action.status)
  );

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

      {nextActions.length > 0 && onStatusChange && (
        <div className="order-actions">
          {nextActions.map((action) => (
            <button
              key={action.status}
              type="button"
              onClick={() => onStatusChange(order.id, action.status)}
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </article>
  );
}
