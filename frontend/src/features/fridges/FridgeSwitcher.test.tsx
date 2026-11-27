import { cleanup, fireEvent, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import '../../i18n';
import { createMockAuthApi, resetAuthMock } from '../../api/authMock';
import { fridgesApi } from '../../api/fridges';
import { resetFridgesMock } from '../../api/fridgesMock';
import type { Fridge } from '../../api/fridgesTypes';
import { renderAppAt } from '../auth/authTestUtils';
import { useAuthStore } from '../../store/authStore';

vi.mock('../../api/auth', async () => {
  const { createMockAuthApi } = await import('../../api/authMock');
  return { authApi: createMockAuthApi(0), isAuthMockEnabled: () => true };
});

vi.mock('../../api/profile', () => ({
  profileApi: {
    getProfile: () => Promise.resolve({ themeColor: 'white', isOnboardingDone: true }),
    updateProfile: () => Promise.resolve({ themeColor: 'white', isOnboardingDone: true }),
  },
}));

vi.mock('../../api/fridges', async () => {
  const { createMockFridgesApi } = await import('../../api/fridgesMock');
  return { fridgesApi: createMockFridgesApi(0) };
});

const HOME: Fridge = {
  id: '11111111-1111-4111-8111-111111111111',
  name: 'Наш холодильник',
  role: 'owner',
  memberCount: 3,
  productCount: 12,
  isCurrent: true,
};
const DACHA: Fridge = {
  id: '22222222-2222-4222-8222-222222222222',
  name: 'На дачі',
  role: 'owner',
  memberCount: 2,
  productCount: 5,
  isCurrent: false,
};
const PARENTS: Fridge = {
  id: '33333333-3333-4333-8333-333333333333',
  name: 'У батьків',
  role: 'member',
  memberCount: 4,
  productCount: 1,
  isCurrent: false,
};

async function openSwitcherAt(path = '/fridges') {
  await createMockAuthApi(0).loginEmail('marta@example.com', 'freecook26');
  const router = renderAppAt(path);
  await screen.findByRole('dialog', { name: 'Ваші холодильники' });
  await screen.findByText('Наш холодильник', { selector: '.fc-switcher__name' });
  return router;
}

function getRow(name: string) {
  const nameNode = screen.getByText(name, { selector: '.fc-switcher__name' });
  return nameNode.closest('.fc-switcher__row') as HTMLElement;
}

function getPick(name: string) {
  return getRow(name).querySelector('.fc-switcher__pick') as HTMLElement;
}

// The sidebar card: both navs render in jsdom, the card sits in the sidebar.
function getSidebarCardName() {
  const sidebar = document.querySelector('.fc-sidebar') as HTMLElement;
  return sidebar.querySelector('.fc-fridgecard__name')?.textContent;
}

describe('FridgeSwitcher', () => {
  beforeEach(() => {
    resetAuthMock();
    resetFridgesMock([HOME, DACHA, PARENTS]);
    useAuthStore.setState({ accessToken: null, status: 'unknown' });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('lists every fridge with members and products and marks the current one', async () => {
    await openSwitcherAt();

    const current = getRow('Наш холодильник');
    expect(within(current).getByText('3 учасники · 12 продуктів')).toBeTruthy();
    expect(within(current).getByText('поточний')).toBeTruthy();
    expect(getPick('Наш холодильник').getAttribute('aria-current')).toBe('true');
    expect(within(getRow('На дачі')).getByText('2 учасники · 5 продуктів')).toBeTruthy();
    expect(within(getRow('На дачі')).queryByText('поточний')).toBeNull();
  });

  it('shows «Лише ви» for a fridge with one member', async () => {
    resetFridgesMock([{ ...HOME, memberCount: 1, productCount: 8 }]);
    await openSwitcherAt();

    expect(screen.getByText('Лише ви · 8 продуктів')).toBeTruthy();
  });

  it('offers rename only for fridges the user owns', async () => {
    await openSwitcherAt();

    expect(screen.getByRole('button', { name: 'Перейменувати «На дачі»' })).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Перейменувати «У батьків»' })).toBeNull();
  });

  it('switches the fridge in one click, closes and updates the sidebar card', async () => {
    const select = vi.spyOn(fridgesApi, 'selectFridge');
    const router = await openSwitcherAt();
    expect(getSidebarCardName()).toBe('Наш холодильник');

    fireEvent.click(getPick('На дачі'));

    await waitFor(() => expect(router.getPathname()).toBe('/'));
    expect(select).toHaveBeenCalledWith(DACHA.id);
    expect(screen.queryByRole('dialog')).toBeNull();
    await waitFor(() => expect(getSidebarCardName()).toBe('На дачі'));
    // The sidebar card and the one on the home placeholder.
    expect(screen.getAllByText('2 учасники · змінити')).toHaveLength(2);
  });

  it('keeps the choice for the next visit (the backend remembers it)', async () => {
    await openSwitcherAt();
    fireEvent.click(getPick('У батьків'));
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
    cleanup();

    await openSwitcherAt('/fridges');
    expect(within(getRow('У батьків')).getByText('поточний')).toBeTruthy();
    expect(within(getRow('Наш холодильник')).queryByText('поточний')).toBeNull();
  });

  it('rolls back and explains when switching fails', async () => {
    vi.spyOn(fridgesApi, 'selectFridge').mockRejectedValueOnce(new Error('offline'));
    await openSwitcherAt();

    fireEvent.click(getPick('На дачі'));

    expect(
      await screen.findByText('Не вдалося перемкнути холодильник. Спробуйте ще раз.'),
    ).toBeTruthy();
    expect(within(getRow('Наш холодильник')).getByText('поточний')).toBeTruthy();
    expect(screen.getByRole('dialog')).toBeTruthy();
  });

  it('renames a fridge with the pencil', async () => {
    await openSwitcherAt();

    fireEvent.click(screen.getByRole('button', { name: 'Перейменувати «Наш холодильник»' }));
    const input = screen.getByLabelText('Нова назва');
    expect((input as HTMLInputElement).value).toBe('Наш холодильник');
    fireEvent.change(input, { target: { value: '  Мій холодильник ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Зберегти' }));

    expect(
      await screen.findByText('Мій холодильник', { selector: '.fc-switcher__name' }),
    ).toBeTruthy();
    expect(screen.queryByLabelText('Нова назва')).toBeNull();
    await waitFor(() => expect(getSidebarCardName()).toBe('Мій холодильник'));
    // The saved form took the focused field away; Esc still closes the list.
    expect(document.activeElement).toBe(screen.getByRole('dialog'));
    fireEvent.keyDown(document.body, { key: 'Escape' });
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  });

  it('does not save an empty name and keeps the old one on cancel', async () => {
    const rename = vi.spyOn(fridgesApi, 'renameFridge');
    await openSwitcherAt();

    fireEvent.click(screen.getByRole('button', { name: 'Перейменувати «На дачі»' }));
    fireEvent.change(screen.getByLabelText('Нова назва'), { target: { value: '   ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Зберегти' }));

    expect(screen.getByText('Введіть назву холодильника.')).toBeTruthy();
    expect(rename).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Скасувати' }));
    expect(screen.getByText('На дачі', { selector: '.fc-switcher__name' })).toBeTruthy();
  });

  it('creates a new fridge', async () => {
    await openSwitcherAt();

    fireEvent.click(screen.getByRole('button', { name: 'Новий холодильник' }));
    fireEvent.change(screen.getByLabelText('Назва нового холодильника'), {
      target: { value: 'Гуртожиток' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Створити' }));

    const row = await screen.findByText('Гуртожиток', { selector: '.fc-switcher__name' });
    expect(
      within(row.closest('.fc-switcher__row') as HTMLElement).getByText('Лише ви · 0 продуктів'),
    ).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Новий холодильник' })).toBeTruthy();
  });

  it('closes with Esc and with «Закрити»', async () => {
    const router = await openSwitcherAt();
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
    await waitFor(() => expect(router.getPathname()).toBe('/'));
    cleanup();

    const second = await openSwitcherAt();
    fireEvent.click(screen.getByRole('button', { name: 'Закрити' }));
    await waitFor(() => expect(second.getPathname()).toBe('/'));
  });

  it('opens from the fridge card on the home and Profile screens', async () => {
    await createMockAuthApi(0).loginEmail('marta@example.com', 'freecook26');
    const router = renderAppAt('/profile');
    await screen.findByRole('heading', { level: 1, name: 'Профіль' });
    const main = document.querySelector('main') as HTMLElement;

    fireEvent.click(await within(main).findByRole('link', { name: /Наш холодильник/ }));

    await screen.findByRole('dialog', { name: 'Ваші холодильники' });
    expect(router.getPathname()).toBe('/fridges');
  });
});
