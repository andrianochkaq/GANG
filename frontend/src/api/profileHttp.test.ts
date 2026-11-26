import { AxiosError } from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { apiClient } from './client';
import { PROFILE_PATH, httpProfileApi, toProfile, toProfileRequestBody } from './profileHttp';

vi.mock('./client', () => ({ apiClient: { get: vi.fn(), patch: vi.fn() } }));

const BACKEND_USER = {
  id: 'b1c2',
  nickname: 'marta',
  gender: 'unset',
  theme_color: 'sakura',
  is_onboarding_done: true,
};

describe('toProfile', () => {
  it('reads the colour and onboarding flag from the snake_case body', () => {
    expect(toProfile(BACKEND_USER)).toEqual({ themeColor: 'sakura', isOnboardingDone: true });
  });

  it('falls back to white for a colour this app does not know', () => {
    expect(toProfile({ ...BACKEND_USER, theme_color: 'neon' }).themeColor).toBe('white');
  });

  it('refuses a body without the onboarding flag', () => {
    expect(() => toProfile({ theme_color: 'white' })).toThrow();
  });
});

describe('toProfileRequestBody', () => {
  it('sends only the fields that changed, in snake_case', () => {
    expect(toProfileRequestBody({ isOnboardingDone: true })).toEqual({
      is_onboarding_done: true,
    });
    expect(toProfileRequestBody({ themeColor: 'ocean', isOnboardingDone: false })).toEqual({
      theme_color: 'ocean',
      is_onboarding_done: false,
    });
    expect(toProfileRequestBody({})).toEqual({});
  });
});

describe('httpProfileApi', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.patch).mockReset();
  });

  it('reads the profile from /api/me/', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: BACKEND_USER } as never);
    await expect(httpProfileApi.getProfile()).resolves.toEqual({
      themeColor: 'sakura',
      isOnboardingDone: true,
    });
    expect(apiClient.get).toHaveBeenCalledWith(PROFILE_PATH);
  });

  it('saves a change with PATCH and returns the updated profile', async () => {
    vi.mocked(apiClient.patch).mockResolvedValue({ data: BACKEND_USER } as never);
    await expect(
      httpProfileApi.updateProfile({ themeColor: 'sakura', isOnboardingDone: true }),
    ).resolves.toEqual({ themeColor: 'sakura', isOnboardingDone: true });
    expect(apiClient.patch).toHaveBeenCalledWith(PROFILE_PATH, {
      theme_color: 'sakura',
      is_onboarding_done: true,
    });
  });

  it('turns a failed request into an auth error the screens can explain', async () => {
    vi.mocked(apiClient.patch).mockRejectedValue(new AxiosError('Network Error'));
    await expect(httpProfileApi.updateProfile({ isOnboardingDone: true })).rejects.toMatchObject({
      code: 'network',
    });
  });
});
