import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useSearchParams } from 'react-router-dom';

import { authApi } from '../../api/auth';
import { toAuthApiError } from '../../api/authErrors';
import AuthBackLink from './AuthBackLink';
import AuthErrorMessage from './AuthErrorMessage';
import TheAuthLayout from './TheAuthLayout';
import { getPasswordErrorKey } from './validation';

const LOGIN_PATH = '/login';
const FORGOT_PATH = '/forgot-password';

// No board: built from Forgot3 / DForgot. The email link (FC-107) opens
// /reset-password?uid=…&token=… and works once.
export default function ResetPasswordPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const uid = searchParams.get('uid') ?? '';
  const token = searchParams.get('token') ?? '';
  const [password, setPassword] = useState('');
  const [repeat, setRepeat] = useState('');
  const [passwordErrorKey, setPasswordErrorKey] = useState<string | null>(null);
  const [isMismatch, setIsMismatch] = useState(false);

  const reset = useMutation({ mutationFn: () => authApi.resetPassword(uid, token, password) });
  const isLinkInvalid =
    !uid ||
    !token ||
    (reset.error ? toAuthApiError(reset.error).code === 'reset_link_invalid' : false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextError = getPasswordErrorKey(password, true);
    const isNextMismatch = !nextError && password !== repeat;
    setPasswordErrorKey(nextError);
    setIsMismatch(isNextMismatch);
    if (!nextError && !isNextMismatch && !reset.isPending) {
      reset.mutate();
    }
  }

  return (
    <TheAuthLayout brandTitle={t('auth.reset.brandTitle')}>
      <AuthBackLink to={LOGIN_PATH} label={t('auth.back.toLogin')} />

      {reset.isSuccess ? (
        <>
          <div className="fc-auth__intro" role="status">
            <h1 className="fc-auth__title">{t('auth.reset.doneTitle')}</h1>
            <p className="fc-auth__text">{t('auth.reset.doneText')}</p>
          </div>
          <Link to={LOGIN_PATH} className="fc-btn fc-btn--primary fc-btn--block">
            {t('auth.reset.toLogin')}
          </Link>
        </>
      ) : isLinkInvalid ? (
        <>
          <div className="fc-auth__intro">
            <h1 className="fc-auth__title">{t('auth.reset.title')}</h1>
          </div>
          {reset.error ? (
            <AuthErrorMessage error={reset.error} />
          ) : (
            <p className="fc-field__error" role="alert">
              {t('auth.reset.missingLink')}
            </p>
          )}
          <Link to={FORGOT_PATH} className="fc-btn fc-btn--primary fc-btn--block">
            {t('auth.reset.requestNew')}
          </Link>
        </>
      ) : (
        <>
          <div className="fc-auth__intro">
            <h1 className="fc-auth__title">{t('auth.reset.title')}</h1>
            <p className="fc-auth__text">{t('auth.reset.text')}</p>
          </div>
          <form className="fc-auth__fields" onSubmit={handleSubmit} noValidate>
            <div className="fc-field">
              <label htmlFor="reset-password" className="fc-field__label">
                {t('auth.reset.newPassword')}
              </label>
              <input
                id="reset-password"
                className="fc-input"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-invalid={passwordErrorKey ? true : undefined}
                aria-describedby="reset-password-hint"
              />
              {passwordErrorKey ? (
                <p className="fc-field__error" id="reset-password-hint">
                  {t(passwordErrorKey)}
                </p>
              ) : (
                <span className="fc-field__hint" id="reset-password-hint">
                  {t('auth.passwordHint')}
                </span>
              )}
            </div>
            <div className="fc-field">
              <label htmlFor="reset-repeat" className="fc-field__label">
                {t('auth.reset.repeatPassword')}
              </label>
              <input
                id="reset-repeat"
                className="fc-input"
                type="password"
                autoComplete="new-password"
                value={repeat}
                onChange={(event) => setRepeat(event.target.value)}
                aria-invalid={isMismatch || undefined}
                aria-describedby={isMismatch ? 'reset-repeat-error' : undefined}
              />
              {isMismatch && (
                <p className="fc-field__error" id="reset-repeat-error">
                  {t('auth.reset.mismatch')}
                </p>
              )}
            </div>
            <AuthErrorMessage error={reset.error} />
            <button
              type="submit"
              className="fc-btn fc-btn--primary fc-btn--block"
              aria-busy={reset.isPending || undefined}
            >
              {t('auth.reset.submit')}
            </button>
          </form>
        </>
      )}
    </TheAuthLayout>
  );
}
