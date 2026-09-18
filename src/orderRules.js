export const STATUS_LABELS = {
  NewOrder: 'Нове',
  Registered: 'Зареєстроване',
  Granted: 'Погоджене',
  Shipped: 'Відправлене',
  Invoiced: 'Рахунок виставлено',
  Cancelled: 'Скасоване',
};

const ALLOWED_TRANSITIONS = {
  NewOrder: ['Registered', 'Cancelled'],
  Registered: ['Granted', 'Shipped', 'Cancelled'],
  Granted: ['Shipped', 'Cancelled'],
  Shipped: ['Invoiced'],
  Invoiced: [],
  Cancelled: [],
};

export function canTransition(currentStatus, nextStatus) {
  return Object.hasOwn(ALLOWED_TRANSITIONS, currentStatus)
    && ALLOWED_TRANSITIONS[currentStatus].includes(nextStatus);
}

export function canAddProduct(status) {
  return Object.hasOwn(STATUS_LABELS, status) && status !== 'Cancelled';
}