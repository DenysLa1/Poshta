import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/products': 'http://localhost:8000',
      '/orders': 'http://localhost:8000',
      '/login': 'http://localhost:8000',
      '/register': 'http://localhost:8000',
      '/auth': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/users': 'http://localhost:8000',
    },
  },
});
