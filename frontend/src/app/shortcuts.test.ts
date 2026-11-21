import { describe, expect, it } from "vitest";

import {
  NAV_LETTERS,
  SEQUENCE_TIMEOUT_MS,
  isEditableTarget,
  isHelpShortcut,
  isPaletteShortcut,
  isSequenceExpired,
  isSequenceStart,
  matchNavShortcut,
  modifierKeyLabel,
  navShortcuts,
  shortcutHint,
  type NavShortcut,
} from "@/app/shortcuts";

const FEATURES = [
  { id: "dashboard", label: "Pulpit", path: "" },
  { id: "calendar", label: "Kalendarz terminów", path: "kalendarz" },
  { id: "drafting", label: "Generator odpowiedzi", path: "odpowiedzi" },
  { id: "nieznany", label: "Moduł bez skrótu", path: "modul" },
];

describe("navShortcuts", () => {
  it("buduje skróty tylko dla modułów z przypisaną literą", () => {
    const shortcuts = navShortcuts(FEATURES);
    expect(shortcuts.map((item) => item.featureId)).toEqual([
      "dashboard",
      "calendar",
      "drafting",
    ]);
  });

  it("zamienia ścieżkę modułu na adres z ukośnikiem", () => {
    const shortcuts = navShortcuts(FEATURES);
    expect(shortcuts[0].path).toBe("/");
    expect(shortcuts[1].path).toBe("/kalendarz");
    expect(shortcuts[2].path).toBe("/odpowiedzi");
  });

  it("nie powtarza liter w obrębie rejestru", () => {
    const letters = Object.values(NAV_LETTERS);
    expect(new Set(letters).size).toBe(letters.length);
  });
});

describe("matchNavShortcut", () => {
  const shortcuts: NavShortcut[] = navShortcuts(FEATURES);

  it("dopasowuje literę niezależnie od wielkości", () => {
    expect(matchNavShortcut("K", shortcuts)?.featureId).toBe("calendar");
    expect(matchNavShortcut("k", shortcuts)?.featureId).toBe("calendar");
  });

  it("zwraca null dla nieprzypisanej litery", () => {
    expect(matchNavShortcut("z", shortcuts)).toBeNull();
  });
});

describe("isPaletteShortcut", () => {
  it("rozpoznaje Ctrl+K i Cmd+K", () => {
    expect(isPaletteShortcut({ key: "k", ctrlKey: true })).toBe(true);
    expect(isPaletteShortcut({ key: "K", metaKey: true })).toBe(true);
  });

  it("nie reaguje bez modyfikatora albo z Alt", () => {
    expect(isPaletteShortcut({ key: "k" })).toBe(false);
    expect(isPaletteShortcut({ key: "k", ctrlKey: true, altKey: true })).toBe(
      false,
    );
  });

  it("nie reaguje na inne litery z modyfikatorem", () => {
    expect(isPaletteShortcut({ key: "j", ctrlKey: true })).toBe(false);
  });
});

describe("isHelpShortcut", () => {
  it("rozpoznaje znak zapytania i Shift+ukośnik", () => {
    expect(isHelpShortcut({ key: "?" })).toBe(true);
    expect(isHelpShortcut({ key: "/", shiftKey: true })).toBe(true);
  });

  it("nie reaguje na sam ukośnik ani na skrót z modyfikatorem", () => {
    expect(isHelpShortcut({ key: "/" })).toBe(false);
    expect(isHelpShortcut({ key: "?", ctrlKey: true })).toBe(false);
  });
});

describe("isSequenceStart", () => {
  it("rozpoznaje samo g", () => {
    expect(isSequenceStart({ key: "g" })).toBe(true);
    expect(isSequenceStart({ key: "G" })).toBe(true);
  });

  it("nie reaguje na g z modyfikatorem", () => {
    expect(isSequenceStart({ key: "g", ctrlKey: true })).toBe(false);
    expect(isSequenceStart({ key: "g", shiftKey: true })).toBe(false);
  });
});

describe("isSequenceExpired", () => {
  it("pozwala dokończyć sekwencję w oknie czasowym", () => {
    expect(isSequenceExpired(1000, 1000 + SEQUENCE_TIMEOUT_MS)).toBe(false);
  });

  it("przepada po przekroczeniu okna", () => {
    expect(isSequenceExpired(1000, 1000 + SEQUENCE_TIMEOUT_MS + 1)).toBe(true);
  });
});

describe("isEditableTarget", () => {
  it("rozpoznaje pola formularza", () => {
    expect(isEditableTarget({ tagName: "INPUT" })).toBe(true);
    expect(isEditableTarget({ tagName: "textarea" })).toBe(true);
    expect(isEditableTarget({ tagName: "SELECT" })).toBe(true);
  });

  it("rozpoznaje edytor z contenteditable", () => {
    expect(isEditableTarget({ tagName: "DIV", isContentEditable: true })).toBe(
      true,
    );
  });

  it("rozpoznaje pola o roli tekstowej", () => {
    const target = {
      tagName: "BUTTON",
      getAttribute: (name: string) => (name === "role" ? "combobox" : null),
    };
    expect(isEditableTarget(target)).toBe(true);
  });

  it("nie traktuje przycisku ani braku celu jako pola tekstowego", () => {
    expect(isEditableTarget({ tagName: "BUTTON" })).toBe(false);
    expect(isEditableTarget(null)).toBe(false);
    expect(isEditableTarget(undefined)).toBe(false);
  });
});

describe("shortcutHint", () => {
  it("składa podpowiedź sekwencji", () => {
    expect(shortcutHint("k")).toBe("g k");
  });
});

describe("modifierKeyLabel", () => {
  it("na macOS pokazuje Cmd", () => {
    expect(
      modifierKeyLabel(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
      ),
    ).toBe("Cmd");
  });

  it("na pozostałych systemach pokazuje Ctrl", () => {
    expect(
      modifierKeyLabel("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"),
    ).toBe("Ctrl");
    expect(
      modifierKeyLabel("Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
    ).toBe("Ctrl");
  });

  it("bez informacji o systemie wybiera Ctrl", () => {
    expect(modifierKeyLabel("")).toBe("Ctrl");
  });
});
