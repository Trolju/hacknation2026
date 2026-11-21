/**
 * Logika prezentacji oceny podobieństwa.
 *
 * Backend zwraca `score` w przedziale 0–1 i już sortuje wyniki, ale lista
 * renderuje się z lokalnego stanu — sortujemy ponownie, żeby kolejność nigdy
 * nie zależała od tego, czy odpowiedź przyszła z cache.
 */

import type { SimilarCase } from "@/lib/types";

export type ScoreTone = "high" | "medium" | "low";

/** Kolor wypełnienia paska — `Progress` renderuje wskaźnik jako pierwsze dziecko. */
export const SCORE_BAR_CLASS: Record<ScoreTone, string> = {
  high: "[&>div]:bg-emerald-500",
  medium: "[&>div]:bg-amber-500",
  low: "[&>div]:bg-slate-400",
};

export const SCORE_TEXT_CLASS: Record<ScoreTone, string> = {
  high: "text-emerald-700 dark:text-emerald-300",
  medium: "text-amber-700 dark:text-amber-300",
  low: "text-slate-600 dark:text-slate-300",
};

function clamp(score: number): number {
  if (!Number.isFinite(score)) return 0;
  return Math.min(Math.max(score, 0), 1);
}

/** Ocena jako procent szerokości paska. */
export function scorePercent(score: number): number {
  return Math.round(clamp(score) * 100);
}

/** Ocena jako liczba z przecinkiem dziesiętnym — tak zapisuje się po polsku. */
export function formatScore(score: number): string {
  return clamp(score).toFixed(2).replace(".", ",");
}

export function scoreTone(score: number): ScoreTone {
  const value = clamp(score);
  if (value >= 0.6) return "high";
  if (value >= 0.35) return "medium";
  return "low";
}

/** Sortowanie po ocenie malejąco; przy remisie decyduje identyfikator. */
export function sortByScore(results: SimilarCase[]): SimilarCase[] {
  return [...results].sort(
    (left, right) =>
      right.score - left.score || left.archive_id.localeCompare(right.archive_id),
  );
}

/** Zdanie z zapytania, które urzędnik może rozpoznać jako źródło trafienia. */
export function queryPreview(text: string, max = 120): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max - 1).trimEnd()}…`;
}
