import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const HTTP_UNAUTHORIZED = 401;

type RetriableConfig = InternalAxiosRequestConfig & { hasRetriedAuth?: boolean };

type AuthInterceptorOptions = {
  getAccessToken: () => string | null;
  refreshAccessToken: () => Promise<string | null>;
  // Requests that must never trigger a refresh (login, refresh itself).
  isAuthRequest: (url: string) => boolean;
};

// Sends the access token with every request; on a 401 refreshes it once and
// repeats the request. A failed refresh ends the session (the store turns
// anonymous and ProtectedRoute sends the user to the login screen).
export function installAuthInterceptor(client: AxiosInstance, options: AuthInterceptorOptions) {
  const requestId = client.interceptors.request.use((config) => {
    const token = options.getAccessToken();
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }
    return config;
  });

  const responseId = client.interceptors.response.use(undefined, async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined;
    const isUnauthorized = error.response?.status === HTTP_UNAUTHORIZED;
    if (
      !config ||
      !isUnauthorized ||
      config.hasRetriedAuth ||
      options.isAuthRequest(config.url ?? '')
    ) {
      throw error;
    }
    config.hasRetriedAuth = true;
    const token = await options.refreshAccessToken();
    if (!token) {
      throw error;
    }
    config.headers.set('Authorization', `Bearer ${token}`);
    return client.request(config);
  });

  return () => {
    client.interceptors.request.eject(requestId);
    client.interceptors.response.eject(responseId);
  };
}
