import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';

import { authApi } from '../../api/auth';
import BaseCodeInput, { CODE_LENGTH } from '../../components/ui/BaseCodeInput';
import AuthBackLink from './AuthBackLink';
import AuthErrorMessage from './AuthErrorMessage';
import AuthIcon from './AuthIcon';
import AuthResendHint from './AuthResendHint';
import TheAuthLayout from './TheAuthLayout';
import { useFinishLogin } from './useFinishLogin';
import { useResendTimer } from './useResendTimer';
import { formatPhoneForDisplay, toE164 } from './validation';

// Ukraine first; the backend validates and normalises any E.164 number.
export const COUNTRY_CODES = [
  { country: 'UA', dialCode: '+380' },
  { country: 'PL', dialCode: '+48' },
  { country: 'DE', dialCode: '+49' },
  { country: 'CZ', dialCode: '+420' },
  { country: 'GB', dialCode: '+44' },
  { country: 'US', dialCode: '+1' },
] as const;

const LOGIN_PATH = '/login';

export default function PhoneLoginPage() {
  const { t } = useTranslation();
  const finishLogin = useFinishLogin();
  const timer = useResendTimer();
  const [dialCode, setDialCode] = useState<string>(COUNTRY_CODES[0].dialCode);
  const [localNumber, setLocalNumber] = useState('');
  const [isNumberInvalid, setIsNumberInvalid] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(null);
  const [code, setCode] = useState('');
  const [isIncomplete, setIsIncomplete] = useState(false);

  const requestCode = useMutation({
    mutationFn: (phone: string) => authApi.requestPhoneCode(phone),
    onSuccess: (_data, phone) => {
      setSentTo(phone);
      setCode('');
      timer.restart();
    },
  });

  const verify = useMutation({
    mutationFn: () => authApi.verifyPhone(sentTo ?? '', code),
    onSuccess: (result) => finishLogin(result.access),
  });

  function handleRequestCode(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const phone = toE164(dialCode, localNumber);
    setIsNumberInvalid(!phone);
    if (phone && !requestCode.isPending) {
      requestCode.mutate(phone);
    }
  }

  function handleVerify(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const isComplete = code.length === CODE_LENGTH;
    setIsIncomplete(!isComplete);
    if (isComplete && !verify.isPending) {
      verify.mutate();
    }
  }

  function handleChangeNumber() {
    setSentTo(null);
    setCode('');
    verify.reset();
    requestCode.reset();
  }

  return (
    <TheAuthLayout brandTitle={t('auth.phone.brandTitle')} brandText={t('auth.phone.brandText')}>
      <AuthBackLink to={LOGIN_PATH} label={t('auth.back.otherMethods')} />

      <div className="fc-auth__intro">
        <h1 className="fc-auth__title">{t('auth.phone.title')}</h1>
        <p className="fc-auth__text">
          {sentTo ? t('auth.phone.text') : t('auth.phone.desktopText')}
        </p>
      </div>

      {sentTo ? (
        <>
          <div className="fc-auth__numbercard">
            <span className="fc-auth__numbertext">
              <span className="fc-auth__numberlabel">{t('auth.phone.numberLabel')}</span>
              <span className="fc-auth__number">{formatPhoneForDisplay(sentTo, dialCode)}</span>
            </span>
            <button
              type="button"
              className="fc-btn fc-btn--tonal fc-btn--sm"
              onClick={handleChangeNumber}
            >
              {t('auth.phone.change')}
            </button>
          </div>

          <form className="fc-auth__fields" onSubmit={handleVerify} noValidate>
            <BaseCodeInput
              value={code}
              onChange={(next) => {
                setCode(next);
                setIsIncomplete(false);
              }}
              legend={t('auth.phone.legend')}
              isInvalid={Boolean(verify.error) || isIncomplete}
              describedBy="phone-resend"
            />
            {isIncomplete && (
              <p className="fc-field__error" role="alert">
                {t('auth.code.incomplete')}
              </p>
            )}
            <AuthErrorMessage error={verify.error ?? requestCode.error} />
            <AuthResendHint
              id="phone-resend"
              secondsLeft={timer.secondsLeft}
              countdownKey="auth.phone.resendIn"
              linkKey="auth.phone.resendNow"
              onResend={() => {
                verify.reset();
                requestCode.mutate(sentTo);
              }}
              isSending={requestCode.isPending}
            />
            <button
              type="submit"
              className="fc-btn fc-btn--primary fc-btn--block"
              aria-busy={verify.isPending || undefined}
            >
              {t('auth.phone.submit')}
            </button>
          </form>

          <div className="fc-banner fc-banner--info">
            <AuthIcon name="info" />
            <span>{t('auth.phone.noPassword')}</span>
          </div>
        </>
      ) : (
        <form className="fc-auth__fields" onSubmit={handleRequestCode} noValidate>
          <div className="fc-field">
            <label htmlFor="auth-phone" className="fc-field__label">
              {t('auth.phone.label')}
            </label>
            <div className="fc-inputrow">
              <select
                className="fc-select fc-auth__country"
                aria-label={t('auth.phone.countryCode')}
                value={dialCode}
                onChange={(event) => setDialCode(event.target.value)}
              >
                {COUNTRY_CODES.map((option) => (
                  <option key={option.country} value={option.dialCode}>
                    {`${option.country} ${option.dialCode}`}
                  </option>
                ))}
              </select>
              <input
                id="auth-phone"
                className="fc-input"
                type="tel"
                inputMode="tel"
                autoComplete="tel-national"
                value={localNumber}
                onChange={(event) => setLocalNumber(event.target.value)}
                aria-invalid={isNumberInvalid || undefined}
                aria-describedby="auth-phone-hint"
              />
            </div>
            {isNumberInvalid ? (
              <p className="fc-field__error" id="auth-phone-hint">
                {t('auth.phone.invalidNumber')}
              </p>
            ) : (
              <span className="fc-field__hint" id="auth-phone-hint">
                {t('auth.phone.codeHint')}
              </span>
            )}
          </div>
          <AuthErrorMessage error={requestCode.error} />
          <button
            type="submit"
            className="fc-btn fc-btn--primary fc-btn--block"
            aria-busy={requestCode.isPending || undefined}
          >
            {t('auth.phone.getCode')}
          </button>
          <p className="fc-auth__note">{t('auth.legal')}</p>
        </form>
      )}
    </TheAuthLayout>
  );
}
