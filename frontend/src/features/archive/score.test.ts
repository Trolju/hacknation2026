import { describe, expect, it } from "vitest";

import type { SimilarCase } from "@/lib/types";

import {
  formatScore,
  queryPreview,
  scorePercent,
  scoreTone,
  sortByScore,
} from "./score";

function result(archiveId: string, score: number): SimilarCase {
  return {
    archive_id: archiveId,
    case_number: `UDIP.1435.${archiveId}.2025`,
    subject: `Sprawa ${archiveId}`,
    year: 2025,
    score,
    snippet: "",
    matched_terms: [],
    response_excerpt: "",
  };
}

describe("scorePercent", () => {
  it("zamienia ocenę na procent szerokości paska", () => {
    expect(scorePercent(0.82)).toBe(82);
    expect(scorePercent(0)).toBe(0);
    expect(scorePercent(1)).toBe(100);
  });

  it("przycina wartości spoza przedziału", () => {
    expect(scorePercent(-0.5)).toBe(0);
    expect(scorePercent(1.7)).toBe(100);
  });

  it("traktuje NaN jak zero", () => {
    expect(scorePercent(Number.NaN)).toBe(0);
  });
});

describe("formatScore", () => {
  it("używa przecinka dziesiętnego", () => {
    expect(formatScore(0.8234)).toBe("0,82");
    expect(formatScore(1)).toBe("1,00");
  });

  it("przycina wartości spoza przedziału", () => {
    expect(formatScore(-1)).toBe("0,00");
    expect(formatScore(3)).toBe("1,00");
  });
});

describe("scoreTone", () => {
  it("rozróżnia mocne, średnie i słabe trafienia", () => {
    expect(scoreTone(0.75)).toBe("high");
    expect(scoreTone(0.6)).toBe("high");
    expect(scoreTone(0.45)).toBe("medium");
    expect(scoreTone(0.35)).toBe("medium");
    expect(scoreTone(0.2)).toBe("low");
  });
});

describe("sortByScore", () => {
  it("sortuje malejąco po ocenie", () => {
    const sorted = sortByScore([result("a0003", 0.2), result("a0001", 0.9), result("a0002", 0.5)]);

    expect(sorted.map((item) => item.archive_id)).toEqual(["a0001", "a0002", "a0003"]);
  });

  it("przy remisie decyduje identyfikator", () => {
    const sorted = sortByScore([result("a0009", 0.5), result("a0002", 0.5)]);

    expect(sorted.map((item) => item.archive_id)).toEqual(["a0002", "a0009"]);
  });

  it("nie zmienia listy wejściowej", () => {
    const input = [result("a0001", 0.1), result("a0002", 0.9)];
    sortByScore(input);

    expect(input.map((item) => item.archive_id)).toEqual(["a0001", "a0002"]);
  });
});

describe("queryPreview", () => {
  it("zwraca zapytanie bez zmian, jeśli mieści się w limicie", () => {
    expect(queryPreview("  diety   radnych ")).toBe("diety radnych");
  });

  it("skraca długie zapytanie wielokropkiem", () => {
    const preview = queryPreview("a".repeat(200), 20);

    expect(preview).toHaveLength(20);
    expect(preview.endsWith("…")).toBe(true);
  });
});
