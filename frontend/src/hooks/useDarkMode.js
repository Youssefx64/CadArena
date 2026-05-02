import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'cadarena-theme';

export function useDarkMode() {
  const [isDark, setIsDark] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) return stored === 'dark';
    } catch {}
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isDark) {
      root.setAttribute('data-theme', 'dark');
      root.classList.add('dark');
    } else {
      root.removeAttribute('data-theme');
      root.classList.remove('dark');
    }
    try { localStorage.setItem(STORAGE_KEY, isDark ? 'dark' : 'light'); } catch {}
  }, [isDark]);

  const toggle = useCallback(() => setIsDark((v) => !v), []);
  return { isDark, toggle };
}
