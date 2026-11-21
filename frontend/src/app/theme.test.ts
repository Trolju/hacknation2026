import { describe, expect, it } from "vitest";

import {
  THEME_STORAGE_KEY,
  applyThemeToRoot,
  isTheme,
  readStoredTheme,
  resolveTheme,
  storeTheme,
  themeLabel,
  themeToggleLabel,
  toggleTheme,
  type ThemeRoot,
  type ThemeStorage,
} from "@/app/theme";

function memoryStorage(initial: Record<string, string> = {}): ThemeStorage {
  const data = new Map(Object.entries(initial));
  return {
    getItem: (key) => data.get(key) ?? null,
    setItem: (key, value) => {
      data.set(key, value);
    },
  };
}

function fakeRoot(): ThemeRoot & { classes: Set<string> } {
  const classes = new Set<string>();
  return {
    classes,
    classList: {
      add: (token) => classes.add(token),
      remove: (token) => classes.delete(token),
    },
    dataset: {},
    style: { colorScheme: "" },
  };
}

describe("isTheme", () => {
  it("przyjmuje tylko znane warianty", () => {
    expect(isTheme("light")).toBe(true);
    expect(isTheme("dark")).toBe(true);
    expect(isTheme("system")).toBe(false);
    expect(isTheme(null)).toBe(false);
  });
});

describe("readStoredTheme", () => {
  it("odczytuje zapisany motyw", () => {
    const storage = memoryStorage({ [THEME_STORAGE_KEY]: "dark" });
    expect(readStoredTheme(storage)).toBe("dark");
  });

  it("ignoruje nieznaną wartość", () => {
    const storage = memoryStorage({ [THEME_STORAGE_KEY]: "neon" });
    expect(readStoredTheme(storage)).toBeNull();
  });

  it("nie wywraca się bez magazynu ani przy błędzie dostępu", () => {
    expect(readStoredTheme(null)).toBeNull();
    const broken: ThemeStorage = {
      getItem: () => {
        throw new Error("brak dostępu");
      },
      setItem: () => undefined,
    };
    expect(readStoredTheme(broken)).toBeNull();
  });
});

describe("storeTheme", () => {
  it("zapisuje wybór użytkownika", () => {
    const storage = memoryStorage();
    storeTheme(storage, "dark");
    expect(storage.getItem(THEME_STORAGE_KEY)).toBe("dark");
  });

  it("milczy, gdy zapis jest niemożliwy", () => {
    const broken: ThemeStorage = {
      getItem: () => null,
      setItem: () => {
        throw new Error("tryb prywatny");
      },
    };
    expect(() => storeTheme(broken, "light")).not.toThrow();
  });
});

describe("resolveTheme", () => {
  it("zapisany wybór wygrywa z ustawieniem systemowym", () => {
    expect(resolveTheme("light", true)).toBe("light");
    expect(resolveTheme("dark", false)).toBe("dark");
  });

  it("bez zapisu decyduje system", () => {
    expect(resolveTheme(null, true)).toBe("dark");
    expect(resolveTheme(null, false)).toBe("light");
  });
});

describe("toggleTheme", () => {
  it("przełącza w obie strony", () => {
    expect(toggleTheme("light")).toBe("dark");
    expect(toggleTheme("dark")).toBe("light");
  });
});

describe("applyThemeToRoot", () => {
  it("dodaje klasę dark i ustawia color-scheme", () => {
    const root = fakeRoot();
    applyThemeToRoot("dark", root);
    expect(root.classes.has("dark")).toBe(true);
    expect(root.dataset?.theme).toBe("dark");
    expect(root.style?.colorScheme).toBe("dark");
  });

  it("usuwa klasę dark przy powrocie do jasnego", () => {
    const root = fakeRoot();
    applyThemeToRoot("dark", root);
    applyThemeToRoot("light", root);
    expect(root.classes.has("dark")).toBe(false);
    expect(root.style?.colorScheme).toBe("light");
  });

  it("nie wywraca się bez elementu głównego", () => {
    expect(() => applyThemeToRoot("dark", null)).not.toThrow();
  });
});

describe("etykiety motywu", () => {
  it("nazywa stan i akcję osobno", () => {
    expect(themeLabel("dark")).toBe("Motyw ciemny");
    expect(themeToggleLabel("dark")).toBe("Włącz motyw jasny");
    expect(themeToggleLabel("light")).toBe("Włącz motyw ciemny");
  });
});
