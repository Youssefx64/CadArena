import { useEffect, useState } from 'react';

/**
 * Hook to detect if user prefers reduced motion
 * Returns true if user has enabled "Reduce motion" in their OS settings
 */
export default function useReducedMotion() {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    // Check initial preference
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReduced(mediaQuery.matches);

    // Listen for changes
    const handleChange = (e) => {
      setPrefersReduced(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReduced;
}
