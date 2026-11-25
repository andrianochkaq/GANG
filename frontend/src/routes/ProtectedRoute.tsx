import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { refreshAccessToken } from '../api/session';
import { useAuthStore } from '../store/authStore';

export const LOGIN_PATH = '/login';

// After a reload the access token is gone (it lives in memory), so the
// refresh cookie is tried once before deciding the user is logged out.
export default function ProtectedRoute() {
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

  if (status === 'anonymous') {
    return (
      <Navigate
        to={LOGIN_PATH}
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }

  return <Outlet />;
}
