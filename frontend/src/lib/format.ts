import { format, formatDistanceToNowStrict, parseISO } from "date-fns";
import { pl } from "date-fns/locale";

export type Urgency =
  | "overdue"
  | "today"
  | "tomorrow"
  | "soon"
  | "normal"
  | "closed";

export const URGENCY_LABEL: Record<Urgency, string> = {
  overdue: "Po terminie",
  today: "Termin dziś",
  tomorrow: "Termin jutro",
  soon: "Termin wkrótce",
  normal: "W terminie",
  closed: "Zamknięta",
};

export const URGENCY_CLASS: Record<Urgency, string> = {
  overdue: "bg-red-100 text-red-800 border-red-200",
  today: "bg-orange-100 text-orange-900 border-orange-200",
  tomorrow: "bg-amber-100 text-amber-900 border-amber-200",
  soon: "bg-yellow-50 text-yellow-900 border-yellow-200",
  normal: "bg-emerald-50 text-emerald-800 border-emerald-200",
  closed: "bg-slate-100 text-slate-600 border-slate-200",
};

export const STATUS_LABEL: Record<string, string> = {
  nowy: "Nowy",
  zapytania_wyslane: "Zapytania wysłane",
  kwerenda: "Kwerenda",
  przygotowana_odpowiedz: "Przygotowana odpowiedź",
  odpowiedz_wyslana: "Odpowiedź wysłana",
};

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return format(parseISO(value), "d MMMM yyyy", { locale: pl });
}

export function formatShortDate(value: string | null | undefined): string {
  if (!value) return "—";
  return format(parseISO(value), "dd.MM.yyyy", { locale: pl });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return format(parseISO(value), "d MMM yyyy, HH:mm", { locale: pl });
}

export function relativeDays(days: number): string {
  if (days === 0) return "dziś";
  if (days === 1) return "jutro";
  if (days === -1) return "wczoraj";
  if (days < 0) return `${Math.abs(days)} dni temu`;
  return `za ${days} dni`;
}

export function relativeFromNow(value: string): string {
  return formatDistanceToNowStrict(parseISO(value), {
    locale: pl,
    addSuffix: true,
  });
}
