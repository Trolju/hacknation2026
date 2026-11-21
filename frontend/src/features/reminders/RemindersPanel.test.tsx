import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { RemindersPanel } from "@/features/reminders/RemindersPanel";
import type { Reminder } from "@/features/reminders/types";

/**
 * Testy listy przypomnień. Renderujemy serwerowo, bo środowisko testów nie ma
 * DOM-u — sprawdzamy więc wyłącznie to, co trafia do HTML-a: numer wniosku,
 * oznaczenie pilności, tekst przypomnienia i stan pusty.
 */
const REMINDERS: Reminder[] = [
  {
    case_id: "c0000001-0000-4000-8000-000000000001",
    case_number: "UDIP.1435.1.2026",
    subject: "Wynagrodzenia pracowników Urzędu Miasta w 2025 r.",
    deadline: "2026-03-06",
    days_remaining: -10,
    urgency: "overdue",
    status: "zapytania_wyslane",
    handler_initials: "JK",
    message: "Termin odpowiedzi minął 10 dni temu.",
  },
  {
    case_id: "c0000001-0000-4000-8000-000000000002",
    case_number: "UDIP.1435.2.2026",
    subject: "Kopie umów najmu lokali komunalnych przy ul. Dworcowej",
    deadline: "2026-03-16",
    days_remaining: 0,
    urgency: "today",
    status: "kwerenda",
    handler_initials: "AM",
    message: "Termin odpowiedzi mija dziś.",
  },
  {
    case_id: "c0000001-0000-4000-8000-000000000003",
    case_number: "UDIP.1435.3.2026",
    subject: "Wydatki na promocję miasta w mediach społecznościowych",
    deadline: "2026-03-17",
    days_remaining: 1,
    urgency: "tomorrow",
    status: "przygotowana_odpowiedz",
    handler_initials: "PN",
    message: "Termin odpowiedzi mija jutro.",
  },
];

function renderPanel(reminders: Reminder[]): string {
  // Router używa `useLayoutEffect`, którego serwerowy renderer nie obsługuje —
  // ostrzeżenia są tu spodziewane, więc je wyciszamy.
  const originalError = console.error;
  console.error = (...args: unknown[]) => {
    const first = args[0];
    if (
      typeof first === "string" &&
      first.includes("useLayoutEffect does nothing on the server")
    ) {
      return;
    }
    originalError(...args);
  };
  try {
    return renderToString(
      <MemoryRouter initialEntries={["/"]}>
        <RemindersPanel reminders={reminders} />
      </MemoryRouter>,
    );
  } finally {
    console.error = originalError;
  }
}

describe("lista przypomnień", () => {
  it("pokazuje wnioski po terminie, na dziś i na jutro", () => {
    const html = renderPanel(REMINDERS);

    expect(html).toContain("UDIP.1435.1.2026");
    expect(html).toContain("UDIP.1435.2.2026");
    expect(html).toContain("UDIP.1435.3.2026");
    expect(html).toContain("Po terminie");
    expect(html).toContain("Termin dziś");
    expect(html).toContain("Termin jutro");
  });

  it("pokazuje tekst przypomnienia i termin z wniosku", () => {
    const html = renderPanel(REMINDERS);

    expect(html).toContain("Termin odpowiedzi minął 10 dni temu.");
    expect(html).toContain("Termin odpowiedzi mija dziś.");
    expect(html).toContain("06.03.2026");
  });

  it("podaje liczbę przypomnień w nagłówku", () => {
    expect(renderPanel(REMINDERS)).toContain("3 przypomnienia");
    expect(renderPanel(REMINDERS.slice(0, 1))).toContain("1 przypomnienie");
  });

  it("linkuje każde przypomnienie do karty wniosku", () => {
    const html = renderPanel(REMINDERS);

    expect(html).toContain(
      'href="/kalendarz?case=c0000001-0000-4000-8000-000000000001"',
    );
  });

  it("pokazuje stan pusty, gdy nie ma pilnych terminów", () => {
    const html = renderPanel([]);

    expect(html).toContain("Brak pilnych terminów");
    expect(html).toContain("0 przypomnień");
    expect(html).not.toContain("UDIP.1435.1.2026");
  });
});
