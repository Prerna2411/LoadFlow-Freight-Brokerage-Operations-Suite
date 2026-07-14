import axios from 'axios';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export const API_ROOT = API_URL.replace(/\/api\/v1\/?$/, '');

export const apiClient = axios.create({ baseURL: API_URL });

export function setAuthToken(token: string) {
  apiClient.defaults.headers.common.Authorization = token ? `Bearer ${token}` : '';
}
