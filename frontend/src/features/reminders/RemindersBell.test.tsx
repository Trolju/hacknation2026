import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { RemindersBell } from "@/features/reminders/RemindersBell";
import { REMINDERS_QUERY_KEY } from "@/features/reminders/api";
import type { Reminder } from "@/features/reminders/types";

/**
 * Testy dzwonka w nagłówku. Dane wkładamy wprost do cache'u TanStack Query,
 * dzięki czemu render serwerowy widzi gotową listę bez wywołania sieci.
 *
 * Radix używa `useLayoutEffect`, którego serwerowy renderer nie obsługuje —
 * ostrzeżenia są tu spodziewane, więc je wyciszamy.
 */
const REMINDERS: Reminder[] = [
  {
    case_id: "c0000001-0000-4000-8000-000000000001",
    case_number: "BKS.IV.1431.1.2026",
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
    case_number: "BKS.IV.1431.2.2026",
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
    case_number: "BKS.IV.1431.3.2026",
    subject: "Wydatki na promocję miasta w mediach społecznościowych",
    deadline: "2026-03-17",
    days_remaining: 1,
    urgency: "tomorrow",
    status: "przygotowana_odpowiedz",
    handler_initials: "PN",
    message: "Termin odpowiedzi mija jutro.",
  },
];

function renderBell(reminders: Reminder[]): string {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  client.setQueryData(REMINDERS_QUERY_KEY, reminders);

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
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/"]}>
          <RemindersBell />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  } finally {
    console.error = originalError;
  }
}

describe("dzwonek przypomnień", () => {
  it("pokazuje licznik pilnych wniosków", () => {
    const html = renderBell(REMINDERS);

    expect(html).toContain('aria-label="Przypomnienia: 3"');
    expect(html).toContain(">3</span>");
  });

  it("nie pokazuje licznika, gdy nie ma przypomnień", () => {
    const html = renderBell([]);

    expect(html).toContain('aria-label="Brak przypomnień"');
    expect(html).not.toContain(">0</span>");
  });
});
