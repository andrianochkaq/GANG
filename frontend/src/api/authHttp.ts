import { z } from 'zod';

import { toAuthApiError } from './authErrors';
import type { AuthApi } from './authTypes';
import { apiClient } from './client';

// Paths are the frontend's assumption until FC-103 … FC-107 are merged; keep
// them in this one map so matching the backend is a one-file change.
export const AUTH_PATHS = {
  emailRegister: '/api/auth/email/register/',
  emailVerify: '/api/auth/email/verify/',
  emailResend: '/api/auth/email/resend/',
  emailLogin: '/api/auth/email/login/',
  phoneRequestCode: '/api/auth/phone/request-code/',
  phoneVerify: '/api/auth/phone/verify/',
  telegramStart: '/api/auth/telegram/start/',
  telegramStatus: (token: string) => `/api/auth/telegram/status/${encodeURIComponent(token)}/`,
  passwordForgot: '/api/auth/password/forgot/',
  passwordReset: '/api/auth/password/reset/',
  tokenRefresh: '/api/auth/token/refresh/',
  logout: '/api/auth/logout/',
} as const;

const tokensSchema = z.object({ access: z.string().min(1) });

const phoneLoginSchema = tokensSchema.extend({ is_new_user: z.boolean() });

const telegramStartSchema = z.object({
  token: z.string().min(1),
  deep_link: z.string().url(),
  expires_at: z.string(),
});

const telegramStatusSchema = z.discriminatedUnion('status', [
  z.object({ status: z.literal('pending') }),
  z.object({ status: z.literal('expired') }),
  z.object({
    status: z.literal('confirmed'),
    access: z.string().min(1),
    is_new_user: z.boolean().default(false),
  }),
]);

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

// The refresh token lives in an HttpOnly cookie scoped to /api/auth/
// (architecture.md, D4), so refresh and logout send no token in the body.
export const httpAuthApi: AuthApi = {
  async registerEmail(email, password) {
    await post(AUTH_PATHS.emailRegister, { email, password });
  },
  async verifyEmail(email, code) {
    return tokensSchema.parse(await post(AUTH_PATHS.emailVerify, { email, code }));
  },
  async resendEmailCode(email) {
    await post(AUTH_PATHS.emailResend, { email });
  },
  async loginEmail(email, password) {
    return tokensSchema.parse(await post(AUTH_PATHS.emailLogin, { email, password }));
  },
  async requestPhoneCode(phone) {
    await post(AUTH_PATHS.phoneRequestCode, { phone });
  },
  async verifyPhone(phone, code) {
    const data = phoneLoginSchema.parse(await post(AUTH_PATHS.phoneVerify, { phone, code }));
    return { access: data.access, isNewUser: data.is_new_user };
  },
  async startTelegramLogin() {
    const data = telegramStartSchema.parse(await post(AUTH_PATHS.telegramStart));
    return { token: data.token, deepLink: data.deep_link, expiresAt: data.expires_at };
  },
  async getTelegramLoginStatus(token) {
    const data = telegramStatusSchema.parse(await get(AUTH_PATHS.telegramStatus(token)));
    if (data.status === 'confirmed') {
      return { status: 'confirmed', access: data.access, isNewUser: data.is_new_user };
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
    return tokensSchema.parse(await post(AUTH_PATHS.tokenRefresh));
  },
  async logout() {
    await post(AUTH_PATHS.logout);
  },
};
