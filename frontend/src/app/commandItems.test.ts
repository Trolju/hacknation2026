import { describe, expect, it } from "vitest";

import {
  MIN_CASE_QUERY_LENGTH,
  caseSearchTerm,
  filterCases,
  filterEntries,
  matchesQuery,
  normalizeText,
  queryTokens,
  shouldSearchCases,
  type PaletteEntry,
} from "@/app/commandItems";

const ENTRIES: PaletteEntry[] = [
  {
    id: "nav-calendar",
    label: "Kalendarz terminów",
    description: "Wnioski według terminu odpowiedzi",
    keywords: ["kalendarz"],
  },
  {
    id: "nav-routing",
    label: "Routing wydziałowy",
    description: "Wskazywanie komórek organizacyjnych",
    keywords: ["wydzialy"],
  },
  {
    id: "action-new-case",
    label: "Nowy wniosek",
    description: "Dodaj sprawę do kalendarza",
    keywords: ["dodaj", "utwórz"],
  },
];

const CASES = [
  {
    case_number: "BKS.IV.1431.1.2026",
    subject: "Wynagrodzenia pracowników Urzędu Miasta w 2025 r.",
  },
  {
    case_number: "BKS.IV.1431.2.2026",
    subject: "Kopie umów najmu lokali komunalnych",
  },
  {
    case_number: "UDIP.2210.7.2026",
    subject: "Zezwolenia na budowę wydane w 2025 r.",
  },
];

describe("normalizeText", () => {
  it("usuwa polskie znaki diakrytyczne i wielkość liter", () => {
    expect(normalizeText("Wydziały GŁÓWNE")).toBe("wydzialy glowne");
  });

  it("skleja nadmiarowe spacje", () => {
    expect(normalizeText("  nowy   wniosek ")).toBe("nowy wniosek");
  });
});

describe("queryTokens", () => {
  it("dzieli zapytanie na słowa", () => {
    expect(queryTokens("nowy wniosek")).toEqual(["nowy", "wniosek"]);
  });

  it("dla pustego zapytania zwraca pustą listę", () => {
    expect(queryTokens("   ")).toEqual([]);
  });
});

describe("matchesQuery", () => {
  it("puste zapytanie pasuje do wszystkiego", () => {
    expect(matchesQuery(ENTRIES[0], "")).toBe(true);
  });

  it("dopasowuje po etykiecie bez polskich znaków", () => {
    expect(matchesQuery(ENTRIES[1], "wydzialy")).toBe(true);
    expect(matchesQuery(ENTRIES[1], "Wydziałowy")).toBe(true);
  });

  it("dopasowuje po słowach kluczowych i opisie", () => {
    expect(matchesQuery(ENTRIES[2], "utworz")).toBe(true);
    expect(matchesQuery(ENTRIES[0], "terminu")).toBe(true);
  });

  it("wymaga wszystkich słów zapytania", () => {
    expect(matchesQuery(ENTRIES[2], "nowy wniosek")).toBe(true);
    expect(matchesQuery(ENTRIES[2], "nowy lotnisko")).toBe(false);
  });
});

describe("filterEntries", () => {
  it("zawęża listę do pasujących pozycji", () => {
    expect(filterEntries(ENTRIES, "kalendarz").map((item) => item.id)).toEqual([
      "nav-calendar",
      "action-new-case",
    ]);
  });

  it("bez zapytania zwraca całą listę", () => {
    expect(filterEntries(ENTRIES, "")).toHaveLength(ENTRIES.length);
  });
});

describe("filterCases", () => {
  it("znajduje sprawę po numerze", () => {
    expect(filterCases(CASES, "UDIP.2210").map((item) => item.case_number)).toEqual([
      "UDIP.2210.7.2026",
    ]);
  });

  it("znajduje sprawę po fragmencie tematu bez polskich znaków", () => {
    expect(filterCases(CASES, "wynagrodzenia")).toHaveLength(1);
    expect(filterCases(CASES, "umow najmu")).toHaveLength(1);
  });

  it("zwraca pustą listę, gdy nic nie pasuje", () => {
    expect(filterCases(CASES, "lotnisko")).toEqual([]);
  });
});

describe("shouldSearchCases", () => {
  it("wymaga co najmniej dwóch znaków", () => {
    expect(MIN_CASE_QUERY_LENGTH).toBe(2);
    expect(shouldSearchCases("u")).toBe(false);
    expect(shouldSearchCases("ud")).toBe(true);
    expect(shouldSearchCases("  u ")).toBe(false);
  });
});

describe("caseSearchTerm", () => {
  it("obcina skrajne spacje przed wysłaniem do API", () => {
    expect(caseSearchTerm("  BKS.IV.1431  ")).toBe("BKS.IV.1431");
  });
});
