import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import '../../i18n';
import { createMockAuthApi, resetAuthMock } from '../../api/authMock';
import type { Profile } from '../../api/profileTypes';
import { renderAppAt } from '../../features/auth/authTestUtils';
import { useAuthStore } from '../../store/authStore';
import Sidebar from './Sidebar';
import { getNavItems } from './navItems';

const profileState: { value: Profile } = {
  value: { themeColor: 'white', isOnboardingDone: true },
};

vi.mock('../../api/auth', async () => {
  const { createMockAuthApi } = await import('../../api/authMock');
  return { authApi: createMockAuthApi(0), isAuthMockEnabled: () => true };
});

vi.mock('../../api/profile', () => ({
  profileApi: {
    getProfile: () => Promise.resolve(profileState.value),
    updateProfile: () => Promise.resolve(profileState.value),
  },
}));

// Both navs are in the DOM; CSS shows one per width (jsdom applies no media
// queries). The bottom nav is the second «Основна навігація».
function getNavs() {
  return screen.getAllByRole('navigation', { name: 'Основна навігація' });
}

async function renderLoggedInAt(path: string) {
  await createMockAuthApi(0).loginEmail('marta@example.com', 'freecook26');
  const router = renderAppAt(path);
  await screen.findByRole('heading', { level: 1 });
  return router;
}

describe('AppShell', () => {
  beforeEach(() => {
    resetAuthMock();
    useAuthStore.setState({ accessToken: null, status: 'unknown' });
    profileState.value = { themeColor: 'white', isOnboardingDone: true };
  });

  afterEach(cleanup);

  it('shows the four tabs in the design order in both navs', async () => {
    await renderLoggedInAt('/');
    for (const nav of getNavs()) {
      expect(within(nav).getByRole('link', { name: 'Холодильник' })).toBeTruthy();
      expect(within(nav).getByRole('link', { name: 'AI-кухар' })).toBeTruthy();
      expect(within(nav).getByRole('link', { name: 'Калорії' })).toBeTruthy();
      expect(within(nav).getByRole('link', { name: 'Профіль' })).toBeTruthy();
    }
    const bottomLabels = within(getNavs()[1])
      .getAllByRole('link')
      .map((link) => link.textContent);
    expect(bottomLabels).toEqual(['Холодильник', 'AI-кухар', 'Калорії', 'Профіль']);
  });

  it.each([
    ['AI-кухар', '/chef'],
    ['Калорії', '/calories'],
    ['Профіль', '/profile'],
    ['Холодильник', '/'],
  ])('opens %s at %s from the bottom nav', async (label, path) => {
    const router = await renderLoggedInAt(path === '/' ? '/profile' : '/');
    fireEvent.click(within(getNavs()[1]).getByRole('link', { name: label }));

    expect(await screen.findByRole('heading', { level: 1, name: label })).toBeTruthy();
    expect(router.getPathname()).toBe(path);
    const active = within(getNavs()[1]).getByRole('link', { name: label });
    expect(active.getAttribute('aria-current')).toBe('page');
  });

  it('opens Shopping and the fridge list from the sidebar', async () => {
    const router = await renderLoggedInAt('/');
    const sidebar = getNavs()[0];

    fireEvent.click(within(sidebar).getByRole('link', { name: /Покупки/ }));
    expect(await screen.findByRole('heading', { level: 1, name: 'Покупки' })).toBeTruthy();
    expect(router.getPathname()).toBe('/shopping');

    fireEvent.click(within(getNavs()[0]).getByRole('link', { name: /Ваш холодильник/ }));
    expect(await screen.findByRole('heading', { level: 1, name: 'Холодильники' })).toBeTruthy();
    expect(router.getPathname()).toBe('/fridges');
  });

  it('keeps the bottom nav on Shopping but not on other sub-screens', async () => {
    await renderLoggedInAt('/shopping');
    expect(getNavs()).toHaveLength(2);
    cleanup();

    await renderLoggedInAt('/recipes');
    expect(getNavs()).toHaveLength(1);
  });

  it('hides Calories when the profile turns it off and leaves its route', async () => {
    profileState.value = { ...profileState.value, caloriesEnabled: false };
    const router = await renderLoggedInAt('/calories');

    expect(router.getPathname()).toBe('/');
    for (const nav of getNavs()) {
      expect(within(nav).queryByRole('link', { name: 'Калорії' })).toBeNull();
    }
  });
});

describe('Sidebar', () => {
  afterEach(cleanup);

  function renderSidebar(props: Partial<Parameters<typeof Sidebar>[0]> = {}) {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="*" element={<Sidebar items={getNavItems(true)} {...props} />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it('shows the current fridge and the open shopping count when known', () => {
    renderSidebar({ fridge: { name: 'Наш холодильник', memberCount: 3 }, openShoppingCount: 5 });

    expect(screen.getByText('Наш холодильник')).toBeTruthy();
    expect(screen.getByText('3 учасники · змінити')).toBeTruthy();
    expect(screen.getByText('5 покупок')).toBeTruthy();
  });

  it('shows a neutral card and no count before the data exists', () => {
    renderSidebar();

    expect(screen.getByText('Ваш холодильник')).toBeTruthy();
    expect(screen.getByText('змінити')).toBeTruthy();
    expect(screen.getByRole('link', { name: 'Покупки' })).toBeTruthy();
  });
});
