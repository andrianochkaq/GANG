import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { MemoryRouter, useLocation, useRoutes } from 'react-router-dom';
import type { Location } from 'react-router-dom';

import { routes } from '../../routes/router';

type LocationRef = { current: Location | null };

function AppRoutes({ locationRef }: { locationRef: LocationRef }) {
  locationRef.current = useLocation();
  return useRoutes(routes);
}

// Renders the app's real routes at a given URL. A MemoryRouter instead of a
// data router: jsdom's AbortSignal does not fit Node's fetch Request.
// Tests mock ../../api/auth with the in-memory auth API.
export function renderAppAt(entry: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const locationRef: LocationRef = { current: null };
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entry]}>
        <AppRoutes locationRef={locationRef} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  return { getPathname: () => locationRef.current?.pathname };
}
