import { apiClient } from '../api/client';

export const loadflowService = {
  login: (email: string, password: string) => apiClient.post('/auth/login', { email, password }),
  loads: (q?: string) => apiClient.get('/loads', { params: { q: q || undefined } }),
  audit: () => apiClient.get('/audit'),
};
