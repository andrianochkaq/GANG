/// <reference types="vitest" />
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// The repository keeps one .env at its root, so Vite reads VITE_* from there.
export default defineConfig({
  plugins: [react()],
  envDir: '..',
  server: {
    host: true,
    port: 5173,
    strictPort: true,
  },
  test: {
    environment: 'jsdom',
    globals: false,
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
