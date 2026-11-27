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
import GuestRoute from './GuestRoute';
import AppShell from '../components/layout/AppShell';
import PlaceholderPage from '../features/placeholder/PlaceholderPage';
import { APP_PATHS } from './paths';
import ProtectedRoute from './ProtectedRoute';

export const routes: RouteObject[] = [
  {
    // Logged-in users skip these screens (GuestRoute.tsx).
    element: <GuestRoute />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/login/phone', element: <PhoneLoginPage /> },
      { path: '/login/telegram', element: <TelegramLoginPage /> },
      { path: '/register/verify', element: <EmailVerifyPage /> },
      { path: '/forgot-password', element: <ForgotPasswordPage /> },
    ],
  },
  // Outside GuestRoute: the emailed link must work in any tab, logged in or not.
  { path: '/reset-password', element: <ResetPasswordPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        // Loads the profile and sends new accounts to the colour screen once.
        element: <ProfileGate />,
        children: [
          // Onboarding frame: no navigation.
          { path: ONBOARDING_COLOR_PATH, element: <ThemePicker /> },
          {
            element: <AppShell />,
            children: [
              { path: APP_PATHS.home, element: <PlaceholderPage titleKey="shell.nav.fridge" /> },
              { path: APP_PATHS.chef, element: <PlaceholderPage titleKey="shell.nav.chef" /> },
              {
                path: APP_PATHS.calories,
                element: <PlaceholderPage titleKey="shell.nav.calories" />,
              },
              {
                path: APP_PATHS.profile,
                element: <PlaceholderPage titleKey="shell.nav.profile" />,
              },
              {
                path: APP_PATHS.shopping,
                element: <PlaceholderPage titleKey="shell.nav.shopping" />,
              },
              {
                path: APP_PATHS.fridges,
                element: <PlaceholderPage titleKey="shell.placeholder.fridges" />,
              },
              {
                path: APP_PATHS.recipes,
                element: <PlaceholderPage titleKey="shell.placeholder.recipes" />,
              },
              // The backend check from FC-003, kept for local setup; not in the nav.
              { path: APP_PATHS.health, element: <HealthStatusPage /> },
            ],
          },
        ],
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
