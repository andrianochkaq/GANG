import { z } from 'zod';

import { AuthApiError, toAuthApiError } from './authErrors';
import type { AuthApi, PhoneLoginResult, SessionTokens } from './authTypes';
import { apiClient } from './client';
import { clearRefreshToken, readRefreshToken, writeRefreshToken } from './refreshTokenStorage';

// The routes of backend/apps/accounts/urls.py (FC-103 … FC-107).
export const AUTH_PATHS = {
  emailRegister: '/api/auth/email-register/',
  emailVerify: '/api/auth/email-verify/',
  emailResend: '/api/auth/email-code/',
  emailLogin: '/api/auth/email-login/',
  phoneRequestCode: '/api/auth/phone-code/',
  phoneVerify: '/api/auth/phone-login/',
  telegramStart: '/api/auth/telegram/start/',
  telegramStatus: (token: string) => `/api/auth/telegram/status/${encodeURIComponent(token)}/`,
  passwordForgot: '/api/auth/password-forgot/',
  passwordReset: '/api/auth/password-reset/',
  tokenRefresh: '/api/auth/refresh/',
  logout: '/api/auth/logout/',
} as const;

const MS_PER_SECOND = 1000;
const HTTP_FORBIDDEN = 403;
const HTTP_NOT_FOUND = 404;
const HTTP_GONE = 410;

const tokenPairSchema = z.object({
  access: z.string().min(1),
  refresh: z.string().min(1),
});

const loginResultSchema = tokenPairSchema.extend({ is_new_user: z.boolean() });

const telegramStartSchema = z.object({
  token: z.string().min(1),
  deep_link: z.string().url(),
  expires_in_seconds: z.number().int().positive(),
  poll_interval_seconds: z.number().int().positive(),
});

const telegramStatusSchema = z.discriminatedUnion('status', [
  z.object({ status: z.literal('pending') }),
  loginResultSchema.extend({ status: z.literal('confirmed') }),
]);

// Every login answers with a JWT pair: the refresh token is stored, only the
// access token goes on to the screens.
function keepSession(data: z.infer<typeof tokenPairSchema>): SessionTokens {
  writeRefreshToken(data.refresh);
  return { access: data.access };
}

function keepLogin(data: z.infer<typeof loginResultSchema>): PhoneLoginResult {
  return { ...keepSession(data), isNewUser: data.is_new_user };
}

async function post(path: string, body?: object): Promise<unknown> {
  try {
    const response = await apiClient.post(path, body ?? {});
    return response.data;
  } catch (error) {
    throw toAuthApiError(error);
  }
}

async function get(path: string): Promise<unknown> {
  try {
    const response = await apiClient.get(path);
    return response.data;
  } catch (error) {
    throw toAuthApiError(error);
  }
}

export const httpAuthApi: AuthApi = {
  async registerEmail(email, password) {
    await post(AUTH_PATHS.emailRegister, { email, password });
  },
  async verifyEmail(email, code) {
    return keepSession(
      loginResultSchema.parse(await post(AUTH_PATHS.emailVerify, { email, code })),
    );
  },
  async resendEmailCode(email) {
    await post(AUTH_PATHS.emailResend, { email });
  },
  async loginEmail(email, password) {
    return keepSession(
      loginResultSchema.parse(await post(AUTH_PATHS.emailLogin, { email, password })),
    );
  },
  async requestPhoneCode(phone) {
    await post(AUTH_PATHS.phoneRequestCode, { phone });
  },
  async verifyPhone(phone, code) {
    return keepLogin(loginResultSchema.parse(await post(AUTH_PATHS.phoneVerify, { phone, code })));
  },
  async startTelegramLogin() {
    const data = telegramStartSchema.parse(await post(AUTH_PATHS.telegramStart));
    return {
      token: data.token,
      deepLink: data.deep_link,
      expiresAt: new Date(Date.now() + data.expires_in_seconds * MS_PER_SECOND).toISOString(),
      pollIntervalMs: data.poll_interval_seconds * MS_PER_SECOND,
    };
  },
  async getTelegramLoginStatus(token) {
    let body: unknown;
    try {
      body = await get(AUTH_PATHS.telegramStatus(token));
    } catch (error) {
      // 410: the request is older than 5 min; 404: it is gone. Either way
      // the screen offers to start a new one.
      if (
        error instanceof AuthApiError &&
        (error.status === HTTP_GONE || error.status === HTTP_NOT_FOUND)
      ) {
        return { status: 'expired' };
      }
      throw error;
    }
    const data = telegramStatusSchema.parse(body);
    if (data.status === 'confirmed') {
      return { status: 'confirmed', ...keepLogin(data) };
    }
    return data;
  },
  async requestPasswordReset(email) {
    await post(AUTH_PATHS.passwordForgot, { email });
  },
  async resetPassword(uid, token, password) {
    await post(AUTH_PATHS.passwordReset, { uid, token, password });
  },
  async refreshSession() {
    const refresh = readRefreshToken();
    if (!refresh) {
      throw new AuthApiError('not_authenticated');
    }
    try {
      return keepSession(tokenPairSchema.parse(await post(AUTH_PATHS.tokenRefresh, { refresh })));
    } catch (error) {
      // 401 session_ended or 403 account_disabled: the token is dead. A
      // network error keeps it, so the next page load can try again.
      if (
        error instanceof AuthApiError &&
        error.status !== undefined &&
        error.status <= HTTP_FORBIDDEN
      ) {
        clearRefreshToken();
      }
      throw error;
    }
  },
  async logout() {
    const refresh = readRefreshToken();
    clearRefreshToken();
    if (refresh) {
      await post(AUTH_PATHS.logout, { refresh });
    }
  },
};
