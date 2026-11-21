import { describe, expect, it } from "vitest";

import {
  HOME_CRUMB,
  NOT_FOUND_CRUMB,
  buildBreadcrumbs,
  normalizePath,
} from "@/app/breadcrumbs";

const FEATURES = [
  { path: "", label: "Pulpit" },
  { path: "kalendarz", label: "Kalendarz terminów" },
  { path: "dokumenty", label: "Dokumenty" },
];

describe("normalizePath", () => {
  it("usuwa końcowy ukośnik", () => {
    expect(normalizePath("/kalendarz/")).toBe("/kalendarz");
    expect(normalizePath("/kalendarz///")).toBe("/kalendarz");
  });

  it("zamienia pusty adres na stronę główną", () => {
    expect(normalizePath("")).toBe("/");
    expect(normalizePath("/")).toBe("/");
  });
});

describe("buildBreadcrumbs", () => {
  it("na stronie głównej pokazuje tylko nazwę ekranu", () => {
    expect(buildBreadcrumbs("/", FEATURES)).toEqual([{ label: "Pulpit" }]);
  });

  it("na ekranie modułu dokłada okruszek Start", () => {
    expect(buildBreadcrumbs("/kalendarz", FEATURES)).toEqual([
      HOME_CRUMB,
      { label: "Kalendarz terminów" },
    ]);
  });

  it("radzi sobie z końcowym ukośnikiem w adresie", () => {
    expect(buildBreadcrumbs("/dokumenty/", FEATURES)).toEqual([
      HOME_CRUMB,
      { label: "Dokumenty" },
    ]);
  });

  it("dla nieznanego adresu zwraca informację o braku ekranu", () => {
    expect(buildBreadcrumbs("/nie-ma-takiego", FEATURES)).toEqual([
      HOME_CRUMB,
      NOT_FOUND_CRUMB,
    ]);
  });

  it("nie gubi okruszków, gdy rejestr jest pusty", () => {
    expect(buildBreadcrumbs("/kalendarz", [])).toEqual([
      HOME_CRUMB,
      NOT_FOUND_CRUMB,
    ]);
  });
});
