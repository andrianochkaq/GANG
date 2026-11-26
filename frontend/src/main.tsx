import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';

import { installAuthInterceptor } from './api/authInterceptor';
import { apiClient } from './api/client';
import { refreshAccessToken } from './api/session';
import './i18n';
import { router } from './routes/router';
import { useAuthStore } from './store/authStore';
import './theme/global.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { refetchOnWindowFocus: true, retry: 1 },
  },
});

const AUTH_PATH_PREFIX = '/api/auth/';

installAuthInterceptor(apiClient, {
  getAccessToken: () => useAuthStore.getState().accessToken,
  refreshAccessToken: () => refreshAccessToken(),
  isAuthRequest: (url) => url.startsWith(AUTH_PATH_PREFIX),
});

const rootElement = document.getElementById('root');

if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    </StrictMode>,
  );
}
