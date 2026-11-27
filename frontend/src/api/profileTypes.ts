import type { ThemeId } from '../theme/themes';

// The part of /api/me/ that onboarding, the theme and the app shell need.
export type Profile = {
  themeColor: ThemeId;
  isOnboardingDone: boolean;
  // USER_PROFILE.calories_enabled (architecture.md). /api/me/ does not send
  // it yet; absent means the Calories tab is shown.
  caloriesEnabled?: boolean;
};

export type ProfilePatch = Partial<Profile>;

// One contract for the real backend (FC-106) and the mock used with
// VITE_AUTH_MOCK=true. Screens only talk to this interface.
export interface ProfileApi {
  getProfile(): Promise<Profile>;
  updateProfile(patch: ProfilePatch): Promise<Profile>;
}
