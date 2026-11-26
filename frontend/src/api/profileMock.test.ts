import { beforeEach, describe, expect, it } from 'vitest';

import { createMockProfileApi, resetProfileMock, startMockOnboarding } from './profileMock';

const api = createMockProfileApi(0);

describe('mock profile API', () => {
  beforeEach(() => resetProfileMock());

  it('starts as an onboarded account with the white theme', async () => {
    await expect(api.getProfile()).resolves.toEqual({
      themeColor: 'white',
      isOnboardingDone: true,
    });
  });

  it('marks a new account as not onboarded', async () => {
    startMockOnboarding();
    await expect(api.getProfile()).resolves.toMatchObject({ isOnboardingDone: false });
  });

  it('keeps what was saved for the next read', async () => {
    startMockOnboarding();
    await api.updateProfile({ themeColor: 'ocean', isOnboardingDone: true });
    await expect(api.getProfile()).resolves.toEqual({
      themeColor: 'ocean',
      isOnboardingDone: true,
    });
  });

  it('merges a partial change into the saved profile', async () => {
    await api.updateProfile({ themeColor: 'lilac' });
    await expect(api.updateProfile({ isOnboardingDone: false })).resolves.toEqual({
      themeColor: 'lilac',
      isOnboardingDone: false,
    });
  });
});
