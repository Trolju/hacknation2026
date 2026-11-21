/** Funkcje pomocnicze kalendarza — daty i grupowanie wniosków. */

import { differenceInCalendarDays, parseISO, subDays } from "date-fns";

import type { Case } from "@/lib/types";

/**
 * Data odniesienia backendu („dziś”).
 *
 * Backend liczy `days_remaining` względem `settings.demo_today`, a frontend nie
 * zna tej wartości. Ponieważ `days_remaining = deadline - dziś`, wystarczy
 * odjąć liczbę dni od terminu, żeby odtworzyć datę odniesienia bez dodatkowego
 * zapytania. Dzięki temu demo pokazuje właściwy miesiąc także wtedy, gdy
 * prawdziwa data systemowa jest inna.
 */
export function referenceToday(cases: Case[]): Date {
  const sample = cases[0];
  if (!sample) return new Date();
  return subDays(parseISO(sample.deadline), sample.days_remaining);
}

/** Liczba dni kalendarzowych między datą odniesienia a podaną datą ISO. */
export function daysSince(reference: Date, value: string): number {
  return differenceInCalendarDays(reference, parseISO(value));
}

/** Wnioski pogrupowane po dniu terminu (`yyyy-MM-dd`). */
export function groupByDeadline(cases: Case[]): Map<string, Case[]> {
  const grouped = new Map<string, Case[]>();
  for (const item of cases) {
    const bucket = grouped.get(item.deadline);
    if (bucket) {
      bucket.push(item);
    } else {
      grouped.set(item.deadline, [item]);
    }
  }
  return grouped;
}
