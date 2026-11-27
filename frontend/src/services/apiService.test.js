import test, { afterEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  deleteProduct,
  getOrders,
  login,
  logout,
  register,
} from './apiService.js';

const originalFetch = globalThis.fetch;
const originalStorage = globalThis.localStorage;
const originalWindow = globalThis.window;

function setupBrowserMocks() {
  const values = new Map();
  globalThis.localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
  };

  const events = [];
  globalThis.window = {
    dispatchEvent: (event) => events.push(event.type),
  };

  return { values, events };
}

function jsonResponse(data, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  };
}

afterEach(() => {
  globalThis.fetch = originalFetch;
  if (originalStorage === undefined) delete globalThis.localStorage;
  else globalThis.localStorage = originalStorage;
  if (originalWindow === undefined) delete globalThis.window;
  else globalThis.window = originalWindow;
});

test('login sends credentials and persists token and user', async () => {
  const { values } = setupBrowserMocks();
  let requestOptions;
  globalThis.fetch = async (_url, options) => {
    requestOptions = options;
    return jsonResponse({ token: 'test-token', user: { id: 7, username: 'pavlo', role: 'employee' } });
  };

  const user = await login('pavlo', 'secret');

  assert.equal(requestOptions.method, 'POST');
  assert.deepEqual(JSON.parse(requestOptions.body), { username: 'pavlo', password: 'secret' });
  assert.equal(values.get('token'), 'test-token');
  assert.deepEqual(JSON.parse(values.get('user')), user);
});

test('register posts separate optional email and phone fields', async () => {
  setupBrowserMocks();
  let requestBody;
  globalThis.fetch = async (_url, options) => {
    requestBody = JSON.parse(options.body);
    return jsonResponse({ id: 3, username: 'new-client', role: 'client' }, 201);
  };

  await register('new-client', 'secret1', 'client@example.test', '');

  assert.deepEqual(requestBody, {
    username: 'new-client',
    password: 'secret1',
    email: 'client@example.test',
    phone: null,
  });
});

test('getOrders sends query filters and bearer token', async () => {
  const { values } = setupBrowserMocks();
  values.set('token', 'test-token');
  let requestUrl;
  let requestOptions;
  globalThis.fetch = async (url, options) => {
    requestUrl = url;
    requestOptions = options;
    return jsonResponse([]);
  };

  await getOrders({ search: '#12', status: 'Registered' });

  assert.equal(requestUrl, '/orders?search=%2312&status=Registered');
  assert.equal(requestOptions.headers.Authorization, 'Bearer test-token');
});

test('deleteProduct sends DELETE to the product resource', async () => {
  setupBrowserMocks();
  let requestUrl;
  let requestOptions;
  globalThis.fetch = async (url, options) => {
    requestUrl = url;
    requestOptions = options;
    return jsonResponse({ detail: 'Deleted', id: 9 });
  };

  const result = await deleteProduct(9);

  assert.equal(requestUrl, '/products/9');
  assert.equal(requestOptions.method, 'DELETE');
  assert.deepEqual(result, { detail: 'Deleted', id: 9 });
});

test('401 clears session and signals the application', async () => {
  const { values, events } = setupBrowserMocks();
  values.set('token', 'expired-token');
  values.set('user', '{"id":1}');
  globalThis.fetch = async () => jsonResponse({ detail: 'Expired' }, 401);

  await assert.rejects(getOrders(), /Expired/);
  assert.equal(values.has('token'), false);
  assert.equal(values.has('user'), false);
  assert.deepEqual(events, ['auth-expired']);

  // logout remains idempotent after an expired session.
  logout();
});
