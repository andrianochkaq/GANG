import { create } from 'zustand';

import type { Gender } from '../i18n/gender';

type UserState = {
  gender: Gender | null;
  setGender: (gender: Gender | null) => void;
};

// Filled from the profile once accounts land; null means "not set".
export const useUserStore = create<UserState>((set) => ({
  gender: null,
  setGender: (gender) => set({ gender }),
}));
