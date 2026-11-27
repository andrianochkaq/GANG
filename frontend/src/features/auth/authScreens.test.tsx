import { cleanup, fireEvent, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import '../../i18n';
import {
  MOCK_CODE,
  MOCK_EXPIRED_CODE,
  MOCK_WRONG_PASSWORD,
  createMockAuthApi,
  resetAuthMock,
} from '../../api/authMock';
import { useAuthStore } from '../../store/authStore';
import { renderAppAt } from './authTestUtils';

vi.mock('../../api/auth', async () => {
  const { createMockAuthApi } = await import('../../api/authMock');
  return { authApi: createMockAuthApi(0), isAuthMockEnabled: () => true };
});

vi.mock('../../api/profile', async () => {
  const { createMockProfileApi } = await import('../../api/profileMock');
  return { profileApi: createMockProfileApi(0) };
});

function typeCode(code: string) {
  fireEvent.paste(screen.getByLabelText('Цифра 1'), { clipboardData: { getData: () => code } });
}

describe('auth screens', () => {
  beforeEach(() => {
    resetAuthMock();
    useAuthStore.setState({ accessToken: null, status: 'unknown' });
  });

  afterEach(cleanup);

  it('sends a logged-out user from a protected page to the login screen', async () => {
    const router = renderAppAt('/');
    expect(await screen.findByRole('tab', { name: 'Вхід' })).toBeTruthy();
    expect(router.getPathname()).toBe('/login');
  });

  it('keeps the user logged in after a reload of a protected page', async () => {
    // A login before the reload leaves the refresh cookie (here: the mock flag).
    await createMockAuthApi(0).loginEmail('marta@example.com', 'freecook26');
    renderAppAt('/');
    expect(await screen.findByRole('heading', { name: 'Холодильник' })).toBeTruthy();
    expect(useAuthStore.getState().status).toBe('authenticated');
  });

  it('sends a logged-in user from the login screen on to the app', async () => {
    // The browser's back button after a login lands on /login again.
    await createMockAuthApi(0).loginEmail('marta@example.com', 'freecook26');
    const router = renderAppAt('/login');
    expect(await screen.findByRole('heading', { name: 'Холодильник' })).toBeTruthy();
    expect(router.getPathname()).toBe('/');
  });

  it('shows a Ukrainian error for a wrong password', async () => {
    renderAppAt('/login');
    fireEvent.change(await screen.findByLabelText('Електронна пошта'), {
      target: { value: 'marta@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: MOCK_WRONG_PASSWORD } });
    fireEvent.click(screen.getByRole('button', { name: 'Увійти' }));

    expect((await screen.findByRole('alert')).textContent).toBe('Пошта або пароль неправильні.');
  });

  it('returns to the page the user wanted after logging in', async () => {
    const router = renderAppAt('/');
    fireEvent.change(await screen.findByLabelText('Електронна пошта'), {
      target: { value: 'marta@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: 'freecook26' } });
    fireEvent.click(screen.getByRole('button', { name: 'Увійти' }));

    await waitFor(() => expect(router.getPathname()).toBe('/'));
    expect(await screen.findByRole('heading', { name: 'Холодильник' })).toBeTruthy();
  });

  it('registers by email and confirms the code', async () => {
    const router = renderAppAt('/login?tab=register');
    fireEvent.change(await screen.findByLabelText('Електронна пошта'), {
      target: { value: 'new@example.com' },
    });
    fireEvent.change(screen.getByLabelText('Пароль'), { target: { value: 'freecook26' } });
    fireEvent.click(screen.getByRole('button', { name: 'Зареєструватися' }));

    expect(await screen.findByRole('heading', { name: 'Підтвердьте пошту' })).toBeTruthy();
    typeCode('111111');
    fireEvent.click(screen.getByRole('button', { name: 'Підтвердити' }));
    expect((await screen.findByRole('alert')).textContent).toBe(
      'Код неправильний. Спробуйте ще раз.',
    );

    typeCode(MOCK_CODE);
    fireEvent.click(screen.getByRole('button', { name: 'Підтвердити' }));
    // A new account picks its app colour next (FC-202).
    await waitFor(() => expect(router.getPathname()).toBe('/onboarding/color'));
    expect(await screen.findByRole('heading', { name: 'Колір застосунку' })).toBeTruthy();
  });

  it('explains an expired SMS code', async () => {
    renderAppAt('/login/phone');
    fireEvent.change(await screen.findByLabelText('Номер телефону'), {
      target: { value: '67 123 45 67' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Отримати код' }));

    expect(await screen.findByText('+380 67 123 45 67')).toBeTruthy();
    typeCode(MOCK_EXPIRED_CODE);
    fireEvent.click(screen.getByRole('button', { name: 'Підтвердити' }));
    expect((await screen.findByRole('alert')).textContent).toBe('Код уже не діє. Надішліть новий.');
  });

  it('explains too many code requests', async () => {
    renderAppAt('/login/phone');
    const phoneField = await screen.findByLabelText('Номер телефону');
    for (let request = 0; request < 6; request += 1) {
      fireEvent.change(phoneField, { target: { value: '67 123 45 67' } });
      fireEvent.click(screen.getByRole('button', { name: 'Отримати код' }));
      if (request < 5) {
        fireEvent.click(await screen.findByRole('button', { name: 'Змінити' }));
      }
    }
    expect((await screen.findByRole('alert')).textContent).toBe(
      'Забагато запитів. Спробуйте трохи пізніше.',
    );
  });

  it('logs in through Telegram once the bot confirms', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const router = renderAppAt('/login/telegram');
      const link = await screen.findByRole('link', { name: 'Відкрити Telegram' });
      expect(link.getAttribute('href')).toMatch(/^https:\/\/t\.me\/freecook_bot\?start=/);
      await vi.advanceTimersByTimeAsync(6000);
      await waitFor(() => expect(router.getPathname()).toBe('/'));
    } finally {
      vi.useRealTimers();
    }
  });

  it('answers the same for any email on forgot password', async () => {
    renderAppAt('/forgot-password');
    fireEvent.change(await screen.findByLabelText('Електронна пошта'), {
      target: { value: 'nobody@example.com' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Надіслати посилання' }));
    expect(await screen.findByRole('heading', { name: 'Перевірте пошту' })).toBeTruthy();
  });

  it('refuses a used reset link', async () => {
    renderAppAt('/reset-password?uid=1&token=expired');
    fireEvent.change(await screen.findByLabelText('Новий пароль'), {
      target: { value: 'freecook27' },
    });
    fireEvent.change(screen.getByLabelText('Повторіть пароль'), {
      target: { value: 'freecook27' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Зберегти пароль' }));
    expect((await screen.findByRole('alert')).textContent).toBe(
      'Посилання вже не діє. Надішліть нове.',
    );
  });
});
