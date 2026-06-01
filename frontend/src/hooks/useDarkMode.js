import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'cadarena-theme';
const STUDIO_STORAGE_KEY = 'cadarena_theme';

export function useDarkMode() {
  const [isDark, setIsDark] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(STUDIO_STORAGE_KEY);
      if (stored) return stored === 'dark';
    } catch {}
    return false;
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
    try {
      const theme = isDark ? 'dark' : 'light';
      localStorage.setItem(STORAGE_KEY, theme);
      localStorage.setItem(STUDIO_STORAGE_KEY, theme);
    } catch {}
  }, [isDark]);

  const toggle = useCallback(() => setIsDark((v) => !v), []);
  return { isDark, toggle };
}
