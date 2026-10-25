import { useState } from 'react';
import LoginView from './components/LoginView.jsx';
import ClientCatalogView from './components/ClientCatalogView.jsx';
import EmployeeOrdersView from './components/EmployeeOrdersView.jsx';
import AdminProductsView from './components/AdminProductsView.jsx';
import SuperAdminUsersView from './components/SuperAdminUsersView.jsx';
import { logout, getCurrentUser } from './services/apiService.js';

// Кожна роль бачить лише свій екран (RBAC на фронтенді).
const VIEWS_BY_ROLE = {
  client: ClientCatalogView,
  employee: EmployeeOrdersView,
  admin: AdminProductsView,
  superadmin: SuperAdminUsersView,
};

const ROLE_LABELS = {
  client: 'Клієнт',
  employee: 'Працівник',
  admin: 'Адміністратор',
  superadmin: 'Головний адмін',
};

export default function App() {
  const [user, setUser] = useState(getCurrentUser());

  function handleLogout() {
    logout();
    setUser(null);
  }

  // Не увійшли (або роль невідома) — показуємо форму входу.
  if (!user || !VIEWS_BY_ROLE[user.role]) {
    return <LoginView onLogin={setUser} />;
  }

  const View = VIEWS_BY_ROLE[user.role];

  return (
    <main className="app">
      <header className="page-header">
        <p className="eyebrow">Пошта · {ROLE_LABELS[user.role]}</p>
        <div className="header-row">
          <h1>{ROLE_LABELS[user.role]}</h1>
          <div>
            <span className="muted">{user.username}</span>
            <button type="button" onClick={handleLogout}>Вийти</button>
          </div>
        </div>
      </header>

      <View user={user} />
    </main>
  );
}
