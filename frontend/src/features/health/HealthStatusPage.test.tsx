import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import '../../i18n';
import { fetchHealthStatus } from '../../api/health';
import HealthStatusPage from './HealthStatusPage';

vi.mock('../../api/health', () => ({
  fetchHealthStatus: vi.fn(),
}));

const fetchHealthStatusMock = vi.mocked(fetchHealthStatus);

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <HealthStatusPage />
    </QueryClientProvider>,
  );
}

describe('HealthStatusPage', () => {
  afterEach(() => {
    cleanup();
    fetchHealthStatusMock.mockReset();
  });

  it('shows the status of each service in words', async () => {
    fetchHealthStatusMock.mockResolvedValue({ db: 'ok', redis: 'error' });
    renderPage();

    expect(await screen.findByText('Стан сервера')).toBeTruthy();
    expect(screen.getByText('працює')).toBeTruthy();
    expect(screen.getByText('не відповідає')).toBeTruthy();
  });

  it('explains when the server cannot be reached', async () => {
    fetchHealthStatusMock.mockRejectedValue(new Error('Network Error'));
    renderPage();

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Не вдалося зв’язатися з сервером');
  });
});
