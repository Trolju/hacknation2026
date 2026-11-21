import { describe, expect, it } from "vitest";

import {
  STATUS_ORDER,
  requiresNote,
  transitionOptions,
} from "@/features/calendar/statusMachine";
import type { CaseStatus } from "@/lib/types";

function option(current: CaseStatus, to: CaseStatus) {
  return transitionOptions(current).find((item) => item.to === to);
}

describe("maszyna stanów a–e", () => {
  it("zachowuje kolejność stanów", () => {
    expect(STATUS_ORDER).toEqual([
      "nowy",
      "zapytania_wyslane",
      "kwerenda",
      "przygotowana_odpowiedz",
      "odpowiedz_wyslana",
    ]);
  });

  it("pozwala przejść naprzód o jeden krok", () => {
    expect(option("nowy", "zapytania_wyslane")).toMatchObject({
      kind: "forward",
      requiresNote: false,
    });
    expect(option("kwerenda", "przygotowana_odpowiedz")).toMatchObject({
      kind: "forward",
      requiresNote: false,
    });
    expect(option("przygotowana_odpowiedz", "odpowiedz_wyslana")).toMatchObject({
      kind: "forward",
      requiresNote: false,
    });
  });

  it("pozwala pominąć kwerendę", () => {
    expect(option("zapytania_wyslane", "przygotowana_odpowiedz")).toMatchObject({
      kind: "skip",
      requiresNote: false,
    });
  });

  it("wymaga notatki przy cofnięciu", () => {
    expect(option("zapytania_wyslane", "nowy")).toMatchObject({
      kind: "backward",
      requiresNote: true,
    });
    expect(option("odpowiedz_wyslana", "przygotowana_odpowiedz")).toMatchObject({
      kind: "backward",
      requiresNote: true,
    });
  });

  it("nie pokazuje przejść niedozwolonych", () => {
    expect(option("nowy", "kwerenda")).toBeUndefined();
    expect(option("nowy", "odpowiedz_wyslana")).toBeUndefined();
    expect(option("nowy", "nowy")).toBeUndefined();
    expect(option("kwerenda", "nowy")).toBeUndefined();
    expect(option("odpowiedz_wyslana", "nowy")).toBeUndefined();
  });

  it("nie proponuje niczego poza stanem końcowym w przód", () => {
    expect(transitionOptions("odpowiedz_wyslana")).toHaveLength(1);
    expect(transitionOptions("nowy")).toHaveLength(1);
    expect(transitionOptions("zapytania_wyslane")).toHaveLength(3);
  });

  it("rozpoznaje przejścia wymagające notatki", () => {
    expect(requiresNote("zapytania_wyslane", "nowy")).toBe(true);
    expect(requiresNote("odpowiedz_wyslana", "przygotowana_odpowiedz")).toBe(true);
    expect(requiresNote("nowy", "zapytania_wyslane")).toBe(false);
    expect(requiresNote("nowy", "nowy")).toBe(false);
  });
});
