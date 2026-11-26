import { isAxiosError } from 'axios';
import { z } from 'zod';

// Error codes the auth screens explain in their own words (auth.errors.* in
// uk.json). The backend answers {"code", "detail", "fields"} (architecture.md);
// any other code falls back to its Ukrainian "detail".
export const KNOWN_AUTH_ERROR_CODES = [
  'code_invalid',
  'code_expired',
  'code_attempts_exceeded',
  'throttled',
  'invalid_credentials',
  'email_not_verified',
  'email_taken',
  'phone_invalid',
  'reset_link_invalid',
  'login_request_expired',
  'not_authenticated',
  'network',
  'unknown',
] as const;

export type AuthErrorCode = (typeof KNOWN_AUTH_ERROR_CODES)[number];

const HTTP_TOO_MANY_REQUESTS = 429;
const HTTP_UNAUTHORIZED = 401;

const errorBodySchema = z.object({
  code: z.string().optional(),
  detail: z.string().optional(),
  fields: z.record(z.unknown()).optional(),
});

export class AuthApiError extends Error {
  readonly code: string;
  readonly detail: string | undefined;
  readonly status: number | undefined;

  constructor(code: string, options: { detail?: string; status?: number } = {}) {
    super(options.detail ?? code);
    this.name = 'AuthApiError';
    this.code = code;
    this.detail = options.detail;
    this.status = options.status;
  }
}

export function isKnownAuthErrorCode(code: string): code is AuthErrorCode {
  return (KNOWN_AUTH_ERROR_CODES as readonly string[]).includes(code);
}

export function toAuthApiError(error: unknown): AuthApiError {
  if (error instanceof AuthApiError) {
    return error;
  }
  if (!isAxiosError(error)) {
    return new AuthApiError('unknown');
  }
  if (!error.response) {
    return new AuthApiError('network');
  }
  const { status, data } = error.response;
  const body = errorBodySchema.safeParse(data);
  const detail = body.success ? body.data.detail : undefined;
  if (status === HTTP_TOO_MANY_REQUESTS) {
    return new AuthApiError('throttled', { detail, status });
  }
  const code = body.success && body.data.code ? body.data.code : undefined;
  if (code) {
    return new AuthApiError(code, { detail, status });
  }
  if (status === HTTP_UNAUTHORIZED) {
    return new AuthApiError('not_authenticated', { detail, status });
  }
  return new AuthApiError('unknown', { detail, status });
}

// The i18n key and values for an error message: a known code gets our own
// sentence, an unknown one the backend's Ukrainian detail.
export function getAuthErrorMessageKey(error: unknown): { key: string; detail?: string } {
  const authError = toAuthApiError(error);
  if (isKnownAuthErrorCode(authError.code) && authError.code !== 'unknown') {
    return { key: `auth.errors.${authError.code}` };
  }
  if (authError.detail) {
    return { key: 'auth.errors.detail', detail: authError.detail };
  }
  return { key: 'auth.errors.unknown' };
}
