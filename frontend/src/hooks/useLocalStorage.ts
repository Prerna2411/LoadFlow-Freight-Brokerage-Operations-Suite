import { useEffect, useState } from 'react';

export function useLocalStorage(key: string, initialValue = '') {
  const [value, setValue] = useState(() => localStorage.getItem(key) || initialValue);

  useEffect(() => {
    if (value) localStorage.setItem(key, value);
    else localStorage.removeItem(key);
  }, [key, value]);

  return [value, setValue] as const;
}
