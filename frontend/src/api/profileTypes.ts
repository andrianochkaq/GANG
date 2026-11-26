import type { ThemeId } from '../theme/themes';

// The part of /api/me/ that onboarding and the theme need.
export type Profile = {
  themeColor: ThemeId;
  isOnboardingDone: boolean;
};

export type ProfilePatch = Partial<Profile>;

// One contract for the real backend (FC-106) and the mock used with
// VITE_AUTH_MOCK=true. Screens only talk to this interface.
export interface ProfileApi {
  getProfile(): Promise<Profile>;
  updateProfile(patch: ProfilePatch): Promise<Profile>;
}
