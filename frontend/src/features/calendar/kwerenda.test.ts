import { describe, expect, it } from "vitest";

import {
  MAX_KWERENDA_DAYS,
  MIN_KWERENDA_DAYS,
  parseKwerendaDays,
} from "@/features/calendar/kwerenda";

describe("przedłużenie terminu w kwerendzie", () => {
  it("puste pole znaczy brak przedłużenia", () => {
    expect(parseKwerendaDays("")).toEqual({ ok: true, days: undefined });
    expect(parseKwerendaDays("   ")).toEqual({ ok: true, days: undefined });
  });

  it("przyjmuje liczbę dni z zakresu", () => {
    expect(parseKwerendaDays("14")).toEqual({ ok: true, days: 14 });
    expect(parseKwerendaDays(" 7 ")).toEqual({ ok: true, days: 7 });
    expect(parseKwerendaDays(String(MIN_KWERENDA_DAYS))).toEqual({
      ok: true,
      days: MIN_KWERENDA_DAYS,
    });
    expect(parseKwerendaDays(String(MAX_KWERENDA_DAYS))).toEqual({
      ok: true,
      days: MAX_KWERENDA_DAYS,
    });
  });

  it("odrzuca zero i wartości ujemne", () => {
    expect(parseKwerendaDays("0")).toEqual({ ok: false });
    expect(parseKwerendaDays("-5")).toEqual({ ok: false });
  });

  it("odrzuca wartości powyżej górnej granicy", () => {
    expect(parseKwerendaDays(String(MAX_KWERENDA_DAYS + 1))).toEqual({ ok: false });
    expect(parseKwerendaDays("999")).toEqual({ ok: false });
  });

  it("odrzuca tekst i liczby z ogonem", () => {
    expect(parseKwerendaDays("czternaście")).toEqual({ ok: false });
    expect(parseKwerendaDays("14 dni")).toEqual({ ok: false });
    expect(parseKwerendaDays("14.5")).toEqual({ ok: false });
  });
});
