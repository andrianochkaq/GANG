import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import { authApi } from '../../api/auth';
import AuthBackLink from './AuthBackLink';
import AuthErrorMessage from './AuthErrorMessage';
import AuthIcon from './AuthIcon';
import TheAuthLayout from './TheAuthLayout';
import { getEmailErrorKey } from './validation';

const LOGIN_PATH = '/login';

export default function ForgotPasswordPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [emailErrorKey, setEmailErrorKey] = useState<string | null>(null);

  // FC-107 answers the same whether or not the email exists.
  const send = useMutation({
    mutationFn: (address: string) => authApi.requestPasswordReset(address),
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextError = getEmailErrorKey(email);
    setEmailErrorKey(nextError);
    if (!nextError && !send.isPending) {
      send.mutate(email.trim());
    }
  }

  return (
    <TheAuthLayout
      brandTitle={t('auth.forgot.brandTitle')}
      brandSteps={{
        title: t('auth.forgot.brandStepsTitle'),
        items: [
          t('auth.forgot.brandStep1'),
          t('auth.forgot.brandStep2'),
          t('auth.forgot.brandStep3'),
        ],
      }}
    >
      <AuthBackLink to={LOGIN_PATH} label={t('auth.back.toLogin')} />

      <div className="fc-auth__icontile">
        <AuthIcon name="mail" />
      </div>

      {send.isSuccess ? (
        <div className="fc-auth__intro" role="status">
          <h1 className="fc-auth__title">{t('auth.forgot.sentTitle')}</h1>
          <p className="fc-auth__text">{t('auth.forgot.sent', { email: send.variables })}</p>
        </div>
      ) : (
        <>
          <div className="fc-auth__intro">
            <h1 className="fc-auth__title">{t('auth.forgot.title')}</h1>
            <p className="fc-auth__text">{t('auth.forgot.text')}</p>
          </div>

          <form className="fc-auth__fields" onSubmit={handleSubmit} noValidate>
            <div className="fc-field">
              <label htmlFor="forgot-email" className="fc-field__label">
                {t('auth.email')}
              </label>
              <input
                id="forgot-email"
                className="fc-input"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                aria-invalid={emailErrorKey ? true : undefined}
                aria-describedby={emailErrorKey ? 'forgot-email-error' : undefined}
              />
              {emailErrorKey && (
                <p className="fc-field__error" id="forgot-email-error">
                  {t(emailErrorKey)}
                </p>
              )}
            </div>
            <AuthErrorMessage error={send.error} />
            <button
              type="submit"
              className="fc-btn fc-btn--primary fc-btn--block"
              aria-busy={send.isPending || undefined}
            >
              {t('auth.forgot.submit')}
            </button>
          </form>
        </>
      )}

      <div className="fc-auth__infobox">
        <span className="fc-auth__infotitle">{t('auth.forgot.whyTitle')}</span>
        <p className="fc-auth__infotext">{t('auth.forgot.whyText')}</p>
        <div className="fc-auth__chips">
          <Link to="/login/phone" className="fc-btn fc-btn--tonal fc-btn--sm">
            {t('auth.forgot.byPhone')}
          </Link>
          <Link to="/login/telegram" className="fc-btn fc-btn--tonal fc-btn--sm">
            {t('auth.forgot.byTelegram')}
          </Link>
        </div>
      </div>

      <p className="fc-auth__legal">{t('auth.forgot.linkNote')}</p>
    </TheAuthLayout>
  );
}
