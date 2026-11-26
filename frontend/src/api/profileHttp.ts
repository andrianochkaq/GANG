import { z } from 'zod';

import { DEFAULT_THEME_ID, isThemeId, type ThemeId } from '../theme/themes';
import { toAuthApiError } from './authErrors';
import { apiClient } from './client';
import type { Profile, ProfileApi, ProfilePatch } from './profileTypes';

export const PROFILE_PATH = '/api/me/';

// An unknown colour (for example one added by a newer backend) falls back to
// the default theme instead of breaking the whole app.
const profileSchema = z.object({
  theme_color: z
    .string()
    .transform((value): ThemeId => (isThemeId(value) ? value : DEFAULT_THEME_ID)),
  is_onboarding_done: z.boolean(),
});

export function toProfile(data: unknown): Profile {
  const parsed = profileSchema.parse(data);
  return { themeColor: parsed.theme_color, isOnboardingDone: parsed.is_onboarding_done };
}

// PATCH only sends the fields that changed, in the API's snake_case.
export function toProfileRequestBody(patch: ProfilePatch): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  if (patch.themeColor !== undefined) {
    body.theme_color = patch.themeColor;
  }
  if (patch.isOnboardingDone !== undefined) {
    body.is_onboarding_done = patch.isOnboardingDone;
  }
  return body;
}

export const httpProfileApi: ProfileApi = {
  async getProfile() {
    try {
      const response = await apiClient.get(PROFILE_PATH);
      return toProfile(response.data);
    } catch (error) {
      throw toAuthApiError(error);
    }
  },
  async updateProfile(patch) {
    try {
      const response = await apiClient.patch(PROFILE_PATH, toProfileRequestBody(patch));
      return toProfile(response.data);
    } catch (error) {
      throw toAuthApiError(error);
    }
  },
};
