import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { getToken, setToken } from "./api";

/** `localStorage` nie istnieje w środowisku `node` — podstawiamy magazyn w pamięci. */
function memoryStorage(): Storage {
  const store = new Map<string, string>();
  return {
    get length() {
      return store.size;
    },
    clear: () => store.clear(),
    getItem: (key: string) => store.get(key) ?? null,
    key: (index: number) => [...store.keys()][index] ?? null,
    removeItem: (key: string) => void store.delete(key),
    setItem: (key: string, value: string) => void store.set(key, value),
  };
}

describe("token sesji", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", memoryStorage());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("zapisuje i odczytuje token", () => {
    setToken("abc.def.ghi");
    expect(getToken()).toBe("abc.def.ghi");
  });

  it("wylogowanie czyści magazyn", () => {
    setToken("abc.def.ghi");
    setToken(null);
    expect(getToken()).toBeNull();
  });

  it("brak tokenu to null, nie pusty string", () => {
    expect(getToken()).toBeNull();
  });

  it("brak dostępu do magazynu nie wywraca aplikacji", () => {
    vi.stubGlobal("localStorage", undefined);
    expect(() => setToken("abc")).not.toThrow();
    expect(getToken()).toBeNull();
  });
});
