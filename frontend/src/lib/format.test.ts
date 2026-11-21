import { describe, expect, it } from "vitest";

import {
  STATUS_LABEL,
  URGENCY_LABEL,
  formatDate,
  formatShortDate,
  relativeDays,
} from "@/lib/format";

describe("formatowanie dat", () => {
  it("formatuje datę ISO po polsku", () => {
    expect(formatDate("2026-03-16")).toBe("16 marca 2026");
  });

  it("formatuje datę krótko", () => {
    expect(formatShortDate("2026-03-16")).toBe("16.03.2026");
  });

  it("zwraca myślnik dla braku wartości", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatShortDate(undefined)).toBe("—");
  });
});

describe("odległość do terminu", () => {
  it("opisuje dni względem dziś", () => {
    expect(relativeDays(0)).toBe("dziś");
    expect(relativeDays(1)).toBe("jutro");
    expect(relativeDays(-1)).toBe("wczoraj");
    expect(relativeDays(-5)).toBe("5 dni temu");
    expect(relativeDays(3)).toBe("za 3 dni");
  });
});

describe("słowniki etykiet", () => {
  it("pokrywa wszystkie statusy sprawy", () => {
    expect(Object.keys(STATUS_LABEL)).toHaveLength(5);
  });

  it("pokrywa wszystkie poziomy pilności", () => {
    expect(Object.keys(URGENCY_LABEL)).toHaveLength(6);
  });
});
