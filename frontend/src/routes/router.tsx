import { createBrowserRouter } from 'react-router-dom';
import type { RouteObject } from 'react-router-dom';

import EmailVerifyPage from '../features/auth/EmailVerifyPage';
import ForgotPasswordPage from '../features/auth/ForgotPasswordPage';
import LoginPage from '../features/auth/LoginPage';
import PhoneLoginPage from '../features/auth/PhoneLoginPage';
import ResetPasswordPage from '../features/auth/ResetPasswordPage';
import TelegramLoginPage from '../features/auth/TelegramLoginPage';
import HealthStatusPage from '../features/health/HealthStatusPage';
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
    // Placeholder home until the app shell (FC-203) lands.
    children: [{ path: '/', element: <HealthStatusPage /> }],
  },
];

export const router = createBrowserRouter(routes);
