import { AxiosError, AxiosHeaders } from 'axios';
import type { AxiosResponse } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AUTH_PATHS, httpAuthApi } from './authHttp';
import { apiClient } from './client';
import { clearRefreshToken, readRefreshToken, writeRefreshToken } from './refreshTokenStorage';

function ok(data: unknown) {
  return Promise.resolve({ data } as AxiosResponse);
}

function fail(status: number, data: unknown) {
  const config = { headers: new AxiosHeaders() };
  const response = { status, data, statusText: '', headers: {}, config } as AxiosResponse;
  return Promise.reject(
    new AxiosError('Request failed', 'ERR_BAD_REQUEST', config, null, response),
  );
}

const PAIR = { access: 'access-1', refresh: 'refresh-1', is_new_user: false };

describe('httpAuthApi', () => {
  beforeEach(() => {
    clearRefreshToken();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('logs in by email and stores the refresh token', async () => {
    const post = vi.spyOn(apiClient, 'post').mockReturnValue(ok(PAIR));

    await expect(httpAuthApi.loginEmail('a@b.ua', 'secret123')).resolves.toEqual({
      access: 'access-1',
    });
    expect(post).toHaveBeenCalledWith('/api/auth/email-login/', {
      email: 'a@b.ua',
      password: 'secret123',
    });
    expect(readRefreshToken()).toBe('refresh-1');
  });

  it('returns is_new_user of a phone login', async () => {
    vi.spyOn(apiClient, 'post').mockReturnValue(ok({ ...PAIR, is_new_user: true }));

    await expect(httpAuthApi.verifyPhone('+380501234567', '123456')).resolves.toEqual({
      access: 'access-1',
      isNewUser: true,
    });
  });

  it('sends the stored refresh token and keeps the rotated one', async () => {
    writeRefreshToken('refresh-old');
    const post = vi
      .spyOn(apiClient, 'post')
      .mockReturnValue(ok({ access: 'access-2', refresh: 'refresh-new' }));

    await expect(httpAuthApi.refreshSession()).resolves.toEqual({ access: 'access-2' });
    expect(post).toHaveBeenCalledWith(AUTH_PATHS.tokenRefresh, { refresh: 'refresh-old' });
    expect(readRefreshToken()).toBe('refresh-new');
  });

  it('does not call the backend to refresh without a stored token', async () => {
    const post = vi.spyOn(apiClient, 'post');

    await expect(httpAuthApi.refreshSession()).rejects.toMatchObject({
      code: 'not_authenticated',
    });
    expect(post).not.toHaveBeenCalled();
  });

  it('forgets a refresh token the backend has ended', async () => {
    writeRefreshToken('refresh-old');
    vi.spyOn(apiClient, 'post').mockReturnValue(
      fail(401, { code: 'session_ended', detail: 'Сесію завершено.', fields: {} }),
    );

    await expect(httpAuthApi.refreshSession()).rejects.toMatchObject({ code: 'session_ended' });
    expect(readRefreshToken()).toBeNull();
  });

  it('keeps the refresh token when the network fails', async () => {
    writeRefreshToken('refresh-old');
    vi.spyOn(apiClient, 'post').mockReturnValue(
      Promise.reject(
        new AxiosError('Network Error', 'ERR_NETWORK', { headers: new AxiosHeaders() }),
      ),
    );

    await expect(httpAuthApi.refreshSession()).rejects.toMatchObject({ code: 'network' });
    expect(readRefreshToken()).toBe('refresh-old');
  });

  it('revokes the refresh token on logout and forgets it', async () => {
    writeRefreshToken('refresh-old');
    const post = vi.spyOn(apiClient, 'post').mockReturnValue(ok(undefined));

    await httpAuthApi.logout();
    expect(post).toHaveBeenCalledWith(AUTH_PATHS.logout, { refresh: 'refresh-old' });
    expect(readRefreshToken()).toBeNull();
  });

  it('reads the Telegram start answer', async () => {
    vi.spyOn(apiClient, 'post').mockReturnValue(
      ok({
        token: 'tg-1',
        deep_link: 'https://t.me/freecook_bot?start=tg-1',
        expires_in_seconds: 300,
        poll_interval_seconds: 2,
      }),
    );

    const request = await httpAuthApi.startTelegramLogin();
    expect(request).toMatchObject({
      token: 'tg-1',
      deepLink: 'https://t.me/freecook_bot?start=tg-1',
      pollIntervalMs: 2000,
    });
    expect(Date.parse(request.expiresAt)).toBeGreaterThan(Date.now());
  });

  it('stores the session of a confirmed Telegram login', async () => {
    vi.spyOn(apiClient, 'get').mockReturnValue(ok({ status: 'confirmed', ...PAIR }));

    await expect(httpAuthApi.getTelegramLoginStatus('tg-1')).resolves.toEqual({
      status: 'confirmed',
      access: 'access-1',
      isNewUser: false,
    });
    expect(readRefreshToken()).toBe('refresh-1');
  });

  it.each([410, 404])('treats a %i Telegram status as expired', async (status) => {
    vi.spyOn(apiClient, 'get').mockReturnValue(
      fail(status, { code: 'telegram_login_expired', detail: 'Вхід не дійсний.', fields: {} }),
    );

    await expect(httpAuthApi.getTelegramLoginStatus('tg-1')).resolves.toEqual({
      status: 'expired',
    });
  });
});
