// REST API сервіс для FastAPI: авторизація, каталог, замовлення, статистика та користувачі.

const TOKEN_KEY = 'token';
const USER_KEY = 'user';

async function request(path, method = 'GET', body) {
  const headers = {};
  const token = localStorage.getItem(TOKEN_KEY);

  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = 'Bearer ' + token;

  let response;
  try {
    response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error('Не вдалося з’єднатися з сервером. Перевірте, чи запущено бекенд.');
  }

  const data = await response.json().catch(() => null);

  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.dispatchEvent(new Event('auth-expired'));
  }

  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join(', ')
      : detail;
    throw new Error(message || 'Помилка запиту (' + response.status + ').');
  }

  return data;
}

// --- Авторизація ---

export async function login(username, password) {
  const data = await request('/login', 'POST', { username, password });
  localStorage.setItem(TOKEN_KEY, data.token);
  localStorage.setItem(USER_KEY, JSON.stringify(data.user));
  return data.user;
}

export async function register(username, password, email, phone) {
  return request('/register', 'POST', {
    username,
    password,
    email: email || null,
    phone: phone || null,
  });
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

export function getProducts() {
  return request('/products');
}

export function createProduct(product) {
  return request('/products', 'POST', product);
}

export function updateProduct(productId, changes) {
  return request('/products/' + productId, 'PATCH', changes);
}

export function deleteProduct(productId) {
  return request('/products/' + productId, 'DELETE');
}

// --- Замовлення ---

export function createOrder(userId, items) {
  return request('/orders', 'POST', { user_id: userId, items });
}

export async function getOrders({ search = '', status = '', userId = '' } = {}) {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (status) params.set('status', status);
  if (userId) params.set('user_id', userId);

  const query = params.toString();
  return request('/orders' + (query ? '?' + query : ''));
}

export function updateOrderStatus(orderId, status) {
  return request('/orders/' + orderId + '/status', 'PATCH', { status });
}

// --- Статистика ---

export function getStats() {
  return request('/stats');
}

// --- Користувачі (superadmin) ---

export function getUsers({ search = '', role = '' } = {}) {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (role) params.set('role', role);

  const query = params.toString();
  return request('/users' + (query ? '?' + query : ''));
}

export function createUser(user) {
  return request('/users', 'POST', user);
}

export function updateUserRole(userId, role) {
  return request('/users/' + userId, 'PATCH', { role });
}

export function deleteUser(userId) {
  return request('/users/' + userId, 'DELETE');
}
