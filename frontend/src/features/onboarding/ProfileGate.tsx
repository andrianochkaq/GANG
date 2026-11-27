import { useLayoutEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { useThemeStore } from '../../store/themeStore';
import { getRedirectTarget } from '../auth/useFinishLogin';
import { ONBOARDING_COLOR_PATH } from './onboardingPaths';
import { useProfile } from './useProfile';

// Sits inside ProtectedRoute. Loads /api/me/ on every login (any device),
// applies the saved theme, and sends an account that has not finished
// onboarding to the colour screen. Once it is done the screen is closed.
// The saved colour is applied in a layout effect, so it lands in the same
// commit as the profile and can never overwrite a colour the user picks
// a moment later.
export default function ProfileGate() {
  const { t } = useTranslation();
  const location = useLocation();
  const setThemeId = useThemeStore((state) => state.setThemeId);
  const profileQuery = useProfile();
  const profile = profileQuery.data;
  const savedThemeId = profile?.themeColor;

  useLayoutEffect(() => {
    if (savedThemeId) {
      setThemeId(savedThemeId);
    }
  }, [savedThemeId, setThemeId]);

  if (!profile) {
    if (profileQuery.isError) {
      return (
        <main className="fc-page">
          <p className="fc-field__error" role="alert">
            {t('onboarding.profile.loadError')}
          </p>
          <button
            type="button"
            className="fc-btn fc-btn--primary fc-btn--block"
            onClick={() => void profileQuery.refetch()}
          >
            {t('onboarding.profile.retry')}
          </button>
        </main>
      );
    }
    return (
      <main className="fc-page">
        <div className="fc-skeleton" aria-busy="true">
          <span className="fc-sr">{t('onboarding.profile.loading')}</span>
        </div>
      </main>
    );
  }

  const isOnColorScreen = location.pathname === ONBOARDING_COLOR_PATH;

  if (!profile.isOnboardingDone && !isOnColorScreen) {
    return (
      <Navigate
        to={ONBOARDING_COLOR_PATH}
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }

  if (profile.isOnboardingDone && isOnColorScreen) {
    return <Navigate to={getRedirectTarget(location.state)} replace />;
  }

  return <Outlet />;
}
