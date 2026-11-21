import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import ArchivePage from "./Page";

/**
 * Test dymny ekranu: sprawdza, że strona archiwum renderuje się bez wyjątku
 * i pokazuje pole zapytania, licznik znaków oraz stan początkowy.
 *
 * Radix używa `useLayoutEffect`, którego serwerowy renderer nie obsługuje —
 * ostrzeżenia są tu spodziewane, więc je wyciszamy.
 */
function renderPage(): string {
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
        <MemoryRouter initialEntries={["/archiwum"]}>
          <ArchivePage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  } finally {
    console.error = originalError;
  }
}

describe("ArchivePage", () => {
  it("renderuje nagłówek i pole zapytania", () => {
    const html = renderPage();

    expect(html).toContain("Archiwum spraw");
    expect(html).toContain("Wklej treść wniosku");
    expect(html).toContain("Szukaj w archiwum");
  });

  it("pokazuje licznik znaków i stan początkowy listy", () => {
    const html = renderPage();

    expect(html).toContain("0 / 4000 znaków");
    expect(html).toContain("Zacznij od treści wniosku");
  });

  it("udostępnia ustawienia liczby wyników i roku", () => {
    const html = renderPage();

    expect(html).toContain("Liczba wyników");
    expect(html).toContain("Sprawy od roku");
  });
});
