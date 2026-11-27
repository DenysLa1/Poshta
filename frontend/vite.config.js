import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Проксі віддає запити фронтенду (наприклад, /products) на FastAPI,
// щоб у браузері не виникало CORS-помилок.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/products': 'http://localhost:8000',
      '/orders': 'http://localhost:8000',
      '/login': 'http://localhost:8000',
      '/register': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
    },
  },
});
