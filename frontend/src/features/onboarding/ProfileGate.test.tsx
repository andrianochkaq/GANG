import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import '../../i18n';
import { AuthApiError } from '../../api/authErrors';
import { resetAuthMock } from '../../api/authMock';
import { profileApi } from '../../api/profile';
import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';
import { renderAppAt } from '../auth/authTestUtils';
import { startSession } from './onboardingTestUtils';

vi.mock('../../api/auth', async () => {
  const { createMockAuthApi } = await import('../../api/authMock');
  return { authApi: createMockAuthApi(0), isAuthMockEnabled: () => true };
});

vi.mock('../../api/profile', async () => {
  const { createMockProfileApi } = await import('../../api/profileMock');
  return { profileApi: createMockProfileApi(0) };
});

describe('ProfileGate', () => {
  beforeEach(() => {
    resetAuthMock();
    useAuthStore.setState({ accessToken: null, status: 'unknown' });
    useThemeStore.setState({ themeId: 'white' });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  it('applies the colour saved in the profile', async () => {
    await profileApi.updateProfile({ themeColor: 'ocean', isOnboardingDone: true });
    await startSession(false);
    renderAppAt('/');

    expect(await screen.findByRole('heading', { name: 'Холодильник' })).toBeTruthy();
    await waitFor(() => expect(useThemeStore.getState().themeId).toBe('ocean'));
  });

  it('lets an onboarded account straight through', async () => {
    await startSession(false);
    const router = renderAppAt('/');

    expect(await screen.findByRole('heading', { name: 'Холодильник' })).toBeTruthy();
    expect(router.getPathname()).toBe('/');
  });

  it('sends an account that has not finished onboarding to the colour screen', async () => {
    await startSession(true);
    const router = renderAppAt('/');

    expect(await screen.findByRole('heading', { name: 'Колір застосунку' })).toBeTruthy();
    expect(router.getPathname()).toBe('/onboarding/color');
  });

  it('explains a profile that failed to load and loads it again on request', async () => {
    await startSession(false);
    vi.spyOn(profileApi, 'getProfile').mockRejectedValueOnce(new AuthApiError('network'));
    renderAppAt('/');

    expect((await screen.findByRole('alert')).textContent).toBe(
      'Не вдалося завантажити профіль. Перевірте інтернет і спробуйте ще раз.',
    );
    fireEvent.click(screen.getByRole('button', { name: 'Спробувати ще раз' }));

    expect(await screen.findByRole('heading', { name: 'Холодильник' })).toBeTruthy();
  });
});
