import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom';

import { authApi } from '../../api/auth';
import { toAuthApiError } from '../../api/authErrors';
import mascotUrl from '../../assets/mascot-fridge.png';
import AuthErrorMessage from './AuthErrorMessage';
import AuthIcon from './AuthIcon';
import TheAuthLayout from './TheAuthLayout';
import { useFinishLogin } from './useFinishLogin';
import { getEmailErrorKey, getPasswordErrorKey } from './validation';

type LoginMode = 'login' | 'register';

const REGISTER_TAB = 'register';

export function getVerifyPath(email: string): string {
  return `/register/verify?email=${encodeURIComponent(email)}`;
}

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const finishLogin = useFinishLogin();
  const [searchParams, setSearchParams] = useSearchParams();
  const mode: LoginMode = searchParams.get('tab') === REGISTER_TAB ? 'register' : 'login';
  const isRegister = mode === 'register';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [emailErrorKey, setEmailErrorKey] = useState<string | null>(null);
  const [passwordErrorKey, setPasswordErrorKey] = useState<string | null>(null);

  const submit = useMutation({
    mutationFn: async () => {
      const trimmedEmail = email.trim();
      if (isRegister) {
        await authApi.registerEmail(trimmedEmail, password);
        return null;
      }
      return authApi.loginEmail(trimmedEmail, password);
    },
    onSuccess: (tokens) => {
      if (tokens) {
        finishLogin(tokens.access);
      } else {
        navigate(getVerifyPath(email.trim()));
      }
    },
  });

  const isNotVerified = submit.error
    ? toAuthApiError(submit.error).code === 'email_not_verified'
    : false;

  function selectMode(nextMode: LoginMode) {
    submit.reset();
    setPasswordErrorKey(null);
    setSearchParams(nextMode === 'register' ? { tab: REGISTER_TAB } : {}, {
      replace: true,
      state: location.state,
    });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextEmailError = getEmailErrorKey(email);
    const nextPasswordError = getPasswordErrorKey(password, isRegister);
    setEmailErrorKey(nextEmailError);
    setPasswordErrorKey(nextPasswordError);
    if (!nextEmailError && !nextPasswordError && !submit.isPending) {
      submit.mutate();
    }
  }

  async function handleVerifyEmail() {
    const trimmedEmail = email.trim();
    // A fresh code; if resending is throttled the old one may still work.
    await authApi.resendEmailCode(trimmedEmail).catch(() => undefined);
    navigate(getVerifyPath(trimmedEmail));
  }

  return (
    <TheAuthLayout
      brandTitle={t('auth.login.brandTitle')}
      brandText={t('auth.login.brandText')}
      isRoot
    >
      <div className="fc-auth__mascot">
        <div className="fc-auth__mascotcircle">
          <img src={mascotUrl} alt={t('auth.mascotAlt')} />
        </div>
        <span className="fc-auth__wordmark">{t('app.name')}</span>
      </div>

      <div className="fc-auth__intro fc-auth__intro--desktop">
        <h1 className="fc-auth__title">
          {isRegister ? t('auth.login.desktopRegisterTitle') : t('auth.login.desktopTitle')}
        </h1>
        <p className="fc-auth__text">
          {isRegister ? t('auth.login.desktopRegisterText') : t('auth.login.desktopText')}
        </p>
      </div>

      <div className="fc-seg fc-seg--lg" role="tablist" aria-label={t('auth.login.modeLabel')}>
        <button
          type="button"
          role="tab"
          id="auth-tab-login"
          aria-controls="auth-panel"
          aria-selected={!isRegister}
          onClick={() => selectMode('login')}
        >
          {t('auth.login.tabLogin')}
        </button>
        <button
          type="button"
          role="tab"
          id="auth-tab-register"
          aria-controls="auth-panel"
          aria-selected={isRegister}
          onClick={() => selectMode('register')}
        >
          {t('auth.login.tabRegister')}
        </button>
      </div>

      <form
        id="auth-panel"
        role="tabpanel"
        aria-labelledby={isRegister ? 'auth-tab-register' : 'auth-tab-login'}
        className="fc-auth__fields"
        onSubmit={handleSubmit}
        noValidate
      >
        <div className="fc-field">
          <label htmlFor="auth-email" className="fc-field__label">
            {t('auth.email')}
          </label>
          <input
            id="auth-email"
            className="fc-input"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            aria-invalid={emailErrorKey ? true : undefined}
            aria-describedby={emailErrorKey ? 'auth-email-error' : undefined}
          />
          {emailErrorKey && (
            <p className="fc-field__error" id="auth-email-error">
              {t(emailErrorKey)}
            </p>
          )}
        </div>

        <div className="fc-field">
          <div className="fc-field__top">
            <label htmlFor="auth-password" className="fc-field__label">
              {t('auth.password')}
            </label>
            {!isRegister && (
              <Link to="/forgot-password" className="fc-field__link">
                {t('auth.login.forgotPassword')}
              </Link>
            )}
          </div>
          <input
            id="auth-password"
            className="fc-input"
            type="password"
            autoComplete={isRegister ? 'new-password' : 'current-password'}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            aria-invalid={passwordErrorKey ? true : undefined}
            aria-describedby={passwordErrorKey ? 'auth-password-error' : undefined}
          />
          {passwordErrorKey ? (
            <p className="fc-field__error" id="auth-password-error">
              {t(passwordErrorKey)}
            </p>
          ) : (
            isRegister && <span className="fc-field__hint">{t('auth.passwordHint')}</span>
          )}
        </div>

        <AuthErrorMessage error={submit.error} />
        {isNotVerified && (
          <button
            type="button"
            className="fc-btn fc-btn--tonal fc-btn--sm"
            onClick={handleVerifyEmail}
          >
            {t('auth.login.verifyEmail')}
          </button>
        )}

        <button
          type="submit"
          className="fc-btn fc-btn--primary fc-btn--block"
          aria-busy={submit.isPending || undefined}
        >
          {isRegister ? t('auth.login.submitRegister') : t('auth.login.submit')}
        </button>
      </form>

      <div className="fc-auth__divider">{t('auth.login.orWithoutPassword')}</div>

      <div className="fc-auth__methods">
        <Link to="/login/phone" state={location.state} className="fc-auth__method">
          <AuthIcon name="phone" />
          <span className="fc-auth__methodname">{t('auth.login.byPhone')}</span>
          <span className="fc-auth__methodhint">{t('auth.login.byPhoneHint')}</span>
        </Link>
        <Link to="/login/telegram" state={location.state} className="fc-auth__method">
          <AuthIcon name="telegram" />
          <span className="fc-auth__methodname">{t('auth.login.byTelegram')}</span>
          <span className="fc-auth__methodhint">{t('auth.login.byTelegramHint')}</span>
        </Link>
      </div>

      <p className="fc-auth__legal">{t('auth.legal')}</p>
    </TheAuthLayout>
  );
}
