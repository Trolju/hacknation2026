import { describe, expect, it } from "vitest";

import { parseRedactions } from "./api";

describe("parseRedactions", () => {
  it("czyta liczbę trafień z nagłówka", () => {
    expect(parseRedactions("3")).toBe(3);
    expect(parseRedactions("12")).toBe(12);
  });

  it("brak nagłówka oznacza zero", () => {
    expect(parseRedactions(null)).toBe(0);
  });

  it("śmieci w nagłówku nie wywracają eksportu", () => {
    expect(parseRedactions("")).toBe(0);
    expect(parseRedactions("abc")).toBe(0);
    expect(parseRedactions("-5")).toBe(0);
    expect(parseRedactions("NaN")).toBe(0);
  });
});
