import { DEFAULT_THEME_ID, isThemeId } from '../theme/themes';
import type { Profile, ProfileApi } from './profileTypes';

// In-memory stand-in for /api/me/ (FC-106), switched on with VITE_AUTH_MOCK=true.
// It is kept in localStorage too, so a reload (or a second login) in the same
// browser shows the saved colour the way a second device would with the backend.
const RESPONSE_DELAY_MS = 400;
const STORAGE_KEY = 'fc-mock-profile';

function createDefaultProfile(): Profile {
  // Existing accounts are already onboarded; new ones are marked by
  // startMockOnboarding() when the registration code is confirmed.
  return { themeColor: DEFAULT_THEME_ID, isOnboardingDone: true };
}

// Mirrors the storage value for browsers (and test runners) without storage.
let memoryProfile: Profile = createDefaultProfile();

function wait(delayMs: number): Promise<void> {
  return delayMs > 0 ? new Promise((resolve) => setTimeout(resolve, delayMs)) : Promise.resolve();
}

function parseStoredProfile(text: string | null): Profile | null {
  if (!text) {
    return null;
  }
  try {
    const data = JSON.parse(text) as Partial<Profile>;
    if (typeof data.themeColor === 'string' && isThemeId(data.themeColor)) {
      return { themeColor: data.themeColor, isOnboardingDone: data.isOnboardingDone === true };
    }
  } catch {
    // A broken value is treated as no value.
  }
  return null;
}

function readProfile(): Profile {
  try {
    return parseStoredProfile(window.localStorage.getItem(STORAGE_KEY)) ?? { ...memoryProfile };
  } catch {
    return { ...memoryProfile };
  }
}

function writeProfile(profile: Profile): void {
  memoryProfile = { ...profile };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
  } catch {
    // Storage can be blocked; the profile then lasts until reload.
  }
}

export function startMockOnboarding(): void {
  writeProfile({ themeColor: DEFAULT_THEME_ID, isOnboardingDone: false });
}

export function resetProfileMock(): void {
  memoryProfile = createDefaultProfile();
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to clear.
  }
}

export function createMockProfileApi(delayMs = RESPONSE_DELAY_MS): ProfileApi {
  return {
    async getProfile() {
      await wait(delayMs);
      return readProfile();
    },
    async updateProfile(patch) {
      await wait(delayMs);
      const updated: Profile = { ...readProfile(), ...patch };
      writeProfile(updated);
      return updated;
    },
  };
}
