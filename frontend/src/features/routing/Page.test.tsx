import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import RoutingPage from "./Page";

/**
 * Test dymny ekranu: renderuje stronę w całości i sprawdza, że powstaje bez
 * wyjątku oraz że stan początkowy zależy od adresu.
 *
 * Radix używa `useLayoutEffect`, którego serwerowy renderer nie obsługuje —
 * ostrzeżenia są tu spodziewane, więc je wyciszamy (tak samo jak w teście powłoki).
 */
function renderPage(path = "/wydzialy"): string {
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
        <MemoryRouter initialEntries={[path]}>
          <RoutingPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  } finally {
    console.error = originalError;
  }
}

describe("ekran routingu wydziałowego", () => {
  it("renderuje się bez wyjątku", () => {
    const html = renderPage();
    expect(html).toContain("Routing wydziałowy");
    expect(html).toContain("Sugestie komórek");
    expect(html).toContain("Podgląd zapytania");
  });

  it("bez wybranej sprawy prosi o jej wskazanie", () => {
    const html = renderPage();
    expect(html).toContain("Wybierz sprawę z listy");
  });

  it("przyjmuje sprawę z adresu i czeka na zaznaczenie komórek", () => {
    const html = renderPage("/wydzialy?case=c0000001-0000-4000-8000-000000000006");
    expect(html).toContain("Zaznacz co najmniej jedną komórkę");
  });

  it("oferuje wklejenie treści zamiast wyboru sprawy", () => {
    // Lista wniosków jeszcze się nie wczytała, więc `Select` jest wyłączony,
    // ale pole na treść jest dostępne od razu.
    expect(renderPage()).toContain("Wklej treść wniosku");
  });
});
