import { AxiosError, AxiosHeaders } from 'axios';
import type { AxiosResponse } from 'axios';
import { describe, expect, it } from 'vitest';

import { AuthApiError, getAuthErrorMessageKey, toAuthApiError } from './authErrors';

function axiosErrorWith(status: number, data: unknown): AxiosError {
  const config = { headers: new AxiosHeaders() };
  const response = { status, data, statusText: '', headers: {}, config } as AxiosResponse;
  return new AxiosError('Request failed', 'ERR_BAD_REQUEST', config, null, response);
}

describe('toAuthApiError', () => {
  it('takes the code and detail from the backend error body', () => {
    const error = toAuthApiError(
      axiosErrorWith(400, { code: 'code_expired', detail: 'Код не діє' }),
    );
    expect(error.code).toBe('code_expired');
    expect(error.detail).toBe('Код не діє');
    expect(error.status).toBe(400);
  });

  it('treats every 429 as throttled', () => {
    expect(toAuthApiError(axiosErrorWith(429, { detail: 'Зачекайте' })).code).toBe('throttled');
  });

  it('reports a network error when there is no response', () => {
    const error = new AxiosError('Network Error', 'ERR_NETWORK', { headers: new AxiosHeaders() });
    expect(toAuthApiError(error).code).toBe('network');
  });

  it('turns a bare 401 into not_authenticated', () => {
    expect(toAuthApiError(axiosErrorWith(401, {})).code).toBe('not_authenticated');
  });
});

describe('getAuthErrorMessageKey', () => {
  it('uses our own sentence for a known code', () => {
    expect(getAuthErrorMessageKey(new AuthApiError('code_invalid'))).toEqual({
      key: 'auth.errors.code_invalid',
    });
  });

  it('falls back to the backend detail for an unknown code', () => {
    expect(
      getAuthErrorMessageKey(
        new AuthApiError('password_too_common', { detail: 'Пароль надто простий.' }),
      ),
    ).toEqual({ key: 'auth.errors.detail', detail: 'Пароль надто простий.' });
  });

  it('falls back to a generic sentence when nothing is known', () => {
    expect(getAuthErrorMessageKey(new Error('boom'))).toEqual({ key: 'auth.errors.unknown' });
  });
});
