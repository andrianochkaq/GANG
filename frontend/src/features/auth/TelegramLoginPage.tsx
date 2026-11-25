import { useMutation, useQuery } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';

import { authApi } from '../../api/auth';
import AuthBackLink from './AuthBackLink';
import AuthErrorMessage from './AuthErrorMessage';
import AuthIcon from './AuthIcon';
import TheAuthLayout from './TheAuthLayout';
import { useFinishLogin } from './useFinishLogin';

// architecture.md 7.1: the site polls the login request every 2 s.
export const TELEGRAM_POLL_INTERVAL_MS = 2000;

const LOGIN_PATH = '/login';

// No board: built from the Phone3 / DPhone layout (back link, title, one
// primary action, a waiting state).
export default function TelegramLoginPage() {
  const { t } = useTranslation();
  const finishLogin = useFinishLogin();

  const start = useMutation({ mutationFn: () => authApi.startTelegramLogin() });
  const { mutate: startLogin } = start;
  const request = start.data;
  // StrictMode runs effects twice in development; one login request is enough.
  const hasStartedRef = useRef(false);

  useEffect(() => {
    if (!hasStartedRef.current) {
      hasStartedRef.current = true;
      startLogin();
    }
  }, [startLogin]);

  const status = useQuery({
    queryKey: ['auth', 'telegram', request?.token],
    queryFn: () => authApi.getTelegramLoginStatus(request?.token ?? ''),
    enabled: Boolean(request),
    refetchInterval: (query) =>
      query.state.data?.status === 'pending' || !query.state.data
        ? TELEGRAM_POLL_INTERVAL_MS
        : false,
    refetchOnWindowFocus: true,
    gcTime: 0,
  });

  const result = status.data;
  useEffect(() => {
    if (result?.status === 'confirmed') {
      finishLogin(result.access);
    }
  }, [result, finishLogin]);

  const isExpired = result?.status === 'expired';

  return (
    <TheAuthLayout
      brandTitle={t('auth.telegram.brandTitle')}
      brandText={t('auth.telegram.brandText')}
    >
      <AuthBackLink to={LOGIN_PATH} label={t('auth.back.otherMethods')} />

      <div className="fc-auth__intro">
        <h1 className="fc-auth__title">{t('auth.telegram.title')}</h1>
        <p className="fc-auth__text">{t('auth.telegram.text')}</p>
      </div>

      {isExpired || start.isError ? (
        <>
          {isExpired && (
            <p className="fc-field__error" role="alert">
              {t('auth.telegram.expired')}
            </p>
          )}
          <AuthErrorMessage error={start.error} />
          <button
            type="button"
            className="fc-btn fc-btn--primary fc-btn--block"
            onClick={() => startLogin()}
            aria-busy={start.isPending || undefined}
          >
            {t('auth.telegram.retry')}
          </button>
        </>
      ) : (
        <>
          <div className="fc-auth__wait" role="status">
            <span className="fc-auth__spinner" aria-hidden="true" />
            {request ? t('auth.telegram.waiting') : t('auth.telegram.preparing')}
          </div>
          <AuthErrorMessage error={status.error} />
          {request ? (
            <a
              href={request.deepLink}
              target="_blank"
              rel="noopener noreferrer"
              className="fc-btn fc-btn--primary fc-btn--block"
            >
              <AuthIcon name="telegram" />
              {t('auth.telegram.open')}
            </a>
          ) : (
            <button
              type="button"
              className="fc-btn fc-btn--primary fc-btn--block"
              aria-disabled="true"
            >
              <AuthIcon name="telegram" />
              {t('auth.telegram.open')}
            </button>
          )}
          <p className="fc-auth__note">{t('auth.telegram.note')}</p>
        </>
      )}
    </TheAuthLayout>
  );
}
