import { AuthApiError } from './authErrors';
import type { AuthApi, TelegramLoginStatus } from './authTypes';
import { resetProfileMock, startMockOnboarding } from './profileMock';

// In-memory stand-in for the auth backend (FC-103 … FC-107), switched on with
// VITE_AUTH_MOCK=true. Its rules mirror FC-102: 6-digit codes, 5 attempts,
// 5 code requests per target. Fixed inputs trigger every error state:
export const MOCK_CODE = '123456';
export const MOCK_EXPIRED_CODE = '000000';
export const MOCK_TAKEN_EMAIL = 'taken@example.com';
export const MOCK_UNVERIFIED_EMAIL = 'unverified@example.com';
export const MOCK_WRONG_PASSWORD = 'wrong-password';
export const MOCK_EXPIRED_RESET_TOKEN = 'expired';
export const MOCK_TELEGRAM_POLLS_TO_CONFIRM = 3;

const MAX_CODE_ATTEMPTS = 5;
const MAX_CODE_REQUESTS = 5;
const TELEGRAM_REQUEST_TTL_MS = 5 * 60 * 1000;
const RESPONSE_DELAY_MS = 400;
// Stands in for the HttpOnly refresh cookie so a reload keeps the session.
const SESSION_STORAGE_KEY = 'fc-mock-refresh';

type MockState = {
  codeAttempts: Map<string, number>;
  codeRequests: Map<string, number>;
  telegramPolls: Map<string, number>;
  telegramExpiry: Map<string, number>;
};

function createState(): MockState {
  return {
    codeAttempts: new Map(),
    codeRequests: new Map(),
    telegramPolls: new Map(),
    telegramExpiry: new Map(),
  };
}

let state = createState();
// Mirrors the storage flag for browsers (and test runners) without storage.
let hasMemorySession = false;

export function resetAuthMock(): void {
  state = createState();
  writeSessionFlag(false);
  resetProfileMock();
}

function wait(delayMs: number): Promise<void> {
  return delayMs > 0 ? new Promise((resolve) => setTimeout(resolve, delayMs)) : Promise.resolve();
}

function writeSessionFlag(hasSession: boolean): void {
  hasMemorySession = hasSession;
  try {
    if (hasSession) {
      window.localStorage.setItem(SESSION_STORAGE_KEY, '1');
    } else {
      window.localStorage.removeItem(SESSION_STORAGE_KEY);
    }
  } catch {
    // Storage can be blocked; the session then lasts until reload.
  }
}

function readSessionFlag(): boolean {
  try {
    return window.localStorage.getItem(SESSION_STORAGE_KEY) === '1' || hasMemorySession;
  } catch {
    return hasMemorySession;
  }
}

function issueTokens() {
  writeSessionFlag(true);
  return { access: `mock-access-${Date.now()}` };
}

function countCodeRequest(target: string): void {
  const count = (state.codeRequests.get(target) ?? 0) + 1;
  state.codeRequests.set(target, count);
  if (count > MAX_CODE_REQUESTS) {
    throw new AuthApiError('throttled', { status: 429 });
  }
  state.codeAttempts.set(target, 0);
}

function checkCode(target: string, code: string): void {
  const attempts = (state.codeAttempts.get(target) ?? 0) + 1;
  state.codeAttempts.set(target, attempts);
  if (attempts > MAX_CODE_ATTEMPTS) {
    throw new AuthApiError('code_attempts_exceeded', { status: 400 });
  }
  if (code === MOCK_EXPIRED_CODE) {
    throw new AuthApiError('code_expired', { status: 400 });
  }
  if (code !== MOCK_CODE) {
    throw new AuthApiError('code_invalid', { status: 400 });
  }
}

export function createMockAuthApi(delayMs = RESPONSE_DELAY_MS): AuthApi {
  return {
    async registerEmail(email) {
      await wait(delayMs);
      if (email.toLowerCase() === MOCK_TAKEN_EMAIL) {
        throw new AuthApiError('email_taken', { status: 400 });
      }
      countCodeRequest(email);
    },
    async verifyEmail(email, code) {
      await wait(delayMs);
      checkCode(email, code);
      // A confirmed registration is a new account: it still has to pick its colour.
      startMockOnboarding();
      return issueTokens();
    },
    async resendEmailCode(email) {
      await wait(delayMs);
      countCodeRequest(email);
    },
    async loginEmail(email, password) {
      await wait(delayMs);
      if (password === MOCK_WRONG_PASSWORD) {
        throw new AuthApiError('invalid_credentials', { status: 400 });
      }
      if (email.toLowerCase() === MOCK_UNVERIFIED_EMAIL) {
        throw new AuthApiError('email_not_verified', { status: 403 });
      }
      return issueTokens();
    },
    async requestPhoneCode(phone) {
      await wait(delayMs);
      countCodeRequest(phone);
    },
    async verifyPhone(phone, code) {
      await wait(delayMs);
      checkCode(phone, code);
      return { ...issueTokens(), isNewUser: false };
    },
    async startTelegramLogin() {
      await wait(delayMs);
      const token = `mock-${Math.random().toString(36).slice(2, 10)}`;
      const expiresAt = Date.now() + TELEGRAM_REQUEST_TTL_MS;
      state.telegramPolls.set(token, 0);
      state.telegramExpiry.set(token, expiresAt);
      return {
        token,
        deepLink: `https://t.me/freecook_bot?start=${token}`,
        expiresAt: new Date(expiresAt).toISOString(),
      };
    },
    async getTelegramLoginStatus(token): Promise<TelegramLoginStatus> {
      await wait(delayMs);
      const expiresAt = state.telegramExpiry.get(token);
      if (expiresAt === undefined || Date.now() > expiresAt) {
        return { status: 'expired' };
      }
      const polls = (state.telegramPolls.get(token) ?? 0) + 1;
      state.telegramPolls.set(token, polls);
      if (polls < MOCK_TELEGRAM_POLLS_TO_CONFIRM) {
        return { status: 'pending' };
      }
      return { status: 'confirmed', ...issueTokens(), isNewUser: false };
    },
    async requestPasswordReset() {
      await wait(delayMs);
    },
    async resetPassword(_uid, token) {
      await wait(delayMs);
      if (token === MOCK_EXPIRED_RESET_TOKEN) {
        throw new AuthApiError('reset_link_invalid', { status: 400 });
      }
    },
    async refreshSession() {
      await wait(delayMs);
      if (!readSessionFlag()) {
        throw new AuthApiError('not_authenticated', { status: 401 });
      }
      return issueTokens();
    },
    async logout() {
      await wait(delayMs);
      writeSessionFlag(false);
    },
  };
}
