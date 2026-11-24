import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import './index';
import { useUserStore } from '../store/userStore';
import { useGenderedTranslation } from './useGenderedTranslation';

describe('useGenderedTranslation', () => {
  afterEach(() => {
    act(() => useUserStore.getState().setGender(null));
  });

  it('follows the gender of the current user', () => {
    const { result } = renderHook(() => useGenderedTranslation());
    expect(result.current('recipes.cooked')).toBe('Страву приготовано');

    act(() => useUserStore.getState().setGender('female'));
    expect(result.current('recipes.cooked')).toBe('Я приготувала');

    act(() => useUserStore.getState().setGender('male'));
    expect(result.current('recipes.cooked')).toBe('Я приготував');
  });
});
