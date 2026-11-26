import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import '../../i18n';
import { AuthApiError } from '../../api/authErrors';
import { createMockAuthApi, resetAuthMock } from '../../api/authMock';
import { fetchHealthStatus } from '../../api/health';
import { profileApi } from '../../api/profile';
import { useAuthStore } from '../../store/authStore';
import { useThemeStore } from '../../store/themeStore';
import { renderAppAt } from '../auth/authTestUtils';
import { EXISTING_EMAIL, EXISTING_PASSWORD, startSession } from './onboardingTestUtils';

vi.mock('../../api/auth', async () => {
  const { createMockAuthApi } = await import('../../api/authMock');
  return { authApi: createMockAuthApi(0), isAuthMockEnabled: () => true };
});

vi.mock('../../api/profile', async () => {
  const { createMockProfileApi } = await import('../../api/profileMock');
  return { profileApi: createMockProfileApi(0) };
});

vi.mock('../../api/health', () => ({ fetchHealthStatus: vi.fn() }));

const COLOR_PATH = '/onboarding/color';

function resetBrowser() {
  cleanup();
  useAuthStore.setState({ accessToken: null, status: 'unknown' });
  useThemeStore.setState({ themeId: 'white' });
}

describe('ThemePicker (app colour after the first login)', () => {
  beforeEach(() => {
    resetAuthMock();
    resetBrowser();
    vi.mocked(fetchHealthStatus).mockResolvedValue({ db: 'ok', redis: 'ok' });
  });

  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  it('shows a new user the colour screen as step 3 of 3', async () => {
    await startSession(true);
    const router = renderAppAt('/');

    expect(await screen.findByRole('heading', { name: 'Колір застосунку' })).toBeTruthy();
    expect(router.getPathname()).toBe(COLOR_PATH);
    expect(screen.getByText('Реєстрація · крок 3 з 3')).toBeTruthy();
    expect(screen.getAllByRole('radio')).toHaveLength(17);
    expect(screen.getByRole('radio', { name: 'Білий' }).getAttribute('aria-checked')).toBe('true');
  });

  it('previews a chosen colour at once', async () => {
    await startSession(true);
    renderAppAt('/');

    fireEvent.click(await screen.findByRole('radio', { name: 'Сакура' }));

    expect(useThemeStore.getState().themeId).toBe('sakura');
    expect(screen.getByRole('radio', { name: 'Сакура' }).getAttribute('aria-checked')).toBe('true');
    expect(screen.getByRole('status').textContent).toBe('Обрано: Сакура');
  });

  it('saves the colour and finishes onboarding with «Готово»', async () => {
    await startSession(true);
    const router = renderAppAt('/');

    fireEvent.click(await screen.findByRole('radio', { name: 'Океан' }));
    fireEvent.click(screen.getByRole('button', { name: 'Готово' }));

    await waitFor(() => expect(router.getPathname()).toBe('/'));
    expect(await screen.findByText('Стан сервера')).toBeTruthy();
    await expect(profileApi.getProfile()).resolves.toEqual({
      themeColor: 'ocean',
      isOnboardingDone: true,
    });
    expect(useThemeStore.getState().themeId).toBe('ocean');
  });

  it('keeps white and finishes onboarding with «Пропустити»', async () => {
    await startSession(true);
    const router = renderAppAt('/');

    fireEvent.click(await screen.findByRole('radio', { name: 'Сакура' }));
    fireEvent.click(screen.getByRole('button', { name: 'Пропустити' }));

    await waitFor(() => expect(router.getPathname()).toBe('/'));
    await expect(profileApi.getProfile()).resolves.toEqual({
      themeColor: 'white',
      isOnboardingDone: true,
    });
    expect(useThemeStore.getState().themeId).toBe('white');
  });

  it('shows the screen only once', async () => {
    await startSession(true);
    renderAppAt('/');
    fireEvent.click(await screen.findByRole('button', { name: 'Готово' }));
    expect(await screen.findByText('Стан сервера')).toBeTruthy();

    // A new page load, now on the colour screen's address.
    resetBrowser();
    const router = renderAppAt(COLOR_PATH);

    expect(await screen.findByText('Стан сервера')).toBeTruthy();
    expect(router.getPathname()).toBe('/');
  });

  it('shows the chosen colour after logging in on a second browser', async () => {
    await startSession(true);
    renderAppAt('/');
    fireEvent.click(await screen.findByRole('radio', { name: 'Бузок' }));
    fireEvent.click(screen.getByRole('button', { name: 'Готово' }));
    expect(await screen.findByText('Стан сервера')).toBeTruthy();

    // The second browser has no session and starts with white.
    await createMockAuthApi(0).logout();
    resetBrowser();
    const router = renderAppAt('/login');
    fireEvent.change(await screen.findByLabelText('Електронна пошта'), {
      target: { value: EXISTING_EMAIL },
    });
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: EXISTING_PASSWORD } });
    fireEvent.click(screen.getByRole('button', { name: 'Увійти' }));

    await waitFor(() => expect(router.getPathname()).toBe('/'));
    await waitFor(() => expect(useThemeStore.getState().themeId).toBe('lilac'));
  });

  it('explains a failed save next to the button and stays on the screen', async () => {
    await startSession(true);
    vi.spyOn(profileApi, 'updateProfile').mockRejectedValueOnce(new AuthApiError('network'));
    const router = renderAppAt('/');

    fireEvent.click(await screen.findByRole('button', { name: 'Готово' }));

    expect((await screen.findByRole('alert')).textContent).toBe(
      'Не вдалося зв’язатися з сервером. Перевірте інтернет і спробуйте ще раз.',
    );
    expect(router.getPathname()).toBe(COLOR_PATH);
  });
});
