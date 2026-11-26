import { useTranslation } from 'react-i18next';

import { formatCountdown } from './useResendTimer';

type AuthResendHintProps = {
  id: string;
  secondsLeft: number;
  // i18n keys: the countdown sentence and the words around the resend link.
  countdownKey: string;
  linkKey: string;
  prefixKey?: string;
  suffixKey?: string;
  onResend: () => void;
  isSending: boolean;
};

// "Resend in 0:58" (CodeInput.md); when the timer ends the time becomes a link.
export default function AuthResendHint({
  id,
  secondsLeft,
  countdownKey,
  linkKey,
  prefixKey,
  suffixKey,
  onResend,
  isSending,
}: AuthResendHintProps) {
  const { t } = useTranslation();

  if (secondsLeft > 0) {
    return (
      <p className="fc-auth__resend" id={id} aria-live="off">
        {t(countdownKey, { time: formatCountdown(secondsLeft) })}
      </p>
    );
  }
  return (
    <p className="fc-auth__resend" id={id}>
      {prefixKey && `${t(prefixKey)} `}
      <button type="button" onClick={onResend} aria-busy={isSending || undefined}>
        {t(linkKey)}
      </button>
      {suffixKey && ` ${t(suffixKey)}`}
    </p>
  );
}
