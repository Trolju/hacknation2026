import { format } from "date-fns";
import { describe, expect, it } from "vitest";

import {
  daysSince,
  groupByDeadline,
  referenceToday,
} from "@/features/calendar/derive";
import type { Case } from "@/lib/types";

function makeCase(overrides: Partial<Case>): Case {
  return {
    id: "c0000001-0000-4000-8000-000000000001",
    case_number: "BKS.IV.1431.1.2026",
    ordinal: 1,
    subject: "Wniosek testowy",
    applicant: "Jan Testowy",
    inflow_date: "2026-03-02",
    deadline: "2026-03-16",
    response_date: null,
    handler_initials: "JK",
    status: "nowy",
    year: 2026,
    days_remaining: 0,
    urgency: "today",
    applicant_type: "inne",
    source_document_id: null,
    kwerenda_days: null,
    created_at: "2026-03-02T08:00:00+00:00",
    updated_at: "2026-03-02T08:00:00+00:00",
    ...overrides,
  };
}

describe("data odniesienia", () => {
  it("odtwarza dziś backendu z terminu i liczby dni", () => {
    const cases = [
      makeCase({ deadline: "2026-03-16", days_remaining: 0 }),
      makeCase({ deadline: "2026-03-06", days_remaining: -10 }),
    ];
    expect(format(referenceToday(cases), "yyyy-MM-dd")).toBe("2026-03-16");
  });

  it("liczy dni od daty odniesienia", () => {
    const reference = new Date(2026, 2, 16);
    expect(daysSince(reference, "2026-03-16")).toBe(0);
    expect(daysSince(reference, "2026-03-01")).toBe(15);
    expect(daysSince(reference, "2026-03-26")).toBe(-10);
  });
});

describe("grupowanie po dniu terminu", () => {
  it("liczy wnioski przypadające na ten sam dzień", () => {
    const grouped = groupByDeadline([
      makeCase({ id: "a", deadline: "2026-03-16" }),
      makeCase({ id: "b", deadline: "2026-03-16" }),
      makeCase({ id: "c", deadline: "2026-03-17" }),
    ]);
    expect(grouped.get("2026-03-16")).toHaveLength(2);
    expect(grouped.get("2026-03-17")).toHaveLength(1);
    expect(grouped.get("2026-03-18")).toBeUndefined();
  });

  it("zwraca pustą mapę dla braku wniosków", () => {
    expect(groupByDeadline([]).size).toBe(0);
  });
});
