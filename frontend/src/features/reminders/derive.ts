/** Funkcje pomocnicze przypomnień — licznik, odmiana i adres wniosku. */

import type { Reminder } from "@/features/reminders/types";

/** Odmiana rzeczownika „przypomnienie” po liczbie (1 / 2–4 / 5+). */
export function pluralReminders(count: number): string {
  if (count === 1) return "1 przypomnienie";
  const mod10 = count % 10;
  const mod100 = count % 100;
  const few = mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14);
  return few ? `${count} przypomnienia` : `${count} przypomnień`;
}

/** Etykieta dzwonka — licznik czytany przez czytnik ekranu. */
export function reminderCounterLabel(count: number): string {
  return count === 0 ? "Brak przypomnień" : `Przypomnienia: ${count}`;
}

/** Adres kalendarza otwierający kartę wniosku z przypomnienia. */
export function reminderHref(reminder: Reminder): string {
  return `/kalendarz?case=${encodeURIComponent(reminder.case_id)}`;
}
