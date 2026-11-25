import { describe, expect, it } from 'vitest';

import { formatCountdown } from './useResendTimer';
import { formatPhoneForDisplay, getEmailErrorKey, getPasswordErrorKey, toE164 } from './validation';

describe('toE164', () => {
  it('joins the country code and the local number', () => {
    expect(toE164('+380', '67 123 45 67')).toBe('+380671234567');
  });

  it('drops the leading trunk zero of a local number', () => {
    expect(toE164('+380', '067-123-45-67')).toBe('+380671234567');
  });

  it('refuses numbers that are too short', () => {
    expect(toE164('+380', '67 12')).toBeNull();
  });
});

describe('form checks', () => {
  it('asks for a valid email', () => {
    expect(getEmailErrorKey('')).toBe('auth.validation.emailRequired');
    expect(getEmailErrorKey('marta@')).toBe('auth.validation.emailInvalid');
    expect(getEmailErrorKey(' marta@example.com ')).toBeNull();
  });

  it('checks the password length only on registration', () => {
    expect(getPasswordErrorKey('short', true)).toBe('auth.validation.passwordShort');
    expect(getPasswordErrorKey('short', false)).toBeNull();
  });
});

describe('formatting', () => {
  it('shows a Ukrainian number in groups', () => {
    expect(formatPhoneForDisplay('+380671234567', '+380')).toBe('+380 67 123 45 67');
  });

  it('shows the resend countdown as m:ss', () => {
    expect(formatCountdown(58)).toBe('0:58');
    expect(formatCountdown(60)).toBe('1:00');
  });
});
