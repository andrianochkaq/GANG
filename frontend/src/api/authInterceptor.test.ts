import axios, { AxiosError, AxiosHeaders } from 'axios';
import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { describe, expect, it, vi } from 'vitest';

import { installAuthInterceptor } from './authInterceptor';

type Handler = (config: InternalAxiosRequestConfig) => { status: number; data: unknown };

function createClient(handler: Handler) {
  const seenTokens: Array<string | undefined> = [];
  const client = axios.create({
    adapter: async (config) => {
      seenTokens.push(AxiosHeaders.from(config.headers).get('Authorization')?.toString());
      const { status, data } = handler(config);
      const response = { status, data, statusText: '', headers: {}, config } as AxiosResponse;
      if (status >= 400) {
        throw new AxiosError('Request failed', 'ERR_BAD_REQUEST', config, null, response);
      }
      return response;
    },
  });
  return { client, seenTokens };
}

describe('installAuthInterceptor', () => {
  it('sends the access token as a Bearer header', async () => {
    const { client, seenTokens } = createClient(() => ({ status: 200, data: {} }));
    installAuthInterceptor(client, {
      getAccessToken: () => 'token-1',
      refreshAccessToken: vi.fn(),
      isAuthRequest: () => false,
    });

    await client.get('/api/me/');
    expect(seenTokens).toEqual(['Bearer token-1']);
  });

  it('refreshes once on 401 and repeats the request with the new token', async () => {
    let calls = 0;
    const { client, seenTokens } = createClient(() => {
      calls += 1;
      return calls === 1 ? { status: 401, data: {} } : { status: 200, data: { ok: true } };
    });
    let accessToken = 'token-1';
    const refreshAccessToken = vi.fn(async () => {
      accessToken = 'token-2';
      return accessToken;
    });
    installAuthInterceptor(client, {
      getAccessToken: () => accessToken,
      refreshAccessToken,
      isAuthRequest: () => false,
    });

    const response = await client.get('/api/me/');
    expect(response.data).toEqual({ ok: true });
    expect(refreshAccessToken).toHaveBeenCalledTimes(1);
    expect(seenTokens).toEqual(['Bearer token-1', 'Bearer token-2']);
  });

  it('gives up when the refresh fails', async () => {
    const { client } = createClient(() => ({ status: 401, data: {} }));
    installAuthInterceptor(client, {
      getAccessToken: () => 'token-1',
      refreshAccessToken: vi.fn().mockResolvedValue(null),
      isAuthRequest: () => false,
    });

    await expect(client.get('/api/me/')).rejects.toMatchObject({ response: { status: 401 } });
  });

  it('never refreshes for auth requests such as login', async () => {
    const { client } = createClient(() => ({ status: 401, data: {} }));
    const refreshAccessToken = vi.fn();
    installAuthInterceptor(client, {
      getAccessToken: () => null,
      refreshAccessToken,
      isAuthRequest: (url) => url.startsWith('/api/auth/'),
    });

    await expect(client.post('/api/auth/email/login/')).rejects.toBeInstanceOf(AxiosError);
    expect(refreshAccessToken).not.toHaveBeenCalled();
  });
});
