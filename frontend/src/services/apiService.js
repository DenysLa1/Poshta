// 1. Що це: Єдиний сервіс звертань фронтенду до REST API бекенду (FastAPI).
// 2. Для чого: Виконувати HTTP-запити через fetch і зберігати дані поточного користувача.
// 3. Призначення: Авторизація, каталог товарів, замовлення, зміна статусів та статистика.

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

// Тимчасовий демо-вхід для локальної розробки (поки на бекенді немає /auth/login).
// Виставте true — і вхід спрацює без бекенда: логін = роль (client, employee,
// admin, superadmin), пароль будь-який. Перед релізом повернути false!
const DEMO_LOGIN = false;

// Простий обгорташ навколо fetch: додає JSON-заголовки та токен авторизації.
// Шляхи відносні — у режимі dev Vite проксіює їх на http://localhost:8000
// (див. vite.config.js), тому проблем CORS немає.
async function request(path, method, body) {
  const headers = { 'Content-Type': 'application/json' };

  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers.Authorization = 'Bearer ' + token;

  const response = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || 'Помилка запиту (' + response.status + ')');
  }

  return response.json();
}

// --- Авторизація ---

export async function login(username, password) {
  if (DEMO_LOGIN) {
    const demoUser = { id: 1, username, role: username };
    localStorage.setItem(USER_KEY, JSON.stringify(demoUser));
    return demoUser;
  }

  // Очікувана відповідь: { token, user: { id, username, role } }
  const data = await request('/login', 'POST', { username, password });
  localStorage.setItem(TOKEN_KEY, data.token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  return data.user;
}

// Реєстрація нового клієнта. Бекенд очікує email АБО phone (хоча б одне).
export async function register(username, password, email, phone) {
  return request('/register', 'POST', { username, password, email, phone });
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

// --- Каталог ---

export async function getProducts() {
  return request('/products', 'GET');
}

// --- Замовлення ---

// items: [{ product_id, quantity }]
export async function createOrder(userId, items) {
  return request('/orders', 'POST', { user_id: userId, items });
}

export async function getOrders() {
  const orders = await request('/orders', 'GET');

  // Перетворюємо відповідь бекенду у формат, який очікують компоненти.
  // Поки бекенд не повертає імена — показуємо номери (див. Trello, Спринт 2).
  return orders.map((order) => ({
    id: order.id,
    customerName: 'Клієнт #' + order.user_id,
    status: order.status,
    products: order.items.map((item) => ({
      id: item.product_id,
      name: 'Товар #' + item.product_id,
      quantity: item.quantity,
    })),
  }));
}

export async function updateOrderStatus(orderId, status) {
  return request('/orders/' + orderId + '/status', 'PATCH', { status });
}

// --- Статистика (для адміністратора) ---

export async function getStats() {
  return request('/stats', 'GET');
}
