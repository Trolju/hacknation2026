import { describe, expect, it } from "vitest";

import {
  pluralReminders,
  reminderCounterLabel,
  reminderHref,
} from "@/features/reminders/derive";
import type { Reminder } from "@/features/reminders/types";

function makeReminder(overrides: Partial<Reminder> = {}): Reminder {
  return {
    case_id: "c0000001-0000-4000-8000-000000000001",
    case_number: "BKS.IV.1431.1.2026",
    subject: "Wynagrodzenia pracowników Urzędu Miasta w 2025 r.",
    deadline: "2026-03-06",
    days_remaining: -10,
    urgency: "overdue",
    status: "zapytania_wyslane",
    handler_initials: "JK",
    message: "Termin odpowiedzi minął 10 dni temu.",
    ...overrides,
  };
}

describe("odmiana licznika przypomnień", () => {
  it("odmienia rzeczownik po liczbie", () => {
    expect(pluralReminders(1)).toBe("1 przypomnienie");
    expect(pluralReminders(2)).toBe("2 przypomnienia");
    expect(pluralReminders(4)).toBe("4 przypomnienia");
    expect(pluralReminders(5)).toBe("5 przypomnień");
    expect(pluralReminders(12)).toBe("12 przypomnień");
    expect(pluralReminders(22)).toBe("22 przypomnienia");
    expect(pluralReminders(0)).toBe("0 przypomnień");
  });

  it("buduje etykietę dzwonka", () => {
    expect(reminderCounterLabel(0)).toBe("Brak przypomnień");
    expect(reminderCounterLabel(3)).toBe("Przypomnienia: 3");
  });
});

describe("adres wniosku z przypomnienia", () => {
  it("prowadzi do karty wniosku w kalendarzu", () => {
    expect(reminderHref(makeReminder())).toBe(
      "/kalendarz?case=c0000001-0000-4000-8000-000000000001",
    );
  });
});
