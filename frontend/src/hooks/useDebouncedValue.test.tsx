import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useDebouncedValue } from './useDebouncedValue';

describe('useDebouncedValue', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('keeps the old value until the delay passes without changes', () => {
    const { result, rerender } = renderHook(({ text }) => useDebouncedValue(text, 200), {
      initialProps: { text: 'м' },
    });
    rerender({ text: 'мо' });
    act(() => {
      vi.advanceTimersByTime(150);
    });
    rerender({ text: 'мол' });
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(result.current).toBe('м');
    act(() => {
      vi.advanceTimersByTime(60);
    });
    expect(result.current).toBe('мол');
  });
});
