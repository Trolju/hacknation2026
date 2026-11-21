/**
 * Wyszukiwanie w palecie poleceń — czysta logika dopasowania.
 *
 * Wyszukiwanie jest odporne na polskie znaki i wielkość liter: „wydzialy”
 * znajduje „Wydziały”, a „zaleglosci” — „zaległości”. Zapytanie dzielimy na
 * słowa i wymagamy, żeby każde z nich wystąpiło w opisie pozycji.
 */

export type PaletteEntry = {
  id: string;
  label: string;
  description?: string;
  keywords?: string[];
};

const POLISH_LETTERS: Record<string, string> = {
  ą: "a",
  ć: "c",
  ę: "e",
  ł: "l",
  ń: "n",
  ó: "o",
  ś: "s",
  ź: "z",
  ż: "z",
};

export function normalizeText(value: string): string {
  return value
    .toLowerCase()
    .replace(/[ąćęłńóśźż]/g, (char) => POLISH_LETTERS[char] ?? char)
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function queryTokens(query: string): string[] {
  const normalized = normalizeText(query);
  return normalized ? normalized.split(" ") : [];
}

export function matchesQuery(entry: PaletteEntry, query: string): boolean {
  const tokens = queryTokens(query);
  if (tokens.length === 0) return true;
  const haystack = normalizeText(
    [entry.label, entry.description ?? "", ...(entry.keywords ?? [])].join(" "),
  );
  return tokens.every((token) => haystack.includes(token));
}

export function filterEntries<T extends PaletteEntry>(
  entries: T[],
  query: string,
): T[] {
  return entries.filter((entry) => matchesQuery(entry, query));
}

export function caseHaystack(item: {
  case_number: string;
  subject: string;
}): string {
  return normalizeText(`${item.case_number} ${item.subject}`);
}

export function filterCases<
  T extends { case_number: string; subject: string },
>(cases: T[], query: string): T[] {
  const tokens = queryTokens(query);
  if (tokens.length === 0) return cases;
  return cases.filter((item) => {
    const haystack = caseHaystack(item);
    return tokens.every((token) => haystack.includes(token));
  });
}

/** Poniżej dwóch znaków zapytanie do `GET /api/cases?q=` zwraca zbyt wiele. */
export const MIN_CASE_QUERY_LENGTH = 2;

export function shouldSearchCases(query: string): boolean {
  return normalizeText(query).length >= MIN_CASE_QUERY_LENGTH;
}

export function caseSearchTerm(query: string): string {
  return query.trim();
}
