import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { refreshAccessToken } from '../api/session';
import { getRedirectTarget } from '../features/auth/useFinishLogin';
import { useAuthStore } from '../store/authStore';

// The login and sign-up screens are for logged-out users only. A logged-in
// user who lands on one (the browser's back button after a login, a saved
// /login bookmark) goes on to the app instead of seeing the form again.
export default function GuestRoute() {
  const { t } = useTranslation();
  const location = useLocation();
  const status = useAuthStore((state) => state.status);

  useEffect(() => {
    if (status === 'unknown') {
      void refreshAccessToken();
    }
  }, [status]);

  if (status === 'unknown') {
    return (
      <main className="fc-page">
        <div className="fc-skeleton" aria-busy="true">
          <span className="fc-sr">{t('auth.checkingSession')}</span>
        </div>
      </main>
    );
  }

  if (status === 'authenticated') {
    // Same target as useFinishLogin, so a fresh login is not sent elsewhere.
    return <Navigate to={getRedirectTarget(location.state)} replace />;
  }

  return <Outlet />;
}
