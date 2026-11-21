/**
 * Ścieżka nawigacji (breadcrumbs) wyliczana z adresu i rejestru ekranów.
 *
 * Rejestr jest odkrywany automatycznie, więc nowy ekran dostaje okruszek
 * bez żadnej dodatkowej konfiguracji.
 */

export type Crumb = { label: string; to?: string };

export type CrumbFeature = { path: string; label: string };

export const HOME_CRUMB: Crumb = { label: "Start", to: "/" };

export const NOT_FOUND_CRUMB: Crumb = { label: "Nie znaleziono ekranu" };

/** Ujednolica adres: bez końcowego ukośnika, bez pustego stringa. */
export function normalizePath(pathname: string): string {
  if (!pathname) return "/";
  const trimmed = pathname.replace(/\/+$/, "");
  return trimmed === "" ? "/" : trimmed;
}

export function buildBreadcrumbs(
  pathname: string,
  features: CrumbFeature[],
): Crumb[] {
  const path = normalizePath(pathname);
  const feature = features.find(
    (item) => normalizePath(`/${item.path}`) === path,
  );
  if (!feature) return [HOME_CRUMB, NOT_FOUND_CRUMB];
  if (path === "/") return [{ label: feature.label }];
  return [HOME_CRUMB, { label: feature.label }];
}
