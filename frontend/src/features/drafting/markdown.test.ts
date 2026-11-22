import { describe, expect, it } from "vitest";

import {
  citationRefs,
  htmlToMarkdown,
  markerRangeFor,
  markdownToHtml,
  sectionForClaim,
  splitSections,
} from "./markdown";

const SAMPLE = [
  "## Podstawa prawna",
  "",
  "Zgodnie z art. 13 ust. 1 ustawy udostępnianie następuje w terminie 14 dni [^1].",
  "",
  "## Odpowiedź",
  "",
  "W odpowiedzi na wniosek uprzejmie informuję, co następuje.",
  "",
  "- pierwszy punkt [^2]",
  "- drugi punkt",
  "",
  "1. krok pierwszy",
  "2. krok drugi",
  "",
  "## Pouczenie",
  "",
  "Odmowa następuje w drodze decyzji [^3].",
].join("\n");

describe("markdownToHtml", () => {
  it("zamienia nagłówki na elementy h2 i h3", () => {
    const html = markdownToHtml("## Sekcja\n\n### Podsekcja");
    expect(html).toContain("<h2>Sekcja</h2>");
    expect(html).toContain("<h3>Podsekcja</h3>");
  });

  it("skleja zawinięte wiersze w jeden akapit", () => {
    const html = markdownToHtml("Pierwszy wiersz\n drugi wiersz");
    expect(html).toBe("<p>Pierwszy wiersz drugi wiersz</p>");
  });

  it("zamienia pogrubienie i zachowuje odnośniki", () => {
    const html = markdownToHtml("**Ważne** zdanie [^7].");
    expect(html).toContain("<strong>Ważne</strong>");
    expect(html).toContain("[^7]");
  });

  it("buduje listy punktowane i numerowane", () => {
    const html = markdownToHtml("- raz\n- dwa\n\n1. trzy\n2. cztery");
    expect(html).toContain("<ul><li><p>raz</p></li><li><p>dwa</p></li></ul>");
    expect(html).toContain("<ol><li><p>trzy</p></li><li><p>cztery</p></li></ol>");
  });

  it("escapuje znaki specjalne HTML", () => {
    const html = markdownToHtml("Wniosek <pilny> & ważny");
    expect(html).toContain("&lt;pilny&gt;");
    expect(html).toContain("&amp;");
  });
});

describe("htmlToMarkdown", () => {
  it("odtwarza nagłówki, akapity i listy", () => {
    const markdown = htmlToMarkdown(
      "<h2>Podstawa prawna</h2><p>Treść [^1].</p><ul><li><p>punkt</p></li></ul>",
    );
    expect(markdown).toBe("## Podstawa prawna\n\nTreść [^1].\n\n- punkt");
  });

  it("zachowuje pogrubienie i kursywę", () => {
    const markdown = htmlToMarkdown("<p><strong>Ważne</strong> i <em>delikatne</em></p>");
    expect(markdown).toBe("**Ważne** i *delikatne*");
  });

  it("przeżywa pełny obieg Markdown → HTML → Markdown", () => {
    const roundTrip = htmlToMarkdown(markdownToHtml(SAMPLE));
    expect(roundTrip).toBe(SAMPLE);
  });

  it("nie gubi treści przy pustym dokumencie", () => {
    expect(htmlToMarkdown("<p></p>")).toBe("");
  });
});

describe("splitSections", () => {
  it("dzieli treść po nagłówkach", () => {
    const sections = splitSections(SAMPLE);
    expect(sections.map((section) => section.heading)).toEqual([
      null,
      "Podstawa prawna",
      "Odpowiedź",
      "Pouczenie",
    ]);
    expect(sections[2].text).toContain("pierwszy punkt");
  });
});

describe("sectionForClaim", () => {
  it("znajduje sekcję twierdzenia bez źródła", () => {
    const body = `${SAMPLE}\n\nW 2025 roku wydano 120 decyzji.`;
    expect(sectionForClaim(body, "W 2025 roku wydano 120 decyzji.")).toBe("Pouczenie");
  });

  it("znajduje twierdzenie zawinięte w środku zdania", () => {
    const body = "## Odpowiedź\n\nW 2025 roku wydano\n120 decyzji o warunkach.";
    expect(sectionForClaim(body, "W 2025 roku wydano 120 decyzji o warunkach.")).toBe(
      "Odpowiedź",
    );
  });

  it("zwraca null, gdy twierdzenia nie ma w treści", () => {
    expect(sectionForClaim(SAMPLE, "Zupełnie inne zdanie.")).toBeNull();
  });
});

describe("citationRefs", () => {
  it("zwraca numery odnośników bez powtórzeń", () => {
    expect(citationRefs(SAMPLE)).toEqual([1, 2, 3]);
  });

  it("zwraca pustą listę, gdy nie ma odnośników", () => {
    expect(citationRefs("Treść bez źródeł.")).toEqual([]);
  });
});

describe("markerRangeFor", () => {
  it("znajduje zakres obejmujący numer ze środka", () => {
    expect(markerRangeFor("Podstawa [^2]–[^13].", 5)).toBe("[^2]–[^13]");
  });

  it("zwraca null, gdy numer leży poza zakresem", () => {
    expect(markerRangeFor("Podstawa [^2]–[^13].", 14)).toBeNull();
  });

  it("zwraca null, gdy w treści nie ma zakresów", () => {
    expect(markerRangeFor("Podstawa [^1][^2].", 1)).toBeNull();
  });

  it("obsługuje kilka zakresów w jednej treści", () => {
    const body = "A [^1]–[^3] B [^7]–[^9]";
    expect(markerRangeFor(body, 8)).toBe("[^7]–[^9]");
    expect(markerRangeFor(body, 2)).toBe("[^1]–[^3]");
  });
});
