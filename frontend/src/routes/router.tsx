import { createBrowserRouter } from 'react-router-dom';
import type { RouteObject } from 'react-router-dom';

import EmailVerifyPage from '../features/auth/EmailVerifyPage';
import ForgotPasswordPage from '../features/auth/ForgotPasswordPage';
import LoginPage from '../features/auth/LoginPage';
import PhoneLoginPage from '../features/auth/PhoneLoginPage';
import ResetPasswordPage from '../features/auth/ResetPasswordPage';
import TelegramLoginPage from '../features/auth/TelegramLoginPage';
import HealthStatusPage from '../features/health/HealthStatusPage';
import ProfileGate from '../features/onboarding/ProfileGate';
import ThemePicker from '../features/onboarding/ThemePicker';
import { ONBOARDING_COLOR_PATH } from '../features/onboarding/onboardingPaths';
import ProtectedRoute from './ProtectedRoute';

export const routes: RouteObject[] = [
  { path: '/login', element: <LoginPage /> },
  { path: '/login/phone', element: <PhoneLoginPage /> },
  { path: '/login/telegram', element: <TelegramLoginPage /> },
  { path: '/register/verify', element: <EmailVerifyPage /> },
  { path: '/forgot-password', element: <ForgotPasswordPage /> },
  { path: '/reset-password', element: <ResetPasswordPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        // Loads the profile and sends new accounts to the colour screen once.
        element: <ProfileGate />,
        children: [
          // Placeholder home until the app shell (FC-203) lands.
          { path: '/', element: <HealthStatusPage /> },
          { path: ONBOARDING_COLOR_PATH, element: <ThemePicker /> },
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
