import { useEffect, useState } from 'react';
import { createUser, deleteUser, getUsers, updateUserRole } from '../services/apiService.js';

const EMPTY_FORM = { username: '', password: '', email: '', phone: '', role: 'employee' };
const ROLE_LABELS = {
  client: 'Клієнт',
  employee: 'Працівник',
  admin: 'Адміністратор',
  superadmin: 'Головний адмін',
};

export default function SuperAdminUsersView({ user }) {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function loadUsers(query = search, showLoading = true) {
    setError('');
    if (showLoading) setIsLoading(true);
    try {
      setUsers(await getUsers({ search: query }));
    } catch (err) {
      setError(err.message || 'Не вдалося завантажити користувачів.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadUsers('');
  }, []);

  async function handleSearch(event) {
    event.preventDefault();
    const query = searchInput.trim();
    setSearch(query);
    await loadUsers(query);
  }

  async function handleCreate(event) {
    event.preventDefault();
    setError('');
    setMessage('');
    setIsSaving(true);
    try {
      await createUser({
        username: form.username.trim(),
        password: form.password,
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        role: form.role,
      });
      setForm(EMPTY_FORM);
      setMessage('Обліковий запис створено.');
      await loadUsers(search, false);
    } catch (err) {
      setError(err.message || 'Не вдалося створити користувача.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRoleChange(targetUser, role) {
    if (targetUser.role === role) return;
    setError('');
    setMessage('');
    try {
      await updateUserRole(targetUser.id, role);
      setMessage(`Роль користувача ${targetUser.username} змінено.`);
      await loadUsers(search, false);
    } catch (err) {
      setError(err.message || 'Не вдалося змінити роль.');
    }
  }

  async function handleDelete(targetUser) {
    if (!window.confirm(`Видалити користувача «${targetUser.username}»?`)) return;
    setError('');
    setMessage('');
    try {
      await deleteUser(targetUser.id);
      setMessage(`Користувача ${targetUser.username} видалено.`);
      await loadUsers(search, false);
    } catch (err) {
      setError(err.message || 'Не вдалося видалити користувача.');
    }
  }

  function updateForm(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  return (
    <section aria-label="Керування користувачами">
      <h2>Облікові записи</h2>
      {error && <p role="alert" className="error">{error}</p>}
      {message && <p role="status" className="success">{message}</p>}

      <form className="data-form" onSubmit={handleCreate}>
        <h3>Створити обліковий запис</h3>
        <label>
          Логін
          <input
            value={form.username}
            onChange={(event) => updateForm('username', event.target.value)}
            minLength={3}
            maxLength={50}
            required
          />
        </label>
        <label>
          Початковий пароль
          <input
            type="password"
            value={form.password}
            onChange={(event) => updateForm('password', event.target.value)}
            minLength={6}
            required
          />
        </label>
        <label>
          Роль
          <select value={form.role} onChange={(event) => updateForm('role', event.target.value)}>
            <option value="employee">Працівник</option>
            <option value="admin">Адміністратор</option>
            <option value="superadmin">Головний адмін</option>
            <option value="client">Клієнт</option>
          </select>
        </label>
        <label>
          Email (необов’язково)
          <input type="email" value={form.email} onChange={(event) => updateForm('email', event.target.value)} />
        </label>
        <label>
          Телефон (необов’язково)
          <input type="tel" value={form.phone} onChange={(event) => updateForm('phone', event.target.value)} />
        </label>
        <button type="submit" disabled={isSaving}>
          {isSaving ? 'Створення…' : 'Створити користувача'}
        </button>
      </form>

      <form className="search-form" onSubmit={handleSearch}>
        <label htmlFor="user-search">Пошук за логіном, email або телефоном</label>
        <div className="search-row">
          <input
            id="user-search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Введіть запит"
          />
          <button type="submit" disabled={isLoading}>Знайти</button>
          {search && (
            <button type="button" onClick={() => { setSearchInput(''); setSearch(''); loadUsers(''); }}>
              Очистити
            </button>
          )}
        </div>
      </form>

      {isLoading && <p role="status">Завантаження користувачів…</p>}
      {!isLoading && users.length === 0 && <p className="muted">Користувачів не знайдено.</p>}

      <ul className="user-list">
        {users.map((entry) => {
          const isCurrentUser = entry.id === user.id;
          return (
            <li key={entry.id} className="user-card">
              <div className="user-details">
                <strong>{entry.username}{isCurrentUser ? ' (ви)' : ''}</strong>
                <span>{ROLE_LABELS[entry.role] || entry.role}</span>
                {entry.email && <span className="muted">{entry.email}</span>}
                {entry.phone && <span className="muted">{entry.phone}</span>}
              </div>
              <div className="item-actions">
                {isCurrentUser ? (
                  <span className="muted">Власний акаунт захищено</span>
                ) : (
                  <>
                    <label>
                      Роль
                      <select
                        value={entry.role}
                        onChange={(event) => handleRoleChange(entry, event.target.value)}
                      >
                        {Object.entries(ROLE_LABELS).map(([role, label]) => (
                          <option key={role} value={role}>{label}</option>
                        ))}
                      </select>
                    </label>
                    <button type="button" className="danger-button" onClick={() => handleDelete(entry)}>
                      Видалити
                    </button>
                  </>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
