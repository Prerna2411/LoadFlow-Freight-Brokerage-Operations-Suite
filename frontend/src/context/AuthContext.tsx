import { createContext } from 'react';

import type { User } from '../types/domain';

export const AuthContext = createContext<{
  user: User | null;
  token: string;
}>({ user: null, token: '' });
