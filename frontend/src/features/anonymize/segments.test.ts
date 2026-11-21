import { describe, expect, it } from "vitest";

import type { Span } from "@/lib/types";

import { buildSegments, withSpan, withoutSpan } from "./segments";

function span(start: number, end: number, category = "pesel"): Span {
  return {
    start,
    end,
    text: "",
    category,
    confidence: 0.9,
    source: "regex",
  };
}

describe("buildSegments", () => {
  it("dzieli tekst na fragmenty zwykłe i objęte spanem", () => {
    const text = "Jan Kowalski, PESEL 85041212345.";
    const segments = buildSegments(text, [span(0, 12, "imie_nazwisko"), span(20, 31)]);
    expect(segments.map((segment) => segment.text)).toEqual([
      "Jan Kowalski",
      ", PESEL ",
      "85041212345",
      ".",
    ]);
    expect(segments[0].span?.category).toBe("imie_nazwisko");
    expect(segments[1].span).toBeUndefined();
  });

  it("zwraca cały tekst, gdy nie ma spanów", () => {
    expect(buildSegments("Bez danych.", [])).toEqual([{ text: "Bez danych." }]);
  });

  it("pomija spany nachodzące na siebie", () => {
    const text = "abcdefghij";
    const segments = buildSegments(text, [span(0, 5), span(3, 8)]);
    expect(segments.map((segment) => segment.text)).toEqual(["abcde", "fghij"]);
  });

  it("pomija spany wychodzące poza tekst", () => {
    const segments = buildSegments("abc", [span(1, 99)]);
    expect(segments).toEqual([{ text: "abc" }]);
  });

  it("pomija spany puste", () => {
    expect(buildSegments("abc", [span(1, 1)])).toEqual([{ text: "abc" }]);
  });
});

describe("withSpan", () => {
  it("dokłada span i utrzymuje kolejność", () => {
    const result = withSpan([span(10, 15)], span(0, 5));
    expect(result.map((item) => item.start)).toEqual([0, 10]);
  });

  it("usuwa zaznaczenie nakładające się na nowe", () => {
    const result = withSpan([span(0, 10)], span(4, 12, "adres"));
    expect(result).toHaveLength(1);
    expect(result[0].category).toBe("adres");
  });

  it("zostawia spany rozłączne", () => {
    const result = withSpan([span(0, 5)], span(5, 9));
    expect(result).toHaveLength(2);
  });
});

describe("withoutSpan", () => {
  it("usuwa span po pozycji i kategorii", () => {
    const spans = [span(0, 5), span(10, 15, "email")];
    expect(withoutSpan(spans, span(10, 15, "email"))).toEqual([span(0, 5)]);
  });

  it("nie usuwa spanu o innej kategorii na tej samej pozycji", () => {
    const spans = [span(0, 5, "pesel")];
    expect(withoutSpan(spans, span(0, 5, "nip"))).toHaveLength(1);
  });
});
