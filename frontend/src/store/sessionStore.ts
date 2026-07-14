const TOKEN_KEY = 'loadflow_token';

export const sessionStore = {
  getToken: () => localStorage.getItem(TOKEN_KEY) || '',
  setToken: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};
