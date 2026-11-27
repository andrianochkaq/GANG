import { APP_PATHS } from '../../routes/paths';
import type { NavIconName } from './NavIcon';

export type NavItem = {
  id: NavIconName;
  path: string;
  labelKey: string;
};

// Nav3 / DSide: four tab roots in this order; Calories only when enabled.
const NAV_ITEMS: NavItem[] = [
  { id: 'fridge', path: APP_PATHS.home, labelKey: 'shell.nav.fridge' },
  { id: 'chef', path: APP_PATHS.chef, labelKey: 'shell.nav.chef' },
  { id: 'calories', path: APP_PATHS.calories, labelKey: 'shell.nav.calories' },
  { id: 'profile', path: APP_PATHS.profile, labelKey: 'shell.nav.profile' },
];

export function getNavItems(isCaloriesEnabled: boolean): NavItem[] {
  return NAV_ITEMS.filter((item) => isCaloriesEnabled || item.id !== 'calories');
}

// Sub-screens hide the bottom nav on mobile (02-layout-and-screens.md);
// Shopping is the exception and keeps it.
const SUB_SCREEN_PATHS: readonly string[] = [APP_PATHS.fridges, APP_PATHS.recipes];

export function isSubScreen(pathname: string): boolean {
  return SUB_SCREEN_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

// A link stays active on its nested routes (/chef/123); home only on "/".
export function isPathActive(path: string, pathname: string): boolean {
  if (path === APP_PATHS.home) {
    return pathname === APP_PATHS.home;
  }
  return pathname === path || pathname.startsWith(`${path}/`);
}
