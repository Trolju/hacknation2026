import { describe, expect, it } from "vitest";

import { inquiryFileName } from "./api";

describe("inquiryFileName", () => {
  it("używa numeru sprawy", () => {
    expect(inquiryFileName("BKS.IV.1431.6.2026")).toBe("zapytanie-BKS.IV.1431.6.2026.txt");
  });

  it("zamienia znaki spoza nazw plików na myślniki", () => {
    expect(inquiryFileName("BKS.IV.1431 6/2026")).toBe("zapytanie-BKS.IV.1431-6-2026.txt");
  });

  it("nie zostawia myślników na brzegach", () => {
    expect(inquiryFileName("  BKS.IV.1431.1.2026  ")).toBe("zapytanie-BKS.IV.1431.1.2026.txt");
  });

  it("radzi sobie z pustym numerem", () => {
    expect(inquiryFileName("")).toBe("zapytanie-sprawa.txt");
    expect(inquiryFileName("///")).toBe("zapytanie-sprawa.txt");
  });
});
