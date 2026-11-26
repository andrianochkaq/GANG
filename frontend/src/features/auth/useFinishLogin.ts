import { useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { startSession } from '../../api/session';

export const HOME_PATH = '/';

type AuthLocationState = { from?: string } | null;

// Where ProtectedRoute was sending the user before the login screen.
export function getRedirectTarget(state: unknown): string {
  const from = (state as AuthLocationState)?.from;
  return typeof from === 'string' && from.startsWith('/') && !from.startsWith('//')
    ? from
    : HOME_PATH;
}

export function useFinishLogin() {
  const navigate = useNavigate();
  const location = useLocation();

  return useCallback(
    (access: string) => {
      startSession(access);
      // New accounts pick the app colour next (FC-202) once that screen exists.
      navigate(getRedirectTarget(location.state), { replace: true });
    },
    [navigate, location.state],
  );
}
