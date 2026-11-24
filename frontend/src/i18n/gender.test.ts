import { describe, expect, it } from 'vitest';

import i18n from './index';
import { getGenderContext } from './gender';

describe('getGenderContext', () => {
  it('returns the gender when it is set', () => {
    expect(getGenderContext('female')).toBe('female');
    expect(getGenderContext('male')).toBe('male');
  });

  it('returns no context when the gender is not set', () => {
    expect(getGenderContext(null)).toBeUndefined();
    expect(getGenderContext(undefined)).toBeUndefined();
  });
});

describe('gendered translations', () => {
  it('picks the feminine, masculine or neutral form', () => {
    const translate = (context: string | undefined) => i18n.t('recipes.cooked', { context });

    expect(translate(getGenderContext('female'))).toBe('Я приготувала');
    expect(translate(getGenderContext('male'))).toBe('Я приготував');
    expect(translate(getGenderContext(null))).toBe('Страву приготовано');
  });
});
