import { useEffect, useState } from "react";

/**
 * Opóźnia wartość o podany czas. Paleta poleceń wysyła zapytanie do API tylko
 * po ustabilizowaniu wpisywanego tekstu, a nie po każdym znaku.
 */
export function useDebouncedValue<T>(value: T, delay = 250): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
