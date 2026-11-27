import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useProfile } from '../../features/onboarding/useProfile';
import { APP_PATHS } from '../../routes/paths';
import BottomNav from './BottomNav';
import { getNavItems, isPathActive, isSubScreen } from './navItems';
import Sidebar from './Sidebar';

// The frame of every logged-in screen (02-layout-and-screens.md): below
// 1024 px the page with the bottom nav pinned under it, from 1024 px the
// sidebar beside it. CSS picks the one that shows. Sits inside ProfileGate,
// so the profile is already loaded.
export default function AppShell() {
  const { pathname } = useLocation();
  const profile = useProfile().data;
  const isCaloriesEnabled = profile?.caloriesEnabled ?? true;
  const items = getNavItems(isCaloriesEnabled);
  const hasBottomNav = !isSubScreen(pathname);

  if (!isCaloriesEnabled && isPathActive(APP_PATHS.calories, pathname)) {
    return <Navigate to={APP_PATHS.home} replace />;
  }

  return (
    <div className="fc-shell">
      <div className="fc-shell__sidebar">
        <Sidebar items={items} />
      </div>
      <main className={hasBottomNav ? 'fc-shell__main' : 'fc-shell__main--subscreen'}>
        <Outlet />
      </main>
      {hasBottomNav && (
        <div className="fc-shell__bottomnav">
          <BottomNav items={items} />
        </div>
      )}
    </div>
  );
}
