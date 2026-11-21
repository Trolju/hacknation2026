/**
 * Interpretacja pola „Przedłużenie terminu (dni)”.
 *
 * Backend przyjmuje `kwerenda_days` z zakresu 1–60 i tylko przy przejściu do
 * kwerendy. Puste pole znaczy „nie przedłużaj” — wtedy termin zostaje bez
 * zmian, a żądanie nie niesie `kwerenda_days`.
 */

export const MIN_KWERENDA_DAYS = 1;
export const MAX_KWERENDA_DAYS = 60;

export type KwerendaDays =
  | { ok: true; days: number | undefined }
  | { ok: false };

export function parseKwerendaDays(raw: string): KwerendaDays {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return { ok: true, days: undefined };
  }
  // `parseInt` przepuściłby „14abc” — wymagamy samych cyfr.
  if (!/^\d+$/.test(trimmed)) {
    return { ok: false };
  }
  const days = Number.parseInt(trimmed, 10);
  if (days < MIN_KWERENDA_DAYS || days > MAX_KWERENDA_DAYS) {
    return { ok: false };
  }
  return { ok: true, days };
}
