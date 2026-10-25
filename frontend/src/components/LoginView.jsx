import { useState } from 'react';
import { login, register } from '../services/apiService.js';

// Форма входу та реєстрації клієнта. Після успіху повідомляє App про користувача.
export default function LoginView({ onLogin }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(event) {
    event.preventDefault();
    setError('');

    // Бекенд вимагає хоча б один контакт — перевіряємо до запиту.
    if (isRegistering && !email && !phone) {
      setError('Вкажіть email або номер телефону.');
      return;
    }

    setIsLoading(true);
    try {
      if (isRegistering) await register(username, password, email, phone);
      const user = await login(username, password);
      onLogin(user);
    } catch (err) {
      setError(err.message || 'Не вдалося увійти.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <h1>{isRegistering ? 'Реєстрація клієнта' : 'Вхід до системи'}</h1>

      <label>
        Логін
        <input
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          autoComplete="username"
          required
        />
      </label>

      <label>
        Пароль
        <input
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete={isRegistering ? 'new-password' : 'current-password'}
          required
        />
      </label>

      {isRegistering && (
        <>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
            />
          </label>

          <label>
            Телефон
            <input
              type="tel"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
              autoComplete="tel"
            />
          </label>

          <p className="muted">Заповніть хоча б одне поле: email або телефон.</p>
        </>
      )}

      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Зачекайте…' : isRegistering ? 'Створити акаунт' : 'Увійти'}
      </button>

      <button
        type="button"
        className="link-button"
        onClick={() => setIsRegistering((current) => !current)}
      >
        {isRegistering ? 'У мене вже є акаунт' : 'Зареєструватися'}
      </button>

      {error && <p role="alert" className="error">{error}</p>}
    </form>
  );
}