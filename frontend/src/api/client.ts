import axios from 'axios';

const REQUEST_TIMEOUT_MS = 10000;

// VITE_API_URL is the backend origin, e.g. http://localhost:8000.
// Left empty, requests go to the same origin (nginx proxies /api/).
export function getApiBaseUrl(apiUrl: string | undefined): string {
  return (apiUrl ?? '').trim().replace(/\/+$/, '');
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(import.meta.env.VITE_API_URL),
  timeout: REQUEST_TIMEOUT_MS,
  headers: { Accept: 'application/json' },
  // No cookies: the refresh token travels in the body (refreshTokenStorage.ts).
  // The backend does not allow credentialed CORS, so a cookie request to
  // VITE_API_URL on another origin would be blocked by the browser.
  withCredentials: false,
});
