import { useEffect, useState } from "react";

/**
 * Zwraca wartość po `delay` milisekundach bez zmian.
 *
 * Chroni backend przed zapytaniem na każdy klawisz: sugestie komórek liczą się
 * dopiero, gdy urzędnik przestanie pisać.
 */
export function useDebouncedValue<T>(value: T, delay = 350): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
