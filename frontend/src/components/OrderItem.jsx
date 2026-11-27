import { STATUS_LABELS, canTransition } from '../orderRules.js';

const ACTIONS = [
  { status: 'Registered', label: 'Зареєструвати' },
  { status: 'Granted', label: 'Погодити' },
  { status: 'Shipped', label: 'Відправити' },
  { status: 'Invoiced', label: 'Виставити рахунок' },
  { status: 'Cancelled', label: 'Скасувати' },
];

export default function OrderItem({ order, onStatusChange, isUpdating = false }) {
  const nextActions = ACTIONS.filter((action) => canTransition(order.status, action.status));

  return (
    <article className="order-card">
      <header className="order-header">
        <div>
          <h3>Замовлення №{order.id}</h3>
          <p className="customer">{order.customerName}</p>
        </div>
        <span className={`status status-${order.status}`}>
          {STATUS_LABELS[order.status] || order.status}
        </span>
      </header>
      {order.totalPrice !== undefined && (
        <p className="order-total">Сума: {Number(order.totalPrice).toFixed(2)} грн</p>
      )}

      <h4>Товари</h4>
      {order.products.length > 0 ? (
        <ul className="product-list">
          {order.products.map((product) => (
            <li key={product.id}>{product.name} — {product.quantity} шт.</li>
          ))}
        </ul>
      ) : (
        <p className="muted">Позицій у замовленні немає.</p>
      )}

      {nextActions.length > 0 && onStatusChange && (
        <div className="order-actions">
          {nextActions.map((action) => (
            <button
              key={action.status}
              type="button"
              disabled={isUpdating}
              onClick={() => onStatusChange(order.id, action.status)}
            >
              {isUpdating ? 'Оновлення…' : action.label}
            </button>
          ))}
        </div>
      )}
    </article>
  );
}
