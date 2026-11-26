import { startMockOnboarding } from '../../api/profileMock';
import { createMockAuthApi } from '../../api/authMock';

export const EXISTING_EMAIL = 'marta@example.com';
export const EXISTING_PASSWORD = 'freecook26';

// A logged-in browser (the mock keeps the refresh "cookie"); with
// isNewAccount the account has not picked its app colour yet.
export async function startSession(isNewAccount: boolean) {
  if (isNewAccount) {
    startMockOnboarding();
  }
  await createMockAuthApi(0).loginEmail(EXISTING_EMAIL, EXISTING_PASSWORD);
}
