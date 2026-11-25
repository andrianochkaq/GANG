import { useCallback, useEffect, useState } from 'react';

// FC-102: a new code can be requested 60 seconds after the last one.
export const RESEND_DELAY_SECONDS = 60;

const SECONDS_PER_MINUTE = 60;
const TICK_MS = 1000;

export function formatCountdown(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / SECONDS_PER_MINUTE);
  const seconds = totalSeconds % SECONDS_PER_MINUTE;
  return `${minutes}:${String(seconds).padStart(2, '0')}`;
}

export function useResendTimer(delaySeconds = RESEND_DELAY_SECONDS) {
  const [secondsLeft, setSecondsLeft] = useState(delaySeconds);

  useEffect(() => {
    if (secondsLeft <= 0) {
      return undefined;
    }
    const timer = window.setTimeout(() => setSecondsLeft((left) => left - 1), TICK_MS);
    return () => window.clearTimeout(timer);
  }, [secondsLeft]);

  const restart = useCallback(() => setSecondsLeft(delaySeconds), [delaySeconds]);

  return { secondsLeft, canResend: secondsLeft <= 0, restart };
}
