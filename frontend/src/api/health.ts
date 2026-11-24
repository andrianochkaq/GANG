import { z } from 'zod';

import { apiClient } from './client';

const HEALTH_PATH = '/api/health/';

const serviceStatusSchema = z.enum(['ok', 'error']);

export const healthStatusSchema = z.object({
  db: serviceStatusSchema,
  redis: serviceStatusSchema,
});

export type ServiceStatus = z.infer<typeof serviceStatusSchema>;
export type HealthStatus = z.infer<typeof healthStatusSchema>;

// The endpoint answers 503 with the same body when a service is down,
// so both codes carry a status to show.
export async function fetchHealthStatus(): Promise<HealthStatus> {
  const response = await apiClient.get(HEALTH_PATH, {
    validateStatus: (code) => code === 200 || code === 503,
  });
  return healthStatusSchema.parse(response.data);
}
