// The backend (FC-106) returns the refresh token in the response body and
// expects it back in the body of refresh/ and logout/; it sets no cookie.
// So the SPA keeps the token in localStorage to survive a page reload. This
// differs from architecture.md, D4 (HttpOnly cookie); the access token is
// still kept in memory only.
const REFRESH_TOKEN_STORAGE_KEY = 'fc-refresh-token';

// Used when storage is blocked: the session then lasts until reload.
let memoryToken: string | null = null;

export function readRefreshToken(): string | null {
  try {
    return window.localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY) ?? memoryToken;
  } catch {
    return memoryToken;
  }
}

export function writeRefreshToken(token: string): void {
  memoryToken = token;
  try {
    window.localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, token);
  } catch {
    // Storage is blocked; memoryToken keeps the session for this page.
  }
}

export function clearRefreshToken(): void {
  memoryToken = null;
  try {
    window.localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
  } catch {
    // Nothing stored.
  }
}
