// Client-side checks that save a round trip; the backend still validates
// (Django password validators, E.164 normalisation).
export const MIN_PASSWORD_LENGTH = 8;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PHONE_DIGITS = 7;
const MAX_E164_DIGITS = 15;

export function getEmailErrorKey(email: string): string | null {
  const trimmed = email.trim();
  if (!trimmed) {
    return 'auth.validation.emailRequired';
  }
  return EMAIL_PATTERN.test(trimmed) ? null : 'auth.validation.emailInvalid';
}

export function getPasswordErrorKey(password: string, shouldCheckLength: boolean): string | null {
  if (!password) {
    return 'auth.validation.passwordRequired';
  }
  if (shouldCheckLength && password.length < MIN_PASSWORD_LENGTH) {
    return 'auth.validation.passwordShort';
  }
  return null;
}

// "+380" + "067 123 45 67" → "+380671234567": a leading trunk 0 is dropped.
export function toE164(dialCode: string, localNumber: string): string | null {
  const digits = localNumber.replace(/\D/g, '').replace(/^0+/, '');
  const dialDigits = dialCode.replace(/\D/g, '');
  if (digits.length < MIN_PHONE_DIGITS || dialDigits.length + digits.length > MAX_E164_DIGITS) {
    return null;
  }
  return `+${dialDigits}${digits}`;
}

// "+380671234567" → "+380 67 123 45 67" for the Ukrainian number card.
export function formatPhoneForDisplay(e164: string, dialCode: string): string {
  const local = e164.slice(dialCode.length);
  if (dialCode === '+380' && local.length === 9) {
    return `${dialCode} ${local.slice(0, 2)} ${local.slice(2, 5)} ${local.slice(5, 7)} ${local.slice(7)}`;
  }
  return `${dialCode} ${local}`;
}
