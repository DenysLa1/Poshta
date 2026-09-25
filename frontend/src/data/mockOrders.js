export const mockOrders = [
  {
    id: 1001,
    customerName: 'Антон Гайдук',
    status: 'NewOrder',
    products: [{ id: 'p-1', name: 'Блокнот', quantity: 2 }],
  },
  {
    id: 1002,
    customerName: 'Андрій Бондар',
    status: 'Registered',
    products: [{ id: 'p-2', name: 'Клавіатура', quantity: 1 }],
  },
  {
    id: 1003,
    customerName: 'Марія Шевченко',
    status: 'Granted',
    products: [{ id: 'p-3', name: 'Комп’ютерна миша', quantity: 1 }],
  },
  {
    id: 1004,
    customerName: 'Дмитро Мельник',
    status: 'Shipped',
    products: [{ id: 'p-4', name: 'USB-кабель', quantity: 3 }],
  },
  {
    id: 1005,
    customerName: 'Ірина Ткаченко',
    status: 'Invoiced',
    products: [{ id: 'p-5', name: 'Монітор', quantity: 1 }],
  },
  {
    id: 1006,
    customerName: 'Максим Петренко',
    status: 'Cancelled',
    products: [],
  },
];