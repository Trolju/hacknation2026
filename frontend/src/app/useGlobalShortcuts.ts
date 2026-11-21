import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import {
  isEditableTarget,
  isHelpShortcut,
  isPaletteShortcut,
  isSequenceExpired,
  isSequenceStart,
  matchNavShortcut,
  type NavShortcut,
} from "@/app/shortcuts";

type GlobalShortcutsOptions = {
  shortcuts: NavShortcut[];
  onOpenPalette: () => void;
  onOpenHelp: () => void;
};

/** Czy na wierzchu jest modal? Wtedy sekwencje nawigacyjne nie powinny działać. */
function hasOpenDialog(): boolean {
  return (
    document.querySelector(
      '[role="dialog"][data-state="open"], [role="alertdialog"][data-state="open"]',
    ) !== null
  );
}

/**
 * Globalne skróty: `Cmd/Ctrl+K` (paleta), `?` (pomoc) oraz sekwencje `g` + litera.
 *
 * W polach tekstowych skróty nawigacyjne są wyłączone — inaczej nie dałoby się
 * wpisać litery „g” w wyszukiwarce.
 */
export function useGlobalShortcuts({
  shortcuts,
  onOpenPalette,
  onOpenHelp,
}: GlobalShortcutsOptions): void {
  const navigate = useNavigate();

  useEffect(() => {
    let sequenceStartedAt: number | null = null;

    const handler = (event: KeyboardEvent) => {
      if (event.defaultPrevented) return;

      if (isPaletteShortcut(event)) {
        event.preventDefault();
        onOpenPalette();
        return;
      }

      if (isEditableTarget(event.target)) return;

      if (isHelpShortcut(event)) {
        event.preventDefault();
        onOpenHelp();
        return;
      }

      if (hasOpenDialog()) return;

      if (isSequenceStart(event)) {
        sequenceStartedAt = Date.now();
        return;
      }

      if (sequenceStartedAt === null) return;
      const startedAt = sequenceStartedAt;
      sequenceStartedAt = null;
      if (isSequenceExpired(startedAt, Date.now())) return;

      const shortcut = matchNavShortcut(event.key, shortcuts);
      if (!shortcut) return;
      event.preventDefault();
      navigate(shortcut.path);
    };

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate, onOpenHelp, onOpenPalette, shortcuts]);
}
