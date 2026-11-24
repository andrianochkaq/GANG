export type Gender = 'female' | 'male';

// i18next context for gendered keys: "key_female", "key_male", and the
// plain "key" as the neutral form when the profile has no gender.
export function getGenderContext(gender: Gender | null | undefined): Gender | undefined {
  return gender === 'female' || gender === 'male' ? gender : undefined;
}
