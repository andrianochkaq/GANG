import { beforeEach, describe, expect, it } from 'vitest';

import {
  MOCK_CODE,
  MOCK_EXPIRED_CODE,
  MOCK_TELEGRAM_POLLS_TO_CONFIRM,
  createMockAuthApi,
  resetAuthMock,
} from './authMock';

const api = createMockAuthApi(0);
const EMAIL = 'marta@example.com';

describe('mock auth API', () => {
  beforeEach(() => resetAuthMock());

  it('accepts the mock code and keeps the session across a reload', async () => {
    await api.registerEmail(EMAIL, 'freecook26');
    await expect(api.verifyEmail(EMAIL, MOCK_CODE)).resolves.toHaveProperty('access');
    await expect(api.refreshSession()).resolves.toHaveProperty('access');
  });

  it('tells a wrong code from an expired one', async () => {
    await api.requestPhoneCode('+380671234567');
    await expect(api.verifyPhone('+380671234567', '111111')).rejects.toMatchObject({
      code: 'code_invalid',
    });
    await expect(api.verifyPhone('+380671234567', MOCK_EXPIRED_CODE)).rejects.toMatchObject({
      code: 'code_expired',
    });
  });

  it('blocks a code after 5 attempts', async () => {
    await api.requestPhoneCode('+380671234567');
    for (let attempt = 0; attempt < 5; attempt += 1) {
      await api.verifyPhone('+380671234567', '111111').catch(() => undefined);
    }
    await expect(api.verifyPhone('+380671234567', MOCK_CODE)).rejects.toMatchObject({
      code: 'code_attempts_exceeded',
    });
  });

  it('throttles the sixth code request for one target', async () => {
    for (let request = 0; request < 5; request += 1) {
      await api.requestPhoneCode('+380671234567');
    }
    await expect(api.requestPhoneCode('+380671234567')).rejects.toMatchObject({
      code: 'throttled',
    });
  });

  it('confirms a Telegram login after a few polls', async () => {
    const request = await api.startTelegramLogin();
    for (let poll = 1; poll < MOCK_TELEGRAM_POLLS_TO_CONFIRM; poll += 1) {
      await expect(api.getTelegramLoginStatus(request.token)).resolves.toEqual({
        status: 'pending',
      });
    }
    await expect(api.getTelegramLoginStatus(request.token)).resolves.toMatchObject({
      status: 'confirmed',
    });
  });

  it('has no session after logout', async () => {
    await api.loginEmail(EMAIL, 'freecook26');
    await api.logout();
    await expect(api.refreshSession()).rejects.toMatchObject({ code: 'not_authenticated' });
  });
});
