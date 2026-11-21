/** Tytuł karty przeglądarki zależny od bieżącego ekranu. */

import { useEffect } from "react";

export const APP_NAME = "Inteligentny asystent urzędnika";

export function documentTitleFor(label?: string | null): string {
  const trimmed = label?.trim();
  return trimmed ? `${trimmed} · ${APP_NAME}` : APP_NAME;
}

export function useDocumentTitle(label?: string | null): void {
  useEffect(() => {
    document.title = documentTitleFor(label);
  }, [label]);
}
