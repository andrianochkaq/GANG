export type SessionTokens = {
  access: string;
};

export type PhoneLoginResult = SessionTokens & {
  isNewUser: boolean;
};

export type TelegramLoginRequest = {
  token: string;
  deepLink: string;
  expiresAt: string;
  pollIntervalMs: number;
};

export type TelegramLoginStatus =
  | { status: 'pending' }
  | { status: 'expired' }
  | { status: 'confirmed'; access: string; isNewUser: boolean };

// One contract for both the real backend (FC-103 … FC-107) and the mock
// (VITE_AUTH_MOCK=true). Screens only talk to this interface.
export interface AuthApi {
  registerEmail(email: string, password: string): Promise<void>;
  verifyEmail(email: string, code: string): Promise<SessionTokens>;
  resendEmailCode(email: string): Promise<void>;
  loginEmail(email: string, password: string): Promise<SessionTokens>;
  requestPhoneCode(phone: string): Promise<void>;
  verifyPhone(phone: string, code: string): Promise<PhoneLoginResult>;
  startTelegramLogin(): Promise<TelegramLoginRequest>;
  getTelegramLoginStatus(token: string): Promise<TelegramLoginStatus>;
  requestPasswordReset(email: string): Promise<void>;
  resetPassword(uid: string, token: string, password: string): Promise<void>;
  refreshSession(): Promise<SessionTokens>;
  logout(): Promise<void>;
}
