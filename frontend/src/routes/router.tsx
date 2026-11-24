import { createBrowserRouter } from 'react-router-dom';

import HealthStatusPage from '../features/health/HealthStatusPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HealthStatusPage />,
  },
]);
