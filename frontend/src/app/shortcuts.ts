/**
 * Skróty klawiszowe — czysta logika bez nasłuchiwania zdarzeń.
 *
 * Dzięki temu, że funkcje przyjmują obiekt o kształcie `KeyboardEvent`,
 * da się je przetestować bez DOM-u. Nasłuch instaluje `useGlobalShortcuts`.
 */

export type NavShortcut = {
  /** Litera po prefiksie `g`. */
  key: string;
  featureId: string;
  label: string;
  path: string;
};

/**
 * Przypisanie liter do modułów. Klucz to `id` z manifestu ekranu, więc lista
 * skrótów w oknie pomocy zawsze odpowiada temu, co faktycznie jest w menu.
 */
export const NAV_LETTERS: Record<string, string> = {
  dashboard: "d",
  calendar: "k",
  ingest: "f",
  archive: "a",
  routing: "w",
  drafting: "o",
  anonymize: "n",
  settings: "u",
};

export type ShortcutFeature = { id: string; label: string; path: string };

export function navShortcuts(features: ShortcutFeature[]): NavShortcut[] {
  return features
    .filter((feature) => NAV_LETTERS[feature.id] !== undefined)
    .map((feature) => ({
      key: NAV_LETTERS[feature.id],
      featureId: feature.id,
      label: feature.label,
      path: `/${feature.path}`,
    }));
}

export type KeyEventLike = {
  key: string;
  metaKey?: boolean;
  ctrlKey?: boolean;
  altKey?: boolean;
  shiftKey?: boolean;
  target?: unknown;
};

const EDITABLE_TAGS = new Set(["INPUT", "TEXTAREA", "SELECT"]);
const EDITABLE_ROLES = new Set(["textbox", "combobox", "searchbox", "spinbutton"]);

/**
 * Czy zdarzenie pochodzi z pola, w którym użytkownik pisze?
 *
 * Sprawdzamy też `role`, bo pola wyboru z Radix to `<button role="combobox">`,
 * a edytor TipTap to element z `contenteditable`.
 */
export function isEditableTarget(target: unknown): boolean {
  if (!target || typeof target !== "object") return false;
  const element = target as {
    tagName?: unknown;
    isContentEditable?: unknown;
    getAttribute?: (name: string) => string | null;
  };
  if (typeof element.tagName === "string") {
    if (EDITABLE_TAGS.has(element.tagName.toUpperCase())) return true;
  }
  if (element.isContentEditable === true) return true;
  if (typeof element.getAttribute === "function") {
    const role = element.getAttribute("role");
    if (role && EDITABLE_ROLES.has(role)) return true;
  }
  return false;
}

/** `Cmd+K` na macOS, `Ctrl+K` na pozostałych systemach. */
export function isPaletteShortcut(event: KeyEventLike): boolean {
  const modifier = event.metaKey === true || event.ctrlKey === true;
  return modifier && event.altKey !== true && event.key.toLowerCase() === "k";
}

/** `?` — na większości klawiatur to `Shift+/`. */
export function isHelpShortcut(event: KeyEventLike): boolean {
  if (event.metaKey || event.ctrlKey || event.altKey) return false;
  return event.key === "?" || (event.key === "/" && event.shiftKey === true);
}

/** Pierwszy klawisz sekwencji nawigacyjnej: samo `g`. */
export function isSequenceStart(event: KeyEventLike): boolean {
  if (event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) {
    return false;
  }
  return event.key.toLowerCase() === "g";
}

export function matchNavShortcut(
  letter: string,
  shortcuts: NavShortcut[],
): NavShortcut | null {
  const key = letter.toLowerCase();
  return shortcuts.find((shortcut) => shortcut.key === key) ?? null;
}

/** Ile czasu użytkownik ma na dokończenie sekwencji `g` + litera. */
export const SEQUENCE_TIMEOUT_MS = 1500;

export function isSequenceExpired(startedAt: number, now: number): boolean {
  return now - startedAt > SEQUENCE_TIMEOUT_MS;
}

export function shortcutHint(key: string): string {
  return `g ${key}`;
}

/**
 * Etykieta klawisza modyfikującego — na macOS `Cmd`, gdzie indziej `Ctrl`.
 * Podpowiedź w interfejsie musi zgadzać się z tym, co użytkownik ma na klawiaturze.
 */
export function modifierKeyLabel(userAgent?: string): string {
  const agent =
    userAgent ?? (typeof navigator === "undefined" ? "" : navigator.userAgent);
  return /Mac|iPhone|iPad|iPod/i.test(agent) ? "Cmd" : "Ctrl";
}
