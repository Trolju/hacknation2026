/**
 * Motyw jasny/ciemny.
 *
 * Logika jest niezależna od Reacta i od DOM-u (przyjmuje obiekty o minimalnym
 * kształcie), żeby dała się przetestować bez środowiska przeglądarki.
 * Przełączenie motywu to klasa `dark` na `<html>` — zmienne CSS z `index.css`
 * są już przygotowane w obu wariantach.
 */

import { createContext, useContext } from "react";

export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "asystent.motyw";

/** Minimalny kształt `localStorage` — w testach wystarczy zwykły obiekt. */
export type ThemeStorage = {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
};

/** Minimalny kształt `document.documentElement`. */
export type ThemeRoot = {
  classList: { add(token: string): void; remove(token: string): void };
  dataset?: { [key: string]: string | undefined };
  style?: { colorScheme: string };
};

export function isTheme(value: unknown): value is Theme {
  return value === "light" || value === "dark";
}

export function readStoredTheme(
  storage: ThemeStorage | null | undefined,
): Theme | null {
  if (!storage) return null;
  try {
    const value = storage.getItem(THEME_STORAGE_KEY);
    return isTheme(value) ? value : null;
  } catch {
    return null;
  }
}

export function storeTheme(
  storage: ThemeStorage | null | undefined,
  theme: Theme,
): void {
  if (!storage) return;
  try {
    storage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    /* tryb prywatny przeglądarki — motyw działa do końca sesji */
  }
}

/** Zapisany wybór wygrywa; bez wyboru decyduje ustawienie systemowe. */
export function resolveTheme(stored: Theme | null, prefersDark: boolean): Theme {
  if (stored) return stored;
  return prefersDark ? "dark" : "light";
}

export function toggleTheme(theme: Theme): Theme {
  return theme === "dark" ? "light" : "dark";
}

export function applyThemeToRoot(
  theme: Theme,
  root: ThemeRoot | null | undefined,
): void {
  if (!root) return;
  if (theme === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
  if (root.dataset) root.dataset.theme = theme;
  // `color-scheme` sprawia, że natywne kontrolki (pola daty, paski przewijania)
  // też przechodzą na ciemny wariant.
  if (root.style) root.style.colorScheme = theme;
}

export function themeLabel(theme: Theme): string {
  return theme === "dark" ? "Motyw ciemny" : "Motyw jasny";
}

/** Etykieta akcji, nie stanu — czytnik ekranu odczyta, co się stanie po kliknięciu. */
export function themeToggleLabel(theme: Theme): string {
  return theme === "dark" ? "Włącz motyw jasny" : "Włącz motyw ciemny";
}

export type ThemeContextValue = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggle: () => void;
};

export const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme(): ThemeContextValue {
  const value = useContext(ThemeContext);
  if (!value) {
    throw new Error("useTheme musi być użyty wewnątrz ThemeProvider.");
  }
  return value;
}
