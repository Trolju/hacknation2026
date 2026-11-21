import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { Layout } from "@/app/Layout";
import { ThemeProvider } from "@/app/ThemeProvider";

/**
 * Test dymny powłoki: renderuje układ w całości i sprawdza, że szkielet
 * (nawigacja, breadcrumbs, przyciski palety i motywu) powstaje bez wyjątku.
 *
 * Radix używa `useLayoutEffect`, którego serwerowy renderer nie obsługuje —
 * ostrzeżenia są w tym teście spodziewane, więc je wyciszamy.
 */
function renderShell(path: string): string {
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
          <MemoryRouter initialEntries={[path]}>
            <Layout />
          </MemoryRouter>
        </ThemeProvider>
      </QueryClientProvider>,
    );
  } finally {
    console.error = originalError;
  }
}

describe("powłoka aplikacji", () => {
  it("renderuje szkielet z linkiem pomijającym nawigację", () => {
    const html = renderShell("/kalendarz");
    expect(html).toContain("Przejdź do treści");
    expect(html).toContain('id="tresc"');
  });

  it("pokazuje breadcrumbs zgodne z bieżącym ekranem", () => {
    const html = renderShell("/kalendarz");
    expect(html).toContain("Ścieżka nawigacji");
    expect(html).toContain("Kalendarz terminów");
    expect(html).toContain('aria-current="page"');
  });

  it("udostępnia przyciski palety poleceń, motywu i skrótów", () => {
    const html = renderShell("/dokumenty");
    expect(html).toContain("Otwórz paletę poleceń");
    expect(html).toContain("Włącz motyw ciemny");
    expect(html).toContain("Skróty klawiszowe");
  });

  it("renderuje menu wszystkich widocznych ekranów", () => {
    const html = renderShell("/");
    for (const label of [
      "Pulpit",
      "Kalendarz terminów",
      "Dokumenty",
      "Archiwum spraw",
      "Routing wydziałowy",
      "Generator odpowiedzi",
      "Anonimizacja",
      "Ustawienia",
    ]) {
      expect(html, label).toContain(label);
    }
  });

  it("dla nieznanego adresu pokazuje okruszek o braku ekranu", () => {
    const html = renderShell("/nie-ma-takiego");
    expect(html).toContain("Nie znaleziono ekranu");
  });
});
