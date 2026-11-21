/** Zapytanie o przypomnienia o terminach (W11). */

import { useQuery } from "@tanstack/react-query";

import type { Reminder } from "@/features/reminders/types";
import { api } from "@/lib/api";

export const REMINDERS_QUERY_KEY = ["reminders"] as const;

/**
 * Lista przypomnień liczona przez backend przy każdym odczycie.
 *
 * Odświeżamy co minutę, żeby licznik w nagłówku nie zamarł na otwartej karcie —
 * backend nie ma schedulera, więc to jedyny moment, w którym lista się zmienia.
 */
export function useReminders() {
  return useQuery({
    queryKey: REMINDERS_QUERY_KEY,
    queryFn: () => api.get<Reminder[]>("/reminders"),
    refetchInterval: 60_000,
  });
}
