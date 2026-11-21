import { describe, expect, it } from "vitest";

import type { DepartmentSuggestion } from "@/lib/types";

import {
  DEFAULT_SELECTION_SIZE,
  defaultSelection,
  isAllSelected,
  pruneSelection,
  toggleId,
} from "./selection";

function suggestion(id: string, confidence = 0.5): DepartmentSuggestion {
  return {
    department_id: id,
    name: `Komórka ${id}`,
    confidence,
    rationale: "",
    matched_terms: [],
  };
}

const SUGGESTIONS = [
  suggestion("waiu", 0.9),
  suggestion("bpra", 0.4),
  suggestion("wfin", 0.2),
];

describe("toggleId", () => {
  it("dodaje identyfikator na koniec", () => {
    expect(toggleId(["waiu"], "bpra")).toEqual(["waiu", "bpra"]);
  });

  it("usuwa identyfikator, zachowując kolejność reszty", () => {
    expect(toggleId(["waiu", "bpra", "wfin"], "bpra")).toEqual(["waiu", "wfin"]);
  });

  it("nie duplikuje identyfikatora", () => {
    expect(toggleId(["waiu"], "waiu")).toEqual([]);
  });

  it("nie zmienia wejścia", () => {
    const ids = ["waiu"];
    toggleId(ids, "bpra");
    expect(ids).toEqual(["waiu"]);
  });
});

describe("defaultSelection", () => {
  it("bierze dwie najlepsze sugestie", () => {
    expect(defaultSelection(SUGGESTIONS)).toEqual(["waiu", "bpra"]);
    expect(DEFAULT_SELECTION_SIZE).toBe(2);
  });

  it("radzi sobie z krótszą listą", () => {
    expect(defaultSelection([suggestion("waiu")])).toEqual(["waiu"]);
  });

  it("zwraca pustą listę bez sugestii", () => {
    expect(defaultSelection([])).toEqual([]);
  });
});

describe("pruneSelection", () => {
  it("zostawia tylko komórki obecne na liście sugestii", () => {
    expect(pruneSelection(["waiu", "sm", "wfin"], SUGGESTIONS)).toEqual([
      "waiu",
      "wfin",
    ]);
  });

  it("zachowuje kolejność zaznaczenia, nie listy sugestii", () => {
    expect(pruneSelection(["wfin", "waiu"], SUGGESTIONS)).toEqual(["wfin", "waiu"]);
  });

  it("czyści zaznaczenie, gdy sugestii brak", () => {
    expect(pruneSelection(["waiu"], [])).toEqual([]);
  });
});

describe("isAllSelected", () => {
  it("rozpoznaje pełne zaznaczenie", () => {
    expect(isAllSelected(["waiu", "bpra", "wfin"], SUGGESTIONS)).toBe(true);
  });

  it("rozpoznaje częściowe zaznaczenie", () => {
    expect(isAllSelected(["waiu"], SUGGESTIONS)).toBe(false);
  });

  it("pusta lista sugestii nie jest pełnym zaznaczeniem", () => {
    expect(isAllSelected([], [])).toBe(false);
  });
});
