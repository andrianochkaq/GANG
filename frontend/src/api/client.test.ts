import { describe, expect, it } from 'vitest';

import { getApiBaseUrl } from './client';

describe('getApiBaseUrl', () => {
  it('uses VITE_API_URL without a trailing slash', () => {
    expect(getApiBaseUrl('http://localhost:8000/')).toBe('http://localhost:8000');
  });

  it('falls back to the same origin when unset', () => {
    expect(getApiBaseUrl(undefined)).toBe('');
    expect(getApiBaseUrl('  ')).toBe('');
  });
});
