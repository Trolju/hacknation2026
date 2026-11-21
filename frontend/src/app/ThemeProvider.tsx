import {
  type ReactNode,
  useCallback,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";

import {
  ThemeContext,
  applyThemeToRoot,
  readStoredTheme,
  resolveTheme,
  storeTheme,
  toggleTheme,
  type Theme,
  type ThemeStorage,
} from "@/app/theme";

function browserStorage(): ThemeStorage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function systemPrefersDark(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

/**
 * Motyw trzymany w `localStorage` i odzwierciedlony klasą `dark` na `<html>`.
 *
 * Zapisany wybór wygrywa z ustawieniem systemowym. `useLayoutEffect` nakłada
 * klasę przed pierwszym malowaniem, więc ekran nie mruga jasnym motywem.
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() =>
    resolveTheme(readStoredTheme(browserStorage()), systemPrefersDark()),
  );

  useLayoutEffect(() => {
    applyThemeToRoot(theme, document.documentElement);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
    storeTheme(browserStorage(), next);
  }, []);

  const toggle = useCallback(() => {
    setThemeState((current) => {
      const next = toggleTheme(current);
      storeTheme(browserStorage(), next);
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ theme, setTheme, toggle }),
    [theme, setTheme, toggle],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}
