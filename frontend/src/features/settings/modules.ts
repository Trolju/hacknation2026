/**
 * Opisy modułów dla sekcji „Tryb modułów".
 *
 * Dla każdego modułu tłumaczymy jednym zdaniem, co użytkownik realnie dostaje
 * w trybie atrapy, a co w trybie realnym. Bez żargonu technicznego.
 */

import type { ModuleMode } from "@/features/settings/api";

export type ModuleDescription = {
  label: string;
  fake: string;
  real: string;
};

export const MODE_LABEL: Record<ModuleMode, string> = {
  fake: "Atrapa",
  real: "Realny",
};

export const MODULE_DESCRIPTIONS: Record<string, ModuleDescription> = {
  cases: {
    label: "Kalendarz wniosków",
    fake: "Wnioski demonstracyjne z plików przykładowych; zmiany statusu nie trafiają do bazy urzędu.",
    real: "Wnioski zapisywane w bazie danych urzędu, z pełną historią zmian.",
  },
  ingest: {
    label: "Dokumenty i baza wiedzy",
    fake: "Lista dokumentów przykładowych; wgrany plik nie jest odczytywany.",
    real: "Wgrany plik jest odczytywany, dzielony na fragmenty i indeksowany.",
  },
  archive: {
    label: "Archiwum odpowiedzi",
    fake: "Podobieństwo liczone po słowach w przykładowych odpowiedziach archiwalnych.",
    real: "Wyszukiwanie podobnych odpowiedzi w archiwum urzędu.",
  },
  routing: {
    label: "Kierowanie do wydziałów",
    fake: "Komórka wskazywana po słowach kluczowych z listy komórek urzędu.",
    real: "Komórka wskazywana po słowach kluczowych z rdzeniowaniem polskiej odmiany, frazach i wagach IDF — bez udziału modelu językowego.",
  },
  drafting: {
    label: "Generator odpowiedzi",
    fake: "Szkic odpowiedzi z szablonu, bez modelu językowego.",
    real: "Odpowiedź pisze model językowy, z odnośnikami do źródeł.",
  },
  anonymize: {
    label: "Anonimizacja",
    fake: "Dane osobowe wykrywane regułami: PESEL, NIP, telefon, e-mail.",
    real: "Detektory regułowe: nazwiska po wzorcach i końcówkach, adresy, kody pocztowe, numery ksiąg wieczystych. Model spaCy jest opcjonalny — bez niego zostają reguły.",
  },
  inference: {
    label: "Warstwa modeli",
    fake: "Model nie jest wywoływany; odpowiedzi są zawsze takie same.",
    real: "Zapytania idą do modelu: Mistral, llama.cpp, Ollama albo OpenAI.",
  },
  audit: {
    label: "Dziennik audytu",
    fake: "Wpisy trzymane w pamięci; znikają po restarcie aplikacji.",
    real: "Wpisy zapisywane trwale w bazie danych.",
  },
};

const FALLBACK: ModuleDescription = {
  label: "Moduł",
  fake: "Atrapa zwraca ustalone dane demonstracyjne.",
  real: "Moduł przetwarza prawdziwe dane.",
};

export function describeModule(name: string): ModuleDescription {
  return MODULE_DESCRIPTIONS[name] ?? { ...FALLBACK, label: name };
}
