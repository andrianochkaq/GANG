import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Trans, useTranslation } from 'react-i18next';
import { Link, useSearchParams } from 'react-router-dom';

import { authApi } from '../../api/auth';
import BaseCodeInput, { CODE_LENGTH } from '../../components/ui/BaseCodeInput';
import AuthBackLink from './AuthBackLink';
import AuthErrorMessage from './AuthErrorMessage';
import AuthResendHint from './AuthResendHint';
import TheAuthLayout from './TheAuthLayout';
import { useFinishLogin } from './useFinishLogin';
import { useResendTimer } from './useResendTimer';

// Step 2 of 3; step 3 is the app colour (FC-202).
const STEP_PROGRESS_PERCENT = 66;
const REGISTER_PATH = '/login?tab=register';

export default function EmailVerifyPage() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email')?.trim() ?? '';
  const finishLogin = useFinishLogin();
  const timer = useResendTimer();
  const [code, setCode] = useState('');
  const [isIncomplete, setIsIncomplete] = useState(false);

  const verify = useMutation({
    mutationFn: () => authApi.verifyEmail(email, code),
    onSuccess: (tokens) => finishLogin(tokens.access),
  });

  const resend = useMutation({
    mutationFn: () => authApi.resendEmailCode(email),
    onSuccess: () => {
      timer.restart();
      setCode('');
      verify.reset();
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const isComplete = code.length === CODE_LENGTH;
    setIsIncomplete(!isComplete);
    if (isComplete && !verify.isPending) {
      verify.mutate();
    }
  }

  const brand = {
    brandTitle: t('auth.verify.brandTitle'),
    brandSteps: {
      title: t('auth.verify.howTitle'),
      items: [t('auth.verify.howStep1'), t('auth.verify.howStep2'), t('auth.verify.howStep3')],
    },
  };

  if (!email) {
    return (
      <TheAuthLayout {...brand}>
        <AuthBackLink to={REGISTER_PATH} label={t('auth.back.toRegistration')} />
        <p className="fc-field__error" role="alert">
          {t('auth.verify.missingEmail')}
        </p>
        <Link to={REGISTER_PATH} className="fc-btn fc-btn--primary fc-btn--block">
          {t('auth.login.submitRegister')}
        </Link>
      </TheAuthLayout>
    );
  }

  const hasCodeError = Boolean(verify.error) || isIncomplete;

  return (
    <TheAuthLayout {...brand}>
      <AuthBackLink to={REGISTER_PATH} label={t('auth.back.toRegistration')} />

      <div className="fc-steps">
        <span className="fc-steps__label">{t('auth.verify.step')}</span>
        <div
          className="fc-progress"
          role="progressbar"
          aria-label={t('auth.verify.step')}
          aria-valuenow={STEP_PROGRESS_PERCENT}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span style={{ width: `${STEP_PROGRESS_PERCENT}%` }} />
        </div>
      </div>

      <div className="fc-auth__intro">
        <h1 className="fc-auth__title">{t('auth.verify.title')}</h1>
        <p className="fc-auth__text">
          <Trans i18nKey="auth.verify.sentTo" values={{ email }} components={{ b: <b /> }} />
        </p>
      </div>

      <form className="fc-auth__fields" onSubmit={handleSubmit} noValidate>
        <BaseCodeInput
          value={code}
          onChange={(next) => {
            setCode(next);
            setIsIncomplete(false);
          }}
          legend={t('auth.verify.legend')}
          isInvalid={hasCodeError}
          describedBy="verify-resend"
        />
        {isIncomplete && (
          <p className="fc-field__error" role="alert">
            {t('auth.code.incomplete')}
          </p>
        )}
        <AuthErrorMessage error={verify.error ?? resend.error} />
        {resend.isSuccess && timer.secondsLeft > 0 && (
          <p className="fc-field__hint" role="status">
            {t('auth.verify.resent')}
          </p>
        )}
        <AuthResendHint
          id="verify-resend"
          secondsLeft={timer.secondsLeft}
          countdownKey="auth.verify.resendIn"
          linkKey="auth.verify.resendNow"
          prefixKey="auth.verify.resendNowPrefix"
          suffixKey="auth.verify.resendNowSuffix"
          onResend={() => resend.mutate()}
          isSending={resend.isPending}
        />
        <button
          type="submit"
          className="fc-btn fc-btn--primary fc-btn--block"
          aria-busy={verify.isPending || undefined}
        >
          {t('auth.verify.submit')}
        </button>
      </form>

      <div className="fc-auth__infobox">
        <span className="fc-auth__infotitle">{t('auth.verify.howTitle')}</span>
        <ol className="fc-auth__infolist">
          <li>{t('auth.verify.howStep1')}</li>
          <li>{t('auth.verify.howStep2')}</li>
          <li>{t('auth.verify.howStep3')}</li>
        </ol>
      </div>
    </TheAuthLayout>
  );
}
