import { describe, expect, it } from 'vitest';

import { fridgePath, toFridge } from './fridgesHttp';

describe('fridges API mapping', () => {
  it('turns the backend fridge into camelCase', () => {
    expect(
      toFridge({
        id: '11111111-1111-4111-8111-111111111111',
        name: 'Home',
        role: 'owner',
        member_count: 3,
        product_count: 12,
        is_current: true,
        created_at: '2026-11-27T10:00:00Z',
      }),
    ).toEqual({
      id: '11111111-1111-4111-8111-111111111111',
      name: 'Home',
      role: 'owner',
      memberCount: 3,
      productCount: 12,
      isCurrent: true,
    });
  });

  it('treats an unknown role as a member, so rename stays hidden', () => {
    const fridge = toFridge({
      id: 'x',
      name: 'Home',
      role: 'admin',
      member_count: 1,
      product_count: 0,
      is_current: false,
    });
    expect(fridge.role).toBe('member');
  });

  it('builds the detail path', () => {
    expect(fridgePath('abc')).toBe('/api/fridges/abc/');
  });
});
