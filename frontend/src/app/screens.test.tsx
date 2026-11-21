import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { ThemeProvider } from "@/app/ThemeProvider";

/**
 * Test integracyjny powłoki i ekranów.
 *
 * Każdy ekran renderujemy serwerowo w kontekście motywu, zapytań i routera.
 * Test nie sprawdza treści (dane przychodzą z API), tylko to, że wspólne
 * komponenty — `PageHeader`, `States`, `DataTable` — przyjmują to, co podają
 * moduły, i że żaden ekran nie wywraca się przy pierwszym renderze.
 */
const SCREENS: [string, () => Promise<{ default: () => JSX.Element }>][] = [
  ["pulpit", () => import("@/features/dashboard/Page")],
  ["kalendarz", () => import("@/features/calendar/Page")],
  ["dokumenty", () => import("@/features/ingest/Page")],
  ["archiwum", () => import("@/features/archive/Page")],
  ["wydziały", () => import("@/features/routing/Page")],
  ["odpowiedzi", () => import("@/features/drafting/Page")],
  ["anonimizacja", () => import("@/features/anonymize/Page")],
  ["ustawienia", () => import("@/features/settings/Page")],
];

function renderScreen(Page: () => JSX.Element): string {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
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
        <ThemeProvider>
          <MemoryRouter initialEntries={["/"]}>
            <Page />
          </MemoryRouter>
        </ThemeProvider>
      </QueryClientProvider>,
    );
  } finally {
    console.error = originalError;
  }
}

describe("ekrany aplikacji", () => {
  for (const [name, load] of SCREENS) {
    it(`renderuje ekran: ${name}`, async () => {
      const module = await load();
      const html = renderScreen(module.default);
      expect(html.length).toBeGreaterThan(50);
    });
  }
});
